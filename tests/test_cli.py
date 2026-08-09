import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from PyPDF2 import PdfReader, PdfWriter
from typer.testing import CliRunner

from studytool.cli import app


class CommandHierarchyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_root_help_shows_resource_groups(self) -> None:
        result = self.runner.invoke(app, ["--help"])

        self.assertEqual(result.exit_code, 0, result.output)
        for command in ("course", "ebook", "markdown", "pdf", "text", "youtube"):
            self.assertIn(command, result.output)
        for legacy_command in ("pdfmerge", "slides2md", "num2imgpath", "pdf2md", "pdflinks"):
            self.assertNotIn(legacy_command, result.output)

    def test_pdf_help_shows_pdf_operations(self) -> None:
        result = self.runner.invoke(app, ["pdf", "--help"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("to-markdown", result.output)
        self.assertIn("extract-text", result.output)
        self.assertIn("add-page-numbers", result.output)
        self.assertIn("merge", result.output)
        self.assertIn("extract-links", result.output)

    def test_short_help_alias_works_at_every_command_level(self) -> None:
        invocations = [
            ["-h"],
            ["pdf", "-h"],
            ["pdf", "extract-text", "-h"],
            ["ebook", "-h"],
        ]

        for arguments in invocations:
            with self.subTest(arguments=arguments):
                result = self.runner.invoke(app, arguments)
                self.assertEqual(result.exit_code, 0, result.output)
                self.assertIn("Usage:", result.output)

    def test_nested_leaf_is_a_command_not_an_extra_group(self) -> None:
        result = self.runner.invoke(app, ["pdf", "to-markdown", "--help"])

        self.assertEqual(result.exit_code, 0, result.output)
        usage_line = next(line for line in result.output.splitlines() if "Usage:" in line)
        self.assertNotIn("COMMAND", usage_line)

    def test_required_input_is_reported_by_cli(self) -> None:
        result = self.runner.invoke(app, ["pdf", "merge"])

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Missing argument", result.output)

    def test_legacy_alias_remains_available_but_deprecated(self) -> None:
        result = self.runner.invoke(app, ["pdf2md", "--help"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("deprecated", result.output.lower())

    def test_nested_pdf_merge_routes_options_to_existing_operation(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            for filename in ("01.pdf", "02.pdf"):
                writer = PdfWriter()
                writer.add_blank_page(width=72, height=72)
                with (directory / filename).open("wb") as output:
                    writer.write(output)

            merged_pdf = directory / "combined.pdf"
            result = self.runner.invoke(
                app,
                ["pdf", "merge", str(directory), "--output", str(merged_pdf)],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertEqual(len(PdfReader(merged_pdf).pages), 2)

    def test_nested_markdown_command_modifies_requested_file(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            markdown_path = Path(temporary_directory) / "lecture.md"
            markdown_path.write_text("Page\n\n12\n", encoding="utf-8")

            result = self.runner.invoke(app, ["markdown", "insert-images", str(markdown_path)])

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("![012](imgs/lecture/012.jpg)", markdown_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
