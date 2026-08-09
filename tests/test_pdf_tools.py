import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import fitz
from typer.testing import CliRunner

from studytool.cli import app
from studytool.pdf_links import extract_urls_from_pdf_folder
from studytool.pdf_links import extract_urls_from_text as extract_folder_urls
from studytool.pdf_markdown import clean_pdf_text, extract_urls_from_text, pdf_to_markdown
from studytool.pdf_text import clean_selectable_text, count_pdf_pages, extract_selectable_page_texts


def create_pdf(path: Path, page_texts: list[str]) -> None:
    document = fitz.open()
    for text in page_texts:
        page = document.new_page()
        if text:
            page.insert_text((72, 72), text)
    document.save(path)
    document.close()


class PdfTextTests(unittest.TestCase):
    def test_cleans_selectable_text(self) -> None:
        raw = "hyphen-\nated\r\n spaced   words \n\n\nNext"
        self.assertEqual(clean_selectable_text(raw), "hyphenated\nspaced words\n\nNext")

    def test_counts_pages_and_extracts_text(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "lesson.pdf"
            create_pdf(pdf_path, ["First page", "Second page"])

            self.assertEqual(count_pdf_pages(pdf_path), 2)
            self.assertEqual(extract_selectable_page_texts(pdf_path), ["First page", "Second page"])


class PdfMarkdownTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_extracts_and_cleans_pdf_text(self) -> None:
        text = "Visit https://example.com/path). and www.example.org."
        self.assertEqual(
            extract_urls_from_text(text),
            ["https://example.com/path", "https://www.example.org"],
        )

        cleaned = clean_pdf_text("HEAD-\nING\n\n\nTitle Case\nbody   text")
        self.assertIn("### HEADING", cleaned)
        self.assertIn("### Title Case", cleaned)
        self.assertIn("body text", cleaned)

    def test_converts_pdf_to_markdown_with_formatted_links(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            pdf_path = directory / "lesson.pdf"
            output_path = directory / "nested" / "lesson.md"
            create_pdf(pdf_path, ["LESSON\nhttps://example.com", ""])

            with patch(
                "studytool.pdf_markdown.get_formatted_link",
                return_value="[Example](https://example.com)",
            ):
                content = pdf_to_markdown(
                    str(pdf_path),
                    str(output_path),
                    extract_urls=True,
                    url_sort="asc",
                )

            self.assertIn("# lesson", content)
            self.assertIn("## Page 1", content)
            self.assertNotIn("## Page 2", content)
            self.assertIn("## Extracted URLs", content)
            self.assertEqual(output_path.read_text(encoding="utf-8"), content)

    def test_rejects_missing_pdf(self) -> None:
        with self.assertRaisesRegex(FileNotFoundError, "PDF file not found"):
            pdf_to_markdown("missing.pdf")

    def test_pdf_command_reports_success_missing_file_and_conversion_error(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            pdf_path = Path(temporary_directory) / "lesson.pdf"
            pdf_path.touch()
            output_path = pdf_path.with_suffix(".md")

            with patch(
                "studytool.pdf_markdown.pdf_to_markdown",
                return_value="# lesson\n\n## Extracted URLs\n\n- [Example](https://example.com)",
            ) as convert:
                success = self.runner.invoke(
                    app,
                    ["pdf", "to-markdown", str(pdf_path), "--extract-urls", "--sort", "asc"],
                )
            convert.assert_called_once_with(
                str(pdf_path),
                output_path,
                extract_urls=True,
                url_sort="asc",
            )

            with patch("studytool.pdf_markdown.pdf_to_markdown", side_effect=RuntimeError("broken")):
                failure = self.runner.invoke(app, ["pdf", "to-markdown", str(pdf_path)])

        missing = self.runner.invoke(app, ["pdf", "to-markdown", "missing.pdf"])
        self.assertEqual(success.exit_code, 0, success.output)
        self.assertIn("Successfully converted", success.output)
        self.assertEqual(failure.exit_code, 1)
        self.assertIn("broken", failure.output)
        self.assertEqual(missing.exit_code, 1)
        self.assertIn("not found", missing.output)


class PdfLinkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_extracts_and_normalizes_urls(self) -> None:
        self.assertEqual(
            extract_folder_urls("www.example.com, https://example.org/path!"),
            ["https://www.example.com", "https://example.org/path"],
        )

    def test_validates_input_folder(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            file_path = directory / "file.txt"
            file_path.touch()

            with self.assertRaises(FileNotFoundError):
                extract_urls_from_pdf_folder(str(directory / "missing"))
            with self.assertRaisesRegex(ValueError, "not a directory"):
                extract_urls_from_pdf_folder(str(file_path))
            with self.assertRaisesRegex(ValueError, "No PDF files"):
                extract_urls_from_pdf_folder(str(directory))

    def test_extracts_links_from_pdf_folder_and_skips_broken_pdf(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            create_pdf(directory / "lesson.pdf", ["https://example.com and www.example.org"])
            (directory / "broken.pdf").write_bytes(b"not a pdf")

            with patch(
                "studytool.pdf_links.get_formatted_link",
                side_effect=lambda url: f"[{url}]({url})",
            ):
                output = Path(extract_urls_from_pdf_folder(str(directory), "resources.md", "asc"))

            content = output.read_text(encoding="utf-8")
            self.assertIn("**Total PDFs processed:** 1", content)
            self.assertIn("**Total unique URLs found:** 2", content)
            self.assertIn("## lesson.pdf", content)
            self.assertIn("## All Unique URLs", content)

    def test_rejects_folder_when_pdfs_contain_no_urls(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            create_pdf(directory / "lesson.pdf", ["No links here"])

            with self.assertRaisesRegex(ValueError, "No URLs found"):
                extract_urls_from_pdf_folder(str(directory))

    def test_pdf_links_command_reports_success_and_errors(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            output_path = directory / "links.md"
            output_path.write_text(
                "# Links\n\n**Total unique URLs found:** 3\n",
                encoding="utf-8",
            )

            with patch("studytool.pdf_links.extract_urls_from_pdf_folder", return_value=str(output_path)):
                success = self.runner.invoke(app, ["pdf", "extract-links", str(directory), "--sort", "asc"])
            with patch(
                "studytool.pdf_links.extract_urls_from_pdf_folder",
                side_effect=ValueError("nothing found"),
            ):
                failure = self.runner.invoke(app, ["pdf", "extract-links", str(directory)])

        self.assertEqual(success.exit_code, 0, success.output)
        self.assertIn("Found 3 unique URLs", success.output)
        self.assertEqual(failure.exit_code, 1)
        self.assertIn("nothing found", failure.output)


if __name__ == "__main__":
    unittest.main()
