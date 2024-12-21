"""Unit tests for filesystem utilities."""

import io
from pathlib import Path
from typing import List
from unittest.mock import patch

import pandas as pd
import pytest
import tomli_w

from portfolio_analytics.common.filesystem import (
    cleanup_cache,
    cleanup_portfolio_uploads,
    get_portfolio_files,
    get_version,
    read_portfolio_file,
)

FILESYSTEM_MODULE = "portfolio_analytics.common.filesystem"


def _to_csv_bytes(df):
    return df.to_csv(index=False).encode()


def _to_parquet_bytes(df):
    buffer = io.BytesIO()
    df.to_parquet(buffer)
    return buffer.getvalue()


@pytest.fixture
def mock_filesystem_paths(tmp_path):
    """Fixture to mock filesystem paths."""
    samples_dir = tmp_path / "samples"
    uploads_dir = tmp_path / "uploads"
    cache_dir = tmp_path / "cache"

    samples_dir.mkdir()
    uploads_dir.mkdir()
    cache_dir.mkdir()

    with patch(f"{FILESYSTEM_MODULE}.PORTFOLIO_SAMPLES_DIR", samples_dir), patch(
        f"{FILESYSTEM_MODULE}.PORTFOLIO_UPLOADS_DIR", uploads_dir
    ), patch(f"{FILESYSTEM_MODULE}.CACHE_DIR", cache_dir):
        yield samples_dir, uploads_dir, cache_dir


class TestGetVersion:
    """Tests for get_version function."""

    def test_get_version_success(self, tmp_path):
        """Tests successful version retrieval from pyproject.toml."""
        # Given
        mock_toml = {"tool": {"poetry": {"version": "1.0.0"}}}
        mock_path = tmp_path / "pyproject.toml"
        with open(mock_path, "wb") as f:
            tomli_w.dump(mock_toml, f)

        with patch.object(Path, "parents", property(lambda x: [None, None, tmp_path])):
            # When
            version = get_version()

            # Then
            assert version == "1.0.0"

    def test_get_version_file_not_found(self):
        """Tests fallback version when pyproject.toml is not found."""
        with patch.object(
            Path, "parents", property(lambda x: [None, None, Path("/nonexistent")])
        ):
            # When
            version = get_version()

            # Then
            assert version == "0.0.0"


class TestGetPortfolioFiles:
    """Tests for get_portfolio_files function."""

    @pytest.mark.parametrize(
        "sample_files, upload_files, expected_order",
        [
            (["test1.csv"], [], ["test1.csv"]),
            ([], ["file1.xlsx"], ["file1.xlsx"]),
            (
                ["sample1.csv", "sample2.xlsx"],
                ["upload1.parquet"],
                ["sample1.csv", "sample2.xlsx", "upload1.parquet"],
            ),
        ],
    )
    def test_get_portfolio_files_ordering(
        self,
        mock_filesystem_paths,
        sample_files: List[str],
        upload_files: List[str],
        expected_order: List[str],
    ):
        """Tests portfolio files are returned in correct order."""
        # Given
        samples_dir, uploads_dir, _ = mock_filesystem_paths

        for file in sample_files:
            (samples_dir / file).touch()
        for file in upload_files:
            (uploads_dir / file).touch()

        # When
        result = get_portfolio_files()

        # Then
        assert [p.name for p in result] == expected_order


class TestCleanupFunctions:
    """Tests for cleanup functions."""

    def test_cleanup_portfolio_uploads(self, mock_filesystem_paths):
        """Tests cleanup of portfolio uploads directory."""
        # Given
        samples_dir, uploads_dir, _ = mock_filesystem_paths
        test_file = uploads_dir / "test.csv"
        sample_file = samples_dir / "sample.csv"
        test_file.touch()
        sample_file.touch()

        # When
        cleanup_portfolio_uploads()

        # Then
        assert not test_file.exists()
        assert sample_file.exists()

    def test_cleanup_cache(self, mock_filesystem_paths):
        """Tests cleanup of cache directory."""
        # Given
        _, _, cache_dir = mock_filesystem_paths
        cache_file = cache_dir / "cache.tmp"
        cache_file.touch()

        # When
        cleanup_cache()

        # Then
        assert not cache_file.exists()


class TestReadPortfolioFile:
    """Tests for read_portfolio_file function."""

    @pytest.mark.parametrize(
        "extension,content,expected_df",
        [
            (
                ".csv",
                _to_csv_bytes(pd.DataFrame({"col1": [1], "col2": [2]})),
                pd.DataFrame({"col1": [1], "col2": [2]}),
            ),
            (
                ".parquet",
                _to_parquet_bytes(pd.DataFrame({"col1": [1], "col2": [2]})),
                pd.DataFrame({"col1": [1], "col2": [2]}),
            ),
        ],
    )
    def test_read_portfolio_file_formats(
        self, extension: str, content: bytes, expected_df: pd.DataFrame
    ):
        """Tests reading different portfolio file formats."""
        # Given
        file_content = content

        # When
        result = read_portfolio_file(file_content, extension)

        # Then
        pd.testing.assert_frame_equal(result, expected_df)

    def test_read_portfolio_file_invalid_extension(self):
        """Tests error handling for unsupported file extensions."""
        # Given
        content = b"some content"
        extension = ".txt"

        # When/Then
        with pytest.raises(ValueError, match="Unsupported file extension"):
            read_portfolio_file(content, extension)
