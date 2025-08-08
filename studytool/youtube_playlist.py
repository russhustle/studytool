import typer
import youtube_dl

app = typer.Typer()


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


@app.command()
def playlist(
    playlist: str = typer.Argument(default=None, help="Path to YouTube Playlist URL."),
    playlist_number: int = typer.Option(default=200, help="Number of videos to extract."),
):
    """Extract video titles from a YouTube playlist.

    Args:
        playlist: YouTube playlist URL to process.
        playlist_number: Maximum number of video titles to extract from the playlist.
    """
    playlist_titles(url=playlist, number=playlist_number)
