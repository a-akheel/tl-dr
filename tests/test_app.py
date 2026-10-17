import io
import pytest
import app as module
from readfile import getText
from webScrape import getArticle


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(module, "summarize", lambda text, title="", n=7: [text])
    monkeypatch.setattr(module, "getPercentage", lambda *args: 0)
    monkeypatch.setattr(module, "getTopWords", lambda *args: [])
    app = module.create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-only",
            "STATE_DB": str(tmp_path / "state.db"),
        }
    )
    return app.test_client()


def csrf(client):
    client.get("/")
    with client.session_transaction() as session:
        return session["csrf"]


def test_summary_is_not_stored_in_cookie(client):
    text = "PRIVATE DOCUMENT CONTENT"
    response = client.post(
        "/", data={"csrf_token": csrf(client), "text": text, "copy-size": "3"}
    )
    assert response.status_code == 200
    with client.session_transaction() as session:
        assert set(session) <= {"sid", "csrf"}
        assert text not in str(dict(session))
    result = client.get("/download/")
    assert result.status_code == 200
    assert result.data.startswith(b"PK")


def test_csrf_and_invalid_length(client):
    assert client.post("/", data={"text": "test"}).status_code == 403
    assert (
        client.post(
            "/", data={"csrf_token": csrf(client), "text": "test", "copy-size": "900"}
        ).status_code
        == 400
    )


def test_upload_paths_are_portable_and_not_user_controlled(client):
    result = client.post(
        "/",
        data={
            "csrf_token": csrf(client),
            "placeholder": "",
            "file": (io.BytesIO(b"Hello document."), "../../note.txt"),
            "upload-size": "3",
        },
    )
    assert result.status_code == 200


def test_empty_input_and_download_before_generation(client):
    assert client.get("/download/").status_code == 404
    assert (
        client.post("/", data={"csrf_token": csrf(client), "text": "  "}).status_code
        == 400
    )


def test_url_fetch_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ARTICLE_ALLOWED_HOSTS", raising=False)
    with pytest.raises(ValueError):
        getArticle("https://example.com")


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com",
        "https://user@example.com",
        "https://example.com:444",
        "https://other.example",
    ],
)
def test_url_scope(monkeypatch, url):
    monkeypatch.setenv("ARTICLE_ALLOWED_HOSTS", "example.com")
    with pytest.raises(ValueError):
        getArticle(url)


def test_invalid_document(tmp_path):
    path = tmp_path / "bad.pdf"
    path.write_bytes(b"not a pdf")
    with pytest.raises(ValueError):
        getText(path)


def test_clients_do_not_share_documents(client):
    client.post("/", data={"csrf_token": csrf(client), "text": "Private summary"})
    other = client.application.test_client()
    assert other.get("/download/").status_code == 404
