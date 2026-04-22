"""search_sn_docs tool — Raw chunk search over ServiceNow knowledge base.

Thin wrapper delegating to
``ServiceNowKnowledgeMCP._dispatch("search_sn_docs", ...)``.
Returns retrieval chunks with scores, no LLM synthesis.
"""

from __future__ import annotations

from typing import Literal

from servicenow_mcp.server import get_knowledge, mcp
from servicenow_mcp.tools._serialize import text_of_blocks


@mcp.tool(name="search_sn_docs")
async def search_sn_docs(
    query: str,
    limit: int = 10,
    source_filter: Literal["process", "training", "api_reference", "handbook", "customizing"]
    | None = None,
) -> str:
    """Durchsucht die ServiceNow-Dokumentation ohne LLM-Synthese.

    Liefert rohe Chunks mit Scores. `source_filter` engt auf eine Quelle ein:
    `'process'` (ITIL-Prozessdocs), `'training'` (Schulungen),
    `'api_reference'` (REST/GlideRecord), `'handbook'`, `'customizing'`.
    """
    kb = get_knowledge()
    args: dict[str, object] = {"query": query, "limit": limit}
    if source_filter is not None:
        args["source_filter"] = source_filter
    blocks = kb._dispatch("search_sn_docs", args)
    return text_of_blocks(blocks)
