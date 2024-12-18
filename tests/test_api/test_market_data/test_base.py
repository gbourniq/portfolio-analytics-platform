"""Unit tests for YahooFinanceDataSource base class."""

import datetime as dtm
from pathlib import Path
from typing import List
from unittest.mock import patch

import pandas as pd
import pytest

from portfolio_analytics.api.market_data.base import (
    MarketDataException,
    YahooFinanceDataSource,
)


class MockYahooFinanceDataSource(YahooFinanceDataSource):
    """Mock implementation of YahooFinanceDataSource for testing."""

    def get_tickers(self) -> List[str]:
        return ["AAPL", "MSFT"]

    @classmethod
    def get_output_filepath(cls) -> Path:
        return Path("mock_output.parquet")

    @classmethod
    def update_market_data(cls, instruments, start_date=None, end_date=None) -> Path:
        return cls.get_output_filepath()


@pytest.fixture
def data_source():
    """Fixture providing MockYahooFinanceDataSource instance."""
    return MockYahooFinanceDataSource()


@pytest.fixture
def sample_market_data():
    """Fixture providing sample market data DataFrame."""
    dates = pd.DatetimeIndex(["2023-12-19", "2023-12-20"], name="Date")
    columns = pd.MultiIndex.from_tuples(
        [
            ("EURUSD=X", "Open"),
            ("EURUSD=X", "High"),
            ("EURUSD=X", "Low"),
            ("EURUSD=X", "Close"),
            ("EURUSD=X", "Volume"),
            ("EURGBP=X", "Open"),
            ("EURGBP=X", "High"),
            ("EURGBP=X", "Low"),
            ("EURGBP=X", "Close"),
            ("EURGBP=X", "Volume"),
        ],
        names=["Ticker", "Price"],
    )

    data = [
        [
            1.092383,
            1.098800,
            1.091608,
            1.092383,
            0,
            0.86335,
            0.86357,
            0.86335,
            0.86335,
            0,
        ],
        [
            1.098105,
            1.097972,
            1.093565,
            1.098105,
            0,
            0.86242,
            0.86674,
            0.86242,
            0.86242,
            0,
        ],
    ]

    return pd.DataFrame(data, index=dates, columns=columns)


def test_yf_download_never_called():
    """Test that yf.download is never actually called during tests."""
    with patch("yfinance.download") as mock_download:
        mock_download.side_effect = Exception(
            "yf.download should not be called during tests"
        )

        data_source = MockYahooFinanceDataSource()

        # Create sample data with proper multi-level columns
        dates = pd.DatetimeIndex(["2023-12-19", "2023-12-20"], name="Date")
        columns = pd.MultiIndex.from_tuples(
            [
                ("EURUSD=X", "Open"),
                ("EURUSD=X", "High"),
                ("EURUSD=X", "Low"),
                ("EURUSD=X", "Close"),
                ("EURUSD=X", "Volume"),
                ("EURGBP=X", "Open"),
                ("EURGBP=X", "High"),
                ("EURGBP=X", "Low"),
                ("EURGBP=X", "Close"),
                ("EURGBP=X", "Volume"),
            ],
            names=["Ticker", "Price"],
        )

        data = [
            [
                1.092383,
                1.098800,
                1.091608,
                1.092383,
                0,
                0.86335,
                0.86357,
                0.86335,
                0.86335,
                0,
            ],
            [
                1.098105,
                1.097972,
                1.093565,
                1.098105,
                0,
                0.86242,
                0.86674,
                0.86242,
                0.86242,
                0,
            ],
        ]

        sample_data = pd.DataFrame(data, index=dates, columns=columns)

        with patch("yfinance.download", return_value=sample_data):
            result = data_source.download_and_transform(
                start_date=dtm.date(2024, 1, 1), end_date=dtm.date(2024, 1, 2)
            )
            assert isinstance(result, pd.DataFrame)


@patch("yfinance.download")
def test_download_and_transform_empty_data(mock_download, data_source):
    """Test download_and_transform raises exception when no data is fetched."""
    mock_download.return_value = pd.DataFrame()

    with pytest.raises(MarketDataException):
        data_source.download_and_transform()


@patch("yfinance.download")
def test_download_and_transform_success(mock_download, data_source, sample_market_data):
    """Test successful data download and transformation."""
    mock_download.return_value = sample_market_data

    result = data_source.download_and_transform()

    assert isinstance(result, pd.DataFrame)
    assert result.index.names == ["Date", "Ticker"]
    assert "Mid" in result.columns
    assert "CreatedAt" in result.columns


def test_save_to_parquet_new_file(data_source, tmp_path, monkeypatch):
    """Test saving data to a new parquet file."""

    # Given
    test_df = pd.DataFrame(
        {"Mid": [100.0]},
        index=pd.MultiIndex.from_tuples(
            [(dtm.date(2024, 1, 1), "AAPL")], names=["Date", "Ticker"]
        ),
    )
    monkeypatch.setattr(
        MockYahooFinanceDataSource,
        "get_output_filepath",
        lambda: tmp_path / "test_output.parquet",
    )

    # When
    output_path = MockYahooFinanceDataSource.save_to_parquet(test_df)

    # Then
    assert output_path.exists()
    saved_df = pd.read_parquet(output_path)
    assert saved_df.shape == test_df.shape


def test_save_to_parquet_with_duplicates(data_source, tmp_path, monkeypatch):
    """Test deduplication when saving to existing parquet file."""

    # Given
    existing_df = pd.DataFrame(
        {"Mid": [100.0]},
        index=pd.MultiIndex.from_tuples(
            [(dtm.date(2024, 1, 1), "AAPL")], names=["Date", "Ticker"]
        ),
    )
    new_df = pd.DataFrame(
        {"Mid": [101.0]},
        index=pd.MultiIndex.from_tuples(
            [(dtm.date(2024, 1, 1), "AAPL")], names=["Date", "Ticker"]
        ),
    )
    output_path = tmp_path / "test_output.parquet"
    existing_df.to_parquet(output_path)
    monkeypatch.setattr(
        MockYahooFinanceDataSource, "get_output_filepath", lambda: output_path
    )

    # When
    MockYahooFinanceDataSource.save_to_parquet(new_df)

    # Then
    saved_df = pd.read_parquet(output_path)
    assert saved_df.loc[(dtm.date(2024, 1, 1), "AAPL"), "Mid"] == 101.0
