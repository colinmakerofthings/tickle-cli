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
        with mock.patch(
            "sys.argv", ["tickle", str(sample_repo), "--markers", "TODO,FIXME"]
        ):
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

    def test_main_format_markdown(self, sample_repo, capsys):
        """Test --format markdown output."""
        with mock.patch(
            "sys.argv", ["tickle", str(sample_repo), "--format", "markdown"]
        ):
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
            ["tickle", str(sample_repo), "--markers", "TODO", "--format", "json"],
        ):
            main()
            captured = capsys.readouterr()

            data = json.loads(captured.out)
            assert all(item["marker"] == "TODO" for item in data)

    def test_version_flag(self, capsys):
        """Test --version flag displays version."""
        from tickle import __version__

        with mock.patch("sys.argv", ["tickle", "--version"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            assert __version__ in captured.out

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

                # In tree format, tasks are shown with Line numbers and markers
                # Find positions of each marker in output
                bug_pos = captured.out.find("[BUG]")
                fixme_pos = captured.out.find("[FIXME]")
                todo_pos = captured.out.find("[TODO]")

                # Should be in priority order: BUG, FIXME, TODO
                assert bug_pos < fixme_pos < todo_pos

    def test_sort_by_file_default(self, capsys):
        """Test default sorting is by file and uses tree format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            (tmpdir_path / "b.py").write_text("# BUG: High priority\n")
            (tmpdir_path / "a.py").write_text("# NOTE: Low priority\n")

            with mock.patch("sys.argv", ["tickle", tmpdir]):
                main()
                captured = capsys.readouterr()

                # Should use tree format with proper structure
                assert "📁" in captured.out or "📄" in captured.out
                # Files should appear in alphabetical order
                assert "a.py" in captured.out
                assert "b.py" in captured.out

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

    def test_export_plain_text(self, sample_repo, tmp_path, capsys):
        """Test --export flag creates a plain text file with correct content and no color codes."""
        export_file = tmp_path / "output.txt"
        with mock.patch(
            "sys.argv", ["tickle", str(sample_repo), "--export", str(export_file)]
        ):
            main()
            captured = capsys.readouterr()
            assert export_file.exists()
            content = export_file.read_text(encoding="utf-8")
            # Should contain task markers and no ANSI color codes
            assert "TODO" in content and "\x1b[" not in content
            assert "[tickle] Output exported to:" in captured.out

    def test_export_overwrite_plain_text(self, sample_repo, tmp_path, capsys):
        """Test --export overwrites existing file and warns."""
        export_file = tmp_path / "output.txt"
        export_file.write_text("old content", encoding="utf-8")
        with mock.patch(
            "sys.argv", ["tickle", str(sample_repo), "--export", str(export_file)]
        ):
            main()
            captured = capsys.readouterr()
            content = export_file.read_text(encoding="utf-8")
            assert "TODO" in content and "old content" not in content
            assert "Warning: Overwrote" in captured.out

    def test_export_pdf(self, sample_repo, tmp_path, capsys):
        """Test --export-pdf flag creates a PDF file with correct header."""
        export_file = tmp_path / "output.pdf"
        with mock.patch(
            "sys.argv", ["tickle", str(sample_repo), "--export-pdf", str(export_file)]
        ):
            main()
            captured = capsys.readouterr()
            assert export_file.exists()
            # Check PDF header
            with open(export_file, "rb") as f:
                assert f.read(4) == b"%PDF"
            assert "Output exported to PDF" in captured.out

    def test_export_pdf_only_tree_format(self, sample_repo, tmp_path):
        """Test --export-pdf raises error if not using tree format."""
        export_file = tmp_path / "output.pdf"
        with pytest.raises(ValueError):
            with mock.patch(
                "sys.argv",
                [
                    "tickle",
                    str(sample_repo),
                    "--format",
                    "json",
                    "--export-pdf",
                    str(export_file),
                ],
            ):
                main()


class TestSummaryPanel:
    """Test cases for the summary panel feature."""

    def test_panel_appears_by_default(self, sample_repo, capsys):
        """Test that summary panel appears by default (tree format)."""
        with mock.patch("sys.argv", ["tickle", str(sample_repo)]):
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
        with mock.patch(
            "sys.argv", ["tickle", str(sample_repo), "--format", "markdown"]
        ):
            main()
            captured = capsys.readouterr()

            # Panel should not appear (no emoji or "Task Summary")
            assert "📋" not in captured.out
            # Should start with markdown header
            assert "# Outstanding Tasks" in captured.out

    def test_panel_not_shown_when_no_tasks(self, capsys):
        """Test that summary panel doesn't appear when no tasks found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch("sys.argv", ["tickle", tmpdir]):
                main()
                captured = capsys.readouterr()

                # Panel should not appear when no tasks
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


class TestConfigCommands:
    """Test cases for config-related commands."""

    def test_config_show_command_with_config_file(self, capsys):
        """Test 'tickle config show' displays configuration from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "tickle.toml"
            config_file.write_text(
                "[tickle]\n"
                'markers = ["TODO", "FIXME"]\n'
                'ignore = ["node_modules", "dist"]\n'
                'format = "json"\n'
            )

            with mock.patch(
                "sys.argv", ["tickle", "config", "show", "--config", str(config_file)]
            ):
                main()
                captured = capsys.readouterr()

                assert "TODO" in captured.out
                assert "FIXME" in captured.out
                assert "node_modules" in captured.out
                assert "json" in captured.out

    def test_config_show_command_no_config(self, capsys):
        """Test 'tickle config show' with no config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch("sys.argv", ["tickle", "config", "show", tmpdir]):
                main()
                captured = capsys.readouterr()

                # Should show defaults
                assert (
                    "markers" in captured.out.lower() or "todo" in captured.out.lower()
                )

    def test_config_command_without_subcommand_shows_help(self, capsys):
        """Test 'tickle config' without subcommand shows help."""
        with mock.patch("sys.argv", ["tickle", "config"]):
            main()
            captured = capsys.readouterr()

            # Should show help text
            assert "show" in captured.out.lower() or "usage" in captured.out.lower()

    def test_init_command_success(self, capsys):
        """Test 'tickle init' creates config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(tmpdir)

                with mock.patch("sys.argv", ["tickle", "init"]):
                    main()
                    captured = capsys.readouterr()

                    assert Path("tickle.toml").exists()
                    assert "Created" in captured.out
            finally:
                os.chdir(original_cwd)

    def test_init_command_file_exists_error(self, capsys):
        """Test 'tickle init' errors when file already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(tmpdir)

                # Create existing config file
                Path("tickle.toml").write_text("[tickle]\n")

                with mock.patch("sys.argv", ["tickle", "init"]):
                    with pytest.raises(SystemExit) as exc:
                        main()
                    assert exc.value.code == 1

                captured = capsys.readouterr()
                assert "already exists" in captured.out
            finally:
                os.chdir(original_cwd)

    def test_init_command_handles_write_error(self, capsys):
        """Test 'tickle init' handles permission errors gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(tmpdir)

                with mock.patch(
                    "pathlib.Path.write_text",
                    side_effect=PermissionError("Access denied"),
                ):
                    with mock.patch("sys.argv", ["tickle", "init"]):
                        with pytest.raises(SystemExit) as exc:
                            main()
                        assert exc.value.code == 1

                captured = capsys.readouterr()
                assert "Error" in captured.out
            finally:
                os.chdir(original_cwd)

    def test_scan_with_verbose_flag(self, capsys):
        """Test --verbose flag shows config file being used."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            (tmpdir_path / "test.py").write_text("# TODO: Test task\n")

            # Create a config file
            config_file = tmpdir_path / "tickle.toml"
            config_file.write_text('[tickle]\nmarkers = ["TODO"]\n')

            with mock.patch("sys.argv", ["tickle", str(tmpdir), "--verbose"]):
                main()
                captured = capsys.readouterr()

                # Should show config path in stderr
                output = captured.out + captured.err
                assert "config" in output.lower() or "tickle.toml" in output

    def test_scan_with_no_config_flag(self, capsys):
        """Test --no-config flag ignores config files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            (tmpdir_path / "test.py").write_text(
                "# TODO: Test task\n# FIXME: Another\n"
            )

            # Create a config that would filter out TODO
            config_file = tmpdir_path / "tickle.toml"
            config_file.write_text('[tickle]\nmarkers = ["FIXME"]\n')

            with mock.patch("sys.argv", ["tickle", str(tmpdir), "--no-config"]):
                main()
                captured = capsys.readouterr()

                # Should still find TODO because config is ignored
                assert "TODO" in captured.out


class TestPlatformSpecific:
    """Test platform-specific behavior."""

    def test_windows_utf8_encoding(self):
        """Test Windows UTF-8 stdout reconfiguration."""
        with mock.patch("sys.platform", "win32"):
            with mock.patch("sys.stdout.reconfigure") as mock_reconfig:
                with tempfile.TemporaryDirectory() as tmpdir:
                    with mock.patch("sys.argv", ["tickle", tmpdir]):
                        main()
                        mock_reconfig.assert_called_once_with(encoding="utf-8")

    def test_non_windows_no_reconfigure(self):
        """Test non-Windows platforms don't reconfigure encoding."""
        with mock.patch("sys.platform", "linux"):
            with mock.patch("sys.stdout.reconfigure") as mock_reconfig:
                with tempfile.TemporaryDirectory() as tmpdir:
                    with mock.patch("sys.argv", ["tickle", tmpdir]):
                        main()
                        mock_reconfig.assert_not_called()
