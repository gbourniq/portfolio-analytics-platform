"""
Dashboard UI components module for the Portfolio Analytics Dashboard.

This module provides reusable UI components and helper functions for creating
and styling various dashboard elements.
"""

import datetime as dtm

import dash_bootstrap_components as dbc
import plotly.express as px
from dash import html

from portfolio_analytics.common.utils.instruments import Currency
from portfolio_analytics.dashboard.app.layout import STYLES


def get_currency_symbol(currency: Currency) -> str:
    """Returns the appropriate currency symbol for a given currency."""
    symbols = {Currency.USD: "$", Currency.EUR: "€", Currency.GBP: "£"}
    return symbols.get(currency, "$")


def create_pnl_figure(df_plot, pnl_column):
    """
    Creates a styled line chart for PnL visualization.

    Args:
        df_plot (pd.DataFrame): DataFrame containing Date and PnL columns
        pnl_column (str): Column name for PnL values to plot

    Returns:
        plotly.graph_objects.Figure: Styled line chart
    """
    fig = px.line(df_plot, x="Date", y=pnl_column)
    fig.update_layout(xaxis_title="", yaxis_title="", showlegend=False)
    fig.update_traces(
        fill="tozeroy", fillcolor="rgba(0,100,80,0.2)", line_color="rgb(0,100,80)"
    )
    return fig


def create_stats_row(stats, currency=Currency.USD):
    """
    Creates a Bootstrap row containing performance statistics.

    Args:
        stats (NamedTuple): Contains performance metrics
            (max_drawdown, sharpe_ratio, etc.)
        currency (Currency): The currency to display values in

    Returns:
        dash_bootstrap_components.Row: Row component with formatted statistics
    """
    symbol = get_currency_symbol(currency)
    stats_components = [
        ("MAX DRAWDOWN", f"-{symbol}{abs(stats.max_drawdown):,.2f}"),
        ("SHARPE", f"{stats.sharpe_ratio:.2f}"),
        (
            "PERIOD PNL",
            f"{'-' if stats.period_pnl < 0 else ''}{symbol}{abs(stats.period_pnl):,.2f}",
        ),
    ]

    return dbc.Row(
        [
            dbc.Col(
                [
                    html.Div(
                        [
                            html.P(label, style=STYLES["stats_title"]),
                            html.P(value, style=STYLES["stats_value"]),
                        ],
                        style=STYLES["stats_col"],
                    )
                ],
                width=4,
            )
            for label, value in stats_components
        ]
    )


def add_drawdown_indicators(fig, stats, start_date, end_date):
    """Adds drawdown indicators to the PnL figure."""
    if (
        stats.drawdown_start_date
        and stats.max_drawdown_date
        and start_date <= stats.drawdown_start_date <= end_date
        and start_date <= stats.max_drawdown_date <= end_date
    ):
        fig.add_vline(
            x=dtm.datetime.combine(stats.drawdown_start_date, dtm.time()).timestamp()
            * 1000,
            line_width=1,
            line_dash="dash",
            line_color="rgba(255, 0, 0, 0.3)",
            annotation_text="Drawdown Start",
            annotation_position="top",
            annotation=dict(textangle=-45, font=dict(size=10)),
        )
        fig.add_vline(
            x=dtm.datetime.combine(stats.max_drawdown_date, dtm.time()).timestamp()
            * 1000,
            line_width=1,
            line_dash="dash",
            line_color="rgba(255, 0, 0, 0.3)",
            annotation_text="Max Drawdown",
            annotation_position="top",
            annotation=dict(textangle=-45, font=dict(size=10)),
        )
        fig.update_layout(margin=dict(t=70))


def create_performance_table(df, is_positive=True, currency=Currency.USD):
    """
    Creates a styled table for winners or losers.

    Args:
        df (pd.DataFrame): DataFrame containing performance data
        is_positive (bool): True for winners, False for losers
        currency (Currency): The currency to display values in

    Returns:
        dash_bootstrap_components.Table: Styled table component
    """
    if df.empty:
        return html.P("No data available")

    color_class = "success" if is_positive else "danger"
    symbol = get_currency_symbol(currency)

    return html.Div(
        dbc.Table(
            [
                html.Thead(
                    html.Tr(
                        [
                            html.Th("Ticker", style={"width": "40%"}),
                            html.Th(
                                f"Return ({symbol})",
                                className="text-end",
                                style={"width": "60%"},
                            ),
                        ],
                        className=f"table-{color_class}",
                    )
                ),
                html.Tbody(
                    [
                        html.Tr(
                            [
                                html.Td(row["symbol"]),
                                html.Td(
                                    f"{symbol}{row['pnl']:,.2f}",
                                    className="text-end",
                                ),
                            ]
                        )
                        for _, row in df.iterrows()
                    ]
                ),
            ],
            bordered=True,
            hover=True,
            size="sm",
            className="mb-4",
        ),
        style={"maxWidth": "300px", "margin": "0 auto", "display": "block"},
    )


def create_error_state(dropdown_options, error_message):
    """
    Creates a consistent error state for all dashboard components.

    Args:
        dropdown_options (list): List of portfolio dropdown options to preserve
        error_message (str): Error message to display

    Returns:
        tuple: Contains error states for all dashboard components
    """
    error_fig = px.line()
    error_fig.update_layout(
        title={"text": error_message, "x": 0.5, "xanchor": "center", "yanchor": "top"},
        font={"color": "red"},
    )

    error_div = html.Div(
        "Unable to calculate statistics due to missing data",
        style={"color": "red", "text-align": "center", "padding": "20px"},
    )

    no_data_div = html.Div(
        "No data available", style={"color": "red", "text-align": "center"}
    )

    # Default date for date range
    default_date = dtm.datetime.now().date()

    # Default button styles (all inactive)
    button_styles = {
        "1m-button": STYLES["button_inactive"].copy(),
        "6m-button": STYLES["button_inactive"].copy(),
        "1y-button": STYLES["button_inactive"].copy(),
        "3y-button": STYLES["button_inactive"].copy(),
        "max-button": STYLES["button_inactive"].copy(),
        "custom-button": STYLES["button_inactive"].copy(),
    }

    return (
        dropdown_options,  # Keep dropdown options
        error_fig,  # Show error message in graph
        error_div,  # Error message in stats
        default_date,  # date-range min_date_allowed
        default_date,  # date-range max_date_allowed
        default_date,  # date-range start_date
        default_date,  # date-range end_date
        default_date,  # date-range initial_visible_month
        no_data_div,  # Winners table error message
        no_data_div,  # Losers table error message
        {"display": "none"},  # date-range style
        button_styles["1m-button"],  # 1m-button style
        button_styles["6m-button"],  # 6m-button style
        button_styles["1y-button"],  # 1y-button style
        button_styles["3y-button"],  # 3y-button style
        button_styles["max-button"],  # max-button style
        button_styles["custom-button"],  # custom-button style
    )
