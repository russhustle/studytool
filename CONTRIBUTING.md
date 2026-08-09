# Contributing to StudyTool

Thanks for helping improve StudyTool. This guide covers local development and
the conventions used to keep the CLI predictable.

## Development setup

StudyTool requires Python 3.12 or newer. The project uses
[uv](https://docs.astral.sh/uv/) to manage its environment and lock file.

After cloning the repository, install the project and development dependencies:

```shell
uv sync
```

Install the Git hooks if you want checks to run before each commit:

```shell
uv run pre-commit install
```

Course page rendering also requires Poppler. On macOS:

```shell
brew install poppler
```

Confirm the development CLI is available:

```shell
uv run stt --help
# Or:
uv run python -m studytool --help
```

## Project layout

| Path | Purpose |
| --- | --- |
| `src/studytool/cli.py` | Builds the public command hierarchy and compatibility aliases. |
| `src/studytool/__main__.py` | Supports running the package with `python -m studytool`. |
| `src/studytool/cli_types.py` | Contains option types shared by commands. |
| `src/studytool/*.py` | Implements the individual study-tool operations. |
| `tests/` | Contains command hierarchy and behavior tests. |
| `README.md` | Documents installation and user-facing commands. |

Keep operation logic in testable functions and use Typer callbacks only for
argument handling, user messages, and exit codes.

## CLI design conventions

StudyTool organizes commands by the material they operate on:

```text
stt <resource> <operation>
```

For example, use `stt pdf merge` and `stt markdown format-links`. Complete
workflows such as `stt course` and `stt ebook` can remain at the root when an
additional operation name would add no useful meaning.

When adding or changing commands:

- Prefer clear words such as `extract-links` over abbreviations such as
  `pdflinks`.
- Use a required positional argument for the primary input and options for
  optional behavior.
- Reuse common option names: `--output`/`-o`, `--sort`, and `--limit`/`-n`.
- Model finite choices with an enum so invalid values fail before work begins.
- Write short help text that describes the outcome from the user's perspective.
- Make a group display help when invoked without an operation.
- Add a hidden, deprecated alias when renaming a command would otherwise break
  existing scripts.

Register new commands in `src/studytool/cli.py` and update the command tree and
examples in `README.md`.

## Tests and checks

Run the test suite with branch coverage:

```shell
uv run coverage erase
uv run coverage run -m unittest discover -s tests -v
uv run coverage report
```

The coverage configuration in `pyproject.toml` enforces a minimum total of 90%.
The same tests, coverage threshold, formatting check, and lint check run in
GitHub Actions for pushes and pull requests.

Check formatting and linting:

```shell
uv run black --check src/studytool/*.py tests/*.py
uv run flake8 src tests
```

Run every configured repository check before opening a pull request:

```shell
uv run pre-commit run --all-files
```

For packaging changes, also verify that both distribution formats build:

```shell
uv build
```

Add tests for new behavior. CLI changes should normally cover the visible help,
argument validation, and at least one successful invocation through the public
command path.

## Pull requests

Before submitting a pull request:

- Keep the change focused and explain its user-visible effect.
- Include tests for behavior changes and bug fixes.
- Update `README.md` when commands, options, or output formats change.
- Preserve old command paths with deprecated aliases when compatibility matters.
- Do not commit generated distributions, virtual environments, or temporary
  study materials.

## Releases

Releases are maintained through version tags. Maintainers should update the
project version and lock file, run the checks above, then push a tag such as
`vX.Y.Z`. The GitHub Actions publish workflow builds and publishes that tag to
PyPI.
