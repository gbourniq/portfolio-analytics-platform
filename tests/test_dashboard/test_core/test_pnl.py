"""Unit tests for PnL calculation module."""

from typing import List

import pandas as pd
import pytest

from portfolio_analytics.dashboard.core.pnl import (
    _filter_dataframe,
    _validate_date_range,
    calculate_daily_pnl,
    calculate_pnl,
)
from portfolio_analytics.dashboard.utils.dashboard_exceptions import (
    MetricsCalculationError,
)


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Provides a sample DataFrame for testing."""
    return pd.DataFrame(
        {
            "Date": pd.date_range("2023-01-01", "2023-01-03"),
            "Ticker": ["AAPL", "GOOGL", "AAPL"],
            "Positions": [100, 200, 150],
            "Trades": [100, 200, 50],
            "MidUsd": [100, 200, 150],
            "PortfolioValues": [100, 200, 150],
            "CashFlow": [100, 200, 50],
        }
    )


class TestValidateDateRange:
    """Tests for date range validation function."""

    @pytest.mark.parametrize(
        "start_date,end_date,should_raise",
        [
            (pd.Timestamp("2023-01-02"), pd.Timestamp("2023-01-01"), True),
            (pd.Timestamp("2022-12-31"), pd.Timestamp("2023-01-03"), True),
            (pd.Timestamp("2023-01-01"), pd.Timestamp("2023-01-04"), True),
            (pd.Timestamp("2023-01-01"), pd.Timestamp("2023-01-03"), False),
        ],
    )
    def test_date_range_validation(
        self,
        sample_df: pd.DataFrame,
        start_date: pd.Timestamp,
        end_date: pd.Timestamp,
        should_raise: bool,
    ):
        """Tests date range validation with various inputs."""
        # Given
        df = sample_df

        # When/Then
        if should_raise:
            with pytest.raises(MetricsCalculationError):
                _validate_date_range(df, start_date, end_date)
        else:
            _validate_date_range(df, start_date, end_date)


class TestFilterDataframe:
    """Tests for DataFrame filtering function."""

    @pytest.mark.parametrize(
        "tickers,expected_rows",
        [
            (["AAPL"], 2),
            (["GOOGL"], 1),
            (["AAPL", "GOOGL"], 3),
            (None, 3),
        ],
    )
    def test_ticker_filtering(
        self, sample_df: pd.DataFrame, tickers: List[str], expected_rows: int
    ):
        """Tests filtering DataFrame by tickers."""
        # Given
        df = sample_df

        # When
        filtered_df = _filter_dataframe(df, None, None, tickers)

        # Then
        assert len(filtered_df) == expected_rows

    def test_invalid_ticker_filter(self, sample_df: pd.DataFrame):
        """Tests filtering with non-existent ticker."""
        # Given
        df = sample_df
        invalid_tickers = ["INVALID"]

        # When/Then
        with pytest.raises(MetricsCalculationError):
            _filter_dataframe(df, None, None, invalid_tickers)


class TestCalculatePnL:
    """Tests for expanded PnL calculation."""

    def test_pnl_calculation(self, monkeypatch, tmp_path, sample_df: pd.DataFrame):
        """Tests basic PnL calculation."""
        # Given
        df = sample_df
        monkeypatch.setattr(
            "portfolio_analytics.dashboard.core.pnl.CACHE_DIR",
            tmp_path,
        )

        # When
        result = calculate_pnl(df)

        # Then
        assert "PnL" in result.columns
        assert len(result) == len(df)


class TestCalculateDailyPnL:
    """Tests for daily PnL calculation."""

    def test_daily_pnl_aggregation(self, monkeypatch, tmp_path, sample_df: pd.DataFrame):
        """Tests aggregation of PnL values by date."""
        # Given
        monkeypatch.setattr(
            "portfolio_analytics.dashboard.core.pnl.CACHE_DIR",
            tmp_path,
        )
        expanded_pnl = calculate_pnl(sample_df)

        # When
        daily_pnl = calculate_daily_pnl(expanded_pnl)

        # Then
        assert isinstance(daily_pnl, pd.DataFrame)
        assert len(daily_pnl) == len(sample_df["Date"].unique())

    def test_calculation_error_handling(
        self, monkeypatch, tmp_path, sample_df: pd.DataFrame
    ):
        """Tests error handling in daily PnL calculation."""
        # Given
        monkeypatch.setattr(
            "portfolio_analytics.dashboard.core.pnl.CACHE_DIR",
            tmp_path,
        )

        expanded_pnl = calculate_pnl(sample_df)
        invalid_df = expanded_pnl.drop(columns=["PnL"])

        # When/Then
        with pytest.raises(MetricsCalculationError):
            calculate_daily_pnl(invalid_df)
