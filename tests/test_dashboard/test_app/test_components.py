"""Unit tests for dashboard UI components."""

import datetime as dtm
from collections import namedtuple

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import pytest
from dash import html

from portfolio_analytics.common.instruments import Currency
from portfolio_analytics.dashboard.app.components import (
    create_performance_table,
    create_pnl_figure,
    create_stats_row,
    get_currency_symbol,
)


@pytest.mark.parametrize(
    "currency,expected_symbol",
    [
        (Currency.USD, "$"),
        (Currency.EUR, "€"),
        (Currency.GBP, "£"),
        ("UNKNOWN", "$"),
    ],
)
def test_get_currency_symbol(currency, expected_symbol):
    """Verifies currency symbol mapping for different currencies."""
    # When
    symbol = get_currency_symbol(currency)

    # Then
    assert symbol == expected_symbol


def test_create_pnl_figure():
    """Verifies PnL figure creation with correct styling."""
    # Given
    df = pd.DataFrame(
        {
            "Date": [dtm.date(2023, 1, 1), dtm.date(2023, 1, 2)],
            "PnL": [100.0, 150.0],
        }
    )

    # When
    fig = create_pnl_figure(df)

    # Then
    assert isinstance(fig, go.Figure)
    assert fig.layout.xaxis.title.text == ""
    assert fig.layout.yaxis.title.text == ""
    assert not fig.layout.showlegend


def test_create_stats_row():
    """Verifies stats row creation with formatted values."""
    # Given
    Stats = namedtuple("Stats", ["max_drawdown", "sharpe_ratio", "period_pnl"])
    stats = Stats(max_drawdown=-1000.0, sharpe_ratio=2.5, period_pnl=5000.0)

    # When
    row = create_stats_row(stats, Currency.USD)

    # Then
    assert isinstance(row, dbc.Row)
    assert len(row.children) == 3  # Three columns
    assert "$1,000.00" in str(row.children[0].children[0].children[1].children)
    assert "2.50" in str(row.children[1].children[0].children[1].children)
    assert "$5,000.00" in str(row.children[2].children[0].children[1].children)


@pytest.mark.parametrize(
    "df_data,is_positive,currency,expected_values",
    [
        (
            pd.DataFrame({"symbol": ["AAPL"], "pnl": [100.0]}),
            True,
            Currency.USD,
            {"symbol": "AAPL", "value": "100.00", "currency": "$"},
        ),
        (
            pd.DataFrame({"symbol": ["GOOGL"], "pnl": [-50.0]}),
            False,
            Currency.EUR,
            {"symbol": "GOOGL", "value": "50.00", "currency": "€"},
        ),
    ],
)
def test_create_performance_table(df_data, is_positive, currency, expected_values):
    """Verifies performance table creation with different scenarios."""
    # When
    table = create_performance_table(df_data, is_positive, currency)
    table_str = str(table)

    # Then
    assert isinstance(table, html.Div)
    # Check individual components instead of exact string
    assert expected_values["symbol"] in table_str
    assert expected_values["value"] in table_str
    assert expected_values["currency"] in table_str
    color_class = "success" if is_positive else "danger"
    assert f"table-{color_class}" in table_str


def test_create_performance_table_empty():
    """Verifies performance table handling of empty data."""
    # Given
    df_empty = pd.DataFrame()

    # When
    result = create_performance_table(df_empty)

    # Then
    assert isinstance(result, html.P)
    assert "No data available" in str(result)
