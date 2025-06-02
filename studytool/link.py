import re

import requests
from bs4 import BeautifulSoup


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
