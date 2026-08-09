"""Convert timestamped transcripts into paragraph text from the text CLI group."""

import re
from pathlib import Path

import typer

TIMESTAMP_RE = re.compile(r"(?m)^[0-9]{2}:[0-9]{2}:[0-9]{2}[^\S\r\n]*")


def transcript_to_paragraphs(file_path: str | Path) -> None:
    """Remove leading timestamps and join transcript lines with spaces."""
    path = Path(file_path)
    content = path.read_text(encoding="utf-8")
    content = content.removeprefix("\ufeff")
    content = TIMESTAMP_RE.sub("", content)
    path.write_text(re.sub(r"\r?\n", " ", content), encoding="utf-8")


def transcript_to_paragraphs_command(
    file_path: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        writable=True,
        help="Transcript .txt or .md file to update in place.",
    ),
) -> None:
    """Remove timestamps and join transcript lines into a paragraph."""
    if file_path.suffix.lower() not in {".txt", ".md"}:
        typer.echo("Error: Transcript must be a .txt or .md file.", err=True)
        raise typer.Exit(1)
    transcript_to_paragraphs(file_path)
    typer.echo(f"Updated: {file_path}")
