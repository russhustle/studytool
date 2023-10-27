from .slides2md import Slide2md
import typer

app = typer.Typer()


@app.command()
def main(
    course_folder: str = "./",
):
    """Convert slides to markdown."""
    slide2md = Slide2md(course_folder=course_folder)
    slide2md.run()


if __name__ == "__main__":
    app()
