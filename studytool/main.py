import typer

from .pdf_merge import merge_pdfs_in_dir
from .slides2md import Slide2md
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


if __name__ == "__main__":
    app()
