"""
SN Knowledge MCP Server — Streamable HTTP transport.

Runs on Linux (DGX Spark). No ServiceNow instance dependency.
Provides RAG-based Q&A over ServiceNow documentation via Qdrant + Neo4j + vLLM.

Usage:
    python -m servicenow_mcp.knowledge_server
    python -m servicenow_mcp.knowledge_server --port 8092
"""

import argparse
import contextlib
import logging
import os
from collections.abc import AsyncIterator

import uvicorn
from dotenv import load_dotenv
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.routing import Mount

from servicenow_mcp.knowledge_mcp import KnowledgeMCP
from servicenow_mcp.utils.knowledge_config import KnowledgeConfig

logger = logging.getLogger(__name__)


def create_starlette_app(
    mcp_server, *, debug: bool = False
) -> Starlette:
    """Wrap the MCP server in a Starlette app with Streamable HTTP transport."""
    session_manager = StreamableHTTPSessionManager(
        app=mcp_server,
        stateless=False,
    )

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            yield

    return Starlette(
        debug=debug,
        lifespan=lifespan,
        routes=[
            Mount("/mcp", app=session_manager.handle_request),
        ],
    )


def main() -> None:
    load_dotenv()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    parser = argparse.ArgumentParser(description="SN Knowledge MCP Server")
    parser.add_argument("--host", default=os.getenv("KNOWLEDGE_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.getenv("KNOWLEDGE_PORT", "8092")))
    parser.add_argument("--debug", action="store_true",
                        default=os.getenv("KNOWLEDGE_DEBUG", "false").lower() == "true")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    config = KnowledgeConfig.from_env()
    config.host = args.host
    config.port = args.port
    config.debug = args.debug

    logger.info("Initializing SN Knowledge MCP server...")
    knowledge = KnowledgeMCP(config)
    knowledge.connect()
    logger.info("All backends connected.")

    mcp_server = knowledge.start()
    app = create_starlette_app(mcp_server, debug=args.debug)

    logger.info(f"Listening on http://{args.host}:{args.port}/mcp")
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
