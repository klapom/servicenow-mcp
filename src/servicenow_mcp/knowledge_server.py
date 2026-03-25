"""
SN Knowledge MCP Server — Streamable HTTP transport + REST API.

Runs on Linux (DGX Spark). No ServiceNow instance dependency.
Provides RAG-based Q&A over ServiceNow documentation via Qdrant + Neo4j + vLLM.

MCP endpoint: /mcp (Streamable HTTP for Claude Desktop)
REST API:     /api/health, /api/tools, /api/ask, /api/search, /api/lookup, /api/graph

Usage:
    python -m servicenow_mcp.knowledge_server
    python -m servicenow_mcp.knowledge_server --port 8094
"""

import argparse
import contextlib
import json
import logging
import os
from collections.abc import AsyncIterator

import uvicorn
from dotenv import load_dotenv
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from servicenow_mcp.knowledge_mcp import KnowledgeMCP
from servicenow_mcp.utils.knowledge_config import KnowledgeConfig

logger = logging.getLogger(__name__)

# Module-level ref so REST routes can access the knowledge engine
_knowledge: KnowledgeMCP | None = None

# REST API route → MCP tool name mapping
_API_ROUTES = {
    "ask": "ask_sn_knowledge",
    "search": "search_sn_docs",
    "lookup": "lookup_table",
    "graph": "graph_traverse",
}


async def _api_health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "tools": list(_API_ROUTES.keys()), "collection": "sn_mcp_docs"})


async def _api_tools(request: Request) -> JSONResponse:
    return JSONResponse({
        "/api/ask": {"method": "POST", "params": {"question": "str (required)", "context_hint": "str (optional)"}},
        "/api/search": {"method": "POST", "params": {"query": "str (required)", "limit": "int (optional)", "source_filter": "process|training|consulting|api (optional)"}},
        "/api/lookup": {"method": "POST", "params": {"table_name": "str (required)", "field_name": "str (optional)"}},
        "/api/graph": {"method": "POST", "params": {"question": "str (required)"}},
    })


async def _api_call(request: Request) -> JSONResponse:
    action = request.path_params["action"]
    tool_name = _API_ROUTES.get(action)
    if not tool_name:
        return JSONResponse({"error": f"Unknown action: {action}", "available": list(_API_ROUTES.keys())}, status_code=404)
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)
    try:
        result = _knowledge._dispatch(tool_name, body)
        text = result[0].text if result else ""
        try:
            data = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            data = {"response": text}
        return JSONResponse(data)
    except Exception as e:
        logger.exception(f"Tool {tool_name} failed")
        return JSONResponse({"error": str(e)}, status_code=500)


def create_starlette_app(
    mcp_server, *, debug: bool = False
) -> Starlette:
    """Wrap the MCP server in a Starlette app with Streamable HTTP + REST API."""
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
            Route("/api/health", _api_health),
            Route("/api/tools", _api_tools),
            Route("/api/{action}", _api_call, methods=["POST"]),
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

    global _knowledge

    logger.info("Initializing SN Knowledge MCP server...")
    _knowledge = KnowledgeMCP(config)
    _knowledge.connect()
    logger.info("All backends connected.")

    mcp_server = _knowledge.start()
    app = create_starlette_app(mcp_server, debug=args.debug)

    logger.info(f"Listening on http://{args.host}:{args.port}/mcp (MCP) + /api/* (REST)")
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
