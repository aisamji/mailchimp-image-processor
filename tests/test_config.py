from pathlib import Path

from mailchimp_image_processor import config


def test_get_credentials_path():
    result = config.get_credentials_path()
    assert (
        result
        == Path.home() / ".config" / "mailchimp-image-processor" / "credentials.json"
    )
