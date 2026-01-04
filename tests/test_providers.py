from PIL import UnidentifiedImageError
import pytest
from mailchimp_image_processor import providers


### Tests for Filesystem Provider


@pytest.fixture
def filesystem_provider() -> providers.Filesystem:
    return providers.Filesystem()


def test_load_image_from_local_file(filesystem_provider: providers.Filesystem):
    images = filesystem_provider.extract("./tests/images/valid_image_file.jpg")
    # Image.verify always returns None but it raises an Exception when it fails.
    assert len(images) == 1 and not images[0].verify()


@pytest.mark.xfail(raises=UnidentifiedImageError)
def test_load_non_image_from_local_file(filesystem_provider: providers.Filesystem):
    filesystem_provider.extract("./tests/images/failure.txt")


def test_load_images_from_local_directory(filesystem_provider: providers.Filesystem):
    images = filesystem_provider.extract("./tests/images")
    # Image.verify always returns None but it raises an Exception when it fails.
    assert len(images) == 2 and not any(map(lambda x: x.verify(), images))


# TODO: Add tests for non-existent directory, access denied on directory, access denied on file, access denied on file when extracting directory, non-existent file.

################################################
