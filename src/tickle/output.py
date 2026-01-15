# src/tickle/output.py
"""Output formatters for tickle task scanning."""

import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import ClassVar

from colorama import Fore
from humanize import naturaltime
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree

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



class JSONFormatter(Formatter):
    """JSON formatter for task output."""

    def format(self, tasks: list[Task]) -> str:
        """Format tasks as a JSON array."""
        task_dicts = [task.to_dict() for task in tasks]
        return json.dumps(task_dicts, indent=2)


class MarkdownFormatter(Formatter):
    """Markdown formatter for task output."""

    def __init__(self, git_verbose: bool = False):
        """Initialize the markdown formatter.

        Args:
            git_verbose: Whether to show full git commit info (hash and message)
        """
        self.git_verbose = git_verbose

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

            line_text = f"- Line {task.line}: [{task.marker}] {task.text}"

            # Add git info if available
            if task.author:
                git_info = self._format_git_info(task)
                if git_info:
                    line_text += f" _{git_info}_"

            lines.append(line_text)

        return "\n".join(lines)

    def _format_git_info(self, task: Task) -> str:
        """Format git blame information for a task.

        Args:
            task: Task with git blame information

        Returns:
            Formatted git info string
        """
        parts = []

        if task.author:
            parts.append(f"by {task.author}")

        if task.commit_date:
            try:
                commit_dt = datetime.fromisoformat(task.commit_date)
                relative_time = naturaltime(commit_dt)
                parts.append(relative_time)
            except (ValueError, TypeError):
                pass

        if self.git_verbose:
            if task.commit_hash:
                short_hash = task.commit_hash[:7]
                parts.append(f"`{short_hash}`")

            if task.commit_message:
                parts.append(f'"{task.commit_message}"')

        return ", ".join(parts) if parts else ""


class TreeFormatter(Formatter):
    """Tree view formatter for hierarchical task display."""

    # Rich color styles matching colorama markers
    RICH_MARKER_COLORS: ClassVar[dict[str, str]] = {
        "TODO": "blue",
        "FIXME": "yellow",
        "BUG": "red",
        "NOTE": "cyan",
        "HACK": "magenta",
        "CHECKBOX": "green",
    }

    def __init__(self, git_verbose: bool = False, show_details: bool = True, scan_directory: str = "."):
        """Initialize the tree formatter.

        Args:
            git_verbose: Whether to show full git commit info (hash and message)
            show_details: Whether to show individual task details (False shows counts only)
            scan_directory: Directory being scanned (used for root label)
        """
        self.git_verbose = git_verbose
        self.show_details = show_details
        self.scan_directory = scan_directory

    def format(self, tasks: list[Task]) -> str:
        """Format tasks as a hierarchical tree."""
        if not tasks:
            return "No tasks found!"

        # Build tree structure
        tree = self._build_tree(tasks)

        # Render to string using Console
        console = Console(legacy_windows=False)
        with console.capture() as capture:
            console.print(tree)

        return capture.get().rstrip()

    def _build_tree(self, tasks: list[Task]) -> Tree:
        """Build a rich Tree from tasks grouped by directory.

        Args:
            tasks: List of tasks to display

        Returns:
            Rich Tree object
        """
        # Group tasks by file
        tasks_by_file: dict[str, list[Task]] = {}
        for task in tasks:
            if task.file not in tasks_by_file:
                tasks_by_file[task.file] = []
            tasks_by_file[task.file].append(task)

        # Count total tasks
        total_count = len(tasks)

        # Create root node with scan directory and count
        root = Tree(f"📁 {self.scan_directory} ({total_count} tasks)")

        # Build directory structure
        dir_structure = self._build_dir_structure(tasks_by_file)

        # Add to tree recursively
        self._add_to_tree(root, dir_structure, tasks_by_file)

        return root

    def _build_dir_structure(self, tasks_by_file: dict[str, list[Task]]) -> dict:
        """Build nested directory structure from file paths.

        Args:
            tasks_by_file: Dictionary mapping file paths to task lists

        Returns:
            Nested dictionary representing directory structure
        """
        structure: dict = {}

        for filepath in sorted(tasks_by_file.keys()):
            parts = Path(filepath).parts
            current = structure

            # Navigate/create nested structure
            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    # Last part is the file
                    if "_files" not in current:
                        current["_files"] = {}
                    current["_files"][part] = filepath
                else:
                    # Intermediate directories
                    if part not in current:
                        current[part] = {}
                    current = current[part]

        return structure

    def _add_to_tree(
        self,
        parent_node: Tree,
        structure: dict,
        tasks_by_file: dict[str, list[Task]],
        path_prefix: str = ""
    ) -> None:
        """Recursively add directories and files to tree.

        Args:
            parent_node: Parent tree node to add children to
            structure: Directory structure dictionary
            tasks_by_file: Mapping of file paths to tasks
            path_prefix: Current path prefix for building full paths
        """
        # Process directories first
        for key in sorted(structure.keys()):
            if key == "_files":
                continue

            subdir = structure[key]
            # Count tasks in this directory
            dir_count = self._count_tasks_in_dir(subdir, tasks_by_file)

            # Add directory node
            dir_node = parent_node.add(f"📁 {key}/ ({dir_count} tasks)")

            # Recurse into subdirectory
            new_prefix = f"{path_prefix}{key}/" if path_prefix else f"{key}/"
            self._add_to_tree(dir_node, subdir, tasks_by_file, new_prefix)

        # Process files
        if "_files" in structure:
            for filename, filepath in sorted(structure["_files"].items()):
                task_list = tasks_by_file[filepath]
                task_count = len(task_list)

                # Add file node
                file_node = parent_node.add(f"📄 {filename} ({task_count})")

                # Add task details if show_details is True
                if self.show_details:
                    for task in task_list:
                        self._add_task_node(file_node, task)

    def _count_tasks_in_dir(self, dir_structure: dict, tasks_by_file: dict[str, list[Task]]) -> int:
        """Count total tasks in a directory and its subdirectories.

        Args:
            dir_structure: Directory structure dictionary
            tasks_by_file: Mapping of file paths to tasks

        Returns:
            Total task count
        """
        count = 0

        # Count files in this directory
        if "_files" in dir_structure:
            for filepath in dir_structure["_files"].values():
                count += len(tasks_by_file[filepath])

        # Count subdirectories
        for key, subdir in dir_structure.items():
            if key != "_files":
                count += self._count_tasks_in_dir(subdir, tasks_by_file)

        return count

    def _add_task_node(self, parent_node: Tree, task: Task) -> None:
        """Add a task as a child node.

        Args:
            parent_node: Parent tree node
            task: Task to add
        """
        # Build task text with colored marker
        task_text = Text()

        # Add marker with color
        marker_color = self.RICH_MARKER_COLORS.get(task.marker, "white")
        task_text.append(f"[{task.marker}] ", style=marker_color)

        # Add line number and text
        task_text.append(f"Line {task.line}: {task.text}")

        # Add git info if available
        if task.author:
            git_info = self._format_git_info(task)
            if git_info:
                task_text.append(f" ({git_info})", style="dim")

        parent_node.add(task_text)

    def _format_git_info(self, task: Task) -> str:
        """Format git blame information for a task.

        Args:
            task: Task with git blame information

        Returns:
            Formatted git info string
        """
        parts = []

        if task.author:
            parts.append(task.author)

        if task.commit_date:
            try:
                commit_dt = datetime.fromisoformat(task.commit_date)
                relative_time = naturaltime(commit_dt)
                parts.append(relative_time)
            except (ValueError, TypeError):
                pass

        if self.git_verbose:
            if task.commit_hash:
                short_hash = task.commit_hash[:7]
                parts.append(short_hash)

            if task.commit_message:
                parts.append(f'"{task.commit_message}"')

        return ", ".join(parts) if parts else ""


def get_formatter(
    format_type: str,
    git_verbose: bool = False,
    tree_collapse: bool = False,
    scan_directory: str = "."
) -> Formatter:
    """Factory function to get the appropriate formatter.

    Args:
        format_type: The format type ('tree', 'json', or 'markdown').
        git_verbose: Whether to show full git commit info (hash and message)
        tree_collapse: Show only directory structure with counts (tree format only)
        scan_directory: Directory being scanned (tree format only)

    Returns:
        An instance of the appropriate Formatter subclass.

    Raises:
        ValueError: If format_type is not recognized.
    """
    if format_type == "json":
        return JSONFormatter()
    elif format_type == "markdown":
        return MarkdownFormatter(git_verbose=git_verbose)
    elif format_type == "tree":
        return TreeFormatter(
            git_verbose=git_verbose,
            show_details=not tree_collapse,
            scan_directory=scan_directory
        )
    else:
        raise ValueError(f"Unknown format type: {format_type}")


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
