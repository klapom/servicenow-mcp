"""Shared pytest fixtures."""

from __future__ import annotations

import pytest
from mcp_toolkit_py.logging import setup_logging


@pytest.fixture(autouse=True, scope="session")
def _silent_logs() -> None:
    """Avoid structlog printing to stdout during tests (pollutes captured output)."""
    setup_logging(level="error")
