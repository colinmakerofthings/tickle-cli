"""Tickle - Scan repositories for outstanding developer tasks."""

try:
    from importlib.metadata import PackageNotFoundError, version
    __version__ = version("tickle-cli")
except PackageNotFoundError:
    # Fallback for development when not installed - read from pyproject.toml if it exists
    from pathlib import Path
    _pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    if _pyproject_path.is_file():
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        with open(_pyproject_path, "rb") as _f:
            _pyproject_data = tomllib.load(_f)
        __version__ = _pyproject_data["project"]["version"]
    else:
        __version__ = "unknown"
