# src/tickle/output.py
"""Output formatters for tickle task scanning."""

import json
from abc import ABC, abstractmethod

from colorama import Fore, Style

from tickle.models import Task

# Marker-specific color mapping
MARKER_COLORS = {
    "TODO": Fore.BLUE,
    "FIXME": Fore.YELLOW,
    "BUG": Fore.RED,
    "NOTE": Fore.CYAN,
    "HACK": Fore.MAGENTA,
}


class Formatter(ABC):
    """Abstract base class for output formatters."""

    @abstractmethod
    def format(self, tasks: list[Task]) -> str:
        """Format a list of tasks and return the output as a string.

        Args:
            tasks: List of Task objects to format.

        Returns:
            Formatted string representation of the tasks.
        """
        pass


class TextFormatter(Formatter):
    """Plain text formatter for task output."""

    def format(self, tasks: list[Task]) -> str:
        """Format tasks as plain text, one per line with colored markers."""
        if not tasks:
            return "No tasks found!"

        formatted_tasks = []
        for task in tasks:
            task_str = str(task)
            # Colorize the marker in the task string
            marker = task.marker
            color = MARKER_COLORS.get(marker, Fore.WHITE)
            # Replace the marker with colored version
            colored_str = task_str.replace(
                f"[{marker}]",
                f"{color}[{marker}]{Style.RESET_ALL}"
            )
            formatted_tasks.append(colored_str)

        return "\n".join(formatted_tasks)


class JSONFormatter(Formatter):
    """JSON formatter for task output."""

    def format(self, tasks: list[Task]) -> str:
        """Format tasks as a JSON array."""
        task_dicts = [task.to_dict() for task in tasks]
        return json.dumps(task_dicts, indent=2)


class MarkdownFormatter(Formatter):
    """Markdown formatter for task output."""

    def format(self, tasks: list[Task]) -> str:
        """Format tasks as Markdown with file grouping."""
        if not tasks:
            return "# Outstanding Tasks\n\n_No tasks found._"

        lines = ["# Outstanding Tasks\n"]
        current_file = None

        for task in tasks:
            if task.file != current_file:
                current_file = task.file
                lines.append(f"\n## {current_file}\n")
            lines.append(f"- Line {task.line}: [{task.marker}] {task.text}")

        return "\n".join(lines)


def get_formatter(format_type: str) -> Formatter:
    """Factory function to get the appropriate formatter.

    Args:
        format_type: The format type ('text', 'json', or 'markdown').

    Returns:
        An instance of the appropriate Formatter subclass.

    Raises:
        ValueError: If format_type is not recognized.
    """
    formatters = {
        "text": TextFormatter,
        "json": JSONFormatter,
        "markdown": MarkdownFormatter,
    }

    formatter_class = formatters.get(format_type)
    if formatter_class is None:
        raise ValueError(f"Unknown format type: {format_type}")

    return formatter_class()


def generate_stats(tasks: list[Task]) -> str:
    """Generate summary statistics for tasks.

    Args:
        tasks: List of Task objects to analyze.

    Returns:
        Formatted string with statistics summary.
    """
    if not tasks:
        return "No tasks found!"

    # Total count
    total = len(tasks)

    # Count by marker type
    marker_counts = {}
    for task in tasks:
        marker_counts[task.marker] = marker_counts.get(task.marker, 0) + 1

    # Count by file
    file_counts = {}
    for task in tasks:
        file_counts[task.file] = file_counts.get(task.file, 0) + 1

    # Sort markers and files by count (descending)
    sorted_markers = sorted(marker_counts.items(), key=lambda x: x[1], reverse=True)
    sorted_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)

    # Build output
    lines = []
    lines.append(f"Total Tasks: {total}")

    # Marker breakdown with colors
    marker_parts = []
    for marker, count in sorted_markers:
        color = MARKER_COLORS.get(marker, Fore.WHITE)
        marker_parts.append(f"{color}{marker}{Style.RESET_ALL}: {count}")
    lines.append(", ".join(marker_parts))

    # Top files (show top 5)
    top_files = sorted_files[:5]
    file_parts = [f"{file} ({count})" for file, count in top_files]
    lines.append(f"Top Files: {', '.join(file_parts)}")

    return "\n".join(lines)
