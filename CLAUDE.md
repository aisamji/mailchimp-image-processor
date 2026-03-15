# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

An application to upload images to Mailchimp's Content Studio. The application:
- Extracts images from multiple sources (currently filesystem, with plans for Google Drive and other providers)
- Applies predefined transformations (resize, watermark, etc.)
- Files images to specific folders in Mailchimp Content Studio
- Supports multiple Mailchimp accounts

## Development Commands

### Environment Setup
```bash
uv sync                        # Sets up Python virtualenv and installs dependencies
pre-commit install             # Install pre-commit git hooks
pre-commit install -t post-checkout  # Install post-checkout git hooks
```

### Running the Application
```bash
uv run mailchimp-image-processor  # Full command name
uv run mip                         # Short alias
```

### Testing
```bash
uv run pytest                  # Run all tests
uv run pytest tests/test_providers.py  # Run specific test file
uv run pytest tests/test_providers.py::TestFileSystemProvider::test_load_image_from_local_file  # Run specific test
```

### Linting and Formatting
```bash
ruff check                     # Lint code
ruff format                    # Format code
ruff check --fix               # Lint and auto-fix issues
```

**TIP:** While `ruff format` is run automatically as a pre-commit hook, you should run `ruff format` manually before any commit.

## Architecture

### Provider Pattern
The application uses a provider pattern to extract images from various sources:

- **`ImageProvider` (ABC)**: Abstract base class defining the `extract(source: str) -> list[Image]` interface
- **`FilesystemImageProvider`**: Reads images from local filesystem (files or directories)
- Future providers planned: Google Drive, URLs, etc.

Provider implementations are in `src/mailchimp_image_processor/providers.py`.

### Project Structure
- `src/mailchimp_image_processor/`: Application source code
  - `__init__.py`: Entry point with `main()` function
  - `providers.py`: Image provider implementations
- `tests/`: Test suite using pytest
  - Test fixtures use temporary directories with sample images
- `pyproject.toml`: Project metadata, dependencies, and tool configuration
- `.pre-commit-config.yaml`: Git hooks configuration

### System Dependencies
- **uv**: Package and environment management
- **ruff**: Linting and formatting

**NOTE:** Other python dependencies (such as pytest) will be installed in the virtual environment with `uv`. The full list of python dependencies can be viewed in pyproject.toml.

## Workflow and CI/CD

This project follows **trunk-based development** with the `main` branch as the default:

- **Test Workflow** (`.github/workflows/test.yaml`): Runs on all non-main branches
  - Linting with ruff (with GitHub annotations)
  - Test suite execution with pytest

- **Release Workflow** (`.github/workflows/release.yaml`): Runs on main branch commits
  - Uses release-please to manage versions in `pyproject.toml`
  - Creates PRs for version bumps
  - Builds binaries with pyinstaller and attaches to GitHub releases

### Commits

All commits to main must be made through PRs and should be squash-merged to maintain clean git history and compatibility with release-please. All commits and PR titles should conform to [conventional commit](https://www.conventionalcommits.org/en/v1.0.0/) style. Breaking changes should be indicated with `!` rather than a `BREAKING CHANGE` footer to comply with release-please requirements in contrast to what conventional commits allows.

The commit body should not simply be a reiteration and rephrasing of the description, as defined by conventional commits. The body should go into more depth about what was done as well as why, both sections are optional as well as the entire body itself. Footers for `Refs` and `Co-authored-by` are allowed if needed.

All commits should add one or more tests to validate functionality of added features/fixes. No test is there is no logic or input that needs to be tested. For example, a simple getter does not need to be tested however a function that processes some arguments needs tests even if the function itself does not have any complex logic. All functions and modules should have docstrings. Comments should NOT be used to describe what is happening; they should instead be used to explain the "why?" of a specific coding decision or ... TODOs (e.g. `TODO: Remove this workaround when the underlying library has patched the bug.`). Not ALL decisions need to be explained; many decisions are straight-forward. Examples of things that do need to be explained: taking advantage of a non-obvious feature of the language, going against best practices because of specific project requirements (best practices are determined to be correct for 99% of use-cases but there is always that 1%).

