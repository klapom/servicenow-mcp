"""Unit tests for graph_traverse tool wrapper."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from servicenow_mcp.tools import graph as graph_mod


@pytest.fixture
def mock_kb(monkeypatch):
    kb = MagicMock()
    kb._dispatch.return_value = [SimpleNamespace(text="graph result")]
    monkeypatch.setattr(graph_mod, "get_knowledge", lambda: kb)
    return kb


async def test_graph_traverse_minimal(mock_kb):
    result = await graph_mod.graph_traverse("How does incident relate to task?")
    assert result == "graph result"
    mock_kb._dispatch.assert_called_once_with(
        "graph_traverse", {"question": "How does incident relate to task?"}
    )


async def test_graph_traverse_with_start_node(mock_kb):
    await graph_mod.graph_traverse("What tables extend this?", start_node="cmdb_ci")
    mock_kb._dispatch.assert_called_once_with(
        "graph_traverse",
        {"question": "What tables extend this?", "start_node": "cmdb_ci"},
    )


async def test_graph_traverse_empty_start_node_omitted(mock_kb):
    await graph_mod.graph_traverse("Q", start_node="")
    mock_kb._dispatch.assert_called_once_with("graph_traverse", {"question": "Q"})
