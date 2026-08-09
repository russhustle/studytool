"""Expand blank lines in text files from the text CLI group."""

from pathlib import Path

import typer


def double_blank_lines(file_path: str | Path) -> None:
    """Add two newline characters to every blank line."""
    path = Path(file_path)
    with path.open("r", encoding="utf-8", newline="") as source:
        content = source.read()
    lines = content.splitlines(keepends=True)
    expanded = [line * 3 if line in {"\n", "\r\n"} else line for line in lines]
    with path.open("w", encoding="utf-8", newline="") as destination:
        destination.write("".join(expanded))


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
