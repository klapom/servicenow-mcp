"""Unit tests for lookup_table tool wrapper."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from servicenow_mcp.tools import lookup as lookup_mod


@pytest.fixture
def mock_kb(monkeypatch):
    kb = MagicMock()
    kb._dispatch.return_value = [SimpleNamespace(text="table schema")]
    monkeypatch.setattr(lookup_mod, "get_knowledge", lambda: kb)
    return kb


async def test_lookup_table_minimal(mock_kb):
    result = await lookup_mod.lookup_table("incident")
    assert result == "table schema"
    mock_kb._dispatch.assert_called_once_with("lookup_table", {"table_name": "incident"})


async def test_lookup_table_with_field(mock_kb):
    await lookup_mod.lookup_table("change_request", field_name="type")
    mock_kb._dispatch.assert_called_once_with(
        "lookup_table", {"table_name": "change_request", "field_name": "type"}
    )


async def test_lookup_table_empty_field_omitted(mock_kb):
    await lookup_mod.lookup_table("sys_user", field_name="")
    mock_kb._dispatch.assert_called_once_with("lookup_table", {"table_name": "sys_user"})
