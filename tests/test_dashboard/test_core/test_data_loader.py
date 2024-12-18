"""Unit tests for data_loader module."""

from pathlib import Path

import pandas as pd
import pytest

from portfolio_analytics.common.utils.instruments import Currency
from portfolio_analytics.dashboard.core.data_loader import (
    join_positions_and_prices,
    prepare_data,
    validate_and_load,
)
from portfolio_analytics.dashboard.utils.dashboard_exceptions import (
    MissingTickersException,
)


@pytest.fixture
def sample_portfolio_df():
    """Returns a sample portfolio DataFrame."""
    return pd.DataFrame(
        {
            "Date": ["2024-01-01", "2024-01-02"],
            "AAPL": [100, 150],
            "MSFT": [200, 250],
        }
    )


@pytest.fixture
def sample_prices_df():
    """Returns a sample prices DataFrame with MultiIndex."""
    idx = pd.MultiIndex.from_tuples(
        [
            ("2024-01-01", "AAPL"),
            ("2024-01-01", "MSFT"),
            ("2024-01-02", "AAPL"),
            ("2024-01-02", "MSFT"),
        ],
        names=["Date", "Ticker"],
    )
    return pd.DataFrame(
        {"Mid": [150.0, 200.0, 155.0, 205.0], "Currency": ["USD", "USD", "USD", "USD"]},
        index=idx,
    )


@pytest.fixture
def sample_fx_df():
    """Returns a sample FX rates DataFrame with MultiIndex."""
    data = {
        ("2024-01-01", "EURUSD=X"): 1.1,
        ("2024-01-01", "GBPUSD=X"): 1.3,
        ("2024-01-01", "USDEUR=X"): 1 / 1.1,  # Add inverse rates
        ("2024-01-01", "USDGBP=X"): 1 / 1.3,
        ("2024-01-02", "EURUSD=X"): 1.12,
        ("2024-01-02", "GBPUSD=X"): 1.31,
        ("2024-01-02", "USDEUR=X"): 1 / 1.12,
        ("2024-01-02", "USDGBP=X"): 1 / 1.31,
    }
    idx = pd.MultiIndex.from_tuples(data.keys(), names=["Date", "Ticker"])
    return pd.DataFrame({"Mid": list(data.values())}, index=idx)


class TestValidateAndLoad:
    """Unit tests for validate_and_load function."""

    def test_successful_load(
        self, tmp_path, monkeypatch, sample_portfolio_df, sample_prices_df, sample_fx_df
    ):
        """Tests successful loading of all required data files."""
        # Given
        holdings_path = tmp_path / "holdings.csv"
        sample_portfolio_df.to_csv(holdings_path)
        prices_path = tmp_path / "prices.parquet"
        sample_prices_df.to_parquet(prices_path)
        fx_path = tmp_path / "fx.parquet"
        sample_fx_df.to_parquet(fx_path)

        def mock_read_portfolio(*args, **kwargs):
            return sample_portfolio_df

        monkeypatch.setattr(
            "portfolio_analytics.dashboard.core.data_loader.read_portfolio_file",
            mock_read_portfolio,
        )

        # When
        positions, prices, fx = validate_and_load(holdings_path, prices_path, fx_path)

        # Then
        assert not positions.empty
        assert not prices.empty
        assert not fx.empty
        assert list(positions.index.names) == ["Date", "Ticker"]

    def test_missing_tickers(
        self, tmp_path, monkeypatch, sample_portfolio_df, sample_prices_df, sample_fx_df
    ):
        """Tests error handling when tickers are missing from price data."""
        # Given
        holdings_path = tmp_path / "holdings.csv"
        sample_portfolio_df["MISSING"] = [300, 350]  # Add missing ticker
        sample_portfolio_df.to_csv(holdings_path)
        prices_path = tmp_path / "prices.parquet"
        sample_prices_df.to_parquet(prices_path)
        fx_path = tmp_path / "fx.parquet"
        sample_fx_df.to_parquet(fx_path)

        def mock_read_portfolio(*args, **kwargs):
            return sample_portfolio_df

        monkeypatch.setattr(
            "portfolio_analytics.dashboard.core.data_loader.read_portfolio_file",
            mock_read_portfolio,
        )

        # When/Then
        with pytest.raises(MissingTickersException):
            validate_and_load(holdings_path, prices_path, fx_path)


class TestPrepareData:
    """Unit tests for prepare_data function."""

    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch, tmp_path):
        """Setup common test dependencies."""
        self.cache_dir = tmp_path / "cache"
        self.cache_dir.mkdir()
        monkeypatch.setattr(
            "portfolio_analytics.dashboard.core.data_loader.CACHE_DIR", self.cache_dir
        )

    @pytest.mark.parametrize(
        "target_currency",
        [
            Currency.USD,
            Currency.EUR,
            Currency.GBP,
        ],
    )
    def test_prepare_data_different_currencies(
        self,
        target_currency,
        monkeypatch,
        sample_portfolio_df,
        sample_prices_df,
        sample_fx_df,
    ):
        """Tests data preparation with different target currencies."""

        # Given
        def mock_validate_load(*args, **kwargs):
            positions = sample_portfolio_df.melt(
                id_vars="Date", var_name="Ticker", value_name="Positions"
            )
            positions.set_index(["Date", "Ticker"], inplace=True)
            return positions, sample_prices_df, sample_fx_df

        def mock_generate_cache_key(*args, **kwargs):
            return "test_cache_key"

        monkeypatch.setattr(
            "portfolio_analytics.dashboard.core.data_loader.validate_and_load",
            mock_validate_load,
        )
        monkeypatch.setattr(
            "portfolio_analytics.dashboard.core.data_loader.generate_cache_key",
            mock_generate_cache_key,
        )

        # When
        result = prepare_data(
            Path("dummy.csv"),
            Path("dummy.parquet"),
            Path("dummy.parquet"),
            target_currency,
        )

        # Then
        assert "Currency" in result.columns
        assert result["Currency"].iloc[0] == target_currency.value

    def test_prepare_data_uses_cache(
        self,
        monkeypatch,
        sample_portfolio_df,
        sample_prices_df,
        sample_fx_df,
    ):
        """Tests that prepare_data returns cached data when called twice with same inputs."""
        # Given
        mock_validate_load_called = 0

        def mock_validate_load(*args, **kwargs):
            nonlocal mock_validate_load_called
            mock_validate_load_called += 1
            positions = sample_portfolio_df.melt(
                id_vars="Date", var_name="Ticker", value_name="Positions"
            )
            positions.set_index(["Date", "Ticker"], inplace=True)
            return positions, sample_prices_df, sample_fx_df

        def mock_generate_cache_key(*args, **kwargs):
            return "test_cache_key"

        monkeypatch.setattr(
            "portfolio_analytics.dashboard.core.data_loader.validate_and_load",
            mock_validate_load,
        )
        monkeypatch.setattr(
            "portfolio_analytics.dashboard.core.data_loader.generate_cache_key",
            mock_generate_cache_key,
        )

        # When
        result1 = prepare_data(
            Path("dummy.csv"),
            Path("dummy.parquet"),
            Path("dummy.parquet"),
            Currency.USD,
        )
        result2 = prepare_data(
            Path("dummy.csv"),
            Path("dummy.parquet"),
            Path("dummy.parquet"),
            Currency.USD,
        )

        # Then
        assert (
            mock_validate_load_called == 1
        )  # validate_and_load should only be called once
        pd.testing.assert_frame_equal(
            result1, result2
        )  # Both results should be identical
        cache_file = self.cache_dir / "test_cache_key.parquet"
        assert cache_file.exists()  # Cache file should exist


class TestJoinPositionsAndPrices:
    """Unit tests for join_positions_and_prices function."""

    def test_successful_join(self, sample_portfolio_df, sample_prices_df, sample_fx_df):
        """Tests successful joining of positions and prices data."""
        # Given
        positions = sample_portfolio_df.melt(
            id_vars="Date", var_name="Ticker", value_name="Positions"
        )
        positions.set_index(["Date", "Ticker"], inplace=True)

        # When
        result = join_positions_and_prices(positions, sample_prices_df, sample_fx_df)

        # Then
        assert "Trades" in result.columns
        assert "MidUsd" in result.columns
        assert not result.empty

    def test_join_with_different_currencies(self, sample_portfolio_df):
        """Tests joining positions and prices with different currencies."""
        # Given
        positions = sample_portfolio_df.melt(
            id_vars="Date", var_name="Ticker", value_name="Positions"
        )
        positions.set_index(["Date", "Ticker"], inplace=True)

        # Create prices with mixed currencies
        idx = pd.MultiIndex.from_tuples(
            [
                ("2024-01-01", "AAPL"),
                ("2024-01-01", "MSFT"),
                ("2024-01-02", "AAPL"),
                ("2024-01-02", "MSFT"),
            ],
            names=["Date", "Ticker"],
        )
        prices_df = pd.DataFrame(
            {
                "Mid": [150.0, 200.0, 155.0, 205.0],
                "Currency": ["USD", "EUR", "USD", "EUR"],
            },
            index=idx,
        )

        # Create FX rates with all required currency pairs
        fx_data = {
            ("2024-01-01", "EURUSD=X"): 1.1,
            ("2024-01-01", "GBPUSD=X"): 1.3,  # Added GBP rates
            ("2024-01-01", "USDEUR=X"): 1 / 1.1,
            ("2024-01-01", "USDGBP=X"): 1 / 1.3,  # Added GBP rates
            ("2024-01-02", "EURUSD=X"): 1.12,
            ("2024-01-02", "GBPUSD=X"): 1.31,  # Added GBP rates
            ("2024-01-02", "USDEUR=X"): 1 / 1.12,
            ("2024-01-02", "USDGBP=X"): 1 / 1.31,  # Added GBP rates
        }
        fx_idx = pd.MultiIndex.from_tuples(fx_data.keys(), names=["Date", "Ticker"])
        fx_df = pd.DataFrame({"Mid": list(fx_data.values())}, index=fx_idx)

        # When
        result = join_positions_and_prices(positions, prices_df, fx_df)

        # Then
        assert "MidUsd" in result.columns
        assert not result.empty
        # Check if MSFT prices were converted from EUR to USD
        msft_rows = result.xs("MSFT", level="Ticker")
        assert msft_rows["MidUsd"].iloc[0] == pytest.approx(
            200.0 * 1.1
        )  # EUR to USD conversion
        assert msft_rows["MidUsd"].iloc[1] == pytest.approx(205.0 * 1.12)
        # Check if AAPL prices remained unchanged (already in USD)
        aapl_rows = result.xs("AAPL", level="Ticker")
        assert aapl_rows["MidUsd"].iloc[0] == 150.0
        assert aapl_rows["MidUsd"].iloc[1] == 155.0
