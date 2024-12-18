"""
Custom exceptions module for the Portfolio Analytics Dashboard.
"""

from difflib import get_close_matches
from typing import List, Sequence


class MetricsCalculationError(Exception):
    """Base exception for performance calculation errors."""


class DataValidationError(MetricsCalculationError):
    """Base exception for data validation errors."""


class MissingTickersException(MetricsCalculationError):
    """Exception raised when tickers are missing from price data."""

    def __init__(self, missing_tickers: List[str], available_tickers: Sequence[str]):
        self.missing_tickers = missing_tickers
        self.available_tickers = available_tickers

        message = (
            "The following tickers are missing from "
            f"price data: {', '.join(missing_tickers)}.\n"
        )

        # Find suggestions for each missing ticker
        suggestions = {}
        for ticker in missing_tickers:
            close_matches = get_close_matches(ticker, available_tickers, n=1, cutoff=0.6)
            if close_matches:
                suggestions[ticker] = close_matches

        # Add suggestions to the message if any were found
        if suggestions:
            message += "\nDid you mean? "
            suggestion_list = [
                f"{ticker} → {', '.join(matches)}"
                for ticker, matches in suggestions.items()
            ]
            message += ", ".join(suggestion_list)

        super().__init__(message)
