"""Unit tests for portfolio listing endpoint."""

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


class TestListPortfoliosEndpoint:
    """Test cases for the list_portfolios endpoint."""

    def test_empty_portfolio_list(self, test_app_client):
        """Test endpoint returns empty list when no portfolios exist."""
        # Given
        client, _, _ = test_app_client

        # When
        response = client.get(ENDPOINT)

        # Then
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"portfolios": []}

    @pytest.mark.parametrize(
        "test_files,expected_sizes",
        [
            (
                [("portfolio1.csv", 1024), ("portfolio2.xlsx", 2048)],
                [1024, 2048],
            ),
            (
                [("single.csv", 512)],
                [512],
            ),
        ],
    )
    def test_portfolio_list_with_files(
        self,
        test_app_client,
        test_files,
        expected_sizes,
    ):
        """Test endpoint returns correct portfolio list when files exist."""
        # Given
        client, _, uploads_dir = test_app_client

        # Create test files with specified sizes
        for filename, size in test_files:
            file_path = uploads_dir / filename
            file_path.write_bytes(b"x" * size)

        # When
        response = client.get(ENDPOINT)

        # Then
        assert response.status_code == HTTPStatus.OK
        portfolios = sorted(response.json()["portfolios"], key=lambda x: x["filename"])
        test_files_sorted = sorted(test_files, key=lambda x: x[0])
        assert len(portfolios) == len(test_files)
        for portfolio, (filename, expected_size) in zip(portfolios, test_files_sorted):
            assert portfolio["filename"] == filename
            assert portfolio["size"] == expected_size
