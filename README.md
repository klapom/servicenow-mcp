# servicenow-mcp

MCP server for **ServiceNow knowledge** (platform + ITIL/ITSM processes + consulting notes) — RAG over Qdrant+Neo4j+vLLM.

Not a ServiceNow CRUD/API tool. This is a knowledge/advisor MCP: Qdrant dense retrieval + HyDE + graph-routed retrieval + RRF fusion + vLLM answer generation, plus deterministic table/field lookups and Neo4j graph traversal.

**Version:** 0.5.0 · **Stack:** Python 3.12 + uv + FastMCP + `mcp-toolkit-py@v0.1.0` · **Ports:** 32310 REST / 33310 MCP

## Quickstart

```bash
uv sync
cp .env.example .env
uv run servicenow-mcp-http   # dual-surface (REST + MCP Streamable-HTTP)
# or
uv run servicenow-mcp        # stdio only (Claude Desktop)
```

Health: `curl http://localhost:32310/health`

## Dev

```bash
uv sync --dev
uv run pytest                  # unit tests with coverage gate
uv run ruff check .
uv run ruff format .
uv run mypy src
```

## Deploy (systemd user-unit)

```bash
# Stop + disable legacy units
systemctl --user stop sn-api sn-knowledge-mcp
systemctl --user disable sn-api sn-knowledge-mcp

# Install new dual-surface unit
ln -sf ~/projects/servicenow-mcp/systemd/servicenow-mcp.service ~/.config/systemd/user/servicenow-mcp.service
systemctl --user daemon-reload
systemctl --user enable --now servicenow-mcp.service
journalctl --user -u servicenow-mcp -f
```

## Layout

```
src/servicenow_mcp/
├── __init__.py           # version + service name
├── __main__.py           # stdio entry (Claude Desktop)
├── http_server.py        # dual-surface (REST + MCP Streamable-HTTP)
├── server.py             # FastMCP instance + tool imports + KnowledgeMCP singleton
├── config.py             # pydantic-settings (process-env > .env > defaults)
├── knowledge/            # preserved pre-migration RAG class (818 LOC, not touched)
│   ├── config.py         # ServiceNowConfig (RAG backends + retrieval)
│   └── knowledge_mcp.py  # ServiceNowKnowledgeMCP (Qdrant + Neo4j + vLLM + Redis)
└── tools/                # @mcp.tool() thin wrappers delegating to _dispatch
    ├── ask.py            # ask_sn_knowledge
    ├── search.py         # search_sn_docs
    ├── lookup.py         # lookup_table
    ├── graph.py          # graph_traverse
    └── _serialize.py     # text_of_blocks helper
```

Transport-layer (logging, metrics, dual-surface HTTP, stdio, BaseServiceSettings) comes from `mcp-toolkit-py`.

## Related

- `mcp-platform/docs/inventory/PORT_REGISTRY.md` — port reservation (32310/33310)
- `mcp-platform/docs/adr/ADR-005-surfaces.md` — dual-surface contract
- `mcp-platform/docs/adr/ADR-010-config.md` — env-hierarchy

## History

Fork of [echelon-ai-labs/servicenow-mcp](https://github.com/echelon-ai-labs/servicenow-mcp). The upstream ServiceNow CRUD/API tools (incident, catalog, workflow, etc.) were replaced pre-migration with a knowledge-only RAG server. v0.5.0 (B8, 2026-04-22) migrated the transport layer from the Low-Level MCP SDK to FastMCP + `mcp-toolkit-py`, preserving the RAG logic unchanged.
