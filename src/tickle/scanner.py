# src/tickle/scanner.py
from pathlib import Path

# TODO: Define TASK_MARKERS as configurable list (TODO, FIXME, BUG, NOTE, HACK)
TASK_MARKERS = ["TODO", "FIXME", "BUG", "NOTE", "HACK"]

def scan_directory(directory: str):
    """Recursively scan a directory for task markers."""
    # TODO: Accept markers parameter to filter by specific task types
    # TODO: Accept ignore_patterns parameter for .gitignore-style file exclusion
    # TODO: Use models.Task dataclass for return values instead of dicts
    results = []

    directory_path = Path(directory)

    for filepath in directory_path.rglob("*"):
        # Skip directories
        if filepath.is_dir():
            continue
        # Optional: skip binary files by extension
        if filepath.suffix in [".png", ".jpg", ".exe", ".bin"]:
            continue

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for i, line in enumerate(f, start=1):
                    # TODO: Check for all markers in TASK_MARKERS, not just TODO
                    for marker in TASK_MARKERS:
                        if marker in line:
                            results.append({
                                "file": str(filepath),
                                "line": i,
                                "text": line.strip(),
                                "marker": marker  # TODO: Add marker type to results
                            })
                            break
        except Exception:
            # Ignore files that can't be read as text
            pass

    return results
