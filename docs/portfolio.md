# TL;DR portfolio case study

## Problem and intended user

People reviewing long reports and articles need a quick first pass before deciding what to read in detail. TL;DR demonstrates a workflow that accepts familiar inputs and produces a compact, exportable brief. Support analysts and implementation teams are example audiences; they are not verified customers.

## Role

Original project: solo developer, as confirmed by the repository owner. The recovered code includes a Flask web workflow, frequency-based summarization, article ingestion, document uploads, and Word export. The current rebuild was implemented with Codex assistance and is documented separately from the original work.

## Solution

Python/Flask routes text from paste, URL, or TXT/PDF/DOCX input through NLTK sentence scoring. The app preserves selected sentences in source order, reports reduction and recurring terms, and exports DOCX. SQLite stores expiring summaries while the browser retains only an identifier.

## Decisions worth explaining in an interview

- **Extractive summarization:** preserves original wording and requires no model API credentials or inference service. It can miss important low-frequency facts and needs human review.
- **Three input modes:** meet users where their information already lives. Document parsing and HTML extraction have different failure modes, so the UI gives specific recovery guidance.
- **In-memory file handling:** avoids cross-platform upload/download path errors and leaves no original upload files to manage.
- **Server-side result storage:** keeps document content out of signed browser cookies and supports larger summaries. A single-instance SQLite demo is simple; a distributed deployment needs shared infrastructure.
- **Measured demo scope:** short synthetic inputs show reproducible latency and compression. They do not establish adoption, accuracy, or business impact.

## Evidence

- [Source and architecture](../README.md)
- [Verified screenshot](demo-summary.jpg)
- [Automated workflow tests](../tests/test_app.py)
- [Benchmark script](../scripts/benchmark.py) and [raw results](benchmark-results.json)
- [Synthetic customer-rollout sample](../samples/customer-rollout.txt)

Three bundled samples produced 69–72% word-count reduction with median warm summarizer latency of 2.63–2.68 ms across 30 runs per sample on the recorded machine. Human quality evaluation and real-user outcomes remain unmeasured.

## Resume wording

> Developed a solo Python/Flask document summarizer with three ingestion modes, adjustable extractive summaries, and DOCX export; rebuilt the demo with AI assistance and validated it with 18 automated workflow and input-handling tests.

Optional technical measurement, when space permits:

> Benchmarked three synthetic documents over 30 warm runs each, measuring 69–72% word-count reduction and 2.63–2.68 ms median summarization latency on a local machine.

## How to demonstrate Solutions Engineer skills

Start with discovery: which documents does the user review, which facts must survive, and where should the summary go? Walk through one sample, explain the architecture and failure recovery, and discuss how you would integrate a future API into their workflow. Define proof-of-concept acceptance criteria before claiming value: factual coverage, user-rated usefulness, end-to-end latency, and observed task completion time against a baseline.

The synthetic rollout document mentions REST APIs and single sign-on as scenario context. TL;DR itself does not currently implement those integrations or authentication.
