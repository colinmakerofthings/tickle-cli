# src/tickle/cli.py
import argparse
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
    
    # TODO: Pass markers and ignore_patterns to scan_directory once it supports them
    tasks = scan_directory(args.path)
    
    if not tasks:
        print("No tasks found!")
        return
    
    # TODO: Use output.py formatters based on --format flag
    if args.format == "text":
        for task in tasks:
            print(f"{task['file']}:{task['line']}: [{task.get('marker', 'TODO')}] {task['text']}")
    elif args.format == "json":
        import json
        print(json.dumps(tasks, indent=2))
    elif args.format == "markdown":
        print("# Outstanding Tasks\n")
        current_file = None
        for task in tasks:
            if task['file'] != current_file:
                current_file = task['file']
                print(f"\n## {current_file}\n")
            print(f"- Line {task['line']}: [{task.get('marker', 'TODO')}] {task['text']}")


# Entry point for pyproject.toml scripts
app = main

