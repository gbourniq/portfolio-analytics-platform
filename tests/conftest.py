"""This file defines pytest fixtures available for all tests."""

import uuid

import pytest


@pytest.fixture
def isolated_filesystem(tmp_path):
    """Create isolated filesystem directories for each test."""
    test_dir = tmp_path / f"test_{uuid.uuid4().hex[:8]}"
    test_dir.mkdir()

    samples_dir = test_dir / "samples"
    uploads_dir = test_dir / "uploads"
    market_data_dir = test_dir / "market_data"

    samples_dir.mkdir()
    uploads_dir.mkdir()
    market_data_dir.mkdir()

    return {
        "root": test_dir,
        "samples": samples_dir,
        "uploads": uploads_dir,
        "market_data": market_data_dir,
    }
