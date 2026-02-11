"""Helper utilities for mocking Google API responses in tests.

This module provides a fluent interface for creating HttpMockSequence objects
used in testing google-api-python-client based code. It reduces boilerplate
while maintaining the official Google-recommended testing pattern.

Example usage:
    # Simple file download
    http = MockResponseBuilder().file_download(image_bytes).build()

    # Folder with multiple images
    http = (MockResponseBuilder()
        .folder_listing([
            {"id": "img1", "mimeType": "image/jpeg"},
            {"id": "img2", "mimeType": "image/png"}
        ])
        .success(image_bytes)  # Download img1
        .success(image_bytes)  # Download img2
        .build())

    # Error responses
    http = MockResponseBuilder().not_found().build()
    http = MockResponseBuilder().forbidden().build()
"""

import json
from typing import Any

from googleapiclient.http import HttpMockSequence


class MockResponseBuilder:
    """Fluent builder for creating HttpMockSequence objects for Google API tests.

    This class provides a convenient interface for constructing mock HTTP responses
    used with google-api-python-client's HttpMockSequence. Each method adds a
    response to the sequence and returns self for method chaining.

    Methods can be chained to create multi-step API interactions:
        builder = MockResponseBuilder()
        builder.success(data1).success(data2).build()
    """

    def __init__(self):
        """Initialize an empty response sequence."""
        self._responses: list[tuple[dict[str, str], bytes]] = []

    def add_response(self, status: str, body: bytes) -> "MockResponseBuilder":
        """Add a raw HTTP response to the sequence.

        Args:
            status: HTTP status code as string (e.g., "200", "404")
            body: Response body as bytes

        Returns:
            self for method chaining
        """
        self._responses.append(({"status": status}, body))
        return self

    def success(self, body: bytes) -> "MockResponseBuilder":
        """Add a successful (200 OK) response.

        Args:
            body: Response body as bytes

        Returns:
            self for method chaining
        """
        return self.add_response("200", body)

    def not_found(self, message: str = "File not found") -> "MockResponseBuilder":
        """Add a 404 Not Found error response.

        Args:
            message: Error message to include in response

        Returns:
            self for method chaining
        """
        error_body = json.dumps({"error": {"code": 404, "message": message}}).encode()
        return self.add_response("404", error_body)

    def forbidden(self, message: str = "Forbidden") -> "MockResponseBuilder":
        """Add a 403 Forbidden error response.

        Args:
            message: Error message to include in response

        Returns:
            self for method chaining
        """
        error_body = json.dumps({"error": {"code": 403, "message": message}}).encode()
        return self.add_response("403", error_body)

    def rate_limited(
        self, message: str = "Rate limit exceeded"
    ) -> "MockResponseBuilder":
        """Add a 429 Rate Limited error response.

        Args:
            message: Error message to include in response

        Returns:
            self for method chaining
        """
        error_body = json.dumps({"error": {"code": 429, "message": message}}).encode()
        return self.add_response("429", error_body)

    def server_error(
        self, message: str = "Internal server error"
    ) -> "MockResponseBuilder":
        """Add a 500 Internal Server Error response.

        Args:
            message: Error message to include in response

        Returns:
            self for method chaining
        """
        error_body = json.dumps({"error": {"code": 500, "message": message}}).encode()
        return self.add_response("500", error_body)

    def file_download(self, image_bytes: bytes) -> "MockResponseBuilder":
        """Add a successful file download response (Drive API files.get_media).

        This is a convenience method for the common case of downloading a single
        file from Google Drive.

        Args:
            image_bytes: File content to return

        Returns:
            self for method chaining
        """
        return self.success(image_bytes)

    def folder_listing(self, files: list[dict[str, str]]) -> "MockResponseBuilder":
        """Add a successful folder listing response (Drive API files.list).

        Args:
            files: List of file metadata dicts with "id" and "mimeType" keys

        Returns:
            self for method chaining

        Example:
            builder.folder_listing([
                {"id": "img1", "mimeType": "image/jpeg"},
                {"id": "doc1", "mimeType": "text/plain"}
            ])
        """
        response_body = json.dumps({"files": files}).encode()
        return self.success(response_body)

    def empty_folder(self) -> "MockResponseBuilder":
        """Add a successful empty folder listing response.

        Returns:
            self for method chaining
        """
        return self.folder_listing([])

    def document_get(self, doc_data: dict[str, Any]) -> "MockResponseBuilder":
        """Add a successful document.get response (Docs API documents.get).

        Args:
            doc_data: Document metadata dict (must include "documentId")

        Returns:
            self for method chaining

        Example:
            builder.document_get({
                "documentId": "DOC_ID",
                "title": "My Doc",
                "inlineObjects": {...}
            })
        """
        response_body = json.dumps(doc_data).encode()
        return self.success(response_body)

    def document_no_images(
        self, doc_id: str, title: str = "My Doc"
    ) -> "MockResponseBuilder":
        """Add a document.get response for a document with no images.

        Args:
            doc_id: Document ID
            title: Document title (defaults to "My Doc")

        Returns:
            self for method chaining
        """
        return self.document_get({"documentId": doc_id, "title": title})

    def build(self) -> HttpMockSequence:
        """Build and return the HttpMockSequence object.

        Returns:
            HttpMockSequence configured with all added responses
        """
        return HttpMockSequence(self._responses)
