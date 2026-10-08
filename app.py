"""Flask demo for extractive document summarization."""
import json
import os
import secrets
import sqlite3
import time
from io import BytesIO
from contextlib import contextmanager
from pathlib import Path

from docx import Document
from flask import Flask, flash, jsonify, redirect, render_template, request, send_file, session, url_for
from werkzeug.exceptions import RequestEntityTooLarge

from readfile import getText
from summary import getPercentage, getTopWords, summarize
from webScrape import getArticle

app = Flask(__name__, instance_relative_config=True)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
    MAX_CONTENT_LENGTH=5 * 1024 * 1024,
    MAX_TEXT_LENGTH=100_000,
    SUMMARY_TTL=3600,
    DATABASE=str(Path(app.instance_path) / "summaries.sqlite3"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE") == "1",
)


@contextmanager
def database():
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(app.config["DATABASE"])
    connection.execute("CREATE TABLE IF NOT EXISTS summaries (id TEXT PRIMARY KEY, payload TEXT, expires REAL)")
    connection.execute("DELETE FROM summaries WHERE expires <= ?", (time.time(),))
    connection.commit()
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]


app.jinja_env.globals["csrf_token"] = csrf_token


def validate_text(text):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("No readable text found. Paste text or use a document with selectable text.")
    if len(text) > app.config["MAX_TEXT_LENGTH"]:
        raise ValueError("Please use a document with at most 100,000 characters.")
    return text.strip()


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html")
    token = session.get("csrf_token", "")
    if not token or not secrets.compare_digest(token, request.form.get("csrf_token", "")):
        flash("Your form expired. Please try again.")
        return redirect(url_for("index"))
    try:
        title = ""
        if "text" in request.form:
            text = request.form["text"]
            size = request.form.get("copy-size", "7")
        elif "url" in request.form:
            title, text = getArticle(request.form["url"])
            size = request.form.get("url-size", "7")
        elif "file" in request.files:
            uploaded = request.files["file"]
            if not uploaded.filename:
                raise ValueError("Choose a TXT, PDF, or DOCX file.")
            text = getText(uploaded.stream, uploaded.filename)
            size = request.form.get("upload-size", "7")
        else:
            raise ValueError("Paste text, enter an article URL, or choose a file.")
        try:
            size = int(size)
        except (ValueError, TypeError):
            raise ValueError("Summary length must be a number from 3 to 30.") from None
        if not 3 <= size <= 30:
            raise ValueError("Choose between 3 and 30 sentences.")
        text = validate_text(text)
        started = time.perf_counter()
        sentences = summarize(text, title, n=size)
        if not sentences:
            raise ValueError("No sentences could be summarized. Try a longer document.")
        elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
        summary_id = secrets.token_urlsafe(24)
        with database() as connection:
            previous = session.get("summary_id")
            if previous:
                connection.execute("DELETE FROM summaries WHERE id = ?", (previous,))
            connection.execute("INSERT INTO summaries VALUES (?, ?, ?)", (
                summary_id, json.dumps({"title": title, "sentences": sentences}),
                time.time() + app.config["SUMMARY_TTL"],
            ))
        session["summary_id"] = summary_id
        return render_template("result.html", summaries=sentences, title=title,
                               percentage=getPercentage(text, sentences),
                               words=getTopWords(text), elapsed_ms=elapsed_ms)
    except ValueError as error:
        flash(str(error))
    except LookupError:
        app.logger.exception("NLTK resources unavailable")
        flash("Language resources are unavailable. Please contact the demo maintainer.")
    except Exception:
        app.logger.exception("Summary processing failed")
        flash("This document could not be processed. Try pasted text or a different file.")
    return redirect(url_for("index"))


@app.route("/download/")
def download():
    with database() as connection:
        row = connection.execute("SELECT payload FROM summaries WHERE id = ? AND expires > ?",
                                 (session.get("summary_id", ""), time.time())).fetchone()
    if row is None:
        flash("Create a summary first. Downloads expire after one hour.")
        return redirect(url_for("index"))
    payload = json.loads(row[0])
    document = Document()
    document.add_heading(payload["title"] or "Summary", level=1)
    for sentence in payload["sentences"]:
        document.add_paragraph(sentence)
    output = BytesIO()
    document.save(output)
    output.seek(0)
    response = send_file(output, download_name="summary.docx", as_attachment=True,
                        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/_show_url_content/")
def show_url_content():
    try:
        title, text = getArticle(request.args.get("url", ""))
        return jsonify(title=title, result=validate_text(text))
    except ValueError as error:
        return jsonify(error=str(error)), 400
    except Exception:
        app.logger.exception("Article preview failed")
        return jsonify(error="Could not read this article. Paste its text instead."), 400


@app.errorhandler(RequestEntityTooLarge)
def too_large(error):
    flash("The upload is too large. Use a file smaller than 5 MB.")
    return redirect(url_for("index"))


@app.after_request
def no_document_cache(response):
    if request.method == "POST" or request.path.startswith(("/download", "/_show_url_content")):
        response.headers["Cache-Control"] = "no-store"
    return response


if __name__ == "__main__":
    app.run()
