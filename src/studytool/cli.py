"""Command-line interface for StudyTool."""

import typer

from .chinese_conversion import simplify_chinese_command
from .course_builder import build_course_command
from .epub import convert_epub_command
from .markdown_calendar import markdown_calendar_command
from .markdown_images import insert_images_command
from .markdown_links import format_links_command
from .pdf_links import extract_pdf_links_command
from .pdf_markdown import pdf_to_markdown_command
from .pdf_merge import merge_pdfs_command
from .pdf_page_numbers import add_page_numbers_command
from .pdf_text import extract_pdf_text_command
from .text_formatting import double_newlines_command, transcript_to_paragraphs_command
from .unused_images import check_unused_images_command
from .youtube_playlist import playlist_table_command, playlist_titles_command

HELP_CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}

app = typer.Typer(
    help="Turn study materials into useful Markdown and supporting assets.",
    no_args_is_help=True,
    context_settings=HELP_CONTEXT_SETTINGS,
)

pdf_app = typer.Typer(
    help="Convert, merge, and inspect PDF documents.",
    no_args_is_help=True,
    context_settings=HELP_CONTEXT_SETTINGS,
)
markdown_app = typer.Typer(
    help="Prepare links and image references for Markdown.",
    no_args_is_help=True,
    context_settings=HELP_CONTEXT_SETTINGS,
)
text_app = typer.Typer(
    help="Transform text files.",
    no_args_is_help=True,
    context_settings=HELP_CONTEXT_SETTINGS,
)
youtube_app = typer.Typer(
    help="Extract study material from YouTube.",
    no_args_is_help=True,
    context_settings=HELP_CONTEXT_SETTINGS,
)

# Primary command hierarchy. Commands are grouped by the resource they operate on,
# while the two complete workflows remain easy to reach from the root.
app.command(name="course", help="Build Markdown course notes from PDF slides.")(build_course_command)
app.command(name="ebook", help="Convert an EPUB ebook to Markdown.")(convert_epub_command)
app.add_typer(markdown_app, name="markdown")
app.add_typer(pdf_app, name="pdf")
app.add_typer(text_app, name="text")
app.add_typer(youtube_app, name="youtube")

pdf_app.command(name="to-markdown", help="Convert one PDF to Markdown.")(pdf_to_markdown_command)
pdf_app.command(name="extract-text", help="Extract selectable PDF text to a text file.")(extract_pdf_text_command)
pdf_app.command(name="add-page-numbers", help="Add page-number labels to PDF pages.")(add_page_numbers_command)
pdf_app.command(name="merge", help="Merge every PDF in a directory.")(merge_pdfs_command)
pdf_app.command(
    name="extract-links",
    help="Extract links from PDFs in a directory.",
)(extract_pdf_links_command)

markdown_app.command(
    name="calendar",
    help="Create a commit calendar for Markdown files.",
)(markdown_calendar_command)
markdown_app.command(
    name="check-unused-images",
    help="Find or delete unreferenced Markdown images.",
)(check_unused_images_command)
markdown_app.command(
    name="format-links",
    help="Turn URLs into titled Markdown links.",
)(format_links_command)
markdown_app.command(
    name="insert-images",
    help="Replace page numbers with Markdown image references.",
)(insert_images_command)

text_app.command(
    name="double-newlines",
    help="Expand blank lines in a text file.",
)(double_newlines_command)
text_app.command(
    name="simplify-chinese",
    help="Convert Traditional Chinese text to Simplified Chinese.",
)(simplify_chinese_command)
text_app.command(
    name="transcript-to-paragraphs",
    help="Remove timestamps and join transcript lines.",
)(transcript_to_paragraphs_command)

youtube_app.command(
    name="playlist",
    help="Print the titles in a YouTube playlist.",
)(playlist_titles_command)
youtube_app.command(
    name="playlist-table",
    help="Print a YouTube playlist as a Markdown table.",
)(playlist_table_command)

# Backward-compatible aliases. They remain callable for scripts created before
# the hierarchy was introduced, but stay out of the main help screen.
app.command(name="pdfmerge", hidden=True, deprecated=True)(merge_pdfs_command)
app.command(name="slides2md", hidden=True, deprecated=True)(build_course_command)
app.command(name="num2imgpath", hidden=True, deprecated=True)(insert_images_command)
app.command(name="t2s", hidden=True, deprecated=True)(simplify_chinese_command)
app.command(name="playlist", hidden=True, deprecated=True)(playlist_titles_command)
app.command(name="link", hidden=True, deprecated=True)(format_links_command)
app.command(name="pdf2md", hidden=True, deprecated=True)(pdf_to_markdown_command)
app.command(name="pdflinks", hidden=True, deprecated=True)(extract_pdf_links_command)


if __name__ == "__main__":
    app()
