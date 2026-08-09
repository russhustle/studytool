import re
from pathlib import Path

import requests
import typer
from bs4 import BeautifulSoup

from .cli_types import SortOrder

URL_RE = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')
TRAILING_URL_PUNCTUATION_RE = re.compile(r'[.,;:!?)\]}>"\']+$')


def normalize_url(url: str) -> str:
    """Remove prose punctuation and normalize arXiv PDF links."""
    cleaned = TRAILING_URL_PUNCTUATION_RE.sub("", url)
    return re.sub(r"arxiv\.org/pdf/", "arxiv.org/abs/", cleaned, flags=re.IGNORECASE)


def extract_unique_urls(text: str) -> list[str]:
    """Extract unique normalized HTTP URLs from arbitrary text."""
    return sorted({normalize_url(url) for url in URL_RE.findall(text)})


def get_formatted_link(url: str) -> str:
    """
    Fetch the title from a URL and return a formatted markdown link.
    For arXiv URLs, includes date formatting as [YYYY.MM].

    Args:
        url: The URL to fetch the title from

    Returns:
        Formatted markdown link as [title](url)
    """
    url = normalize_url(url)

    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        title_tag = soup.find("title")

        if title_tag and title_tag.string:
            title = title_tag.string.strip()
        else:
            title = "Untitled"

        # Check if this is an arXiv URL and format accordingly
        if "arxiv.org" in url.lower():
            # Extract arXiv ID from URL (e.g., 2001.08361)
            arxiv_match = re.search(r"(\d{4})\.(\d{4,5})", url)
            if arxiv_match:
                year_month = arxiv_match.group(1)
                year = "20" + year_month[:2]
                month = year_month[2:]
                date_format = f"[{year}.{month}]"
                # Remove arXiv ID from title if present and add date format
                title = re.sub(r"^\[\d{4}\.\d{4,5}\]\s*", "", title)
                title = f"{date_format} {title}"

        return f"[{title}]({url})"

    except Exception:
        # Fallback to URL as title if fetching fails
        return f"[‼️ {url}]({url})"


def format_links_command(
    input_text: str = typer.Argument(None, help="URL, raw text, or a path containing URLs."),
    file: str = typer.Option(None, "--file", "-f", help="Path to a file containing one URL per line."),
    sort: SortOrder = typer.Option(SortOrder.ASCENDING, help="Sort order for formatted links."),
):
    """Format URLs as markdown links with automatic title extraction.

    Can process a single URL or multiple URLs from a file. URLs are automatically
    fetched to extract page titles for properly formatted markdown links.

    Args:
        input_text: URL, raw text, or file path containing URLs.
        file: Path to file containing multiple URLs (one per line).
        sort: Sort order for multiple URLs - 'asc' for ascending, 'desc' for descending.

    Raises:
        typer.Exit: If neither URL nor file is provided, or if file doesn't exist.
    """
    is_collection = bool(file)
    if file:
        file_path = Path(file)
        if not file_path.exists():
            typer.echo(f"Error: File {file} not found", err=True)
            raise typer.Exit(1)
        text = file_path.read_text(encoding="utf-8")
    elif input_text:
        input_path = Path(input_text)
        try:
            is_input_file = input_path.is_file()
        except OSError:
            is_input_file = False
        if is_input_file:
            text = input_path.read_text(encoding="utf-8")
            is_collection = True
        else:
            text = input_text
    else:
        typer.echo("Error: Provide a URL, text, file path, or use --file", err=True)
        raise typer.Exit(1)

    urls = extract_unique_urls(text)
    if not urls:
        typer.echo("Error: No URLs found in the provided input", err=True)
        raise typer.Exit(1)

    is_collection = is_collection or len(urls) > 1 or text.strip() != urls[0]
    formatted_links = sorted(
        (get_formatted_link(url) for url in urls),
        reverse=(sort == SortOrder.DESCENDING),
    )
    for link in formatted_links:
        typer.echo(f"- {link}" if is_collection else link)
