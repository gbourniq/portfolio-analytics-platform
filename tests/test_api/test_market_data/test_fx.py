import datetime as dtm
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from portfolio_analytics.api.market_data.fx import FX
from portfolio_analytics.common.utils.instruments import Currency


@pytest.fixture
def mock_yahoo_fx_data():
    # Create sample multi-level columns with names
    columns = pd.MultiIndex.from_product(
        [
            ["EURUSD=X", "GBPUSD=X"],  # FX Pairs
            ["Open", "High", "Low", "Close", "Volume"],  # Price columns
        ],
        names=["Ticker", "Price"],
    )

    # Create sample data
    data = [
        # EURUSD=X data       GBPUSD=X data
        [1.10, 1.11, 1.09, 1.105, 1000, 1.25, 1.26, 1.24, 1.255, 2000],  # 2024-01-01
        [1.11, 1.12, 1.10, 1.115, 1100, 1.26, 1.27, 1.25, 1.265, 2100],  # 2024-01-02
    ]

    # Create DataFrame with named DatetimeIndex
    dates = pd.date_range("2024-01-01", periods=2, freq="D", name="Date")
    return pd.DataFrame(data, index=dates, columns=columns)


class TestFX:
    def test_init(self):
        fx = FX([Currency.EUR, Currency.GBP])
        assert fx.base_currencies == [Currency.EUR, Currency.GBP]

    def test_get_output_filepath(self):
        path = FX.get_output_filepath()
        assert isinstance(path, Path)

    def test_get_tickers(self):
        fx = FX([Currency.EUR])
        tickers = fx.get_tickers()

        # EUR should create pairs with all other currencies except itself
        expected_pairs = [f"EUR{c.value}=X" for c in Currency if c != Currency.EUR]
        assert sorted(tickers) == sorted(expected_pairs)
        assert "EURUSD=X" in tickers
        assert "EURGBP=X" in tickers
        assert "EUREUR=X" not in tickers  # Shouldn't create pair with itself

    def test_get_tickers_multiple_base(self):
        fx = FX([Currency.EUR, Currency.GBP])
        tickers = fx.get_tickers()

        # Check EUR and GBP pairs are present
        eur_pairs = [f"EUR{c.value}=X" for c in Currency if c != Currency.EUR]
        gbp_pairs = [f"GBP{c.value}=X" for c in Currency if c != Currency.GBP]
        expected_pairs = eur_pairs + gbp_pairs

        assert sorted(tickers) == sorted(expected_pairs)
        assert "EURUSD=X" in tickers
        assert "GBPUSD=X" in tickers
        assert "EURGBP=X" in tickers
        assert "GBPEUR=X" in tickers

    @patch("yfinance.download")
    def test_download_and_transform(self, mock_yf_download, mock_yahoo_fx_data):
        # Setup
        fx = FX([Currency.EUR, Currency.GBP])
        mock_yf_download.return_value = mock_yahoo_fx_data

        # Test parameters
        start_date = dtm.date(2024, 1, 1)
        end_date = dtm.date(2024, 1, 2)

        # Execute
        result = fx.download_and_transform(start_date, end_date)

        # Verify
        assert isinstance(result, pd.DataFrame)
        assert isinstance(result.index, pd.MultiIndex)  # Should have Date, Ticker index
        assert "CreatedAt" in result.columns

        # Verify data structure
        assert len(result) == 4  # 2 dates * 2 tickers
        assert result.index.names == ["Date", "Ticker"]

        # Verify mock calls
        mock_yf_download.assert_called_once()

    @patch.object(FX, "download_and_transform")
    @patch.object(FX, "save_to_parquet")
    def test_update_market_data(self, mock_save, mock_download):
        # Setup mock returns
        mock_download.return_value = pd.DataFrame()
        mock_save.return_value = "test_path.parquet"

        # Test parameters
        start_date = dtm.date(2024, 1, 1)
        end_date = dtm.date(2024, 1, 31)
        currencies = [Currency.EUR, Currency.GBP]

        # Call method
        result = FX.update_market_data(
            instruments=currencies, start_date=start_date, end_date=end_date
        )

        # Verify results
        assert isinstance(result, Path)
        assert mock_download.call_count == 1
        assert mock_save.call_count == 1
