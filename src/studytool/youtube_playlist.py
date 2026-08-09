import math
import re

import typer
import youtube_dl
import yt_dlp


def playlist_titles(url: str, number: int = 200) -> None:
    """Print YouTube playlist titles."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
        "playlistend": number,  # Set the number of videos to retrieve
    }

    with youtube_dl.YoutubeDL(params=ydl_opts) as ydl:
        playlist_info = ydl.extract_info(url=url, download=False)
        video_titles = [video["title"] for video in playlist_info["entries"]]
        for title in video_titles:
            print(title)


def playlist_titles_command(
    playlist: str = typer.Argument(..., help="YouTube playlist URL."),
    playlist_number: int = typer.Option(
        200,
        "--limit",
        "-n",
        "--playlist-number",
        min=1,
        help="Maximum number of video titles to print.",
    ),
):
    """Extract video titles from a YouTube playlist.

    Args:
        playlist: YouTube playlist URL to process.
        playlist_number: Maximum number of video titles to extract from the playlist.
    """
    playlist_titles(url=playlist, number=playlist_number)


def format_duration(entry: dict) -> str:
    """Format a playlist entry's duration as minutes or hours."""
    if entry.get("duration_string"):
        return str(entry["duration_string"])
    duration = entry.get("duration")
    if not isinstance(duration, (int, float)) or isinstance(duration, bool):
        return "?"
    seconds = math.floor(duration)
    minutes, remaining_seconds = divmod(seconds, 60)
    hours, remaining_minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{remaining_minutes:02d}:{remaining_seconds:02d}"
    return f"{minutes}:{remaining_seconds:02d}"


def playlist_table(url: str, number: int | None = None) -> str:
    """Return a YouTube playlist as a Markdown table."""
    normalized_url = re.sub(r"\\([?=&])", r"\1", url)
    options: dict[str, object] = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
    }
    if number is not None:
        options["playlistend"] = number
    with yt_dlp.YoutubeDL(options) as downloader:
        playlist_info = downloader.extract_info(normalized_url, download=False)

    rows = ["| name | 📽️ | length |", "|---|---|---|"]
    for entry in playlist_info.get("entries", []):
        if not isinstance(entry, dict):
            continue
        title = entry.get("title")
        video_id = entry.get("id")
        if not isinstance(title, str) or not title or not isinstance(video_id, str) or not video_id:
            continue
        escaped_title = title.replace("|", r"\|")
        rows.append(
            f"| {escaped_title} | " f"[📽️](https://www.youtube.com/watch?v={video_id}) | " f"{format_duration(entry)} |"
        )
    return "\n".join(rows)


def playlist_table_command(
    playlist: str = typer.Argument(..., help="YouTube playlist URL."),
    playlist_number: int | None = typer.Option(
        None,
        "--limit",
        "-n",
        min=1,
        help="Maximum number of playlist entries to print.",
    ),
) -> None:
    """Print a YouTube playlist as a Markdown table."""
    typer.echo(playlist_table(playlist, playlist_number))
