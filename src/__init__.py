import typer
from rich.console import Console

from .ebook import app as ebook
from .link import app as link
from .num_to_image_path import app as num2imgpath
from .pdf2text import app as pdf2md
from .pdf_merge import app as pdfmerge
from .pdflinks import app as pdflinks
from .slides2md import app as slides2md
from .trad_to_simp import app as t2s
from .youtube_playlist import app as playlist_titles

app = typer.Typer()
app.add_typer(pdfmerge, name="pdfmerge", help="Merge PDF files in a directory")
app.add_typer(slides2md, name="course", help="Convert PDF slides to markdown files")
app.add_typer(slides2md, name="slides2md", help="Convert PDF slides to markdown files")
app.add_typer(num2imgpath, name="num2imgpath", help="Convert numbered patterns in markdown to image paths")
app.add_typer(t2s, name="t2s", help="Convert Traditional Chinese text to Simplified Chinese in a file")
app.add_typer(playlist_titles, name="playlist", help="Fetch YouTube playlist titles and save to markdown")
app.add_typer(link, name="link", help="Generate formatted links for markdown files")
app.add_typer(pdf2md, name="pdf2md", help="Extract URLs from PDF files and save to markdown")
app.add_typer(ebook, name="ebook", help="Convert EPUB files to markdown or extract images and TOC")
app.add_typer(pdflinks, name="pdflinks", help="Extract links from PDF files and save to markdown")

if __name__ == "__main__":
    app()
