from platformdirs import user_config_path

from mailchimp_image_processor import config


def test_get_credentials_path():
    result = config.get_credentials_path()
    assert result == user_config_path("mip") / "credentials.json"
