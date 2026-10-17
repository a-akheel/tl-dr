"""Bounded local file extraction without a Java/Tika server."""

from pathlib import Path
from zipfile import ZipFile
from docx import Document
from pypdf import PdfReader


def getText(path):
    path = Path(path)
    try:
        if path.suffix.lower() == ".txt":
            return path.read_text(encoding="utf-8")
        if path.suffix.lower() == ".pdf":
            reader = PdfReader(path)
            if reader.is_encrypted or len(reader.pages) > 100:
                raise ValueError("Encrypted or oversized PDF")
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
                if len(text) > 100_000:
                    raise ValueError("Document too large")
            return text
        if path.suffix.lower() == ".docx":
            with ZipFile(path) as archive:
                if sum(x.file_size for x in archive.infolist()) > 20_000_000:
                    raise ValueError("Expanded document too large")
            return "\n".join(p.text for p in Document(path).paragraphs)
    except Exception as exc:
        raise ValueError("Cannot extract document") from exc
    raise ValueError("Unsupported extension")
