"""Market data module for handling equity index constituent data.

This module provides functionality to download and process equity data
for major stock indices (S&P 500, FTSE 100, EURO STOXX 50) from Yahoo
Finance. It handles the retrieval of constituent tickers, data transformation,
and storage.

Classes:
    Equity: Handler for stock index constituent data with currency mapping.
"""

import datetime as dtm
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

import pandas as pd

from portfolio_analytics.api.market_data.base import (
    MarketDataException,
    YahooFinanceDataSource,
)
from portfolio_analytics.common.utils.filesystem import EQUITY_FILE_PATH
from portfolio_analytics.common.utils.instruments import Currency, StockIndex
from portfolio_analytics.common.utils.logging_config import setup_logger

# Configure logging
log = setup_logger(__name__)


class Equity(YahooFinanceDataSource):
    """Handler for stock index data."""

    CURRENCY_MAP = {
        StockIndex.SP500: Currency.USD,
        StockIndex.FTSE100: Currency.GBP,
        StockIndex.EUROSTOXX50: Currency.EUR,
    }

    def __init__(self, index: StockIndex):
        log.debug(f"Initializing Equity handler for index: {index.value}")
        self.index = index
        self._ticker_functions = {
            StockIndex.SP500: self._get_sp500_tickers,
            StockIndex.FTSE100: self._get_ftse100_tickers,
            StockIndex.EUROSTOXX50: self._get_eurostoxx50_tickers,
        }

    @classmethod
    def get_output_filepath(cls) -> Path:
        return EQUITY_FILE_PATH

    @staticmethod
    def _get_sp500_tickers() -> List[str]:
        log.debug("Fetching S&P 500 tickers from Wikipedia")
        data = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
        mapping = {"BRK.B": "BRK-B", "BF.B": "BF-B"}
        tickers = [mapping.get(str(t), str(t)) for t in data[0]["Symbol"]]
        return tickers

    @staticmethod
    def _get_ftse100_tickers() -> List[str]:
        log.debug("Fetching FTSE 100 tickers from Wikipedia")
        data = pd.read_html("https://en.wikipedia.org/wiki/FTSE_100_Index")[4]
        tickers = [f"{str(t)}.L" for t in data["Ticker"]]
        return tickers

    @staticmethod
    def _get_eurostoxx50_tickers() -> List[str]:
        log.debug("Fetching EURO STOXX 50 tickers from Wikipedia")
        data = pd.read_html("https://en.wikipedia.org/wiki/EURO_STOXX_50")[4]
        tickers = [str(t) for t in data["Ticker"]]
        return tickers

    @lru_cache(maxsize=128)
    def get_tickers(self) -> List[str]:
        """Retrieve list of constituent tickers for the specified stock index.

        Returns:
            List[str]: List of stock tickers in Yahoo Finance format.

        Raises:
            MarketDataException: If the specified index is not supported.
        """
        if self.index not in self._ticker_functions:
            log.error(f"Unsupported index: {self.index}")
            raise MarketDataException(f"Unsupported index: {self.index}")

        tickers = self._ticker_functions[self.index]()
        log.info(f"Found {len(tickers)} tickers for {self.index.value}")
        log.debug(f"Tickers for {self.index.value}: {tickers}")
        return tickers

    def add_static_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extend the base class static columns with added currency field.

        Args:
            df: DataFrame with MultiIndex (Date, Ticker)

        Returns:
            DataFrame with additional Currency and created_at columns
        """
        # First apply base class static columns
        df = super().add_static_columns(df)

        # Reset index to access Ticker column
        df = df.reset_index()

        # Add static columns
        df["EquityIndex"] = self.index.value
        df["Currency"] = self.CURRENCY_MAP[self.index].value

        # Reorder columns to put CreatedAt at the end
        cols = [col for col in df.columns if col != "CreatedAt"] + ["CreatedAt"]
        df = df[cols]

        # Restore the index
        df = df.set_index(["Date", "Ticker"])

        return df

    @classmethod
    def update_market_data(
        cls,
        instruments: List[StockIndex],  # type: ignore
        start_date: Optional[dtm.date] = None,
        end_date: Optional[dtm.date] = None,
    ) -> Path:
        log.info(f"Updating market data for indices: {[i.value for i in instruments]}")

        dfs = []
        for index in instruments:
            log.info(f"Processing {index.value}")
            handler = cls(index)
            df = handler.download_and_transform(start_date, end_date)
            dfs.append(df)
            log.debug(f"Processed {len(df)} rows for {index.value}")

        combined_df = pd.concat(dfs)
        log.info(f"Combined data shape: {combined_df.shape}")
        return Path(cls.save_to_parquet(combined_df))


if __name__ == "__main__":

    # historical
    start_date = dtm.date.today() - dtm.timedelta(days=365)
    end_date = dtm.date.today() - dtm.timedelta(days=10)

    # latest
    # start_date = dtm.date.today() - dtm.timedelta(days=10)
    # end_date = None

    stock_transformed_path = Equity.update_market_data(
        instruments=[StockIndex.SP500, StockIndex.FTSE100, StockIndex.EUROSTOXX50],
        start_date=start_date,
        end_date=end_date,
    )
