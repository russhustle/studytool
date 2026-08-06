import re
from pathlib import Path

import fitz

PdfPath = str | Path


def clean_selectable_text(text: str) -> str:
    """Lightly clean selectable PDF text without inferring Markdown structure."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"(?<=\w)-[ \t]*\n[ \t]*(?=\w)", "", normalized)
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in normalized.split("\n")]
    normalized = "\n".join(lines)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def count_pdf_pages(pdf_path: PdfPath) -> int:
    """Return the number of pages in a PDF."""
    with fitz.open(str(pdf_path)) as document:
        return document.page_count


def extract_selectable_page_texts(pdf_path: PdfPath) -> list[str]:
    """Return one lightly cleaned selectable-text value per PDF page."""
    with fitz.open(str(pdf_path)) as document:
        return [clean_selectable_text(page.get_text()) for page in document]
