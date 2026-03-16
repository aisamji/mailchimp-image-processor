"""Profile management for multiple Mailchimp account configurations."""

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path

from mailchimp_image_processor.config import CONFIG_DIR, DATA_DIR

logger = logging.getLogger(__name__)


class ProfileError(Exception):
    """Raised when a profile operation fails, such as accessing a missing profile."""


@dataclass
class Profile:
    """A named Mailchimp account configuration."""

    name: str
    mailchimp_api_key: str
    mailchimp_server_prefix: str


def get_profiles_path() -> Path:
    """Return the path to the profiles configuration file."""
    return CONFIG_DIR / "profiles.json"


def get_credentials_path() -> Path:
    """Return the path to the credentials file."""
    return DATA_DIR / "credentials.json"


class ProfileStore:
    """Persistent store for loading and saving Mailchimp profiles.

    Profile metadata (server prefix) is stored separately from credentials
    (API key) so that sensitive data can be placed in a more restricted
    location if desired.
    """

    def __init__(
        self, path: Path | None = None, credentials_path: Path | None = None
    ) -> None:
        """Initialize a ProfileStore with optional custom file paths.

        Args:
            path: Path to the profiles JSON file. Defaults to the standard config location.
            credentials_path: Path to the credentials JSON file. Defaults to the standard data location.
        """
        self.path = path if path is not None else get_profiles_path()
        self.credentials_path = (
            credentials_path if credentials_path is not None else get_credentials_path()
        )

    def load(self) -> dict[str, Profile]:
        """Load all profiles from disk, merging profile config with credentials.

        Returns an empty dict if the profiles file does not exist. Profiles
        missing a corresponding credentials entry are skipped with a warning.
        """
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
        """Persist profiles to disk, writing config and credentials to separate files."""
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
        """Return the profile with the given name, raising ProfileError if not found."""
        profiles = self.load()
        if name not in profiles:
            raise ProfileError(f"Profile '{name}' not found")
        return profiles[name]

    def add(self, profile: Profile) -> None:
        """Add or replace a profile and persist it to disk."""
        profiles = self.load()
        profiles[profile.name] = profile
        self.save(profiles)

    def remove(self, name: str) -> None:
        """Remove the named profile and persist the change, raising ProfileError if not found."""
        profiles = self.load()
        if name not in profiles:
            raise ProfileError(f"Profile '{name}' not found")
        del profiles[name]
        self.save(profiles)


def resolve_profile(
    profiles: dict[str, Profile], *, cli_name: str | None = None
) -> Profile:
    """Return the active profile, checking CLI arg, then MIP_PROFILE env var, then 'default'.

    Raises ProfileError if the specified profile does not exist or no profile can be resolved.
    """
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
