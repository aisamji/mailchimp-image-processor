from pathlib import Path

from platformdirs import user_config_dir

CONFIG_DIR = Path(user_config_dir("mip"))


def get_credentials_path() -> Path:
    """Get the credentials.json path from the user config directory."""
    return CONFIG_DIR / "credentials.json"
