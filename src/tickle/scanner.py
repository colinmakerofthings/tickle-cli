# src/tickle/scanner.py
from fnmatch import fnmatch
from pathlib import Path
from typing import List

from tickle.models import Task

# Default task markers to search for
DEFAULT_TASK_MARKERS = ["TODO", "FIXME", "BUG", "NOTE", "HACK"]

# Binary and media file extensions to skip
BINARY_EXTENSIONS = {".png", ".jpg", ".jpeg", ".exe", ".bin", ".so", ".dll", ".pyc"}


def _should_ignore_path(filepath: Path, ignore_patterns: List[str]) -> bool:
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
    markers: List[str] = None,
    ignore_patterns: List[str] = None
) -> List[Task]:
    """Recursively scan a directory for task markers.
    
    Args:
        directory: Root directory to scan
        markers: List of task markers to search for (default: TODO, FIXME, BUG, NOTE, HACK)
        ignore_patterns: List of glob patterns to ignore (e.g., ["*.min.js", "node_modules"])
        
    Returns:
        List of Task objects found in the directory
    """
    if markers is None:
        markers = DEFAULT_TASK_MARKERS
    if ignore_patterns is None:
        ignore_patterns = []
    
    results: List[Task] = []
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
            with open(filepath, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, start=1):
                    # Check for any marker in the line
                    for marker in markers:
                        if marker in line:
                            task = Task(
                                file=str(filepath),
                                line=line_num,
                                marker=marker,
                                text=line.strip()
                            )
                            results.append(task)
                            break  # Only count first marker match per line
        except Exception:
            # Ignore files that can't be read as text
            pass

    # Sort by file and line number
    results.sort()
    return results

