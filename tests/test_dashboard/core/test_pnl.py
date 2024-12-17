"""
Profit and Loss calculation module for the Portfolio Analytics Dashboard.
"""

import pandas as pd

from portfolio_analytics.common.utils.logging_config import setup_logger
from portfolio_analytics.dashboard.utils.dashboard_exceptions import (
    MetricsCalculationError,
)

# Configure logging
log = setup_logger(__name__)


def calculate_pnl(positions_prices_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates portfolio PnL from position data with currency conversion.
    """
    try:
        # Calculate base PnL
        pnl_df = pd.DataFrame()
        pnl_df["pnl_unrealised"] = positions_prices_df.groupby("Date")[
            "PortfolioValues"
        ].sum()
        pnl_df["pnl_realised"] = (
            positions_prices_df.groupby("Date")["CashFlow"].sum().cumsum()
        )

        return pnl_df

    except Exception as e:
        raise MetricsCalculationError(f"Error calculating PnL: {str(e)}") from e
