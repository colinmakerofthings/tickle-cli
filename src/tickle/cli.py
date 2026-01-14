# src/tickle/cli.py
import argparse

from colorama import init as colorama_init

from tickle import __version__
from tickle.output import generate_stats, get_formatter
from tickle.scanner import scan_directory


def main():
    """Main entry point for tickle CLI."""
    # Initialize colorama for Windows compatibility
    colorama_init(autoreset=True)

    parser = argparse.ArgumentParser(
        description="Scan repositories for outstanding developer tasks (TODO, FIXME, BUG, NOTE, HACK)"
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to scan (default: current directory)"
    )
    parser.add_argument(
        "--markers",
        type=str,
        default="TODO,FIXME,BUG,NOTE,HACK",
        help="Comma-separated list of task markers to search for (default: TODO,FIXME,BUG,NOTE,HACK)"
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)"
    )
    parser.add_argument(
        "--ignore",
        type=str,
        default="",
        help="Comma-separated list of file/directory patterns to ignore (e.g., *.min.js,node_modules)"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show summary statistics instead of individual tasks"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )

    args = parser.parse_args()

    # Parse markers from comma-separated string
    markers = [m.strip() for m in args.markers.split(",") if m.strip()]

    # Parse ignore patterns from comma-separated string
    ignore_patterns = [p.strip() for p in args.ignore.split(",") if p.strip()] if args.ignore else []

    # Scan directory with markers and ignore patterns
    tasks = scan_directory(args.path, markers=markers, ignore_patterns=ignore_patterns)

    # Format and output results
    if args.stats:
        output = generate_stats(tasks)
    else:
        formatter = get_formatter(args.format)
        output = formatter.format(tasks)
    print(output)


# Entry point for pyproject.toml scripts
app = main

