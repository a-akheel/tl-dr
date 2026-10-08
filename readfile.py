"""Read uploaded documents in memory; no Java server or temporary uploads."""
from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PdfReader


def getText(source, filename=None):
    """Accept a file-like object or a local path for command-line use."""
    if filename is None:
        filename = str(source)
        source = BytesIO(Path(source).read_bytes())
    extension = Path(filename).suffix.lower()
    try:
        if extension == ".txt":
            return source.read().decode("utf-8-sig")
        if extension == ".docx":
            document = Document(source)
            paragraphs = [p.text for p in document.paragraphs]
            paragraphs.extend(" ".join(cell.text for cell in row.cells)
                              for table in document.tables for row in table.rows)
            return "\n".join(paragraphs)
        if extension == ".pdf":
            reader = PdfReader(source)
            if reader.is_encrypted:
                raise ValueError("Use a PDF without password protection.")
            if len(reader.pages) > 100:
                raise ValueError("Use a PDF with at most 100 pages.")
            return "\n".join(page.extract_text() or "" for page in reader.pages)
    except ValueError:
        raise
    except Exception:
        raise ValueError("Could not read this file. Use UTF-8 TXT, DOCX, or a PDF with selectable text.") from None
    raise ValueError("Unsupported file. Use TXT, PDF, or DOCX.")
