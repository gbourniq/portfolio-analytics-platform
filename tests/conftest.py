"""This file defines pytest fixtures available for all tests."""

import datetime as dtm
import uuid

import pytest


@pytest.fixture(autouse=True)
def any_timestamp():
    """A fixture that checks if the compared value is a valid iso timestamp"""

    class AnyTimestamp:
        value = None

        def __eq__(self, other):
            try:
                dtm.datetime.fromisoformat(other)
                self.value = other
                return True
            except ValueError:
                self.value = f"<Invalid timestamp: {other}>"
                return False

        def __repr__(self):
            return str(self.value) if self.value else super().__repr__()

    return AnyTimestamp()


@pytest.fixture(autouse=True)
def any_string():
    """A fixture that checks if the compared value is a string"""

    class AnyString:
        value = None

        def __eq__(self, other):
            try:
                assert isinstance(other, str)
                self.value = other
                return True
            except AssertionError:
                self.value = f"<Invalid string: {other}>"
                return False

        def __repr__(self):
            return str(self.value) if self.value else super().__repr__()

    return AnyString()


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
