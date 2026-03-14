from pathlib import Path

from platformdirs import user_config_path

CONFIG_DIR = user_config_path("mip")


def get_credentials_path() -> Path:
    """Get the credentials.json path from the user config directory."""
    return CONFIG_DIR / "credentials.json"
