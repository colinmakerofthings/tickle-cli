"""Tests for git_utils module."""

from unittest.mock import MagicMock, patch

from tickle.git_utils import (
    BlameInfo,
    get_file_blame,
    get_git_root,
    is_git_available,
    is_in_git_repo,
    parse_git_blame_porcelain,
    should_skip_blame,
)


class TestIsGitAvailable:
    """Tests for is_git_available function."""

    def test_git_available_when_git_exists(self):
        """Test that git is detected when available."""
        with patch("shutil.which", return_value="/usr/bin/git"):
            assert is_git_available() is True

    def test_git_not_available_when_git_missing(self):
        """Test that git is not detected when missing."""
        with patch("shutil.which", return_value=None):
            assert is_git_available() is False


class TestGetGitRoot:
    """Tests for get_git_root function."""

    def test_returns_none_when_git_not_available(self):
        """Test that None is returned when git is not available."""
        with patch("tickle.git_utils.is_git_available", return_value=False):
            result = get_git_root("/some/path/file.py")
            assert result is None

    def test_returns_root_when_in_git_repo(self):
        """Test that root path is returned when file is in a git repo."""
        with (
            patch("tickle.git_utils.is_git_available", return_value=True),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(
                returncode=0, stdout="/home/user/project\n"
            )
            result = get_git_root("/home/user/project/src/file.py")
            assert result == "/home/user/project"

    def test_returns_none_when_not_in_git_repo(self):
        """Test that None is returned when file is not in a git repo."""
        with (
            patch("tickle.git_utils.is_git_available", return_value=True),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=128)
            result = get_git_root("/some/path/file.py")
            assert result is None

    def test_returns_none_on_subprocess_error(self):
        """Test that None is returned when subprocess raises an error."""
        with (
            patch("tickle.git_utils.is_git_available", return_value=True),
            patch("subprocess.run", side_effect=OSError),
        ):
            result = get_git_root("/some/path/file.py")
            assert result is None


class TestIsInGitRepo:
    """Tests for is_in_git_repo function."""

    def test_returns_true_when_git_root_found(self):
        """Test that True is returned when file is in a git repo."""
        with patch("tickle.git_utils.get_git_root", return_value="/home/user/project"):
            assert is_in_git_repo("/home/user/project/src/file.py") is True

    def test_returns_false_when_git_root_not_found(self):
        """Test that False is returned when file is not in a git repo."""
        with patch("tickle.git_utils.get_git_root", return_value=None):
            assert is_in_git_repo("/some/path/file.py") is False


class TestShouldSkipBlame:
    """Tests for should_skip_blame function."""

    def test_skips_large_files(self, tmp_path):
        """Test that files larger than threshold are skipped."""
        # Create a file with 1001 lines
        test_file = tmp_path / "large.txt"
        test_file.write_text("\n" * 1001)

        result = should_skip_blame(str(test_file), line_count_threshold=1000)
        assert result is True

    def test_does_not_skip_small_files(self, tmp_path):
        """Test that files smaller than threshold are not skipped."""
        # Create a file with 999 lines
        test_file = tmp_path / "small.txt"
        test_file.write_text("\n" * 999)

        result = should_skip_blame(str(test_file), line_count_threshold=1000)
        assert result is False

    def test_skips_unreadable_files(self):
        """Test that unreadable files are skipped."""
        result = should_skip_blame("/nonexistent/file.py")
        assert result is True


class TestParseGitBlamePorcelain:
    """Tests for parse_git_blame_porcelain function."""

    def test_parses_simple_blame_output(self):
        """Test parsing of simple git blame porcelain output."""
        porcelain_output = """abc123def 1 1 1
author John Doe
author-mail <john@example.com>
author-time 1234567890
summary Initial commit
\tprint("Hello, world!")
"""
        result = parse_git_blame_porcelain(porcelain_output)

        assert 1 in result
        assert result[1].author == "John Doe"
        assert result[1].author_email == "john@example.com"
        assert result[1].commit_hash == "abc123def"
        assert result[1].commit_message == "Initial commit"

    def test_parses_multiple_lines(self):
        """Test parsing of blame output with multiple lines."""
        porcelain_output = """abc123def 1 1 1
author John Doe
author-mail <john@example.com>
author-time 1234567890
summary Initial commit
\tprint("Hello, world!")
def456abc 2 2 1
author Jane Smith
author-mail <jane@example.com>
author-time 1234567900
summary Add feature
\tprint("Goodbye!")
"""
        result = parse_git_blame_porcelain(porcelain_output)

        assert len(result) == 2
        assert result[1].author == "John Doe"
        assert result[2].author == "Jane Smith"

    def test_ignores_uncommitted_lines(self):
        """Test that uncommitted lines (zero hash) are ignored."""
        porcelain_output = """0000000000000000000000000000000000000000 1 1 1
author Not Committed Yet
author-mail <none@none.com>
author-time 0
summary
\tprint("Uncommitted line")
"""
        result = parse_git_blame_porcelain(porcelain_output)

        assert len(result) == 0

    def test_handles_empty_output(self):
        """Test handling of empty blame output."""
        result = parse_git_blame_porcelain("")
        assert result == {}


class TestGetFileBlame:
    """Tests for get_file_blame function."""

    def test_returns_empty_when_git_not_available(self):
        """Test that empty dict is returned when git is not available."""
        with patch("tickle.git_utils.is_git_available", return_value=False):
            result = get_file_blame("/some/file.py")
            assert result == {}

    def test_returns_empty_when_not_in_git_repo(self):
        """Test that empty dict is returned when file is not in a git repo."""
        with (
            patch("tickle.git_utils.is_git_available", return_value=True),
            patch("tickle.git_utils.is_in_git_repo", return_value=False),
        ):
            result = get_file_blame("/some/file.py")
            assert result == {}

    def test_returns_empty_when_file_should_be_skipped(self):
        """Test that empty dict is returned when file should be skipped."""
        with (
            patch("tickle.git_utils.is_git_available", return_value=True),
            patch("tickle.git_utils.is_in_git_repo", return_value=True),
            patch("tickle.git_utils.should_skip_blame", return_value=True),
        ):
            result = get_file_blame("/some/file.py")
            assert result == {}

    def test_returns_blame_info_on_success(self):
        """Test that blame info is returned on successful git blame."""
        with (
            patch("tickle.git_utils.is_git_available", return_value=True),
            patch("tickle.git_utils.is_in_git_repo", return_value=True),
            patch("tickle.git_utils.should_skip_blame", return_value=False),
            patch("tickle.git_utils.get_git_root", return_value="/project"),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="""abc123def 1 1 1
author John Doe
author-mail <john@example.com>
author-time 1234567890
summary Initial commit
\tprint("Hello")
""",
            )
            result = get_file_blame("/project/src/file.py")

            assert 1 in result
            assert result[1].author == "John Doe"

    def test_returns_empty_on_git_error(self):
        """Test that empty dict is returned when git command fails."""
        with (
            patch("tickle.git_utils.is_git_available", return_value=True),
            patch("tickle.git_utils.is_in_git_repo", return_value=True),
            patch("tickle.git_utils.should_skip_blame", return_value=False),
            patch("tickle.git_utils.get_git_root", return_value="/project"),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=1)
            result = get_file_blame("/project/src/file.py")
            assert result == {}


class TestBlameInfo:
    """Tests for BlameInfo dataclass."""

    def test_blame_info_creation(self):
        """Test that BlameInfo can be created with all fields."""
        info = BlameInfo(
            author="John Doe",
            author_email="john@example.com",
            commit_hash="abc123",
            commit_date="2024-01-01T12:00:00",
            commit_message="Initial commit",
        )

        assert info.author == "John Doe"
        assert info.author_email == "john@example.com"
        assert info.commit_hash == "abc123"
        assert info.commit_date == "2024-01-01T12:00:00"
        assert info.commit_message == "Initial commit"
