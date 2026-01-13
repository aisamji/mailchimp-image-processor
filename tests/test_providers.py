import os
import shutil
import tempfile
from collections.abc import Generator

import pytest
from PIL import UnidentifiedImageError

from mailchimp_image_processor.providers import FilesystemImageProvider


class TestFileSystemProvider:
    """Tests for the FilesystemProvider"""

    @pytest.fixture(scope="class")
    def tmp_images_dir(
        self,
    ) -> Generator[str, None, None]:
        tempdir = tempfile.mkdtemp()
        bad_permissions_file_name = os.path.join(tempdir, "bad_permissions.jpg")
        bad_permissions_dir_name = os.path.join(tempdir, "bad_permissions")
        try:
            shutil.copy("./tests/sample.jpg", tempdir)
            shutil.copy("./tests/sample.jpg", os.path.join(tempdir, "sample2.jpg"))
            with open(os.path.join(tempdir, "not_an_image.txt"), mode="w"):
                pass
            with open(bad_permissions_file_name, mode="w"):
                pass
            os.chmod(bad_permissions_file_name, 0o000)
            os.mkdir(bad_permissions_dir_name)
            os.chmod(bad_permissions_dir_name, 0o000)
            yield tempdir
        finally:
            # Restore permissions before cleanup
            if os.path.exists(bad_permissions_file_name):
                os.chmod(bad_permissions_file_name, 0o644)
            if os.path.exists(bad_permissions_dir_name):
                os.chmod(bad_permissions_dir_name, 0o755)
            shutil.rmtree(tempdir)

    @pytest.fixture(scope="class")
    def provider(
        self,
    ) -> FilesystemImageProvider:
        return FilesystemImageProvider()

    def test_load_image_from_local_file(
        self, provider: FilesystemImageProvider, tmp_images_dir: str
    ):
        images = provider.extract(os.path.join(tmp_images_dir, "sample.jpg"))
        # Image.verify always returns None but it raises an Exception when it fails.
        assert len(images) == 1 and not images[0].verify()

    def test_load_images_from_invalid_source(self, provider: FilesystemImageProvider):
        with pytest.raises(FileNotFoundError):
            provider.extract("https://www.google.com")

    def test_load_non_image_from_local_file(
        self, provider: FilesystemImageProvider, tmp_images_dir: str
    ):
        with pytest.raises(UnidentifiedImageError):
            provider.extract(os.path.join(tmp_images_dir, "not_an_image.txt"))

    def test_load_images_from_local_directory(
        self, provider: FilesystemImageProvider, tmp_images_dir: str
    ):
        images = provider.extract(tmp_images_dir)
        # Image.verify always returns None but it raises an Exception when it fails.
        assert len(images) == 2 and not any(map(lambda x: x.verify(), images))

    def test_load_local_image_with_missing_permissions(
        self,
        provider: FilesystemImageProvider,
        tmp_images_dir: str,
    ):
        with pytest.raises(PermissionError):
            provider.extract(os.path.join(tmp_images_dir, "bad_permissions.jpg"))

    def test_load_local_directory_with_missing_permissions(
        self,
        provider: FilesystemImageProvider,
        tmp_images_dir: str,
    ):
        with pytest.raises(PermissionError):
            provider.extract(os.path.join(tmp_images_dir, "bad_permissions"))


################################################
