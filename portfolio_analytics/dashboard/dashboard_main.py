"""
Main application module for the Portfolio Analytics Dashboard.

This module serves as the entry point for the dashboard application. It initializes
the Dash application, sets up callbacks for interactivity, and handles the main
application logic for updating the dashboard based on user interactions and
data changes.
"""

import datetime as dtm
import os
import sys
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from dateutil.relativedelta import relativedelta

from portfolio_analytics.common.utils.filesystem import (
    EQUITY_FILE_PATH,
    FX_DATA_PATH,
    PORTFOLIO_UPLOADS_DIR,
    get_portfolio_files,
)
from portfolio_analytics.common.utils.instruments import Currency
from portfolio_analytics.common.utils.logging_config import setup_logger
from portfolio_analytics.dashboard.app.components import (
    add_drawdown_indicators,
    create_error_state,
    create_performance_table,
    create_pnl_figure,
    create_stats_row,
)
from portfolio_analytics.dashboard.app.layout import STYLES, create_layout
from portfolio_analytics.dashboard.core.data_loader import prepare_data
from portfolio_analytics.dashboard.core.pnl import (
    calculate_daily_pnl,
    calculate_pnl_expanded,
)
from portfolio_analytics.dashboard.core.stats import (
    calculate_stats,
    get_winners_and_losers,
)

# Configure logging
log = setup_logger(__name__)

# Initialize app and load initial data
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    title="Portfolio Analytics Dashboard",
)

# Define the layout
app = create_layout(app)

server = app.server  # Expose Flask server

# Disable debug mode
app.config.suppress_callback_exceptions = False


def _handle_button_styles(ctx, date_picker_style, trigger_source=None) -> dict:
    """Handle button styles based on context and user interactions.

    Args:
        ctx (dash.callback_context): The Dash callback context containing trigger
            information
        date_picker_style (dict): The current style dictionary for the date picker
        trigger_source (str, optional): The ID of the component that triggered
            the callback

    Returns:
        dict: A dictionary mapping button IDs to their style dictionaries,
            where each contains CSS properties for active/inactive states.
    """
    button_styles = {
        "1m-button": STYLES["button_inactive"].copy(),
        "6m-button": STYLES["button_inactive"].copy(),
        "1y-button": STYLES["button_inactive"].copy(),
        "3y-button": STYLES["button_inactive"].copy(),
        "max-button": STYLES["button_inactive"].copy(),
        "custom-button": STYLES["button_inactive"].copy(),
    }

    # Set max button as active by default or when changing portfolio/currency/pnl
    if not ctx.triggered or trigger_source in [
        "portfolio-selector",
        "currency-selector",
        "pnl-type-selector",
    ]:
        button_styles["max-button"] = STYLES["button_active"].copy()
        return button_styles

    # Handle button clicks
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if button_id in button_styles:
        for key in button_styles:
            button_styles[key] = STYLES["button_inactive"].copy()
        button_styles[button_id] = STYLES["button_active"].copy()

    # Handle custom date picker
    if date_picker_style["display"] == "block":
        for key in button_styles:
            button_styles[key] = STYLES["button_inactive"].copy()
        button_styles["custom-button"] = STYLES["button_active"].copy()

    return button_styles


def _handle_date_range(ctx, new_min_date, new_max_date, start_date, end_date):
    """Calculate date range and date picker visibility based on user interactions."""
    date_picker_style = {"display": "none"}
    current_date = dtm.datetime.now().date()

    # Convert string dates if needed
    if isinstance(start_date, str):
        start_date = dtm.datetime.strptime(start_date, "%Y-%m-%d").date()
    if isinstance(end_date, str):
        end_date = dtm.datetime.strptime(end_date, "%Y-%m-%d").date()

    # Get trigger information
    if not ctx.triggered:
        return new_min_date, new_max_date, date_picker_style

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Keep date picker visible if it's already shown and we're interacting with it
    if button_id == "date-range":
        date_picker_style = {"display": "block"}
        # Ensure dates are within valid range
        start_date = max(start_date, new_min_date)
        end_date = min(end_date, new_max_date)
        return start_date, end_date, date_picker_style

    # Handle other triggers
    if button_id in ["portfolio-selector", "currency-selector", "pnl-type-selector"]:
        return new_min_date, new_max_date, date_picker_style

    date_range_mapping = {
        "1m-button": relativedelta(months=1),
        "6m-button": relativedelta(months=6),
        "1y-button": relativedelta(years=1),
        "3y-button": relativedelta(years=3),
    }

    if button_id in date_range_mapping:
        end_date = min(current_date, new_max_date)
        start_date = max(end_date - date_range_mapping[button_id], new_min_date)
    elif button_id == "max-button":
        start_date, end_date = new_min_date, new_max_date
    elif button_id == "custom-button":
        date_picker_style = {"display": "block"}
        # Ensure dates are within valid range
        start_date = max(start_date, new_min_date)
        end_date = min(end_date, new_max_date)

    return start_date, end_date, date_picker_style


@app.callback(
    [
        Output("portfolio-selector", "options"),
        Output("pnl-graph", "figure"),
        Output("stats-display", "children"),
        Output("date-range", "min_date_allowed"),
        Output("date-range", "max_date_allowed"),
        Output("date-range", "start_date"),
        Output("date-range", "end_date"),
        Output("date-range", "initial_visible_month"),
        Output("winners-table", "children"),
        Output("losers-table", "children"),
        Output("date-range", "style"),
        Output("1m-button", "style"),
        Output("6m-button", "style"),
        Output("1y-button", "style"),
        Output("3y-button", "style"),
        Output("max-button", "style"),
        Output("custom-button", "style"),
    ],
    [
        Input("portfolio-selector", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
        Input("currency-selector", "value"),
        Input("1m-button", "n_clicks"),
        Input("6m-button", "n_clicks"),
        Input("1y-button", "n_clicks"),
        Input("3y-button", "n_clicks"),
        Input("max-button", "n_clicks"),
        Input("custom-button", "n_clicks"),
    ],
)
# pragma: no cover
def update_graph(  # pylint: disable=unused-argument,too-many-locals
    portfolio_name,
    start_date,
    end_date,
    currency,
    btn_1m,
    btn_6m,
    btn_1y,
    btn_3y,
    btn_max,
    btn_custom,
):
    """Main callback for updating the dashboard"""
    ctx = dash.callback_context
    trigger_source = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

    # Load initial data
    target_currency = Currency[currency]
    portfolio_files = get_portfolio_files()
    dropdown_options = [{"label": f.name, "value": str(f)} for f in portfolio_files]

    # Prepare data and handle errors
    try:
        prepared_data = prepare_data(
            Path(portfolio_name),
            EQUITY_FILE_PATH,
            FX_DATA_PATH,
            target_currency=target_currency,
        )
    except Exception as e:  # pylint: disable=broad-except
        return create_error_state(dropdown_options, str(e))

    # Get full date range from prepared data
    new_min_date = prepared_data.index.get_level_values("Date").min()
    new_max_date = prepared_data.index.get_level_values("Date").max()

    # Handle date ranges and picker visibility
    start_date, end_date, date_picker_style = _handle_date_range(
        ctx, new_min_date, new_max_date, start_date, end_date
    )

    # Filter data between start and end dates
    prepared_data = prepared_data[
        (prepared_data.index.get_level_values("Date") >= start_date)
        & (prepared_data.index.get_level_values("Date") <= end_date)
    ]

    pnl_expanded_df = calculate_pnl_expanded(prepared_data)

    # Calculate PnL and get date ranges
    pnl_df = calculate_daily_pnl(pnl_expanded_df)

    # Handle button styles
    button_styles = _handle_button_styles(ctx, date_picker_style, trigger_source)

    # Prepare and filter data
    df_plot = pnl_df.reset_index()
    df_plot = df_plot[(df_plot["Date"] >= start_date) & (df_plot["Date"] <= end_date)]

    # Create figure with selected PnL type
    fig = create_pnl_figure(df_plot)

    # Calculate stats and add drawdown indicators
    stats = calculate_stats(pnl_df)
    add_drawdown_indicators(fig, stats, start_date, end_date)

    # Get winners and losers
    winners, losers = get_winners_and_losers(pnl_expanded_df)

    # Create tables
    winners_table = create_performance_table(
        winners, is_positive=True, currency=target_currency
    )
    losers_table = create_performance_table(
        losers, is_positive=False, currency=target_currency
    )

    return (
        dropdown_options,
        fig,
        create_stats_row(stats, currency=target_currency),
        new_min_date,
        new_max_date,
        start_date,
        end_date,
        start_date,
        winners_table,
        losers_table,
        date_picker_style,
        button_styles["1m-button"],
        button_styles["6m-button"],
        button_styles["1y-button"],
        button_styles["3y-button"],
        button_styles["max-button"],
        button_styles["custom-button"],
    )


def _run_dev_server():
    """Run the development server for the dashboard application.

    Checks for the existence of portfolio files in the uploads directory before
    starting. Uses environment variable 'PORT' (defaults to 8050) and enables
    debug mode.

    Raises:
        SystemExit: If no portfolio files are found in the uploads directory
    """

    if not get_portfolio_files():
        log.error("No portfolio files found in the uploads directory.")
        log.error(f"Please add portfolio files to: {PORTFOLIO_UPLOADS_DIR}")
        sys.exit(1)
    app.run_server(host="0.0.0.0", port=int(os.getenv("PORT", "8050")), debug=True)


if __name__ == "__main__":
    _run_dev_server()
