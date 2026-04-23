#!/usr/bin/env python3
"""
Import an SN schema Excel (from export_sn_schema.py) into Neo4j.

Writes into namespace `sn_mcp` under the same `:Entity` label scheme as
scripts/extract_sn_entities.py — seed and extracted entities share the graph.

Label scheme
------------
    :Entity {key, name, sub_type, source}
      sub_type ∈ {TABLE, FIELD, ROLE, CHOICE_VALUE}
      source   ∈ {seed, doc, seed+doc}  (auto-merged on key collision)

Relation scheme (all with namespace_id='sn_mcp')
------------------------------------------------
    (TABLE)-[:EXTENDS]->(TABLE)              — super_class inheritance
    (TABLE)-[:HAS_FIELD]->(FIELD)            — sys_dictionary
    (FIELD)-[:REFERENCES]->(TABLE)           — FK-like pointers
    (FIELD)-[:HAS_CHOICE]->(CHOICE_VALUE)    — sys_choice

Key scheme (must match extract_sn_entities.py)
----------------------------------------------
    TABLE::<table_name_lower>
    FIELD::<table_name_lower>.<element_lower>
    ROLE::<role_name_lower>
    CHOICE_VALUE::<table_lower>.<element_lower>=<value_lower>

Usage:
    .venv/bin/python3 scripts/import_sn_schema.py data/sn_schema_sn_test_core.xlsx
    .venv/bin/python3 scripts/import_sn_schema.py data/... --purge-seed
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

import pandas as pd
from neo4j import GraphDatabase

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("import_sn_schema")

NAMESPACE = "sn_mcp"
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "aegis-rag-neo4j-password")


# ──────────────────────────────────────────────────────────────────────
# Key builders
# ──────────────────────────────────────────────────────────────────────
def table_key(name: str) -> str:
    return f"TABLE::{name.strip().lower()}"


def field_key(table: str, element: str) -> str:
    return f"FIELD::{table.strip().lower()}.{element.strip().lower()}"


def role_key(name: str) -> str:
    return f"ROLE::{name.strip().lower()}"


def choice_key(table: str, element: str, value: str) -> str:
    return (
        f"CHOICE_VALUE::{table.strip().lower()}.{element.strip().lower()}"
        f"={str(value).strip().lower()}"
    )


# ──────────────────────────────────────────────────────────────────────
# Neo4j writer
# ──────────────────────────────────────────────────────────────────────
def ensure_constraints(session) -> None:
    session.run(
        "CREATE CONSTRAINT sn_entity_key IF NOT EXISTS "
        "FOR (e:Entity) REQUIRE e.key IS UNIQUE"
    )


def purge_legacy_labels(session) -> None:
    """Delete old hardcoded-seed labels (:Table, :Field, :Process, :State, :Role, :Pattern).

    Safe to run repeatedly. Only targets nodes in the sn_mcp namespace.
    """
    for label in ("Table", "Field", "Process", "State", "Role", "Pattern"):
        r = session.run(
            f"MATCH (n:{label} {{namespace_id:$ns}}) DETACH DELETE n "
            "RETURN count(n) as c",
            ns=NAMESPACE,
        ).single()
        if r and r["c"]:
            logger.info(f"  Purged {r['c']} legacy :{label} nodes")


def purge_seed_entities(session) -> None:
    """Delete Entity nodes that are ONLY from seed (not mentioned in any doc)."""
    r = session.run(
        "MATCH (e:Entity {namespace_id:$ns}) "
        "WHERE e.source = 'seed' "
        "AND NOT (:Document)-[:MENTIONS]->(e) "
        "DETACH DELETE e RETURN count(e) as c",
        ns=NAMESPACE,
    ).single()
    if r and r["c"]:
        logger.info(f"  Purged {r['c']} orphan seed entities")


def upsert_entity(
    session,
    key: str,
    sub_type: str,
    name: str,
    props: dict,
) -> None:
    """MERGE entity; mark source as seed or seed+doc if already present."""
    cypher = (
        "MERGE (e:Entity {key: $key}) "
        "ON CREATE SET e.source = 'seed', e.created_by='seed' "
        "ON MATCH  SET e.source = CASE "
        "   WHEN e.source = 'doc' THEN 'seed+doc' "
        "   WHEN e.source IS NULL THEN 'seed' "
        "   ELSE e.source END "
        "SET e.namespace_id = $ns, e.sub_type = $stype, e.name = $name "
        "SET e += $props"
    )
    session.run(
        cypher,
        key=key,
        ns=NAMESPACE,
        stype=sub_type,
        name=name,
        props=props,
    )


def upsert_relation(
    session,
    from_key: str,
    rel_type: str,
    to_key: str,
    props: dict,
) -> None:
    cypher = (
        "MATCH (a:Entity {key:$fk}), (b:Entity {key:$tk}) "
        f"MERGE (a)-[r:`{rel_type}`]->(b) "
        "SET r.namespace_id=$ns, r += $props"
    )
    session.run(cypher, fk=from_key, tk=to_key, ns=NAMESPACE, props=props)


# ──────────────────────────────────────────────────────────────────────
# Import phases
# ──────────────────────────────────────────────────────────────────────
def import_tables(session, df: pd.DataFrame) -> int:
    n = 0
    for _, row in df.iterrows():
        name = str(row.get("name") or "").strip()
        if not name:
            continue
        props = {
            "label": str(row.get("label") or "").strip() or None,
            "scope": str(row.get("scope") or "").strip() or None,
            "sys_id": str(row.get("sys_id") or "").strip() or None,
            "is_custom": name.startswith(("u_", "x_")),
        }
        props = {k: v for k, v in props.items() if v is not None}
        upsert_entity(session, table_key(name), "TABLE", name, props)
        n += 1
    # EXTENDS edges
    for _, row in df.iterrows():
        name = str(row.get("name") or "").strip()
        super_class = str(row.get("super_class") or "").strip()
        if name and super_class:
            # Ensure super_class exists (some OOB parents may not be in scope)
            upsert_entity(
                session,
                table_key(super_class),
                "TABLE",
                super_class,
                {"is_custom": False},
            )
            upsert_relation(
                session,
                table_key(name),
                "EXTENDS",
                table_key(super_class),
                {},
            )
    return n


def import_fields(session, df: pd.DataFrame) -> int:
    n = 0
    for _, row in df.iterrows():
        table = str(row.get("table") or "").strip()
        element = str(row.get("element") or "").strip()
        if not (table and element):
            continue
        def _clean(val) -> str | None:
            if val is None or (isinstance(val, float) and pd.isna(val)):
                return None
            s = str(val).strip()
            return s if s and s.lower() != "nan" else None

        props = {
            "field_type": _clean(row.get("type")),
            "label": _clean(row.get("label")),
            "mandatory": bool(row.get("mandatory")),
            "max_length": (
                int(row["max_length"])
                if pd.notna(row.get("max_length"))
                and str(row["max_length"]).strip().isdigit()
                else None
            ),
            "reference_table": _clean(row.get("reference_table")),
            "default_value": _clean(row.get("default_value")),
            "has_choices": bool(row.get("has_choices")),
            "description": _clean(row.get("description")),
            "is_custom": element.startswith("u_"),
        }
        props = {k: v for k, v in props.items() if v is not None}
        fk = field_key(table, element)
        upsert_entity(session, fk, "FIELD", element, props)
        # Ensure table exists then HAS_FIELD
        upsert_entity(
            session,
            table_key(table),
            "TABLE",
            table,
            {"is_custom": table.startswith(("u_", "x_"))},
        )
        upsert_relation(
            session, table_key(table), "HAS_FIELD", fk, {}
        )
        n += 1
    return n


def import_references(session, df: pd.DataFrame) -> int:
    n = 0
    for _, row in df.iterrows():
        ft = str(row.get("from_table") or "").strip()
        fe = str(row.get("from_field") or "").strip()
        tt = str(row.get("to_table") or "").strip()
        if not (ft and fe and tt):
            continue
        # Ensure target table node exists
        upsert_entity(
            session,
            table_key(tt),
            "TABLE",
            tt,
            {"is_custom": tt.startswith(("u_", "x_"))},
        )
        upsert_relation(
            session, field_key(ft, fe), "REFERENCES", table_key(tt), {}
        )
        n += 1
    return n


def import_roles(session, df: pd.DataFrame) -> int:
    n = 0
    for _, row in df.iterrows():
        name = str(row.get("name") or "").strip()
        if not name:
            continue
        props = {
            "description": str(row.get("description") or "").strip() or None,
            "elevated_privilege": bool(row.get("elevated_privilege")),
            "scope": str(row.get("scope") or "global").strip() or None,
        }
        props = {k: v for k, v in props.items() if v is not None}
        upsert_entity(session, role_key(name), "ROLE", name, props)
        n += 1
    return n


def import_choices(session, df: pd.DataFrame) -> int:
    n = 0
    for _, row in df.iterrows():
        table = str(row.get("table") or "").strip()
        element = str(row.get("element") or "").strip()
        value = row.get("value")
        if not (table and element) or value is None or pd.isna(value):
            continue
        value_s = str(value).strip()
        label = str(row.get("label") or "").strip()
        ck = choice_key(table, element, value_s)
        props = {
            "value": value_s,
            "label": label or None,
            "hint": str(row.get("hint") or "").strip() or None,
        }
        props = {k: v for k, v in props.items() if v is not None}
        upsert_entity(
            session, ck, "CHOICE_VALUE", label or value_s, props
        )
        upsert_relation(
            session, field_key(table, element), "HAS_CHOICE", ck, {}
        )
        n += 1
    return n


# ──────────────────────────────────────────────────────────────────────
# Driver
# ──────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("excel", help="Path to sn_schema_*.xlsx")
    ap.add_argument(
        "--purge-legacy",
        action="store_true",
        default=True,
        help="Delete old :Table/:Field/:Process/:State/:Role/:Pattern nodes",
    )
    ap.add_argument(
        "--purge-seed",
        action="store_true",
        help="Also delete prior seed-only :Entity nodes (orphan check)",
    )
    ap.add_argument(
        "--skip-choices",
        action="store_true",
        help="Skip sys_choice import (1k+ rows, optional)",
    )
    args = ap.parse_args()

    path = Path(args.excel)
    if not path.exists():
        ap.error(f"File not found: {path}")

    logger.info(f"Reading {path}...")
    xl = pd.ExcelFile(path)

    def read(sheet: str) -> pd.DataFrame:
        return pd.read_excel(xl, sheet_name=sheet) if sheet in xl.sheet_names else pd.DataFrame()

    tables_df = read("Tables")
    fields_df = read("Fields")
    refs_df = read("References")
    roles_df = read("Roles")
    choices_df = read("Choices")
    logger.info(
        f"Loaded: tables={len(tables_df)} fields={len(fields_df)} "
        f"refs={len(refs_df)} roles={len(roles_df)} choices={len(choices_df)}"
    )

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as s:
        ensure_constraints(s)
        if args.purge_legacy:
            logger.info("Purging legacy labels (hardcoded seed)...")
            purge_legacy_labels(s)
        if args.purge_seed:
            logger.info("Purging orphan seed entities...")
            purge_seed_entities(s)

        logger.info("Importing tables...")
        t = import_tables(s, tables_df)
        logger.info(f"  → {t} table nodes")

        logger.info("Importing fields...")
        f = import_fields(s, fields_df)
        logger.info(f"  → {f} field nodes + HAS_FIELD")

        logger.info("Importing references...")
        r = import_references(s, refs_df)
        logger.info(f"  → {r} REFERENCES edges")

        logger.info("Importing roles...")
        rl = import_roles(s, roles_df)
        logger.info(f"  → {rl} role nodes")

        if not args.skip_choices and not choices_df.empty:
            logger.info("Importing choices...")
            c = import_choices(s, choices_df)
            logger.info(f"  → {c} CHOICE_VALUE nodes + HAS_CHOICE")
    driver.close()
    logger.info("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
