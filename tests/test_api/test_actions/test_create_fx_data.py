"""Unit tests for FX data creation endpoints."""

import datetime as dtm
from http import HTTPStatus

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from portfolio_analytics.api.api_main import app

ENDPOINT = "/market_data/fx"
MODULE = "portfolio_analytics.api.market_data.fx"


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def sample_fx_df():
    """Returns a sample FX DataFrame for testing."""
    return pd.DataFrame(
        {
            "Date": [dtm.date(2024, 1, 1), dtm.date(2024, 1, 2)],
            "Ticker": ["EURUSD=X", "GBPUSD=X"],
        }
    )


@pytest.fixture
def sample_request_data():
    """Returns a sample request data matching the sample FX DataFrame."""
    return {
        "instruments": ["EUR", "GBP"],
        "start_date": "2024-01-01",
        "end_date": "2024-01-02",
    }


class TestCreateFXData:
    """Test suite for FX update request validation."""

    @pytest.fixture(autouse=True)
    def setup(self, sample_fx_df, sample_request_data, monkeypatch, isolated_filesystem):
        """Setup test fixtures."""
        self.sample_df = sample_fx_df
        self.sample_request = sample_request_data
        self.output_path = isolated_filesystem["market_data"] / "fx_data.parquet"

        # Add default mock for all tests
        def default_mock_update_market_data(*args, **kwargs):
            self.sample_df.to_parquet(self.output_path, index=False)
            return self.output_path

        monkeypatch.setattr(
            f"{MODULE}.FX.update_market_data",
            default_mock_update_market_data,
        )

    def test_valid_request(self, client):
        """Test that a valid request is accepted."""
        # When
        response = client.post(ENDPOINT, json=self.sample_request)

        # Then
        assert response.status_code == HTTPStatus.OK

    def test_invalid_dates(self, client):
        """Test that invalid date ranges are rejected."""
        # Given
        request_data = {
            "instruments": ["EUR"],
            "start_date": "2024-01-01",
            "end_date": "2023-01-01",
        }

        # When
        response = client.post(ENDPOINT, json=request_data)

        # Then
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert "Start date must be before end date" in response.text

    def test_invalid_instrument(self, client):
        """Test that invalid instruments are rejected."""
        # Given
        request_data = {
            "instruments": ["INVALID_CURRENCY"],
        }

        # When
        response = client.post(ENDPOINT, json=request_data)

        # Then
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert "Input should be" in response.json()["detail"][0]["msg"]

    def test_successful_update(self, client):
        """Test successful FX data update."""
        # When
        response = client.post(ENDPOINT, json=self.sample_request)

        # Then
        assert response.status_code == HTTPStatus.OK
        response_data = response.json()
        assert response_data["output_path"] == str(self.output_path)
        assert response_data["file_stats"] == {
            "row_count": 2,
            "file_date_range": {"min": "2024-01-01", "max": "2024-01-02"},
            "columns": ["index", "Date", "Ticker"],
            "currencies_covered": ["EURUSD=X", "GBPUSD=X"],
            "file_size_mb": 0.0,
        }

    def test_update_failure(self, client, monkeypatch):
        """Test error handling when FX update fails."""

        # Override the default mock for this specific test
        def mock_update_market_data(*args, **kwargs):
            raise ConnectionError("Download failed")

        monkeypatch.setattr(
            f"{MODULE}.FX.update_market_data",
            mock_update_market_data,
        )

        # Given
        request_data = {"instruments": ["EUR"]}

        # When
        response = client.post(ENDPOINT, json=request_data)

        # Then
        assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
        assert "Download failed" in response.json()["detail"]

    def test_multiple_instruments(self, client, monkeypatch):
        """Test update with multiple instruments."""

        # Override the default mock for this specific test
        def mock_update_market_data(*args, **kwargs):
            return self.output_path

        monkeypatch.setattr(
            f"{MODULE}.FX.update_market_data",
            mock_update_market_data,
        )

        # Given
        request_data = {
            "instruments": ["EUR", "GBP"],
            "start_date": "2024-01-01",
            "end_date": "2024-01-02",
        }

        def mock_read_parquet(*args, **kwargs):
            return pd.DataFrame(
                {
                    "Date": [dtm.date(2024, 1, 1)] * 4,
                    "Ticker": ["EURUSD=X", "EURGBP=X", "GBPUSD=X", "GBPEUR=X"],
                }
            )

        def mock_getsize(*args, **kwargs):
            return 2 * 1024 * 1024  # 2MB

        monkeypatch.setattr("pandas.read_parquet", mock_read_parquet)
        monkeypatch.setattr("os.path.getsize", mock_getsize)

        # When
        response = client.post(ENDPOINT, json=request_data)

        # Then
        assert response.status_code == HTTPStatus.OK
        response_data = response.json()
        assert "EURUSD=X" in response_data["file_stats"]["currencies_covered"]
        assert "GBPUSD=X" in response_data["file_stats"]["currencies_covered"]
