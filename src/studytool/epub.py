import os
import re
from pathlib import Path

import ebooklib
import typer
from bs4 import BeautifulSoup
from ebooklib import epub
from PIL import Image
from rich.console import Console

console = Console()


def epub_to_chapters(epub_path):
    """
    Extract chapters from an EPUB file.

    Args:
        epub_path (str): Path to the EPUB file

    Returns:
        list: List of (title, content) tuples for each chapter
    """
    book = epub.read_epub(epub_path)
    chapters = []

    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            content = item.get_content().decode("utf-8")
            soup = BeautifulSoup(content, "html.parser")

            title = ""
            title_tag = soup.find("h1")
            if title_tag:
                title = title_tag.get_text().strip()
            else:
                title_tag = soup.find(["h2", "h3", "title"])
                if title_tag:
                    title = title_tag.get_text().strip()

            if not title:
                title = item.get_id() or os.path.basename(item.get_name())

            html_content = str(soup)
            chapters.append((title, html_content))

    return chapters


def save_chapters_as_markdown(chapters, output_dir):
    """
    Save each chapter as a separate markdown file.

    Args:
        chapters (list): List of (title, content) tuples
        output_dir (str): Directory to save markdown files
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for i, (title, html_content) in enumerate(chapters):
        safe_title = re.sub(r"[^\w\s-]", "", title).strip().replace(" ", "_")
        if not safe_title:
            safe_title = f"chapter_{i + 1}"

        filename = f"{i + 1:02d}_{safe_title}.md"
        soup = BeautifulSoup(html_content, "html.parser")
        markdown_content = f"# {title}\n\n"

        for element in soup.find_all(
            [
                "p",
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "h6",
                "ul",
                "ol",
                "li",
                "blockquote",
                "pre",
                "code",
            ]
        ):
            if element.name.startswith("h"):
                level = int(element.name[1])
                markdown_content += f"{'#' * level} {element.get_text().strip()}\n\n"
            elif element.name == "p":
                markdown_content += f"{element.get_text().strip()}\n\n"
            elif element.name == "li":
                markdown_content += f"* {element.get_text().strip()}\n"
            elif element.name == "pre" or element.name == "code":
                markdown_content += f"```\n{element.get_text().strip()}\n```\n\n"
            elif element.name == "blockquote":
                markdown_content += f"> {element.get_text().strip()}\n\n"

        output_path = os.path.join(output_dir, filename)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        print(f"Saved chapter: {title} to {filename}")


def epub_to_markdown(epub_path, output_dir):
    """
    Process an EPUB file and save each chapter as a separate markdown file.

    Args:
        epub_path (str): Path to the EPUB file
        output_dir (str): Directory to save markdown files
    """
    print(f"Processing {epub_path}...")
    chapters = epub_to_chapters(epub_path)
    print(f"Found {len(chapters)} chapters.")
    save_chapters_as_markdown(chapters, output_dir)
    print(f"Processing complete. Files saved to {output_dir}")


def extract_images_from_epub(epub_path, output_dir):
    """
    Extract images from an EPUB file and save them to a folder.

    Args:
        epub_path (str): Path to the EPUB file
        output_dir (str): Directory to save images
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    book = epub.read_epub(epub_path)

    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_IMAGE:
            image_content = item.get_content()
            image_name = os.path.basename(item.get_name())
            image_path = os.path.join(output_dir, image_name)

            with open(image_path, "wb") as f:
                f.write(image_content)

            print(f"Saved image: {image_name}")


def resize_images_in_folder(folder_path: str | Path, target_width: int) -> list[Path]:
    """Resize supported images proportionally and return the updated paths."""
    if target_width <= 0:
        raise ValueError("target width must be greater than zero")

    folder = Path(folder_path)
    resized_paths = []
    for image_path in sorted(folder.iterdir(), key=lambda path: path.name.casefold()):
        if not image_path.is_file() or image_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".gif"}:
            continue
        with Image.open(image_path) as image:
            target_height = max(1, round(image.height * (target_width / image.width)))
            resized_image = image.resize((target_width, target_height))
            try:
                resized_image.save(image_path)
            finally:
                resized_image.close()
        resized_paths.append(image_path)
        print(f"Resized image: {image_path.name}")
    return resized_paths


def extract_toc(epub_path, output_path=None):
    """
    Extract the table of contents from an EPUB file and save it to a text file.

    Args:
        epub_path (str): Path to the EPUB file
        output_path (str, optional): Path to save the TOC. If None, uses the EPUB filename with .txt extension

    Returns:
        str: Path to the saved TOC file
    """
    try:
        if output_path is None:
            base_name = os.path.splitext(os.path.basename(epub_path))[0]
            output_path = f"{base_name}_toc.txt"

        book = epub.read_epub(epub_path)
        toc = book.toc

        if not toc:
            print("No table of contents found in this EPUB.")
            return None

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"Table of Contents for: {os.path.basename(epub_path)}\n")
            f.write("=" * 50 + "\n\n")

            def write_toc_items(items, level=0):
                """Write nested ebooklib TOC items with Markdown indentation."""
                for item in items:
                    if isinstance(item, tuple) and len(item) >= 2:
                        if isinstance(item[0], epub.Link):
                            title = item[0].title
                            f.write("  " * level + f"- {title}\n")
                        elif isinstance(item[0], epub.Section) and hasattr(item[0], "title"):
                            title = item[0].title
                            f.write("  " * level + f"- {title}\n")

                        if len(item) > 1 and isinstance(item[1], list):
                            write_toc_items(item[1], level + 1)

                    elif isinstance(item, epub.Link):
                        f.write("  " * level + f"- {item.title}\n")

                    elif isinstance(item, epub.Section) and hasattr(item, "title"):
                        f.write("  " * level + f"- {item.title}\n")

                    elif isinstance(item, list):
                        write_toc_items(item, level)

            write_toc_items(toc)

        print(f"Table of contents saved to: {output_path}")
        return output_path

    except Exception as e:
        print(f"Error processing EPUB file: {e}")
        return None


def convert_epub_command(
    epub_path: str = typer.Argument(..., help="Path to the EPUB file"),
    output_dir: str = typer.Option(
        None,
        "--output",
        "-o",
        "--output-dir",
        help="Output directory for Markdown files.",
    ),
    extract_images: bool = typer.Option(True, help="Extract images from EPUB"),
    image_width: int | None = typer.Option(
        None,
        min=1,
        help="Resize extracted images to this width in pixels.",
    ),
    generate_toc: bool = typer.Option(True, help="Generate table of contents"),
):
    """Convert EPUB ebook to markdown format with optional image and TOC extraction.

    Extracts chapters from EPUB file and converts them to individual markdown files.
    Optionally extracts images and generates a table of contents.

    Args:
        epub_path: Path to the EPUB file to convert.
        output_dir: Output directory for markdown files. If not provided, uses EPUB directory.
        extract_images: If True, extracts all images from the EPUB to an 'assets' folder.
        image_width: Optional target width for extracted images.
        generate_toc: If True, generates a table of contents file.

    Raises:
        typer.Exit: If EPUB file doesn't exist or conversion fails.
    """
    if image_width is not None and not extract_images:
        raise typer.BadParameter("requires image extraction", param_hint="--image-width")

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
        epub_to_markdown(str(epub_path), str(output_dir))

        if extract_images:
            console.print("Extracting images...")
            image_output_dir = output_dir / "assets"
            extract_images_from_epub(str(epub_path), str(image_output_dir))
            if image_width is not None:
                console.print(f"Resizing images to {image_width}px...")
                resize_images_in_folder(image_output_dir, image_width)
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
