# src/tickle/detectors.py
"""Task detectors for finding task markers in source code."""

from abc import ABC, abstractmethod

from tickle.models import Task

# Default task markers to search for
DEFAULT_TASK_MARKERS = ["TODO", "FIXME", "BUG", "NOTE", "HACK", "CHECKBOX"]


class Detector(ABC):
    """Abstract base class for task detectors."""

    @abstractmethod
    def detect(self, line: str, line_num: int, filepath: str) -> list[Task]:
        """Detect tasks in a line of text.

        Args:
            line: The line of text to search
            line_num: The line number (1-indexed)
            filepath: The path to the file being scanned

        Returns:
            List of Task objects found in this line
        """
        pass


class CommentMarkerDetector(Detector):
    """Detector that finds task markers as substrings in lines (e.g., in comments)."""

    def __init__(self, markers: list[str] | None = None):
        """Initialize detector with markers to search for.

        Args:
            markers: list of marker strings to detect (e.g., ["TODO", "FIXME"])
                    If None, uses DEFAULT_TASK_MARKERS
        """
        self.markers = markers if markers is not None else DEFAULT_TASK_MARKERS

    def detect(self, line: str, line_num: int, filepath: str) -> list[Task]:
        """Find the first marker in the line.

        Args:
            line: The line of text to search
            line_num: The line number (1-indexed)
            filepath: The path to the file being scanned

        Returns:
            List containing one Task if a marker is found, empty list otherwise
        """
        # Check for any marker in the line
        for marker in self.markers:
            if marker in line:
                task = Task(
                    file=filepath, line=line_num, marker=marker, text=line.strip()
                )
                return [task]

        return []


class MarkdownCheckboxDetector(Detector):
    """Detector that finds unchecked markdown checkboxes."""

    def __init__(self):
        """Initialize the markdown checkbox detector."""
        import re

        # Pattern matches: - [ ] or * [ ] (with optional space) and optional leading whitespace
        self.pattern = re.compile(r"^\s*[-*]\s+\[\s*\]")

    def detect(self, line: str, line_num: int, filepath: str) -> list[Task]:
        """Find unchecked markdown checkboxes in the line.

        Args:
            line: The line of text to search
            line_num: The line number (1-indexed)
            filepath: The path to the file being scanned

        Returns:
            List containing one Task if an unchecked checkbox is found, empty list otherwise
        """
        if self.pattern.match(line):
            task = Task(
                file=filepath, line=line_num, marker="CHECKBOX", text=line.strip()
            )
            return [task]
        return []


class CompositeDetector(Detector):
    """Detector that runs multiple detectors and combines their results."""

    def __init__(self, detectors: list[Detector]):
        """Initialize with a list of detectors to run.

        Args:
            detectors: List of Detector instances to run on each line
        """
        self.detectors = detectors

    def detect(self, line: str, line_num: int, filepath: str) -> list[Task]:
        """Run all detectors and aggregate results.

        Args:
            line: The line of text to search
            line_num: The line number (1-indexed)
            filepath: The path to the file being scanned

        Returns:
            List of all Task objects found by any detector
        """
        results = []
        for detector in self.detectors:
            tasks = detector.detect(line, line_num, filepath)
            results.extend(tasks)
        return results


def create_detector(
    detector_type: str = "comment", markers: list[str] | None = None
) -> Detector:
    """Factory function to create a detector instance.

    Args:
        detector_type: Type of detector to create (currently only "comment" supported)
        markers: list of markers for the detector (uses defaults if None)

    Returns:
        A Detector instance

    Raises:
        ValueError: If detector_type is not recognized
    """
    if detector_type == "comment":
        return CommentMarkerDetector(markers=markers)
    else:
        raise ValueError(f"Unknown detector type: {detector_type}")
