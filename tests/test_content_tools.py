import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import ebooklib
from ebooklib import epub
from PIL import Image
from typer.testing import CliRunner

from studytool.text_simplify_chinese import convert_traditional_to_simplified
from studytool.cli import app
from studytool.epub import (
    epub_to_chapters,
    epub_to_markdown,
    extract_images_from_epub,
    extract_toc,
    resize_images_in_folder,
    save_chapters_as_markdown,
)


class FakeEpubItem:
    def __init__(self, item_type: int, content: bytes, name: str, item_id: str = "") -> None:
        self.item_type = item_type
        self.content = content
        self.name = name
        self.item_id = item_id

    def get_type(self) -> int:
        return self.item_type

    def get_content(self) -> bytes:
        return self.content

    def get_name(self) -> str:
        return self.name

    def get_id(self) -> str:
        return self.item_id


class FakeEpubBook:
    def __init__(self, items=None, toc=None) -> None:
        self.items = items or []
        self.toc = toc or []

    def get_items(self):
        return self.items


class EpubTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_extracts_chapters_with_heading_and_fallback_titles(self) -> None:
        items = [
            FakeEpubItem(ebooklib.ITEM_DOCUMENT, b"<h1>First</h1><p>Text</p>", "first.xhtml"),
            FakeEpubItem(ebooklib.ITEM_DOCUMENT, b"<h2>Second</h2>", "second.xhtml"),
            FakeEpubItem(ebooklib.ITEM_DOCUMENT, b"<p>No title</p>", "third.xhtml", "chapter-three"),
            FakeEpubItem(ebooklib.ITEM_IMAGE, b"image", "cover.jpg"),
        ]
        with patch("studytool.epub.epub.read_epub", return_value=FakeEpubBook(items=items)):
            chapters = epub_to_chapters("book.epub")

        self.assertEqual([title for title, _ in chapters], ["First", "Second", "chapter-three"])

    def test_saves_chapters_as_markdown_with_safe_names(self) -> None:
        chapters = [
            (
                "Chapter One",
                "<h2>Heading</h2><p>Paragraph</p><ul><li>Item</li></ul>"
                "<blockquote>Quote</blockquote><pre>code</pre>",
            ),
            ("!!!", "<p>Fallback filename</p>"),
        ]
        with TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory) / "chapters"
            save_chapters_as_markdown(chapters, str(output_directory))

            first = (output_directory / "01_Chapter_One.md").read_text(encoding="utf-8")
            second = (output_directory / "02_chapter_2.md").read_text(encoding="utf-8")

        self.assertIn("## Heading", first)
        self.assertIn("* Item", first)
        self.assertIn("> Quote", first)
        self.assertIn("```\ncode\n```", first)
        self.assertIn("# !!!", second)

    def test_epub_to_markdown_coordinates_extraction_and_writing(self) -> None:
        chapters = [("Chapter", "<p>Text</p>")]
        with (
            patch("studytool.epub.epub_to_chapters", return_value=chapters) as extract,
            patch("studytool.epub.save_chapters_as_markdown") as save,
        ):
            epub_to_markdown("book.epub", "output")

        extract.assert_called_once_with("book.epub")
        save.assert_called_once_with(chapters, "output")

    def test_extracts_epub_images(self) -> None:
        items = [
            FakeEpubItem(ebooklib.ITEM_IMAGE, b"image-data", "images/cover.jpg"),
            FakeEpubItem(ebooklib.ITEM_DOCUMENT, b"<p>Text</p>", "chapter.xhtml"),
        ]
        with TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory) / "assets"
            with patch("studytool.epub.epub.read_epub", return_value=FakeEpubBook(items=items)):
                extract_images_from_epub("book.epub", str(output_directory))

            self.assertEqual((output_directory / "cover.jpg").read_bytes(), b"image-data")

    def test_resizes_supported_epub_images_proportionally(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            image_path = directory / "cover.PNG"
            Image.new("RGB", (200, 100), color="red").save(image_path)
            (directory / "notes.txt").touch()

            resized = resize_images_in_folder(directory, 50)
            with Image.open(image_path) as image:
                size = image.size

        self.assertEqual(resized, [image_path])
        self.assertEqual(size, (50, 25))
        with self.assertRaisesRegex(ValueError, "greater than zero"):
            resize_images_in_folder("unused", 0)

    def test_extracts_nested_toc_and_handles_empty_or_invalid_books(self) -> None:
        first = epub.Link("first.xhtml", "First", "first")
        second = epub.Link("second.xhtml", "Second", "second")
        section = epub.Section("Part One")
        book = FakeEpubBook(toc=[first, (section, [second]), [first]])

        with TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "toc.txt"
            with patch("studytool.epub.epub.read_epub", return_value=book):
                result = extract_toc("book.epub", str(output_path))
            content = output_path.read_text(encoding="utf-8")

        self.assertEqual(result, str(output_path))
        self.assertIn("- First", content)
        self.assertIn("- Part One", content)
        self.assertIn("  - Second", content)

        with patch("studytool.epub.epub.read_epub", return_value=FakeEpubBook()):
            self.assertIsNone(extract_toc("empty.epub", "empty.txt"))
        with patch("studytool.epub.epub.read_epub", side_effect=OSError("broken")):
            self.assertIsNone(extract_toc("broken.epub", "broken.txt"))

    def test_epub_command_reports_missing_success_and_failure(self) -> None:
        missing = self.runner.invoke(app, ["ebook", "missing.epub"])

        with TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            source = directory / "book.epub"
            source.touch()
            output = directory / "output"
            output.mkdir()
            with (
                patch("studytool.epub.epub_to_markdown") as convert,
                patch("studytool.epub.extract_images_from_epub") as images,
                patch("studytool.epub.resize_images_in_folder") as resize,
                patch("studytool.epub.extract_toc") as toc,
            ):
                success = self.runner.invoke(
                    app,
                    ["ebook", str(source), "--output", str(output), "--image-width", "320"],
                )

            convert.assert_called_once_with(str(source), str(output))
            images.assert_called_once()
            resize.assert_called_once_with(output / "assets", 320)
            toc.assert_called_once()
            self.assertTrue((output / "book.epub").exists())

            broken_source = directory / "broken.epub"
            broken_source.touch()
            with patch("studytool.epub.epub_to_markdown", side_effect=RuntimeError("conversion failed")):
                failure = self.runner.invoke(
                    app,
                    ["ebook", str(broken_source), "--output", str(output), "--no-extract-images"],
                )

            invalid_options = self.runner.invoke(
                app,
                ["ebook", str(broken_source), "--no-extract-images", "--image-width", "100"],
            )

        self.assertEqual(missing.exit_code, 1)
        self.assertIn("not found", missing.output)
        self.assertEqual(success.exit_code, 0, success.output)
        self.assertIn("Successfully converted", success.output)
        self.assertEqual(failure.exit_code, 1)
        self.assertIn("conversion failed", failure.output)
        self.assertNotEqual(invalid_options.exit_code, 0)
        self.assertIn("requires image extraction", invalid_options.output)


class TextAndYoutubeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_converts_traditional_chinese_and_reports_missing_file(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            text_path = Path(temporary_directory) / "notes.md"
            text_path.write_text("學習繁體中文", encoding="utf-8")
            result = self.runner.invoke(app, ["text", "simplify-chinese", str(text_path)])

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertEqual(text_path.read_text(encoding="utf-8"), "学习繁体中文")

        with patch("builtins.print") as print_message:
            convert_traditional_to_simplified("missing.md")
        print_message.assert_called_once_with("Error: File not found at 'missing.md'.")

    def test_reports_chinese_converter_errors(self) -> None:
        with (
            patch("studytool.text_simplify_chinese.OpenCC", side_effect=RuntimeError("bad config")),
            patch("builtins.print") as print_message,
        ):
            convert_traditional_to_simplified("notes.md")

        print_message.assert_called_once_with("An error occurred: bad config")

    def test_prints_youtube_playlist_titles_with_limit(self) -> None:
        downloader = Mock()
        downloader.extract_info.return_value = {"entries": [{"title": "First"}, {"title": "Second"}]}
        manager = Mock()
        manager.__enter__ = Mock(return_value=downloader)
        manager.__exit__ = Mock(return_value=False)

        with patch("studytool.youtube_playlist.youtube_dl.YoutubeDL", return_value=manager) as youtube_dl:
            result = self.runner.invoke(
                app,
                ["youtube", "playlist", "https://youtube.test/playlist", "--limit", "2"],
            )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(result.output, "First\nSecond\n")
        youtube_dl.assert_called_once()
        options = youtube_dl.call_args.kwargs["params"]
        self.assertEqual(options["playlistend"], 2)
        downloader.extract_info.assert_called_once_with(url="https://youtube.test/playlist", download=False)


if __name__ == "__main__":
    unittest.main()
