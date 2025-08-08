import re
from pathlib import Path

import fitz
from tqdm import tqdm

from .link import get_formatted_link
from rich.console import Console
import typer

app = typer.Typer()
console = Console()


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


@app.command()
def pdf2md(
    pdf_path: str = typer.Argument(..., help="Path to the PDF file"),
    output: str = typer.Option(None, help="Output markdown file path (optional)"),
    extract_urls: bool = typer.Option(False, help="Extract URLs from PDF and include in markdown"),
    url_sort: str = typer.Option("desc", help="Sort order for URLs: 'asc' (ascending) or 'desc' (descending)"),
):
    """Convert PDF file to markdown format with optional URL extraction.

    Extracts text content from PDF and converts it to markdown format.
    Optionally extracts and lists all URLs found in the PDF.

    Args:
        pdf_path: Path to the PDF file to convert.
        output: Output path for the markdown file. If not provided, uses PDF name with .md extension.
        extract_urls: If True, extracts all URLs from the PDF and appends them to the markdown.
        url_sort: Sort order for extracted URLs - 'asc' for ascending, 'desc' for descending.

    Raises:
        typer.Exit: If PDF file doesn't exist or conversion fails.
    """
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        console.print(f"[red]Error: PDF file not found: {pdf_path}[/red]")
        raise typer.Exit(1)

    if not output:
        output = pdf_file.with_suffix(".md")

    try:
        content = pdf_to_markdown(pdf_path, output, extract_urls=extract_urls, url_sort=url_sort)
        console.print(f"[green]✅ Successfully converted PDF to Markdown: {output}[/green]")
        console.print(f"[blue]📄 Generated {len(content.split())} words[/blue]")

        if extract_urls:
            url_count = content.count("## Extracted URLs")
            if url_count > 0:
                console.print(f"[yellow]🔗 Extracted and sorted URLs ({url_sort} order)[/yellow]")
            else:
                console.print("[yellow]🔗 No URLs found in the PDF[/yellow]")

    except Exception as e:
        console.print(f"[red]Error converting PDF: {str(e)}[/red]")
        raise typer.Exit(1)
