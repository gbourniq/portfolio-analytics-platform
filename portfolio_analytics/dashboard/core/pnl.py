"""
Profit and Loss calculation module for the Portfolio Analytics Dashboard.
"""

import datetime as dtm
from typing import List, Optional

import pandas as pd

from portfolio_analytics.common.utils.logging_config import setup_logger
from portfolio_analytics.dashboard.utils.dashboard_exceptions import (
    MetricsCalculationError,
)

# Configure logging
log = setup_logger(__name__)


def _validate_date_range(
    df: pd.DataFrame, start_date: Optional[dtm.date], end_date: Optional[dtm.date]
) -> None:
    """Validate the provided date range against the DataFrame's date range."""
    portfolio_start, portfolio_end = df["Date"].min(), df["Date"].max()

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


def _filter_dataframe(
    df: pd.DataFrame,
    start_date: Optional[dtm.date],
    end_date: Optional[dtm.date],
    tickers: Optional[List[str]],
) -> pd.DataFrame:
    """Apply date and ticker filters to the DataFrame."""
    filtered_df = df.copy()
    portfolio_start, portfolio_end = df["Date"].min(), df["Date"].max()

    # Apply date filters
    filtered_df = filtered_df[
        (filtered_df["Date"] >= (start_date or portfolio_start))
        & (filtered_df["Date"] <= (end_date or portfolio_end))
    ]

    # Apply ticker filter if provided
    if tickers:
        filtered_df = filtered_df[filtered_df["Ticker"].isin(tickers)]
        if filtered_df.empty:
            raise MetricsCalculationError(
                f"No data found for provided tickers: {tickers}"
            )

    return filtered_df


def calculate_pnl_expanded(
    raw_df: pd.DataFrame,
    start_date: Optional[dtm.date] = None,
    end_date: Optional[dtm.date] = None,
    tickers: Optional[List[str]] = None,
):
    """
    Filter raw dataframe based on dates and tickers, then calculate PnL raw values.
    """
    df_sorted = raw_df.copy().reset_index()

    # Calculate cumulative cash flows and PnL per ticker
    _validate_date_range(df_sorted, start_date, end_date)
    df_sorted = _filter_dataframe(df_sorted, start_date, end_date, tickers)

    df_sorted["CashFlowCumSum"] = df_sorted.groupby("Ticker")["CashFlow"].cumsum()
    df_sorted["PnL"] = df_sorted.apply(
        lambda row: row["PortfolioValues"] - row["CashFlowCumSum"], axis=1
    )

    return df_sorted


def calculate_daily_pnl(pnl_expanded: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates daily PnL given full PnL data
    """
    try:
        pnl_df = pd.DataFrame()
        pnl_df["PnL"] = pnl_expanded.groupby("Date")["PnL"].sum()
        return pnl_df

    except Exception as e:
        raise MetricsCalculationError(f"Error calculating PnL: {str(e)}") from e
