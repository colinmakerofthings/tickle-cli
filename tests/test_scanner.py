"""Tests for tickle.scanner module."""

import tempfile
from pathlib import Path

import pytest

from tickle.scanner import scan_directory
from tickle.models import Task
from tickle.detectors import CommentMarkerDetector, create_detector


@pytest.fixture
def sample_repo():
    """Create a temporary sample repository with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create Python file with TODOs
        python_file = tmpdir_path / "example.py"
        python_file.write_text(
            "def hello():\n"
            "    # TODO: Add greeting\n"
            "    pass\n"
            "    # FIXME: Handle None case\n"
        )
        
        # Create another Python file
        another_py = tmpdir_path / "utils.py"
        another_py.write_text(
            "# BUG: Off-by-one error in loop\n"
            "for i in range(10):\n"
            "    # NOTE: This is important\n"
            "    print(i)\n"
        )
        
        # Create a subdirectory with files
        subdir = tmpdir_path / "subdir"
        subdir.mkdir()
        sub_file = subdir / "nested.py"
        sub_file.write_text(
            "# HACK: Temporary workaround\n"
            "# TODO: Refactor this\n"
        )
        
        # Create a binary file (should be skipped)
        binary_file = tmpdir_path / "image.png"
        binary_file.write_bytes(b"\x89PNG\r\n\x1a\n")
        
        yield tmpdir_path


class TestScanDirectory:
    """Test cases for scan_directory function."""
    
    def test_scan_directory_finds_all_markers(self, sample_repo):
        """Test that scan_directory finds all marker types."""
        tasks = scan_directory(str(sample_repo))
        
        assert len(tasks) == 6  # TODO, FIXME, BUG, NOTE, HACK, TODO (in subdir)
        assert all(isinstance(task, Task) for task in tasks)
    
    def test_scan_directory_default_markers(self, sample_repo):
        """Test that default markers include TODO, FIXME, BUG, NOTE, HACK."""
        tasks = scan_directory(str(sample_repo))
        markers = {task.marker for task in tasks}
        
        assert markers == {"TODO", "FIXME", "BUG", "NOTE", "HACK"}
    
    def test_scan_directory_custom_markers(self, sample_repo):
        """Test filtering with custom markers."""
        tasks = scan_directory(str(sample_repo), markers=["TODO", "FIXME"])
        
        assert len(tasks) == 3  # 2 TODOs, 1 FIXME
        markers = {task.marker for task in tasks}
        assert markers == {"TODO", "FIXME"}
    
    def test_scan_directory_single_marker(self, sample_repo):
        """Test filtering by a single marker type."""
        tasks = scan_directory(str(sample_repo), markers=["TODO"])
        
        assert len(tasks) == 2  # Two TODO markers
        assert all(task.marker == "TODO" for task in tasks)
    
    def test_scan_directory_ignore_patterns(self, sample_repo):
        """Test ignore patterns functionality."""
        tasks = scan_directory(str(sample_repo), ignore_patterns=["subdir"])
        
        # Should skip the nested.py file
        files = {task.file for task in tasks}
        assert not any("subdir" in f for f in files)
    
    def test_scan_directory_ignore_multiple_patterns(self, sample_repo):
        """Test multiple ignore patterns."""
        tasks = scan_directory(
            str(sample_repo),
            ignore_patterns=["subdir", "utils.py"]
        )
        
        files = {task.file for task in tasks}
        assert not any("subdir" in f for f in files)
        assert not any("utils.py" in f for f in files)
    
    def test_scan_directory_skips_binary_files(self, sample_repo):
        """Test that binary files are skipped."""
        tasks = scan_directory(str(sample_repo))
        files = {task.file for task in tasks}
        
        # PNG file should not appear
        assert not any(f.endswith(".png") for f in files)
    
    def test_scan_directory_sorts_results(self, sample_repo):
        """Test that results are sorted by file and line number."""
        tasks = scan_directory(str(sample_repo))
        
        # Verify sorting
        for i in range(len(tasks) - 1):
            current = tasks[i]
            next_task = tasks[i + 1]
            assert (current.file, current.line) <= (next_task.file, next_task.line)
    
    def test_task_attributes(self, sample_repo):
        """Test that Task objects have correct attributes."""
        tasks = scan_directory(str(sample_repo), markers=["TODO"])
        
        task = tasks[0]
        assert hasattr(task, "file")
        assert hasattr(task, "line")
        assert hasattr(task, "marker")
        assert hasattr(task, "text")
        assert task.marker == "TODO"
        assert isinstance(task.line, int)
        assert isinstance(task.text, str)
    
    def test_empty_directory(self):
        """Test scanning an empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tasks = scan_directory(tmpdir)
            assert tasks == []
    
    def test_directory_with_no_matches(self):
        """Test scanning directory with no matching markers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            (tmpdir_path / "normal.py").write_text("def hello():\n    pass\n")
            
            tasks = scan_directory(tmpdir, markers=["TODO"])
            assert tasks == []


class TestScanDirectoryWithDetector:
    """Test scan_directory integration with detector instances."""
    
    def test_scan_directory_with_custom_detector(self):
        """Test scan_directory works with custom detector instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            (tmpdir_path / "test.py").write_text(
                "# TODO: First\n"
                "# FIXME: Second\n"
            )
            
            detector = CommentMarkerDetector(markers=["TODO"])
            tasks = scan_directory(str(tmpdir_path), detector=detector)
            
            assert len(tasks) == 1
            assert tasks[0].marker == "TODO"
    
    def test_scan_directory_respects_detector_markers(self):
        """Test that detector's marker list is respected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            (tmpdir_path / "test.py").write_text(
                "# TODO: Item 1\n"
                "# BUG: Item 2\n"
                "# FIXME: Item 3\n"
            )
            
            detector = CommentMarkerDetector(markers=["BUG", "FIXME"])
            tasks = scan_directory(str(tmpdir_path), detector=detector)
            
            markers = {task.marker for task in tasks}
            assert markers == {"BUG", "FIXME"}
            assert len(tasks) == 2
    
    def test_scan_directory_detector_takes_precedence(self):
        """Test that detector parameter takes precedence over markers parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            (tmpdir_path / "test.py").write_text(
                "# TODO: Item 1\n"
                "# FIXME: Item 2\n"
            )
            
            # Pass both detector and markers - detector should win
            detector = CommentMarkerDetector(markers=["TODO"])
            tasks = scan_directory(
                str(tmpdir_path),
                markers=["FIXME"],
                detector=detector
            )
            
            # Should use detector's TODO, not the markers parameter's FIXME
            assert len(tasks) == 1
            assert tasks[0].marker == "TODO"
    
    def test_scan_directory_factory_detector(self):
        """Test scan_directory with detector from factory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            (tmpdir_path / "test.py").write_text("# TODO: Test\n")
            
            detector = create_detector("comment", markers=["TODO"])
            tasks = scan_directory(str(tmpdir_path), detector=detector)
            
            assert len(tasks) == 1
            assert tasks[0].marker == "TODO"
    
    def test_scan_directory_without_detector_uses_markers(self):
        """Test that markers parameter is used when detector not provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            (tmpdir_path / "test.py").write_text(
                "# TODO: Item 1\n"
                "# FIXME: Item 2\n"
            )
            
            # No detector provided, should use markers parameter
            tasks = scan_directory(str(tmpdir_path), markers=["FIXME"])
            
            assert len(tasks) == 1
            assert tasks[0].marker == "FIXME"

