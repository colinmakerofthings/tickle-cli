# tickle 🪶

*Work-in-Progress – API and features are evolving.*

<!-- badges: start -->
![Project Status: Work In Progress](https://www.repostatus.org/badges/1.0.0/wip.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
<!-- badges: end -->

A lightweight tool that scans repositories for outstanding developer tasks.

## Why?

I wanted a fast, configurable way to surface TODOs across many repos.

## Features

- Multi-repo scanning
- Configurable task markers
- JSON / Markdown output

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

Combine options:

```bash
python -m tickle /path/to/repo --markers TODO,FIXME --format json --ignore "tests,venv"
```
