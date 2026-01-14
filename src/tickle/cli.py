# src/tickle/cli.py
import argparse
import json
from tickle.scanner import scan_directory


def main():
    """Main entry point for tickle CLI."""
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
    
    args = parser.parse_args()
    
    # Parse markers from comma-separated string
    markers = [m.strip() for m in args.markers.split(",") if m.strip()]
    
    # Parse ignore patterns from comma-separated string
    ignore_patterns = [p.strip() for p in args.ignore.split(",") if p.strip()] if args.ignore else []
    
    # Scan directory with markers and ignore patterns
    tasks = scan_directory(args.path, markers=markers, ignore_patterns=ignore_patterns)
    
    if not tasks:
        print("No tasks found!")
        return
    
    # Format and output results
    if args.format == "text":
        for task in tasks:
            print(str(task))
    elif args.format == "json":
        task_dicts = [task.to_dict() for task in tasks]
        print(json.dumps(task_dicts, indent=2))
    elif args.format == "markdown":
        print("# Outstanding Tasks\n")
        current_file = None
        for task in tasks:
            if task.file != current_file:
                current_file = task.file
                print(f"\n## {current_file}\n")
            print(f"- Line {task.line}: [{task.marker}] {task.text}")


# Entry point for pyproject.toml scripts
app = main



# Entry point for pyproject.toml scripts
app = main

