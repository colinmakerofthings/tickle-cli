# src/tickle/scanner.py
from fnmatch import fnmatch
from pathlib import Path

from tickle.detectors import (
    CompositeDetector,
    Detector,
    MarkdownCheckboxDetector,
    create_detector,
)
from tickle.models import Task, get_sort_key

# Binary and media file extensions to skip
BINARY_EXTENSIONS = {".png", ".jpg", ".jpeg", ".exe", ".bin", ".so", ".dll", ".pyc"}


def _should_ignore_path(filepath: Path, ignore_patterns: list[str], ignore_hidden: bool = True) -> bool:
    """Check if a file path matches any ignore patterns.

    Args:
        filepath: Path object to check
        ignore_patterns: List of glob patterns to match against
        ignore_hidden: Whether to ignore hidden directories (starting with .)

    Returns:
        True if the file should be ignored, False otherwise
    """
    # Ignore hidden directories (starting with .) unless explicitly included
    if ignore_hidden:
        for part in filepath.parts:
            if part.startswith('.') and part != '.':
                return True

    if not ignore_patterns:
        return False

    filepath_str = str(filepath)
    for pattern in ignore_patterns:
        if fnmatch(filepath_str, f"*{pattern}*") or fnmatch(filepath.name, pattern):
            return True
    return False


def scan_directory(
    directory: str,
    markers: list[str] | None = None,
    ignore_patterns: list[str] | None = None,
    detector: Detector | None = None,
    sort_by: str = "file",
    ignore_hidden: bool = True
) -> list[Task]:
    """Recursively scan a directory for task markers.

    Args:
        directory: Root directory to scan
        markers: List of task markers to search for (default: TODO, FIXME, BUG, NOTE, HACK, CHECKBOX)
        ignore_patterns: List of glob patterns to ignore (e.g., ["*.min.js", "node_modules"])
        detector: Detector instance to use for finding tasks. If None, creates a CommentMarkerDetector
                  using the provided markers.
        sort_by: Sort method - "file" (by file and line, default) or "marker" (by marker priority)
        ignore_hidden: Whether to ignore hidden directories starting with . (default: True)

    Returns:
        List of Task objects found in the directory
    """
    if ignore_patterns is None:
        ignore_patterns = []

    # Create detector if not provided
    if detector is None:
        detectors = []
        # Always add comment detector with specified markers
        comment_detector = create_detector("comment", markers=markers)
        detectors.append(comment_detector)

        # Add checkbox detector only if CHECKBOX is in the markers list (or using defaults)
        if markers is None or "CHECKBOX" in markers:
            checkbox_detector = MarkdownCheckboxDetector()
            detectors.append(checkbox_detector)

        detector = CompositeDetector(detectors)

    results: list[Task] = []
    directory_path = Path(directory)

    for filepath in directory_path.rglob("*"):
        # Skip directories
        if filepath.is_dir():
            continue

        # Skip binary files by extension
        if filepath.suffix.lower() in BINARY_EXTENSIONS:
            continue

        # Skip ignored patterns
        if _should_ignore_path(filepath, ignore_patterns, ignore_hidden):
            continue

        try:
            with open(filepath, encoding="utf-8") as f:
                for line_num, line in enumerate(f, start=1):
                    # Use detector to find tasks in this line
                    tasks = detector.detect(line, line_num, str(filepath))
                    results.extend(tasks)
        except Exception:
            # Ignore files that can't be read as text
            pass

    # Sort by specified method
    sort_key = get_sort_key(sort_by)
    results.sort(key=sort_key)
    return results

