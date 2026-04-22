"""Shared helpers for tool wrappers."""

from __future__ import annotations


def text_of_blocks(blocks: list) -> str:  # type: ignore[type-arg]
    """Flatten a list of ``mcp.types.TextContent`` blocks into a single string.

    Dispatch branches in ``ServiceNowKnowledgeMCP._dispatch`` return
    JSON-serialized or plain-text TextContent via ``_ok()``; concatenating
    ``.text`` yields the right payload for an MCP-tool return.
    """
    return "\n".join(getattr(b, "text", "") for b in blocks)
