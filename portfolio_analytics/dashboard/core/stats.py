"""
Performance statistics calculation module for the Portfolio Analytics Dashboard.
"""

import datetime as dtm
from dataclasses import dataclass
from typing import Tuple

import numpy as np
import pandas as pd

from portfolio_analytics.common.logging_config import setup_logger
from portfolio_analytics.dashboard.utils.dashboard_exceptions import (
    MetricsCalculationError,
)

# Configure logging
log = setup_logger(__name__)


@dataclass
class PortfolioStats:
    """Container for portfolio performance statistics."""

    max_drawdown: float
    max_drawdown_date: dtm.date
    drawdown_start_date: dtm.date
    sharpe_ratio: float
    period_pnl: float


def _calculate_drawdown(df_sorted: pd.DataFrame) -> Tuple[float, dtm.date, dtm.date]:
    """Helper function to calculate drawdown metrics.

    Calculates the maximum drawdown and its corresponding dates from a DataFrame
    containing PnL data. The drawdown represents the largest peak-to-trough decline in
    the PnL over the given period.

    Args:
        df_sorted (pd.DataFrame): A sorted DataFrame containing PnL data with
            a 'Date' column and the specified PnL column.

    Returns:
        Tuple[float, dtm.date, dtm.date]: A tuple containing:
            - max_drawdown (float): The maximum drawdown value (always positive)
            - max_drawdown_date (dtm.date): The date when the maximum drawdown occurred
            - drawdown_start_date (dtm.date): The date when the drawdown period started

    Note:
        The function assumes the input DataFrame is already sorted by date and contains
        a 'Date' column of type datetime.date.
    """
    # Calculate drawdown
    df_sorted["PnLMax"] = df_sorted["PnL"].cummax()
    df_sorted["Drawdown"] = df_sorted["PnLMax"] - df_sorted["PnL"]

    # Find maximum drawdown
    max_drawdown = df_sorted["Drawdown"].max()
    max_drawdown_idx = df_sorted["Drawdown"].idxmax()
    max_drawdown_date = df_sorted.at[max_drawdown_idx, "Date"]

    # Find drawdown start
    cumulative_max = df_sorted.at[max_drawdown_idx, "PnLMax"]
    drawdown_start_idx = df_sorted[
        (df_sorted["PnL"] == cumulative_max) & (df_sorted.index <= max_drawdown_idx)
    ].index[0]
    drawdown_start_date = df_sorted.at[drawdown_start_idx, "Date"]

    return max_drawdown, max_drawdown_date, drawdown_start_date


def calculate_stats(pnl_daily_df: pd.DataFrame) -> PortfolioStats:
    """
    Calculates performance statistics with optional date range and ticker filtering.
    """
    df_sorted = pnl_daily_df.copy()
    df_sorted.reset_index(inplace=True)

    # Calculate metrics
    max_drawdown, max_drawdown_date, drawdown_start_date = _calculate_drawdown(df_sorted)

    daily_return = df_sorted["PnL"].diff().copy()
    sharpe_ratio = (daily_return.mean() / daily_return.std()) * np.sqrt(252)

    period_pnl = df_sorted["PnL"].iloc[-1] - df_sorted["PnL"].iloc[0]

    return PortfolioStats(
        max_drawdown=max_drawdown,
        max_drawdown_date=max_drawdown_date,
        drawdown_start_date=drawdown_start_date,
        sharpe_ratio=sharpe_ratio,
        period_pnl=period_pnl,
    )


def get_winners_and_losers(
    pnl_expanded: pd.DataFrame,
    top_n: int = 5,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calculate top winners and losers based on portfolio values (unrealised PnL).

    Args:
        pnl_expanded: DataFrame containing full PnL data
        top_n: Number of top/bottom performers to return

    Returns:
        Tuple of (winners_df, losers_df)
    """
    try:

        # Calculate PnL per ticker
        pnl_expanded.sort_index(inplace=True)
        ticker_pnl = pnl_expanded.groupby("Ticker")["PnL"].last()

        # Create DataFrames for winners and losers
        winners = pd.DataFrame(
            {
                "symbol": ticker_pnl.nlargest(top_n).index,
                "pnl": ticker_pnl.nlargest(top_n).values,
            }
        )

        losers = pd.DataFrame(
            {
                "symbol": ticker_pnl.nsmallest(top_n).index,
                "pnl": ticker_pnl.nsmallest(top_n).values,
            }
        )

        return winners, losers

    except Exception as e:
        raise MetricsCalculationError(
            f"Error calculating winners and losers: {str(e)}"
        ) from e
