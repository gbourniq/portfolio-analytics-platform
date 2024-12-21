"""Unit tests for portfolio creation endpoints."""

from http import HTTPStatus
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

ENDPOINT = "/portfolio"
FILESYSTEM_MODULE = "portfolio_analytics.common.filesystem"


@pytest.fixture
def test_app_client(isolated_filesystem):
    """Create a test client with isolated filesystem paths."""
    with patch(
        f"{FILESYSTEM_MODULE}.PORTFOLIO_SAMPLES_DIR", isolated_filesystem["samples"]
    ), patch(
        f"{FILESYSTEM_MODULE}.PORTFOLIO_UPLOADS_DIR", isolated_filesystem["uploads"]
    ):
        from portfolio_analytics.api.api_main import app

        client = TestClient(app)
        yield client, isolated_filesystem["samples"], isolated_filesystem["uploads"]


class TestPortfolioUpload:
    """Test suite for portfolio upload endpoint."""

    # Class-level constants instead of fixture
    valid_content = b"Date,Value\n2024-01-01,100\n2024-01-02,200"
    test_filename = "test_portfolio.csv"

    # def test_upload_portfolio_success(self, test_app_client):
    #     """Test successful portfolio upload."""
    #     # Given
    #     client, _, uploads_dir = test_app_client
    #     files = {"file": (self.test_filename, self.valid_content, "text/csv")}

    #     # When
    #     response = client.post(ENDPOINT, files=files)

    #     # Then
    #     assert response.status_code == HTTPStatus.CREATED
    #     response_data = response.json()
    #     assert response_data["filename"] == self.test_filename
    #     assert response_data["content_type"] == "text/csv"
    #     assert response_data["size"] == len(self.valid_content)
    #     assert "uploaded_at" in response_data

    #     # Verify file was written
    #     uploaded_file = uploads_dir / self.test_filename
    #     assert uploaded_file.exists()
    #     assert uploaded_file.read_bytes() == self.valid_content

    @pytest.mark.parametrize(
        "filename, expected_error",
        [
            ("a" * 256, "Filename must be less than {MAX_FILENAME_LENGTH} characters"),
            ("invalid@file.csv", "Filename contains invalid characters"),
            ("file.txt", "Only .csv, .parquet, .xlsx files are supported"),
        ],
    )
    def test_upload_portfolio_invalid_filename(
        self, test_app_client, filename: str, expected_error: str
    ):
        """Test validation fails for invalid filenames."""
        # Given
        client, _, uploads_dir = test_app_client
        files = {"file": (filename, self.valid_content, "text/csv")}

        # When
        response = client.post(ENDPOINT, files=files)

        # Then
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert expected_error in response.json()["message"]

    # def test_upload_portfolio_duplicate_file(self, test_app_client):
    #     """Test validation fails when file already exists."""
    #     # Given
    #     client, _, uploads_dir = test_app_client
    #     existing_file = uploads_dir / self.test_filename
    #     existing_file.write_bytes(b"existing content")

    #     files = {"file": (self.test_filename, self.valid_content, "text/csv")}

    #     # When
    #     response = client.post(ENDPOINT, files=files)

    #     # Then
    #     assert response.status_code == HTTPStatus.BAD_REQUEST
    #     assert "A file with this name already exists" in response.json()["message"]

    @pytest.mark.parametrize(
        "content, expected_error",
        [
            (
                b"invalid_content",
                'DataFrame must contain a "Date" column',
            ),
            (
                b"Date,Value\ninvalid,100",
                'The "Date" column must contain valid date/datetime values',
            ),
            (
                b"Date,Value\n2024-01-01,abc",
                'Column "Value" must contain numeric values',
            ),
        ],
    )
    def test_upload_portfolio_invalid_content(
        self, test_app_client, content: bytes, expected_error: str
    ):
        """Test validation fails for invalid file contents."""
        # Given
        client, _, _ = test_app_client
        files = {"file": ("somefile.csv", content, "text/csv")}

        # When
        response = client.post(ENDPOINT, files=files)

        # Then
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert expected_error in response.json()["message"]
