import datetime as dtm
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from portfolio_analytics.api.market_data.equity import Equity
from portfolio_analytics.common.instruments import Currency, StockIndex


@pytest.fixture
def mock_sp500_data():
    return pd.DataFrame({"Symbol": ["AAPL", "BRK.B", "BF.B"]})


@pytest.fixture
def mock_ftse_data():
    return pd.DataFrame({"Ticker": ["AAL", "HSBA", "VOD"]})


@pytest.fixture
def mock_eurostoxx_data():
    return pd.DataFrame({"Ticker": ["ADS", "AIR", "ALV"]})


@pytest.fixture
def mock_yahoo_data():
    # Create sample multi-level columns with names
    columns = pd.MultiIndex.from_product(
        [
            ["AAPL", "MSFT"],  # Tickers
            ["Open", "High", "Low", "Close", "Volume"],  # Price columns
        ],
        names=["Ticker", "Price"],
    )  # Add names to MultiIndex

    # Create sample data
    data = [
        # AAPL data          MSFT data
        [100, 101, 99, 100.5, 1000, 200, 201, 199, 200.5, 2000],  # 2024-01-01
        [101, 102, 100, 101.5, 1100, 201, 202, 200, 201.5, 2100],  # 2024-01-02
    ]

    # Create DataFrame with named DatetimeIndex
    dates = pd.date_range("2024-01-01", periods=2, freq="D", name="Date")
    return pd.DataFrame(data, index=dates, columns=columns)


class TestEquity:
    def test_init(self):
        equity = Equity(StockIndex.SP500)
        assert equity.index == StockIndex.SP500

    def test_get_output_filepath(self):
        path = Equity.get_output_filepath()
        assert isinstance(path, Path)

    @patch("pandas.read_html")
    def test_get_sp500_tickers(self, mock_read_html, mock_sp500_data):
        mock_read_html.return_value = [mock_sp500_data]
        equity = Equity(StockIndex.SP500)
        tickers = equity.get_tickers()

        assert tickers == ["AAPL", "BRK-B", "BF-B"]
        mock_read_html.assert_called_once_with(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        )

    @patch("pandas.read_html")
    def test_get_ftse100_tickers(self, mock_read_html, mock_ftse_data):
        mock_read_html.return_value = [None, None, None, None, mock_ftse_data]
        equity = Equity(StockIndex.FTSE100)
        tickers = equity.get_tickers()

        assert tickers == ["AAL.L", "HSBA.L", "VOD.L"]
        mock_read_html.assert_called_once_with(
            "https://en.wikipedia.org/wiki/FTSE_100_Index"
        )

    @patch("pandas.read_html")
    def test_get_eurostoxx50_tickers(self, mock_read_html, mock_eurostoxx_data):
        mock_read_html.return_value = [None, None, None, None, mock_eurostoxx_data]
        equity = Equity(StockIndex.EUROSTOXX50)
        tickers = equity.get_tickers()

        assert tickers == ["ADS", "AIR", "ALV"]
        mock_read_html.assert_called_once_with(
            "https://en.wikipedia.org/wiki/EURO_STOXX_50"
        )

    def test_get_tickers_invalid_index(self):
        invalid_index = Mock()
        equity = Equity(invalid_index)
        with pytest.raises(Exception):  # Replace with your specific exception
            equity.get_tickers()

    def test_add_static_columns(self):
        equity = Equity(StockIndex.SP500)

        # Create sample input DataFrame
        df = pd.DataFrame(
            {"Value": [100, 200, 300]},
            index=pd.MultiIndex.from_tuples(
                [
                    (dtm.date(2024, 1, 1), "AAPL"),
                    (dtm.date(2024, 1, 1), "MSFT"),
                    (dtm.date(2024, 1, 1), "GOOGL"),
                ],
                names=["Date", "Ticker"],
            ),
        )

        result = equity.add_static_columns(df)

        # Check if new columns are added
        assert "EquityIndex" in result.columns
        assert "Currency" in result.columns
        assert "CreatedAt" in result.columns

        # Check values
        assert result["EquityIndex"].unique()[0] == StockIndex.SP500.value
        assert result["Currency"].unique()[0] == Currency.USD.value

    @patch.object(Equity, "download_and_transform")
    @patch.object(Equity, "save_to_parquet")
    def test_update_market_data(self, mock_save, mock_download):
        # Setup mock returns
        mock_download.return_value = pd.DataFrame()
        mock_save.return_value = "test_path.parquet"

        # Test parameters
        start_date = dtm.date(2024, 1, 1)
        end_date = dtm.date(2024, 1, 31)
        instruments = [StockIndex.SP500, StockIndex.FTSE100]

        # Call method
        result = Equity.update_market_data(
            instruments=instruments, start_date=start_date, end_date=end_date
        )

        # Verify results
        assert isinstance(result, Path)
        assert mock_download.call_count == len(instruments)
        assert mock_save.call_count == 1

    @patch.object(Equity, "get_tickers")
    @patch("yfinance.download")
    def test_download_and_transform(
        self, mock_yf_download, mock_get_tickers, mock_yahoo_data
    ):
        # Setup
        equity = Equity(StockIndex.SP500)
        mock_get_tickers.return_value = ["AAPL", "MSFT"]
        mock_yf_download.return_value = mock_yahoo_data

        # Test parameters
        start_date = dtm.date(2024, 1, 1)
        end_date = dtm.date(2024, 1, 2)

        # Execute
        result = equity.download_and_transform(start_date, end_date)

        # Verify
        assert isinstance(result, pd.DataFrame)
        assert isinstance(result.index, pd.MultiIndex)  # Should have Date, Ticker index
        assert "EquityIndex" in result.columns
        assert "Currency" in result.columns
        assert "CreatedAt" in result.columns

        # Verify data structure
        assert len(result) == 4  # 2 dates * 2 tickers
        assert result.index.names == ["Date", "Ticker"]

        # Verify static columns
        assert (result["EquityIndex"] == StockIndex.SP500.value).all()
        assert (result["Currency"] == Currency.USD.value).all()

        # Verify mock calls
        mock_yf_download.assert_called_once()
        mock_get_tickers.assert_called_once()
