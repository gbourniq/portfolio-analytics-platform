"""
Intended for running analysis on a portfolio file
instead of relying on the Dashboard
"""

from portfolio_analytics.common.instruments import Currency
from portfolio_analytics.common.logging_config import setup_logger

from portfolio_analytics.dashboard.core.data_loader import prepare_data
from portfolio_analytics.dashboard.core.pnl import calculate_pnl, calculate_daily_pnl
from portfolio_analytics.dashboard.core.stats import (
    calculate_stats,
    get_winners_and_losers,
)
from portfolio_analytics.dashboard.utils.dashboard_exceptions import (
    MissingTickersException,
    MetricsCalculationError,
)

import numpy as np

# Configure logging
log = setup_logger(__name__)

try:

    from portfolio_analytics.common.filesystem import (
        EQUITY_FILE_PATH,
        FX_DATA_PATH,
        PORTFOLIO_SAMPLES_DIR,
    )

    # Computed cached based data
    prepared_data = prepare_data(
        PORTFOLIO_SAMPLES_DIR / "sample_portfolio.csv",
        EQUITY_FILE_PATH,
        FX_DATA_PATH,
    )

    # Compute cached PnL
    pnl_df = calculate_pnl(prepared_data, target_currency=Currency.EUR)

    # Outputs
    daily_pnl_df = calculate_daily_pnl(pnl_df)
    winners_df, losers_df = get_winners_and_losers(pnl_df)
    stats = calculate_stats(pnl_df)

    # Validation: Sum of PnL per ticker matches the period PnL within 1% tolerance
    pnl_per_ticker = pnl_df.groupby("Ticker")["PnL"].last()
    assert np.isclose(pnl_per_ticker.sum(), stats.period_pnl, rtol=0.01), (
        "PnL per ticker differs from period PnL by more than 1%,"
        "indicating a potential calculation issue"
    )

    log.info(pnl_df.head())
    log.info(f"Analysis complete. Stats:\n{stats}")

except MissingTickersException as e:
    log.error(f"Portfolio Analysis Failed: {str(e)}")
    log.error("Please ensure all portfolio tickers have corresponding price data.")
except MetricsCalculationError as e:
    log.error(f"Portfolio Analysis Failed: {str(e)}")
