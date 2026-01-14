"""Tests for tickle.output module."""

import json

import pytest

from tickle.models import Task


class TestTaskFormatting:
    """Test Task object formatting for different output formats."""
    
    @pytest.fixture
    def sample_tasks(self):
        """Create sample Task objects for testing."""
        return [
            Task(file="src/main.py", line=5, marker="TODO", text="# TODO: Implement feature"),
            Task(file="src/main.py", line=12, marker="FIXME", text="# FIXME: Fix bug"),
            Task(file="tests/test.py", line=3, marker="BUG", text="# BUG: Known issue"),
        ]
    
    def test_task_str_format(self, sample_tasks):
        """Test Task.__str__() produces readable output."""
        task = sample_tasks[0]
        result = str(task)
        
        assert "src/main.py" in result
        assert "5" in result
        assert "TODO" in result
        assert "# TODO: Implement feature" in result
    
    def test_task_to_dict(self, sample_tasks):
        """Test Task.to_dict() returns proper dictionary."""
        task = sample_tasks[0]
        result = task.to_dict()
        
        assert isinstance(result, dict)
        assert result["file"] == "src/main.py"
        assert result["line"] == 5
        assert result["marker"] == "TODO"
        assert result["text"] == "# TODO: Implement feature"
    
    def test_task_sorting(self, sample_tasks):
        """Test Task objects can be sorted by file and line."""
        tasks = sample_tasks.copy()
        tasks.reverse()
        tasks.sort()
        
        # Should be sorted by file first, then line
        assert tasks[0].file == "src/main.py"
        assert tasks[0].line == 5
        assert tasks[1].file == "src/main.py"
        assert tasks[1].line == 12
        assert tasks[2].file == "tests/test.py"
    
    def test_tasks_json_serializable(self, sample_tasks):
        """Test that Task objects can be serialized to JSON."""
        task_dicts = [task.to_dict() for task in sample_tasks]
        
        # Should be valid JSON
        json_str = json.dumps(task_dicts)
        parsed = json.loads(json_str)
        
        assert len(parsed) == 3
        assert parsed[0]["marker"] == "TODO"
    
    def test_task_comparison_operators(self):
        """Test Task comparison for sorting."""
        task1 = Task(file="a.py", line=1, marker="TODO", text="text1")
        task2 = Task(file="a.py", line=2, marker="TODO", text="text2")
        task3 = Task(file="b.py", line=1, marker="TODO", text="text3")
        
        assert task1 < task2  # Same file, different line
        assert task2 < task3  # Different file
        assert task1 < task3  # Different file and line
