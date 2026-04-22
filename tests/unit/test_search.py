"""Unit tests for search_sn_docs tool wrapper."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from servicenow_mcp.tools import search as search_mod


@pytest.fixture
def mock_kb(monkeypatch):
    kb = MagicMock()
    kb._dispatch.return_value = [SimpleNamespace(text="chunk1\nchunk2")]
    monkeypatch.setattr(search_mod, "get_knowledge", lambda: kb)
    return kb


async def test_search_sn_docs_minimal(mock_kb):
    result = await search_mod.search_sn_docs("incident state")
    assert result == "chunk1\nchunk2"
    mock_kb._dispatch.assert_called_once_with(
        "search_sn_docs", {"query": "incident state", "limit": 10}
    )


async def test_search_sn_docs_with_limit(mock_kb):
    await search_mod.search_sn_docs("cmdb", limit=25)
    mock_kb._dispatch.assert_called_once_with("search_sn_docs", {"query": "cmdb", "limit": 25})


async def test_search_sn_docs_with_source_filter(mock_kb):
    await search_mod.search_sn_docs("GlideRecord", source_filter="api_reference")
    mock_kb._dispatch.assert_called_once_with(
        "search_sn_docs",
        {"query": "GlideRecord", "limit": 10, "source_filter": "api_reference"},
    )


async def test_search_sn_docs_none_source_filter_omitted(mock_kb):
    await search_mod.search_sn_docs("x", source_filter=None)
    mock_kb._dispatch.assert_called_once_with("search_sn_docs", {"query": "x", "limit": 10})
