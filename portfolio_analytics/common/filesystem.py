"""Utilities for file system operations and data file management.

This module provides functionality for managing portfolio files, cache, and dat
directories. It includes functions for reading different file formats, cleaning
up temporary files, and accessing market data and portfolio files.
"""

import io
from pathlib import Path
from typing import Final

import pandas as pd
import tomli

from portfolio_analytics.common.logging_config import setup_logger

# Configure logging
log = setup_logger(__name__)

DATA_DIR: Final[Path] = Path(__file__).parents[2] / "data"

MARKET_DATA_DIR: Final[Path] = DATA_DIR / "market_data"
FX_DATA_PATH: Final[Path] = MARKET_DATA_DIR / "fx.snappy.parquet"
EQUITY_FILE_PATH: Final[Path] = MARKET_DATA_DIR / "stocks.snappy.parquet"

PORTFOLIO_DIR: Final[Path] = DATA_DIR / "portfolios"
PORTFOLIO_UPLOADS_DIR: Final[Path] = PORTFOLIO_DIR / "uploads"
PORTFOLIO_SAMPLES_DIR: Final[Path] = PORTFOLIO_UPLOADS_DIR / "samples"
CACHE_DIR: Final[Path] = DATA_DIR / "cache"


# Read version from pyproject.toml
def get_version():
    """Read and return the package version from pyproject.toml.

    Returns:
        str: The version string from pyproject.toml, or '0.0.0' if reading fails
    """
    try:
        pyproject_path = Path(__file__).parents[2] / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            pyproject_data = tomli.load(f)
        return pyproject_data["tool"]["poetry"]["version"]
    except (FileNotFoundError, KeyError, tomli.TOMLDecodeError) as e:
        log.warning(f"Failed to read version from pyproject.toml: {e}")
        return "0.0.0"  # fallback version


def get_portfolio_files():
    """
    Scans the input directory for portfolio files with supported extensions.
    Returns sample files first, followed by other portfolio files.

    Returns:
        list[Path]: List of portfolio file paths, with sample files first
    """
    supported_extensions = (".csv", ".xlsx", ".parquet")

    # Get sample files first
    sample_files = [
        f
        for f in PORTFOLIO_SAMPLES_DIR.glob("*.*")
        if f.suffix.lower() in supported_extensions
    ]

    # Get root directory files
    root_files = [
        f
        for f in PORTFOLIO_UPLOADS_DIR.glob("*.*")
        if f.suffix.lower() in supported_extensions and f.parent == PORTFOLIO_UPLOADS_DIR
    ]

    return sorted(sample_files) + root_files


def cleanup_portfolio_uploads():
    """
    Deletes all files in the portfolio uploads directory,
    except for files in the samples subdirectory.
    """
    # Get all files in uploads directory (excluding samples directory)
    files_to_delete = [
        f
        for f in PORTFOLIO_UPLOADS_DIR.glob("*.*")
        if f.is_file() and f.parent == PORTFOLIO_UPLOADS_DIR
    ]

    # Delete each file
    for file in files_to_delete:
        try:
            file.unlink()
        except (PermissionError, FileNotFoundError) as e:
            log.error(f"Failed to delete {file}: {str(e)}")


def cleanup_cache():
    """
    Deletes all files in the cache directory.
    """
    for file in [f for f in CACHE_DIR.glob("*.*") if f.is_file()]:
        try:
            file.unlink()
        except (PermissionError, FileNotFoundError) as e:
            log.error(f"Failed to delete {file}: {str(e)}")


def read_portfolio_file(content: bytes, file_extension: str) -> pd.DataFrame:
    """Read portfolio file content into a pandas DataFrame based on file extension.

    Args:
        content: Raw file content in bytes
        file_extension: File extension (including the dot)

    Returns:
        pd.DataFrame: The loaded DataFrame

    Raises:
        ValueError: If the file extension is not supported
    """
    if file_extension.lower() == ".csv":
        return pd.read_csv(io.BytesIO(content))
    if file_extension.lower() == ".xlsx":
        return pd.read_excel(io.BytesIO(content), header=1)
    if file_extension.lower() == ".parquet":
        return pd.read_parquet(io.BytesIO(content))
    raise ValueError(f"Unsupported file extension: {file_extension}")
