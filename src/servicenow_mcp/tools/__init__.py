"""Tool definitions — one file per tool.

Each tool is decorated with ``@mcp.tool()`` from the shared server instance
(``servicenow_mcp.server.mcp``). Tools-as-Data is enforced by FastMCP: the
function signature (type hints + docstring) is the schema source of truth.
"""
