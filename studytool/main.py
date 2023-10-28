import typer

from .slides2md import Slide2md
from .youtube_playlist import playlist_titles

app = typer.Typer()


@app.command()
def main(
    course: str = typer.Option(default=None, help="Path to course folder."),
    playlist: str = typer.Option(default=None, help="Path to YouTube Playlost URL."),
    playlist_number: int = typer.Option(default=200, help="Number of videos to extract."),
):
    """Mian Function for the Study Tool."""
    if course:
        """Convert slides to markdown."""
        slide2md = Slide2md(course_folder=course)
        slide2md.run()

    if playlist:
        """Print YouTube playlist titles."""
        playlist_titles(url=playlist, number=playlist_number)


if __name__ == "__main__":
    app()
