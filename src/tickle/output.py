# src/tickle/output.py
"""Output formatters for tickle task scanning."""

import json
from abc import ABC, abstractmethod

from colorama import Fore, Style
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from tickle.models import MARKER_PRIORITY, Task

# Marker-specific color mapping
MARKER_COLORS = {
    "TODO": Fore.BLUE,
    "FIXME": Fore.YELLOW,
    "BUG": Fore.RED,
    "NOTE": Fore.CYAN,
    "HACK": Fore.MAGENTA,
    "CHECKBOX": Fore.GREEN,
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


def display_summary_panel(tasks: list[Task]) -> None:
    """Display a rich panel with task summary statistics.

    Args:
        tasks: List of Task objects to analyze.
    """
    if not tasks:
        return

    # Total count
    total = len(tasks)

    # Count by marker type
    marker_counts = {}
    for task in tasks:
        marker_counts[task.marker] = marker_counts.get(task.marker, 0) + 1

    # Count unique files
    unique_files = len({task.file for task in tasks})

    # Map colorama colors to rich styles
    color_map = {
        "TODO": "blue",
        "FIXME": "yellow",
        "BUG": "red",
        "NOTE": "cyan",
        "HACK": "magenta",
        "CHECKBOX": "green",
    }

    # Build panel content
    content = Text()

    # First line: Total tasks and files
    file_word = "file" if unique_files == 1 else "files"
    task_word = "task" if total == 1 else "tasks"
    content.append(f"Total: {total} {task_word} in {unique_files} {file_word}\n")

    # Second line: Marker breakdown sorted by priority
    # Get markers sorted by priority
    sorted_markers = sorted(
        marker_counts.items(),
        key=lambda x: (MARKER_PRIORITY.get(x[0], 999), x[0])
    )

    # Build marker breakdown with colors (only non-zero markers)
    marker_parts = []
    for marker, count in sorted_markers:
        if count > 0:
            text_part = Text()
            style = color_map.get(marker, "white")
            text_part.append(f"{marker}", style=style)
            text_part.append(f": {count}")
            marker_parts.append(text_part)

    # Join marker parts with " | "
    for i, part in enumerate(marker_parts):
        if i > 0:
            content.append(" | ")
        content.append(part)

    # Create and display panel
    panel = Panel(
        content,
        title="Task Summary",
        box=box.SQUARE,
        expand=False
    )

    console = Console(legacy_windows=False)
    console.print(panel)
