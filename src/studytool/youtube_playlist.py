import typer
import youtube_dl


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
