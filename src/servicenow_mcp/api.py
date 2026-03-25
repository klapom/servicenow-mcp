"""Lightweight REST API wrapper for the SN Knowledge MCP tools.

Usage:
    python -m servicenow_mcp.api          # starts on port 8095
    python -m servicenow_mcp.api --port 9000

Curl examples:
    curl -s localhost:8095/ask -d '{"question":"How does Incident Management work in ServiceNow?"}'
    curl -s localhost:8095/search -d '{"query":"GlideRecord","source_filter":"training"}'
    curl -s localhost:8095/lookup -d '{"table_name":"incident","field_name":"state"}'
    curl -s localhost:8095/graph -d '{"question":"Change Management relationships"}'
    curl -s localhost:8095/health
"""

import argparse
import json
import logging
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

from dotenv import load_dotenv

from servicenow_mcp.utils.knowledge_config import KnowledgeConfig
from servicenow_mcp.knowledge_mcp import KnowledgeMCP

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("sn-api")

_server: KnowledgeMCP | None = None


def _call_tool(name: str, args: dict) -> dict:
    """Call an MCP tool and return the result as dict/string."""
    result = _server._dispatch(name, args)
    text = result[0].text if result else ""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return {"response": text}


class SNHandler(BaseHTTPRequestHandler):
    """HTTP request handler mapping paths to SN Knowledge MCP tools."""

    ROUTES = {
        "/ask": "ask_sn_knowledge",
        "/search": "search_sn_docs",
        "/lookup": "lookup_table",
        "/graph": "graph_traverse",
    }

    def do_GET(self):
        if self.path == "/health":
            self._json_response({"status": "ok", "tools": list(self.ROUTES.keys()), "collection": "sn_mcp_docs"})
        elif self.path == "/tools":
            self._json_response({
                "/ask": {"method": "POST", "params": {"question": "str (required)", "context_hint": "str (optional)"}},
                "/search": {"method": "POST", "params": {"query": "str (required)", "limit": "int (optional)", "source_filter": "process|training|consulting|api (optional)"}},
                "/lookup": {"method": "POST", "params": {"table_name": "str (required)", "field_name": "str (optional)"}},
                "/graph": {"method": "POST", "params": {"question": "str (required)"}},
            })
        else:
            self._json_response({"error": "Not found. Try /health or /tools"}, 404)

    def do_POST(self):
        tool_name = self.ROUTES.get(self.path)
        if not tool_name:
            self._json_response({"error": f"Unknown endpoint: {self.path}", "available": list(self.ROUTES.keys())}, 404)
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length > 0 else {}
        except json.JSONDecodeError:
            self._json_response({"error": "Invalid JSON body"}, 400)
            return

        try:
            result = _call_tool(tool_name, body)
            self._json_response(result)
        except Exception as e:
            logger.exception(f"Tool {tool_name} failed")
            self._json_response({"error": str(e)}, 500)

    def _json_response(self, data, status=200):
        body = json.dumps(data, indent=2, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        logger.info(f"{self.client_address[0]} {fmt % args}")


def main():
    global _server

    parser = argparse.ArgumentParser(description="SN Knowledge REST API")
    parser.add_argument("--port", type=int, default=8095)
    args = parser.parse_args()

    config = KnowledgeConfig.from_env()

    logger.info("Initializing SN Knowledge server...")
    _server = KnowledgeMCP(config)
    _server.connect()

    httpd = HTTPServer(("0.0.0.0", args.port), SNHandler)
    logger.info(f"SN Knowledge API running on http://0.0.0.0:{args.port}")
    logger.info(f"Endpoints: /health /tools /ask /search /lookup /graph")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        _server.disconnect()
        httpd.server_close()


if __name__ == "__main__":
    main()
