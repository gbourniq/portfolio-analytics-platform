"""Unit tests for dashboard exceptions."""

import pytest

from portfolio_analytics.dashboard.utils.dashboard_exceptions import (
    MissingTickersException,
)


class TestMissingTickersException:
    """Test suite for MissingTickersException class."""

    @pytest.mark.parametrize(
        "missing_tickers,available_tickers,expected_message",
        [
            (
                ["AAPL", "GOOGL"],
                ["MSFT", "AMZN"],
                "The following tickers are missing from price data: AAPL, GOOGL.\n",
            ),
            (
                ["APPL"],  # Misspelled AAPL
                ["AAPL", "MSFT"],
                (
                    "The following tickers are missing from price data: APPL.\n\nDid you"
                    " mean? APPL → AAPL"
                ),
            ),
        ],
    )
    def test_missing_tickers_exception_message(
        self, missing_tickers, available_tickers, expected_message
    ):
        """Test exception message formatting with and without suggestions."""
        # Given
        # Parameters provided by pytest.mark.parametrize

        # When
        exception = MissingTickersException(missing_tickers, available_tickers)

        # Then
        assert str(exception) == expected_message

    def test_missing_tickers_exception_attributes(self):
        """Test exception attributes are correctly stored."""
        # Given
        missing_tickers = ["AAPL", "GOOGL"]
        available_tickers = ["MSFT", "AMZN"]

        # When
        exception = MissingTickersException(missing_tickers, available_tickers)

        # Then
        assert exception.missing_tickers == missing_tickers
        assert exception.available_tickers == available_tickers
