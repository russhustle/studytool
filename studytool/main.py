import re
from pathlib import Path

import typer

from .link import get_formatted_link
from .num_to_image_path import num2img_path
from .pdf_merge import merge_pdfs_in_dir
from .slides2md import Slide2md
from .trad_to_simp import convert_trad_to_simp
from .youtube_playlist import playlist_titles

app = typer.Typer()


@app.command()
def course(
    course: str = typer.Argument(
        default="./",
        help="Path to the course folder.",
    ),
    update_yaml_only: bool = typer.Option(default=False, help="Update MKDocs YAML Only"),
    dpi: int = typer.Option(default=100, help="DPI for PDF to image conversion"),
):
    """Convert slides to markdown.

    Example:
        studytool course <course_folder>
        studytool course <course_folder> --update-yaml-only
        studytool course <course_folder> --dpi 200
    """
    slide2md = Slide2md(course_folder=course, dpi=dpi)

    if update_yaml_only:
        slide2md.update_index_yaml()

    else:
        slide2md.run()


@app.command()
def pdfmerge(
    dir_path: str = typer.Argument(default=None, help="Path to the directory"),
    output_file: str = typer.Option(default="merged_pdf.pdf", help="Merged PDF"),
):
    """Merge PDF files in a directory.

    Example:
        studytool pdfmerge <directory_path>
    """
    merge_pdfs_in_dir(dir_path=dir_path, output_file=output_file)


@app.command()
def playlist(
    playlist: str = typer.Argument(default=None, help="Path to YouTube Playlost URL."),
    playlist_number: int = typer.Option(default=200, help="Number of videos to extract."),
):
    """Print YouTube playlist titles.

    Example:
        studytool playlist <url>
    """
    playlist_titles(url=playlist, number=playlist_number)


@app.command()
def imgpath(
    md_path: str = typer.Argument(default=None, help="Path to the markdown file"),
    interval: int = typer.Option(default=10, help="Interval in seconds to rerun the operation"),
    pattern: str = typer.Option(default="、", help="Custom pattern to replace with image paths"),
    once: bool = typer.Option(default=True, help="Run once without continuous monitoring"),
):
    """Convert numbers to image paths in markdown files.

    Example:
        studytool imgpath <md_file_path>
        studytool imgpath <md_file_path> --interval 5
        studytool imgpath <md_file_path> --pattern "XXX"
        studytool imgpath <md_file_path> --once
    """
    import time

    num2img_path(md_path=md_path, pattern=pattern)

    if not once:
        while True:
            time.sleep(interval)
            num2img_path(md_path=md_path, pattern=pattern)


@app.command()
def t2s(
    file_path: str = typer.Argument(
        ..., help="Path to the Markdown or text file to convert from Traditional to Simplified Chinese."
    ),
):
    """
    Convert Traditional Chinese text in a Markdown or text file to Simplified Chinese.
    The file is overwritten with the converted content.

    Example:
        studytool t2s <path_to_file.md_or_txt>
    """
    convert_trad_to_simp(file_path=file_path)


@app.command()
def link(
    url: str = typer.Argument(None, help="URL to format as markdown link"),
    file: str = typer.Option(None, help="Path to file containing URLs (one per line)"),
    sort: str = typer.Option("asc", help="Sort order: 'asc' (ascending) or 'desc' (descending)"),
):
    """Format URL(s) as markdown links with titles.

    Example:
        studytool link https://example.com
        studytool link --file urls.txt
        studytool link --file urls.txt --sort desc
    """
    if file:
        # Process multiple URLs from file
        file_path = Path(file)
        if not file_path.exists():
            typer.echo(f"Error: File {file} not found", err=True)
            raise typer.Exit(1)

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Extract URLs from each line (handle markdown links or plain URLs)
        urls = []
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Extract URL from markdown link format [title](url) or plain URL
            url_match = re.search(r"\((https?://[^\)]+)\)", line)
            if url_match:
                urls.append(url_match.group(1))
            elif line.startswith("http"):
                urls.append(line)

        # Get formatted links
        formatted_links = []
        for url in urls:
            formatted_link = get_formatted_link(url)
            formatted_links.append(formatted_link)

        # Sort the formatted links
        if sort.lower() == "desc":
            formatted_links.sort(reverse=True)
        else:
            formatted_links.sort()

        # Output results
        for link in formatted_links:
            typer.echo(f"- {link}")

    elif url:
        # Process single URL
        formatted_link = get_formatted_link(url)
        typer.echo(formatted_link)

    else:
        typer.echo("Error: Either provide a URL or use --file option", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
