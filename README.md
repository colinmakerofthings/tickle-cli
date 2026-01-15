# tickle 🪶

<!-- badges: start -->
![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Tests](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/colinmakerofthings/38120414da63546897e889745fcb37c0/raw/tickle-tests.json)
[![Coverage](https://codecov.io/gh/colinmakerofthings/tickle-cli/branch/main/graph/badge.svg)](https://codecov.io/gh/colinmakerofthings/tickle-cli)
![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-d7ff64.svg)
<!-- badges: end -->

A lightweight, cross-platform tool that provides **hierarchical visualization** of TODOs, code comments, and markdown checkboxes across your repositories and personal notes.

*The name? It's all about **tick**ing things off your list.*

**Platform Support:** Windows, Linux, macOS

## Why?

I wanted a fast, configurable way to surface TODOs across many repos. Whether it's tracking bugs in code or managing your life in markdown journals and task lists, tickle finds and reports what needs attention.

## Features

- **Hierarchical tree view** showing tasks organized by directory structure
- Multi-repo scanning
- Configurable task markers (TODO, FIXME, BUG, NOTE, HACK, CHECKBOX)
- Markdown checkbox detection (finds unchecked `- [ ]` items)
- Git blame enrichment (shows who wrote each task and when)
- Visual summary panel showing task counts and breakdown
- Alternative JSON / Markdown output formats for automation
- Cross-platform compatibility (Windows, Linux, macOS)

## Installation

### From PyPI (Recommended)

```bash
pip install tickle-cli
```

### From Source (Development)

```bash
git clone https://github.com/colinmakerofthings/tickle-cli.git
cd tickle-cli
pip install -e ".[dev]"
```

## Usage

Check the version:

```bash
tickle --version
```

Scan the current directory for tasks:

```bash
tickle
```

**Output shows a hierarchical tree view** with summary panel:

```text
┌─────── Task Summary ────────┐
│ Total: 14 tasks in 6 files  │
│ BUG: 2 | FIXME: 5 | TODO: 7 │
└─────────────────────────────┘

📁 tickle-cli (14 tasks)
├── 📁 src (10)
│   ├── 📁 tickle (10)
│   │   ├── 📄 cli.py (2)
│   │   │   ├── [TODO] Line 15: Add config file support (by alice, 2 days ago)
│   │   │   └── [FIXME] Line 42: Handle edge case (by bob, 3 weeks ago)
│   │   └── 📄 scanner.py (3)
│   │       └── [BUG] Line 67: Memory leak (by charlie, 1 month ago)
└── 📁 tests (4)
    └── 📄 test_cli.py (4)
```

*Note: Git blame information (author and date) is automatically included when scanning git repositories. Use `--no-blame` to disable this feature for faster scanning.*

Scan a specific directory:

```bash
tickle /path/to/repo
```

Filter by specific task markers:

```bash
tickle --markers TODO,FIXME,BUG
```

Show collapsed tree view (counts only):

```bash
tickle --tree-collapse
```

This shows just the directory structure with task counts, hiding individual task details.

Output in JSON format (for automation):

```bash
tickle --format json
```

Output in Markdown format (for documentation):

```bash
tickle --format markdown
```

*Note: Summary panel and tree view are shown by default. Use `--format json` or `--format markdown` for machine-readable or documentation output.*

Ignore specific file patterns:

```bash
tickle --ignore "*.min.js,node_modules,build"
```

Sort tasks by marker priority:

```bash
tickle --sort marker
```

This groups tasks by priority (BUG → FIXME → TODO → HACK → NOTE → CHECKBOX), making it easy to focus on critical issues first. Default is `--sort file` which sorts by file path and line number.

Sort by commit age (oldest first):

```bash
tickle --sort age
```

This shows oldest TODOs first based on git commit date, helping identify technical debt and long-standing issues. Tasks without git blame data appear last.

Sort by author:

```bash
tickle --sort author
```

This groups tasks alphabetically by author name, making it easy to see who wrote each TODO. Requires git blame to be enabled (default).

Scan for markdown checkboxes:

```bash
tickle --markers CHECKBOX
```

This finds all unchecked markdown checkboxes (`- [ ]` or `* [ ]`) in your markdown files.

Include hidden directories in scan:

```bash
tickle --include-hidden
```

By default, hidden directories (starting with `.` like `.git`, `.vscode`) are ignored. Use this flag to include them.

Disable git blame enrichment:

```bash
tickle --no-blame
```

By default, tickle enriches task output with git blame information (author and date). Use this flag to skip git blame for faster scanning when you don't need author/date information.

Show verbose git information:

```bash
tickle --git-verbose
```

This shows additional git details including the commit hash and commit message for each task. Only works when git blame is enabled (don't use with `--no-blame`).

Combine options:

```bash
tickle /path/to/repo --markers TODO,FIXME --ignore "tests,venv" --tree-collapse
```
