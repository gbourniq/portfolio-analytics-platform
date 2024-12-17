"""
Performance statistics calculation module for the Portfolio Analytics Dashboard.
"""

import datetime as dtm
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from portfolio_analytics.common.utils.logging_config import setup_logger
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


def calculate_stats(
    pnl_df: pd.DataFrame,
    use_realized: bool = True,
    start_date: Optional[dtm.date] = None,
    end_date: Optional[dtm.date] = None,
    tickers: Optional[List[str]] = None,
) -> PortfolioStats:
    """
    Calculates performance statistics with optional date range and ticker filtering.

    Args:
        pnl_df: DataFrame containing PnL data
        use_realized: If True, uses realized PnL, otherwise uses unrealized PnL
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        tickers: Optional list of tickers for filtering

    Returns:
        PortfolioStats object containing performance metrics
    """
    df_sorted = pnl_df.copy()
    df_sorted.reset_index(inplace=True)

    pnl_column = "pnl_realised" if use_realized else "pnl_unrealised"

    # Validate and apply date filters
    portfolio_start, portfolio_end = df_sorted["Date"].min(), df_sorted["Date"].max()

    if start_date and end_date and start_date > end_date:
        raise MetricsCalculationError(
            f"Start date {start_date} is after end date {end_date}"
        )

    if (start_date and start_date < portfolio_start) or (
        end_date and end_date > portfolio_end
    ):
        raise MetricsCalculationError(
            f"Date range [{start_date or portfolio_start} -"
            f" {end_date or portfolio_end}] outside portfolio range"
            f" [{portfolio_start} - {portfolio_end}]"
        )

    # Apply date filters if provided
    df_sorted = df_sorted[
        (df_sorted["Date"] >= (start_date or portfolio_start))
        & (df_sorted["Date"] <= (end_date or portfolio_end))
    ]

    # Apply ticker filter if provided
    if tickers:
        df_sorted = df_sorted[df_sorted["Ticker"].isin(tickers)]
        if df_sorted.empty:
            raise MetricsCalculationError(
                f"No data found for provided tickers: {tickers}"
            )

    # Calculate drawdown
    df_sorted["pnl_max"] = df_sorted[pnl_column].cummax()
    df_sorted["drawdown"] = df_sorted["pnl_max"] - df_sorted[pnl_column]

    # Find maximum drawdown
    max_drawdown = df_sorted["drawdown"].max()
    max_drawdown_idx = df_sorted["drawdown"].idxmax()
    max_drawdown_date = df_sorted.at[max_drawdown_idx, "Date"]

    # Find drawdown start
    cumulative_max = df_sorted.at[max_drawdown_idx, "pnl_max"]
    drawdown_start_idx = df_sorted[
        (df_sorted[pnl_column] == cumulative_max)
        & (df_sorted.index <= max_drawdown_idx)
    ].index[0]
    drawdown_start_date = df_sorted.at[drawdown_start_idx, "Date"]

    # Calculate sharpe ratio
    daily_return = df_sorted[pnl_column].diff().copy()
    sharpe_ratio = (daily_return.mean() / daily_return.std()) * np.sqrt(252)

    # Get the starting and ending values for the period
    period_start_value = df_sorted[pnl_column].iloc[0]
    period_end_value = df_sorted[pnl_column].iloc[-1]
    period_pnl = period_end_value - period_start_value

    return PortfolioStats(
        max_drawdown=max_drawdown,
        max_drawdown_date=max_drawdown_date,
        drawdown_start_date=drawdown_start_date,
        sharpe_ratio=sharpe_ratio,
        period_pnl=period_pnl,
    )


def get_winners_and_losers(
    positions_prices_df: pd.DataFrame,
    start_date: Optional[dtm.date] = None,
    end_date: Optional[dtm.date] = None,
    top_n: int = 5,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calculate top winners and losers based on portfolio values (unrealised PnL).

    Args:
        positions_prices_df: DataFrame containing portfolio positions and their values
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        top_n: Number of top/bottom performers to return

    Returns:
        Tuple of (winners_df, losers_df)
    """
    try:
        # Filter by date if provided
        df = positions_prices_df.copy()
        if start_date or end_date:
            dates = pd.to_datetime(df.index.get_level_values("Date")).date
            df = df[
                (dates >= (start_date or dates.min()))
                & (dates <= (end_date or dates.max()))
            ]

        # Calculate PnL per ticker
        ticker_pnl = df.groupby("Ticker")["PortfolioValues"].sum()

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
