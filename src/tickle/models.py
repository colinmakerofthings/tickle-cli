"""Data models for tickle task scanning."""

from dataclasses import dataclass
from typing import Callable

# Marker priority for sorting (lower number = higher priority)
MARKER_PRIORITY = {
    "BUG": 0,
    "FIXME": 1,
    "TODO": 2,
    "HACK": 3,
    "NOTE": 4,
}


def get_sort_key(sort_by: str) -> Callable[["Task"], tuple]:
    """Get a sort key function for tasks.

    Args:
        sort_by: Sort method - "file" (by file and line) or "marker" (by marker, then file and line)

    Returns:
        A function that takes a Task and returns a sort key tuple
    """
    if sort_by == "marker":
        def marker_sort_key(task: "Task") -> tuple:
            # Sort by marker priority (with unknown markers at the end), then file, then line
            # Including marker ensures alphabetical ordering within the same priority level
            priority = MARKER_PRIORITY.get(task.marker, 999)
            return (priority, task.marker, task.file, task.line)
        return marker_sort_key
    else:  # default to "file"
        def file_sort_key(task: "Task") -> tuple:
            return (task.file, task.line)
        return file_sort_key


@dataclass
class Task:
    """Represents a single task marker found in source code.

    Attributes:
        file: Path to the file containing the task
        line: Line number where the task is located (1-indexed)
        marker: Task marker type (e.g., "TODO", "FIXME", "BUG", "NOTE", "HACK")
        text: The full text of the line containing the task marker
    """
    file: str
    line: int
    marker: str
    text: str

    def __str__(self) -> str:
        """Return formatted string representation of the task."""
        return f"{self.file}:{self.line}: [{self.marker}] {self.text}"

    def __lt__(self, other: "Task") -> bool:
        """Support sorting by file, then line number."""
        if self.file != other.file:
            return self.file < other.file
        return self.line < other.line

    def to_dict(self) -> dict:
        """Convert task to dictionary format."""
        return {
            "file": self.file,
            "line": self.line,
            "marker": self.marker,
            "text": self.text
        }
