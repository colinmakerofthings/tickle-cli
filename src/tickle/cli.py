# src/tickle/cli.py
from tickle.scanner import scan_directory

def main():
    """Main entry point for tickle."""
    # TODO: Add argparse for CLI arguments (path, --markers, --format, --ignore)
    # TODO: Support path argument to scan custom directories
    # TODO: Add --markers flag to filter by task markers (TODO, FIXME, BUG, NOTE, HACK)
    # TODO: Add --format flag for output formats (text, json, markdown)
    # TODO: Add --ignore flag for file/directory patterns
    path = "."  # For now, scan current directory
    tasks = scan_directory(path)
    
    if not tasks:
        print("No TODOs found!")
        return
    
    # TODO: Use output.py formatters based on --format flag
    for task in tasks:
        print(f"{task['file']}:{task['line']}: {task['text']}")

# Entry point for pyproject.toml scripts
app = main
