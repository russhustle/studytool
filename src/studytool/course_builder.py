import os
import tempfile
from pathlib import Path

import typer
from pdf2image import convert_from_path
from rich.progress import track

from .course_markdown import PageContentOrder, compose_course_markdown
from .pdf_text import count_pdf_pages, extract_selectable_page_texts


def _write_text_atomic(path: Path, content: str) -> None:
    """Replace a text file atomically, creating its parent directory first."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


class CourseBuilder:
    """Orchestrate course PDF images, Markdown, and MkDocs navigation."""

    def __init__(
        self,
        course_folder: str | Path,
        dpi: int = 100,
        include_text: bool = False,
        page_order: PageContentOrder = PageContentOrder.IMAGE_TEXT,
    ):
        self.course_folder = Path(course_folder)
        self.slides_folder = self.course_folder / "slides"
        self.docs_folder = self.course_folder / "docs"
        self.imgs_folder = self.docs_folder / "imgs"
        self.index_file = self.docs_folder / "README.md"
        self.index_yaml = self.course_folder / "mkdocs.yaml"
        self.dpi = dpi
        self.include_text = include_text
        self.page_order = page_order

    def validate_course(self) -> None:
        """Ensure the course and its slides directory exist."""
        if not self.course_folder.is_dir():
            raise ValueError(f"Course folder not found: {self.course_folder}")
        if not self.slides_folder.is_dir():
            raise ValueError(f"Slides folder not found: {self.slides_folder}")

    def prepare_output_directories(self) -> None:
        """Create the output tree and initial course index when needed."""
        self.imgs_folder.mkdir(parents=True, exist_ok=True)
        if not self.index_file.exists():
            _write_text_atomic(self.index_file, "Course Index\n===\n\n")

    def discover_pdfs(self) -> list[Path]:
        """Return course PDFs in a deterministic case-insensitive order."""
        return sorted(
            (path for path in self.slides_folder.iterdir() if path.is_file() and path.suffix.lower() == ".pdf"),
            key=lambda path: path.name.casefold(),
        )

    def pdf_to_image(self, pdf_path: Path) -> None:
        """Render every PDF page as a numbered JPEG."""
        images = convert_from_path(pdf_path=str(pdf_path), dpi=self.dpi)
        if not images:
            raise RuntimeError(f"PDF has no renderable pages: {pdf_path}")

        image_directory = self.imgs_folder / pdf_path.stem
        image_directory.mkdir(parents=True, exist_ok=True)
        for index, image in track(
            enumerate(images, start=1),
            description=f"Converting {pdf_path.stem}",
            total=len(images),
        ):
            image.save(fp=image_directory / f"{index:03}.jpg")

    def ensure_page_images(self, pdf_path: Path, page_count: int) -> tuple[list[Path], bool]:
        """Return every expected page image, rendering missing images when needed."""
        if page_count <= 0:
            raise ValueError(f"PDF has no pages: {pdf_path}")

        image_directory = self.imgs_folder / pdf_path.stem
        expected_images = [image_directory / f"{page:03}.jpg" for page in range(1, page_count + 1)]
        rendered = not all(image.is_file() for image in expected_images)
        if rendered:
            self.pdf_to_image(pdf_path)

        missing_images = [image for image in expected_images if not image.is_file()]
        if missing_images:
            missing_names = ", ".join(image.name for image in missing_images)
            raise RuntimeError(f"Missing rendered page images for {pdf_path.name}: {missing_names}")

        return expected_images, rendered

    def create_md(self, pdf_path: Path, image_paths: list[Path], page_texts: list[str] | None) -> None:
        """Write one complete Markdown document for a PDF."""
        relative_images = [image.relative_to(self.docs_folder).as_posix() for image in image_paths]
        content = compose_course_markdown(
            pdf_path.stem,
            relative_images,
            page_texts,
            page_order=self.page_order,
        )
        _write_text_atomic(self.docs_folder / f"{pdf_path.stem}.md", content)

    def process_pdf(self, pdf_path: Path) -> None:
        """Update the images and Markdown for one course PDF."""
        page_texts = extract_selectable_page_texts(pdf_path) if self.include_text else None
        page_count = len(page_texts) if page_texts is not None else count_pdf_pages(pdf_path)
        image_paths, rendered = self.ensure_page_images(pdf_path, page_count)
        markdown_path = self.docs_folder / f"{pdf_path.stem}.md"

        if self.include_text or rendered or not markdown_path.exists():
            self.create_md(pdf_path, image_paths, page_texts)

    def update_index_yaml(self) -> None:
        """Update the MkDocs navigation file."""
        markdown_files = sorted(
            (path for path in self.docs_folder.glob("*.md") if path.name != self.index_file.name),
            key=lambda path: path.name.casefold(),
        )
        lines = [f"site_name: {self.course_folder.name}", "", "nav:", "   - Home: README.md"]
        for markdown_file in markdown_files:
            title = markdown_file.stem.replace("-", " ").title()
            lines.append(f"   - {title}: {markdown_file.name}")
        _write_text_atomic(self.index_yaml, "\n".join(lines) + "\n")

    def run(self) -> None:
        """Process all course PDFs."""
        self.validate_course()
        pdfs = self.discover_pdfs()
        if not pdfs:
            raise ValueError(f"No PDF files found in: {self.slides_folder}")

        self.prepare_output_directories()
        for pdf_path in pdfs:
            self.process_pdf(pdf_path)
        self.update_index_yaml()
        print("Done!")

    def update_yaml_only(self) -> None:
        """Refresh only the course index and MkDocs navigation."""
        self.validate_course()
        self.prepare_output_directories()
        self.update_index_yaml()


def build_course_command(
    course: str = typer.Argument(default="./", help="Path to the course folder."),
    update_yaml_only: bool = typer.Option(default=False, help="Update MKDocs YAML Only"),
    dpi: int = typer.Option(default=100, min=1, help="DPI for PDF to image conversion"),
    include_text: bool = typer.Option(
        default=False,
        help="Include each PDF page's selectable text in Markdown.",
    ),
    page_order: PageContentOrder = typer.Option(
        default=PageContentOrder.IMAGE_TEXT,
        help="Order of each page's image and selectable text.",
    ),
):
    """Process course PDFs into page images and Markdown documents."""
    if include_text and update_yaml_only:
        raise typer.BadParameter("cannot be used with --update-yaml-only", param_hint="--include-text")
    if not include_text and page_order == PageContentOrder.TEXT_IMAGE:
        raise typer.BadParameter("requires --include-text", param_hint="--page-order")

    converter = CourseBuilder(
        course_folder=course,
        dpi=dpi,
        include_text=include_text,
        page_order=page_order,
    )
    try:
        converter.update_yaml_only() if update_yaml_only else converter.run()
    except Exception as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from None
