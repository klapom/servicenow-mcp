"""ask_sn_knowledge tool — RAG Q&A over ServiceNow knowledge base.

Thin wrapper delegating to
``ServiceNowKnowledgeMCP._dispatch("ask_sn_knowledge", ...)``
(Qdrant dense + HyDE + graph-expanded + graph-routed retrieval, RRF fusion,
vLLM-generated answer).
"""

from __future__ import annotations

from servicenow_mcp.server import get_knowledge, mcp
from servicenow_mcp.tools._serialize import text_of_blocks


@mcp.tool(name="ask_sn_knowledge")
async def ask_sn_knowledge(
    question: str,
    context_hint: str = "",
) -> str:
    """Beantwortet ServiceNow-/ITIL-/ITSM-Fragen per RAG (Vector + Graph + LLM) mit Quellen.

    `context_hint` engt die Suche ein (z.B. `'ITSM'`, `'CMDB'`, `'scripting'`,
    `'change management'`, `'flow designer'`).
    """
    kb = get_knowledge()
    args: dict[str, object] = {"question": question}
    if context_hint:
        args["context_hint"] = context_hint
    blocks = kb._dispatch("ask_sn_knowledge", args)
    return text_of_blocks(blocks)
