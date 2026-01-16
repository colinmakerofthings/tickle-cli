# tickle 🪶

<!-- badges: start -->
![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Tests](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/colinmakerofthings/38120414da63546897e889745fcb37c0/raw/tickle-tests.json)
[![Coverage](https://codecov.io/gh/colinmakerofthings/tickle-cli/branch/main/graph/badge.svg)](https://codecov.io/gh/colinmakerofthings/tickle-cli)
![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-d7ff64.svg)
![Security: ruff](https://img.shields.io/badge/security-ruff%20S-orange)
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

Reverse any sort order:

```bash
tickle --sort marker --reverse
```

The `--reverse` flag inverts any sort order. Use it with `--sort file` (Z→A paths), `--sort marker` (lowest to highest priority), `--sort age` (newest first), or `--sort author` (Z→A names).

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
ticklе /path/to/repo --markers TODO,FIXME --ignore "tests,venv" --sort marker --reverse --tree-collapse
```

## Configuration

Tired of typing the same flags every time? Configuration files let you set persistent defaults for ignore patterns, markers, output format, and more. Share configuration across your team via `pyproject.toml`, or maintain personal preferences in your user config.

### Quick Start

Create a configuration file in your project:

```bash
tickle init
```

This creates a `tickle.toml` file in the current directory with sensible defaults. Edit this file to customize your ignore patterns, markers, and other settings.

View your effective configuration:

```bash
tickle config show
```

This shows which config file is being used and the final merged settings.

### Configuration Files

tickle supports multiple configuration file locations with the following precedence (highest to lowest):

1. **Explicit config** (via `--config` flag)
2. **Project-level**: `tickle.toml` or `.tickle.toml` in current directory
3. **pyproject.toml**: `[tool.tickle]` section in `pyproject.toml`
4. **User-level**:
   - Linux/Mac: `~/.config/tickle/tickle.toml`
   - Windows: `%APPDATA%\tickle\tickle.toml`

CLI arguments always take precedence over configuration files.

### Minimal Configuration Example

A typical `tickle.toml` for ignoring common build artifacts:

```toml
[tickle]
# Task markers to search for
markers = ["TODO", "FIXME", "BUG", "NOTE", "HACK", "CHECKBOX"]

# Patterns to ignore (glob-style)
ignore = [
    "*.min.js",
    "*.min.css",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".git"
]
```

### Comprehensive Configuration Example

See [tickle.toml.example](tickle.toml.example) for a complete example with all available options and comments.

All available configuration options:

```toml
[tickle]
# Task markers to search for
markers = ["TODO", "FIXME", "BUG", "NOTE", "HACK", "CHECKBOX"]

# File/directory patterns to ignore
ignore = ["node_modules", "dist", "*.min.js"]

# Default output format: "tree", "json", or "markdown"
format = "tree"

# Default sort method: "file", "marker", "age", or "author"
sort = "file"

# Reverse sort order
reverse = false

# Include hidden directories (starting with .)
include_hidden = false

# Enable git blame enrichment (author, date, commit info)
git_blame = true

# Show verbose git information (full commit hash and message)
git_verbose = false

# Collapse tree view (show only directory structure with counts)
tree_collapse = false
```

### Configuration Options Reference

| Option | Type | Default | Description | CLI Flag |
| ------ | ---- | ------- | ----------- | -------- |
| `markers` | list[str] | `["TODO", "FIXME", "BUG", "NOTE", "HACK", "CHECKBOX"]` | Task markers to search for | `--markers` |
| `ignore` | list[str] | `[]` | File/directory patterns to ignore | `--ignore` |
| `format` | str | `"tree"` | Output format (`tree`, `json`, `markdown`) | `--format` |
| `sort` | str | `"file"` | Sort method (`file`, `marker`, `age`, `author`) | `--sort` |
| `reverse` | bool | `false` | Reverse sort order | `--reverse` |
| `include_hidden` | bool | `false` | Include hidden directories | `--include-hidden` |
| `git_blame` | bool | `true` | Enable git blame enrichment | `--no-blame` (inverted) |
| `git_verbose` | bool | `false` | Show full git commit info | `--git-verbose` |
| `tree_collapse` | bool | `false` | Show only directory structure | `--tree-collapse` |

### Troubleshooting Configuration

**Config not loading?**

Use `tickle config show` to see which config file is being used and verify your settings.

**Values not applying?**

Remember that CLI arguments always override config file values. If you pass `--markers TODO`, it will override the `markers` setting in your config file.

**Unknown keys warning?**

tickle will warn about unrecognized configuration keys but will continue running. Check your spelling and refer to the options table above.

### Real-World Examples

#### Example 1: Ignore build artifacts in a Node.js project

```toml
[tickle]
ignore = [
    "node_modules",
    "dist",
    "build",
    "*.min.js",
    "*.min.css",
    "coverage"
]
```

#### Example 2: Focus on critical issues only

```toml
[tickle]
markers = ["BUG", "FIXME"]
sort = "marker"
```

#### Example 3: Team-shared configuration in pyproject.toml

```toml
[tool.tickle]
markers = ["TODO", "FIXME", "BUG", "HACK"]
ignore = ["dist", "build", "__pycache__", "*.egg-info", ".venv"]
sort = "age"  # Show oldest TODOs first for tech debt review
git_verbose = true  # Show full commit context
```

#### Example 4: Fast scanning without git info

```toml
[tickle]
git_blame = false  # Skip git blame for faster scanning
tree_collapse = true  # Show only counts
```
