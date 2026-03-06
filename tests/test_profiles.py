import json
from pathlib import Path

import pytest

from mailchimp_image_processor.profiles import (
    Profile,
    ProfileError,
    ProfileStore,
    get_profiles_path,
    resolve_profile,
)


class TestGetProfilesPath:
    def test_default_path(self, monkeypatch):
        monkeypatch.delenv("MIP_PROFILES_PATH", raising=False)
        path = get_profiles_path()
        assert path == Path.home() / ".config" / "mip" / "profiles.json"

    def test_override_via_env(self, monkeypatch, tmp_path):
        override = str(tmp_path / "custom" / "profiles.json")
        monkeypatch.setenv("MIP_PROFILES_PATH", override)
        assert get_profiles_path() == Path(override)


class TestProfileStore:
    def test_load_missing_file(self, tmp_path):
        store = ProfileStore(tmp_path / "profiles.json")
        assert store.load() == {}

    def test_load_existing_file(self, tmp_path):
        profiles_file = tmp_path / "profiles.json"
        profiles_file.write_text(
            json.dumps(
                {
                    "default": {"api_key": "key1", "server_prefix": "us6"},
                    "work": {"api_key": "key2", "server_prefix": "us1"},
                }
            )
        )
        store = ProfileStore(profiles_file)
        profiles = store.load()
        assert set(profiles.keys()) == {"default", "work"}
        assert profiles["default"] == Profile(
            name="default", api_key="key1", server_prefix="us6"
        )
        assert profiles["work"] == Profile(
            name="work", api_key="key2", server_prefix="us1"
        )

    def test_save_creates_parent_dirs(self, tmp_path):
        profiles_file = tmp_path / "nested" / "dir" / "profiles.json"
        store = ProfileStore(profiles_file)
        store.save(
            {"default": Profile(name="default", api_key="k", server_prefix="us6")}
        )
        assert profiles_file.exists()
        data = json.loads(profiles_file.read_text())
        assert data == {"default": {"api_key": "k", "server_prefix": "us6"}}

    def test_save_writes_correct_json(self, tmp_path):
        profiles_file = tmp_path / "profiles.json"
        store = ProfileStore(profiles_file)
        store.save(
            {
                "default": Profile(name="default", api_key="key1", server_prefix="us6"),
            }
        )
        data = json.loads(profiles_file.read_text())
        assert data == {"default": {"api_key": "key1", "server_prefix": "us6"}}

    def test_get_returns_profile(self, tmp_path):
        profiles_file = tmp_path / "profiles.json"
        profiles_file.write_text(
            json.dumps({"default": {"api_key": "key1", "server_prefix": "us6"}})
        )
        store = ProfileStore(profiles_file)
        profile = store.get("default")
        assert profile == Profile(name="default", api_key="key1", server_prefix="us6")

    def test_get_raises_for_unknown(self, tmp_path):
        store = ProfileStore(tmp_path / "profiles.json")
        with pytest.raises(ProfileError, match="'missing'"):
            store.get("missing")

    def test_add_persists_profile(self, tmp_path):
        profiles_file = tmp_path / "profiles.json"
        store = ProfileStore(profiles_file)
        store.add(Profile(name="new", api_key="k", server_prefix="us2"))
        loaded = store.load()
        assert "new" in loaded
        assert loaded["new"].api_key == "k"

    def test_remove_persists(self, tmp_path):
        profiles_file = tmp_path / "profiles.json"
        profiles_file.write_text(
            json.dumps({"default": {"api_key": "key1", "server_prefix": "us6"}})
        )
        store = ProfileStore(profiles_file)
        store.remove("default")
        assert store.load() == {}

    def test_remove_raises_for_unknown(self, tmp_path):
        store = ProfileStore(tmp_path / "profiles.json")
        with pytest.raises(ProfileError, match="'ghost'"):
            store.remove("ghost")


class TestResolveProfile:
    def _profiles(self):
        return {
            "default": Profile(name="default", api_key="key_d", server_prefix="us6"),
            "work": Profile(name="work", api_key="key_w", server_prefix="us1"),
        }

    def test_cli_takes_priority(self, monkeypatch):
        monkeypatch.setenv("MIP_PROFILE", "work")
        profile = resolve_profile(self._profiles(), cli_name="default")
        assert profile.name == "default"

    def test_env_var_used_without_cli(self, monkeypatch):
        monkeypatch.setenv("MIP_PROFILE", "work")
        profile = resolve_profile(self._profiles(), cli_name=None)
        assert profile.name == "work"

    def test_falls_back_to_default(self, monkeypatch):
        monkeypatch.delenv("MIP_PROFILE", raising=False)
        profile = resolve_profile(self._profiles(), cli_name=None)
        assert profile.name == "default"

    def test_raises_when_no_match(self, monkeypatch):
        monkeypatch.delenv("MIP_PROFILE", raising=False)
        with pytest.raises(ProfileError):
            resolve_profile(
                {"work": Profile(name="work", api_key="k", server_prefix="us1")},
                cli_name=None,
            )
