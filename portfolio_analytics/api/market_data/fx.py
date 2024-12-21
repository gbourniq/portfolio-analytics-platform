"""Market data module for handling foreign exchange (FX) rate data.

This module provides functionality to download and process FX rate data
from Yahoo Finance. It handles the generation of currency pairs, data
transformation, and storage for specified base currencies.

Classes:
    FX: Handler for foreign exchange rate data.
"""

import datetime as dtm
from pathlib import Path
from typing import List, Optional

from portfolio_analytics.api.market_data.base import YahooFinanceDataSource
from portfolio_analytics.common.filesystem import FX_DATA_PATH
from portfolio_analytics.common.instruments import Currency
from portfolio_analytics.common.logging_config import setup_logger

# Configure logging
log = setup_logger(__name__)


class FX(YahooFinanceDataSource):
    """Handler for FX data."""

    def __init__(self, base_currencies: List[Currency]):
        self.base_currencies = base_currencies

    @classmethod
    def get_output_filepath(cls) -> Path:
        return FX_DATA_PATH

    def get_tickers(self) -> List[str]:
        """Generate list of FX pair tickers for specified base currencies.

        Creates FX pairs by combining each base currency with all other available
        currencies in Yahoo Finance format (e.g., 'EURUSD=X').

        Returns:
            List[str]: List of FX pair tickers in Yahoo Finance format.
        """
        pairs = []
        log.debug(
            "Generating FX pairs for base currencies:"
            f" {[c.value for c in self.base_currencies]}"
        )
        for base in self.base_currencies:
            for quote in Currency:
                if base != quote:
                    pairs.append(f"{base.value}{quote.value}=X")
        log.info(f"Generated {len(pairs)} FX pairs")
        log.debug(f"FX pairs: {pairs}")
        return pairs

    @classmethod
    def update_market_data(
        cls,
        instruments: List[Currency],  # type: ignore
        start_date: Optional[dtm.date] = None,
        end_date: Optional[dtm.date] = None,
    ) -> Path:
        log.info(
            f"Updating FX data for base currencies: {[i.value for i in instruments]}"
        )

        handler = cls(instruments)

        df = handler.download_and_transform(start_date, end_date)

        return Path(cls.save_to_parquet(df))


if __name__ == "__main__":

    # historical
    start_date = dtm.date.today() - dtm.timedelta(days=365)
    end_date = dtm.date.today() - dtm.timedelta(days=10)

    # latest
    # start_date = dtm.date.today() - dtm.timedelta(days=10)
    # end_date = None

    fx_transformed_path = FX.update_market_data(
        instruments=[Currency.USD, Currency.EUR, Currency.GBP],
        start_date=start_date,
        end_date=end_date,
    )
