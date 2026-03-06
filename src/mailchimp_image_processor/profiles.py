import json
import os
from dataclasses import dataclass
from pathlib import Path


class ProfileError(Exception):
    pass


@dataclass
class Profile:
    name: str
    api_key: str
    server_prefix: str


def get_profiles_path() -> Path:
    override = os.environ.get("MIP_PROFILES_PATH")
    if override:
        return Path(override)
    return Path.home() / ".config" / "mip" / "profiles.json"


class ProfileStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path if path is not None else get_profiles_path()

    def load(self) -> dict[str, Profile]:
        if not self.path.exists():
            return {}
        with self.path.open() as f:
            data = json.load(f)
        return {name: Profile(name=name, **attrs) for name, attrs in data.items()}

    def save(self, profiles: dict[str, Profile]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            name: {"api_key": p.api_key, "server_prefix": p.server_prefix}
            for name, p in profiles.items()
        }
        with self.path.open("w") as f:
            json.dump(data, f, indent=2)

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
