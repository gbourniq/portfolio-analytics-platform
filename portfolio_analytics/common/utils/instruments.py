"""Financial instruments and asset class definitions.

This module defines enumerations for various financial instruments and asset classes
used throughout the portfolio analytics system. It provides standardized identifiers
for currencies, stock indices, and other financial instruments.

The enumerations ensure consistent representation of financial instruments across
the application.
"""

from enum import Enum


class Instrument(Enum):
    """Base class for all instruments."""


class Currency(Instrument):
    """Available currencies."""

    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"


class StockIndex(Instrument):
    """Available stock indices."""

    SP500 = "SP500"
    FTSE100 = "FTSE100"
    EUROSTOXX50 = "EUROSTOXX50"
