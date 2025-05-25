import os
import re
from typing import List, Optional, Tuple


def num2img_path(md_path: str, pattern: Optional[str] = None) -> None:
    """
    Find and replace numbers in a markdown file with image paths.

    Args:
        md_path: Path to the markdown file
        pattern: Custom pattern to replace with image paths (defaults to "、")
    """
    if not os.path.exists(md_path):
        print(f"Error: File {md_path} not found.")
        return

    try:
        with open(md_path, "r", encoding="utf-8") as file:
            content = file.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    folder = os.path.basename(md_path).split(".")[0]
    print(f"Using folder name: {folder}")

    # Get the last image number used
    last_number = find_last_image_number(content)
    print(f"Last image number: {last_number}")

    # Process content
    updated_content = replace_numbers_with_images(content, folder)

    # Handle the replacement pattern
    updated_last = str(last_number + 1).zfill(3)
    replace_pattern = pattern if pattern else "、"

    updated_content = re.sub(
        f"\n{replace_pattern}\n",
        rf"\n![{updated_last}](imgs/{folder}/{updated_last}.jpg)\n",
        updated_content,
    )

    try:
        with open(md_path, "w", encoding="utf-8") as file:
            file.write(updated_content)
        print(f"Find and replace operation completed. Modified file: {md_path}")
    except Exception as e:
        print(f"Error writing to file: {e}")


def find_last_image_number(content: str) -> int:
    """Find the highest image number already used in the content."""
    pattern_regex = r"!\[(\d+)\]\(imgs/[^/]+/\1\.jpg\)"
    matches = re.findall(pattern_regex, content)
    return max(int(match) for match in matches) if matches else 0


def replace_numbers_with_images(content: str, folder: str) -> str:
    """Replace standalone numbers with image references."""

    def replace_match(match):
        num = match.group(1)
        padded_num = num.zfill(3)
        return f"\n![{padded_num}](imgs/{folder}/{padded_num}.jpg)\n"

    return re.sub(r"\n(\d{2,3})\n", replace_match, content)
