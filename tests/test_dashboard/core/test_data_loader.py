"""
Data loading and caching module for portfolio analytics calculations.

Handles loading and preprocessing of portfolio, price, and FX data with caching
to enable efficient recalculation of PnL and performance metrics using different
filters without reprocessing raw data.
"""

from pathlib import Path
from typing import Tuple

import pandas as pd

from portfolio_analytics.common.utils.filesystem import CACHE_DIR, read_portfolio_file
from portfolio_analytics.common.utils.instruments import Currency
from portfolio_analytics.common.utils.logging_config import setup_logger
from portfolio_analytics.dashboard.utils.cache_utils import generate_cache_key
from portfolio_analytics.dashboard.utils.dashboard_exceptions import (
    MetricsCalculationError,
    MissingTickersException,
)

# Configure logging
log = setup_logger(__name__)


def validate_and_load(
    holdings_path: Path, prices_path: Path, fx_path: Path
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Loads and validates portfolio, price, and FX data.

    Returns:
        Tuple of (positions_df, prices_df, fx_df)
    """
    try:
        # Load portfolio
        portfolio = read_portfolio_file(
            content=holdings_path.read_bytes(), file_extension=holdings_path.suffix
        )
        portfolio["Date"] = pd.to_datetime(portfolio["Date"]).dt.date

        # Reshape portfolio
        positions_df = portfolio.melt(
            id_vars="Date", var_name="Ticker", value_name="Positions"
        )
        positions_df.set_index(["Date", "Ticker"], inplace=True)
        positions_df.sort_index(inplace=True)

        # Get portfolio metadata
        portfolio_tickers = (
            positions_df.index.get_level_values("Ticker").unique().tolist()
        )
        date_range = (portfolio.Date.min(), portfolio.Date.max())

        # Load and filter price data with date filters for efficiency
        filters = [
            ("Date", ">=", date_range[0]),
            ("Date", "<=", date_range[1]),
        ]
        prices_df = pd.read_parquet(prices_path, filters=filters)
        fx_df = pd.read_parquet(fx_path, filters=filters)

        # Validate tickers
        available_tickers = prices_df.index.get_level_values("Ticker").unique()
        missing_tickers = [t for t in portfolio_tickers if t not in available_tickers]
        if missing_tickers:
            raise MissingTickersException(missing_tickers, list(available_tickers))

        # Validate FX data covers portfolio dates
        fx_dates = fx_df.index.get_level_values("Date")
        if date_range[0] < fx_dates.min() or date_range[1] > fx_dates.max():
            raise MetricsCalculationError(
                f"Portfolio date range [{date_range[0]} - {date_range[1]}] not fully"
                f" covered by FX data coverage [{fx_dates.min()} - {fx_dates.max()}]"
            )

        # Filter prices to portfolio date range and tickers
        prices_df = prices_df[
            (prices_df.index.get_level_values("Date") >= date_range[0])
            & (prices_df.index.get_level_values("Date") <= date_range[1])
            & (prices_df.index.get_level_values("Ticker").isin(portfolio_tickers))
        ]

        # Filter FX data to portfolio date range
        fx_df = fx_df[
            (fx_df.index.get_level_values("Date") >= date_range[0])
            & (fx_df.index.get_level_values("Date") <= date_range[1])
        ]

        return positions_df, prices_df, fx_df

    except Exception as e:
        raise MetricsCalculationError(f"Error loading data: {str(e)}") from e


def prepare_positions_prices_data(
    portfolio_path: Path,
    equity_path: Path,
    fx_path: Path,
    target_currency: Currency = Currency.USD,
) -> pd.DataFrame:
    """
    Prepares and caches raw data, including portfolio positions,
    trades, and FX converted portfolio values and cash flows.
    """
    try:
        # Create cache directory if it doesn't exist
        CACHE_DIR.mkdir(exist_ok=True)

        # Generate cache key and construct cache file path
        cache_key = generate_cache_key(
            portfolio_path, equity_path, fx_path, target_currency
        )

        # Return cached data if it exists
        if (cache_file_path := CACHE_DIR / f"{cache_key}.parquet").exists():
            return pd.read_parquet(cache_file_path)

        # If no cache exists or loading failed, load and prepare the data
        positions_df, prices_df, fx_df = validate_and_load(
            portfolio_path, equity_path, fx_path
        )

        prepared_data = join_positions_and_prices(positions_df, prices_df, fx_df)

        # Convert to target currency if needed
        if target_currency != Currency.USD:
            fx_rates = prepared_data.groupby("Date")[
                f"USD{target_currency.name}=X"
            ].first()
            prepared_data["PortfolioValues"] *= fx_rates
            prepared_data["CashFlow"] *= fx_rates

        prepared_data.to_parquet(cache_file_path)
        return prepared_data

    except Exception as e:
        raise MetricsCalculationError(str(e)) from e


def join_positions_and_prices(
    positions_df: pd.DataFrame, prices_df: pd.DataFrame, fx_df: pd.DataFrame
) -> pd.DataFrame:
    """Prepares position data with trades and joins with prices,
    and calculating USD-converted portfolio values and cash flows."""

    # Prepare price data with complete date range
    holdings_dates = positions_df.index.get_level_values("Date").unique()
    tickers = prices_df.index.get_level_values("Ticker").unique()
    multi_index = pd.MultiIndex.from_product(
        [holdings_dates, tickers],
        names=["Date", "Ticker"],
    )
    prices_df = prices_df.reindex(multi_index).groupby("Ticker").ffill()

    # Process positions
    positions_sorted = positions_df.copy()
    positions_sorted = positions_sorted.sort_index(level=["Date", "Ticker"])
    positions_sorted["Trades"] = positions_sorted.groupby("Ticker")["Positions"].diff()

    # Set initial trades to 0
    first_date = positions_sorted.index.get_level_values("Date").min()
    positions_sorted.loc[
        positions_sorted.index.get_level_values("Date") == first_date, "Trades"
    ] = 0.0

    # Join with prices
    combined_df = positions_sorted.join(prices_df)

    # Join with FX rates - only select needed columns
    fx_df.reset_index(inplace=True)
    fx_pivot = fx_df.pivot(index="Date", columns="Ticker", values="Mid")[
        ["EURUSD=X", "GBPUSD=X", "USDEUR=X", "USDGBP=X"]
    ]
    combined_df = combined_df.join(fx_pivot, on="Date")

    # Edge case when first row has null values, remove it
    combined_df = combined_df[
        combined_df["Mid"].notna() & combined_df["Currency"].notna()
    ]

    # Convert prices to USD based on Currency
    def get_fx_rate(row):
        if row["Currency"] == "USD":
            return 1.0
        elif row["Currency"] == "EUR":
            return row["EURUSD=X"]
        elif row["Currency"] == "GBP":
            return row["GBPUSD=X"]
        else:
            raise MetricsCalculationError(f"Unsupported currency: {row['Currency']}")

    combined_df["FxRate"] = combined_df.apply(get_fx_rate, axis=1)

    # Calculate USD-converted values
    combined_df["MidUsd"] = combined_df["Mid"] * combined_df["FxRate"]

    # Drop intermediate FX rate after conversion
    combined_df = combined_df.drop(columns=["EURUSD=X", "GBPUSD=X", "FxRate"])

    # Calculate USD-converted values
    combined_df["PortfolioValues"] = combined_df["Positions"] * combined_df["MidUsd"]
    combined_df["CashFlow"] = (combined_df["Trades"] * combined_df["MidUsd"]).apply(
        lambda x: 0 if x == 0 else -x
    )

    log.info(f"Combined DataFrame: {combined_df.head()}\n{combined_df.tail()}")

    return combined_df
