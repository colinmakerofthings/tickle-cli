"""Tickle - Scan repositories for outstanding developer tasks."""

try:
    from importlib.metadata import version, PackageNotFoundError

    __version__ = version("tickle")
except PackageNotFoundError:
    # Fallback for development when not installed - read from pyproject.toml
    try:
        import tomllib
    except ImportError:
        # Python < 3.11
        import tomli as tomllib

    from pathlib import Path

    _pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    with open(_pyproject_path, "rb") as _f:
        _pyproject_data = tomllib.load(_f)
    __version__ = _pyproject_data["project"]["version"]