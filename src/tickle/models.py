"""Data models for tickle task scanning."""

from dataclasses import dataclass


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
