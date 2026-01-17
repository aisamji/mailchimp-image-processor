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

Note: `ruff check` and `ruff format` run automatically on commit via pre-commit hooks. `uv sync` runs automatically on pull, merge, or checkout via post-checkout hook.

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

### Key Dependencies
- **pillow**: Image processing (PIL)
- **pyinstaller**: Building standalone binaries
- **pytest**: Testing framework
- **uv**: Package and environment management
- **ruff**: Linting and formatting

## Workflow and CI/CD

This project follows **trunk-based development** with the `main` branch as the default:

- **Test Workflow** (`.github/workflows/test.yaml`): Runs on all non-main branches
  - Linting with ruff (with GitHub annotations)
  - Test suite execution with pytest

- **Release Workflow** (`.github/workflows/release.yaml`): Runs on main branch commits
  - Uses release-please to manage versions in `pyproject.toml`
  - Creates PRs for version bumps
  - Builds binaries with pyinstaller and attaches to GitHub releases

**Important**: All commits to main must be made through PRs and should be squash-merged to maintain clean git history and compatibility with release-please.

## Python Version

This project requires Python 3.13 or higher (see `pyproject.toml` and `.python-version`).
