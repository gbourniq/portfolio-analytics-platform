"""
Tests for the Portfolio Analytics Dashboard main functionality
"""

import datetime as dtm
from pathlib import Path

import pytest

from portfolio_analytics.common.utils.instruments import Currency
from portfolio_analytics.dashboard.dashboard_main import (
    _handle_button_styles,
    _handle_date_range,
    app,
)


class TestDashboardMain:
    """Tests for dashboard main functionality"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup method for dashboard tests"""
        self.app = app
        # Create a mock context instead of using the real one
        self.ctx = type("MockContext", (), {"triggered": []})()

    @pytest.mark.parametrize(
        "trigger_source, date_picker_style, expected_active",
        [
            ("portfolio-selector", {"display": "none"}, "max-button"),
            ("currency-selector", {"display": "none"}, "max-button"),
            ("1m-button", {"display": "none"}, "1m-button"),
            ("custom-button", {"display": "block"}, "custom-button"),
        ],
    )
    def test_handle_button_styles(
        self, trigger_source, date_picker_style, expected_active
    ):
        """Test button style handling based on different triggers"""
        # Given: Set up a mock context with a specific trigger source
        # This simulates a user clicking different buttons in the dashboard
        # (portfolio selector, currency selector, 1-month button, or custom date button)
        self.ctx.triggered = [{"prop_id": f"{trigger_source}.value"}]

        # When: Call the button style handler with our mock context
        # This function determines how buttons should appear (active/inactive)
        # based on which button was clicked
        button_styles = _handle_button_styles(
            self.ctx, date_picker_style, trigger_source
        )

        # Then: Verify the clicked button has the correct "active" styling
        # The active button should have a dark blue background (#2C3E50)
        # and white text to indicate it's selected
        assert button_styles[expected_active] == {
            "background-color": "#2C3E50",
            "color": "white",
            "border-color": "#2C3E50",
        }

    @pytest.mark.parametrize(
        "button_id, current_date, expected_range",
        [
            (
                "1m-button",
                dtm.date(2024, 2, 1),
                (dtm.date(2024, 1, 1), dtm.date(2024, 2, 1)),
            ),
            (
                "max-button",
                dtm.date(2024, 2, 1),
                (dtm.date(2023, 1, 1), dtm.date(2024, 12, 31)),
            ),
        ],
    )
    def test_handle_date_range(
        self, monkeypatch, button_id, current_date, expected_range
    ):
        """Test date range calculation for different button triggers"""
        # Given: Set up a mock datetime to ensure consistent test results
        # We fix the current date and create a mock datetime object
        # This helps test date calculations predictably
        mock_dt = dtm.datetime.combine(current_date, dtm.time())
        MockDatetime = type(
            "MockDatetime",
            (),
            {
                "now": staticmethod(lambda: mock_dt),
                "combine": staticmethod(dtm.datetime.combine),
            },
        )
        monkeypatch.setattr(
            "portfolio_analytics.dashboard.dashboard_main.dtm.datetime", MockDatetime
        )
        # Set up the button click trigger (either 1-month or max range button)
        self.ctx.triggered = [{"prop_id": f"{button_id}.n_clicks"}]
        min_date = dtm.date(2023, 1, 1)
        max_date = dtm.date(2024, 12, 31)

        # When: Call the date range handler
        # This function calculates the appropriate date range based on
        # which button was clicked (1m shows last month, max shows full range)
        start_date, end_date, _ = _handle_date_range(
            self.ctx, min_date, max_date, min_date, max_date
        )

        # Then: Verify the calculated date range matches expectations
        # For 1m button: should return (first day of previous month, current date)
        # For max button: should return (min_date, max_date)
        assert (start_date, end_date) == expected_range

    def test_update_graph_error_handling(self, monkeypatch):
        """Test graph update error handling"""

        # Given: Set up a mock data preparation function that raises an error
        # This simulates what happens when data processing fails
        def mock_prepare_data(*args, **kwargs):
            raise ValueError("Test error")

        monkeypatch.setattr(
            "portfolio_analytics.dashboard.dashboard_main.prepare_data",
            mock_prepare_data,
        )

        # When: Attempt to update the graph with our mocked function
        # This simulates a graph update with invalid/problematic data
        mock_callback = self.app.callback_map.get("graph.figure", {}).get(
            "callback", None
        )
        if not mock_callback:
            pytest.skip("Callback not registered - test not applicable")

        result = mock_callback(
            Path("test.csv"),
            dtm.date(2024, 1, 1),
            dtm.date(2024, 2, 1),
            Currency.USD.name,
            None,
            None,
            None,
            None,
            None,
            None,
        )

        # Then: Verify the error is properly captured in the result
        # The error message should be included in the graph's output
        # to inform the user about the failure
        assert "Test error" in str(result)
