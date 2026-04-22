"""Unit tests for text_of_blocks helper."""

from __future__ import annotations

from types import SimpleNamespace

from servicenow_mcp.tools._serialize import text_of_blocks


def test_text_of_blocks_multi():
    blocks = [SimpleNamespace(text="a"), SimpleNamespace(text="b")]
    assert text_of_blocks(blocks) == "a\nb"


def test_text_of_blocks_empty():
    assert text_of_blocks([]) == ""


def test_text_of_blocks_block_without_text_attr():
    blocks = [SimpleNamespace(text="x"), SimpleNamespace(other="y")]
    # getattr default "" keeps it silent
    assert text_of_blocks(blocks) == "x\n"
