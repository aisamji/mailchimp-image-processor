import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import override
from urllib.parse import parse_qs, urlparse

from PIL import Image as img, UnidentifiedImageError
from PIL.Image import Image


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
    @abstractmethod
    def extract(self, source: str) -> list[Image]:
        pass


class FilesystemImageProvider(ImageProvider):
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
        images: list[Image] = []
        for file in os.listdir(directory):
            try:
                images.append(self._extract_from_file(os.path.join(directory, file)))
            except (PermissionError, UnidentifiedImageError):
                # Ignore unreadable files. Potentially display warning.
                pass
        return images

    def _extract_from_file(self, file: str) -> Image:
        return img.open(file)
