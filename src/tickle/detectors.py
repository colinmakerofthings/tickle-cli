# src/tickle/detectors.py
"""Task detectors for finding task markers in source code."""

from abc import ABC, abstractmethod
from typing import List
from tickle.models import Task

# Default task markers to search for
DEFAULT_TASK_MARKERS = ["TODO", "FIXME", "BUG", "NOTE", "HACK"]


class Detector(ABC):
    """Abstract base class for task detectors."""
    
    @abstractmethod
    def detect(self, line: str, line_num: int, filepath: str) -> List[Task]:
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
    
    def __init__(self, markers: List[str] = None):
        """Initialize detector with markers to search for.
        
        Args:
            markers: List of marker strings to detect (e.g., ["TODO", "FIXME"])
                    If None, uses DEFAULT_TASK_MARKERS
        """
        self.markers = markers if markers is not None else DEFAULT_TASK_MARKERS
    
    def detect(self, line: str, line_num: int, filepath: str) -> List[Task]:
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
                    file=filepath,
                    line=line_num,
                    marker=marker,
                    text=line.strip()
                )
                return [task]
        
        return []


def create_detector(detector_type: str = "comment", markers: List[str] = None) -> Detector:
    """Factory function to create a detector instance.
    
    Args:
        detector_type: Type of detector to create (currently only "comment" supported)
        markers: List of markers for the detector (uses defaults if None)
        
    Returns:
        A Detector instance
        
    Raises:
        ValueError: If detector_type is not recognized
    """
    if detector_type == "comment":
        return CommentMarkerDetector(markers=markers)
    else:
        raise ValueError(f"Unknown detector type: {detector_type}")
