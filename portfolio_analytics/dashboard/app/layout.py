"""
Dashboard layout configuration module for the Portfolio Analytics Dashboard.

This module defines the main layout structure and styling configuration for the
dashboard.
"""

import dash_bootstrap_components as dbc
from dash import dcc, html

from portfolio_analytics.common.filesystem import get_portfolio_files, get_version
from portfolio_analytics.common.instruments import Currency

# Styles configuration
STYLES = {
    "stats_col": {
        "textAlign": "center",
        "display": "flex",
        "flexDirection": "column",
        "alignItems": "center",
    },
    "stats_title": {
        "fontFamily": "Arial, sans-serif",
        "fontSize": "14px",
        "fontWeight": "bold",
        "margin": "0",
        "color": "#666",
        "textTransform": "uppercase",
        "letterSpacing": "1px",
    },
    "stats_value": {
        "fontFamily": "Roboto Mono, monospace",
        "fontSize": "24px",
        "fontWeight": "bold",
        "margin": "0",
        "color": "#333",
    },
    "divider": {
        "borderTop": "1px solid #dee2e6",
        "width": "80%",
        "margin": "auto",
        "opacity": "0.5",
    },
    "dropdown": {
        "width": "250px",
        "backgroundColor": "white",
        "borderRadius": "8px",
        "fontWeight": "500",
    },
    "button_active": {
        "background-color": "#2C3E50",  # Darker shade for active button
        "color": "white",
        "border-color": "#2C3E50",
    },
    "button_inactive": {
        "background-color": "#95a5a6",  # Lighter shade for inactive buttons
        "color": "white",
        "border-color": "#95a5a6",
    },
    "title": {
        "fontSize": "2.5rem",
        "fontWeight": "600",
        "background": "linear-gradient(120deg, #2C3E50, #3498db)",
        "WebkitBackgroundClip": "text",
        "WebkitTextFillColor": "transparent",
        "letterSpacing": "0.5px",
        "marginBottom": "0.5rem",
        "fontFamily": (
            "'Segoe UI', -apple-system, BlinkMacSystemFont, 'Roboto', sans-serif"
        ),
        "paddingBottom": "0.5rem",
        "width": "100%",
        "textAlign": "center",
    },
    "description": {
        "fontSize": "1rem",
        "color": "#666",
        "textAlign": "center",
        "marginBottom": "1rem",
        "fontFamily": (
            "'Segoe UI', -apple-system, BlinkMacSystemFont, 'Roboto', sans-serif"
        ),
    },
    "api_link": {
        "fontSize": "0.9rem",
        "color": "#3498db",
        "textDecoration": "none",
        "textAlign": "center",
        "marginBottom": "1rem",
        "fontFamily": (
            "'Segoe UI', -apple-system, BlinkMacSystemFont, 'Roboto', sans-serif"
        ),
    },
    "version": {
        "fontSize": "0.7rem",
        "color": "#95a5a6",
        "position": "fixed",
        "bottom": "10px",
        "right": "15px",
        "fontFamily": "'Segoe UI', sans-serif",
        "opacity": "0.7",
    },
}


def create_layout(app):
    """Create the layout for the dashboard application."""
    app.layout = dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.Label(
                                        "ACTIVE PORTFOLIO:",
                                        style={
                                            "fontSize": "12px",
                                            "fontWeight": "bold",
                                            "color": "#666",
                                            "marginBottom": "4px",
                                            "textTransform": "uppercase",
                                            "letterSpacing": "1px",
                                        },
                                    ),
                                    dcc.Dropdown(
                                        id="portfolio-selector",
                                        options=[
                                            {"label": f.name, "value": str(f)}
                                            for f in get_portfolio_files()
                                        ],
                                        value=str(get_portfolio_files()[0]),
                                        clearable=False,
                                        style=STYLES["dropdown"],
                                        className="custom-dropdown",
                                    ),
                                ]
                            ),
                        ],
                        width=2,
                    ),
                    dbc.Col(
                        [
                            html.H1(
                                "Portfolio Analytics Dashboard", style=STYLES["title"]
                            ),
                            html.P(
                                "Interactive visualization of portfolio performance"
                                " metrics.",
                                style=STYLES["description"],
                            ),
                            html.Div(
                                html.A(
                                    "Manage Portfolios & Load Market Data via API →",
                                    href="https://api.portfolio-analytics.click/docs",
                                    target="_blank",
                                    style=STYLES["api_link"],
                                ),
                                style={"textAlign": "center"},
                            ),
                        ],
                        width=8,
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.Label(
                                        "CURRENCY:",
                                        style={
                                            "fontSize": "12px",
                                            "fontWeight": "bold",
                                            "color": "#666",
                                            "marginBottom": "4px",
                                            "textTransform": "uppercase",
                                            "letterSpacing": "1px",
                                        },
                                    ),
                                    dcc.Dropdown(
                                        id="currency-selector",
                                        options=[
                                            {
                                                "label": currency.name,
                                                "value": currency.name,
                                            }
                                            for currency in Currency
                                        ],
                                        value=Currency.USD.name,
                                        clearable=False,
                                        style=STYLES["dropdown"],
                                        className="custom-dropdown",
                                    ),
                                ]
                            ),
                        ],
                        width=2,
                    ),
                ],
                style={"margin-bottom": "5rem"},
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Hr(style=STYLES["divider"]),
                            dcc.Loading(
                                id="loading-stats",
                                children=[
                                    html.Div(
                                        id="stats-display", style={"margin": "2rem 0"}
                                    )
                                ],
                                type="circle",
                                color="#119DFF",
                                style={"marginTop": "20px"},
                            ),
                            html.Hr(style=STYLES["divider"]),
                        ],
                        style={"margin-bottom": "5rem"},
                    )
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    dbc.ButtonGroup(
                                        [
                                            dbc.Button(
                                                "1M",
                                                id="1m-button",
                                                style=STYLES["button_inactive"],
                                            ),
                                            dbc.Button(
                                                "6M",
                                                id="6m-button",
                                                style=STYLES["button_inactive"],
                                            ),
                                            dbc.Button(
                                                "1Y",
                                                id="1y-button",
                                                style=STYLES["button_inactive"],
                                            ),
                                            dbc.Button(
                                                "3Y",
                                                id="3y-button",
                                                style=STYLES["button_inactive"],
                                            ),
                                            dbc.Button(
                                                "MAX",
                                                id="max-button",
                                                style=STYLES["button_active"],
                                            ),
                                            dbc.Button(
                                                "Custom",
                                                id="custom-button",
                                                style=STYLES["button_inactive"],
                                            ),
                                        ],
                                        className="mb-2",
                                    ),
                                    dcc.DatePickerRange(
                                        id="date-range",
                                        min_date_allowed="2024-01-01",  # Dummy value
                                        max_date_allowed="2024-12-31",
                                        initial_visible_month="2024-01-01",
                                        start_date="2024-01-01",
                                        end_date="2024-12-31",
                                        className="mb-2",
                                        style={"display": "none"},  # Hidden by default
                                        display_format="DD/MM/YYYY",
                                    ),
                                ]
                            ),
                        ],
                        width=3,
                        className="offset-8 d-flex justify-content-end",
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dcc.Loading(
                                id="loading-graph",
                                children=[dcc.Graph(id="pnl-graph")],
                                type="circle",
                                color="#119DFF",
                                style={"marginTop": "20px"},
                            )
                        ]
                    )
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H4(
                                "Top Winners", className="text-success mb-3 text-center"
                            ),
                            dcc.Loading(
                                id="loading-winners",
                                children=[
                                    html.Div(
                                        id="winners-table", className="table-responsive"
                                    )
                                ],
                                type="circle",
                                color="#119DFF",
                                style={"marginTop": "20px"},
                            ),
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            html.H4(
                                "Top Losers", className="text-danger mb-3 text-center"
                            ),
                            dcc.Loading(
                                id="loading-losers",
                                children=[
                                    html.Div(
                                        id="losers-table", className="table-responsive"
                                    )
                                ],
                                type="circle",
                                color="#119DFF",
                                style={"marginTop": "20px"},
                            ),
                        ],
                        width=6,
                    ),
                ],
                className="mt-4",
            ),
        ],
        fluid=True,
        className="p-4",
    )

    app.index_string = (
        """
    <!DOCTYPE html>
    <html>
        <head>
            {%metas%}
            <title>{%title%}</title>
            {%favicon%}
            {%css%}
        </head>
        <body>
            {%app_entry%}
            <footer>
                <div id="version">v"""
        + get_version()
        + """</div>
                {%config%}
                {%scripts%}
                {%renderer%}
            </footer>
            <style>
                #version {"""
        + "; ".join(f"{k}: {v}" for k, v in STYLES["version"].items())
        + """}
            </style>
        </body>
    </html>
    """
    )

    return app
