"""Unit tests for health check endpoint."""

from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient

from portfolio_analytics.api.actions.health import HealthResponse

ENDPOINT = "/health"


@pytest.fixture
def client():
    """Create a test client fixture."""
    from portfolio_analytics.api.api_main import app

    return TestClient(app)


class TestHealthCheckEndpoint:
    """Test cases for the health check endpoint."""

    def test_health_check(self, client):
        """Test the health check endpoint returns expected response."""
        # When
        response = client.get(ENDPOINT)

        # Then
        assert response.status_code == HTTPStatus.OK
        health_data = response.json()
        assert isinstance(health_data, dict)
        assert health_data["status"] == "healthy"
        assert health_data["version"] == "1.0.0"

        # Validate response matches Pydantic model
        health_response = HealthResponse(**health_data)
        assert isinstance(health_response, HealthResponse)
