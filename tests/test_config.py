from pathlib import Path

from platformdirs import user_config_dir

from mailchimp_image_processor import config


def test_get_credentials_path():
    result = config.get_credentials_path()
    assert result == Path(user_config_dir("mip")) / "credentials.json"
