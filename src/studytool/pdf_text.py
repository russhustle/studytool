import re
from pathlib import Path

import fitz
import typer

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


def render_pdf_text(pdf_path: PdfPath, include_page_numbers: bool = False) -> str:
    """Return raw selectable text from every page of a PDF."""
    with fitz.open(str(pdf_path)) as document:
        parts = []
        for index, page in enumerate(document, start=1):
            text = page.get_text("text")
            if include_page_numbers:
                parts.append(f"--- Page {index} ---\n{text}")
            else:
                parts.append(text)
    return "\n".join(parts)


def export_pdf_text(
    pdf_path: PdfPath,
    output_path: PdfPath | None = None,
    include_page_numbers: bool = False,
) -> Path:
    """Extract PDF text to a UTF-8 text file and return its path."""
    pdf_path = Path(pdf_path)
    destination = Path(output_path) if output_path is not None else pdf_path.with_suffix(".txt")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        render_pdf_text(pdf_path, include_page_numbers=include_page_numbers),
        encoding="utf-8",
    )
    return destination


def extract_pdf_text_command(
    pdf_path: Path = typer.Argument(
        ...,
        exists=True,
        dir_okay=False,
        readable=True,
        help="PDF file to extract text from.",
    ),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output text file."),
    page_numbers: bool = typer.Option(
        False,
        "--page-numbers",
        "-p",
        help="Insert a numbered separator before each page.",
    ),
) -> None:
    """Extract selectable PDF text into a plain-text file."""
    try:
        destination = export_pdf_text(pdf_path, output, include_page_numbers=page_numbers)
    except Exception as error:
        typer.echo(f"Error extracting PDF text: {error}", err=True)
        raise typer.Exit(1) from None
    typer.echo(f"Saved: {destination}")
