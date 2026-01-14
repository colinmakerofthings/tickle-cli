"""Tests for tickle.detectors module."""

import pytest

from tickle.detectors import (
    DEFAULT_TASK_MARKERS,
    CommentMarkerDetector,
    Detector,
    create_detector,
)


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


class TestMarkdownCheckboxDetector:
    """Unit tests for MarkdownCheckboxDetector."""

    def test_detect_finds_unchecked_dash_checkbox(self):
        """detect() finds unchecked - [ ] checkbox."""
        from tickle.detectors import MarkdownCheckboxDetector
        detector = MarkdownCheckboxDetector()
        tasks = detector.detect("- [ ] Task to do", 1, "todo.md")

        assert len(tasks) == 1
        assert tasks[0].marker == "CHECKBOX"
        assert tasks[0].line == 1
        assert tasks[0].file == "todo.md"
        assert tasks[0].text == "- [ ] Task to do"

    def test_detect_finds_unchecked_star_checkbox(self):
        """detect() finds unchecked * [ ] checkbox."""
        from tickle.detectors import MarkdownCheckboxDetector
        detector = MarkdownCheckboxDetector()
        tasks = detector.detect("* [ ] Another task", 2, "todo.md")

        assert len(tasks) == 1
        assert tasks[0].marker == "CHECKBOX"

    def test_detect_handles_indentation(self):
        """detect() finds checkboxes with leading whitespace."""
        from tickle.detectors import MarkdownCheckboxDetector
        detector = MarkdownCheckboxDetector()
        tasks = detector.detect("  - [ ] Indented task", 3, "todo.md")

        assert len(tasks) == 1
        assert tasks[0].marker == "CHECKBOX"

    def test_detect_ignores_checked_lowercase_x(self):
        """detect() ignores checked [x] checkbox."""
        from tickle.detectors import MarkdownCheckboxDetector
        detector = MarkdownCheckboxDetector()
        tasks = detector.detect("- [x] Completed task", 4, "todo.md")

        assert tasks == []

    def test_detect_ignores_checked_uppercase_x(self):
        """detect() ignores checked [X] checkbox."""
        from tickle.detectors import MarkdownCheckboxDetector
        detector = MarkdownCheckboxDetector()
        tasks = detector.detect("- [X] Done", 5, "todo.md")

        assert tasks == []

    def test_detect_returns_empty_for_no_match(self):
        """detect() returns empty list for regular text."""
        from tickle.detectors import MarkdownCheckboxDetector
        detector = MarkdownCheckboxDetector()
        tasks = detector.detect("Regular markdown text", 6, "todo.md")

        assert tasks == []

    def test_detect_requires_checkbox_at_start(self):
        """detect() only matches checkboxes at line start."""
        from tickle.detectors import MarkdownCheckboxDetector
        detector = MarkdownCheckboxDetector()
        tasks = detector.detect("Some text - [ ] checkbox", 7, "todo.md")

        assert tasks == []

    def test_detect_finds_checkbox_without_space(self):
        """detect() finds checkboxes with no space between brackets."""
        from tickle.detectors import MarkdownCheckboxDetector
        detector = MarkdownCheckboxDetector()
        tasks = detector.detect("- [] No space task", 8, "todo.md")

        assert len(tasks) == 1
        assert tasks[0].marker == "CHECKBOX"

    def test_detect_finds_checkbox_with_multiple_spaces(self):
        """detect() finds checkboxes with multiple spaces between brackets."""
        from tickle.detectors import MarkdownCheckboxDetector
        detector = MarkdownCheckboxDetector()
        tasks = detector.detect("- [  ] Two spaces", 9, "todo.md")

        assert len(tasks) == 1
        assert tasks[0].marker == "CHECKBOX"


class TestCompositeDetector:
    """Unit tests for CompositeDetector."""

    def test_runs_multiple_detectors(self):
        """CompositeDetector runs all provided detectors."""
        from tickle.detectors import (
            CommentMarkerDetector,
            CompositeDetector,
            MarkdownCheckboxDetector,
        )
        comment_detector = CommentMarkerDetector(markers=["TODO"])
        checkbox_detector = MarkdownCheckboxDetector()
        composite = CompositeDetector([comment_detector, checkbox_detector])

        # Line with both TODO and checkbox
        tasks = composite.detect("- [ ] TODO: Something", 1, "test.md")

        assert len(tasks) == 2
        markers = {task.marker for task in tasks}
        assert markers == {"TODO", "CHECKBOX"}

    def test_combines_results_from_all_detectors(self):
        """CompositeDetector aggregates all task results."""
        from tickle.detectors import CommentMarkerDetector, CompositeDetector
        todo_detector = CommentMarkerDetector(markers=["TODO"])
        fixme_detector = CommentMarkerDetector(markers=["FIXME"])
        composite = CompositeDetector([todo_detector, fixme_detector])

        tasks = composite.detect("# TODO: Fix FIXME", 1, "test.py")

        assert len(tasks) == 2

    def test_returns_empty_when_no_detector_matches(self):
        """CompositeDetector returns empty list when no tasks found."""
        from tickle.detectors import CommentMarkerDetector, CompositeDetector
        detector = CompositeDetector([CommentMarkerDetector(markers=["TODO"])])

        tasks = detector.detect("Regular code", 1, "test.py")

        assert tasks == []

    def test_works_with_empty_detector_list(self):
        """CompositeDetector handles empty detector list."""
        from tickle.detectors import CompositeDetector
        detector = CompositeDetector([])

        tasks = detector.detect("Any line", 1, "test.py")

        assert tasks == []


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
