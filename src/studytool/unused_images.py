"""Find image files that are not referenced by their Markdown document."""

import subprocess
from pathlib import Path

import typer


def find_unused_images(markdown_paths: list[str | Path]) -> dict[Path, list[Path]]:
    """Return images absent from each Markdown file's text."""
    unused: dict[Path, list[Path]] = {}
    for markdown_path in map(Path, markdown_paths):
        image_directory = markdown_path.parent / "imgs" / markdown_path.stem
        if not image_directory.is_dir():
            continue
        content = markdown_path.read_text(encoding="utf-8")
        unmatched = [
            image_path
            for image_path in sorted(image_directory.iterdir())
            if image_path.is_file() and image_path.name not in content
        ]
        if unmatched:
            unused[markdown_path] = unmatched
    return unused


def remove_unused_images(image_paths: list[str | Path]) -> list[Path]:
    """Stage and delete image files, tolerating files outside Git repositories."""
    removed: list[Path] = []
    for image_path in map(Path, image_paths):
        try:
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(image_path.parent),
                    "rm",
                    "--cached",
                    "--",
                    image_path.name,
                ],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            pass
        image_path.unlink(missing_ok=True)
        removed.append(image_path)
    return removed


def check_unused_images_command(
    markdown_paths: list[Path] = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Markdown files whose image directories should be checked.",
    ),
    fix: bool = typer.Option(False, "--fix", help="Delete images that are not referenced."),
) -> None:
    """Check for and optionally delete unused Markdown images."""
    unused = find_unused_images(markdown_paths)
    if fix:
        image_paths = [image_path for paths in unused.values() for image_path in paths]
        for image_path in remove_unused_images(image_paths):
            typer.echo(f"Removed: {image_path}")
        return

    for markdown_path, image_paths in unused.items():
        for image_path in image_paths:
            typer.echo(f"{markdown_path}: unused image '{image_path.name}' " f"in {image_path.parent}")

    if unused:
        typer.echo("\nTo clean unused images, run:")
        for markdown_path in unused:
            typer.echo(f"  stt markdown check-unused-images --fix {markdown_path}")
        raise typer.Exit(1)
