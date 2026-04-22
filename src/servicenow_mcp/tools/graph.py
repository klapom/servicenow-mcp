"""graph_traverse tool — Neo4j graph navigation over ServiceNow tables + processes.

Thin wrapper delegating to
``ServiceNowKnowledgeMCP._dispatch("graph_traverse", ...)``.
"""

from __future__ import annotations

from servicenow_mcp.server import get_knowledge, mcp
from servicenow_mcp.tools._serialize import text_of_blocks


@mcp.tool(name="graph_traverse")
async def graph_traverse(
    question: str,
    start_node: str = "",
) -> str:
    """Navigiert die Tabellen- und Prozess-Relationen in Neo4j.

    Findet Beziehungen zwischen Tabellen (Referenzen, Extensions) und
    Prozessen. Beispiele: `'How does incident relate to task?'`,
    `'What tables extend cmdb_ci?'`. `start_node` optional — schränkt auf
    einen Startknoten ein (z.B. `'incident'`, `'Change Management'`).
    """
    kb = get_knowledge()
    args: dict[str, object] = {"question": question}
    if start_node:
        args["start_node"] = start_node
    blocks = kb._dispatch("graph_traverse", args)
    return text_of_blocks(blocks)
