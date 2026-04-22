"""Dual-surface HTTP entry — delegates to mcp-toolkit-py.

REST on ``listen_port`` (32310) + MCP Streamable-HTTP on ``mcp_port`` (33310).
Thin wrapper: toolkit provides the FastAPI app, uvicorn orchestration, logging
and metrics setup.

Run with:
    uv run servicenow-mcp-http
"""

from __future__ import annotations

import asyncio

from mcp_toolkit_py.http import run_dual_surface
from mcp_toolkit_py.logging import setup_logging
from mcp_toolkit_py.metrics import init_metrics

from servicenow_mcp import __service_name__, __version__
from servicenow_mcp.config import get_settings
from servicenow_mcp.server import mcp


def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)
    init_metrics(__service_name__, __version__)
    asyncio.run(
        run_dual_surface(
            mcp,
            service_name=__service_name__,
            version=__version__,
            listen_port=settings.listen_port,
            mcp_port=settings.mcp_port,
        )
    )


if __name__ == "__main__":
    main()
