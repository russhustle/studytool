import typer
from opencc import OpenCC

app = typer.Typer()


def convert_trad_to_simp(file_path: str):
    """
    Reads a Markdown or text file, converts its Traditional Chinese content
    to Simplified Chinese, and saves it back to the same file.

    Args:
        file_path (str): The path to the Markdown or text file.
    """
    try:
        converter = OpenCC("t2s.json")  # t2s.json for Traditional to Simplified
        with open(file_path, "r", encoding="utf-8") as file:
            traditional_content = file.read()

        simplified_content = converter.convert(traditional_content)

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(simplified_content)
        print(f"Successfully converted '{file_path}' to Simplified Chinese.")
    except FileNotFoundError:
        print(f"Error: File not found at '{file_path}'.")
    except Exception as e:
        print(f"An error occurred: {e}")


@app.callback(invoke_without_command=True)
def main(
    file_path: str = typer.Argument(
        None, help="Path to the Markdown or text file to convert from Traditional to Simplified Chinese."
    ),
    ctx: typer.Context = typer.Context,
):
    """Convert Traditional Chinese text to Simplified Chinese in a file.

    Args:
        file_path: Path to the markdown or text file containing Traditional Chinese text.
    """
    if file_path is None:
        typer.echo(ctx.get_help())
        return

    convert_trad_to_simp(file_path=file_path)
