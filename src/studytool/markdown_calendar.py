"""Generate an HTML calendar of Markdown files by last commit date."""

import calendar
import html
import subprocess
import webbrowser
from collections import defaultdict
from datetime import date
from pathlib import Path

import typer

CALENDAR_STYLES = """
body { font-family: -apple-system, sans-serif; background:#f5f5f7; padding:20px; }
h1 { color:#333; }
.calendar { display:grid; grid-template-columns:repeat(7,1fr); gap:6px; max-width:1000px; }
.day-header { font-weight:bold; text-align:center; padding:8px; background:#333; color:#fff; border-radius:4px; }
.day { background:#fff; border-radius:6px; padding:6px; min-height:90px; font-size:12px; box-shadow:0 1px 3px rgba(0,0,0,0.1); }
.day.empty { background:transparent; box-shadow:none; }
.date-num { font-weight:bold; color:#0070c9; margin-bottom:4px; }
.file { display:block; color:#333; font-size:11px; margin:2px 0; word-break:break-all; }
.month-title { margin-top:30px; font-size:20px; color:#222; }
""".strip()


def _git(repo: Path, *arguments: str) -> str:
    """Run a Git command and return its standard output."""
    result = subprocess.run(
        ["git", "-C", str(repo), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def collect_markdown_commit_dates(repo: str | Path) -> list[tuple[date, str]]:
    """Collect tracked Markdown basenames and their most recent commit dates."""
    root = Path(repo)
    records: list[tuple[date, str]] = []
    for relative_path in _git(root, "ls-files", "--", "*.md").splitlines():
        committed = _git(
            root,
            "log",
            "-1",
            "--format=%ad",
            "--date=short",
            "--",
            relative_path,
        ).strip()
        if committed:
            records.append((date.fromisoformat(committed), Path(relative_path).name))
    return sorted(records, reverse=True)


def render_markdown_calendar(records: list[tuple[date, str]]) -> str:
    """Render Markdown commit records as a standalone HTML calendar."""
    by_month: dict[tuple[int, int], dict[int, list[str]]] = defaultdict(lambda: defaultdict(list))
    for committed, filename in records:
        by_month[(committed.year, committed.month)][committed.day].append(filename)

    sections: list[str] = []
    for (year, month), days in sorted(by_month.items(), reverse=True):
        sections.append(f'<h2 class="month-title">{calendar.month_name[month]} {year}</h2>')
        sections.append('<div class="calendar">')
        sections.extend(
            f'<div class="day-header">{name}</div>' for name in ("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")
        )
        first_weekday, days_in_month = calendar.monthrange(year, month)
        sections.extend('<div class="day empty"></div>' for _ in range((first_weekday + 1) % 7))
        for day_number in range(1, days_in_month + 1):
            sections.append(f'<div class="day"><div class="date-num">{day_number}</div>')
            sections.extend(
                f'<span class="file">📄 {html.escape(filename)}</span>' for filename in sorted(days.get(day_number, []))
            )
            sections.append("</div>")
        sections.append("</div>")

    body = "\n".join(sections)
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Markdown Calendar</title>
<style>
{CALENDAR_STYLES}
</style>
</head>
<body>
<h1>📅 Markdown Files by Last Commit</h1>
{body}
</body>
</html>
"""


def generate_markdown_calendar(repo: str | Path, output: str | Path) -> Path:
    """Generate a Markdown commit calendar and return the output path."""
    output_path = Path(output)
    records = collect_markdown_commit_dates(repo)
    output_path.write_text(render_markdown_calendar(records), encoding="utf-8")
    return output_path


def markdown_calendar_command(
    directory: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Git repository containing the Markdown files.",
    ),
    output: Path = typer.Option(
        Path("md_calendar.html"),
        "--output",
        "-o",
        help="HTML file to create.",
    ),
    open_calendar: bool = typer.Option(
        True,
        "--open/--no-open",
        help="Open the generated calendar in the default browser.",
    ),
) -> None:
    """Create an HTML calendar from Markdown files' last commits."""
    try:
        output_path = generate_markdown_calendar(directory, output)
    except (FileNotFoundError, subprocess.CalledProcessError, ValueError) as error:
        typer.echo(f"Error: Could not read Markdown history: {error}", err=True)
        raise typer.Exit(1) from error

    typer.echo(f"Generated: {output_path}")
    if open_calendar:
        webbrowser.open(output_path.resolve().as_uri())
