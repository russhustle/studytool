import re
from pathlib import Path

import fitz  # PyMuPDF
import typer
from rich.console import Console
from tqdm import tqdm

from .cli_types import SortOrder
from .markdown_links import get_formatted_link

console = Console()


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
        url = re.sub(r'[.,;:!?)\]}>"\']+$', "", url)
        if url.lower().startswith("www."):
            url = "https://" + url
        cleaned_urls.append(url)

    return cleaned_urls


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


def extract_pdf_links_command(
    folder_path: str = typer.Argument(..., help="Path to folder containing PDF files"),
    output: str = typer.Option("links.md", "--output", "-o", help="Output Markdown file name."),
    url_sort: SortOrder = typer.Option(
        SortOrder.DESCENDING,
        "--sort",
        "--url-sort",
        help="Sort order for extracted URLs.",
    ),
):
    """Extract all URLs from PDF files in a folder and save to markdown.

    Processes all PDF files in the specified folder, extracts URLs from each,
    removes duplicates, and saves the sorted list to a markdown file.

    Args:
        folder_path: Path to folder containing PDF files to process.
        output: Name of the output markdown file for the extracted URLs.
        url_sort: Sort order for URLs - 'asc' for ascending, 'desc' for descending.

    Raises:
        typer.Exit: If folder doesn't exist or URL extraction fails.
    """
    try:
        output_path = extract_urls_from_pdf_folder(folder_path, output, url_sort)
        console.print("[green]✅ Successfully extracted URLs from PDF files[/green]")
        console.print(f"[blue]📄 Output saved to: {output_path}[/blue]")

        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
            match = re.search(r"\*\*Total unique URLs found:\*\* (\d+)", content)
            if match:
                url_count = int(match.group(1))
                console.print(f"[yellow]🔗 Found {url_count} unique URLs ({url_sort} order)[/yellow]")
            else:
                console.print(f"[yellow]🔗 URLs extracted and sorted ({url_sort} order)[/yellow]")

    except Exception as e:
        console.print(f"[red]Error extracting URLs: {str(e)}[/red]")
        raise typer.Exit(1)
