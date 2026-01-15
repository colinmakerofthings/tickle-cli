# tickle 🪶

<!-- badges: start -->
![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Tests](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/colinmakerofthings/38120414da63546897e889745fcb37c0/raw/tickle-tests.json)
[![Coverage](https://codecov.io/gh/colinmakerofthings/tickle-cli/branch/main/graph/badge.svg)](https://codecov.io/gh/colinmakerofthings/tickle-cli)
![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-d7ff64.svg)
<!-- badges: end -->

A lightweight, cross-platform tool that scans your files and repos for TODOs, code comments, and markdown checkboxes-whether tracking bugs across repos or managing tasks in personal notes.

*The name? It's all about **tick**ing things off your list.*

**Platform Support:** Windows, Linux, macOS

## Why?

I wanted a fast, configurable way to surface TODOs across many repos. Whether it's tracking bugs in code or managing your life in markdown journals and task lists, tickle finds and reports what needs attention.

## Features

- Multi-repo scanning
- Configurable task markers (TODO, FIXME, BUG, NOTE, HACK, CHECKBOX)
- Markdown checkbox detection (finds unchecked `- [ ]` items)
- Visual summary panel showing task counts and breakdown (in text mode)
- JSON / Markdown output
- Cross-platform compatibility (Windows, Linux, macOS)

## Installation

### From Source (Development)

```bash
git clone https://github.com/colinmakerofthings/tickle-cli.git
cd tickle-cli
pip install -e ".[dev]"
```

*PyPI package coming soon.*

## Usage

Check the version:

```bash
python -m tickle --version
```

Scan the current directory for tasks:

```bash
python -m tickle
```

**Output includes a summary panel** (in text mode):

```text

┌─────── Task Summary ────────┐
│ Total: 14 tasks in 6 files  │
│ BUG: 2 | FIXME: 5 | TODO: 7 │
└─────────────────────────────┘

src/main.py:10: [TODO] # TODO: Implement feature
src/main.py:25: [FIXME] # FIXME: Fix bug
...
```

Scan a specific directory:

```bash
python -m tickle /path/to/repo
```

Filter by specific task markers:

```bash
python -m tickle --markers TODO,FIXME,BUG
```

Output in JSON format:

```bash
python -m tickle --format json
```

Output in Markdown format:

```bash
python -m tickle --format markdown
```

*Note: Summary panel is only shown in text mode. JSON and Markdown formats output data only.*

Ignore specific file patterns:

```bash
python -m tickle --ignore "*.min.js,node_modules,build"
```

Sort tasks by marker priority:

```bash
python -m tickle --sort marker
```

This groups tasks by priority (BUG → FIXME → TODO → HACK → NOTE → CHECKBOX), making it easy to focus on critical issues first. Default is `--sort file` which sorts by file path and line number.

Scan for markdown checkboxes:

```bash
python -m tickle --markers CHECKBOX
```

This finds all unchecked markdown checkboxes (`- [ ]` or `* [ ]`) in your markdown files.

Include hidden directories in scan:

```bash
python -m tickle --include-hidden
```

By default, hidden directories (starting with `.` like `.git`, `.vscode`) are ignored. Use this flag to include them.

Combine options:

```bash
python -m tickle /path/to/repo --markers TODO,FIXME --format json --ignore "tests,venv"
```
