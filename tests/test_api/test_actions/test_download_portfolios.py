"""Unit tests for portfolio download endpoints."""

from http import HTTPStatus
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

ENDPOINT = "/portfolio"
FILESYSTEM_MODULE = "portfolio_analytics.common.utils.filesystem"


@pytest.fixture
def test_app_client(isolated_filesystem):
    """Create a test client with mocked filesystem paths."""
    # Create and start patches before importing FastAPI app
    with patch(
        f"{FILESYSTEM_MODULE}.PORTFOLIO_SAMPLES_DIR", isolated_filesystem["samples"]
    ), patch(
        f"{FILESYSTEM_MODULE}.PORTFOLIO_UPLOADS_DIR", isolated_filesystem["uploads"]
    ):
        # Import app here after patches are active
        from portfolio_analytics.api.api_main import app

        client = TestClient(app)
        yield client, isolated_filesystem["samples"], isolated_filesystem["uploads"]


class TestDownloadPortfolios:
    """Test suite for portfolio download endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data."""
        self.sample_content = b"Date,Value\n2024-01-01,100"
        self.upload_content = b"Date,Value\n2024-01-02,200"

    @pytest.mark.parametrize(
        "samples_only,expected_filename",
        [
            (True, "sample_portfolios.zip"),
            (False, "all_portfolios.zip"),
        ],
    )
    def test_download_portfolios(
        self,
        test_app_client,
        samples_only: bool,
        expected_filename: str,
    ) -> None:
        """Test downloading portfolio archives with different options."""
        # Given
        client, samples_dir, uploads_dir = test_app_client

        # Create test files
        (samples_dir / "sample1.csv").write_bytes(self.sample_content)
        (samples_dir / "sample2.csv").write_bytes(self.sample_content)
        (uploads_dir / "upload1.csv").write_bytes(self.upload_content)
        (uploads_dir / "upload2.csv").write_bytes(self.upload_content)

        # When
        response = client.get(
            f"{ENDPOINT}/download", params={"samples_only": samples_only}
        )

        # Then
        assert response.status_code == HTTPStatus.OK
        assert response.headers["content-type"] == "application/zip"
        assert (
            response.headers["content-disposition"]
            == f'attachment; filename="{expected_filename}"'
        )

    def test_download_nonexistent_portfolio(self, test_app_client) -> None:
        """Test downloading a nonexistent portfolio file returns 404."""
        # Given
        client, _, _ = test_app_client
        filename = "nonexistent.csv"

        # When
        response = client.get(f"{ENDPOINT}/download/{filename}")

        # Then
        assert response.status_code == HTTPStatus.NOT_FOUND
