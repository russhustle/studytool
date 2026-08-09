import subprocess
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from typer.testing import CliRunner

from studytool.cli import app
from studytool.markdown_calendar import (
    collect_markdown_commit_dates,
    generate_markdown_calendar,
    render_markdown_calendar,
)
from studytool.markdown_unused_images import find_unused_images, remove_unused_images
from studytool.text_double_newlines import double_blank_lines
from studytool.text_transcript_to_paragraphs import transcript_to_paragraphs
from studytool.youtube_playlist import format_duration, playlist_table


class TextFormattingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_doubles_unix_and_windows_blank_lines(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            text_path = Path(temporary_directory) / "notes.txt"
            text_path.write_bytes(b"One\r\n\r\nTwo\n\n")

            double_blank_lines(text_path)

            self.assertEqual(text_path.read_bytes(), b"One\r\n\r\n\r\n\r\nTwo\n\n\n\n")

    def test_removes_transcript_timestamps_bom_and_newlines(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            transcript_path = Path(temporary_directory) / "talk.md"
            transcript_path.write_text(
                "\ufeff00:00:01\tFirst line\r\n00:01:30  Second line\nLast line\n",
                encoding="utf-8",
            )

            result = self.runner.invoke(
                app,
                ["text", "transcript-to-paragraphs", str(transcript_path)],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertEqual(
                transcript_path.read_text(encoding="utf-8"),
                "First line Second line Last line ",
            )

    def test_text_commands_update_files_and_reject_transcript_extension(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            text_path = directory / "notes.txt"
            text_path.write_text("One\n\nTwo\n", encoding="utf-8")
            double_result = self.runner.invoke(app, ["text", "double-newlines", str(text_path)])

            invalid_path = directory / "talk.csv"
            invalid_path.write_text("00:00:01,Hello", encoding="utf-8")
            invalid_result = self.runner.invoke(
                app,
                ["text", "transcript-to-paragraphs", str(invalid_path)],
            )

            updated_content = text_path.read_text(encoding="utf-8")

        self.assertEqual(double_result.exit_code, 0, double_result.output)
        self.assertEqual(updated_content, "One\n\n\n\nTwo\n")
        self.assertEqual(invalid_result.exit_code, 1)
        self.assertIn(".txt or .md", invalid_result.output)

    def test_transcript_helper_accepts_plain_text_without_timestamps(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            text_path = Path(temporary_directory) / "plain.txt"
            text_path.write_text("First\nSecond", encoding="utf-8")

            transcript_to_paragraphs(text_path)

            self.assertEqual(text_path.read_text(encoding="utf-8"), "First Second")


class UnusedImageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_finds_only_unreferenced_files(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            markdown_path = root / "lesson.md"
            image_directory = root / "imgs" / "lesson"
            image_directory.mkdir(parents=True)
            markdown_path.write_text("![Used](imgs/lesson/used.jpg)", encoding="utf-8")
            (image_directory / "used.jpg").touch()
            unused_path = image_directory / "unused.png"
            unused_path.touch()
            (image_directory / "nested").mkdir()

            unused = find_unused_images([markdown_path])

            self.assertEqual(unused, {markdown_path: [unused_path]})
            no_images = root / "other.md"
            no_images.write_text("No images", encoding="utf-8")
            self.assertEqual(find_unused_images([no_images]), {})

    def test_remove_stages_image_then_deletes_it(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            image_path = Path(temporary_directory) / "unused.jpg"
            image_path.touch()

            with patch("studytool.markdown_unused_images.subprocess.run") as run:
                removed = remove_unused_images([image_path])

            self.assertEqual(removed, [image_path])
            self.assertFalse(image_path.exists())
            run.assert_called_once_with(
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

    def test_remove_still_deletes_when_git_is_unavailable(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            image_path = Path(temporary_directory) / "unused.jpg"
            image_path.touch()

            with patch(
                "studytool.markdown_unused_images.subprocess.run",
                side_effect=FileNotFoundError,
            ):
                remove_unused_images([image_path])

            self.assertFalse(image_path.exists())

    def test_check_file_keeps_images_when_user_declines(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            markdown_path = root / "lesson.md"
            image_directory = root / "imgs" / "lesson"
            image_directory.mkdir(parents=True)
            markdown_path.write_text("No image references", encoding="utf-8")
            unused_path = image_directory / "unused.jpg"
            unused_path.touch()

            result = self.runner.invoke(
                app,
                ["markdown", "check-unused-images", str(markdown_path)],
                input="n\n",
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("unused image 'unused.jpg'", result.output)
            self.assertIn("Remove 1 unused image?", result.output)
            self.assertIn("Kept 1 unused image.", result.output)
            self.assertTrue(unused_path.exists())

    def test_check_file_removes_images_when_user_confirms(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            markdown_path = root / "lesson.md"
            image_directory = root / "imgs" / "lesson"
            image_directory.mkdir(parents=True)
            markdown_path.write_text("No image references", encoding="utf-8")
            unused_path = image_directory / "unused.jpg"
            unused_path.touch()

            result = self.runner.invoke(
                app,
                ["markdown", "check-unused-images", str(markdown_path)],
                input="y\n",
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("Removed:", result.output)
            self.assertFalse(unused_path.exists())

    def test_fix_deletes_without_prompt(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            markdown_path = root / "lesson.md"
            image_directory = root / "imgs" / "lesson"
            image_directory.mkdir(parents=True)
            markdown_path.write_text("No image references", encoding="utf-8")
            unused_path = image_directory / "unused.jpg"
            unused_path.touch()

            fixed = self.runner.invoke(
                app,
                ["markdown", "check-unused-images", "--fix", str(markdown_path)],
            )

            self.assertEqual(fixed.exit_code, 0, fixed.output)
            self.assertNotIn("Remove 1", fixed.output)
            self.assertFalse(unused_path.exists())

    def test_rejects_directory_input(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            result = self.runner.invoke(
                app,
                ["markdown", "check-unused-images", temporary_directory],
            )

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("File", result.output)

    def test_check_reports_when_all_images_are_referenced(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            markdown_path = root / "lesson.md"
            image_directory = root / "imgs" / "lesson"
            image_directory.mkdir(parents=True)
            markdown_path.write_text("![Used](imgs/lesson/used.jpg)", encoding="utf-8")
            (image_directory / "used.jpg").touch()

            result = self.runner.invoke(
                app,
                ["markdown", "check-unused-images", str(markdown_path)],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertEqual(result.output, "No unused images found.\n")


class MarkdownCalendarTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_collects_only_committed_markdown_files(self) -> None:
        with patch(
            "studytool.markdown_calendar._git",
            side_effect=["docs/lesson.md\nREADME.md\n", "2026-08-09\n", "\n"],
        ) as git:
            records = collect_markdown_commit_dates("repo")

        self.assertEqual(records, [(date(2026, 8, 9), "lesson.md")])
        self.assertEqual(git.call_count, 3)

    def test_renders_months_days_and_escaped_filenames(self) -> None:
        rendered = render_markdown_calendar(
            [
                (date(2026, 8, 9), "lesson & notes.md"),
                (date(2026, 7, 1), "older.md"),
            ]
        )

        self.assertIn("August 2026", rendered)
        self.assertIn("July 2026", rendered)
        self.assertLess(rendered.index("August 2026"), rendered.index("July 2026"))
        self.assertIn("lesson &amp; notes.md", rendered)
        self.assertIn('<div class="date-num">9</div>', rendered)

    def test_generates_calendar_file(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "calendar.html"
            with patch(
                "studytool.markdown_calendar.collect_markdown_commit_dates",
                return_value=[(date(2026, 8, 9), "lesson.md")],
            ):
                generated = generate_markdown_calendar("repo", output_path)

            self.assertEqual(generated, output_path)
            self.assertIn("lesson.md", output_path.read_text(encoding="utf-8"))

    def test_calendar_command_opens_output_and_reports_git_errors(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            output_path = directory / "calendar.html"
            with (
                patch(
                    "studytool.markdown_calendar.generate_markdown_calendar",
                    return_value=output_path,
                ),
                patch("studytool.markdown_calendar.webbrowser.open") as open_browser,
            ):
                success = self.runner.invoke(
                    app,
                    [
                        "markdown",
                        "calendar",
                        str(directory),
                        "--output",
                        str(output_path),
                    ],
                )
                no_open = self.runner.invoke(
                    app,
                    ["markdown", "calendar", str(directory), "--no-open"],
                )

            open_browser.assert_called_once_with(output_path.resolve().as_uri())
            with patch(
                "studytool.markdown_calendar.generate_markdown_calendar",
                side_effect=subprocess.CalledProcessError(1, "git"),
            ):
                failure = self.runner.invoke(app, ["markdown", "calendar", str(directory)])

        self.assertEqual(success.exit_code, 0, success.output)
        self.assertIn("Generated:", success.output)
        self.assertEqual(no_open.exit_code, 0, no_open.output)
        self.assertEqual(failure.exit_code, 1)
        self.assertIn("Could not read Markdown history", failure.output)

        missing_directory = self.runner.invoke(app, ["markdown", "calendar"])
        self.assertNotEqual(missing_directory.exit_code, 0)
        self.assertIn("Missing argument", missing_directory.output)


class YoutubePlaylistTableTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_formats_available_duration_forms(self) -> None:
        self.assertEqual(format_duration({"duration_string": "4:32"}), "4:32")
        self.assertEqual(format_duration({"duration": 65.9}), "1:05")
        self.assertEqual(format_duration({"duration": 3661}), "1:01:01")
        self.assertEqual(format_duration({}), "?")
        self.assertEqual(format_duration({"duration": True}), "?")

    def test_builds_playlist_table_and_filters_unusable_entries(self) -> None:
        downloader = Mock()
        downloader.extract_info.return_value = {
            "entries": [
                {"title": "First | Lesson", "id": "abc", "duration": 65},
                {"title": "Missing ID"},
                {"title": "", "id": "empty-title"},
                None,
            ]
        }
        manager = Mock()
        manager.__enter__ = Mock(return_value=downloader)
        manager.__exit__ = Mock(return_value=False)

        with patch("studytool.youtube_playlist.yt_dlp.YoutubeDL", return_value=manager) as youtube_dl:
            table = playlist_table(r"https://youtube.test/playlist\?list\=123\&feature\=share", 5)

        self.assertIn("| name | 📽️ | length |", table)
        self.assertIn(r"First \| Lesson", table)
        self.assertIn("watch?v=abc", table)
        self.assertIn("| 1:05 |", table)
        self.assertNotIn("Missing ID", table)
        youtube_dl.assert_called_once()
        self.assertEqual(youtube_dl.call_args.args[0]["playlistend"], 5)
        downloader.extract_info.assert_called_once_with(
            "https://youtube.test/playlist?list=123&feature=share", download=False
        )

    def test_playlist_table_is_unlimited_by_default(self) -> None:
        downloader = Mock()
        downloader.extract_info.return_value = {"entries": []}
        manager = Mock()
        manager.__enter__ = Mock(return_value=downloader)
        manager.__exit__ = Mock(return_value=False)

        with patch("studytool.youtube_playlist.yt_dlp.YoutubeDL", return_value=manager) as youtube_dl:
            playlist_table("https://youtube.test/playlist")

        self.assertNotIn("playlistend", youtube_dl.call_args.args[0])

    def test_playlist_table_command_prints_markdown(self) -> None:
        with patch("studytool.youtube_playlist.playlist_table", return_value="| table |") as render:
            result = self.runner.invoke(
                app,
                [
                    "youtube",
                    "playlist-table",
                    "https://youtube.test/list",
                    "--limit",
                    "3",
                ],
            )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(result.output, "| table |\n")
        render.assert_called_once_with("https://youtube.test/list", 3)

    def test_playlist_table_command_has_no_default_limit(self) -> None:
        with patch("studytool.youtube_playlist.playlist_table", return_value="| table |") as render:
            result = self.runner.invoke(
                app,
                ["youtube", "playlist-table", "https://youtube.test/list"],
            )

        self.assertEqual(result.exit_code, 0, result.output)
        render.assert_called_once_with("https://youtube.test/list", None)


class NewCommandHelpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_group_help_lists_every_new_command(self) -> None:
        commands_by_group = {
            "markdown": ("calendar", "check-unused-images"),
            "text": ("double-newlines", "transcript-to-paragraphs"),
            "youtube": ("playlist-table",),
        }

        for group, commands in commands_by_group.items():
            with self.subTest(group=group):
                result = self.runner.invoke(app, [group, "--help"])
                self.assertEqual(result.exit_code, 0, result.output)
                for command in commands:
                    self.assertIn(command, result.output)


if __name__ == "__main__":
    unittest.main()
