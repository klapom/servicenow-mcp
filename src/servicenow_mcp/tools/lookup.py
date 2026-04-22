"""lookup_table tool — Deterministic ServiceNow table/field documentation lookup.

Thin wrapper delegating to
``ServiceNowKnowledgeMCP._dispatch("lookup_table", ...)``.
Reads from the `docs/` directory; no vector search.
"""

from __future__ import annotations

from servicenow_mcp.server import get_knowledge, mcp
from servicenow_mcp.tools._serialize import text_of_blocks


@mcp.tool(name="lookup_table")
async def lookup_table(
    table_name: str,
    field_name: str = "",
) -> str:
    """Deterministischer Lookup einer ServiceNow-Tabelle oder eines Feldes.

    Beispiele: `table_name='incident', field_name='state'` oder nur
    `table_name='change_request'` für den Tabellen-Überblick.
    """
    kb = get_knowledge()
    args: dict[str, object] = {"table_name": table_name}
    if field_name:
        args["field_name"] = field_name
    blocks = kb._dispatch("lookup_table", args)
    return text_of_blocks(blocks)
