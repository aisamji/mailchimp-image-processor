import sys
from enum import Enum
from pathlib import Path


class Environment(Enum):
    PYINSTALLER = "PYINSTALLER"
    VENV = "VENV"


environment: Environment | None = None


def detect_environment() -> None:
    """Auto-detect the runtime environment and set config.environment."""
    global environment
    if hasattr(sys, "_MEIPASS"):
        environment = Environment.PYINSTALLER
    else:
        environment = Environment.VENV


def get_credentials_path() -> Path:
    """Get the credentials.json path based on the environment.

    Returns:
        Path to credentials.json file

    Raises:
        RuntimeError: If config.environment is not set
        RuntimeError: If PYINSTALLER mode but sys._MEIPASS not found
    """
    if environment is None:
        raise RuntimeError("config.environment is not set")

    match environment:
        case Environment.PYINSTALLER:
            if not hasattr(sys, "_MEIPASS"):
                raise RuntimeError(
                    "Running in PYINSTALLER mode but sys._MEIPASS not found"
                )
            return Path(sys._MEIPASS) / "credentials.json"
        case Environment.VENV:
            # Navigate from src/mailchimp_image_processor to project root
            project_root = Path(__file__).parent.parent.parent
            return project_root / "credentials.json"


# Auto-detect environment on module import
detect_environment()
