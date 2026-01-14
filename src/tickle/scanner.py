# src/tickle/scanner.py
from fnmatch import fnmatch
from pathlib import Path

from tickle.detectors import Detector, create_detector
from tickle.models import Task

# Binary and media file extensions to skip
BINARY_EXTENSIONS = {".png", ".jpg", ".jpeg", ".exe", ".bin", ".so", ".dll", ".pyc"}


def _should_ignore_path(filepath: Path, ignore_patterns: list[str]) -> bool:
    """Check if a file path matches any ignore patterns.

    Args:
        filepath: Path object to check
        ignore_patterns: List of glob patterns to match against

    Returns:
        True if the file should be ignored, False otherwise
    """
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
    detector: Detector | None = None
) -> list[Task]:
    """Recursively scan a directory for task markers.

    Args:
        directory: Root directory to scan
        markers: List of task markers to search for (default: TODO, FIXME, BUG, NOTE, HACK)
        ignore_patterns: List of glob patterns to ignore (e.g., ["*.min.js", "node_modules"])
        detector: Detector instance to use for finding tasks. If None, creates a CommentMarkerDetector
                  using the provided markers.

    Returns:
        List of Task objects found in the directory
    """
    if ignore_patterns is None:
        ignore_patterns = []

    # Create detector if not provided
    if detector is None:
        detector = create_detector("comment", markers=markers)

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
        if _should_ignore_path(filepath, ignore_patterns):
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

    # Sort by file and line number
    results.sort()
    return results

