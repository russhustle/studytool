import os

from PyPDF2 import PdfMerger


def merge_pdfs_in_dir(dir_path: str, output_file: str) -> None:
    """Merges all PDF files in a directory into a single PDF file."""
    merger = PdfMerger()
    pdf_files = sorted([f for f in os.listdir(dir_path) if f.endswith(".pdf")])

    for pdf_file in pdf_files:
        with open(os.path.join(dir_path, pdf_file), "rb") as file:
            merger.append(file)

    with open(output_file, "wb") as file:
        merger.write(file)
