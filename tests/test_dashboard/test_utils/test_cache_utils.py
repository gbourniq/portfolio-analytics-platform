"""Unit tests for cache utilities."""

from pathlib import Path
from unittest.mock import Mock

import pandas as pd
import pytest

from portfolio_analytics.dashboard.utils.cache_utils import (
    generate_cache_key,
    get_dataframe_hash,
    quick_file_signature,
)


@pytest.fixture
def sample_dataframe():
    """Returns a sample DataFrame for testing."""
    return pd.DataFrame({"A": [1, 2, 3], "B": ["a", "b", "c"]})


@pytest.fixture
def mock_file_path():
    """Returns a mocked Path with predefined stat values."""
    mock_path = Mock(spec=Path)
    mock_stat = Mock()
    mock_stat.st_size = 1000
    mock_stat.st_mtime_ns = 1234567890
    mock_path.stat.return_value = mock_stat
    return mock_path


class TestGetDataframeHash:
    """Unit tests for get_dataframe_hash function."""

    def test_simple_dataframe_hash(self, sample_dataframe):
        """Tests hash generation for a simple DataFrame."""
        # Given
        df = sample_dataframe

        # When
        result = get_dataframe_hash(df)

        # Then
        assert isinstance(result, str)
        assert len(result) == 40  # SHA-1 hash length

    @pytest.mark.parametrize("index_order", [[2, 1, 0], [1, 0, 2], [0, 2, 1]])
    def test_hash_consistency_with_different_index_orders(
        self, sample_dataframe, index_order
    ):
        """Tests if hash remains consistent regardless of index order."""
        # Given
        df = sample_dataframe
        reordered_df = df.iloc[index_order]

        # When
        original_hash = get_dataframe_hash(df)
        reordered_hash = get_dataframe_hash(reordered_df)

        # Then
        assert original_hash == reordered_hash


class TestQuickFileSignature:
    """Unit tests for quick_file_signature function."""

    def test_file_signature_format(self, mock_file_path):
        """Tests the format of the generated file signature."""
        # Given
        expected_signature = "1000_1234567890"

        # When
        result = quick_file_signature(mock_file_path)

        # Then
        assert result == expected_signature


class TestGenerateCacheKey:
    """Unit tests for generate_cache_key function."""

    def test_cache_key_generation(self, mock_file_path):
        """Tests generation of cache key from file paths and currency."""
        # Given
        portfolio_path = mock_file_path
        equity_path = mock_file_path
        fx_path = mock_file_path

        # When
        result = generate_cache_key(portfolio_path, equity_path, fx_path)

        # Then
        assert isinstance(result, str)
        assert len(result) == 40  # SHA-1 hash length

    def test_different_inputs_produce_different_keys(self, mock_file_path):
        """Tests that different inputs produce different cache keys."""
        # Given
        path1 = mock_file_path
        path2 = Mock(spec=Path)
        mock_stat2 = Mock()
        mock_stat2.st_size = 2000  # Different size
        mock_stat2.st_mtime_ns = 9876543210  # Different timestamp
        path2.stat.return_value = mock_stat2

        # When
        key1 = generate_cache_key(path1, path1, path1)
        key2 = generate_cache_key(path2, path2, path2)

        # Then
        assert key1 != key2
