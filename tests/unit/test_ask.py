"""Unit tests for ask_sn_knowledge tool wrapper."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from servicenow_mcp.tools import ask as ask_mod


@pytest.fixture
def mock_kb(monkeypatch):
    kb = MagicMock()
    kb._dispatch.return_value = [SimpleNamespace(text="mocked answer")]
    monkeypatch.setattr(ask_mod, "get_knowledge", lambda: kb)
    return kb


async def test_ask_sn_knowledge_minimal(mock_kb):
    result = await ask_mod.ask_sn_knowledge("What is the incident table?")
    assert result == "mocked answer"
    mock_kb._dispatch.assert_called_once_with(
        "ask_sn_knowledge", {"question": "What is the incident table?"}
    )


async def test_ask_sn_knowledge_with_hint(mock_kb):
    await ask_mod.ask_sn_knowledge("How to script a business rule?", context_hint="scripting")
    mock_kb._dispatch.assert_called_once_with(
        "ask_sn_knowledge",
        {"question": "How to script a business rule?", "context_hint": "scripting"},
    )


async def test_ask_sn_knowledge_empty_hint_omitted(mock_kb):
    """Empty string hint should not be forwarded — avoids unwanted empty-filter behavior."""
    await ask_mod.ask_sn_knowledge("Q", context_hint="")
    mock_kb._dispatch.assert_called_once_with("ask_sn_knowledge", {"question": "Q"})
