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
    "CHECKBOX": 5,
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
        author: Name of the person who wrote this line (from git blame)
        author_email: Email of the author (from git blame)
        commit_hash: Commit hash where this line was last modified (from git blame)
        commit_date: Date when this line was last modified (from git blame)
        commit_message: Commit message for the commit that last modified this line (from git blame)
    """
    file: str
    line: int
    marker: str
    text: str
    author: str | None = None
    author_email: str | None = None
    commit_hash: str | None = None
    commit_date: str | None = None
    commit_message: str | None = None

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
        result = {
            "file": self.file,
            "line": self.line,
            "marker": self.marker,
            "text": self.text
        }
        # Include git blame fields if present
        if self.author is not None:
            result["author"] = self.author
        if self.author_email is not None:
            result["author_email"] = self.author_email
        if self.commit_hash is not None:
            result["commit_hash"] = self.commit_hash
        if self.commit_date is not None:
            result["commit_date"] = self.commit_date
        if self.commit_message is not None:
            result["commit_message"] = self.commit_message
        return result
