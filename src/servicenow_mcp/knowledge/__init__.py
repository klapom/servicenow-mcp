"""Legacy RAG class for ServiceNow knowledge (Qdrant+Neo4j+vLLM).

Preserved pre-migration (818 LOC) — transport layer is provided by
``servicenow_mcp.server`` (FastMCP) + ``mcp-toolkit-py``. Tool wrappers
in ``servicenow_mcp.tools`` delegate via ``ServiceNowKnowledgeMCP._dispatch``.
"""
