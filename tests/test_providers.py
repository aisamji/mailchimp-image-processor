import io
import os
import shutil
import tempfile
from collections.abc import Generator

import pytest
from googleapiclient.http import HttpMockSequence
from PIL import Image as img
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


class TestGoogleDriveUrlParser:
    """Tests for Google Drive URL parsing utility."""

    def test_parse_drive_url_extracts_simple_file_id(self):
        """URL parser extracts file ID from basic file URL."""
        from mailchimp_image_processor.providers import parse_drive_url

        result = parse_drive_url("https://drive.google.com/file/d/ABC123/view")
        assert result.file_id == "ABC123"

    def test_parse_drive_url_extracts_file_id_with_query_params(self):
        """URL parser extracts file ID from file URL with query parameters."""
        from mailchimp_image_processor.providers import parse_drive_url

        result = parse_drive_url(
            "https://drive.google.com/file/d/ABC123/view?usp=sharing"
        )
        assert result.file_id == "ABC123"

    def test_parse_drive_url_extracts_file_id_from_open_url(self):
        """URL parser extracts file ID from /open?id= URL format."""
        from mailchimp_image_processor.providers import parse_drive_url

        result = parse_drive_url("https://drive.google.com/open?id=ABC123")
        assert result.file_id == "ABC123"

    def test_parse_drive_url_extracts_doc_id(self):
        """URL parser extracts document ID from Google Docs URL."""
        from mailchimp_image_processor.providers import parse_drive_url

        result = parse_drive_url("https://docs.google.com/document/d/DOC456/edit")
        assert result.file_id == "DOC456"

    def test_parse_drive_url_extracts_folder_id(self):
        """URL parser extracts folder ID from folder URL."""
        from mailchimp_image_processor.providers import parse_drive_url

        result = parse_drive_url("https://drive.google.com/drive/folders/FOLDER789")
        assert result.file_id == "FOLDER789"

    def test_parse_drive_url_invalid_url_raises_error(self):
        """URL parser raises ValueError for non-Google Drive URLs."""
        from mailchimp_image_processor.providers import parse_drive_url

        with pytest.raises(ValueError, match="Not a valid Google Drive URL"):
            parse_drive_url("https://example.com/file.jpg")


################################################


class TestGoogleDriveImageProvider:
    """Tests for the GoogleDriveImageProvider"""

    @pytest.fixture(scope="class")
    def mock_data_dir(self) -> str:
        """Return path to mock data files for Google API responses."""
        return "./tests/mock_data/google_drive"

    @pytest.fixture(scope="class")
    def drive_discovery(self, mock_data_dir: str) -> bytes:
        """Load the Google Drive API v3 discovery document."""
        with open(f"{mock_data_dir}/drive_v3_discovery.json", "rb") as f:
            return f.read()

    @pytest.fixture(scope="class")
    def sample_image_bytes(self) -> bytes:
        """Create a minimal valid PNG image in memory."""
        image = img.new("RGB", (100, 100), color="red")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    def test_extract_image_file_returns_single_image(
        self, drive_discovery: bytes, sample_image_bytes: bytes
    ):
        """When source is an image file URL, extract returns a single image."""
        from mailchimp_image_processor.providers import GoogleDriveImageProvider

        http = HttpMockSequence(
            [
                # 1. files.get_media to download content
                ({"status": "200"}, sample_image_bytes),
            ]
        )

        provider = GoogleDriveImageProvider(http=http, discovery_doc=drive_discovery)
        url = "https://drive.google.com/file/d/1ABC123def456/view"

        images = provider.extract(url)

        assert len(images) == 1
        assert images[0].verify() is None

    def test_extract_non_image_file_raises_error(self, drive_discovery: bytes):
        """When source is a non-image file URL, extract raises ImageExtractionError."""
        from mailchimp_image_processor.providers import (
            GoogleDriveImageProvider,
            ImageExtractionError,
        )

        http = HttpMockSequence(
            [
                # 1. files.get_media returns non-image content
                ({"status": "200"}, b"This is a text file, not an image"),
            ]
        )

        provider = GoogleDriveImageProvider(http=http, discovery_doc=drive_discovery)
        url = "https://drive.google.com/file/d/2DEF789ghi012/view"

        with pytest.raises(ImageExtractionError, match="not an image"):
            provider.extract(url)

    def test_extract_file_not_found_raises_error(self, drive_discovery: bytes):
        """When file returns 404, extract raises ImageExtractionError."""
        from mailchimp_image_processor.providers import (
            GoogleDriveImageProvider,
            ImageExtractionError,
        )

        http = HttpMockSequence(
            [
                # 1. files.get_media returns 404
                (
                    {"status": "404"},
                    b'{"error": {"code": 404, "message": "File not found"}}',
                ),
            ]
        )

        provider = GoogleDriveImageProvider(http=http, discovery_doc=drive_discovery)
        url = "https://drive.google.com/file/d/INVALID_ID/view"

        with pytest.raises(ImageExtractionError):
            provider.extract(url)
