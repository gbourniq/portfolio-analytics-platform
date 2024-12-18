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
    DataValidationError,
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
    portfolio_tickers = positions_df.index.get_level_values("Ticker").unique().tolist()
    date_range = (portfolio.Date.min(), portfolio.Date.max())

    # Validate price and fx data date coverage
    error_messages = []

    price_dates = pd.read_parquet(prices_path, columns=[]).index.get_level_values("Date")
    if date_range[0] < price_dates.min() or date_range[1] > price_dates.max():
        error_messages.append(
            f"Price data coverage: [{price_dates.min()} - {price_dates.max()}]"
        )

    fx_dates = pd.read_parquet(fx_path, columns=[]).index.get_level_values("Date")
    if date_range[0] < fx_dates.min() or date_range[1] > fx_dates.max():
        error_messages.append(f"FX data coverage: [{fx_dates.min()} - {fx_dates.max()}]")

    if error_messages:
        raise DataValidationError(
            f"Portfolio date range [{date_range[0]} - {date_range[1]}] "
            f"not fully covered by market data: {', '.join(error_messages)}"
        )

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


def prepare_data(
    portfolio_path: Path,
    equity_path: Path,
    fx_path: Path,
    target_currency: Currency = Currency.USD,
) -> pd.DataFrame:
    """# noqa: E501,W505  # pylint: disable=line-too-long
    Prepares and caches raw data used to calculate PnL.
    This includes portfolio positions, trades, and FX converted
    prices, portfolio values and cash flows.

    The data is indexed on (Date, Ticker).

    Returns an expanded view of the PnL in the following shape:

    (Date, Ticker)      Positions  Trades EquityIndex      Mid  ... PortfolioValues  CashFlow
    2024-10-30  QRVO            0     0.0       SP500      121  ...        0.000000       0.0
                ROP            65     0.0       SP500      122  ...    27410.009023       0.0
                SMCI            0     0.0       SP500      120  ...        0.000000       0.0
                TSLA            0     0.0       SP500      121  ...        0.000000       0.0
                UAL             0     0.0       SP500      123  ...        0.000000       0.0
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

        df = join_positions_and_prices(positions_df, prices_df, fx_df)

        # Calculate USD-converted values
        df["PortfolioValues"] = df["Positions"] * df["MidUsd"]
        df["CashFlow"] = (df["Trades"] * df["MidUsd"]).apply(lambda x: -x if x else 0)

        # Convert to target currency if needed
        if target_currency != Currency.USD:
            fx_rates = df.groupby("Date")[f"USD{target_currency.name}=X"].first()
            df["PortfolioValues"] *= fx_rates
            df["CashFlow"] *= fx_rates

        df["Currency"] = target_currency.value

        # Drop fx columns and rename to Mid
        df = df.drop(columns=[col for col in df.columns if col.endswith("=X")])
        df = df.rename(columns={"MidUsd": "Mid"})

        log.debug(f"Prepared DataFrame: {df.head()}\n{df.tail()}")

        df.to_parquet(cache_file_path)
        return df

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

    # Forward Fill FX to cover full portfolio date ranges
    for col in combined_df.columns:
        if col.endswith("=X"):
            combined_df[col].ffill(inplace=True)

    # Edge case when first row has null values, remove it
    combined_df = combined_df[
        combined_df["Mid"].notna() & combined_df["Currency"].notna()
    ]

    # Convert prices to USD based on Currency
    def get_fx_rate(row):
        if row["Currency"] == "USD":
            return 1.0
        if row["Currency"] == "EUR":
            return row["EURUSD=X"]
        if row["Currency"] == "GBP":
            return row["GBPUSD=X"]
        raise MetricsCalculationError(f"Unsupported currency: {row['Currency']}")

    combined_df["FxRate"] = combined_df.apply(get_fx_rate, axis=1)

    # Calculate USD-converted values
    combined_df["MidUsd"] = combined_df["Mid"] * combined_df["FxRate"]

    # Drop Mid and intermediate FX rate after conversion
    combined_df = combined_df.drop(columns=["Mid", "EURUSD=X", "GBPUSD=X", "FxRate"])

    return combined_df
