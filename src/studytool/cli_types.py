from enum import StrEnum


class SortOrder(StrEnum):
    """Supported ordering for command output."""

    ASCENDING = "asc"
    DESCENDING = "desc"
