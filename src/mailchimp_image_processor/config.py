from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "mailchimp-image-processor"


def get_credentials_path() -> Path:
    """Get the credentials.json path from the user config directory."""
    return CONFIG_DIR / "credentials.json"
