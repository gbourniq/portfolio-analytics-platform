"""Common utilities and configurations for the Portfolio Analytics API."""

import os
from enum import Enum
from typing import List

URL_PREFIX = os.environ.get("PORTFOLIO_ANALYTICS_PREFIX_URL", "")

CORS_ORIGIN_DOMAINS = os.environ.get("CORS_ORIGIN_DOMAINS", "*")


class ApiTagBase(Enum):
    """Base enumeration class for API tag management.

    Provides common functionality for converting tags to strings and generating
    OpenAPI documentation tags.
    """

    def __str__(self) -> str:
        return str(self.value["name"])

    @classmethod
    def get_openapi_tags(cls) -> List[dict]:
        """Return openapi_tags"""
        return [m.value for m in dict(cls.__members__).values()]


class ApiTag(ApiTagBase):
    MARKET_DATA = {
        "name": "Market Data",
        "description": (
            "Operations to trigger and manage market data pipelines for FX and Equity"
            " data."
        ),
    }
    PORTFOLIO_MANAGEMENT = {
        "name": "Portfolio Management",
        "description": (
            "Operations to manage portfolio files including creation, listing, "
            "deleting and downloading."
        ),
    }
