"""Git integration utilities for enriching tasks with blame information."""

import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime


@dataclass
class BlameInfo:
    """Information from git blame for a specific line.

    Attributes:
        author: Name of the person who last modified this line
        author_email: Email of the author
        commit_hash: Full commit hash
        commit_date: ISO format date string of the commit
        commit_message: First line of the commit message
    """
    author: str
    author_email: str
    commit_hash: str
    commit_date: str
    commit_message: str


def is_git_available() -> bool:
    """Check if git binary is available in PATH.

    Returns:
        True if git is available, False otherwise
    """
    return shutil.which("git") is not None


def get_git_root(filepath: str) -> str | None:
    """Find the git repository root for a given file.

    Args:
        filepath: Path to a file that may be in a git repository

    Returns:
        Absolute path to the git repository root, or None if not in a git repo
    """
    if not is_git_available():
        return None

    try:
        # Get the directory containing the file
        file_dir = os.path.dirname(os.path.abspath(filepath))

        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],  # noqa: S607
            cwd=file_dir,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=5
        )

        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (subprocess.SubprocessError, OSError):
        return None


def is_in_git_repo(filepath: str) -> bool:
    """Check if a file is in a git repository.

    Args:
        filepath: Path to the file to check

    Returns:
        True if the file is in a git repository, False otherwise
    """
    return get_git_root(filepath) is not None


def should_skip_blame(filepath: str, line_count_threshold: int = 1000) -> bool:
    """Determine if git blame should be skipped for a file.

    Args:
        filepath: Path to the file
        line_count_threshold: Maximum number of lines before skipping blame

    Returns:
        True if blame should be skipped, False otherwise
    """
    try:
        with open(filepath, encoding='utf-8') as f:
            line_count = sum(1 for _ in f)
        return line_count > line_count_threshold
    except (OSError, UnicodeDecodeError):
        # If we can't read the file, skip blame
        return True


def parse_git_blame_porcelain(output: str) -> dict[int, BlameInfo]:
    """Parse git blame --porcelain output.

    Args:
        output: Raw output from git blame --porcelain command

    Returns:
        Dictionary mapping line numbers (1-indexed) to BlameInfo objects
    """
    blame_info: dict[int, BlameInfo] = {}
    commit_cache: dict[str, BlameInfo] = {}  # Cache commit info for reuse
    lines = output.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i]

        # Each blame section starts with a commit hash and line numbers
        if not line or line.startswith('\t'):
            i += 1
            continue

        # Parse the header line: <commit> <original-line> <final-line> [<num-lines>]
        parts = line.split()
        if len(parts) < 3:
            i += 1
            continue

        commit_hash = parts[0]
        final_line = int(parts[2])

        # Skip uncommitted lines
        if commit_hash == '0000000000000000000000000000000000000000':
            i += 1
            # Skip any metadata and content line
            while i < len(lines) and not lines[i].startswith('\t'):
                i += 1
            if i < len(lines) and lines[i].startswith('\t'):
                i += 1
            continue

        # Check if we've seen this commit before
        if commit_hash in commit_cache:
            # Reuse cached commit info
            blame_info[final_line] = commit_cache[commit_hash]
            i += 1
            # Skip any metadata lines (may or may not be present)
            while i < len(lines) and not lines[i].startswith('\t'):
                i += 1
            if i < len(lines) and lines[i].startswith('\t'):
                i += 1
            continue

        # Extract metadata from subsequent lines (first occurrence of commit)
        author = ""
        author_email = ""
        author_time = ""
        summary = ""

        i += 1
        while i < len(lines) and not lines[i].startswith('\t'):
            if lines[i].startswith('author '):
                author = lines[i][7:]
            elif lines[i].startswith('author-mail '):
                # Remove < and > from email
                author_email = lines[i][12:].strip('<>')
            elif lines[i].startswith('author-time '):
                # Convert Unix timestamp to ISO format
                timestamp = int(lines[i][12:])
                author_time = datetime.fromtimestamp(timestamp).isoformat()
            elif lines[i].startswith('summary '):
                summary = lines[i][8:]
            i += 1

        # Store the blame info and cache it
        if author:
            info = BlameInfo(
                author=author,
                author_email=author_email,
                commit_hash=commit_hash,
                commit_date=author_time,
                commit_message=summary
            )
            blame_info[final_line] = info
            commit_cache[commit_hash] = info

        # Skip the actual line content (starts with tab)
        if i < len(lines) and lines[i].startswith('\t'):
            i += 1

    return blame_info


def get_file_blame(filepath: str) -> dict[int, BlameInfo]:
    """Get git blame information for all lines in a file.

    Args:
        filepath: Path to the file to blame

    Returns:
        Dictionary mapping line numbers (1-indexed) to BlameInfo objects.
        Returns empty dict if blame fails or file should be skipped.
    """
    # Check if we should skip this file
    if not is_git_available():
        return {}

    if not is_in_git_repo(filepath):
        return {}

    if should_skip_blame(filepath):
        return {}

    try:
        # Get the git root to use as working directory
        git_root = get_git_root(filepath)
        if not git_root:
            return {}

        # Make the file path relative to git root for the command
        abs_filepath = os.path.abspath(filepath)
        rel_filepath = os.path.relpath(abs_filepath, git_root)

        result = subprocess.run(  # noqa: S603
            ["git", "blame", "--porcelain", rel_filepath],  # noqa: S607
            cwd=git_root,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=10
        )

        if result.returncode == 0 and result.stdout:
            return parse_git_blame_porcelain(result.stdout)

        return {}
    except (subprocess.SubprocessError, OSError, ValueError):
        return {}
