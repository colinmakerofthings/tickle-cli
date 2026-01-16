# src/tickle/cli.py
import argparse
import sys
from pathlib import Path

from colorama import init as colorama_init

from tickle import __version__
from tickle.config import (
    create_minimal_config,
    find_config_file,
    format_config_for_display,
    load_config,
    merge_config_with_args,
)
from tickle.output import display_summary_panel, get_formatter
from tickle.scanner import scan_directory


def handle_init_command(args):
    """Handle the 'tickle init' command to create a config file."""
    config_path = Path("tickle.toml")

    if config_path.exists():
        print("Error: tickle.toml already exists. Remove it first if you want to recreate it.")
        sys.exit(1)

    try:
        config_content = create_minimal_config()
        config_path.write_text(config_content, encoding="utf-8")
        print(f"Created {config_path}")
        print("\nYou can now edit this file to customize your tickle configuration.")
    except Exception as e:
        print(f"Error creating config file: {e}")
        sys.exit(1)


def handle_config_show_command(args):
    """Handle the 'tickle config show' command to display effective configuration."""
    # Find config file (respect --config flag if provided)
    config_path = find_config_file(
        start_path=getattr(args, "path", "."),
        config_override=getattr(args, "config", None),
    )

    # Load configuration
    config = load_config(config_path, validate=True)

    # Display formatted configuration
    output = format_config_for_display(config, config_path)
    print(output)


def handle_scan_command(args):
    """Handle the default scan command."""
    # Load configuration unless --no-config is specified
    config_path = None
    if not args.no_config:
        config_path = find_config_file(start_path=args.path, config_override=args.config)
        if args.verbose and config_path:
            print(f"Using config from: {config_path}", file=sys.stderr)

    # Load and merge configuration with CLI args
    config = load_config(config_path, validate=True)
    merged = merge_config_with_args(config, args)

    # Scan directory with merged configuration
    tasks = scan_directory(
        merged["path"],
        markers=merged["markers"],
        ignore_patterns=merged["ignore_patterns"],
        sort_by=merged["sort"],
        reverse_sort=merged["reverse"],
        ignore_hidden=not merged["include_hidden"],
        enable_git_blame=merged["enable_git_blame"],
    )

    # Display summary panel for tree format (only if tasks exist)
    if tasks and merged["format"] == "tree":
        display_summary_panel(tasks)
        print()  # Blank line separator

    # Format and output results
    formatter = get_formatter(
        merged["format"],
        git_verbose=merged["git_verbose"],
        tree_collapse=merged["tree_collapse"],
        scan_directory=merged["path"],
    )
    output = formatter.format(tasks)
    print(output)


def main():
    """Main entry point for tickle CLI."""
    # Set UTF-8 encoding for stdout on Windows
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    # Initialize colorama for Windows compatibility
    colorama_init(autoreset=True)

    # Special handling for subcommands to avoid argparse conflict with positional path
    # Check if first arg is a known subcommand
    if len(sys.argv) > 1 and sys.argv[1] in ["init", "config"]:
        # Use subparser-based parsing
        parser = argparse.ArgumentParser(
            description="Scan repositories for outstanding developer tasks (TODO, FIXME, BUG, NOTE, HACK, CHECKBOX)",
            prog="tickle",
        )
        parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Subcommand: init
        subparsers.add_parser("init", help="Create a tickle.toml configuration file")

        # Subcommand: config show
        config_parser = subparsers.add_parser("config", help="Configuration management")
        config_subparsers = config_parser.add_subparsers(dest="config_command")
        config_show_parser = config_subparsers.add_parser("show", help="Show effective configuration")
        config_show_parser.add_argument(
            "--config", type=str, help="Path to config file to use"
        )
        config_show_parser.add_argument(
            "path", nargs="?", default=".", help="Path to scan (for finding project config)"
        )

        args = parser.parse_args()

        # Route to subcommand handlers
        if args.command == "init":
            handle_init_command(args)
        elif args.command == "config":
            if args.config_command == "show":
                handle_config_show_command(args)
            else:
                config_parser.print_help()
        return

    # Default behavior: scan mode (no subcommands)
    parser = argparse.ArgumentParser(
        description="Scan repositories for outstanding developer tasks (TODO, FIXME, BUG, NOTE, HACK, CHECKBOX)",
        prog="tickle",
    )

    parser.add_argument("path", nargs="?", default=".", help="Path to scan (default: current directory)")
    parser.add_argument(
        "--markers",
        type=str,
        default="TODO,FIXME,BUG,NOTE,HACK,CHECKBOX",
        help="Comma-separated list of task markers to search for (default: TODO,FIXME,BUG,NOTE,HACK,CHECKBOX)",
    )
    parser.add_argument(
        "--format",
        choices=["tree", "json", "markdown"],
        default="tree",
        help="Output format (default: tree)",
    )
    parser.add_argument(
        "--ignore",
        type=str,
        default="",
        help="Comma-separated list of file/directory patterns to ignore (e.g., *.min.js,node_modules)",
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
        ),
    )
    parser.add_argument("--reverse", action="store_true", help="Reverse the sort order")
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden directories (starting with .) in scan",
    )
    parser.add_argument(
        "--no-blame",
        action="store_true",
        help="Skip git blame enrichment (faster but no author/date info)",
    )
    parser.add_argument(
        "--git-verbose",
        action="store_true",
        help="Show full git commit hash and message (only with git blame enabled)",
    )
    parser.add_argument(
        "--tree-collapse",
        action="store_true",
        help="Show only directory structure with counts (hide task details)",
    )
    parser.add_argument(
        "--config", type=str, help="Path to config file to use (overrides default search)"
    )
    parser.add_argument(
        "--no-config", action="store_true", help="Ignore all configuration files"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show which config file is being used"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    args = parser.parse_args()
    handle_scan_command(args)


# Entry point for pyproject.toml scripts
app = main

