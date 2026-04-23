# ServiceNow MCP

## Project Overview
ServiceNow MCP server providing two distinct capabilities:
1. **Tool Server** — CRUD tools for ServiceNow instance interaction (incident, change, problem, catalog, CMDB, workflows, etc.)
2. **Knowledge Server** — RAG-based Q&A over ServiceNow platform and ITIL process documentation (no SN instance needed)

## Architecture

### Tool Server (main MCP)
- Entry: `src/servicenow_mcp/server.py`
- Tools defined in `src/servicenow_mcp/tools/*.py`
- Tool packages configured in `config/tool_packages.yaml`
- Requires ServiceNow instance credentials in `.env`

### Knowledge Server (RAG MCP)
- Entry: `src/servicenow_mcp/knowledge_server.py` → port 8094
- Engine: `src/servicenow_mcp/knowledge_mcp.py`
- Config: `src/servicenow_mcp/utils/knowledge_config.py`
- systemd: `sn-knowledge-mcp.service` (user-level)
- 4-signal retrieval: Dense (BGE-M3) + HyDE (Qwen35) + Graph (Neo4j) + RRF fusion
- Tools: `ask_sn_knowledge`, `search_sn_docs`, `lookup_table`, `graph_traverse`

### Backends
- Qdrant (localhost:6333) — collection `sn_mcp_docs`, 810 chunks
- Neo4j (localhost:7687) — namespace `sn_mcp`
- vLLM (localhost:18087) — Qwen35-35B, completions API, `api_key="not-needed"`
- Redis (localhost:6379) — HyDE cache

## Key Directories
- `schulungen/` — 27 structured process/platform guides (indexed into Qdrant + extracted to Neo4j)
- `raw_research/` — Source material from Browser-Use and WebFetch
- `docs/` — API docs, integration docs, business rules analysis
- `consulting/` — Future: customer-specific consulting knowledge
- `data/` — Excel exports of live SN schema (sn_schema_<env>_<profile>.xlsx)
- `scripts/` — `index_sn_docs.py` (Qdrant), `export_sn_schema.py` + `import_sn_schema.py` (SN instance → Excel → Neo4j seed), `extract_sn_entities.py` (doc → entity graph)

## Development
```bash
# Install with knowledge dependencies
uv pip install -e ".[knowledge]"

# Re-index after adding/changing schulungen/ or docs/
.venv/bin/python3 scripts/index_sn_docs.py

# Rebuild Neo4j seed graph from live SN instance (2 steps)
.venv/bin/python3 scripts/export_sn_schema.py --env SN_TEST --profile core    # → data/sn_schema_sn_test_core.xlsx
.venv/bin/python3 scripts/import_sn_schema.py data/sn_schema_sn_test_core.xlsx

# (Re-)extract entities + relations from schulungen/ docs
.venv/bin/python3 scripts/extract_sn_entities.py --all-schulungen --purge-docs

# Run knowledge server locally
.venv/bin/python3 -m servicenow_mcp.knowledge_server --port 8094

# systemd management
systemctl --user status sn-knowledge-mcp
systemctl --user restart sn-knowledge-mcp
journalctl --user -u sn-knowledge-mcp -f
```

## FNT Integration (Option C — Pragmatic Interface)
- Handbook: `docs/SN_FNT_Implementation_Handbook_v1.0.docx`
- Update Set: "CMDB FNT-SN Interface" (`0b799b61c3b37654ae727313e40131bd`)
- Postman: Workspace "PHOENIX — SN ↔ FNT Integration", Collection "SN FNT Implementation Handbook v1.0"
- Environments: PHOENIX DEV (`phoenixdev.service-now.com`), PHOENIX TEST (`phoenixtest.service-now.com`)
- SN credentials in `.env` — use `dotenv_values()` not `source` (passwords contain shell-breaking chars)
- REST API cannot assign update sets — use `sys_update_xml` PATCH or `GlideUpdateManager2`
- Business Rules return HTTP 403 (not 409) via `setAbortAction(true)`
- Lifecycle sys_ids are identical across DEV/TEST/PROD (OOTB reference data)

## Important Notes
- vLLM uses Qwen35 (thinking model) — completions API with `<think>` block stripping, NOT chat API
- MCP pin changed from `==1.3.0` to `>=1.3.0` for Streamable HTTP support
- Project-specific content (FNT/PHOENIX) is separated from generic SN knowledge
- `itil-api.service` on port 8092 is a separate ITIL service — do not conflict
