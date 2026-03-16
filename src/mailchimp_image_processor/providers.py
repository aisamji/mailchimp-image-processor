"""Image extraction providers for various sources."""

import io
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import override
from urllib.parse import parse_qs, urlparse

import httplib2
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, build_from_document
from googleapiclient.errors import HttpError
from PIL import Image as img, UnidentifiedImageError
from PIL.Image import Image

from mailchimp_image_processor import config


class ImageExtractionError(Exception):
    """Generic exception for image extraction failures across all providers.

    This exception is provider-agnostic and can be reused by
    FilesystemImageProvider, GoogleDriveImageProvider, and future providers.

    Attributes:
        message: Human-readable error description
        source: The source that failed to extract (URL, path, etc.)
        cause: Optional underlying exception that caused this error
    """

    def __init__(self, message: str, source: str, cause: Exception | None = None):
        self.message = message
        self.source = source
        self.cause = cause
        super().__init__(f"{message}: {source}")


@dataclass
class DriveUrlInfo:
    """Information extracted from a Google Drive URL."""

    file_id: str


def parse_drive_url(url: str) -> DriveUrlInfo:
    """Parse a Google Drive URL to extract the file/folder ID."""
    parsed = urlparse(url)

    # Validate domain
    if parsed.netloc not in ("drive.google.com", "docs.google.com"):
        raise ValueError(f"Not a valid Google Drive URL: {url}")

    match = re.search(r"/file/d/([^/]+)", url)
    if match:
        return DriveUrlInfo(file_id=match.group(1))

    match = re.search(r"/document/d/([^/]+)", url)
    if match:
        return DriveUrlInfo(file_id=match.group(1))

    match = re.search(r"/folders/([^/]+)", url)
    if match:
        return DriveUrlInfo(file_id=match.group(1))

    # Try /open?id= format
    if parsed.path == "/open":
        query_params = parse_qs(parsed.query)
        if "id" in query_params:
            return DriveUrlInfo(file_id=query_params["id"][0])

    raise ValueError(f"Could not extract file ID from URL: {url}")


class ImageProvider(ABC):
    """Abstract base class for extracting images from various sources."""

    @abstractmethod
    def extract(self, source: str) -> list[Image]:
        """Extract images from the given source string."""


class FilesystemImageProvider(ImageProvider):
    """Extracts images from the local filesystem."""

    @override
    def extract(self, source: str) -> list[Image]:
        """Read one or more images from the given path.

        If source is a file, try to read it as an PIL.Image and return an array with just that item.
        If source is a directory, load all image files in the directory as PIL.Image and return an array with the images. Does NOT descend into subdirectories.
        """
        if not os.path.exists(source):
            raise FileNotFoundError({source})
        if os.path.isfile(source):
            return [self._extract_from_file(source)]
        elif os.path.isdir(source):
            return self._extract_from_dir(source)
        else:
            raise ValueError("`source` must be the path to a file or directory.")

    def _extract_from_dir(self, directory: str) -> list[Image]:
        """Extract all valid images from a directory, skipping unreadable or non-image files."""
        images: list[Image] = []
        for file in os.listdir(directory):
            try:
                images.append(self._extract_from_file(os.path.join(directory, file)))
            except (PermissionError, UnidentifiedImageError):
                # Ignore unreadable files. Potentially display warning.
                pass
        return images

    def _extract_from_file(self, file: str) -> Image:
        """Open and return the image at the given file path."""
        return img.open(file)


class GoogleDriveImageProvider(ImageProvider):
    """Extracts images from Google Drive files, folders, and Google Docs."""

    def __init__(self, http=None, discovery_doc=None):
        """Initialize Google Drive provider.

        Args:
            http: Optional HTTP mock for testing (overrides credentials)
            discovery_doc: Optional discovery document for testing
        """
        self._http = http
        self._discovery_doc = discovery_doc

        # Load credentials unless http mock is provided for testing
        if http is None:
            credentials_path = config.get_credentials_path()
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path),
                scopes=[
                    "https://www.googleapis.com/auth/drive.file",
                ],
            )
            self._credentials = flow.run_local_server(port=0)
        else:
            self._credentials = None

    @override
    def extract(self, source: str) -> list[Image]:
        """Extract images from Google Drive URL."""
        # Parse the URL to get file ID
        url_info = parse_drive_url(source)

        # Build the Drive service
        if self._discovery_doc:
            import json

            service = build_from_document(
                json.loads(self._discovery_doc),
                http=self._http,
                credentials=self._credentials,
            )
        else:
            service = build(
                "drive", "v3", http=self._http, credentials=self._credentials
            )

        # Check if this is a Google Docs URL
        if "/document/" in source:
            # Get document content
            doc = service.documents().get(documentId=url_info.file_id).execute()
            # Check for inline objects (embedded images)
            inline_objects = doc.get("inlineObjects", {})

            images = []
            for obj_id, obj_data in inline_objects.items():
                # Extract content URI from embedded image
                try:
                    image_props = obj_data["inlineObjectProperties"]["embeddedObject"][
                        "imageProperties"
                    ]
                    content_uri = image_props.get("contentUri")

                    if content_uri:
                        # Download the image from the content URI
                        h = httplib2.Http() if self._http is None else self._http
                        resp, content = h.request(content_uri)
                        image = img.open(io.BytesIO(content))
                        images.append(image)
                except (KeyError, UnidentifiedImageError, httplib2.HttpLib2Error):
                    # Skip objects that aren't images or can't be downloaded
                    pass

            return images

        # Check if this is a folder URL
        if "/folders/" in source:
            # List files in folder
            try:
                results = (
                    service.files().list(q=f"'{url_info.file_id}' in parents").execute()
                )
            except HttpError as e:
                raise ImageExtractionError(
                    f"Failed to list folder: {e.reason}", source, cause=e
                ) from e

            files = results.get("files", [])

            images = []
            for file in files:
                # Only process image files
                mime_type = file.get("mimeType", "")
                if mime_type.startswith("image/"):
                    try:
                        # Download the image
                        request = service.files().get_media(fileId=file["id"])
                        file_content = request.execute()
                        image = img.open(io.BytesIO(file_content))
                        images.append(image)
                    except (HttpError, UnidentifiedImageError):
                        # Skip files that can't be downloaded or aren't valid images
                        pass

            return images

        # Download file content
        request = service.files().get_media(fileId=url_info.file_id)
        try:
            file_content = request.execute()
        except HttpError as e:
            raise ImageExtractionError(
                f"Failed to download file: {e.reason}", source, cause=e
            ) from e

        # Convert to PIL Image
        try:
            image = img.open(io.BytesIO(file_content))
        except UnidentifiedImageError as e:
            raise ImageExtractionError("File is not an image", source, cause=e) from e

        return [image]
