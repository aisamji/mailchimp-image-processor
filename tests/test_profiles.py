import json

import pytest

from mailchimp_image_processor.profiles import (
    Profile,
    ProfileError,
    ProfileStore,
    resolve_profile,
)


class TestProfileStore:
    def _store(self, tmp_path):
        return ProfileStore(
            path=tmp_path / "profiles.json",
            credentials_path=tmp_path / "credentials.json",
        )

    def test_load_missing_profiles_file(self, tmp_path):
        assert self._store(tmp_path).load() == {}

    def test_load_skips_profiles_without_credentials(self, tmp_path, caplog):
        (tmp_path / "profiles.json").write_text(
            json.dumps({"default": {"mailchimp_server_prefix": "us6"}})
        )
        # credentials.json absent
        import logging

        with caplog.at_level(logging.WARNING):
            profiles = self._store(tmp_path).load()
        assert profiles == {}
        assert "default" in caplog.text

    def test_load_existing_file(self, tmp_path):
        (tmp_path / "profiles.json").write_text(
            json.dumps(
                {
                    "default": {"mailchimp_server_prefix": "us6"},
                    "work": {"mailchimp_server_prefix": "us1"},
                }
            )
        )
        (tmp_path / "credentials.json").write_text(
            json.dumps(
                {
                    "default": {"mailchimp_api_key": "key1"},
                    "work": {"mailchimp_api_key": "key2"},
                }
            )
        )
        profiles = self._store(tmp_path).load()
        assert set(profiles.keys()) == {"default", "work"}
        assert profiles["default"] == Profile(
            name="default", mailchimp_api_key="key1", mailchimp_server_prefix="us6"
        )
        assert profiles["work"] == Profile(
            name="work", mailchimp_api_key="key2", mailchimp_server_prefix="us1"
        )

    def test_save_creates_parent_dirs(self, tmp_path):
        store = ProfileStore(
            path=tmp_path / "config" / "profiles.json",
            credentials_path=tmp_path / "data" / "credentials.json",
        )
        store.save(
            {
                "default": Profile(
                    name="default", mailchimp_api_key="k", mailchimp_server_prefix="us6"
                )
            }
        )
        assert store.path.exists()
        assert store.credentials_path.exists()

    def test_save_writes_correct_json(self, tmp_path):
        self._store(tmp_path).save(
            {
                "default": Profile(
                    name="default",
                    mailchimp_api_key="key1",
                    mailchimp_server_prefix="us6",
                ),
            }
        )
        assert json.loads((tmp_path / "profiles.json").read_text()) == {
            "default": {"mailchimp_server_prefix": "us6"}
        }
        assert json.loads((tmp_path / "credentials.json").read_text()) == {
            "default": {"mailchimp_api_key": "key1"}
        }

    def test_get_returns_profile(self, tmp_path):
        (tmp_path / "profiles.json").write_text(
            json.dumps({"default": {"mailchimp_server_prefix": "us6"}})
        )
        (tmp_path / "credentials.json").write_text(
            json.dumps({"default": {"mailchimp_api_key": "key1"}})
        )
        profile = self._store(tmp_path).get("default")
        assert profile == Profile(
            name="default", mailchimp_api_key="key1", mailchimp_server_prefix="us6"
        )

    def test_get_raises_for_unknown(self, tmp_path):
        with pytest.raises(ProfileError, match="'missing'"):
            self._store(tmp_path).get("missing")

    def test_add_persists_profile(self, tmp_path):
        store = self._store(tmp_path)
        store.add(
            Profile(name="new", mailchimp_api_key="k", mailchimp_server_prefix="us2")
        )
        loaded = store.load()
        assert "new" in loaded
        assert loaded["new"].mailchimp_api_key == "k"

    def test_remove_persists(self, tmp_path):
        (tmp_path / "profiles.json").write_text(
            json.dumps({"default": {"mailchimp_server_prefix": "us6"}})
        )
        (tmp_path / "credentials.json").write_text(
            json.dumps({"default": {"mailchimp_api_key": "key1"}})
        )
        store = self._store(tmp_path)
        store.remove("default")
        assert store.load() == {}

    def test_remove_raises_for_unknown(self, tmp_path):
        with pytest.raises(ProfileError, match="'ghost'"):
            self._store(tmp_path).remove("ghost")


class TestResolveProfile:
    def _profiles(self):
        return {
            "default": Profile(
                name="default", mailchimp_api_key="key_d", mailchimp_server_prefix="us6"
            ),
            "work": Profile(
                name="work", mailchimp_api_key="key_w", mailchimp_server_prefix="us1"
            ),
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

    def test_raises_when_profile_not_found(self, monkeypatch):
        monkeypatch.delenv("MIP_PROFILE", raising=False)
        with pytest.raises(ProfileError):
            resolve_profile(
                {
                    "work": Profile(
                        name="work",
                        mailchimp_api_key="k",
                        mailchimp_server_prefix="us1",
                    )
                },
                cli_name=None,
            )
