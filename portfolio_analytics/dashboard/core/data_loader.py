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
from portfolio_analytics.common.utils.logging_config import setup_logger
from portfolio_analytics.dashboard.utils.cache_utils import (
    generate_cache_key_prepared_data,
)
from portfolio_analytics.dashboard.utils.dashboard_exceptions import (
    DataValidationError,
    MetricsCalculationError,
    MissingTickersException,
)

# Configure logging
log = setup_logger(__name__)


def _validate_and_load(
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

    # Load the index information once for both date and ticker validation
    price_index = pd.read_parquet(prices_path, columns=[]).index
    price_dates = price_index.get_level_values("Date")
    available_tickers = price_index.get_level_values("Ticker").unique()
    fx_dates = pd.read_parquet(fx_path, columns=[]).index.get_level_values("Date")

    # Date validation
    if date_range[0] < price_dates.min() or date_range[1] > price_dates.max():
        error_messages.append(
            f"Price data coverage: [{price_dates.min()} - {price_dates.max()}]"
        )

    if date_range[0] < fx_dates.min() or date_range[1] > fx_dates.max():
        error_messages.append(f"FX data coverage: [{fx_dates.min()} - {fx_dates.max()}]")

    if error_messages:
        raise DataValidationError(
            f"Portfolio date range [{date_range[0]} - {date_range[1]}] "
            f"not fully covered by market data: {', '.join(error_messages)}"
        )

    # Validate tickers
    missing_tickers = [t for t in portfolio_tickers if t not in available_tickers]
    if missing_tickers:
        raise MissingTickersException(missing_tickers, list(available_tickers))

    # Load and filter price data with date and ticker filters for efficiency
    filters = [
        ("Date", ">=", date_range[0]),
        ("Date", "<=", date_range[1]),
        ("Ticker", "in", portfolio_tickers),
    ]
    prices_df = pd.read_parquet(prices_path, filters=filters)
    fx_df = pd.read_parquet(fx_path, filters=filters[:2])  # Only date filters for FX

    return positions_df, prices_df, fx_df


def prepare_data(portfolio_path: Path, equity_path: Path, fx_path: Path) -> pd.DataFrame:
    """# noqa: E501,W505  # pylint: disable=line-too-long
    Prepares and caches raw data used to calculate PnL.
    This includes USD-converted prices for the full portfolio date range
    as well as additional FX rates to convert the PnL to a target currency.

    The data is indexed on (Date, Ticker).

    Returns an expanded view of the PnL in the following shape:

                        Positions  Trades EquityIndex Currency                  CreatedAt  USDEUR=X  USDGBP=X      MidUsd
    Date       Ticker
    2024-08-30  AAPL            0     0.0       SP500      USD 2024-12-16 15:10:12.910032  0.902950   0.75966  228.688398
                ABBV            0     0.0       SP500      USD 2024-12-16 15:10:12.910032  0.902950   0.75966  193.787502
                ALL             0     0.0       SP500      USD 2024-12-16 15:10:12.910032  0.902950   0.75966  187.209078
                BA              0     0.0       SP500      USD 2024-12-16 15:10:12.910032  0.902950   0.75966  172.925003
                BIIB            0     0.0       SP500      USD 2024-12-16 15:10:12.910032  0.902950   0.75966  204.365005
    ...                       ...     ...         ...      ...                        ...       ...       ...         ...
    2024-10-30  QRVO            0     0.0       SP500      USD 2024-12-16 15:10:12.910032  0.922655   0.76987   74.660000
                ROP            65     0.0       SP500      USD 2024-12-16 15:10:12.910032  0.922655   0.76987  547.744995
                SMCI            0     0.0       SP500      USD 2024-12-16 15:10:12.910032  0.922655   0.76987   35.100000
                TSLA            0     0.0       SP500      USD 2024-12-16 15:10:12.910032  0.922655   0.76987  259.585007
                UAL             0     0.0       SP500      USD 2024-12-16 15:10:12.910032  0.922655   0.76987   78.744999
    """
    try:
        # Generate cache key and construct cache file path
        cache_key = generate_cache_key_prepared_data(
            portfolio_path, equity_path, fx_path
        )

        # Return cached data if it exists
        if (cache_file_path := CACHE_DIR / f"{cache_key}.parquet").exists():
            return pd.read_parquet(cache_file_path)

        # If no cache exists or loading failed, load and prepare the data
        positions_df, prices_df, fx_df = _validate_and_load(
            portfolio_path, equity_path, fx_path
        )

        df = _prepare_portfolio_data_with_usd_prices(positions_df, prices_df, fx_df)

        log.debug(f"Prepared DataFrame: {df.head()}\n{df.tail()}")

        df.to_parquet(cache_file_path)
        return df

    except Exception as e:
        raise MetricsCalculationError(str(e)) from e


def _prepare_portfolio_data_with_usd_prices(
    positions_df: pd.DataFrame, prices_df: pd.DataFrame, fx_df: pd.DataFrame
) -> pd.DataFrame:
    """Prepares position data with trades and joins with prices,
    and calculating USD-converted portfolio values and cash flows."""

    # Prepare price data with complete portfolio date range
    holdings_dates = positions_df.index.get_level_values("Date").unique()
    tickers = prices_df.index.get_level_values("Ticker").unique()
    multi_index = pd.MultiIndex.from_product(
        [holdings_dates, tickers],
        names=["Date", "Ticker"],
    )
    prices_df = prices_df.reindex(multi_index).groupby("Ticker").ffill()

    # Join with prices
    combined_df = positions_df.join(prices_df)

    # Join with FX rates
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
