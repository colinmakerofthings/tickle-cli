# Release Process for tickle-cli

This document describes the steps to create a new release of tickle-cli. Follow these steps to ensure a smooth and consistent release process.

## Prerequisites

- Push access to the repository
- PyPI trusted publishing is set up (no passwords needed in workflow)
- Clean working tree (no uncommitted changes)

## Local Checks

1. **Create/activate a virtual environment:**

   ```sh
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies:**

   ```sh
   pip install -e .[dev]
   ```

3. **Lint and format:**

   ```sh
   ruff check src/ tests/
   black --check src/ tests/
   ```

4. **Run tests:**

   ```sh
   pytest
   ```

5. **Smoke test the CLI:**

   ```sh
   python -m tickle --help
   tickle --version
   ```

## Release Steps

1. **Bump the version** in `pyproject.toml` (use semantic versioning).
2. **Update `CHANGELOG.md`** with notable changes.
3. **Commit and push changes:**

   ```sh
   git add pyproject.toml CHANGELOG.md
   git commit -m "Release vX.Y.Z"
   git push origin main
   ```

4. **Tag the release and push the tag:**

   ```sh
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

5. **GitHub Actions** will run the release workflow:
   - Run tests, lint, and build
   - Publish to PyPI
   - Create a GitHub Release

## Verification

- Check the GitHub Actions workflow for success
- Verify the new release on PyPI
- Install the package from PyPI and test the CLI

## Rollback

- Never delete a PyPI release. If needed, bump the patch version and release a fix.

---

For questions, open an issue or contact a maintainer.
