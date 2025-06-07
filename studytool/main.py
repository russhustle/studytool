import re
from pathlib import Path

import typer
from rich.console import Console

from .ebook import epub_to_md, extract_imgs_from_epub, extract_toc
from .link import get_formatted_link
from .num_to_image_path import num2img_path
from .pdf2text import extract_urls_from_pdf_folder, pdf_to_markdown
from .pdf_merge import merge_pdfs_in_dir
from .slides2md import Slide2md
from .trad_to_simp import convert_trad_to_simp
from .youtube_playlist import playlist_titles

app = typer.Typer()
console = Console()


@app.command()
def course(
    course: str = typer.Argument(default="./", help="Path to the course folder."),
    update_yaml_only: bool = typer.Option(default=False, help="Update MKDocs YAML Only"),
    dpi: int = typer.Option(default=100, help="DPI for PDF to image conversion"),
):
    """Process course materials and convert slides to markdown format.

    Args:
        course: Path to the course folder containing slides and materials.
        update_yaml_only: If True, only updates MKDocs YAML configuration without processing slides.
        dpi: Resolution for PDF to image conversion (higher values = better quality).
    """
    slide2md = Slide2md(course_folder=course, dpi=dpi)
    slide2md.update_index_yaml() if update_yaml_only else slide2md.run()


@app.command()
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


@app.command()
def playlist(
    playlist: str = typer.Argument(default=None, help="Path to YouTube Playlost URL."),
    playlist_number: int = typer.Option(default=200, help="Number of videos to extract."),
):
    """Extract video titles from a YouTube playlist.

    Args:
        playlist: YouTube playlist URL to process.
        playlist_number: Maximum number of video titles to extract from the playlist.
    """
    playlist_titles(url=playlist, number=playlist_number)


@app.command()
def imgpath(
    md_path: str = typer.Argument(default=None, help="Path to the markdown file"),
    interval: int = typer.Option(default=10, help="Interval in seconds to rerun the operation"),
    pattern: str = typer.Option(default="、", help="Custom pattern to replace with image paths"),
    once: bool = typer.Option(default=True, help="Run once without continuous monitoring"),
):
    """Convert numbered patterns in markdown to image paths.

    This function replaces patterns (like "、") with corresponding image paths
    in markdown files. Can run once or continuously monitor the file.

    Args:
        md_path: Path to the markdown file to process.
        interval: Time in seconds between runs when continuous monitoring is enabled.
        pattern: Text pattern to replace with image paths.
        once: If True, runs once; if False, runs continuously with specified interval.
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
    )
):
    """Convert Traditional Chinese text to Simplified Chinese in a file.

    Args:
        file_path: Path to the markdown or text file containing Traditional Chinese text.
    """
    convert_trad_to_simp(file_path=file_path)


@app.command()
def link(
    url: str = typer.Argument(None, help="URL to format as markdown link"),
    file: str = typer.Option(None, help="Path to file containing URLs (one per line)"),
    sort: str = typer.Option("asc", help="Sort order: 'asc' (ascending) or 'desc' (descending)"),
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


@app.command()
def pdflinks(
    folder_path: str = typer.Argument(..., help="Path to folder containing PDF files"),
    output: str = typer.Option("links.md", help="Output markdown file name"),
    url_sort: str = typer.Option("desc", help="Sort order for URLs: 'asc' (ascending) or 'desc' (descending)"),
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


@app.command()
def ebook2md(
    epub_path: str = typer.Argument(..., help="Path to the EPUB file"),
    output_dir: str = typer.Option(None, help="Output directory for markdown files (optional)"),
    extract_images: bool = typer.Option(True, help="Extract images from EPUB"),
    generate_toc: bool = typer.Option(True, help="Generate table of contents"),
):
    """Convert EPUB ebook to markdown format with optional image and TOC extraction.

    Extracts chapters from EPUB file and converts them to individual markdown files.
    Optionally extracts images and generates a table of contents.

    Args:
        epub_path: Path to the EPUB file to convert.
        output_dir: Output directory for markdown files. If not provided, uses EPUB directory.
        extract_images: If True, extracts all images from the EPUB to an 'assets' folder.
        generate_toc: If True, generates a table of contents file.

    Raises:
        typer.Exit: If EPUB file doesn't exist or conversion fails.
    """
    epub_file = Path(epub_path)
    if not epub_file.exists():
        console.print(f"[red]Error: EPUB file not found: {epub_path}[/red]")
        raise typer.Exit(1)

    try:
        if not output_dir:
            output_dir = epub_file.parent / epub_file.stem
        else:
            output_dir = Path(output_dir)

        console.print("Converting EPUB to markdown...")
        epub_to_md(str(epub_path), str(output_dir))

        if extract_images:
            console.print("Extracting images...")
            image_output_dir = output_dir / "assets"
            extract_imgs_from_epub(str(epub_path), str(image_output_dir))
            console.print(f"Images extracted to: {image_output_dir}")

        if generate_toc:
            console.print("Generating table of contents...")
            toc_path = output_dir / f"{epub_file.stem}_toc.txt"
            extract_toc(str(epub_path), str(toc_path))
            console.print(f"Table of contents saved to: {toc_path}")

        console.print("Successfully converted EPUB to markdown")
        console.print(f"Markdown files saved to: {output_dir}")

        # Move the EPUB file to the output directory
        epub_output_path = output_dir / epub_file.name
        epub_file.rename(epub_output_path)
        console.print(f"EPUB file moved to: {epub_output_path}")

    except Exception as e:
        console.print(f"Error converting EPUB: {str(e)}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
