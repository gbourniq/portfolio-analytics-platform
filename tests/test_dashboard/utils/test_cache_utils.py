"""
Caching utilities module for the Portfolio Analytics Dashboard.

This module provides utilities for caching and retrieving processed data to
improve dashboard performance. It implements efficient caching strategies
using file signatures and content hashing for optimal data retrieval.
"""

import hashlib
from pathlib import Path

import pandas as pd

from portfolio_analytics.common.utils.instruments import Currency
from portfolio_analytics.common.utils.logging_config import setup_logger

# Configure logging
log = setup_logger(__name__)


def get_dataframe_hash(df: pd.DataFrame) -> str:
    """Creates a deterministic hash of a DataFrame's contents."""
    # Sort index and columns for consistency
    df = df.sort_index()
    if isinstance(df.index, pd.MultiIndex):
        df = df.sort_index(level=list(range(df.index.nlevels)))

    # Convert array values to bytes before hashing
    hash_values = pd.util.hash_pandas_object(df, index=True).values
    return hashlib.sha1(bytes(hash_values)).hexdigest()


def quick_file_signature(file_path: Path) -> str:
    """
    Create a quick file signature using size and mtime.
    Much faster than computing hash, but less reliable if files are modified
    without changing mtime.
    """
    stats = file_path.stat()
    return f"{stats.st_size}_{stats.st_mtime_ns}"


def generate_cache_key(
    portfolio_path: Path, equity_path: Path, fx_path: Path, target_currency: Currency
) -> str:
    """
    Create a cache key based on the file signatures.

    Args:
        portfolio_path: Path to portfolio file
        equity_path: Path to equity prices file
        fx_path: Path to FX rates file

    Returns:
        str: SHA-1 hash to use as cache key
    """

    return hashlib.sha1(
        f"{quick_file_signature(portfolio_path)}|"
        f"{quick_file_signature(equity_path)}|"
        f"{quick_file_signature(fx_path)}|"
        f"{target_currency}".encode()
    ).hexdigest()
