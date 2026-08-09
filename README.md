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
│   ├── calendar                   Build an HTML calendar from Markdown commit dates
│   ├── check-unused-images        Find or delete unreferenced images
│   ├── format-links               Turn URLs into titled Markdown links
│   └── insert-images              Replace page numbers with image references
├── pdf
│   ├── to-markdown                Convert one PDF to Markdown
│   ├── extract-text               Extract selectable text to a text file
│   ├── add-page-numbers           Add labels to one PDF or a directory
│   ├── merge                      Merge PDFs in a directory
│   └── extract-links              Extract links from PDFs in a directory
├── text
│   ├── double-newlines            Expand every blank line
│   ├── simplify-chinese           Convert Traditional Chinese to Simplified
│   └── transcript-to-paragraphs   Remove timestamps and join transcript lines
└── youtube
    ├── playlist                   Print playlist video titles
    └── playlist-table             Print a playlist as a Markdown table
```

Run `stt --help`, `stt -h`, or `stt <group> -h` to explore the available commands.

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

# Extract plain text with page separators
stt pdf extract-text lecture.pdf --page-numbers --output lecture.txt

# Add right-aligned page numbers to one PDF
stt pdf add-page-numbers slides.pdf --position right --output numbered.pdf

# Add page numbers to every PDF in a directory
stt pdf add-page-numbers ./slides --output ./numbered-slides

# Merge every PDF in a directory
stt pdf merge ./handouts --output handouts.pdf

# Create links.md from links found across a directory of PDFs
stt pdf extract-links ./handouts --output links.md
```

### Work with Markdown and text

```shell
stt markdown format-links https://example.com
stt markdown format-links --file urls.txt --sort asc
stt markdown format-links "Read https://example.com and https://arxiv.org/pdf/2001.08361"
stt markdown insert-images notes.md
stt markdown check-unused-images chapter-1.md chapter-2.md
stt markdown check-unused-images --fix chapter-1.md
stt markdown calendar ./notes --output md_calendar.html
stt text double-newlines notes.md
stt text simplify-chinese notes.md
stt text transcript-to-paragraphs transcript.txt
```

Markdown calendars open in the default browser after generation. Pass
`--no-open` when generating one in an automated workflow.

For each Markdown file, StudyTool checks its matching `imgs/<file-stem>/` folder
and asks whether to remove any unused images it finds. Answer no to keep them, or
use `--fix` to remove them without prompting.

### Convert an ebook

```shell
stt ebook book.epub --output ./book-notes
stt ebook book.epub --output ./book-notes --image-width 800
```

Images and the table of contents are included by default. Disable either with
`--no-extract-images` or `--no-generate-toc`. Use `--image-width` to resize
extracted images proportionally.

### List YouTube playlist titles

```shell
stt youtube playlist "https://youtube.com/playlist?list=..." --limit 50
stt youtube playlist-table "https://youtube.com/playlist?list=..."
stt youtube playlist-table "https://youtube.com/playlist?list=..." --limit 50
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
