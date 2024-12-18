"""Tests for the FastAPI application main module."""

import os
from http import HTTPStatus
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from portfolio_analytics.api.api_main import _run_dev_server, app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestAPIMain:
    """Tests for FastAPI application setup and configuration."""

    def test_root_redirect(self, client):
        """Test root endpoint redirects to docs."""
        # Given/When
        response = client.get("/")

        # Then
        assert response.status_code == HTTPStatus.OK
        assert response.history[0].status_code == HTTPStatus.TEMPORARY_REDIRECT

    def test_cors_configuration(self):
        """Test CORS middleware configuration."""
        # Given/When
        cors_middleware = next(
            m for m in app.user_middleware if m.cls.__name__ == "CORSMiddleware"
        )

        # Then
        assert cors_middleware.kwargs["allow_origins"] == ["*"]
        assert cors_middleware.kwargs["allow_methods"] == ["*"]
        assert cors_middleware.kwargs["allow_headers"] == ["*"]

    @pytest.mark.parametrize(
        "route_path,expected_name",
        [
            ("/health", ""),
            ("/portfolio", ""),
            ("/market_data/fx", ""),
            ("/market_data/equity", ""),
        ],
    )
    def test_route_names_are_empty(self, route_path, expected_name):
        """Test route names are cleared for Swagger docs."""
        # Given/When
        matching_routes = [r for r in app.routes if r.path == route_path]
        assert matching_routes, f"Route {route_path} not found in app.routes"
        route = matching_routes[0]

        # Then
        assert route.name == expected_name

    def test_dev_server_configuration(self, monkeypatch):
        """Test development server configuration."""
        # Given
        mock_uvicorn = Mock()
        monkeypatch.setattr("uvicorn.run", mock_uvicorn)
        os.environ["PORT"] = "8080"

        # When
        _run_dev_server()

        # Then
        mock_uvicorn.assert_called_once_with(
            "portfolio_analytics.api.api_main:app",
            host="0.0.0.0",
            port=8080,
            reload=True,
        )

    def test_dev_server_default_port(self, monkeypatch):
        """Test development server uses default port when not specified."""
        # Given
        mock_uvicorn = Mock()
        monkeypatch.setattr("uvicorn.run", mock_uvicorn)
        if "PORT" in os.environ:
            del os.environ["PORT"]

        # When
        _run_dev_server()

        # Then
        mock_uvicorn.assert_called_once_with(
            "portfolio_analytics.api.api_main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
        )

    def test_registered_routers(self):
        """Test all required routers are registered."""
        # Given/When
        router_paths = {route.path for route in app.routes}

        # Then
        expected_paths = {
            "/health",
            "/portfolio",
            "/portfolio/download",
            "/portfolio/download/{filename}",
            "/market_data/fx",
            "/market_data/equity",
        }
        assert expected_paths.issubset(router_paths)
