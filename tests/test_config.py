"""Tests for tickle.config module."""

import os
import tempfile
import warnings
from pathlib import Path
from unittest import mock

from tickle.config import (
    TickleConfig,
    create_minimal_config,
    find_config_file,
    format_config_for_display,
    get_user_config_path,
    load_config,
    merge_config_with_args,
)


class TestGetUserConfigPath:
    """Test cases for get_user_config_path function."""

    def test_windows_path(self):
        """Test user config path on Windows."""
        with mock.patch("sys.platform", "win32"):
            with mock.patch.dict(
                os.environ, {"APPDATA": "C:\\Users\\Test\\AppData\\Roaming"}
            ):
                path = get_user_config_path()
                assert path == Path(
                    "C:\\Users\\Test\\AppData\\Roaming\\tickle\\tickle.toml"
                )

    def test_unix_path(self):
        """Test user config path on Unix systems."""
        with mock.patch("sys.platform", "linux"):
            with mock.patch("pathlib.Path.home", return_value=Path("/home/test")):
                path = get_user_config_path()
                assert path == Path("/home/test/.config/tickle/tickle.toml")

    def test_macos_path(self):
        """Test user config path on macOS."""
        with mock.patch("sys.platform", "darwin"):
            with mock.patch("pathlib.Path.home", return_value=Path("/Users/test")):
                path = get_user_config_path()
                assert path == Path("/Users/test/.config/tickle/tickle.toml")


class TestFindConfigFile:
    """Test cases for find_config_file function."""

    def test_find_tickle_toml(self):
        """Test finding tickle.toml in current directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "tickle.toml"
            config_path.write_text("[tickle]\nmarkers = ['TODO']")

            found = find_config_file(start_path=tmpdir)
            assert found.resolve() == config_path.resolve()

    def test_find_dot_tickle_toml(self):
        """Test finding .tickle.toml in current directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".tickle.toml"
            config_path.write_text("[tickle]\nmarkers = ['TODO']")

            found = find_config_file(start_path=tmpdir)
            assert found.resolve() == config_path.resolve()

    def test_find_pyproject_toml(self):
        """Test finding pyproject.toml with [tool.tickle] section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pyproject = Path(tmpdir) / "pyproject.toml"
            pyproject.write_text("[tool.tickle]\nmarkers = ['TODO']")

            found = find_config_file(start_path=tmpdir)
            assert found.resolve() == pyproject.resolve()

    def test_precedence_tickle_over_pyproject(self):
        """Test that tickle.toml takes precedence over pyproject.toml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tickle_config = Path(tmpdir) / "tickle.toml"
            tickle_config.write_text("[tickle]\nmarkers = ['TODO']")

            pyproject = Path(tmpdir) / "pyproject.toml"
            pyproject.write_text("[tool.tickle]\nmarkers = ['FIXME']")

            found = find_config_file(start_path=tmpdir)
            assert found.resolve() == tickle_config.resolve()

    def test_config_override(self):
        """Test explicit config file override."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_config = Path(tmpdir) / "custom.toml"
            custom_config.write_text("[tickle]\nmarkers = ['TODO']")

            found = find_config_file(
                start_path=tmpdir, config_override=str(custom_config)
            )
            assert found == custom_config

    def test_config_override_not_found_warns(self):
        """Test warning when override config doesn't exist."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            found = find_config_file(config_override="/nonexistent/config.toml")
            assert found is None
            assert len(w) == 1
            assert "Config file not found" in str(w[0].message)

    def test_no_config_found(self):
        """Test when no config file is found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            found = find_config_file(start_path=tmpdir)
            assert found is None

    def test_pyproject_without_tickle_section(self):
        """Test pyproject.toml without [tool.tickle] is ignored."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pyproject = Path(tmpdir) / "pyproject.toml"
            pyproject.write_text("[tool.other]\nname = 'test'")

            found = find_config_file(start_path=tmpdir)
            assert found is None


class TestLoadConfig:
    """Test cases for load_config function."""

    def test_load_empty_config(self):
        """Test loading with no config file returns empty TickleConfig."""
        config = load_config(None)
        assert isinstance(config, TickleConfig)
        assert config.markers is None
        assert config.ignore is None

    def test_load_basic_config(self):
        """Test loading basic configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "tickle.toml"
            config_path.write_text(
                """
[tickle]
markers = ["TODO", "FIXME"]
ignore = ["node_modules", "*.min.js"]
format = "json"
sort = "marker"
"""
            )

            config = load_config(config_path)
            assert config.markers == ["TODO", "FIXME"]
            assert config.ignore == ["node_modules", "*.min.js"]
            assert config.format == "json"
            assert config.sort == "marker"

    def test_load_boolean_options(self):
        """Test loading boolean configuration options."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "tickle.toml"
            config_path.write_text(
                """
[tickle]
reverse = true
include_hidden = true
git_blame = false
git_verbose = true
tree_collapse = true
"""
            )

            config = load_config(config_path)
            assert config.reverse is True
            assert config.include_hidden is True
            assert config.git_blame is False
            assert config.git_verbose is True
            assert config.tree_collapse is True

    def test_load_pyproject_toml(self):
        """Test loading from pyproject.toml [tool.tickle] section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "pyproject.toml"
            config_path.write_text(
                """
[tool.tickle]
markers = ["BUG"]
ignore = ["dist"]
"""
            )

            config = load_config(config_path)
            assert config.markers == ["BUG"]
            assert config.ignore == ["dist"]

    def test_invalid_markers_type_warns(self):
        """Test warning for invalid markers type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "tickle.toml"
            config_path.write_text('[tickle]\nmarkers = "TODO"')  # Should be list

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                config = load_config(config_path)
                assert config.markers is None
                assert len(w) == 1
                assert "Invalid 'markers'" in str(w[0].message)

    def test_invalid_format_value_warns(self):
        """Test warning for invalid format value."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "tickle.toml"
            config_path.write_text('[tickle]\nformat = "invalid"')

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                config = load_config(config_path)
                assert config.format is None
                assert len(w) == 1
                assert "Invalid 'format'" in str(w[0].message)

    def test_invalid_sort_value_warns(self):
        """Test warning for invalid sort value."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "tickle.toml"
            config_path.write_text('[tickle]\nsort = "invalid"')

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                config = load_config(config_path)
                assert config.sort is None
                assert len(w) == 1
                assert "Invalid 'sort'" in str(w[0].message)

    def test_unknown_keys_warn(self):
        """Test warning for unknown configuration keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "tickle.toml"
            config_path.write_text(
                """
[tickle]
markers = ["TODO"]
unknown_key = "value"
another_unknown = 123
"""
            )

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                config = load_config(config_path)
                assert config.markers == ["TODO"]
                assert len(w) == 1
                assert "Unknown configuration keys" in str(w[0].message)
                assert "unknown_key" in str(w[0].message)

    def test_malformed_toml_warns(self):
        """Test warning for malformed TOML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "tickle.toml"
            config_path.write_text("this is not valid toml [[[")

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                config = load_config(config_path)
                assert isinstance(config, TickleConfig)
                assert len(w) == 1
                assert "Failed to parse config file" in str(w[0].message)

    def test_partial_config(self):
        """Test loading partial configuration (only some options set)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "tickle.toml"
            config_path.write_text('[tickle]\nignore = ["build"]')

            config = load_config(config_path)
            assert config.ignore == ["build"]
            assert config.markers is None
            assert config.format is None


class TestMergeConfigWithArgs:
    """Test cases for merge_config_with_args function."""

    def test_cli_args_override_config(self):
        """Test that CLI arguments override config values."""
        config = TickleConfig(
            markers=["TODO"], ignore=["build"], format="json", sort="marker"
        )

        # Mock CLI args with non-default values
        args = mock.Mock()
        args.markers = "FIXME,BUG"  # Override
        args.ignore = "dist"  # Override
        args.format = "markdown"  # Override
        args.sort = "age"  # Override
        args.reverse = False
        args.include_hidden = False
        args.no_blame = False
        args.git_verbose = False
        args.tree_collapse = False
        args.path = "."

        merged = merge_config_with_args(config, args)

        assert merged["markers"] == ["FIXME", "BUG"]
        assert merged["ignore_patterns"] == ["dist"]
        assert merged["format"] == "markdown"
        assert merged["sort"] == "age"

    def test_config_used_when_cli_at_defaults(self):
        """Test that config values are used when CLI is at defaults."""
        config = TickleConfig(
            markers=["TODO", "FIXME"],
            ignore=["node_modules"],
            format="json",
            sort="marker",
        )

        # Mock CLI args with default values
        args = mock.Mock()
        args.markers = "TODO,FIXME,BUG,NOTE,HACK,CHECKBOX"  # Default
        args.ignore = ""  # Default
        args.format = "tree"  # Default
        args.sort = "file"  # Default
        args.reverse = False
        args.include_hidden = False
        args.no_blame = False
        args.git_verbose = False
        args.tree_collapse = False
        args.path = "."

        merged = merge_config_with_args(config, args)

        assert merged["markers"] == ["TODO", "FIXME"]
        assert merged["ignore_patterns"] == ["node_modules"]
        assert merged["format"] == "json"
        assert merged["sort"] == "marker"

    def test_boolean_flags_from_config(self):
        """Test boolean flags use config when CLI flag not set."""
        config = TickleConfig(
            reverse=True,
            include_hidden=True,
            git_blame=False,
            git_verbose=True,
            tree_collapse=True,
        )

        args = mock.Mock()
        args.markers = "TODO,FIXME,BUG,NOTE,HACK,CHECKBOX"
        args.ignore = ""
        args.format = "tree"
        args.sort = "file"
        args.reverse = False  # Not set by user
        args.include_hidden = False  # Not set by user
        args.no_blame = False  # Not set by user
        args.git_verbose = False  # Not set by user
        args.tree_collapse = False  # Not set by user
        args.path = "."

        merged = merge_config_with_args(config, args)

        assert merged["reverse"] is True
        assert merged["include_hidden"] is True
        assert merged["enable_git_blame"] is False
        assert merged["git_verbose"] is True
        assert merged["tree_collapse"] is True

    def test_cli_no_blame_overrides_config(self):
        """Test --no-blame CLI flag overrides config git_blame setting."""
        config = TickleConfig(git_blame=True)

        args = mock.Mock()
        args.markers = "TODO,FIXME,BUG,NOTE,HACK,CHECKBOX"
        args.ignore = ""
        args.format = "tree"
        args.sort = "file"
        args.reverse = False
        args.include_hidden = False
        args.no_blame = True  # Explicitly disabled
        args.git_verbose = False
        args.tree_collapse = False
        args.path = "."

        merged = merge_config_with_args(config, args)

        assert merged["enable_git_blame"] is False

    def test_empty_config_uses_defaults(self):
        """Test that empty config falls back to CLI defaults."""
        config = TickleConfig()

        args = mock.Mock()
        args.markers = "TODO,FIXME,BUG,NOTE,HACK,CHECKBOX"
        args.ignore = ""
        args.format = "tree"
        args.sort = "file"
        args.reverse = False
        args.include_hidden = False
        args.no_blame = False
        args.git_verbose = False
        args.tree_collapse = False
        args.path = "/some/path"

        merged = merge_config_with_args(config, args)

        assert "TODO" in merged["markers"]
        assert merged["ignore_patterns"] == []
        assert merged["format"] == "tree"
        assert merged["sort"] == "file"
        assert merged["path"] == "/some/path"


class TestCreateMinimalConfig:
    """Test cases for create_minimal_config function."""

    def test_creates_valid_toml(self):
        """Test that generated config is valid TOML."""
        content = create_minimal_config()
        assert "[tickle]" in content
        assert "markers" in content
        assert "ignore" in content

    def test_includes_common_options(self):
        """Test that minimal config includes commonly used options."""
        content = create_minimal_config()
        assert "TODO" in content
        assert "node_modules" in content
        assert "dist" in content

    def test_parseable_toml(self):
        """Test that generated config can be parsed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "tickle.toml"
            content = create_minimal_config()
            config_path.write_text(content)

            # Should load without errors
            config = load_config(config_path)
            assert config.markers is not None
            assert config.ignore is not None


class TestFormatConfigForDisplay:
    """Test cases for format_config_for_display function."""

    def test_format_with_config_path(self):
        """Test formatting config with a path."""
        config = TickleConfig(markers=["TODO"], ignore=["build"])
        path = Path("/test/tickle.toml")

        output = format_config_for_display(config, path)

        assert str(path) in output
        assert "TODO" in output
        assert "build" in output

    def test_format_without_config_path(self):
        """Test formatting config without a path."""
        config = TickleConfig()

        output = format_config_for_display(config, None)

        assert "No configuration file found" in output
        assert "using defaults" in output.lower()

    def test_format_shows_all_options(self):
        """Test that all config options are displayed."""
        config = TickleConfig(
            markers=["TODO"],
            ignore=["dist"],
            format="json",
            sort="marker",
            reverse=True,
            include_hidden=True,
            git_blame=False,
            git_verbose=True,
            tree_collapse=True,
        )

        output = format_config_for_display(config)

        assert "markers" in output
        assert "ignore" in output
        assert "format" in output
        assert "sort" in output
        assert "reverse" in output
        assert "include_hidden" in output
        assert "git_blame" in output
        assert "git_verbose" in output
        assert "tree_collapse" in output


class TestConfigIntegration:
    """Integration tests combining config loading and merging."""

    def test_full_workflow_with_project_config(self):
        """Test complete workflow: find -> load -> merge."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create project config
            config_path = Path(tmpdir) / "tickle.toml"
            config_path.write_text(
                """
[tickle]
markers = ["BUG", "FIXME"]
ignore = ["node_modules", "dist"]
format = "json"
"""
            )

            # Find config
            found = find_config_file(start_path=tmpdir)
            assert found.resolve() == config_path.resolve()

            # Load config
            config = load_config(found)
            assert config.markers == ["BUG", "FIXME"]
            assert config.format == "json"

            # Merge with CLI args (using defaults)
            args = mock.Mock()
            args.markers = "TODO,FIXME,BUG,NOTE,HACK,CHECKBOX"  # Default
            args.ignore = ""  # Default
            args.format = "tree"  # Default
            args.sort = "file"
            args.reverse = False
            args.include_hidden = False
            args.no_blame = False
            args.git_verbose = False
            args.tree_collapse = False
            args.path = tmpdir

            merged = merge_config_with_args(config, args)

            # Config values should be used
            assert merged["markers"] == ["BUG", "FIXME"]
            assert merged["ignore_patterns"] == ["node_modules", "dist"]
            assert merged["format"] == "json"

    def test_cli_override_project_config(self):
        """Test CLI args override project config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create project config
            config_path = Path(tmpdir) / "tickle.toml"
            config_path.write_text(
                """
[tickle]
markers = ["TODO"]
format = "json"
"""
            )

            found = find_config_file(start_path=tmpdir)
            config = load_config(found)

            # CLI args with explicit values
            args = mock.Mock()
            args.markers = "BUG"  # Override
            args.ignore = "build"  # Override
            args.format = "markdown"  # Override
            args.sort = "marker"
            args.reverse = False
            args.include_hidden = False
            args.no_blame = False
            args.git_verbose = False
            args.tree_collapse = False
            args.path = tmpdir

            merged = merge_config_with_args(config, args)

            # CLI values should be used
            assert merged["markers"] == ["BUG"]
            assert merged["ignore_patterns"] == ["build"]
            assert merged["format"] == "markdown"


class TestBooleanValidation:
    """Test cases for boolean field validation."""

    def test_load_config_invalid_reverse_type(self):
        """Test warning for invalid reverse type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "tickle.toml"
            config_path.write_text('[tickle]\nreverse = "true"\n')

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                config = load_config(config_path)
                assert any("reverse" in str(warning.message).lower() for warning in w)
                assert config.reverse is None  # Invalid value results in None

    def test_load_config_invalid_include_hidden_type(self):
        """Test warning for invalid include_hidden type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "tickle.toml"
            config_path.write_text("[tickle]\ninclude_hidden = 1\n")

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                config = load_config(config_path)
                assert any(
                    "include_hidden" in str(warning.message).lower() for warning in w
                )
                assert config.include_hidden is None  # Invalid value results in None

    def test_load_config_invalid_git_verbose_type(self):
        """Test warning for invalid git_verbose type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "tickle.toml"
            config_path.write_text('[tickle]\ngit_verbose = "yes"\n')

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                load_config(config_path)
                assert any(
                    "git_verbose" in str(warning.message).lower() for warning in w
                )

    def test_load_config_invalid_tree_collapse_type(self):
        """Test warning for invalid tree_collapse type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "tickle.toml"
            config_path.write_text("[tickle]\ntree_collapse = []\n")

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                load_config(config_path)
                assert any(
                    "tree_collapse" in str(warning.message).lower() for warning in w
                )

    def test_load_config_invalid_git_blame_type(self):
        """Test warning for invalid git_blame type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "tickle.toml"
            config_path.write_text('[tickle]\ngit_blame = "false"\n')

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                load_config(config_path)
                assert any("git_blame" in str(warning.message).lower() for warning in w)


class TestMergeEdgeCases:
    """Test edge cases in config merging."""

    def test_merge_config_empty_ignore_string(self):
        """Test merge handles empty ignore string."""
        import argparse

        config = TickleConfig()
        args = argparse.Namespace(
            markers="TODO,FIXME,BUG,NOTE,HACK,CHECKBOX",
            ignore="",
            format="tree",
            sort="file",
            reverse=False,
            include_hidden=False,
            no_blame=False,
            git_verbose=False,
            tree_collapse=False,
            path=".",
        )

        merged = merge_config_with_args(config, args)
        assert merged["ignore_patterns"] == []

    def test_merge_config_git_blame_combinations(self):
        """Test various git_blame and no_blame combinations."""
        import argparse

        # Test: config.git_blame=True, args.no_blame=False
        config = TickleConfig(git_blame=True)
        args = argparse.Namespace(
            markers="TODO",
            ignore="",
            format="tree",
            sort="file",
            reverse=False,
            include_hidden=False,
            no_blame=False,
            git_verbose=False,
            tree_collapse=False,
            path=".",
        )
        merged = merge_config_with_args(config, args)
        assert merged["enable_git_blame"] is True

        # Test: config.git_blame=False, args.no_blame=False (config wins)
        config = TickleConfig(git_blame=False)
        merged = merge_config_with_args(config, args)
        assert merged["enable_git_blame"] is False

        # Test: config.git_blame=True, args.no_blame=True (CLI wins)
        args.no_blame = True
        config = TickleConfig(git_blame=True)
        merged = merge_config_with_args(config, args)
        assert merged["enable_git_blame"] is False

    def test_merge_config_whitespace_in_ignore(self):
        """Test merge handles whitespace in ignore patterns."""
        import argparse

        config = TickleConfig()
        args = argparse.Namespace(
            markers="TODO",
            ignore="  node_modules , dist  , build ",
            format="tree",
            sort="file",
            reverse=False,
            include_hidden=False,
            no_blame=False,
            git_verbose=False,
            tree_collapse=False,
            path=".",
        )

        merged = merge_config_with_args(config, args)
        assert "node_modules" in merged["ignore_patterns"]
        assert "dist" in merged["ignore_patterns"]
        assert "build" in merged["ignore_patterns"]


class TestWindowsEdgeCases:
    """Test Windows-specific edge cases."""

    def test_windows_without_appdata(self):
        """Test Windows config path when APPDATA is not set."""
        with mock.patch("sys.platform", "win32"):
            with mock.patch.dict(os.environ, {}, clear=True):
                # Returns None when APPDATA not available on Windows
                path = get_user_config_path()
                assert path is None
