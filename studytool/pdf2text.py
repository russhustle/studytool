import re
from pathlib import Path

import fitz
from tqdm import tqdm

from .link import get_formatted_link


def pdf_to_markdown(pdf_path: str, output_path: str = None, extract_urls: bool = False, url_sort: str = "desc") -> str:
    """Convert a PDF file to markdown format.

    Args:
        pdf_path: Path to the PDF file to convert
        output_path: Optional path to save the output file
        extract_urls: Whether to extract URLs from the PDF
        url_sort: Sort order for URLs ("asc" or "desc")

    Returns:
        The markdown content as a string
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    doc = fitz.open(pdf_path)
    markdown_content = [f"# {pdf_path.stem}", ""]
    all_urls = []

    for page_num in tqdm(range(len(doc)), desc=f"Processing {pdf_path.name}"):
        page = doc.load_page(page_num)
        text = page.get_text()

        if text.strip():
            markdown_content.extend([f"## Page {page_num + 1}", "", clean_pdf_text(text), ""])

            if extract_urls:
                all_urls.extend(extract_urls_from_text(text))

    if extract_urls and all_urls:
        unique_urls = list(set(all_urls))
        formatted_links = [get_formatted_link(url) for url in tqdm(unique_urls, desc="Formatting URLs")]

        formatted_links.sort(reverse=(url_sort.lower() != "asc"))

        markdown_content.extend(["## Extracted URLs", ""])
        markdown_content.extend([f"- {link}" for link in formatted_links])
        markdown_content.append("")

    doc.close()
    final_content = "\n".join(markdown_content)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_content)

    return final_content


def extract_urls_from_text(text: str) -> list:
    """Extract URLs from text using regex patterns.

    Args:
        text: The text to extract URLs from

    Returns:
        List of cleaned URLs found in the text
    """
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+|www\.[^\s<>"{}|\\^`\[\]]+'
    urls = re.findall(url_pattern, text, re.IGNORECASE)

    cleaned_urls = []
    for url in urls:
        url = re.sub(r'[.,;:!?)\]}>"\']$', "", url)
        if url.lower().startswith("www."):
            url = "https://" + url
        cleaned_urls.append(url)

    return cleaned_urls


def clean_pdf_text(text: str) -> str:
    """Clean and format text extracted from PDF.

    Args:
        text: Raw text extracted from PDF

    Returns:
        Cleaned and formatted text with proper spacing and headers
    """
    text = re.sub(r"\n\s*\n\s*\n", "\n\n", text)
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
    text = re.sub(r" +", " ", text)
    text = re.sub(r"\n +", "\n", text)

    lines = text.split("\n")
    formatted_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            formatted_lines.append("")
        elif (line.isupper() and len(line) < 100) or (line.istitle() and len(line) < 80):
            formatted_lines.append(f"### {line}")
        else:
            formatted_lines.append(line)

    return "\n".join(formatted_lines)


def extract_urls_from_pdf_folder(folder_path: str, output_file: str = "links.md", url_sort: str = "desc") -> str:
    """Extract URLs from all PDF files in a folder and save to markdown.

    Args:
        folder_path: Path to folder containing PDF files
        output_file: Name of output markdown file
        url_sort: Sort order for URLs ("asc" or "desc")

    Returns:
        Path to the created output file
    """
    folder_path = Path(folder_path)

    if not folder_path.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")
    if not folder_path.is_dir():
        raise ValueError(f"Path is not a directory: {folder_path}")

    pdf_files = list(folder_path.glob("*.pdf"))
    if not pdf_files:
        raise ValueError(f"No PDF files found in: {folder_path}")

    pdf_urls_data = []
    all_unique_urls = set()

    for pdf_file in tqdm(pdf_files, desc="Processing PDF files"):
        try:
            doc = fitz.open(pdf_file)
            pdf_urls = []

            for page_num in tqdm(range(len(doc)), desc=f"Pages in {pdf_file.name}", leave=False):
                page = doc.load_page(page_num)
                pdf_urls.extend(extract_urls_from_text(page.get_text()))

            doc.close()

            if pdf_urls:
                unique_pdf_urls = list(set(pdf_urls))
                formatted_links = [
                    get_formatted_link(url)
                    for url in tqdm(unique_pdf_urls, desc=f"Formatting URLs in {pdf_file.name}", leave=False)
                ]

                for link in formatted_links:
                    all_unique_urls.add(link)

                formatted_links.sort(reverse=(url_sort.lower() != "asc"))
                pdf_urls_data.append(
                    {"filename": pdf_file.name, "urls": formatted_links, "count": len(formatted_links)}
                )

        except Exception as e:
            tqdm.write(f"Warning: Could not process {pdf_file.name}: {str(e)}")

    if not pdf_urls_data:
        raise ValueError("No URLs found in any PDF files")

    pdf_urls_data.sort(key=lambda x: x["filename"])

    markdown_content = [
        "# Extracted URLs from PDF Files",
        "",
        f"**Folder:** `{folder_path.resolve()}`",
        f"**Total PDFs processed:** {len(pdf_urls_data)}",
        f"**Total unique URLs found:** {len(all_unique_urls)}",
        f"**Sort order:** {url_sort}",
        "",
        "## Table of Contents",
        "",
    ]

    for pdf_data in pdf_urls_data:
        markdown_content.append(
            f"- [{pdf_data['filename']}](#{pdf_data['filename'].replace('.', '').replace(' ', '-').lower()}) ({pdf_data['count']} URLs)"
        )

    markdown_content.append("")

    for pdf_data in pdf_urls_data:
        markdown_content.extend([f"## {pdf_data['filename']}", "", f"**Found {pdf_data['count']} URLs:**", ""])
        markdown_content.extend([f"- {link}" for link in pdf_data["urls"]])
        markdown_content.append("")

    all_formatted_links = list(all_unique_urls)
    all_formatted_links.sort(reverse=(url_sort.lower() != "asc"))

    markdown_content.extend(["## All Unique URLs (Summary)", ""])
    markdown_content.extend([f"- {link}" for link in all_formatted_links])

    output_path = folder_path / output_file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(markdown_content))

    return str(output_path)
