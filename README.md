# tickle 🪶

*Work-in-Progress – API and features are evolving.*

<!-- badges: start -->
![Project Status: Work In Progress](https://www.repostatus.org/badges/1.0.0/wip.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
<!-- badges: end -->

A lightweight, cross-platform tool that scans repositories for outstanding developer tasks.

**Platform Support:** Windows, Linux, macOS

## Why?

I wanted a fast, configurable way to surface TODOs across many repos.

## Features

- Multi-repo scanning
- Configurable task markers (TODO, FIXME, BUG, NOTE, HACK, CHECKBOX)
- Markdown checkbox detection (finds unchecked `- [ ]` items)
- JSON / Markdown output
- Cross-platform compatibility (Windows, Linux, macOS)

## Installation

WIP

## Usage

Check the version:

```bash
python -m tickle --version
```

Scan the current directory for tasks:

```bash
python -m tickle
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
