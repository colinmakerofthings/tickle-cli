# src/tickle/cli.py
import argparse
import sys

from colorama import init as colorama_init

from tickle import __version__
from tickle.output import display_summary_panel, get_formatter
from tickle.scanner import scan_directory


def main():
    """Main entry point for tickle CLI."""
    # Set UTF-8 encoding for stdout on Windows
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')

    # Initialize colorama for Windows compatibility
    colorama_init(autoreset=True)

    parser = argparse.ArgumentParser(
        description="Scan repositories for outstanding developer tasks (TODO, FIXME, BUG, NOTE, HACK, CHECKBOX)"
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
        default="TODO,FIXME,BUG,NOTE,HACK,CHECKBOX",
        help="Comma-separated list of task markers to search for (default: TODO,FIXME,BUG,NOTE,HACK,CHECKBOX)"
    )
    parser.add_argument(
        "--format",
        choices=["tree", "json", "markdown"],
        default="tree",
        help="Output format (default: tree)"
    )
    parser.add_argument(
        "--ignore",
        type=str,
        default="",
        help="Comma-separated list of file/directory patterns to ignore (e.g., *.min.js,node_modules)"
    )
    parser.add_argument(
        "--sort",
        choices=["file", "marker", "age", "author"],
        default="file",
        help=(
            "Sort tasks by: "
            "'file' (file and line number, default), "
            "'marker' (marker type priority), "
            "'age' (oldest first by commit date), "
            "'author' (alphabetically by author name)"
        )
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden directories (starting with .) in scan"
    )
    parser.add_argument(
        "--no-blame",
        action="store_true",
        help="Skip git blame enrichment (faster but no author/date info)"
    )
    parser.add_argument(
        "--git-verbose",
        action="store_true",
        help="Show full git commit hash and message (only with git blame enabled)"
    )
    parser.add_argument(
        "--tree-collapse",
        action="store_true",
        help="Show only directory structure with counts (hide task details)"
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
    tasks = scan_directory(
        args.path,
        markers=markers,
        ignore_patterns=ignore_patterns,
        sort_by=args.sort,
        ignore_hidden=not args.include_hidden,
        enable_git_blame=not args.no_blame
    )

    # Display summary panel for tree format (only if tasks exist)
    if tasks and args.format == "tree":
        display_summary_panel(tasks)
        print()  # Blank line separator

    # Format and output results
    formatter = get_formatter(
        args.format,
        git_verbose=args.git_verbose,
        tree_collapse=args.tree_collapse,
        scan_directory=args.path
    )
    output = formatter.format(tasks)
    print(output)


# Entry point for pyproject.toml scripts
app = main

