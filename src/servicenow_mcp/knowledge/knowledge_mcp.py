"""
SN Knowledge MCP Server — Tool definitions and dispatch.

Pure knowledge/advisor server (no ServiceNow instance dependency).
Uses Qdrant for semantic search, Neo4j for graph traversal,
and vLLM (Nemotron) for answer generation.
"""

import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Sequence

import mcp.types as types
import redis
from mcp.server.lowlevel import Server
from neo4j import GraphDatabase
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from servicenow_mcp.knowledge.config import ServiceNowConfig

logger = logging.getLogger(__name__)

NAMESPACE = "sn_mcp"


SYSTEM_PROMPT = """\
You are an expert on the ServiceNow platform, ITIL processes, and IT Service Management.
Answer questions based ONLY on the provided documentation context.
If the context doesn't contain enough information, say so explicitly.
Cite specific tables, fields, business rules, and API endpoints when relevant
(e.g. incident.state, change_request.type, sys_user.active).
Reference ITIL process names (Incident Management, Change Management, Problem Management, etc.)
and ServiceNow modules (GlideRecord, GlideSystem, Flow Designer, etc.) where applicable.
The documentation mixes German and English — answer in the language the user writes in.\
"""


def _ok(data: Any) -> list[types.TextContent]:
    if isinstance(data, str):
        text = data
    else:
        text = json.dumps(data, indent=2, ensure_ascii=False, default=str)
    return [types.TextContent(type="text", text=text)]


def _err(msg: str) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=json.dumps({"error": msg}, indent=2))]


# ── Tool definitions ─────────────────────────────────────────────────────────

TOOL_DEFINITIONS: List[types.Tool] = [
    types.Tool(
        name="ask_sn_knowledge",
        description=(
            "Ask a question about ServiceNow platform, ITIL processes, or IT Service Management. "
            "Uses RAG (vector search + graph traversal + LLM) to generate an answer "
            "with source citations from official documentation, training materials, "
            "API references, and consulting knowledge base. "
            "context_hint narrows the search (e.g. 'ITSM', 'CMDB', 'scripting', "
            "'change management', 'flow designer')."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The question to answer",
                },
                "context_hint": {
                    "type": "string",
                    "description": (
                        "Optional hint to narrow search scope "
                        "(e.g. 'ITSM', 'CMDB', 'scripting', 'change management')"
                    ),
                    "default": "",
                },
            },
            "required": ["question"],
        },
    ),
    types.Tool(
        name="search_sn_docs",
        description=(
            "Search the ServiceNow documentation without LLM synthesis. "
            "Returns raw chunks with scores. Use source_filter to narrow: "
            "'process' (ITIL process docs), 'training' (Schulungen), "
            "'api_reference' (REST/GlideRecord API), 'handbook', 'customizing'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results (default: 10)",
                    "default": 10,
                },
                "source_filter": {
                    "type": "string",
                    "description": (
                        "Filter by source: 'process', 'training', "
                        "'api_reference', 'handbook', 'customizing' (optional)"
                    ),
                    "default": "",
                },
            },
            "required": ["query"],
        },
    ),
    types.Tool(
        name="lookup_table",
        description=(
            "Look up a specific ServiceNow table or field documentation. "
            "Uses deterministic file lookup (no vector search needed). "
            "Examples: table_name='incident', field_name='state' "
            "or just table_name='change_request' for the table overview."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "description": "ServiceNow table name (e.g. 'incident', 'change_request', 'cmdb_ci')",
                },
                "field_name": {
                    "type": "string",
                    "description": "Field name (e.g. 'state', 'priority'). Omit for table overview.",
                    "default": "",
                },
            },
            "required": ["table_name"],
        },
    ),
    types.Tool(
        name="graph_traverse",
        description=(
            "Traverse the ServiceNow table hierarchy and process relationship graph. "
            "Find relationships between tables: what fields reference which tables, "
            "which tables extend which base tables, how processes connect to tables. "
            "Examples: 'How does incident relate to task?', "
            "'What tables extend cmdb_ci?', 'Which roles are needed for change management?'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "Graph traversal question",
                },
                "start_node": {
                    "type": "string",
                    "description": (
                        "Starting table or process name (e.g. 'incident', 'Change Management'). "
                        "Optional — if omitted, searches all nodes."
                    ),
                    "default": "",
                },
            },
            "required": ["question"],
        },
    ),
]


# ── Server class ─────────────────────────────────────────────────────────────

class ServiceNowKnowledgeMCP:
    """
    SN Knowledge MCP server.

    Lifecycle:
        server = KnowledgeMCP(config)
        server.connect()
        mcp_server = server.start()
    """

    def __init__(self, config: ServiceNowConfig):
        self.config = config
        self.docs_dir = Path(config.docs_dir)
        self.qdrant: QdrantClient | None = None
        self.neo4j_driver = None
        self.llm: OpenAI | None = None
        self._embed_client: OpenAI | None = None
        self.mcp_server = Server("sn-knowledge-mcp")
        self._register_handlers()

    def connect(self) -> None:
        """Initialize all backend connections."""
        logger.info("Connecting to Qdrant...")
        self.qdrant = QdrantClient(url=self.config.qdrant_url)

        logger.info("Connecting to Neo4j...")
        self.neo4j_driver = GraphDatabase.driver(
            self.config.neo4j_uri,
            auth=(self.config.neo4j_user, self.config.neo4j_password),
        )
        self.neo4j_driver.verify_connectivity()

        logger.info("Connecting to vLLM...")
        self.llm = OpenAI(base_url=self.config.vllm_base_url, api_key="not-needed")

        logger.info("Connecting to Redis (HyDE cache)...")
        try:
            self.redis = redis.Redis(host="localhost", port=6379, decode_responses=True)
            self.redis.ping()
            logger.info("Redis connected.")
        except Exception as e:
            logger.warning(f"Redis not available, HyDE caching disabled: {e}")
            self.redis = None

        embed_url = self.config.embed_base_url if hasattr(self.config, "embed_base_url") and self.config.embed_base_url else "http://127.0.0.1:8097/v1"
        self._embed_client = OpenAI(base_url=embed_url, api_key="not-needed")
        logger.info(f"Using central embedding proxy at {embed_url}")

    def disconnect(self) -> None:
        if self.neo4j_driver:
            self.neo4j_driver.close()

    def start(self) -> Server:
        return self.mcp_server

    def _register_handlers(self) -> None:
        mcp = self.mcp_server

        @mcp.list_tools()
        async def list_tools() -> List[types.Tool]:
            return TOOL_DEFINITIONS

        @mcp.call_tool()
        async def call_tool(
            name: str, arguments: Dict[str, Any]
        ) -> Sequence[types.TextContent]:
            try:
                return self._dispatch(name, arguments)
            except Exception as e:
                logger.exception(f"Tool '{name}' raised: {e}")
                return _err(str(e))

    # ── Embedding helper ─────────────────────────────────────────────────

    def _embed(self, text: str) -> list[float]:
        resp = self._embed_client.embeddings.create(input=text, model="bge-m3")
        return resp.data[0].embedding

    # ── Qdrant search ────────────────────────────────────────────────────

    def _search_qdrant_vec(
        self, vec: list[float], limit: int = 8, qdrant_filter=None
    ) -> list[dict]:
        """Search Qdrant with a pre-computed vector."""
        results = self.qdrant.search(
            collection_name=self.config.qdrant_collection,
            query_vector=("dense", vec),
            query_filter=qdrant_filter,
            limit=limit,
        )
        return [
            {
                "content": hit.payload.get("content", ""),
                "source_type": hit.payload.get("source_type", ""),
                "source_file": hit.payload.get("source_file", ""),
                "table_name": hit.payload.get("table_name", ""),
                "score": round(hit.score, 4),
                "source": "dense",
            }
            for hit in results
        ]

    def _search_qdrant(
        self, query: str, limit: int = 8, source_filter: str = ""
    ) -> list[dict]:
        query_vec = self._embed(query)
        qdrant_filter = None
        if source_filter:
            qdrant_filter = Filter(
                must=[FieldCondition(key="source_type", match=MatchValue(value=source_filter))]
            )
        return self._search_qdrant_vec(query_vec, limit=limit, qdrant_filter=qdrant_filter)

    # ── HyDE (Hypothetical Document Embeddings) ─────────────────────────

    def _hyde_generate(self, question: str) -> str | None:
        """Generate a hypothetical answer document via Nemotron. Cached in Redis."""
        cache_key = f"hyde:sn_mcp:{hashlib.sha256(question.encode()).hexdigest()[:16]}"

        # Check cache
        if self.redis:
            try:
                cached = self.redis.get(cache_key)
                if cached:
                    logger.debug(f"HyDE cache hit: {cache_key}")
                    return cached
            except Exception:
                pass

        # Generate hypothetical document (using completions API for thinking models)
        try:
            prompt = (
                "Write a concise technical passage (50-80 words) answering this "
                "ServiceNow platform / ITIL question. Include specific table names, "
                "field names, GlideRecord examples, or ITIL process references. "
                "No full code examples needed.\n\n"
                f"Question: {question}\n\nAnswer:"
            )
            response = self.llm.completions.create(
                model=self.config.vllm_model,
                prompt=prompt,
                max_tokens=1024,
                temperature=0.3,
            )
            raw_text = response.choices[0].text or ""
            # Strip <think>...</think> blocks from thinking models
            hypo_doc = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()
            logger.info(f"HyDE generated ({len(hypo_doc)} chars)")

            # Cache for 24h
            if self.redis:
                try:
                    self.redis.setex(cache_key, 86400, hypo_doc)
                except Exception:
                    pass

            return hypo_doc
        except Exception as e:
            logger.warning(f"HyDE generation failed: {e}")
            return None

    def _hyde_search(self, question: str, limit: int = 8) -> list[dict]:
        """Generate hypothetical doc, embed it, search Qdrant."""
        hypo_doc = self._hyde_generate(question)
        if not hypo_doc:
            return []
        vec = self._embed(hypo_doc)
        results = self._search_qdrant_vec(vec, limit=limit)
        for r in results:
            r["source"] = "hyde"
        return results

    # ── Graph-based query expansion ──────────────────────────────────────

    def _graph_expand_query(self, question: str) -> list[str]:
        """Find related tables/fields/processes via Neo4j keyword search.

        Uses unified :Entity graph (seed schema from SN export + doc-extracted).
        """
        keywords = re.findall(r'\b[A-Za-z_]{4,}\b', question)
        if not keywords:
            return []

        expansion_terms = []
        with self.neo4j_driver.session(database="neo4j") as session:
            for kw in keywords[:3]:
                # Signal A: Schema fields (prefer seed — authoritative)
                result = session.run(
                    """
                    MATCH (t:Entity {sub_type:'TABLE', namespace_id:$ns})
                          -[:HAS_FIELD]->
                          (f:Entity {sub_type:'FIELD', namespace_id:$ns})
                    WHERE (toLower(f.name) CONTAINS toLower($kw)
                           OR toLower(coalesce(f.description,'')) CONTAINS toLower($kw)
                           OR toLower(coalesce(f.label,'')) CONTAINS toLower($kw))
                      AND coalesce(f.source,'doc') <> 'doc'
                    RETURN DISTINCT t.name AS table_name, f.name AS field_name
                    LIMIT 5
                    """,
                    kw=kw, ns=NAMESPACE,
                )
                for r in result:
                    expansion_terms.append(f"{r['table_name']}.{r['field_name']}")

                # Signal B: ITIL processes and concepts (doc-extracted)
                result = session.run(
                    """
                    MATCH (p:Entity {namespace_id:$ns})
                    WHERE p.sub_type IN ['ITIL_PROCESS','FLOW','BUSINESS_RULE','ROLE']
                      AND (toLower(p.name) CONTAINS toLower($kw)
                           OR toLower(coalesce(p.description,'')) CONTAINS toLower($kw))
                    OPTIONAL MATCH (p)-[:USES_TABLE]->(t:Entity {sub_type:'TABLE'})
                    RETURN p.name AS pattern_name,
                           collect(DISTINCT t.name) AS related_tables
                    LIMIT 5
                    """,
                    kw=kw, ns=NAMESPACE,
                )
                for r in result:
                    expansion_terms.append(r["pattern_name"])
                    for tbl in r["related_tables"]:
                        expansion_terms.append(tbl)

        return list(set(expansion_terms))[:12]

    _STOPWORDS = {
        "wie", "was", "wer", "wen", "wem", "den", "dem", "des", "die", "der", "das",
        "ein", "eine", "einen", "einem", "einer", "und", "oder", "mit", "von", "für",
        "aus", "bei", "nach", "über", "unter", "kann", "sind", "wird", "gibt", "haben",
        "machen", "ich", "man", "sie", "wir", "ihr", "mir", "mich", "uns", "sich",
        "auf", "als", "auch", "noch", "nur", "schon", "dann", "wenn", "aber", "doch",
        "nicht", "kein", "keine", "keinen", "sehr", "mehr", "soll", "muss",
        "the", "how", "what", "which", "does", "can", "from", "with", "into",
        "that", "this", "for", "and", "not", "but", "all", "are", "has", "have",
        "tell", "about", "relationship", "between", "extend", "extends", "fields",
        "field", "table", "tables", "reference", "references", "mir", "please",
    }

    def _graph_routed_search(self, question: str, limit: int = 8) -> list[dict]:
        """Find matching entities in Neo4j, route to their Documents, search Qdrant."""
        keywords = [
            w for w in re.findall(r'\b[A-Za-z_]{3,}\b', question)
            if w.lower() not in self._STOPWORDS
        ]
        if not keywords:
            return []

        source_files = set()
        with self.neo4j_driver.session(database="neo4j") as session:
            for kw in keywords[:5]:
                # Match any doc-extracted concept (not pure schema nodes)
                result = session.run(
                    """
                    MATCH (d:Document {namespace_id:$ns})-[:MENTIONS]->(e:Entity)
                    WHERE e.sub_type IN ['ITIL_PROCESS','FLOW','BUSINESS_RULE',
                                         'ROLE','STATE','ACL','UPDATE_SET']
                      AND (toLower(e.name) CONTAINS toLower($kw)
                           OR toLower(coalesce(e.description,'')) CONTAINS toLower($kw))
                    RETURN DISTINCT d.source AS source_path
                    LIMIT 5
                    """,
                    kw=kw, ns=NAMESPACE,
                )
                for r in result:
                    if r["source_path"]:
                        # Qdrant indexes by basename only
                        source_files.add(Path(r["source_path"]).name)

        if not source_files:
            return []

        logger.info(f"Graph-routed: found {len(source_files)} source files: {list(source_files)[:5]}")

        # Search Qdrant filtered to these specific source files
        from qdrant_client.models import FieldCondition, Filter, MatchAny
        query_vec = self._embed(question)
        file_filter = Filter(
            must=[FieldCondition(key="source_file", match=MatchAny(any=list(source_files)))]
        )
        results = self._search_qdrant_vec(query_vec, limit=limit, qdrant_filter=file_filter)
        for r in results:
            r["source"] = "graph_routed"
        return results

    # ── Reciprocal Rank Fusion ───────────────────────────────────────────

    def _rrf_fuse(self, *rankings: list[dict], k: int = 60) -> list[dict]:
        """Fuse multiple ranked lists using RRF. Deduplicates by content hash."""
        scores: dict[str, float] = {}
        items: dict[str, dict] = {}

        for ranking in rankings:
            for rank, item in enumerate(ranking):
                # Use content hash as unique key
                key = hashlib.md5(item["content"][:200].encode()).hexdigest()
                scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1)
                if key not in items:
                    items[key] = item

        # Sort by fused score descending
        sorted_keys = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        result = []
        for key in sorted_keys:
            item = items[key].copy()
            item["rrf_score"] = round(scores[key], 6)
            result.append(item)
        return result

    # ── Neo4j graph queries ──────────────────────────────────────────────

    def _graph_find_path(self, start_table: str, end_table: str) -> list[dict]:
        """Find shortest path between two SN tables via EXTENDS/REFERENCES/USES_TABLE edges."""
        with self.neo4j_driver.session(database="neo4j") as session:
            result = session.run(
                """
                MATCH path = shortestPath(
                    (a:Entity {sub_type:'TABLE', name:$start, namespace_id:$ns})
                    -[:EXTENDS|HAS_FIELD|REFERENCES|USES_TABLE*..6]->
                    (b:Entity {sub_type:'TABLE', name:$end, namespace_id:$ns})
                )
                UNWIND relationships(path) AS rel
                RETURN
                    startNode(rel).name AS from_name,
                    type(rel) AS rel_type,
                    endNode(rel).name AS to_name,
                    CASE WHEN endNode(rel).sub_type = 'FIELD'
                         THEN endNode(rel).name ELSE null END AS via_field
                """,
                start=start_table.lower(), end=end_table.lower(), ns=NAMESPACE,
            )
            return [dict(r) for r in result]

    def _graph_table_fields(self, table_name: str) -> list[dict]:
        """Get all fields of a table with their reference types.

        Only seed-sourced fields (authoritative schema), excluding doc-extracted
        concepts that the LLM mis-labeled as fields.
        """
        with self.neo4j_driver.session(database="neo4j") as session:
            result = session.run(
                """
                MATCH (t:Entity {sub_type:'TABLE', name:$name, namespace_id:$ns})
                      -[:HAS_FIELD]->
                      (f:Entity {sub_type:'FIELD', namespace_id:$ns})
                WHERE coalesce(f.source,'doc') <> 'doc'
                OPTIONAL MATCH (f)-[:REFERENCES]->(rt:Entity {sub_type:'TABLE'})
                RETURN f.name AS field,
                       coalesce(f.field_type, f.label) AS field_type,
                       f.description AS description,
                       rt.name AS references_table
                ORDER BY f.name
                """,
                name=table_name.lower(), ns=NAMESPACE,
            )
            return [dict(r) for r in result]

    def _graph_table_extensions(self, table_name: str) -> list[dict]:
        """Get tables that extend this table."""
        with self.neo4j_driver.session(database="neo4j") as session:
            result = session.run(
                """
                MATCH (child:Entity {sub_type:'TABLE', namespace_id:$ns})
                      -[:EXTENDS]->
                      (parent:Entity {sub_type:'TABLE', name:$name, namespace_id:$ns})
                RETURN child.name AS child_table,
                       coalesce(child.description, child.label) AS description
                ORDER BY child.name
                """,
                name=table_name.lower(), ns=NAMESPACE,
            )
            return [dict(r) for r in result]

    def _graph_search(self, question: str, start_node: str = "") -> dict:
        """Answer a graph traversal question."""
        # Extract SN table names from the question (snake_case patterns)
        mentioned_tables = re.findall(r'\b[a-z][a-z_]*[a-z]\b', question)
        # Filter to likely table names (contain underscore or are known short names)
        known_short = {"incident", "problem", "task", "change", "request", "user", "group", "role"}
        mentioned_tables = [
            t for t in mentioned_tables
            if "_" in t or t in known_short
        ]
        if start_node:
            mentioned_tables = [start_node] + [m for m in mentioned_tables if m != start_node]
        # Deduplicate while preserving order
        seen = set()
        unique_tables = []
        for t in mentioned_tables:
            if t not in seen:
                seen.add(t)
                unique_tables.append(t)
        mentioned_tables = unique_tables

        results = {}
        not_found: list[str] = []

        # If two tables mentioned, find path
        if len(mentioned_tables) >= 2:
            path = self._graph_find_path(mentioned_tables[0], mentioned_tables[1])
            if path:
                results["path"] = path

        # Show fields and extensions of mentioned tables;
        # track those that do not exist in the graph.
        for tbl in mentioned_tables[:3]:
            fields = self._graph_table_fields(tbl)
            extensions = self._graph_table_extensions(tbl)
            if fields:
                results[f"fields_of_{tbl}"] = fields
            if extensions:
                results[f"extensions_of_{tbl}"] = extensions
            if not fields and not extensions:
                # Explicit existence check to distinguish "leaf table with no
                # extensions" from "not in graph at all".
                with self.neo4j_driver.session(database="neo4j") as session:
                    exists = session.run(
                        "MATCH (t:Entity {sub_type:'TABLE', name:$n, "
                        "namespace_id:$ns}) RETURN count(t) > 0 AS e",
                        n=tbl.lower(), ns=NAMESPACE,
                    ).single()["e"]
                    if not exists:
                        not_found.append(tbl)

        if not_found:
            results["not_found"] = not_found
            # If the explicit start_node is unknown, skip the noisy keyword
            # search — it would only return loose English-word matches.
            if start_node and start_node in not_found:
                return results

        # Search ITIL-process / flow / business-rule / role entities by
        # keyword. Only match on .name (not .description) to avoid English-
        # stopword pollution, and require keyword length ≥ 4.
        raw_keywords = re.findall(r'\b[A-Za-z_]{4,}\b', question)
        keywords = [
            k for k in raw_keywords if k.lower() not in self._STOPWORDS
        ]
        if keywords:
            with self.neo4j_driver.session(database="neo4j") as session:
                for kw in keywords[:3]:
                    result = session.run(
                        """
                        MATCH (p:Entity {namespace_id:$ns})
                        WHERE p.sub_type IN ['ITIL_PROCESS','FLOW','BUSINESS_RULE',
                                             'ROLE','STATE','ACL','UPDATE_SET']
                          AND toLower(p.name) CONTAINS toLower($kw)
                        OPTIONAL MATCH (p)-[:USES_TABLE]->(t:Entity {sub_type:'TABLE'})
                        OPTIONAL MATCH (d:Document)-[:MENTIONS]->(p)
                        RETURN p.sub_type AS type, p.name AS name,
                               p.description AS description,
                               collect(DISTINCT d.source)[0] AS source_file,
                               collect(DISTINCT t.name) AS uses_tables
                        LIMIT 10
                        """,
                        kw=kw, ns=NAMESPACE,
                    )
                    knowledge_hits = [dict(r) for r in result]
                    if knowledge_hits:
                        results.setdefault("knowledge_nodes", []).extend(knowledge_hits)

        # If no tables found in question, search fields by keyword (seed-only)
        if not mentioned_tables:
            with self.neo4j_driver.session(database="neo4j") as session:
                kw = question.split()[0] if question.split() else question
                result = session.run(
                    """
                    MATCH (t:Entity {sub_type:'TABLE', namespace_id:$ns})
                          -[:HAS_FIELD]->
                          (f:Entity {sub_type:'FIELD', namespace_id:$ns})
                    WHERE coalesce(f.source,'doc') <> 'doc'
                      AND (toLower(f.name) CONTAINS toLower($kw)
                           OR toLower(coalesce(f.label,'')) CONTAINS toLower($kw)
                           OR toLower(coalesce(f.description,'')) CONTAINS toLower($kw))
                    RETURN t.name AS table_name, f.name AS field,
                           f.field_type AS field_type,
                           coalesce(f.description, f.label) AS description
                    LIMIT 15
                    """,
                    kw=kw, ns=NAMESPACE,
                )
                results["keyword_matches"] = [dict(r) for r in result]

        # Deduplicate knowledge_nodes
        if "knowledge_nodes" in results:
            seen_names = set()
            deduped = []
            for kn in results["knowledge_nodes"]:
                if kn["name"] not in seen_names:
                    seen_names.add(kn["name"])
                    deduped.append(kn)
            results["knowledge_nodes"] = deduped

        return results

    # ── Deterministic table/field lookup ─────────────────────────────────

    def _lookup_table(self, table_name: str, field_name: str = "") -> dict:
        """Look up a ServiceNow table/field doc by deterministic filename."""
        # Try to find a markdown or HTML doc for this table
        candidates = []
        if not field_name:
            # Table overview
            candidates = [
                self.docs_dir / f"{table_name}.md",
                self.docs_dir / f"{table_name}.html",
                self.docs_dir / f"table_{table_name}.md",
                self.docs_dir / f"tables" / f"{table_name}.md",
            ]
        else:
            # Specific field
            candidates = [
                self.docs_dir / f"{table_name}_{field_name}.md",
                self.docs_dir / f"{table_name}.md",  # Fallback to full table doc
                self.docs_dir / f"table_{table_name}.md",
            ]

        # Try each candidate
        for path in candidates:
            if path.exists():
                try:
                    text = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    text = path.read_text(encoding="latin-1")

                # If looking for a specific field in a larger doc, try to extract it
                if field_name and len(text) > 500:
                    # Try to find the field section
                    pattern = rf'(?i)(#{1,3}\s*{re.escape(field_name)}.*?)(?=\n#{1,3}\s|\Z)'
                    match = re.search(pattern, text, re.DOTALL)
                    if match:
                        text = match.group(1).strip()

                return {
                    "table": table_name,
                    "field": field_name or "(overview)",
                    "content": text[:3000],
                    "file": str(path.name),
                }

        # Fallback: search Qdrant for the table/field
        query = f"{table_name}.{field_name}" if field_name else table_name
        hits = self._search_qdrant(query, limit=3, source_filter="")
        if hits:
            return {
                "table": table_name,
                "field": field_name or "(overview)",
                "note": "Exact file not found, showing closest matches from vector search",
                "results": hits,
            }

        return {"error": f"No documentation found for {table_name}.{field_name}"}

    # ── LLM answer generation ────────────────────────────────────────────

    def _generate_answer(
        self, question: str, context_chunks: list[dict], graph_context: dict | None = None
    ) -> dict:
        """Generate an answer using vLLM with retrieved context."""
        # Build context block
        context_parts = []
        for i, chunk in enumerate(context_chunks, 1):
            source = chunk.get("source_file", "unknown")
            tbl = chunk.get("table_name", "")
            prefix = f"[{i}] {source}"
            if tbl:
                prefix += f" ({tbl})"
            context_parts.append(f"{prefix}:\n{chunk['content']}")

        context_text = "\n\n---\n\n".join(context_parts)

        # Add graph context if available
        if graph_context:
            graph_text = json.dumps(graph_context, indent=2, ensure_ascii=False, default=str)
            context_text += f"\n\n--- Graph Context ---\n{graph_text}"

        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"Context:\n{context_text}\n\n"
            f"Question: {question}\n\n"
            f"Answer:"
        )
        response = self.llm.completions.create(
            model=self.config.vllm_model,
            prompt=prompt,
            max_tokens=4096,
            temperature=0.1,
        )
        raw_answer = response.choices[0].text or ""
        # Strip <think>...</think> blocks from thinking models
        answer = re.sub(r"<think>.*?</think>", "", raw_answer, flags=re.DOTALL).strip()

        sources = [
            {"file": c["source_file"], "type": c["source_type"], "score": c["score"]}
            for c in context_chunks
        ]

        return {"answer": answer, "sources": sources}

    # ── Dispatch ─────────────────────────────────────────────────────────

    def _dispatch(self, name: str, args: Dict[str, Any]) -> List[types.TextContent]:
        logger.info(f"Tool call: {name} args={list(args.keys())}")

        if name == "ask_sn_knowledge":
            question = args["question"]
            hint = args.get("context_hint", "")
            query = f"{hint} {question}".strip() if hint else question
            top_k = self.config.retrieval_top_k

            # Signal 1: Dense vector search (original query)
            dense_results = self._search_qdrant(query, limit=top_k)
            logger.info(f"Dense search: {len(dense_results)} results")

            # Signal 2: HyDE search (hypothetical answer embedded)
            hyde_results = self._hyde_search(question, limit=top_k)
            logger.info(f"HyDE search: {len(hyde_results)} results")

            # Signal 3: Graph-expanded search
            expansion_terms = self._graph_expand_query(question)
            graph_results = []
            if expansion_terms:
                expanded_query = f"{query} {' '.join(expansion_terms)}"
                graph_results = self._search_qdrant(expanded_query, limit=top_k)
                for r in graph_results:
                    r["source"] = "graph_expansion"
                logger.info(
                    f"Graph expansion: {len(graph_results)} results "
                    f"(terms: {expansion_terms[:3]})"
                )

            # Signal 4: Graph-routed retrieval (knowledge nodes -> source files -> Qdrant)
            graph_routed_results = self._graph_routed_search(question, limit=top_k)
            logger.info(f"Graph-routed: {len(graph_routed_results)} results")

            # RRF Fusion (4 signals)
            fused = self._rrf_fuse(
                dense_results, hyde_results, graph_results, graph_routed_results
            )
            chunks = fused[:top_k]
            logger.info(f"RRF fusion: {len(fused)} unique -> top {len(chunks)}")

            # Graph context for structural questions
            graph_ctx = None
            # Check if question mentions SN table names (snake_case)
            mentioned = re.findall(r'\b[a-z]+_[a-z_]+\b', question)
            if mentioned:
                graph_ctx = self._graph_search(question)

            # Generate answer
            result = self._generate_answer(question, chunks, graph_ctx)
            return _ok(result)

        elif name == "search_sn_docs":
            query = args["query"]
            limit = args.get("limit", 10)
            source_filter = args.get("source_filter", "")
            results = self._search_qdrant(query, limit=limit, source_filter=source_filter)
            return _ok({"results": results, "count": len(results)})

        elif name == "lookup_table":
            result = self._lookup_table(
                table_name=args["table_name"],
                field_name=args.get("field_name", ""),
            )
            return _ok(result)

        elif name == "graph_traverse":
            result = self._graph_search(
                question=args["question"],
                start_node=args.get("start_node", ""),
            )
            return _ok(result)

        else:
            return _err(f"Unknown tool: {name}")
