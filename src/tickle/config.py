"""Configuration file handling for tickle."""

import os
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Python <3.11


@dataclass
class TickleConfig:
    """Configuration settings for tickle."""

    markers: list[str] | None = None
    ignore: list[str] | None = None
    format: str | None = None
    sort: str | None = None
    reverse: bool | None = None
    include_hidden: bool | None = None
    git_blame: bool | None = None
    git_verbose: bool | None = None
    tree_collapse: bool | None = None


# Valid choices for validation
VALID_FORMATS = ["tree", "json", "markdown"]
VALID_SORTS = ["file", "marker", "age", "author"]


def get_user_config_path() -> Path | None:
    """Get the user-level config file path based on platform.

    Returns:
        Path to user config file, or None if platform not supported
    """
    if sys.platform == "win32":
        # Windows: %APPDATA%\tickle\tickle.toml
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "tickle" / "tickle.toml"
    else:
        # Linux/Mac: ~/.config/tickle/tickle.toml
        home = Path.home()
        return home / ".config" / "tickle" / "tickle.toml"
    return None


def find_config_file(start_path: str = ".", config_override: str | None = None) -> Path | None:
    """Find config file in precedence order.

    Args:
        start_path: Directory to start searching from (default: current directory)
        config_override: Explicit config file path to use (highest precedence)

    Returns:
        Path to config file, or None if not found

    Precedence order:
        1. config_override (if provided)
        2. Project-level: tickle.toml or .tickle.toml in current directory
        3. pyproject.toml with [tool.tickle] section
        4. User-level: ~/.config/tickle/tickle.toml (or %APPDATA%\\tickle\\tickle.toml on Windows)
    """
    # Check for explicit config override
    if config_override:
        config_path = Path(config_override)
        if config_path.exists():
            return config_path
        warnings.warn(f"Config file not found: {config_override}", UserWarning, stacklevel=2)
        return None

    start = Path(start_path).resolve()

    # Check for project-level configs
    for name in ["tickle.toml", ".tickle.toml"]:
        config = start / name
        if config.exists():
            return config

    # Check pyproject.toml for [tool.tickle] section
    pyproject = start / "pyproject.toml"
    if pyproject.exists():
        try:
            with open(pyproject, "rb") as f:
                data = tomllib.load(f)
                if "tool" in data and "tickle" in data["tool"]:
                    return pyproject
        except Exception:  # noqa: S110
            # If we can't parse it, skip it (by design)
            pass

    # Check user-level config
    user_config = get_user_config_path()
    if user_config and user_config.exists():
        return user_config

    return None


def load_config(config_path: Path | None = None, validate: bool = True) -> TickleConfig:
    """Load configuration from file.

    Args:
        config_path: Path to config file (if None, returns empty config)
        validate: Whether to validate config values and emit warnings

    Returns:
        TickleConfig object with loaded settings
    """
    if config_path is None:
        return TickleConfig()

    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
    except Exception as e:
        warnings.warn(f"Failed to parse config file {config_path}: {e}", UserWarning, stacklevel=2)
        return TickleConfig()

    # Handle pyproject.toml [tool.tickle] section
    if config_path.name == "pyproject.toml":
        config_data = data.get("tool", {}).get("tickle", {})
    else:
        config_data = data.get("tickle", data)  # Support both [tickle] and top-level

    # Extract and validate configuration
    config = TickleConfig()

    # Markers
    if "markers" in config_data:
        markers = config_data["markers"]
        if isinstance(markers, list) and all(isinstance(m, str) for m in markers):
            config.markers = markers
        else:
            if validate:
                warnings.warn(
                    f"Invalid 'markers' in config: expected list of strings, got {type(markers).__name__}",
                    UserWarning,
                    stacklevel=2,
                )

    # Ignore patterns
    if "ignore" in config_data:
        ignore = config_data["ignore"]
        if isinstance(ignore, list) and all(isinstance(p, str) for p in ignore):
            config.ignore = ignore
        else:
            if validate:
                warnings.warn(
                    f"Invalid 'ignore' in config: expected list of strings, got {type(ignore).__name__}",
                    UserWarning,
                    stacklevel=2,
                )

    # Format
    if "format" in config_data:
        fmt = config_data["format"]
        if isinstance(fmt, str):
            if validate and fmt not in VALID_FORMATS:
                warnings.warn(
                    f"Invalid 'format' in config: '{fmt}'. Valid options: {', '.join(VALID_FORMATS)}",
                    UserWarning,
                    stacklevel=2,
                )
            else:
                config.format = fmt
        else:
            if validate:
                warnings.warn(
                    f"Invalid 'format' in config: expected string, got {type(fmt).__name__}",
                    UserWarning,
                    stacklevel=2,
                )

    # Sort
    if "sort" in config_data:
        sort = config_data["sort"]
        if isinstance(sort, str):
            if validate and sort not in VALID_SORTS:
                warnings.warn(
                    f"Invalid 'sort' in config: '{sort}'. Valid options: {', '.join(VALID_SORTS)}",
                    UserWarning,
                    stacklevel=2,
                )
            else:
                config.sort = sort
        else:
            if validate:
                warnings.warn(
                    f"Invalid 'sort' in config: expected string, got {type(sort).__name__}",
                    UserWarning,
                    stacklevel=2,
                )

    # Boolean options
    for key in ["reverse", "include_hidden", "git_verbose", "tree_collapse"]:
        if key in config_data:
            value = config_data[key]
            if isinstance(value, bool):
                setattr(config, key, value)
            else:
                if validate:
                    warnings.warn(
                        f"Invalid '{key}' in config: expected boolean, got {type(value).__name__}",
                        UserWarning,
                        stacklevel=2,
                    )

    # Special handling for git_blame (inverse of --no-blame)
    if "git_blame" in config_data:
        value = config_data["git_blame"]
        if isinstance(value, bool):
            config.git_blame = value
        else:
            if validate:
                warnings.warn(
                    f"Invalid 'git_blame' in config: expected boolean, got {type(value).__name__}",
                    UserWarning,
                    stacklevel=2,
                )

    # Warn about unknown keys
    if validate:
        known_keys = {
            "markers",
            "ignore",
            "format",
            "sort",
            "reverse",
            "include_hidden",
            "git_blame",
            "git_verbose",
            "tree_collapse",
        }
        unknown_keys = set(config_data.keys()) - known_keys
        if unknown_keys:
            warnings.warn(
                f"Unknown configuration keys in {config_path}: {', '.join(sorted(unknown_keys))}",
                UserWarning,
                stacklevel=2,
            )

    return config


def merge_config_with_args(config: TickleConfig, args) -> dict:
    """Merge config file settings with CLI arguments.

    CLI arguments take precedence over config file values.
    Only uses config values when the CLI arg is at its default value.

    Args:
        config: Loaded configuration
        args: Parsed command-line arguments

    Returns:
        Dictionary with final merged values
    """
    # Default values from CLI
    default_markers = "TODO,FIXME,BUG,NOTE,HACK,CHECKBOX"
    default_format = "tree"
    default_sort = "file"
    default_ignore = ""

    result = {}

    # Markers: use config if CLI is at default
    if hasattr(args, "markers") and args.markers == default_markers and config.markers:
        result["markers"] = config.markers
    elif hasattr(args, "markers"):
        result["markers"] = [m.strip() for m in args.markers.split(",") if m.strip()]
    else:
        result["markers"] = [m.strip() for m in default_markers.split(",")]

    # Ignore patterns: use config if CLI is at default
    if hasattr(args, "ignore") and args.ignore == default_ignore and config.ignore:
        result["ignore_patterns"] = config.ignore
    elif hasattr(args, "ignore"):
        result["ignore_patterns"] = (
            [p.strip() for p in args.ignore.split(",") if p.strip()] if args.ignore else []
        )
    else:
        result["ignore_patterns"] = []

    # Format: use config if CLI is at default
    if hasattr(args, "format") and args.format == default_format and config.format:
        result["format"] = config.format
    elif hasattr(args, "format"):
        result["format"] = args.format
    else:
        result["format"] = default_format

    # Sort: use config if CLI is at default
    if hasattr(args, "sort") and args.sort == default_sort and config.sort:
        result["sort"] = config.sort
    elif hasattr(args, "sort"):
        result["sort"] = args.sort
    else:
        result["sort"] = default_sort

    # Boolean flags: config provides default, CLI explicitly overrides
    # For reverse, include_hidden, git_verbose, tree_collapse: False is default
    for key, cli_key in [
        ("reverse", "reverse"),
        ("include_hidden", "include_hidden"),
        ("git_verbose", "git_verbose"),
        ("tree_collapse", "tree_collapse"),
    ]:
        cli_value = getattr(args, cli_key, False)
        config_value = getattr(config, key, False)

        # If CLI flag is set (True), use it; otherwise use config or default False
        result[cli_key] = cli_value if cli_value else (config_value or False)

    # Special handling for git_blame (inverse of --no-blame flag)
    # Default is True (enable git blame)
    # Config git_blame: true/false sets the default
    # CLI --no-blame overrides to disable
    if hasattr(args, "no_blame"):
        if args.no_blame:
            # CLI explicitly disabled
            result["enable_git_blame"] = False
        elif config.git_blame is not None:
            # Use config value
            result["enable_git_blame"] = config.git_blame
        else:
            # Default: enabled
            result["enable_git_blame"] = True
    else:
        result["enable_git_blame"] = True

    # Path
    if hasattr(args, "path"):
        result["path"] = args.path
    else:
        result["path"] = "."

    return result


def create_minimal_config() -> str:
    """Generate a minimal tickle.toml configuration file content.

    Returns:
        String content for tickle.toml with commonly used options
    """
    return """# tickle configuration file
# See https://github.com/colinmakerofthings/tickle-cli for full documentation

[tickle]
# Task markers to search for (comment-style markers)
markers = ["TODO", "FIXME", "BUG", "NOTE", "HACK", "CHECKBOX"]

# Patterns to ignore (supports glob patterns)
ignore = [
    "*.min.js",
    "*.min.css",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".git"
]

# Uncomment to set default output format
# format = "tree"  # options: tree, json, markdown

# Uncomment to set default sort method
# sort = "file"  # options: file, marker, age, author

# Uncomment to enable git blame by default (default: true)
# git_blame = true
"""


def format_config_for_display(config: TickleConfig, config_path: Path | None = None) -> str:
    """Format configuration for human-readable display.

    Args:
        config: Configuration to display
        config_path: Path to config file (if any)

    Returns:
        Formatted string showing configuration
    """
    lines = []

    if config_path:
        lines.append(f"Configuration loaded from: {config_path}")
    else:
        lines.append("No configuration file found (using defaults)")

    lines.append("")
    lines.append("Effective Configuration:")
    lines.append("-" * 40)

    # Show each config option
    if config.markers:
        lines.append(f"markers: {', '.join(config.markers)}")
    else:
        lines.append("markers: (using defaults)")

    if config.ignore:
        lines.append(f"ignore: {', '.join(config.ignore)}")
    else:
        lines.append("ignore: (none)")

    if config.format:
        lines.append(f"format: {config.format}")
    else:
        lines.append("format: (default: tree)")

    if config.sort:
        lines.append(f"sort: {config.sort}")
    else:
        lines.append("sort: (default: file)")

    if config.reverse is not None:
        lines.append(f"reverse: {config.reverse}")
    else:
        lines.append("reverse: (default: false)")

    if config.include_hidden is not None:
        lines.append(f"include_hidden: {config.include_hidden}")
    else:
        lines.append("include_hidden: (default: false)")

    if config.git_blame is not None:
        lines.append(f"git_blame: {config.git_blame}")
    else:
        lines.append("git_blame: (default: true)")

    if config.git_verbose is not None:
        lines.append(f"git_verbose: {config.git_verbose}")
    else:
        lines.append("git_verbose: (default: false)")

    if config.tree_collapse is not None:
        lines.append(f"tree_collapse: {config.tree_collapse}")
    else:
        lines.append("tree_collapse: (default: false)")

    return "\n".join(lines)
