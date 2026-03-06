import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


class ProfileError(Exception):
    pass


@dataclass
class Profile:
    name: str
    mailchimp_api_key: str
    mailchimp_server_prefix: str


def get_profiles_path() -> Path:
    override = os.environ.get("MIP_PROFILES_PATH")
    if override:
        return Path(override)
    return Path.home() / ".config" / "mip" / "profiles.json"


def get_credentials_path() -> Path:
    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg_data_home) if xdg_data_home else Path.home() / ".local" / "share"
    return base / "mip" / "credentials.json"


class ProfileStore:
    def __init__(
        self, path: Path | None = None, credentials_path: Path | None = None
    ) -> None:
        self.path = path if path is not None else get_profiles_path()
        self.credentials_path = (
            credentials_path if credentials_path is not None else get_credentials_path()
        )

    def load(self) -> dict[str, Profile]:
        if not self.path.exists():
            return {}
        with self.path.open() as f:
            data = json.load(f)

        creds: dict[str, dict] = {}
        if self.credentials_path.exists():
            with self.credentials_path.open() as f:
                creds = json.load(f)

        profiles = {}
        for name, attrs in data.items():
            if name not in creds:
                logger.warning("Skipping profile '%s': no credentials found", name)
                continue
            profiles[name] = Profile(name=name, **creds[name], **attrs)
        return profiles

    def save(self, profiles: dict[str, Profile]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            name: {"mailchimp_server_prefix": p.mailchimp_server_prefix}
            for name, p in profiles.items()
        }
        with self.path.open("w") as f:
            json.dump(data, f, indent=2)

        self.credentials_path.parent.mkdir(parents=True, exist_ok=True)
        creds = {
            name: {"mailchimp_api_key": p.mailchimp_api_key}
            for name, p in profiles.items()
        }
        with self.credentials_path.open("w") as f:
            json.dump(creds, f, indent=2)

    def get(self, name: str) -> Profile:
        profiles = self.load()
        if name not in profiles:
            raise ProfileError(f"Profile '{name}' not found")
        return profiles[name]

    def add(self, profile: Profile) -> None:
        profiles = self.load()
        profiles[profile.name] = profile
        self.save(profiles)

    def remove(self, name: str) -> None:
        profiles = self.load()
        if name not in profiles:
            raise ProfileError(f"Profile '{name}' not found")
        del profiles[name]
        self.save(profiles)


def resolve_profile(
    profiles: dict[str, Profile], *, cli_name: str | None = None
) -> Profile:
    if cli_name is not None:
        if cli_name not in profiles:
            raise ProfileError(f"Profile '{cli_name}' not found")
        return profiles[cli_name]

    env_name = os.environ.get("MIP_PROFILE")
    if env_name is not None:
        if env_name not in profiles:
            raise ProfileError(f"Profile '{env_name}' not found")
        return profiles[env_name]

    if "default" in profiles:
        return profiles["default"]

    raise ProfileError(
        "No profile specified. Use --profile, set MIP_PROFILE, or create a 'default' profile."
    )
