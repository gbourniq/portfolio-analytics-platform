"""Integration tests for API workflows.

These tests verify end-to-end functionality of the API endpoints
when running in a containerized environment.
"""

import datetime as dtm
import io
import zipfile
from http import HTTPStatus
from typing import Generator

import pytest
import requests

# Configuration
BASE_URL = "http://localhost:8000"
HEADERS = {"Accept": "application/json"}


@pytest.fixture(scope="module")
def api_client() -> Generator[requests.Session, None, None]:
    """Create a session for API requests."""
    session = requests.Session()
    session.headers.update(HEADERS)

    # Verify API is accessible
    try:
        response = session.get(f"{BASE_URL}/health")
        response.raise_for_status()
    except requests.RequestException as e:
        pytest.skip(f"API not available at {BASE_URL}: {str(e)}")

    yield session
    session.close()


@pytest.mark.integration
@pytest.mark.api_integration
class TestFXDataPipeline:
    """Test FX market data pipeline workflow."""

    def test_fx_data_pipeline(self, api_client: requests.Session) -> None:
        """Test creating FX market data with a small sample."""
        # Given
        payload = {
            "instruments": ["USD", "EUR"],
            "start_date": (dtm.date.today() - dtm.timedelta(days=5)).isoformat(),
            "end_date": dtm.date.today().isoformat(),
        }

        # When
        response = api_client.post(f"{BASE_URL}/market_data/fx", json=payload)

        # Then
        assert response.status_code == HTTPStatus.OK
        data = response.json()

        # Verify response structure
        assert "output_path" in data
        assert "file_stats" in data

        # Verify data coverage
        stats = data["file_stats"]
        assert stats["row_count"] > 0
        assert any("USD" in ticker for ticker in stats["currencies_covered"])
        assert any("EUR" in ticker for ticker in stats["currencies_covered"])


@pytest.mark.integration
@pytest.mark.api_integration
class TestPortfolioWorkflow:
    """Test complete portfolio management workflow."""

    @pytest.fixture
    def sample_portfolio(self) -> io.BytesIO:
        """Create a sample portfolio file."""
        content = "Date,Value\n2024-01-01,100\n2024-01-02,200\n"
        return io.BytesIO(content.encode())

    def test_portfolio_workflow(
        self, api_client: requests.Session, sample_portfolio: io.BytesIO
    ) -> None:
        """Test complete portfolio workflow: upload, list, download, delete."""
        # 1. Upload portfolio
        files = {"file": ("test_portfolio.csv", sample_portfolio, "text/csv")}
        response = api_client.post(f"{BASE_URL}/portfolio", files=files)

        assert response.status_code == HTTPStatus.CREATED
        upload_data = response.json()
        assert upload_data["filename"] == "test_portfolio.csv"

        # 2. Download all portfolios (including our upload)
        response = api_client.get(
            f"{BASE_URL}/portfolio/download", params={"samples_only": False}
        )

        assert response.status_code == HTTPStatus.OK
        assert response.headers["content-type"] == "application/zip"

        # Verify our file is in the zip
        zip_data = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_data) as zf:
            assert "test_portfolio.csv" in zf.namelist()

        # 3. Download specific portfolio
        response = api_client.get(f"{BASE_URL}/portfolio/download/test_portfolio.csv")

        assert response.status_code == HTTPStatus.OK
        assert response.headers["content-type"] == "application/octet-stream"

        # 4. Delete all portfolios
        response = api_client.delete(f"{BASE_URL}/portfolio")

        assert response.status_code == HTTPStatus.OK
        delete_data = response.json()
        assert "Successfully deleted" in delete_data["message"]

        # 5. Verify deletion
        response = api_client.get(f"{BASE_URL}/portfolio/download/test_portfolio.csv")
        assert response.status_code == HTTPStatus.NOT_FOUND


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
