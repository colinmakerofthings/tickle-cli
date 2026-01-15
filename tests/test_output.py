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
    get_formatter,
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


class TestGetFormatter:
    """Test get_formatter factory function."""

    def test_get_formatter_text(self):
        """Test getting text formatter."""
        formatter = get_formatter("text")
        assert isinstance(formatter, TextFormatter)

    def test_get_formatter_json(self):
        """Test getting JSON formatter."""
        formatter = get_formatter("json")
        assert isinstance(formatter, JSONFormatter)

    def test_get_formatter_markdown(self):
        """Test getting Markdown formatter."""
        formatter = get_formatter("markdown")
        assert isinstance(formatter, MarkdownFormatter)

    def test_get_formatter_unknown_raises(self):
        """Test that unknown format type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown format type: invalid"):
            get_formatter("invalid")


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


class TestGitBlameFormatting:
    """Test git blame information formatting."""

    @pytest.fixture
    def task_with_blame(self):
        """Create a task with git blame information."""
        return Task(
            file="src/main.py",
            line=10,
            marker="TODO",
            text="# TODO: Fix this",
            author="John Doe",
            author_email="john@example.com",
            commit_hash="abc123def456789",
            commit_date="2024-01-15T10:30:00",
            commit_message="Add feature"
        )

    @pytest.fixture
    def task_without_blame(self):
        """Create a task without git blame information."""
        return Task(
            file="src/main.py",
            line=10,
            marker="TODO",
            text="# TODO: Fix this"
        )

    def test_text_formatter_shows_git_info(self, task_with_blame):
        """Test that TextFormatter shows git blame info when available."""
        formatter = TextFormatter(git_verbose=False)
        result = formatter.format([task_with_blame])

        result_plain = strip_ansi(result)
        assert "by John Doe" in result_plain
        # Should show relative time (humanize output varies)
        assert "ago" in result_plain or "from now" in result_plain

    def test_text_formatter_verbose_shows_hash_and_message(self, task_with_blame):
        """Test that TextFormatter shows full git info in verbose mode."""
        formatter = TextFormatter(git_verbose=True)
        result = formatter.format([task_with_blame])

        result_plain = strip_ansi(result)
        assert "by John Doe" in result_plain
        assert "abc123d" in result_plain  # Short hash (7 chars)
        assert "Add feature" in result_plain

    def test_text_formatter_no_git_info_when_absent(self, task_without_blame):
        """Test that TextFormatter works without git blame info."""
        formatter = TextFormatter(git_verbose=False)
        result = formatter.format([task_without_blame])

        result_plain = strip_ansi(result)
        assert "src/main.py:10: [TODO]" in result_plain
        # Should not have git info
        assert "by" not in result_plain

    def test_markdown_formatter_shows_git_info(self, task_with_blame):
        """Test that MarkdownFormatter shows git blame info when available."""
        formatter = MarkdownFormatter(git_verbose=False)
        result = formatter.format([task_with_blame])

        assert "by John Doe" in result
        assert "_" in result  # Git info should be italicized

    def test_markdown_formatter_verbose_shows_hash(self, task_with_blame):
        """Test that MarkdownFormatter shows hash in verbose mode."""
        formatter = MarkdownFormatter(git_verbose=True)
        result = formatter.format([task_with_blame])

        assert "`abc123d`" in result  # Hash in code format
        assert "Add feature" in result

    def test_markdown_formatter_no_git_info_when_absent(self, task_without_blame):
        """Test that MarkdownFormatter works without git blame info."""
        formatter = MarkdownFormatter(git_verbose=False)
        result = formatter.format([task_without_blame])

        assert "Line 10: [TODO]" in result
        assert "by" not in result

    def test_json_formatter_includes_git_fields(self, task_with_blame):
        """Test that JSONFormatter includes git blame fields when present."""
        formatter = JSONFormatter()
        result = formatter.format([task_with_blame])

        parsed = json.loads(result)
        assert parsed[0]["author"] == "John Doe"
        assert parsed[0]["author_email"] == "john@example.com"
        assert parsed[0]["commit_hash"] == "abc123def456789"
        assert parsed[0]["commit_date"] == "2024-01-15T10:30:00"
        assert parsed[0]["commit_message"] == "Add feature"

    def test_json_formatter_excludes_absent_git_fields(self, task_without_blame):
        """Test that JSONFormatter excludes git fields when not present."""
        formatter = JSONFormatter()
        result = formatter.format([task_without_blame])

        parsed = json.loads(result)
        assert "author" not in parsed[0]
        assert "author_email" not in parsed[0]
        assert "commit_hash" not in parsed[0]
        assert "commit_date" not in parsed[0]
        assert "commit_message" not in parsed[0]

    def test_get_formatter_passes_git_verbose_to_text(self):
        """Test that get_formatter passes git_verbose to TextFormatter."""
        formatter = get_formatter("text", git_verbose=True)
        assert isinstance(formatter, TextFormatter)
        assert formatter.git_verbose is True

    def test_get_formatter_passes_git_verbose_to_markdown(self):
        """Test that get_formatter passes git_verbose to MarkdownFormatter."""
        formatter = get_formatter("markdown", git_verbose=True)
        assert isinstance(formatter, MarkdownFormatter)
        assert formatter.git_verbose is True

    def test_get_formatter_json_ignores_git_verbose(self):
        """Test that get_formatter works with JSONFormatter (no git_verbose param)."""
        formatter = get_formatter("json", git_verbose=True)
        assert isinstance(formatter, JSONFormatter)

