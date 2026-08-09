"""In-place text formatting helpers."""

import re
from pathlib import Path

import typer

TIMESTAMP_RE = re.compile(r"(?m)^[0-9]{2}:[0-9]{2}:[0-9]{2}[^\S\r\n]*")


def double_blank_lines(file_path: str | Path) -> None:
    """Add two newline characters to every blank line."""
    path = Path(file_path)
    with path.open("r", encoding="utf-8", newline="") as source:
        content = source.read()
    lines = content.splitlines(keepends=True)
    expanded = [line * 3 if line in {"\n", "\r\n"} else line for line in lines]
    with path.open("w", encoding="utf-8", newline="") as destination:
        destination.write("".join(expanded))


def transcript_to_paragraphs(file_path: str | Path) -> None:
    """Remove leading timestamps and join transcript lines with spaces."""
    path = Path(file_path)
    content = path.read_text(encoding="utf-8")
    content = content.removeprefix("\ufeff")
    content = TIMESTAMP_RE.sub("", content)
    path.write_text(re.sub(r"\r?\n", " ", content), encoding="utf-8")


def double_newlines_command(
    file_path: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        writable=True,
        help="Text or Markdown file to update in place.",
    ),
) -> None:
    """Add two line breaks to every blank line."""
    double_blank_lines(file_path)
    typer.echo(f"Updated: {file_path}")


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
