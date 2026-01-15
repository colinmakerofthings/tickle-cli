"""Tests for tickle.output module."""

import json
import re

import pytest

from tickle.models import Task
from tickle.output import (
    JSONFormatter,
    MarkdownFormatter,
    TextFormatter,
    display_summary_panel,
)


def strip_ansi(text):
    """Remove ANSI color codes from text."""
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    return ansi_escape.sub('', text)


class TestTaskFormatting:
    """Test Task object formatting for different output formats."""

    @pytest.fixture
    def sample_tasks(self):
        """Create sample Task objects for testing."""
        return [
            Task(file="src/main.py", line=5, marker="TODO", text="# TODO: Implement feature"),
            Task(file="src/main.py", line=12, marker="FIXME", text="# FIXME: Fix bug"),
            Task(file="tests/test.py", line=3, marker="BUG", text="# BUG: Known issue"),
        ]

    def test_task_str_format(self, sample_tasks):
        """Test Task.__str__() produces readable output."""
        task = sample_tasks[0]
        result = str(task)

        assert "src/main.py" in result
        assert "5" in result
        assert "TODO" in result
        assert "# TODO: Implement feature" in result

    def test_task_to_dict(self, sample_tasks):
        """Test Task.to_dict() returns proper dictionary."""
        task = sample_tasks[0]
        result = task.to_dict()

        assert isinstance(result, dict)
        assert result["file"] == "src/main.py"
        assert result["line"] == 5
        assert result["marker"] == "TODO"
        assert result["text"] == "# TODO: Implement feature"

    def test_task_sorting(self, sample_tasks):
        """Test Task objects can be sorted by file and line."""
        tasks = sample_tasks.copy()
        tasks.reverse()
        tasks.sort()

        # Should be sorted by file first, then line
        assert tasks[0].file == "src/main.py"
        assert tasks[0].line == 5
        assert tasks[1].file == "src/main.py"
        assert tasks[1].line == 12
        assert tasks[2].file == "tests/test.py"

    def test_tasks_json_serializable(self, sample_tasks):
        """Test that Task objects can be serialized to JSON."""
        task_dicts = [task.to_dict() for task in sample_tasks]

        # Should be valid JSON
        json_str = json.dumps(task_dicts)
        parsed = json.loads(json_str)

        assert len(parsed) == 3
        assert parsed[0]["marker"] == "TODO"

    def test_task_comparison_operators(self):
        """Test Task comparison for sorting."""
        task1 = Task(file="a.py", line=1, marker="TODO", text="text1")
        task2 = Task(file="a.py", line=2, marker="TODO", text="text2")
        task3 = Task(file="b.py", line=1, marker="TODO", text="text3")

        assert task1 < task2  # Same file, different line
        assert task2 < task3  # Different file
        assert task1 < task3  # Different file and line


class TestFormatters:
    """Test formatter classes for different output formats."""

    @pytest.fixture
    def sample_tasks(self):
        """Create sample Task objects for testing."""
        return [
            Task(file="src/main.py", line=5, marker="TODO", text="# TODO: Implement feature"),
            Task(file="src/main.py", line=12, marker="FIXME", text="# FIXME: Fix bug"),
            Task(file="tests/test.py", line=3, marker="BUG", text="# BUG: Known issue"),
        ]

    @pytest.fixture
    def empty_tasks(self):
        """Return empty task list for testing empty state."""
        return []

    @pytest.fixture
    def single_task(self):
        """Single task for minimal testing."""
        return [Task(file="app.py", line=1, marker="NOTE", text="# NOTE: Remember this")]

    @pytest.fixture
    def multi_file_tasks(self):
        """Tasks across multiple files for grouping tests."""
        return [
            Task(file="a.py", line=1, marker="TODO", text="# TODO: Task 1"),
            Task(file="a.py", line=5, marker="FIXME", text="# FIXME: Task 2"),
            Task(file="b.py", line=2, marker="BUG", text="# BUG: Task 3"),
            Task(file="c.py", line=10, marker="HACK", text="# HACK: Task 4"),
        ]

    # TextFormatter tests
    def test_text_formatter_with_tasks(self, sample_tasks):
        """Test TextFormatter with normal task list."""
        formatter = TextFormatter()
        result = formatter.format(sample_tasks)

        lines = result.split("\n")
        assert len(lines) == 3
        # Strip ANSI color codes for assertion
        assert "src/main.py:5: [TODO]" in strip_ansi(lines[0])
        assert "src/main.py:12: [FIXME]" in strip_ansi(lines[1])
        assert "tests/test.py:3: [BUG]" in strip_ansi(lines[2])

    def test_text_formatter_empty_tasks(self, empty_tasks):
        """Test TextFormatter with empty task list."""
        formatter = TextFormatter()
        result = formatter.format(empty_tasks)

        assert result == "No tasks found!"

    def test_text_formatter_single_task(self, single_task):
        """Test TextFormatter with single task."""
        formatter = TextFormatter()
        result = formatter.format(single_task)

        # Strip ANSI color codes for assertion
        result_plain = strip_ansi(result)
        assert "app.py:1: [NOTE]" in result_plain
        assert "# NOTE: Remember this" in result_plain

    def test_text_formatter_preserves_order(self, multi_file_tasks):
        """Test that TextFormatter preserves input order."""
        formatter = TextFormatter()
        result = formatter.format(multi_file_tasks)

        lines = result.split("\n")
        assert len(lines) == 4
        assert "a.py:1" in lines[0]
        assert "a.py:5" in lines[1]
        assert "b.py:2" in lines[2]
        assert "c.py:10" in lines[3]

    # JSONFormatter tests
    def test_json_formatter_with_tasks(self, sample_tasks):
        """Test JSONFormatter with normal task list."""
        formatter = JSONFormatter()
        result = formatter.format(sample_tasks)

        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 3
        assert parsed[0]["file"] == "src/main.py"
        assert parsed[0]["line"] == 5
        assert parsed[0]["marker"] == "TODO"
        assert parsed[0]["text"] == "# TODO: Implement feature"

    def test_json_formatter_empty_tasks(self, empty_tasks):
        """Test JSONFormatter with empty task list."""
        formatter = JSONFormatter()
        result = formatter.format(empty_tasks)

        parsed = json.loads(result)
        assert parsed == []

    def test_json_formatter_indent_two_spaces(self, sample_tasks):
        """Test JSONFormatter uses 2-space indentation."""
        formatter = JSONFormatter()
        result = formatter.format(sample_tasks[:2])  # Use 2 tasks for clearer test

        # Check for 2-space indentation in output
        assert "\n  {" in result or "\n  \"file\"" in result

    def test_json_formatter_valid_structure(self, single_task):
        """Test JSONFormatter produces valid structure."""
        formatter = JSONFormatter()
        result = formatter.format(single_task)

        parsed = json.loads(result)
        assert len(parsed) == 1
        task_dict = parsed[0]
        assert "file" in task_dict
        assert "line" in task_dict
        assert "marker" in task_dict
        assert "text" in task_dict

    # MarkdownFormatter tests
    def test_markdown_formatter_with_tasks(self, sample_tasks):
        """Test MarkdownFormatter with normal task list."""
        formatter = MarkdownFormatter()
        result = formatter.format(sample_tasks)

        assert "# Outstanding Tasks" in result
        assert "## src/main.py" in result
        assert "## tests/test.py" in result
        assert "- Line 5: [TODO] # TODO: Implement feature" in result
        assert "- Line 12: [FIXME] # FIXME: Fix bug" in result
        assert "- Line 3: [BUG] # BUG: Known issue" in result

    def test_markdown_formatter_empty_tasks(self, empty_tasks):
        """Test MarkdownFormatter with empty task list."""
        formatter = MarkdownFormatter()
        result = formatter.format(empty_tasks)

        assert "# Outstanding Tasks" in result
        assert "_No tasks found._" in result

    def test_markdown_formatter_groups_by_file(self, multi_file_tasks):
        """Test MarkdownFormatter groups tasks by file."""
        formatter = MarkdownFormatter()
        result = formatter.format(multi_file_tasks)

        # Count file headers
        file_header_count = result.count("## ")
        assert file_header_count == 3  # a.py, b.py, c.py

        # Check grouping
        assert "## a.py" in result
        assert "## b.py" in result
        assert "## c.py" in result

    def test_markdown_formatter_single_file(self, sample_tasks):
        """Test MarkdownFormatter with tasks from single file then another."""
        formatter = MarkdownFormatter()
        result = formatter.format(sample_tasks)

        # Two unique files (src/main.py appears twice, tests/test.py once)
        file_header_count = result.count("## ")
        assert file_header_count == 2

    def test_markdown_formatter_preserves_order(self, multi_file_tasks):
        """Test MarkdownFormatter preserves input order."""
        formatter = MarkdownFormatter()
        result = formatter.format(multi_file_tasks)

        # Find positions of file headers
        pos_a = result.index("## a.py")
        pos_b = result.index("## b.py")
        pos_c = result.index("## c.py")

        # Order should match input
        assert pos_a < pos_b < pos_c


class TestDisplaySummaryPanel:
    """Test display_summary_panel function."""

    @pytest.fixture
    def sample_tasks(self):
        """Create sample Task objects for testing."""
        return [
            Task(file="src/main.py", line=5, marker="TODO", text="# TODO: Implement feature"),
            Task(file="src/main.py", line=12, marker="FIXME", text="# FIXME: Fix bug"),
            Task(file="tests/test.py", line=3, marker="BUG", text="# BUG: Known issue"),
            Task(file="src/utils.py", line=8, marker="TODO", text="# TODO: Add tests"),
        ]

    @pytest.fixture
    def single_task(self):
        """Single task for minimal testing."""
        return [Task(file="app.py", line=1, marker="NOTE", text="# NOTE: Remember this")]

    @pytest.fixture
    def empty_tasks(self):
        """Return empty task list."""
        return []

    def test_display_panel_with_tasks(self, sample_tasks, capsys):
        """Test display_summary_panel shows correct summary."""
        display_summary_panel(sample_tasks)
        captured = capsys.readouterr()

        # Should contain total count
        assert "4 tasks" in captured.out
        # Should contain file count
        assert "3 files" in captured.out
        # Should contain task summary title
        assert "Task Summary" in captured.out

    def test_display_panel_shows_marker_breakdown(self, sample_tasks, capsys):
        """Test panel shows marker breakdown sorted by priority."""
        display_summary_panel(sample_tasks)
        captured = capsys.readouterr()

        # Should show all markers present
        assert "BUG" in captured.out
        assert "FIXME" in captured.out
        assert "TODO" in captured.out
        # Should show counts
        assert ": 1" in captured.out  # BUG: 1, FIXME: 1
        assert ": 2" in captured.out  # TODO: 2

    def test_display_panel_marker_priority_order(self, capsys):
        """Test markers are displayed in priority order (BUG, FIXME, TODO, etc.)."""
        tasks = [
            Task(file="a.py", line=1, marker="NOTE", text="# NOTE: note"),
            Task(file="a.py", line=2, marker="BUG", text="# BUG: bug"),
            Task(file="a.py", line=3, marker="TODO", text="# TODO: todo"),
        ]
        display_summary_panel(tasks)
        captured = capsys.readouterr()

        # Find positions of markers
        bug_pos = captured.out.index("BUG")
        todo_pos = captured.out.index("TODO")
        note_pos = captured.out.index("NOTE")

        # Should be in priority order: BUG < TODO < NOTE
        assert bug_pos < todo_pos < note_pos

    def test_display_panel_empty_tasks(self, empty_tasks, capsys):
        """Test display_summary_panel with empty task list does nothing."""
        display_summary_panel(empty_tasks)
        captured = capsys.readouterr()

        # Should not display anything for empty tasks
        assert captured.out == ""

    def test_display_panel_single_task_singular(self, single_task, capsys):
        """Test display_summary_panel uses singular form for single task."""
        display_summary_panel(single_task)
        captured = capsys.readouterr()

        # Should use singular forms
        assert "1 task in 1 file" in captured.out

    def test_display_panel_multiple_files_plural(self, sample_tasks, capsys):
        """Test display_summary_panel uses plural forms correctly."""
        display_summary_panel(sample_tasks)
        captured = capsys.readouterr()

        # Should use plural forms
        assert "tasks" in captured.out
        assert "files" in captured.out

    def test_display_panel_only_nonzero_markers(self, capsys):
        """Test panel only shows markers with non-zero counts."""
        tasks = [
            Task(file="a.py", line=1, marker="TODO", text="# TODO: task"),
            Task(file="a.py", line=2, marker="BUG", text="# BUG: bug"),
        ]
        display_summary_panel(tasks)
        captured = capsys.readouterr()

        # Should show TODO and BUG
        assert "TODO" in captured.out
        assert "BUG" in captured.out
        # Should not show other markers like FIXME, HACK, NOTE, CHECKBOX
        assert "FIXME" not in captured.out
        assert "HACK" not in captured.out
        assert "NOTE" not in captured.out
        assert "CHECKBOX" not in captured.out
