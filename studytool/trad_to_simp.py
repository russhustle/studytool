from opencc import OpenCC


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
