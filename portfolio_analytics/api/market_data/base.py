"""Market data base module providing abstract base class for
data source implementations.

This module defines the core functionality for downloading and processing market data
from Yahoo Finance. It includes the base exception class and an abstract base class
that implements common functionality for different types of market data sources.

Classes:
    MarketDataException: Base exception for market data operations.
    YahooFinanceDataSource: Abstract base class for Yahoo Finance data sources.
"""

import datetime as dtm
import ssl
import warnings
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, TypeVar

import pandas as pd
import requests
import urllib3
import yfinance as yf

from portfolio_analytics.common.utils.instruments import Instrument
from portfolio_analytics.common.utils.logging_config import setup_logger

# Configure logging
log = setup_logger(__name__)

# Configure SSL and suppress warnings
ssl._create_default_https_context = ssl._create_unverified_context
warnings.filterwarnings("ignore", category=urllib3.exceptions.InsecureRequestWarning)


class MarketDataException(Exception):
    """Base exception for market data operations."""


T = TypeVar("T", bound=Instrument)


class YahooFinanceDataSource(ABC):
    """Abstract base class for Yahoo Finance data sources."""

    @abstractmethod
    def get_tickers(self) -> List[str]:
        """Get list of tickers for this data source."""

    def download_and_transform(
        self,
        start_date: Optional[dtm.date] = None,
        end_date: Optional[dtm.date] = None,
    ) -> pd.DataFrame:
        """Download and transform market data for the specified date range.

        Args:
            start_date: Optional start date for data download. If None, downloads from
                earliest available date.
            end_date: Optional end date for data download. If None, downloads up to
                latest available date.

        Returns:
            pd.DataFrame: Transformed data with MultiIndex (Date, Ticker) and columns
                including 'Mid' price and static fields.

        Raises:
            MarketDataException: If no data is fetched from Yahoo Finance.
        """

        # TODO: to remove
        session = requests.Session()
        session.verify = False

        tickers = self.get_tickers()

        period_str = (
            f"from {start_date} to {end_date}"
            if start_date and end_date
            else (
                f"from {start_date} onwards"
                if start_date
                else f"until {end_date}" if end_date else "(full history)"
            )
        )

        log.info(
            f"{type(self).__name__}: Downloading data for {len(tickers)} tickers"
            f" {period_str}"
        )

        df = yf.download(
            tickers=tickers,
            start=start_date.strftime("%Y-%m-%d") if start_date else None,
            end=end_date.strftime("%Y-%m-%d") if end_date else None,
            auto_adjust=True,
            session=session,
            group_by="ticker",
        )

        if df.empty:
            raise MarketDataException(f"No data fetched for {type(self).__name__}")

        # Transform directly
        df = (df.xs("High", level=1, axis=1) + df.xs("Low", level=1, axis=1)) / 2.0
        df_long = pd.melt(
            df.reset_index(),
            id_vars=["Date"],
            var_name="Ticker",
            value_name="Mid",
        )
        df_long["Date"] = df_long["Date"].dt.date
        df_long.set_index(["Date", "Ticker"], inplace=True)

        df_long = self.add_static_columns(df_long)

        log.info(f"{type(self).__name__}: Downloaded and transformed {len(df)} rows")
        log.debug(
            f"{type(self).__name__} DataFrame info:\n- Shape: {df_long.shape}\n- Index:"
            f" {df_long.index.names}\n- Date range:"
            f" {df_long.index.get_level_values('Date').min()} to"
            f" {df_long.index.get_level_values('Date').max()}\n- Number of unique"
            f" tickers: {len(df_long.index.get_level_values('Ticker').unique())}\n-"
            f" Columns: {df_long.columns.tolist()}\n- First few"
            f" rows:\n{df_long.head().to_string()}\n- Data"
            f" types:\n{df_long.dtypes.to_string()}\n- Missing values:"
            f" {df_long.isna().sum().to_dict()}"
        )

        return df_long

    @classmethod
    @abstractmethod
    def update_market_data(
        cls,
        instruments: List[T],
        start_date: Optional[dtm.date] = None,
        end_date: Optional[dtm.date] = None,
    ) -> Path:
        """Download, process, and save market data for given instruments
        and date range."""

    def add_static_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add static columns to the DataFrame.

        Args:
            df: DataFrame with MultiIndex (Date, Ticker)

        Returns:
            DataFrame with additional static columns
        """
        df = df.reset_index()
        df["CreatedAt"] = dtm.datetime.now()
        df = df.set_index(["Date", "Ticker"])
        return df

    @classmethod
    @abstractmethod
    def get_output_filepath(cls) -> Path:
        """Get the output file path for this data source."""

    @classmethod
    def save_to_parquet(cls, df: pd.DataFrame) -> Path:
        """Save DataFrame to parquet file, appending to existing data if present.

        Handles deduplication of records based on the primary key (Date, Ticker),
        keeping the latest version of any duplicated records.

        Args:
            df: DataFrame to save, with MultiIndex (Date, Ticker).

        Returns:
            Path: The filesystem path where the data was saved.
        """

        log.debug(f"{cls.__name__}: New data shape: {df.shape}")

        if (output_path := cls.get_output_filepath()).exists():
            existing_df = pd.read_parquet(output_path)
            log.debug(f"{cls.__name__}: Existing data shape: {existing_df.shape}")

            df = pd.concat([existing_df, df])
            log.debug(f"{cls.__name__}: Combined data shape (before dedup): {df.shape}")

            duplicates_count = df.index.duplicated().sum()
            log.debug(f"{cls.__name__}: Found {duplicates_count} duplicate records")

            df = df[~df.index.duplicated(keep="last")]
            log.debug(
                f"{cls.__name__}: Final data shape (after deduplication): {df.shape}"
            )

        df.to_parquet(output_path, compression="snappy")
        log.info(f"{cls.__name__}: Saved data to {output_path}")
        return output_path
