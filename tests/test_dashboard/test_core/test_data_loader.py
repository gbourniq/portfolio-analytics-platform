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
    MetricsCalculationError,
    MissingTickersException,
)


@pytest.fixture
def dates():
    """Returns sample dates as datetime.date objects."""
    return [pd.to_datetime("2024-01-01").date(), pd.to_datetime("2024-01-02").date()]


@pytest.fixture
def tickers():
    """Returns sample ticker symbols."""
    return ["AAPL", "MSFT"]


@pytest.fixture
def sample_portfolio_df(dates, tickers):
    """Returns a sample portfolio DataFrame with positions."""
    data = {
        "Date": dates,
        **{ticker: [100 + i * 50, 150 + i * 50] for i, ticker in enumerate(tickers)},
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_positions_df(sample_portfolio_df):
    """Returns melted positions DataFrame with MultiIndex."""
    positions = sample_portfolio_df.melt(
        id_vars="Date", var_name="Ticker", value_name="Positions"
    )
    return positions.set_index(["Date", "Ticker"])


@pytest.fixture
def sample_prices_df(dates, tickers):
    """Returns a sample prices DataFrame with MultiIndex."""
    idx = pd.MultiIndex.from_product([dates, tickers], names=["Date", "Ticker"])
    return pd.DataFrame(
        {"Mid": [150.0, 200.0, 155.0, 205.0], "Currency": ["USD"] * 4},
        index=idx,
    )


@pytest.fixture
def sample_fx_rates():
    """Returns sample FX rates data."""
    return {
        "EURUSD=X": [1.1, 1.12],
        "GBPUSD=X": [1.3, 1.31],
        "USDEUR=X": [1 / 1.1, 1 / 1.12],
        "USDGBP=X": [1 / 1.3, 1 / 1.31],
    }


@pytest.fixture
def sample_fx_df(dates, sample_fx_rates):
    """Returns a sample FX rates DataFrame with MultiIndex."""
    data = []
    for date in dates:
        for ticker, rates in sample_fx_rates.items():
            data.append((date, ticker, rates[dates.index(date)]))

    df = pd.DataFrame(data, columns=["Date", "Ticker", "Mid"])
    return df.set_index(["Date", "Ticker"])


class TestValidateAndLoad:
    """Unit tests for validate_and_load function."""

    def test_successful_load(
        self, tmp_path, monkeypatch, sample_portfolio_df, sample_prices_df, sample_fx_df
    ):
        """Tests successful loading of all required data files."""
        # Given
        holdings_path = tmp_path / "holdings.csv"
        prices_path = tmp_path / "prices.parquet"
        fx_path = tmp_path / "fx.parquet"

        sample_portfolio_df.to_csv(holdings_path)
        sample_prices_df.to_parquet(prices_path)
        sample_fx_df.to_parquet(fx_path)

        monkeypatch.setattr(
            "portfolio_analytics.dashboard.core.data_loader.read_portfolio_file",
            lambda *args, **kwargs: sample_portfolio_df,
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
        sample_portfolio_df["MISSING"] = [300, 350]  # Add missing ticker

        holdings_path = tmp_path / "holdings.csv"
        prices_path = tmp_path / "prices.parquet"
        fx_path = tmp_path / "fx.parquet"

        sample_portfolio_df.to_csv(holdings_path)
        sample_prices_df.to_parquet(prices_path)
        sample_fx_df.to_parquet(fx_path)

        monkeypatch.setattr(
            "portfolio_analytics.dashboard.core.data_loader.read_portfolio_file",
            lambda *args, **kwargs: sample_portfolio_df,
        )

        # When/Then
        with pytest.raises(MissingTickersException):
            validate_and_load(holdings_path, prices_path, fx_path)

    def test_fx_date_range_validation(
        self, tmp_path, monkeypatch, sample_portfolio_df, sample_prices_df, sample_fx_df
    ):
        """Tests error handling when portfolio dates are not fully covered by FX data."""
        # Given
        # Create portfolio with dates outside FX coverage
        sample_portfolio_df["Date"] = (
            pd.Series(["2023-12-31", "2024-01-02"]).pipe(pd.to_datetime).dt.date
        )

        # Convert MultiIndex dates to datetime.date for prices_df
        dates = pd.to_datetime(sample_prices_df.index.get_level_values("Date")).date
        tickers = sample_prices_df.index.get_level_values("Ticker")
        new_index = pd.MultiIndex.from_arrays([dates, tickers], names=["Date", "Ticker"])
        sample_prices_df.index = new_index

        # Convert MultiIndex dates to datetime.date for fx_df
        dates = pd.to_datetime(sample_fx_df.index.get_level_values("Date")).date
        tickers = sample_fx_df.index.get_level_values("Ticker")
        new_index = pd.MultiIndex.from_arrays([dates, tickers], names=["Date", "Ticker"])
        sample_fx_df.index = new_index

        # Save files
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

        # When/Then
        with pytest.raises(MetricsCalculationError) as exc_info:
            validate_and_load(holdings_path, prices_path, fx_path)

        assert "Portfolio date range" in str(exc_info.value)
        assert "not fully covered by market data" in str(exc_info.value)


class TestPrepareData:
    """Unit tests for prepare_data function."""

    @pytest.fixture
    def mock_validate_load(self, sample_positions_df, sample_prices_df, sample_fx_df):
        """Returns a mock validate_and_load function."""

        def _mock(*args, **kwargs):
            return sample_positions_df, sample_prices_df, sample_fx_df

        return _mock

    def test_prepare_data_uses_cache(self, tmp_path, monkeypatch, mock_validate_load):
        """Tests that prepare_data uses cache correctly."""
        # Given
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        monkeypatch.setattr(
            "portfolio_analytics.dashboard.core.data_loader.CACHE_DIR", cache_dir
        )
        monkeypatch.setattr(
            "portfolio_analytics.dashboard.core.data_loader.validate_and_load",
            mock_validate_load,
        )
        monkeypatch.setattr(
            "portfolio_analytics.dashboard.core.data_loader.generate_cache_key",
            lambda *args: "test_cache_key",
        )

        # When
        result1 = prepare_data(
            Path("dummy.csv"), Path("dummy.parquet"), Path("dummy.parquet"), Currency.USD
        )
        result2 = prepare_data(
            Path("dummy.csv"), Path("dummy.parquet"), Path("dummy.parquet"), Currency.USD
        )

        # Then
        pd.testing.assert_frame_equal(result1, result2)
        assert (cache_dir / "test_cache_key.parquet").exists()


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

        # Create prices with mixed currencies - using datetime.date objects
        dates = [
            pd.to_datetime("2024-01-01").date(),
            pd.to_datetime("2024-01-02").date(),
        ]
        idx = pd.MultiIndex.from_product(
            [dates, ["AAPL", "MSFT"]], names=["Date", "Ticker"]
        )
        prices_df = pd.DataFrame(
            {
                "Mid": [150.0, 200.0, 155.0, 205.0],
                "Currency": ["USD", "EUR", "USD", "EUR"],
            },
            index=idx,
        )

        # Create FX rates with all required currency pairs
        fx_pairs = ["EURUSD=X", "GBPUSD=X", "USDEUR=X", "USDGBP=X"]
        fx_idx = pd.MultiIndex.from_product([dates, fx_pairs], names=["Date", "Ticker"])
        # fmt: off
        fx_rates = [
            1.1, 1.3, 1/1.1, 1/1.3,  # 2024-01-01
            1.12, 1.31, 1/1.12, 1/1.31,  # 2024-01-02
        ]
        # fmt: on
        fx_df = pd.DataFrame({"Mid": fx_rates}, index=fx_idx)

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
