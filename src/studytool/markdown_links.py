import re
from pathlib import Path

import requests
import typer
from bs4 import BeautifulSoup

from .cli_types import SortOrder


def get_formatted_link(url: str) -> str:
    """
    Fetch the title from a URL and return a formatted markdown link.
    For arXiv URLs, includes date formatting as [YYYY.MM].

    Args:
        url: The URL to fetch the title from

    Returns:
        Formatted markdown link as [title](url)
    """
    # Convert arXiv PDF URLs to abstract URLs
    if "arxiv.org/pdf/" in url.lower():
        url = url.replace("/pdf/", "/abs/")

    try:
        response = requests.get(url, timeout=10)
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
    url: str = typer.Argument(None, help="URL to format as markdown link"),
    file: str = typer.Option(None, "--file", "-f", help="Path to a file containing one URL per line."),
    sort: SortOrder = typer.Option(SortOrder.ASCENDING, help="Sort order for formatted links."),
):
    """Format URLs as markdown links with automatic title extraction.

    Can process a single URL or multiple URLs from a file. URLs are automatically
    fetched to extract page titles for properly formatted markdown links.

    Args:
        url: Single URL to format as a markdown link.
        file: Path to file containing multiple URLs (one per line).
        sort: Sort order for multiple URLs - 'asc' for ascending, 'desc' for descending.

    Raises:
        typer.Exit: If neither URL nor file is provided, or if file doesn't exist.
    """
    if file:
        file_path = Path(file)
        if not file_path.exists():
            typer.echo(f"Error: File {file} not found", err=True)
            raise typer.Exit(1)

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        urls = []
        for line in lines:
            line = line.strip()
            if not line:
                continue

            url_match = re.search(r"\((https?://[^\)]+)\)", line)
            if url_match:
                urls.append(url_match.group(1))
            elif line.startswith("http"):
                urls.append(line)

        formatted_links = [get_formatted_link(url) for url in urls]
        formatted_links.sort(reverse=(sort.lower() == "desc"))

        for link in formatted_links:
            typer.echo(f"- {link}")

    elif url:
        typer.echo(get_formatted_link(url))
    else:
        typer.echo("Error: Either provide a URL or use --file option", err=True)
        raise typer.Exit(1)
