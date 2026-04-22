"""Stdio entry point — ``python -m servicenow_mcp`` or ``servicenow-mcp``."""

from __future__ import annotations

from mcp_toolkit_py.stdio import run_stdio

from servicenow_mcp import __service_name__, __version__
from servicenow_mcp.config import get_settings
from servicenow_mcp.server import mcp


def main_stdio() -> None:
    settings = get_settings()
    run_stdio(
        mcp,
        service_name=__service_name__,
        version=__version__,
        log_level=settings.log_level,
    )


if __name__ == "__main__":
    main_stdio()
