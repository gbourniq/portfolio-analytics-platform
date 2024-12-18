"""
Tests for portfolio performance statistics calculations
"""

import datetime as dtm

import numpy as np
import pandas as pd
import pytest

from portfolio_analytics.dashboard.core.stats import (
    PortfolioStats,
    _calculate_drawdown,
    calculate_stats,
    get_winners_and_losers,
)
from portfolio_analytics.dashboard.utils.dashboard_exceptions import (
    MetricsCalculationError,
)


class TestStats:
    """Tests for portfolio statistics calculations"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup method for stats tests"""
        self.sample_df = pd.DataFrame(
            {
                "Date": pd.date_range(start="2023-01-01", periods=5).date,
                "PnL": [100, 120, 90, 110, 130],
            }
        )

    def test_calculate_drawdown(self):
        """Test drawdown calculation for a simple PnL series"""
        # Given
        df = self.sample_df.copy()

        # When
        max_dd, max_dd_date, dd_start_date = _calculate_drawdown(df)

        # Then
        assert max_dd == 30
        assert max_dd_date == dtm.date(2023, 1, 3)
        assert dd_start_date == dtm.date(2023, 1, 2)

    @pytest.mark.parametrize(
        "pnl_values, expected_sharpe",
        [
            (
                [100, 112, 118, 132, 140],
                np.float64(43.47413023856832),
            ),  # Generally increasing with variance
            (
                [100, 88, 82, 68, 60],
                np.float64(-43.47413023856832),
            ),  # Generally decreasing with variance
        ],
    )
    def test_calculate_stats_sharpe_ratio(self, pnl_values, expected_sharpe):
        """Test Sharpe ratio calculation for different PnL patterns"""
        # Given
        df = pd.DataFrame(
            {
                "Date": pd.date_range(start="2023-01-01", periods=5).date,
                "PnL": pnl_values,
            }
        )

        # When
        stats = calculate_stats(df)

        # Then
        np.testing.assert_almost_equal(stats.sharpe_ratio, expected_sharpe, decimal=2)

    def test_calculate_stats_period_pnl(self):
        """Test period PnL calculation"""
        # Given
        df = self.sample_df.copy()

        # When
        stats = calculate_stats(df)

        # Then
        assert stats.period_pnl == 30

    @pytest.mark.parametrize(
        "top_n, expected_winners, expected_losers",
        [
            (2, ["AAPL", "MSFT"], ["GME", "AMC"]),
        ],
    )
    def test_get_winners_and_losers(self, top_n, expected_winners, expected_losers):
        """Test winners and losers calculation for different top_n values"""
        # Given
        df = pd.DataFrame(
            {
                "Date": ["2023-01-01"] * 4,
                "Ticker": ["AAPL", "MSFT", "GME", "AMC"],
                "PnL": [100, 50, -50, -100],
            }
        )

        # When
        winners, losers = get_winners_and_losers(df, top_n)

        # Then
        assert sorted(winners["symbol"].tolist()) == sorted(expected_winners)
        assert sorted(losers["symbol"].tolist()) == sorted(expected_losers)

    def test_get_winners_and_losers_error_handling(self):
        """Test error handling in winners and losers calculation"""
        # Given
        invalid_df = pd.DataFrame()

        # When/Then
        with pytest.raises(MetricsCalculationError):
            get_winners_and_losers(invalid_df)

    def test_portfolio_stats_dataclass(self):
        """Test PortfolioStats dataclass initialization"""
        # Given
        test_date = dtm.date(2023, 1, 1)

        # When
        stats = PortfolioStats(
            max_drawdown=10.0,
            max_drawdown_date=test_date,
            drawdown_start_date=test_date,
            sharpe_ratio=2.0,
            period_pnl=100.0,
        )

        # Then
        assert stats.max_drawdown == 10.0
        assert stats.sharpe_ratio == 2.0
