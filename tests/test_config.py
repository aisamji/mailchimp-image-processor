"""Tests for the config module."""

from platformdirs import user_config_path

from mailchimp_image_processor import config


def test_get_credentials_path():
    """credentials path resolves to the expected location within the user config directory."""
    result = config.get_credentials_path()
    assert result == user_config_path("mip") / "credentials.json"
