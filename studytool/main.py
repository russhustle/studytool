from .slides2md import Slide2md
import typer

app = typer.Typer()


@app.command()
def main(
    course: str = typer.Option(default="./", help="Path to course folder."),
):
    """Convert slides to markdown."""
    slide2md = Slide2md(course_folder=course)
    slide2md.run()


if __name__ == "__main__":
    app()
