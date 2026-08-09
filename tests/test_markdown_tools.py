import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from typer.testing import CliRunner

from studytool.cli import app
from studytool.markdown_images import (
    find_last_image_number,
    insert_image_paths,
    insert_images_command,
    replace_numbers_with_images,
)
from studytool.markdown_links import get_formatted_link


class MarkdownImageTests(unittest.TestCase):
    def test_finds_and_replaces_numbered_images(self) -> None:
        content = "Existing\n![009](imgs/lesson/009.jpg)\n\n12\n"

        self.assertEqual(find_last_image_number(content), 9)
        self.assertEqual(find_last_image_number("No images"), 0)
        self.assertIn("![012](imgs/lesson/012.jpg)", replace_numbers_with_images(content, "lesson"))

    def test_inserts_custom_marker_after_highest_existing_image(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            markdown_path = Path(temporary_directory) / "lesson.md"
            markdown_path.write_text("![003](imgs/lesson/003.jpg)\n\nNEXT\n", encoding="utf-8")

            insert_image_paths(str(markdown_path), pattern="NEXT")

            content = markdown_path.read_text(encoding="utf-8")
            self.assertIn("![004](imgs/lesson/004.jpg)", content)

    def test_missing_file_is_reported_without_raising(self) -> None:
        with patch("builtins.print") as print_message:
            insert_image_paths("missing.md")

        print_message.assert_called_once_with("Error: File missing.md not found.")

    def test_watch_mode_repeats_after_interval(self) -> None:
        with (
            patch("studytool.markdown_images.insert_image_paths") as insert,
            patch("time.sleep", side_effect=[None, RuntimeError("stop")]),
        ):
            with self.assertRaisesRegex(RuntimeError, "stop"):
                insert_images_command("lesson.md", interval=1, pattern="NEXT", once=False)

        self.assertEqual(insert.call_count, 2)


class MarkdownLinkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_formats_page_title(self) -> None:
        response = Mock(content=b"<html><title>Example Page</title></html>")
        response.raise_for_status.return_value = None

        with patch("studytool.markdown_links.requests.get", return_value=response) as get:
            link = get_formatted_link("https://example.com")

        get.assert_called_once_with(
            "https://example.com",
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        self.assertEqual(link, "[Example Page](https://example.com)")

    def test_normalizes_arxiv_pdf_and_adds_publication_month(self) -> None:
        response = Mock(content=b"<title>[2001.08361] Useful Paper</title>")
        response.raise_for_status.return_value = None

        with patch("studytool.markdown_links.requests.get", return_value=response):
            link = get_formatted_link("https://arxiv.org/pdf/2001.08361")

        self.assertEqual(link, "[[2020.01] Useful Paper](https://arxiv.org/abs/2001.08361)")

    def test_uses_untitled_and_failure_fallbacks(self) -> None:
        untitled_response = Mock(content=b"<html></html>")
        untitled_response.raise_for_status.return_value = None

        with patch("studytool.markdown_links.requests.get", return_value=untitled_response):
            self.assertEqual(get_formatted_link("https://example.com/empty"), "[Untitled](https://example.com/empty)")

        with patch("studytool.markdown_links.requests.get", side_effect=OSError("offline")):
            self.assertEqual(
                get_formatted_link("https://example.com/failure"),
                "[‼️ https://example.com/failure](https://example.com/failure)",
            )

    def test_formats_links_from_file_and_sorts_them(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            input_path = Path(temporary_directory) / "urls.txt"
            input_path.write_text(
                "https://example.com/b\n[Existing](https://example.com/a)\n\nnot-a-url\n",
                encoding="utf-8",
            )
            with patch(
                "studytool.markdown_links.get_formatted_link",
                side_effect=lambda url: f"[{url.rsplit('/', 1)[-1]}]({url})",
            ):
                result = self.runner.invoke(
                    app,
                    ["markdown", "format-links", "--file", str(input_path), "--sort", "desc"],
                )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertLess(result.output.index("[b]"), result.output.index("[a]"))

    def test_extracts_unique_links_from_raw_text_and_normalizes_arxiv(self) -> None:
        raw_text = (
            "Read https://example.com/page. Duplicate https://example.com/page, "
            "then https://arxiv.org/pdf/2001.08361)."
        )
        with patch(
            "studytool.markdown_links.get_formatted_link",
            side_effect=lambda url: f"[{url}]({url})",
        ) as format_link:
            result = self.runner.invoke(app, ["markdown", "format-links", raw_text])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(format_link.call_count, 2)
        format_link.assert_any_call("https://example.com/page")
        format_link.assert_any_call("https://arxiv.org/abs/2001.08361")
        self.assertEqual(result.output.count("https://example.com/page"), 2)

    def test_keeps_single_url_output_unbulleted(self) -> None:
        with patch("studytool.markdown_links.get_formatted_link", return_value="[Page](https://example.com)"):
            result = self.runner.invoke(app, ["markdown", "format-links", "https://example.com"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(result.output, "[Page](https://example.com)\n")

    def test_accepts_positional_file_and_long_raw_text(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            input_path = Path(temporary_directory) / "notes.md"
            input_path.write_text("See https://example.com/page", encoding="utf-8")
            with patch("studytool.markdown_links.get_formatted_link", return_value="[Page](https://example.com/page)"):
                file_result = self.runner.invoke(app, ["markdown", "format-links", str(input_path)])
                long_text_result = self.runner.invoke(
                    app,
                    ["markdown", "format-links", f"{'x' * 300} https://example.com/page"],
                )

        self.assertEqual(file_result.exit_code, 0, file_result.output)
        self.assertTrue(file_result.output.startswith("- "))
        self.assertEqual(long_text_result.exit_code, 0, long_text_result.output)

    def test_reports_missing_or_absent_input(self) -> None:
        missing_file = self.runner.invoke(app, ["markdown", "format-links", "--file", "missing.txt"])
        no_input = self.runner.invoke(app, ["markdown", "format-links"])
        no_urls = self.runner.invoke(app, ["markdown", "format-links", "plain text"])

        self.assertEqual(missing_file.exit_code, 1)
        self.assertIn("not found", missing_file.output)
        self.assertEqual(no_input.exit_code, 1)
        self.assertIn("Provide a URL", no_input.output)
        self.assertEqual(no_urls.exit_code, 1)
        self.assertIn("No URLs found", no_urls.output)


if __name__ == "__main__":
    unittest.main()
