"""
Main application module for the Portfolio Analytics Dashboard.

This module serves as the entry point for the dashboard application. It initializes
the Dash application, sets up callbacks for interactivity, and handles the main
application logic for updating the dashboard based on user interactions and
data changes.
"""

import datetime as dtm
import os
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
from portfolio_analytics.dashboard.core.data_loader import prepare_positions_prices_data
from portfolio_analytics.dashboard.core.pnl import calculate_pnl
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


# Callback to update the graph and stats
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
        Input("pnl-type-selector", "value"),
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
def update_graph(
    portfolio_name,
    pnl_type,
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
    ctx = dash.callback_context
    date_picker_style = {"display": "none"}

    # Load data first to get valid date ranges
    target_currency = Currency[currency]
    portfolio_files = get_portfolio_files()
    dropdown_options = [{"label": f.name, "value": str(f)} for f in portfolio_files]

    try:
        prepared_data = prepare_positions_prices_data(
            Path(portfolio_name),
            EQUITY_FILE_PATH,
            FX_DATA_PATH,
            target_currency=target_currency,
        )
    except Exception as e:
        return create_error_state(dropdown_options, str(e))

    pnl_df = calculate_pnl(prepared_data)

    # Get valid date range from the PnL dataframe
    new_min_date = pnl_df.index.min()
    new_max_date = pnl_df.index.max()

    # Initialize all buttons as inactive
    button_styles = {
        "1m-button": STYLES["button_inactive"].copy(),
        "6m-button": STYLES["button_inactive"].copy(),
        "1y-button": STYLES["button_inactive"].copy(),
        "3y-button": STYLES["button_inactive"].copy(),
        "max-button": STYLES["button_active"].copy(),
        "custom-button": STYLES["button_inactive"].copy(),
    }

    # Handle button clicks or portfolio changes
    if ctx.triggered:
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # Set active button based on which was clicked
        if button_id in button_styles:
            # Reset all buttons to inactive first
            for key in button_styles:
                button_styles[key] = STYLES["button_inactive"].copy()
            # Set clicked button to active
            button_styles[button_id] = STYLES["button_active"].copy()

        # Handle portfolio, currency, and pnl-type changes
        if button_id in [
            "portfolio-selector",
            "currency-selector",
            "pnl-type-selector",
        ]:
            start_date = new_min_date
            end_date = new_max_date
            # Reset all buttons to inactive first
            for key in button_styles:
                button_styles[key] = STYLES["button_inactive"].copy()
            # Set MAX button to active
            button_styles["max-button"] = STYLES["button_active"].copy()

        elif button_id in [
            "1m-button",
            "6m-button",
            "1y-button",
            "3y-button",
            "max-button",
        ]:
            # Handle date range button clicks
            current_date = dtm.datetime.now().date()
            end_date = min(current_date, new_max_date)

            if button_id == "1m-button":
                start_date = max(end_date - relativedelta(months=1), new_min_date)
            elif button_id == "6m-button":
                start_date = max(end_date - relativedelta(months=6), new_min_date)
            elif button_id == "1y-button":
                start_date = max(end_date - relativedelta(years=1), new_min_date)
            elif button_id == "3y-button":
                start_date = max(end_date - relativedelta(years=3), new_min_date)
            elif button_id == "max-button":
                start_date = new_min_date
                end_date = new_max_date

        elif button_id == "custom-button":
            date_picker_style = {"display": "block"}

        elif button_id in ["date-range"]:
            # When dates are selected via date picker
            button_styles["custom-button"] = STYLES["button_active"].copy()
            date_picker_style = {"display": "block"}

    # If custom dates are being used (date picker is visible), keep custom button active
    if date_picker_style["display"] == "block":
        button_styles["custom-button"] = STYLES["button_active"].copy()

    # Convert string dates to datetime objects if they're strings
    if isinstance(start_date, str):
        start_date = dtm.datetime.strptime(start_date, "%Y-%m-%d").date()
    if isinstance(end_date, str):
        end_date = dtm.datetime.strptime(end_date, "%Y-%m-%d").date()

    # Ensure dates are within valid range
    start_date = max(start_date, new_min_date)
    end_date = min(end_date, new_max_date)

    # Prepare and filter data
    df_plot = pnl_df.reset_index()
    df_plot = df_plot[(df_plot["Date"] >= start_date) & (df_plot["Date"] <= end_date)]

    # Create figure with selected PnL type
    pnl_column = "pnl_realised" if pnl_type == "realized" else "pnl_unrealised"
    fig = create_pnl_figure(df_plot, pnl_column)

    # Calculate and add drawdown indicators
    stats = calculate_stats(
        pnl_df,
        use_realized=(pnl_type == "realized"),
        start_date=start_date,
        end_date=end_date,
    )
    add_drawdown_indicators(fig, stats, start_date, end_date)

    # Get winners and losers
    winners, losers = get_winners_and_losers(
        prepared_data, start_date=start_date, end_date=end_date
    )

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
    """Run the development server"""
    if not get_portfolio_files():
        log.error("No portfolio files found in the uploads directory.")
        log.error(f"Please add portfolio files to: {PORTFOLIO_UPLOADS_DIR}")
        exit(1)
    app.run_server(host="0.0.0.0", port=int(os.getenv("PORT", "8050")), debug=True)


if __name__ == "__main__":
    _run_dev_server()
