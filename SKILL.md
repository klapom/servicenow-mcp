---
name: servicenow-mcp
description: Knowledge MCP für ServiceNow (Plattform + ITIL/ITSM-Prozesse + Consulting). RAG über Qdrant (Dense + HyDE) + Neo4j (Tabellen-/Prozess-Graph) + vLLM (Answer-Generation). 4 Tools ask_sn_knowledge, search_sn_docs, lookup_table, graph_traverse. Dual-Surface REST 32310 + MCP 33310.
---

# servicenow-mcp

MCP server für **ServiceNow-Wissen** — Plattform (Tabellen, Felder, Business Rules, GlideRecord, Flow Designer), ITIL/ITSM-Prozesse, Schulungsmaterialien und Consulting-Notizen. Backed by Qdrant (dense retrieval + HyDE), Neo4j (Tabellen- und Prozess-Graph) und vLLM (Answer-Generation).

**Version:** 0.5.0 · **Stack:** Python 3.12 + uv + FastMCP · **Ports:** 32310 REST / 33310 MCP

## Surfaces

- **REST:** `http://<host>:32310/tools/<name>` (POST, JSON body) · `/tools` · `/health` · `/metrics`
- **MCP Streamable-HTTP:** `http://<host>:33310/mcp` (ohne trailing slash — nach FastMCP-Migration)
- **stdio:** `uv run servicenow-mcp` (Claude Desktop / local agents)

Public hostnames (CF-Tunnel + Access):

- `https://api-servicenow.pommerconsulting.de` — REST (`servicenow-token`)
- `https://mcp-servicenow.pommerconsulting.de` — MCP (`servicenow-token`)

## Tools

| Name | Beschreibung |
|---|---|
| `ask_sn_knowledge` | RAG-Antwort mit Quellen (4-Signal: Dense + HyDE + Graph-Expansion + Graph-Routing → RRF). Optional `context_hint` (z.B. `'ITSM'`, `'CMDB'`, `'scripting'`). |
| `search_sn_docs` | Rohe Chunks, keine LLM-Synthese. Optional `limit` (default 10) + `source_filter` (`process` / `training` / `api_reference` / `handbook` / `customizing`). |
| `lookup_table` | Deterministischer Tabellen-/Feld-Lookup aus `docs/`. Optional `field_name` für Feldebene, sonst Tabellen-Überblick. |
| `graph_traverse` | Neo4j-Graph-Navigation (Referenzen, Extensions, Prozess-Tabellen-Relationen). Optional `start_node` als Startknoten. |

## Backends

- vLLM: `http://localhost:32000/v1` (Modell `qwen36-35b`)
- Qdrant: `http://localhost:6333` (Collection `sn_mcp_docs`, Namespace `sn_mcp`)
- Neo4j: `bolt://localhost:7687`
- Embedding-Proxy: `http://127.0.0.1:8097/v1` (Modell `bge-m3`)

Knowledge-Inhalte (ServiceNow-Plattformdoku, ITIL-Schulungen, Handbücher, Customizing-Notizen, API-Referenz) liegen als Qdrant-Index + Neo4j-Graph vor.

## Auth

Default: **CF-Access-Service-Token** (`servicenow-token`) extern. LAN: unprotected auf 32310/33310.

## Beispiele

```bash
# RAG-Antwort mit Context-Hint
curl -sS -X POST http://localhost:32310/tools/ask_sn_knowledge \
  -H 'content-type: application/json' \
  -d '{"question":"Wie modelliere ich eine Change-Approval in Flow Designer?","context_hint":"change management"}'

# Rohe Chunks aus API-Referenz
curl -sS -X POST http://localhost:32310/tools/search_sn_docs \
  -H 'content-type: application/json' \
  -d '{"query":"GlideRecord addQuery","source_filter":"api_reference","limit":5}'

# Tabellen-Feld-Lookup
curl -sS -X POST http://localhost:32310/tools/lookup_table \
  -H 'content-type: application/json' \
  -d '{"table_name":"incident","field_name":"state"}'

# Graph-Traversal
curl -sS -X POST http://localhost:32310/tools/graph_traverse \
  -H 'content-type: application/json' \
  -d '{"question":"What tables extend cmdb_ci?","start_node":"cmdb_ci"}'
```

## Deploy

systemd User-Unit `systemd/servicenow-mcp.service`. Ersetzt die alten `sn-api.service` (REST 32310) + `sn-knowledge-mcp.service` (MCP 33310) mit einem Dual-Surface-Prozess.
