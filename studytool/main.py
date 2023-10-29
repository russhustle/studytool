import typer

from .pdf_merge import merge_pdfs_in_dir
from .slides2md import Slide2md
from .youtube_playlist import playlist_titles

app = typer.Typer()


@app.command()
def playlist(
    playlist: str = typer.Argument(default=None, help="Path to YouTube Playlost URL."),
    playlist_number: int = typer.Option(default=200, help="Number of videos to extract."),
):
    """Print YouTube playlist titles."""
    playlist_titles(url=playlist, number=playlist_number)


@app.command()
def course(
    course: str = typer.Argument(
        default="./",
        help="Path to the course folder.",
    ),
):
    """Convert slides to markdown."""
    slide2md = Slide2md(course_folder=course)
    slide2md.run()


@app.command()
def pdfmerge(
    dir_path: str = typer.Argument(default=None, help="Path to the directory"),
    output_file: str = typer.Option(default="merged_pdf.pdf", help="Merged PDF"),
):
    """Merge PDF files in a directory."""
    merge_pdfs_in_dir(dir_path=dir_path, output_file=output_file)


if __name__ == "__main__":
    app()
