# TL;DR — extractive document summarizer

An earlier Flask/NLTK project that ranks source sentences. This is an extractive baseline, not an LLM application. Text, TXT/PDF/DOCX files and explicitly allowed article hosts can be summarized and exported as Word documents.

## Run locally

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m nltk.downloader punkt punkt_tab stopwords wordnet
.venv/bin/python app.py
```

Open http://127.0.0.1:5000. Debug mode is off. Without `FLASK_SECRET_KEY`, a random process-local key is generated; restarting signs out existing sessions. Configure a persistent strong key for multiple workers. Do not commit it.

Document summaries live in a private SQLite file under `instance/`; cookies contain only random IDs and CSRF tokens. State older than 24 hours is removed on the next state access. Uploaded files are temporary and removed after extraction. Exports are generated in memory. This is not an authenticated, internet-ready document service; use synthetic/public text for demonstrations.

URL fetching is disabled unless `ARTICLE_ALLOWED_HOSTS` lists exact trusted hostnames. Only HTTPS on port 443 is accepted; redirects and environment proxies are disabled and downloads are bounded. Only configure hosts you trust, and use network egress restrictions before deployment. The application does not claim complete protection against DNS rebinding.

## Verify

```sh
.venv/bin/pip install pytest
.venv/bin/python -m pytest -q
```

Route tests isolate the NLP algorithm to test session isolation, CSRF, file handling and downloads. They do not benchmark summary quality. File extraction uses pypdf and python-docx rather than an external Java/Tika service.

## Next experiment

Compare this extractive baseline with a source-cited LLM summary on a fixed public dataset. Measure omitted facts and unsupported claims separately from compression. That extension is planned, not implemented here.

Local verification also exercised the real NLTK summarizer on a four-sentence public synthetic example: it selected two source sentences and handled an empty compression input. This is a smoke check, not a quality evaluation.
