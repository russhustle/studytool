# StudyTool

[![GitHub version](https://badge.fury.io/gh/russhustle%2Fstudytool.svg)](https://badge.fury.io/gh/russhustle%2Fstudytool)
[![PyPI version](https://badge.fury.io/py/studytool.svg)](https://badge.fury.io/py/studytool)

A command-line toolkit for turning PDFs, EPUBs, links, and video playlists into study notes.

## Installation

```shell
pip install studytool
```

Rendering PDF pages requires [Poppler](https://poppler.freedesktop.org/). On macOS:

```shell
brew install poppler
```

## Command structure

Commands are organized by the material they work with:

```text
stt
├── course                         Build a complete course from slide PDFs
├── ebook                          Convert an EPUB to Markdown
├── markdown
│   ├── format-links               Turn URLs into titled Markdown links
│   └── insert-images              Replace page numbers with image references
├── pdf
│   ├── to-markdown                Convert one PDF to Markdown
│   ├── merge                      Merge PDFs in a directory
│   └── extract-links              Extract links from PDFs in a directory
├── text
│   └── simplify-chinese           Convert Traditional Chinese to Simplified
└── youtube
    └── playlist                   Print playlist video titles
```

Run `stt --help` or `stt <group> --help` to explore the available commands.

## Examples

### Build course notes

Put source PDFs in a `slides` directory, then pass the course directory to `stt course`:

```shell
stt course tinyml
```

Include selectable text from each PDF page:

```shell
stt course tinyml --include-text
stt course tinyml --include-text --page-order text-image
```

Scanned pages remain available as images, but StudyTool does not perform OCR.

```text
# Before
tinyml
└── slides
    ├── lec01.pdf
    └── lec02.pdf

# After
tinyml
├── docs
│   ├── README.md
│   ├── imgs
│   │   ├── lec01
│   │   └── lec02
│   ├── lec01.md
│   └── lec02.md
├── mkdocs.yaml
└── slides
    ├── lec01.pdf
    └── lec02.pdf
```

### Work with PDFs

```shell
# Convert one PDF, writing notes.md
stt pdf to-markdown lecture.pdf --output notes.md

# Include links found in the PDF
stt pdf to-markdown lecture.pdf --extract-urls --sort asc

# Merge every PDF in a directory
stt pdf merge ./handouts --output handouts.pdf

# Create links.md from links found across a directory of PDFs
stt pdf extract-links ./handouts --output links.md
```

### Work with Markdown and text

```shell
stt markdown format-links https://example.com
stt markdown format-links --file urls.txt --sort asc
stt markdown insert-images notes.md
stt text simplify-chinese notes.md
```

### Convert an ebook

```shell
stt ebook book.epub --output ./book-notes
```

Images and the table of contents are included by default. Disable either with
`--no-extract-images` or `--no-generate-toc`.

### List YouTube playlist titles

```shell
stt youtube playlist "https://youtube.com/playlist?list=..." --limit 50
```

## Migrating old commands

The old flat commands remain available as hidden deprecated aliases, so existing
scripts continue to work. New scripts should use the structured forms:

| Old command | New command |
| --- | --- |
| `stt slides2md` | `stt course` |
| `stt pdf2md` | `stt pdf to-markdown` |
| `stt pdfmerge` | `stt pdf merge` |
| `stt pdflinks` | `stt pdf extract-links` |
| `stt link` | `stt markdown format-links` |
| `stt num2imgpath` | `stt markdown insert-images` |
| `stt t2s` | `stt text simplify-chinese` |
| `stt playlist` | `stt youtube playlist` |

## Contributing

Development setup, CLI design conventions, and validation steps are documented
in [CONTRIBUTING.md](CONTRIBUTING.md).
