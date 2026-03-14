from pathlib import Path

from platformdirs import user_config_path, user_data_path

APP_NAME = "mip"
CONFIG_DIR = user_config_path(APP_NAME)
DATA_DIR = user_data_path(APP_NAME)


def get_credentials_path() -> Path:
    """Get the credentials.json path from the user config directory."""
    return CONFIG_DIR / "credentials.json"
