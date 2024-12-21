"""Unit tests for portfolio deletion endpoints."""

from pathlib import Path
from typing import List

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from portfolio_analytics.api.actions.delete_portfolios import router
from portfolio_analytics.common.filesystem import PORTFOLIO_UPLOADS_DIR


class TestDeletePortfolios:
    """Test suite for portfolio deletion endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        app = FastAPI()
        app.include_router(router)
        self.client = TestClient(app)

    @pytest.mark.parametrize(
        "portfolio_files,expected_message,expected_status",
        [
            (
                [Path("file1.csv"), Path("file2.csv")],
                "Successfully deleted 2 portfolio files (except samples)",
                200,
            ),
            ([], "No portfolio files found to delete", 200),
        ],
    )
    def test_delete_portfolios(
        self,
        monkeypatch,
        portfolio_files: List[Path],
        expected_message: str,
        expected_status: int,
    ):
        """Test portfolio deletion with different file scenarios."""

        # Given
        def mock_get_portfolio_files():
            return [PORTFOLIO_UPLOADS_DIR / f for f in portfolio_files]

        def mock_cleanup_portfolio_uploads():
            pass

        def mock_cleanup_cache():
            pass

        monkeypatch.setattr(
            "portfolio_analytics.api.actions.delete_portfolios.get_portfolio_files",
            mock_get_portfolio_files,
        )
        monkeypatch.setattr(
            "portfolio_analytics.api.actions.delete_portfolios.cleanup_portfolio_uploads",
            mock_cleanup_portfolio_uploads,
        )
        monkeypatch.setattr(
            "portfolio_analytics.api.actions.delete_portfolios.cleanup_cache",
            mock_cleanup_cache,
        )

        # When
        response = self.client.delete("/portfolio")

        # Then
        assert response.status_code == expected_status
        assert response.json()["message"] == expected_message
