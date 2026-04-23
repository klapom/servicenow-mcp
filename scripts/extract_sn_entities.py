#!/usr/bin/env python3
"""
Extract SN-specific entities and relations from curated schulungen docs and
write them to Neo4j as typed nodes/edges under namespace `sn_mcp`.

Pipeline per chunk:
    1. Entity extraction (structured JSON, no reasoning)
    2. Relation extraction using the entities found (structured JSON)
    3. Write :Document, :Entity, :MENTIONS, plus relation hints as typed edges

vLLM: Qwen 3.6 with chat_template_kwargs.enable_thinking=False +
response_format=json_object — no <think> blocks to strip.

Usage:
    .venv/bin/python3 scripts/extract_sn_entities.py schulungen/26_customization_best_practices.md schulungen/27_customization_architecture_guidelines.md
    .venv/bin/python3 scripts/extract_sn_entities.py --all-schulungen
    .venv/bin/python3 scripts/extract_sn_entities.py --purge-docs schulungen/26_customization_best_practices.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import sys
from pathlib import Path

import yaml
from neo4j import GraphDatabase
from openai import OpenAI

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("extract_sn_entities")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOMAIN_CONFIG = PROJECT_ROOT / "config" / "sn_domains.yaml"
NAMESPACE = "sn_mcp"

VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:32000/v1")
VLLM_MODEL = os.getenv("VLLM_MODEL", "qwen36-35b")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "aegis-rag-neo4j-password")

CHUNK_SIZE = 2000
CHUNK_OVERLAP = 150

# ──────────────────────────────────────────────────────────────────────
# Prompts (structured JSON, no reasoning, domain-enriched)
# ──────────────────────────────────────────────────────────────────────
ENTITY_SYSTEM = (
    "You are a precise information extractor for ServiceNow platform "
    "documentation. Reply with ONLY a JSON object — no prose, no reasoning, "
    "no <think> blocks. Schema: "
    '{"entities": [{"name": str (≤4 words, canonical), '
    '"type": one of the allowed sub-types, '
    '"description": str (≤1 sentence), '
    '"confidence": float in [0.0, 1.0]}]} '
    "Core rules: "
    "(1) Only extract named, self-contained concepts — NEVER extract "
    "fragments, prefixes, suffixes, or modifiers on their own. "
    'BAD: "u_", "sys_*", "Before", "After", "Async", "onSubmit", "u_", '
    '"Display/Query". '
    'GOOD: "cmdb_ci", "incident", "business rule", "Script Include", '
    '"GlideRecord", "Client Script". '
    "(2) A Business Rule TYPE (before/after/async/display) is a PROPERTY "
    "of the concept 'business rule', not its own entity. Do not emit it. "
    "(3) Extract the concept, not the example: if text says 'the u_foo "
    "field on incident', emit only 'incident' (TABLE) — skip 'u_foo' "
    "unless it's the documentation's actual subject. "
    "(4) Canonical names: 'incident' not 'the incident table'; "
    "'business rule' not 'a business rule'; use lowercase for SN table/ "
    "field technical names, TitleCase for process names. "
    "(5) No duplicates. Confidence: 1.0 explicit, 0.7 implied, 0.4 inferred."
)

RELATION_SYSTEM = (
    "You are a precise relation extractor for ServiceNow documentation. "
    "Reply with ONLY a JSON object — no prose, no reasoning, no <think> "
    "blocks. Schema: "
    '{"relations": [{"subject": str (must match an entity name), '
    '"relation": one of the allowed relation types, '
    '"object": str (must match an entity name), '
    '"description": str (≤1 sentence evidence from text), '
    '"strength": int in [1, 10]}]} '
    "Core rules: "
    "(1) subject and object MUST appear verbatim in the provided Entities "
    "list — do NOT invent new names. "
    "(2) Relation semantics matter. Use the right one: "
    "EXTENDS = database-level table inheritance ONLY (e.g. incident EXTENDS "
    "task). Do NOT use EXTENDS for 'is a kind of' — for that, there is no "
    "relation, skip it. "
    "USES_TABLE = an ITIL process or flow operates on a table (e.g. "
    "'Incident Management' USES_TABLE 'incident'). Do NOT use it for "
    "'a REST API accesses a table' — use USES instead. "
    "HAS_FIELD = a table definition owns a field as a schema member. "
    "RUNS_ON = a business rule / client script / flow executes against a "
    "specific table. "
    "REFERENCES = a field is a reference-type pointing to another table. "
    "(3) Decompose N-ary facts into multiple triples. "
    "(4) Strength: 10 explicit, 7 strongly implied, 4 inferred. "
    "(5) Use RELATED_TO only when no other relation fits."
)


def build_entity_user_prompt(domain: dict, text: str) -> str:
    sub_types = "\n".join(f"  - {t}" for t in domain["entity_sub_types"])
    # Include a handful of universal types for people/orgs/dates in prose
    universal = "\n".join(
        f"  - {t}" for t in ("PERSON", "ORGANIZATION", "DATE_TIME", "EVENT")
    )
    return (
        f"Allowed entity sub-types (ServiceNow):\n{sub_types}\n"
        f"Allowed universal types (use sparingly):\n{universal}\n\n"
        f"Text:\n{text}\n\n"
        'Return JSON like: {"entities": [...]}'
    )


def build_relation_user_prompt(
    domain: dict, entities: list[dict], text: str
) -> str:
    hints = "\n".join(f"  - {h}" for h in domain["relation_hints"])
    universals = (
        "  - PART_OF, CONTAINS, REQUIRES, USES, CREATES, IMPLEMENTS, "
        "DEPENDS_ON, ASSOCIATED_WITH, RELATED_TO (fallback)"
    )
    ent_list = "\n".join(
        f"  - {e['name']} ({e['type']})" for e in entities
    )
    return (
        f"ServiceNow relation hints (prefer these):\n{hints}\n"
        f"Universal relations (use if hints do not fit):\n{universals}\n\n"
        f"Entities:\n{ent_list}\n\n"
        f"Text:\n{text}\n\n"
        'Return JSON like: {"relations": [...]}'
    )


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────
def load_domain(domain_id: str = "itsm_servicenow") -> dict:
    with DOMAIN_CONFIG.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    for d in cfg["domains"]:
        if d["domain_id"] == domain_id:
            return d
    raise ValueError(f"Domain {domain_id} not found in {DOMAIN_CONFIG}")


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Strip YAML frontmatter and return (meta_dict, body)."""
    if not text.startswith("---"):
        return {}, text
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not m:
        return {}, text
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        meta = {}
    return meta, m.group(2)


def chunk_text(text: str) -> list[str]:
    text = text.strip()
    if len(text) <= CHUNK_SIZE:
        return [text] if text else []
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        if end < len(text):
            para = text.rfind("\n\n", start + CHUNK_SIZE // 2, end)
            if para > start:
                end = para
            else:
                sent = text.rfind(". ", start + CHUNK_SIZE // 2, end)
                if sent > start:
                    end = sent + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - CHUNK_OVERLAP if end < len(text) else len(text)
    return chunks


def doc_id(path: Path) -> str:
    rel = path.relative_to(PROJECT_ROOT).as_posix()
    h = hashlib.sha1(rel.encode()).hexdigest()[:10]
    return f"sn_mcp_doc_{h}"


def entity_key(name: str, sub_type: str) -> str:
    canon = name.strip().lower()
    return f"{sub_type}::{canon}"


# ──────────────────────────────────────────────────────────────────────
# vLLM calls
# ──────────────────────────────────────────────────────────────────────
def llm_json(
    client: OpenAI, system: str, user: str, max_tokens: int = 2048
) -> dict:
    """Call vLLM chat with thinking disabled + JSON object response."""
    resp = client.chat.completions.create(
        model=VLLM_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.0,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )
    raw = resp.choices[0].message.content or "{}"
    # Defensive: strip <think> in case a future model regresses
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse failed: {e} | raw[:200]={raw[:200]!r}")
        return {}


# Fragments / modifiers that should never be standalone entities.
# Lowercased comparison.
_FRAGMENT_BLOCKLIST = {
    "u_", "sys_", "sys_*", "x_", "u_*",
    "before", "after", "async", "sync", "display", "query",
    "onload", "onchange", "onsubmit", "oncellchange",
    "insert", "update", "delete", "read", "create",
    "true", "false", "null", "none", "yes", "no",
    "application", "applications",  # too generic
}

# Name must contain at least one letter; reject pure punctuation/prefixes.
_VALID_NAME_RE = re.compile(r"[A-Za-z]{2,}")


def _is_fragment(name: str) -> bool:
    n = name.strip().lower()
    if len(n) < 3:
        return True
    if n in _FRAGMENT_BLOCKLIST:
        return True
    # Pure prefix (ends in _ or *) with nothing meaningful after
    if n.endswith("_") or n.endswith("*"):
        return True
    # Starts with sys_ or u_ but has * wildcard only
    if re.fullmatch(r"(sys|u|x)_\*+", n):
        return True
    # Must contain at least 2 consecutive letters
    if not _VALID_NAME_RE.search(n):
        return True
    return False


def extract_entities(client: OpenAI, domain: dict, text: str) -> list[dict]:
    data = llm_json(
        client, ENTITY_SYSTEM, build_entity_user_prompt(domain, text)
    )
    allowed_types = set(domain["entity_sub_types"]) | {
        "PERSON",
        "ORGANIZATION",
        "DATE_TIME",
        "EVENT",
    }
    out = []
    for e in data.get("entities") or []:
        if not isinstance(e, dict):
            continue
        name = (e.get("name") or "").strip()
        etype = (e.get("type") or "").strip().upper()
        if not name or etype not in allowed_types:
            continue
        if _is_fragment(name):
            continue
        out.append(
            {
                "name": name,
                "type": etype,
                "description": (e.get("description") or "")[:300],
                "confidence": float(e.get("confidence") or 0.5),
            }
        )
    # Dedup by (name.lower(), type)
    seen, uniq = set(), []
    for e in out:
        k = (e["name"].lower(), e["type"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(e)
    return uniq


def extract_relations(
    client: OpenAI, domain: dict, entities: list[dict], text: str
) -> list[dict]:
    if len(entities) < 2:
        return []
    data = llm_json(
        client,
        RELATION_SYSTEM,
        build_relation_user_prompt(domain, entities, text),
    )
    # Build lookup of entity names → canonical entry
    by_name = {e["name"].lower(): e for e in entities}
    hint_types = {
        h.split("→")[0].strip() for h in domain["relation_hints"]
    }
    universal = {
        "PART_OF",
        "CONTAINS",
        "REQUIRES",
        "USES",
        "CREATES",
        "IMPLEMENTS",
        "DEPENDS_ON",
        "ASSOCIATED_WITH",
        "RELATED_TO",
    }
    allowed_rels = hint_types | universal
    out = []
    for r in data.get("relations") or []:
        if not isinstance(r, dict):
            continue
        subj = (r.get("subject") or "").strip()
        obj = (r.get("object") or "").strip()
        rel = (r.get("relation") or "").strip().upper()
        if not (subj and obj and rel):
            continue
        if subj.lower() not in by_name or obj.lower() not in by_name:
            continue
        if rel not in allowed_rels:
            rel = "RELATED_TO"
        out.append(
            {
                "subject": by_name[subj.lower()],
                "relation": rel,
                "object": by_name[obj.lower()],
                "description": (r.get("description") or "")[:300],
                "strength": int(r.get("strength") or 5),
            }
        )
    return out


# ──────────────────────────────────────────────────────────────────────
# Neo4j persistence
# ──────────────────────────────────────────────────────────────────────
def ensure_constraints(session) -> None:
    session.run(
        "CREATE CONSTRAINT sn_entity_key IF NOT EXISTS "
        "FOR (e:Entity) REQUIRE e.key IS UNIQUE"
    )
    session.run(
        "CREATE CONSTRAINT sn_document_id IF NOT EXISTS "
        "FOR (d:Document) REQUIRE d.doc_id IS UNIQUE"
    )


def purge_document(session, did: str) -> None:
    """Delete doc + its MENTIONS. Entities stay (may be referenced elsewhere)."""
    session.run(
        "MATCH (d:Document {doc_id: $did, namespace_id: $ns}) DETACH DELETE d",
        did=did,
        ns=NAMESPACE,
    )


def persist_chunk(
    session,
    did: str,
    source_rel: str,
    title: str,
    chunk_idx: int,
    entities: list[dict],
    relations: list[dict],
) -> None:
    session.run(
        "MERGE (d:Document {doc_id: $did}) "
        "SET d.namespace_id=$ns, d.source=$src, d.title=$title",
        did=did,
        ns=NAMESPACE,
        src=source_rel,
        title=title,
    )
    for e in entities:
        key = entity_key(e["name"], e["type"])
        # Sub-type stored as property; dynamic labels would need APOC.
        # Source tagging: 'doc' on create, promote to 'seed+doc' if the
        # seed importer has already claimed this key.
        session.run(
            "MERGE (e:Entity {key: $key}) "
            "ON CREATE SET e.source = 'doc' "
            "ON MATCH  SET e.source = CASE "
            "   WHEN e.source = 'seed' THEN 'seed+doc' "
            "   WHEN e.source IS NULL THEN 'doc' "
            "   ELSE e.source END "
            "SET e.namespace_id=$ns, e.name=$name, e.sub_type=$stype, "
            "    e.description=coalesce(e.description, $desc)",
            key=key,
            ns=NAMESPACE,
            name=e["name"],
            stype=e["type"],
            desc=e["description"],
        )
        session.run(
            "MATCH (d:Document {doc_id: $did}), (e:Entity {key: $key}) "
            "MERGE (d)-[m:MENTIONS]->(e) "
            "SET m.chunk_idx=$idx, m.confidence=$conf",
            did=did,
            key=key,
            idx=chunk_idx,
            conf=e["confidence"],
        )
    for r in relations:
        sk = entity_key(r["subject"]["name"], r["subject"]["type"])
        ok = entity_key(r["object"]["name"], r["object"]["type"])
        # Relation type must be static in Cypher; inject via APOC-free template
        cypher = (
            "MATCH (s:Entity {key: $sk}), (o:Entity {key: $ok}) "
            f"MERGE (s)-[rel:`{r['relation']}`]->(o) "
            "SET rel.namespace_id=$ns, rel.strength=$strength, "
            "    rel.description=coalesce(rel.description, $desc), "
            "    rel.source_doc=$did"
        )
        session.run(
            cypher,
            sk=sk,
            ok=ok,
            ns=NAMESPACE,
            strength=r["strength"],
            desc=r["description"],
            did=did,
        )


# ──────────────────────────────────────────────────────────────────────
# Driver
# ──────────────────────────────────────────────────────────────────────
def process_file(
    path: Path,
    client: OpenAI,
    domain: dict,
    neo4j_session,
    purge_first: bool,
) -> dict:
    text = path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)
    title = meta.get("title") or path.stem
    did = doc_id(path)
    source_rel = path.relative_to(PROJECT_ROOT).as_posix()

    if purge_first:
        purge_document(neo4j_session, did)
        logger.info(f"Purged prior extractions for {source_rel}")

    chunks = chunk_text(body)
    logger.info(f"{source_rel}: {len(chunks)} chunk(s)")

    total_ents, total_rels = 0, 0
    for idx, chunk in enumerate(chunks):
        ents = extract_entities(client, domain, chunk)
        rels = extract_relations(client, domain, ents, chunk) if ents else []
        persist_chunk(
            neo4j_session, did, source_rel, title, idx, ents, rels
        )
        total_ents += len(ents)
        total_rels += len(rels)
        logger.info(
            f"  chunk {idx + 1}/{len(chunks)}: "
            f"{len(ents)} entities, {len(rels)} relations"
        )
    return {"doc": source_rel, "entities": total_ents, "relations": total_rels}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*", help="Markdown files (relative or absolute)")
    ap.add_argument(
        "--all-schulungen",
        action="store_true",
        help="Process every schulungen/*.md file",
    )
    ap.add_argument(
        "--purge-docs",
        action="store_true",
        help="Delete prior :Document + :MENTIONS before re-extracting",
    )
    args = ap.parse_args()

    if args.all_schulungen:
        files = sorted((PROJECT_ROOT / "schulungen").glob("*.md"))
    else:
        files = [
            Path(f) if Path(f).is_absolute() else PROJECT_ROOT / f
            for f in args.files
        ]
    if not files:
        ap.error("No files given (use --all-schulungen or pass paths)")

    domain = load_domain()
    logger.info(
        f"Domain={domain['domain_id']} sub_types={len(domain['entity_sub_types'])} "
        f"relation_hints={len(domain['relation_hints'])}"
    )

    client = OpenAI(base_url=VLLM_BASE_URL, api_key="not-needed")
    driver = GraphDatabase.driver(
        NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
    )
    results = []
    with driver.session() as session:
        ensure_constraints(session)
        for path in files:
            if not path.exists():
                logger.warning(f"Skip missing: {path}")
                continue
            try:
                r = process_file(
                    path, client, domain, session, args.purge_docs
                )
                results.append(r)
            except Exception as e:
                logger.error(f"Failed {path}: {e}", exc_info=True)
    driver.close()

    print("\n─── Summary ────────────────────────────────────────────")
    for r in results:
        print(
            f"  {r['doc']}: {r['entities']} entities, {r['relations']} relations"
        )
    print("────────────────────────────────────────────────────────")
    return 0


if __name__ == "__main__":
    sys.exit(main())
