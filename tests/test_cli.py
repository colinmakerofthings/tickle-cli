"""Tests for tickle.cli module."""

import json
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from tickle.cli import main


@pytest.fixture
def sample_repo():
    """Create a temporary sample repository with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create a file with various markers
        test_file = tmpdir_path / "tasks.py"
        test_file.write_text(
            "# TODO: Implement feature\n"
            "# FIXME: Fix bug\n"
            "# BUG: Known issue\n"
            "# NOTE: Important note\n"
        )

        yield tmpdir_path


class TestCLI:
    """Test cases for CLI functionality."""

    def test_main_default_path(self, sample_repo, capsys):
        """Test main with default current directory."""
        with mock.patch("sys.argv", ["tickle", str(sample_repo)]):
            main()
            captured = capsys.readouterr()

            assert "TODO" in captured.out
            assert "FIXME" in captured.out

    def test_main_custom_path(self, sample_repo, capsys):
        """Test main with custom path argument."""
        with mock.patch("sys.argv", ["tickle", str(sample_repo)]):
            main()
            captured = capsys.readouterr()

            assert "tasks.py" in captured.out

    def test_main_no_tasks_found(self, capsys):
        """Test main when no tasks are found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch("sys.argv", ["tickle", tmpdir]):
                main()
                captured = capsys.readouterr()

                assert "No tasks found!" in captured.out

    def test_main_markers_filter(self, sample_repo, capsys):
        """Test --markers flag to filter specific markers."""
        with mock.patch("sys.argv", ["tickle", str(sample_repo), "--markers", "TODO,FIXME"]):
            main()
            captured = capsys.readouterr()

            # Should find TODO and FIXME
            assert "TODO" in captured.out or "FIXME" in captured.out
            # Should not find BUG or NOTE
            lines = captured.out.split("\n")
            todo_lines = [line for line in lines if "BUG" in line or "NOTE" in line]
            assert len(todo_lines) == 0

    def test_main_format_json(self, sample_repo, capsys):
        """Test --format json output."""
        with mock.patch("sys.argv", ["tickle", str(sample_repo), "--format", "json"]):
            main()
            captured = capsys.readouterr()

            # Should be valid JSON
            data = json.loads(captured.out)
            assert isinstance(data, list)
            assert all("file" in item for item in data)
            assert all("line" in item for item in data)
            assert all("marker" in item for item in data)
            assert all("text" in item for item in data)

    def test_main_format_text(self, sample_repo, capsys):
        """Test --format text (default) output."""
        with mock.patch("sys.argv", ["tickle", str(sample_repo), "--format", "text"]):
            main()
            captured = capsys.readouterr()

            # Should have readable format with file:line: [MARKER] text
            assert "[TODO]" in captured.out or "[FIXME]" in captured.out
            assert str(sample_repo) in captured.out or "tasks.py" in captured.out

    def test_main_format_markdown(self, sample_repo, capsys):
        """Test --format markdown output."""
        with mock.patch("sys.argv", ["tickle", str(sample_repo), "--format", "markdown"]):
            main()
            captured = capsys.readouterr()

            # Should have markdown headers and bullets
            assert "# Outstanding Tasks" in captured.out
            assert "##" in captured.out  # File headers
            assert "-" in captured.out  # Bullet points

    def test_main_ignore_patterns(self, capsys):
        """Test --ignore flag to skip patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create files
            (tmpdir_path / "include.py").write_text("# TODO: Include this\n")
            (tmpdir_path / "exclude.py").write_text("# TODO: Exclude this\n")

            with mock.patch("sys.argv", ["tickle", tmpdir, "--ignore", "exclude.py"]):
                main()
                captured = capsys.readouterr()

                # Should include the first file
                assert "include.py" in captured.out
                # Should not include the ignored file
                assert "exclude.py" not in captured.out

    def test_main_combined_flags(self, sample_repo, capsys):
        """Test combining multiple flags."""
        with mock.patch(
            "sys.argv",
            ["tickle", str(sample_repo), "--markers", "TODO", "--format", "json"]
        ):
            main()
            captured = capsys.readouterr()

            data = json.loads(captured.out)
            assert all(item["marker"] == "TODO" for item in data)

    def test_version_flag(self, capsys):
        """Test --version flag displays version."""
        with mock.patch("sys.argv", ["tickle", "--version"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            assert "0.1.0" in captured.out

    def test_sort_by_marker(self, capsys):
        """Test --sort marker flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            (tmpdir_path / "test.py").write_text(
                "# TODO: Third priority\n"
                "# BUG: First priority\n"
                "# FIXME: Second priority\n"
            )

            with mock.patch("sys.argv", ["tickle", tmpdir, "--sort", "marker"]):
                main()
                captured = capsys.readouterr()

                # Find positions of each marker in output (skip panel lines by looking for file paths)
                lines = captured.out.split("\n")
                task_lines = [line for line in lines if "test.py" in line]
                bug_line = next(i for i, line in enumerate(task_lines) if "BUG" in line)
                fixme_line = next(i for i, line in enumerate(task_lines) if "FIXME" in line)
                todo_line = next(i for i, line in enumerate(task_lines) if "TODO" in line)

                # Should be in priority order: BUG, FIXME, TODO
                assert bug_line < fixme_line < todo_line

    def test_sort_by_file_default(self, capsys):
        """Test default sorting is by file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            (tmpdir_path / "b.py").write_text("# BUG: High priority\n")
            (tmpdir_path / "a.py").write_text("# NOTE: Low priority\n")

            with mock.patch("sys.argv", ["tickle", tmpdir]):
                main()
                captured = capsys.readouterr()

                # Find positions
                lines = captured.out.split("\n")
                a_py_line = next(i for i, line in enumerate(lines) if "a.py" in line)
                b_py_line = next(i for i, line in enumerate(lines) if "b.py" in line)

                # Should be sorted by file (a.py before b.py)
                assert a_py_line < b_py_line

    def test_sort_by_file_explicit(self, capsys):
        """Test explicit --sort file flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            (tmpdir_path / "z.py").write_text("# BUG: High priority marker\n")
            (tmpdir_path / "a.py").write_text("# NOTE: Low priority marker\n")

            with mock.patch("sys.argv", ["tickle", tmpdir, "--sort", "file"]):
                main()
                captured = capsys.readouterr()

                # Find positions
                lines = captured.out.split("\n")
                a_py_line = next(i for i, line in enumerate(lines) if "a.py" in line)
                z_py_line = next(i for i, line in enumerate(lines) if "z.py" in line)

                # Should be sorted by file (a.py before z.py)
                assert a_py_line < z_py_line


class TestSummaryPanel:
    """Test cases for the summary panel feature."""

    def test_panel_appears_in_text_mode(self, sample_repo, capsys):
        """Test that summary panel appears in text format."""
        with mock.patch("sys.argv", ["tickle", str(sample_repo), "--format", "text"]):
            main()
            captured = capsys.readouterr()

            # Panel should appear
            assert "Task Summary" in captured.out
            assert "tasks" in captured.out
            # sample_repo has 1 file, so check for singular
            assert "file" in captured.out

    def test_panel_not_in_json_mode(self, sample_repo, capsys):
        """Test that summary panel does not appear in JSON format."""
        with mock.patch("sys.argv", ["tickle", str(sample_repo), "--format", "json"]):
            main()
            captured = capsys.readouterr()

            # Panel should not appear
            assert "Task Summary" not in captured.out
            # Should be valid JSON
            data = json.loads(captured.out)
            assert isinstance(data, list)

    def test_panel_not_in_markdown_mode(self, sample_repo, capsys):
        """Test that summary panel does not appear in Markdown format."""
        with mock.patch("sys.argv", ["tickle", str(sample_repo), "--format", "markdown"]):
            main()
            captured = capsys.readouterr()

            # Panel should not appear (no emoji or "Task Summary")
            assert "📋" not in captured.out
            # Should start with markdown header
            assert "# Outstanding Tasks" in captured.out

    def test_panel_not_shown_when_no_tasks(self, capsys):
        """Test that summary panel doesn't appear when no tasks found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch("sys.argv", ["tickle", tmpdir, "--format", "text"]):
                main()
                captured = capsys.readouterr()

                # Panel should not appear
                assert "Task Summary" not in captured.out
                # Should show normal empty message
                assert "No tasks found!" in captured.out

    def test_panel_shows_correct_counts(self, capsys):
        """Test panel displays accurate task and file counts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            (tmpdir_path / "file1.py").write_text("# TODO: Task 1\n# TODO: Task 2\n")
            (tmpdir_path / "file2.py").write_text("# FIXME: Task 3\n")

            with mock.patch("sys.argv", ["tickle", tmpdir]):
                main()
                captured = capsys.readouterr()

                # Should show 3 tasks in 2 files
                assert "3 tasks" in captured.out
                assert "2 files" in captured.out

    def test_panel_shows_marker_breakdown(self, capsys):
        """Test panel shows breakdown of markers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            (tmpdir_path / "test.py").write_text(
                "# TODO: Task 1\n"
                "# TODO: Task 2\n"
                "# BUG: Task 3\n"
                "# FIXME: Task 4\n"
            )

            with mock.patch("sys.argv", ["tickle", tmpdir]):
                main()
                captured = capsys.readouterr()

                # Should show all marker types
                assert "TODO" in captured.out
                assert "BUG" in captured.out
                assert "FIXME" in captured.out
                # Should show counts (looking for ": 2" for TODO)
                assert ": 2" in captured.out
                assert ": 1" in captured.out

