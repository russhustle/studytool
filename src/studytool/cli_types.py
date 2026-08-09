from enum import StrEnum


class SortOrder(StrEnum):
    """Supported ordering for command output."""

    ASCENDING = "asc"
    DESCENDING = "desc"


class PageNumberColor(StrEnum):
    """Supported PDF page-number colors."""

    BLACK = "black"
    WHITE = "white"


class PageNumberPosition(StrEnum):
    """Supported horizontal page-number positions."""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
