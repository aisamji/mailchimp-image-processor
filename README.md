# mailchimp-image-processor

An application to upload images to Mailchimp's Content Studio.

- Extract images from multiple sources
- Apply predefined transformations (resize, watermark, etc.)
- File images to a specific folder in the Mailchimp Content Studio
- Work with multiple Mailchimp accounts

## Building

Prerequisites:
- [uv](https://docs.astral.sh/uv/)
- [ruff](https://docs.astral.sh/ruff/)
- [pre-commit](https://pre-commit.com/)

With the above tools installed, run the following two commands to prepare your environment:

```bash
uv sync  # Sets up a python virtualenvironment for this project.
pre-commit install  # Install pre-commit git hooks.
pre-commit install -t post-checkout  # Install post-checkout git hooks.
```
You can now run the project with `uv run mailchimp-image-processor` or run tests with `uv run pytest`. Modify application code under the *src/* directory and modify tests under the *tests/* directory.

Normally, you would have to run `uv sync` everytime you perform any git operation that causes the _uv.lock_ and _pyproject.toml_ files to be updated out-of-band of `uv`. However, there is a git hook configured as part of the above that will run `uv sync` on every pull, merge, or checkout so you don't have to remember to do that. We also run `ruff check` and `ruff format` as part of the pre-commit hooks — these perform linting and formatting respectively and can be [configured](https://docs.astral.sh/ruff/configuration/) via the `[tool.ruff]` dictionary in _pyproject.toml_.

In addition to the local git hooks, we also have two github actions workflows to complete the **trunk-based SDLC**: _Test_ and _Release_. The _Test_ workflow runs on every commit to non-default branches and performs linting — with proper github annotations — and runs the test suite. The _Release_ workflow runs [release-please](https://github.com/googleapis/release-please) on every commit to the default branch which will either create a PR bumping the version in _pyproject.toml_ or create a new git release for the version. If a new git release is created, the _Release_ workflow will also build binaries by leveraging [pyinstaller](https://pyinstaller.org/en/stable/index.html) and attach them to the specified git release.

All commits to main should be made through PRs and should be squash-merged to work properly with release-please and maintain a clean git history.

