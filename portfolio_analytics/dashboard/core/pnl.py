"""
Profit and Loss calculation module for the Portfolio Analytics Dashboard.
"""

import datetime as dtm
from typing import List, Optional

import pandas as pd

from portfolio_analytics.common.utils.instruments import Currency
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
    target_currency: Currency = Currency.USD,
):
    """
    Filter raw dataframe based on dates and tickers, then calculate PnL raw values.
    """
    df = raw_df.copy().reset_index()

    # Calculate cumulative cash flows and PnL per ticker
    _validate_date_range(df, start_date, end_date)
    df = _filter_dataframe(df, start_date, end_date, tickers)

    # Convert to target currency if needed
    if target_currency != Currency.USD:
        df["MidUsd"] *= df[f"USD{target_currency.name}=X"]
    df["Currency"] = target_currency.value

    # Drop fx columns and rename to Mid
    df = df.drop(columns=[col for col in df.columns if col.endswith("=X")])
    df = df.rename(columns={"MidUsd": "Mid"})

    # Consider positions at t0 as 0
    df.loc[df.groupby("Ticker").head(1).index, "Positions"] = 0
    df["Trades"] = df.groupby("Ticker")["Positions"].diff()
    df["PortfolioValues"] = df["Positions"] * df["Mid"]
    df["CashFlow"] = (df["Trades"] * df["Mid"]).apply(lambda x: -x if x else 0)

    # Calculate cumulative cash flows and PnL per ticker
    df["CashFlowCumSum"] = df.groupby("Ticker")["CashFlow"].cumsum()
    df["PnL"] = df.apply(
        lambda row: row["PortfolioValues"] + row["CashFlowCumSum"], axis=1
    )

    return df


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
