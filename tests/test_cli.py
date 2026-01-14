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

