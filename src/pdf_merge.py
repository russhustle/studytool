import os

import typer
from PyPDF2 import PdfMerger

app = typer.Typer()


def merge_pdfs_in_dir(dir_path: str, output_file: str) -> None:
    """Merges all PDF files in a directory into a single PDF file."""
    merger = PdfMerger()
    pdf_files = sorted([f for f in os.listdir(dir_path) if f.endswith(".pdf")])

    for pdf_file in pdf_files:
        with open(os.path.join(dir_path, pdf_file), "rb") as file:
            merger.append(file)

    with open(output_file, "wb") as file:
        merger.write(file)


@app.callback(invoke_without_command=True)
def pdfmerge(
    dir_path: str = typer.Argument(default=None, help="Path to the directory"),
    output_file: str = typer.Option(default="merged_pdf.pdf", help="Merged PDF"),
):
    """Merge all PDF files in a directory into a single PDF file.

    Args:
        dir_path: Path to the directory containing PDF files to merge.
        output_file: Name of the output merged PDF file.
    """
    merge_pdfs_in_dir(dir_path=dir_path, output_file=output_file)
