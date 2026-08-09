import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from click import unstyle
from typer.testing import CliRunner

from studytool.cli import app
from studytool.course_builder import CourseBuilder
from studytool.course_markdown import PageContentOrder, compose_course_markdown


class CourseMarkdownTests(unittest.TestCase):
    def test_composes_images_and_text_in_both_orders(self) -> None:
        image_first = compose_course_markdown(
            "Lesson",
            [r"imgs\lesson\001.jpg", "imgs/lesson/002.jpg"],
            ["First page", ""],
        )
        text_first = compose_course_markdown(
            "Lesson",
            ["imgs/lesson/001.jpg"],
            ["First page"],
            PageContentOrder.TEXT_IMAGE,
        )

        self.assertIn("![001](imgs/lesson/001.jpg)\n\nFirst page", image_first)
        self.assertIn("First page\n\n![001](imgs/lesson/001.jpg)", text_first)
        self.assertTrue(image_first.endswith("\n"))

    def test_rejects_mismatched_page_content(self) -> None:
        with self.assertRaisesRegex(ValueError, "page image count"):
            compose_course_markdown("Lesson", ["001.jpg"], [])


class CourseBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.course_path = Path(self.temporary_directory.name) / "demo-course"
        self.slides_path = self.course_path / "slides"
        self.slides_path.mkdir(parents=True)
        self.builder = CourseBuilder(self.course_path)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_validates_course_and_slides_directories(self) -> None:
        self.builder.validate_course()

        with self.assertRaisesRegex(ValueError, "Course folder not found"):
            CourseBuilder(self.course_path / "missing").validate_course()

        self.slides_path.rmdir()
        with self.assertRaisesRegex(ValueError, "Slides folder not found"):
            self.builder.validate_course()

    def test_prepares_directories_and_discovers_sorted_pdfs(self) -> None:
        (self.slides_path / "B.pdf").touch()
        (self.slides_path / "a.PDF").touch()
        (self.slides_path / "notes.txt").touch()

        self.builder.prepare_output_directories()
        original_index = self.builder.index_file.read_text(encoding="utf-8")
        self.builder.prepare_output_directories()

        self.assertEqual([path.name for path in self.builder.discover_pdfs()], ["a.PDF", "B.pdf"])
        self.assertEqual(original_index, "Course Index\n===\n\n")

    def test_renders_numbered_page_images(self) -> None:
        class FakeImage:
            def save(self, fp) -> None:
                Path(fp).write_bytes(b"image")

        pdf_path = self.slides_path / "lesson.pdf"
        pdf_path.touch()

        with patch("studytool.course_builder.convert_from_path", return_value=[FakeImage(), FakeImage()]) as convert:
            self.builder.pdf_to_image(pdf_path)

        convert.assert_called_once_with(pdf_path=str(pdf_path), dpi=100)
        image_dir = self.builder.imgs_folder / "lesson"
        self.assertEqual(sorted(path.name for path in image_dir.iterdir()), ["001.jpg", "002.jpg"])

        with patch("studytool.course_builder.convert_from_path", return_value=[]):
            with self.assertRaisesRegex(RuntimeError, "no renderable pages"):
                self.builder.pdf_to_image(pdf_path)

    def test_ensures_existing_and_new_page_images(self) -> None:
        pdf_path = self.slides_path / "lesson.pdf"
        pdf_path.touch()
        image_dir = self.builder.imgs_folder / "lesson"
        image_dir.mkdir(parents=True)
        for number in (1, 2):
            (image_dir / f"{number:03}.jpg").touch()

        images, rendered = self.builder.ensure_page_images(pdf_path, 2)
        self.assertFalse(rendered)
        self.assertEqual(len(images), 2)

        (image_dir / "002.jpg").unlink()

        def render_missing(_pdf_path: Path) -> None:
            (image_dir / "002.jpg").touch()

        with patch.object(self.builder, "pdf_to_image", side_effect=render_missing):
            _, rendered = self.builder.ensure_page_images(pdf_path, 2)
        self.assertTrue(rendered)

        with self.assertRaisesRegex(ValueError, "no pages"):
            self.builder.ensure_page_images(pdf_path, 0)

        (image_dir / "002.jpg").unlink()
        with patch.object(self.builder, "pdf_to_image"):
            with self.assertRaisesRegex(RuntimeError, "Missing rendered page images"):
                self.builder.ensure_page_images(pdf_path, 2)

    def test_creates_markdown_and_navigation(self) -> None:
        self.builder.prepare_output_directories()
        pdf_path = self.slides_path / "first-lesson.pdf"
        pdf_path.touch()
        image_path = self.builder.imgs_folder / "first-lesson" / "001.jpg"
        image_path.parent.mkdir()
        image_path.touch()

        self.builder.create_md(pdf_path, [image_path], ["Lesson text"])
        self.builder.update_index_yaml()

        markdown = (self.builder.docs_folder / "first-lesson.md").read_text(encoding="utf-8")
        navigation = self.builder.index_yaml.read_text(encoding="utf-8")
        self.assertIn("![001](imgs/first-lesson/001.jpg)", markdown)
        self.assertIn("Lesson text", markdown)
        self.assertIn("- First Lesson: first-lesson.md", navigation)

    def test_processes_pdf_only_when_output_needs_refreshing(self) -> None:
        self.builder.prepare_output_directories()
        pdf_path = self.slides_path / "lesson.pdf"
        pdf_path.touch()
        markdown_path = self.builder.docs_folder / "lesson.md"
        markdown_path.touch()
        images = [self.builder.imgs_folder / "lesson" / "001.jpg"]

        with (
            patch("studytool.course_builder.count_pdf_pages", return_value=1),
            patch.object(self.builder, "ensure_page_images", return_value=(images, False)),
            patch.object(self.builder, "create_md") as create_markdown,
        ):
            self.builder.process_pdf(pdf_path)
        create_markdown.assert_not_called()

        self.builder.include_text = True
        with (
            patch("studytool.course_builder.extract_selectable_page_texts", return_value=["Text"]),
            patch.object(self.builder, "ensure_page_images", return_value=(images, False)),
            patch.object(self.builder, "create_md") as create_markdown,
        ):
            self.builder.process_pdf(pdf_path)
        create_markdown.assert_called_once_with(pdf_path, images, ["Text"])

    def test_run_processes_discovered_pdfs_and_rejects_empty_course(self) -> None:
        with self.assertRaisesRegex(ValueError, "No PDF files"):
            self.builder.run()

        pdf_path = self.slides_path / "lesson.pdf"
        pdf_path.touch()
        with patch.object(self.builder, "process_pdf") as process_pdf:
            self.builder.run()

        process_pdf.assert_called_once_with(pdf_path)
        self.assertTrue(self.builder.index_yaml.exists())

    def test_course_command_reports_invalid_options_and_paths(self) -> None:
        runner = CliRunner()
        conflict = runner.invoke(app, ["course", str(self.course_path), "--include-text", "--update-yaml-only"])
        missing_text = runner.invoke(app, ["course", str(self.course_path), "--page-order", "text-image"])
        missing_path = runner.invoke(app, ["course", str(self.course_path / "missing")])

        self.assertNotEqual(conflict.exit_code, 0)
        self.assertIn("cannot be used", conflict.output)
        self.assertNotEqual(missing_text.exit_code, 0)
        self.assertIn("requires --include-text", unstyle(missing_text.output))
        self.assertEqual(missing_path.exit_code, 1)
        self.assertIn("Course folder not found", missing_path.output)


if __name__ == "__main__":
    unittest.main()
