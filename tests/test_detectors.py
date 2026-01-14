"""Tests for tickle.detectors module."""

import pytest
from tickle.detectors import (
    Detector,
    CommentMarkerDetector,
    create_detector,
    DEFAULT_TASK_MARKERS,
)
from tickle.models import Task


class TestCommentMarkerDetector:
    """Unit tests for CommentMarkerDetector."""

    def test_constructor_with_single_marker(self):
        """Constructor accepts single marker."""
        detector = CommentMarkerDetector(markers=["TODO"])
        assert detector.markers == ["TODO"]

    def test_constructor_with_multiple_markers(self):
        """Constructor accepts multiple markers."""
        detector = CommentMarkerDetector(markers=["TODO", "FIXME", "BUG"])
        assert set(detector.markers) == {"TODO", "FIXME", "BUG"}

    def test_constructor_with_default_markers(self):
        """Constructor uses DEFAULT_TASK_MARKERS when None provided."""
        detector = CommentMarkerDetector(markers=None)
        assert detector.markers == DEFAULT_TASK_MARKERS

    def test_constructor_without_markers_arg(self):
        """Constructor uses DEFAULT_TASK_MARKERS when not specified."""
        detector = CommentMarkerDetector()
        assert detector.markers == DEFAULT_TASK_MARKERS

    def test_detect_finds_single_marker(self):
        """detect() finds marker in line."""
        detector = CommentMarkerDetector(markers=["TODO"])
        tasks = detector.detect("    # TODO: Fix this", 10, "app.py")

        assert len(tasks) == 1
        assert tasks[0].marker == "TODO"
        assert tasks[0].line == 10
        assert tasks[0].file == "app.py"

    def test_detect_returns_empty_for_no_match(self):
        """detect() returns empty list when no marker found."""
        detector = CommentMarkerDetector(markers=["TODO"])
        tasks = detector.detect("    # Regular comment", 5, "app.py")

        assert tasks == []

    def test_detect_finds_first_marker_only(self):
        """detect() returns first marker only if multiple in line."""
        detector = CommentMarkerDetector(markers=["TODO", "FIXME"])
        tasks = detector.detect("# TODO: Fix FIXME later", 1, "app.py")

        assert len(tasks) == 1
        assert tasks[0].marker == "TODO"

    def test_detect_with_python_comment(self):
        """detect() works with Python comment format."""
        detector = CommentMarkerDetector(markers=["TODO"])
        tasks = detector.detect("# TODO: something", 1, "f.py")

        assert len(tasks) == 1
        assert tasks[0].marker == "TODO"

    def test_detect_with_indented_comment(self):
        """detect() works with indented comments."""
        detector = CommentMarkerDetector(markers=["TODO"])
        tasks = detector.detect("        # TODO: something", 2, "f.py")

        assert len(tasks) == 1

    def test_detect_with_no_spaces_around_marker(self):
        """detect() works when marker has no spaces around it."""
        detector = CommentMarkerDetector(markers=["TODO"])
        tasks = detector.detect("#TODO:something", 3, "f.py")

        assert len(tasks) == 1

    def test_detect_case_sensitive(self):
        """detect() is case-sensitive."""
        detector = CommentMarkerDetector(markers=["TODO"])

        assert len(detector.detect("# TODO: something", 1, "f.py")) == 1
        assert len(detector.detect("# todo: something", 2, "f.py")) == 0
        assert len(detector.detect("# Todo: something", 3, "f.py")) == 0

    def test_detect_strips_text(self):
        """detect() returns stripped text."""
        detector = CommentMarkerDetector(markers=["TODO"])
        tasks = detector.detect("    # TODO: something    \n", 1, "f.py")

        assert tasks[0].text == "# TODO: something"

    def test_detect_with_no_markers_configured(self):
        """detect() with empty marker list."""
        detector = CommentMarkerDetector(markers=[])
        tasks = detector.detect("# TODO: something", 1, "f.py")

        assert tasks == []

    def test_detect_multiple_markers_configured(self):
        """detect() checks all configured markers."""
        detector = CommentMarkerDetector(markers=["TODO", "FIXME", "BUG"])

        assert len(detector.detect("# TODO: x", 1, "f.py")) == 1
        assert len(detector.detect("# FIXME: x", 2, "f.py")) == 1
        assert len(detector.detect("# BUG: x", 3, "f.py")) == 1
        assert len(detector.detect("# NOTE: x", 4, "f.py")) == 0

    def test_detect_marker_at_end_of_line(self):
        """detect() finds marker even at line end."""
        detector = CommentMarkerDetector(markers=["TODO"])
        tasks = detector.detect("code = 5  # TODO", 1, "f.py")

        assert len(tasks) == 1
        assert tasks[0].marker == "TODO"

    def test_detect_marker_in_middle_of_line(self):
        """detect() finds marker in middle of line."""
        detector = CommentMarkerDetector(markers=["TODO"])
        tasks = detector.detect("print('TODO') # important", 1, "f.py")

        assert len(tasks) == 1
        assert tasks[0].marker == "TODO"

    def test_detect_with_empty_string(self):
        """detect() handles empty line."""
        detector = CommentMarkerDetector(markers=["TODO"])
        tasks = detector.detect("", 1, "f.py")

        assert tasks == []

    def test_detect_with_only_marker(self):
        """detect() handles line with only marker."""
        detector = CommentMarkerDetector(markers=["TODO"])
        tasks = detector.detect("# TODO", 1, "f.py")

        assert len(tasks) == 1
        assert tasks[0].text == "# TODO"

    def test_detect_with_whitespace_only_line(self):
        """detect() handles whitespace-only line."""
        detector = CommentMarkerDetector(markers=["TODO"])
        tasks = detector.detect("    \t   ", 1, "f.py")

        assert tasks == []

    def test_detect_returns_task_with_correct_filepath(self):
        """detect() stores filepath correctly."""
        detector = CommentMarkerDetector(markers=["TODO"])
        tasks = detector.detect("# TODO: x", 5, "src/main.py")

        assert tasks[0].file == "src/main.py"

    def test_detect_returns_task_with_correct_line_number(self):
        """detect() stores line number correctly."""
        detector = CommentMarkerDetector(markers=["TODO"])
        tasks = detector.detect("# TODO: x", 42, "f.py")

        assert tasks[0].line == 42

    def test_detect_all_default_markers(self):
        """detect() finds all default markers."""
        detector = CommentMarkerDetector()

        assert len(detector.detect("# TODO: x", 1, "f.py")) == 1
        assert len(detector.detect("# FIXME: x", 2, "f.py")) == 1
        assert len(detector.detect("# BUG: x", 3, "f.py")) == 1
        assert len(detector.detect("# NOTE: x", 4, "f.py")) == 1
        assert len(detector.detect("# HACK: x", 5, "f.py")) == 1

    def test_detect_marker_priority_by_list_order(self):
        """detect() respects marker list order for priority."""
        detector = CommentMarkerDetector(markers=["FIXME", "TODO"])
        # Line has both TODO and FIXME, but FIXME is checked first
        tasks = detector.detect("# TODO and FIXME both here", 1, "f.py")

        assert len(tasks) == 1
        assert tasks[0].marker == "FIXME"


class TestDetectorFactory:
    """Test detector factory function."""

    def test_factory_creates_comment_detector(self):
        """factory creates CommentMarkerDetector."""
        detector = create_detector("comment", markers=["TODO"])

        assert isinstance(detector, CommentMarkerDetector)

    def test_factory_passes_markers_to_detector(self):
        """factory passes markers to detector constructor."""
        detector = create_detector("comment", markers=["TODO", "FIXME"])

        assert set(detector.markers) == {"TODO", "FIXME"}

    def test_factory_with_default_markers(self):
        """factory uses default markers if not specified."""
        detector = create_detector("comment")

        assert set(detector.markers) == set(DEFAULT_TASK_MARKERS)

    def test_factory_with_unknown_type_raises(self):
        """factory raises ValueError for unknown detector type."""
        with pytest.raises(ValueError, match="Unknown detector type"):
            create_detector("unknown_type")

    def test_factory_default_type_is_comment(self):
        """factory defaults to 'comment' detector type."""
        detector = create_detector(markers=["TODO"])

        assert isinstance(detector, CommentMarkerDetector)

    def test_factory_creates_new_instance_each_call(self):
        """factory creates independent instances."""
        detector1 = create_detector("comment", markers=["TODO"])
        detector2 = create_detector("comment", markers=["FIXME"])

        assert detector1 is not detector2
        assert detector1.markers != detector2.markers


class TestDetectorInterface:
    """Test that detector implements the Detector interface."""

    def test_comment_detector_is_detector_subclass(self):
        """CommentMarkerDetector inherits from Detector."""
        detector = CommentMarkerDetector(markers=["TODO"])

        assert isinstance(detector, Detector)

    def test_detector_is_abstract(self):
        """Detector cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Detector()

    def test_detector_has_detect_method(self):
        """Detector subclasses have detect method."""
        detector = CommentMarkerDetector(markers=["TODO"])

        assert hasattr(detector, "detect")
        assert callable(detector.detect)
