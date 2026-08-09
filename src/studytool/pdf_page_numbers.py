import os
import tempfile
from pathlib import Path

import fitz
import typer

from .cli_types import PageNumberColor, PageNumberPosition

PAGE_NUMBER_COLORS = {
    PageNumberColor.BLACK: (0, 0, 0),
    PageNumberColor.WHITE: (1, 1, 1),
}


def horizontal_text_position(
    position: PageNumberPosition,
    page_width: float,
    text_width: float,
    margin: float,
) -> float:
    """Calculate the horizontal coordinate for a page-number label."""
    if position == PageNumberPosition.CENTER:
        return (page_width - text_width) / 2
    if position == PageNumberPosition.RIGHT:
        return page_width - text_width - margin
    return margin


def add_page_numbers_to_pdf(
    pdf_path: Path,
    output_path: Path,
    color: PageNumberColor = PageNumberColor.BLACK,
    font_size: float = 14.0,
    position: PageNumberPosition = PageNumberPosition.LEFT,
) -> Path:
    """Add `current / total` labels to a PDF and return the output path."""
    source = pdf_path.resolve()
    destination = output_path.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)

    with fitz.open(source) as document:
        total_pages = document.page_count
        for index, page in enumerate(document, start=1):
            scaled_font_size = font_size * (page.rect.height / 540)
            label = f"{index} / {total_pages}"
            text_width = fitz.get_text_length(label, fontsize=scaled_font_size)
            margin = page.rect.width * 0.03
            x_coordinate = horizontal_text_position(position, page.rect.width, text_width, margin)
            y_coordinate = page.rect.height * 0.97
            page.insert_text(
                (x_coordinate, y_coordinate),
                label,
                fontsize=scaled_font_size,
                color=PAGE_NUMBER_COLORS[color],
            )

        with tempfile.NamedTemporaryFile(
            prefix=f".{destination.stem}.",
            suffix=".pdf",
            dir=destination.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
        try:
            document.save(temporary_path)
        except BaseException:
            temporary_path.unlink(missing_ok=True)
            raise

    os.replace(temporary_path, destination)
    return destination


def discover_pdfs(directory: Path) -> list[Path]:
    """Return PDF files in a directory using deterministic ordering."""
    return sorted(
        (path for path in directory.iterdir() if path.is_file() and path.suffix.lower() == ".pdf"),
        key=lambda path: path.name.casefold(),
    )


def add_page_numbers_command(
    input_path: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="Input PDF file or directory.",
    ),
    color: PageNumberColor = typer.Option(PageNumberColor.BLACK, help="Page-number color."),
    font_size: float = typer.Option(14.0, min=0.1, help="Base font size at 540-point page height."),
    position: PageNumberPosition = typer.Option(PageNumberPosition.LEFT, help="Horizontal label position."),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file, or output directory when the input is a directory.",
    ),
) -> None:
    """Add page numbers to one PDF or every PDF in a directory."""
    try:
        if input_path.is_dir():
            pdfs = discover_pdfs(input_path)
            if not pdfs:
                raise ValueError("No PDF files found in directory")
            output_directory = output or input_path
            if output_directory.exists() and not output_directory.is_dir():
                raise ValueError("Output must be a directory when input is a directory")
            output_directory.mkdir(parents=True, exist_ok=True)
            destinations = [
                add_page_numbers_to_pdf(pdf, output_directory / pdf.name, color, font_size, position) for pdf in pdfs
            ]
        else:
            destination = output or input_path
            if destination.exists() and destination.is_dir():
                destination = destination / input_path.name
            destinations = [add_page_numbers_to_pdf(input_path, destination, color, font_size, position)]
    except Exception as error:
        typer.echo(f"Error adding page numbers: {error}", err=True)
        raise typer.Exit(1) from None

    for destination in destinations:
        typer.echo(f"Saved: {destination}")
