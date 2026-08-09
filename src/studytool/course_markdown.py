from collections.abc import Sequence
from enum import Enum
from pathlib import PurePosixPath


class PageContentOrder(str, Enum):
    """Supported image and selectable-text ordering for a PDF page."""

    IMAGE_TEXT = "image-text"
    TEXT_IMAGE = "text-image"


def compose_course_markdown(
    title: str,
    image_paths: Sequence[str],
    page_texts: Sequence[str] | None = None,
    page_order: PageContentOrder = PageContentOrder.IMAGE_TEXT,
) -> str:
    """Compose course Markdown with optional text paired with each page image."""
    if page_texts is not None and len(image_paths) != len(page_texts):
        raise ValueError(f"page image count ({len(image_paths)}) does not match page text count ({len(page_texts)})")

    blocks = [f"{title}\n==="]
    for index, raw_image_path in enumerate(image_paths):
        image_path = str(raw_image_path).replace("\\", "/")
        image_alt = PurePosixPath(image_path).stem
        image_block = f"![{image_alt}]({image_path})"
        page_text = page_texts[index] if page_texts is not None else ""

        if page_order == PageContentOrder.TEXT_IMAGE and page_text:
            blocks.append(page_text)
        blocks.append(image_block)
        if page_order == PageContentOrder.IMAGE_TEXT and page_text:
            blocks.append(page_text)

    return "\n\n".join(blocks) + "\n"
