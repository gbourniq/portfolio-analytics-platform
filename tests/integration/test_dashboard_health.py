# """Integration tests for Dashboard functionality.

# These tests verify end-to-end functionality of the Dashboard
# when running in a containerized environment.
# """

# from http import HTTPStatus

# import pytest
# import requests
# from dash.testing.application_runners import import_app
# from dash.testing.composite import DashComposite

# # Configuration
# DASHBOARD_URL = "http://localhost:8050"
# HEADERS = {"Accept": "application/json"}


# @pytest.fixture(scope="module")
# def dashboard_client() -> DashComposite:
#     """Create a Dash testing client."""
#     try:
#         # Verify dashboard is accessible
#         response = requests.get(f"{DASHBOARD_URL}")
#         response.raise_for_status()
#     except requests.RequestException as e:
#         pytest.skip(f"Dashboard not available at {DASHBOARD_URL}: {str(e)}")

#     # Import the Dash app
#     app = import_app("portfolio_analytics.dashboard.dashboard_main")
#     return DashComposite(app.server, browser="chrome")


# @pytest.mark.integration
# class TestDashboardHealth:
#     """Test Dashboard health and core functionality."""

#     def test_dashboard_loads(self, dashboard_client: DashComposite) -> None:
#         """Test that the dashboard loads successfully."""
#         # When
#         dashboard_client.server_url = DASHBOARD_URL
#         response = requests.get(DASHBOARD_URL)

#         # Then
#         assert response.status_code == HTTPStatus.OK
#         assert "Portfolio Analytics Dashboard" in response.text

#     def test_portfolio_selector(self, dashboard_client: DashComposite) -> None:
#         """Test portfolio selector dropdown functionality."""
#         # Given
#         dashboard_client.wait_for_element("#portfolio-selector")

#         # When
#         options = dashboard_client.find_element("#portfolio-selector").get_property(
#             "options"
#         )

#         # Then
#         assert len(options) > 0  # At least one portfolio should be available
#         assert all(isinstance(opt["value"], str) for opt in options)
#         assert all(isinstance(opt["label"], str) for opt in options)

#     def test_date_range_controls(self, dashboard_client: DashComposite) -> None:
#         """Test date range control buttons."""
#         # Given
#         buttons = ["1m-button", "6m-button", "1y-button", "max-button", "custom-button"]

#         # Then
#         for button_id in buttons:
#             button = dashboard_client.find_element(f"#{button_id}")
#             assert button is not None
#             assert button.get_property("style")  # Should have styling

#     def test_currency_selector(self, dashboard_client: DashComposite) -> None:
#         """Test currency selector functionality."""
#         # Given
#         dashboard_client.wait_for_element("#currency-selector")

#         # When
#         options = dashboard_client.find_element("#currency-selector").get_property(
#             "options"
#         )

#         # Then
#         expected_currencies = {"USD", "EUR", "GBP"}
#         actual_currencies = {opt["value"] for opt in options}
#         assert expected_currencies.issubset(actual_currencies)

#     def test_graph_updates(self, dashboard_client: DashComposite) -> None:
#         """Test that the graph updates when controls change."""
#         # Given
#         dashboard_client.wait_for_element("#pnl-graph")
#         initial_figure = dashboard_client.find_element("#pnl-graph").get_property(
#             "figure"
#         )

#         # When - Change time range to 1 month
#         dashboard_client.find_element("#1m-button").click()
#         dashboard_client.wait_for_element("#pnl-graph")
#         updated_figure = dashboard_client.find_element("#pnl-graph").get_property(
#             "figure"
#         )

#         # Then
#         assert initial_figure != updated_figure  # Graph should update

#     def test_stats_display(self, dashboard_client: DashComposite) -> None:
#         """Test that performance statistics are displayed."""
#         # Given
#         dashboard_client.wait_for_element("#stats-display")

#         # When
#         stats_element = dashboard_client.find_element("#stats-display")

#         # Then
#         assert stats_element is not None
#         stats_text = stats_element.text
#         assert any(metric in stats_text for metric in ["Drawdown", "Sharpe", "P&L"])

#     def test_error_handling(self, dashboard_client: DashComposite) -> None:
#         """Test dashboard error handling with invalid inputs."""
#         # Given - Try to select a non-existent portfolio
#         dashboard_client.wait_for_element("#portfolio-selector")

#         # When - Set an invalid value
#         with pytest.raises(Exception):  # Should handle the error gracefully
#             dashboard_client.select_dcc_dropdown(
#                 "#portfolio-selector", "non_existent_portfolio.csv"
#             )

#         # Then - Should show error message
#         error_message = dashboard_client.wait_for_contains_text("Error")
#         assert error_message is not None


# if __name__ == "__main__":
#     pytest.main([__file__, "-v"])
