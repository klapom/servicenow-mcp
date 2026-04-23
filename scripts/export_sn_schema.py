#!/usr/bin/env python3
"""
Export ServiceNow schema metadata (tables, fields, choices, roles) from a
live SN instance into an Excel workbook.

The Excel file is the human-editable source of truth for the graph seed —
import_sn_schema.py reads it and writes :Entity nodes into Neo4j.

Data sources in SN:
  - sys_db_object   → table definitions, inheritance (super_class)
  - sys_dictionary  → field definitions per table (incl. inherited)
  - sys_choice      → choice list values per (table, element)
  - sys_user_role   → role definitions

Usage:
    .venv/bin/python3 scripts/export_sn_schema.py --env SN_TEST --profile core
    .venv/bin/python3 scripts/export_sn_schema.py --env SN_TEST --profile phoenix \\
        --out data/sn_schema_test.xlsx

Env prefix controls which instance — reads SN_<ENV>_INSTANCE_URL,
SN_<ENV>_USERNAME, SN_<ENV>_PASSWORD from .env.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

import httpx
import pandas as pd
import yaml
from dotenv import dotenv_values

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("export_sn_schema")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "schema_export.yaml"
ENV_PATH = PROJECT_ROOT / ".env"

PAGE_SIZE = 1000


# ──────────────────────────────────────────────────────────────────────
# SN client
# ──────────────────────────────────────────────────────────────────────
class SNClient:
    def __init__(self, url: str, user: str, pwd: str):
        self.url = url.rstrip("/")
        self.auth = (user, pwd)
        self.client = httpx.Client(
            timeout=httpx.Timeout(60.0, connect=15.0),
            auth=self.auth,
            headers={"Accept": "application/json"},
        )

    def fetch_all(
        self, table: str, query: str = "", fields: list[str] | None = None
    ) -> list[dict]:
        out: list[dict] = []
        offset = 0
        while True:
            params = {
                "sysparm_query": query,
                "sysparm_limit": PAGE_SIZE,
                "sysparm_offset": offset,
                "sysparm_exclude_reference_link": "true",
            }
            if fields:
                params["sysparm_fields"] = ",".join(fields)
            r = self.client.get(
                f"{self.url}/api/now/table/{table}", params=params
            )
            r.raise_for_status()
            batch = r.json().get("result", [])
            out.extend(batch)
            if len(batch) < PAGE_SIZE:
                return out
            offset += PAGE_SIZE


# ──────────────────────────────────────────────────────────────────────
# Profile resolution
# ──────────────────────────────────────────────────────────────────────
def resolve_profile(cfg: dict, profile_name: str) -> dict:
    profiles = cfg["profiles"]
    if profile_name not in profiles:
        raise SystemExit(
            f"Unknown profile '{profile_name}'. "
            f"Available: {list(profiles)}"
        )
    prof = dict(profiles[profile_name])
    # Flatten `extends` chain
    tables: list[str] = list(prof.get("tables", []))
    parent = prof.get("extends")
    while parent:
        parent_prof = profiles.get(parent) or {}
        tables = list(parent_prof.get("tables", [])) + tables
        parent = parent_prof.get("extends")
    # Dedup preserving order
    seen: set[str] = set()
    prof["tables"] = [t for t in tables if not (t in seen or seen.add(t))]
    return prof


def discover_custom_tables(
    client: SNClient, prefixes: list[str]
) -> list[str]:
    if not prefixes:
        return []
    query_parts = [f"nameSTARTSWITH{p}" for p in prefixes]
    query = "^OR".join(query_parts)
    rows = client.fetch_all(
        "sys_db_object", query=query, fields=["name"]
    )
    return sorted({r["name"] for r in rows if r.get("name")})


# ──────────────────────────────────────────────────────────────────────
# Extractors
# ──────────────────────────────────────────────────────────────────────
def extract_tables(client: SNClient, table_names: list[str]) -> pd.DataFrame:
    if not table_names:
        return pd.DataFrame(
            columns=["name", "label", "super_class", "scope", "sys_id"]
        )
    # Batch by 50 names to keep URL short
    rows: list[dict] = []
    for i in range(0, len(table_names), 50):
        chunk = table_names[i : i + 50]
        query = "nameIN" + ",".join(chunk)
        batch = client.fetch_all(
            "sys_db_object",
            query=query,
            fields=[
                "name",
                "label",
                "super_class.name",
                "sys_scope.scope",
                "sys_id",
                "sys_created_on",
                "sys_updated_on",
            ],
        )
        rows.extend(batch)
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = df.rename(
        columns={
            "super_class.name": "super_class",
            "sys_scope.scope": "scope",
        }
    )
    return df.sort_values("name").reset_index(drop=True)


def extract_fields(
    client: SNClient,
    table_names: list[str],
    skip_sys_fields: bool,
    max_per_table: int,
) -> pd.DataFrame:
    rows: list[dict] = []
    for name in table_names:
        query_parts = [f"name={name}", "elementISNOTEMPTY"]
        if skip_sys_fields:
            query_parts.append("elementNOT LIKEsys_")
        query = "^".join(query_parts)
        batch = client.fetch_all(
            "sys_dictionary",
            query=query,
            fields=[
                "name",
                "element",
                "column_label",
                "internal_type",
                "reference.name",
                "max_length",
                "mandatory",
                "default_value",
                "choice",
                "comments",
                "active",
            ],
        )
        for f in batch[:max_per_table]:
            rows.append(
                {
                    "table": f.get("name") or name,
                    "element": f.get("element"),
                    "label": f.get("column_label"),
                    "type": f.get("internal_type"),
                    "reference_table": f.get("reference.name") or "",
                    "max_length": f.get("max_length") or "",
                    "mandatory": f.get("mandatory") == "true",
                    "default_value": f.get("default_value") or "",
                    "has_choices": f.get("choice") in ("1", "3"),
                    "active": f.get("active") != "false",
                    "description": (f.get("comments") or "")[:500],
                }
            )
    return pd.DataFrame(rows)


def extract_choices(
    client: SNClient, table_names: list[str]
) -> pd.DataFrame:
    rows: list[dict] = []
    for i in range(0, len(table_names), 50):
        chunk = table_names[i : i + 50]
        query = "nameIN" + ",".join(chunk)
        batch = client.fetch_all(
            "sys_choice",
            query=query + "^inactive=false",
            fields=[
                "name",
                "element",
                "value",
                "label",
                "sequence",
                "hint",
            ],
        )
        for c in batch:
            rows.append(
                {
                    "table": c.get("name"),
                    "element": c.get("element"),
                    "value": c.get("value"),
                    "label": c.get("label"),
                    "sequence": c.get("sequence"),
                    "hint": (c.get("hint") or "")[:300],
                }
            )
    return pd.DataFrame(rows)


def extract_roles(client: SNClient) -> pd.DataFrame:
    batch = client.fetch_all(
        "sys_user_role",
        query="active=true",
        fields=[
            "name",
            "description",
            "elevated_privilege",
            "assignable_by",
            "requires_subscription",
            "sys_scope.scope",
        ],
    )
    rows = [
        {
            "name": r.get("name"),
            "description": (r.get("description") or "")[:500],
            "elevated_privilege": r.get("elevated_privilege") == "true",
            "assignable_by": r.get("assignable_by") or "",
            "requires_subscription": r.get("requires_subscription") or "",
            "scope": r.get("sys_scope.scope") or "global",
        }
        for r in batch
    ]
    return pd.DataFrame(rows).sort_values("name").reset_index(drop=True)


def extract_references(fields_df: pd.DataFrame) -> pd.DataFrame:
    """Derive references (FK-like edges) from fields_df."""
    if fields_df.empty:
        return pd.DataFrame(
            columns=["from_table", "from_field", "to_table"]
        )
    ref = fields_df[fields_df["reference_table"].astype(bool)]
    return ref[["table", "element", "reference_table"]].rename(
        columns={
            "table": "from_table",
            "element": "from_field",
            "reference_table": "to_table",
        }
    ).sort_values(["from_table", "from_field"]).reset_index(drop=True)


# ──────────────────────────────────────────────────────────────────────
# Driver
# ──────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--env",
        default="SN_TEST",
        help="Env var prefix (SN_TEST, SN_DEV)",
    )
    ap.add_argument("--profile", default="core", help="Profile name from config")
    ap.add_argument(
        "--out",
        default=None,
        help="Output .xlsx path (default: data/sn_schema_<env>_<profile>.xlsx)",
    )
    ap.add_argument(
        "--limit-tables",
        type=int,
        default=None,
        help="Dev shortcut: only process first N tables",
    )
    args = ap.parse_args()

    env = dotenv_values(str(ENV_PATH))
    url = env.get(f"{args.env}_INSTANCE_URL")
    user = env.get(f"{args.env}_USERNAME")
    pwd = env.get(f"{args.env}_PASSWORD")
    if not (url and user and pwd):
        ap.error(f"Missing {args.env}_INSTANCE_URL/USERNAME/PASSWORD in .env")

    with CONFIG_PATH.open("r") as f:
        cfg = yaml.safe_load(f)
    profile = resolve_profile(cfg, args.profile)
    export_cfg = cfg.get("export", {})

    client = SNClient(url, user, pwd)

    tables = list(profile["tables"])
    if profile.get("custom_prefixes"):
        logger.info(
            f"Discovering custom tables with prefixes "
            f"{profile['custom_prefixes']}..."
        )
        custom = discover_custom_tables(client, profile["custom_prefixes"])
        logger.info(f"Found {len(custom)} custom tables")
        tables.extend(custom)
    # Dedup
    seen: set[str] = set()
    tables = [t for t in tables if not (t in seen or seen.add(t))]
    if args.limit_tables:
        tables = tables[: args.limit_tables]
    logger.info(f"Exporting {len(tables)} tables from {url}")

    logger.info("Extracting table metadata...")
    tables_df = extract_tables(client, tables)
    logger.info(f"  → {len(tables_df)} tables")

    logger.info("Extracting field metadata (may take a minute)...")
    fields_df = extract_fields(
        client,
        tables,
        skip_sys_fields=export_cfg.get("skip_sys_fields", True),
        max_per_table=export_cfg.get("max_fields_per_table", 300),
    )
    logger.info(f"  → {len(fields_df)} fields")

    references_df = extract_references(fields_df)
    logger.info(f"  → {len(references_df)} references")

    choices_df = pd.DataFrame()
    if export_cfg.get("include_choices", True):
        logger.info("Extracting choice values...")
        choices_df = extract_choices(client, tables)
        logger.info(f"  → {len(choices_df)} choice rows")

    logger.info("Extracting roles...")
    roles_df = extract_roles(client)
    logger.info(f"  → {len(roles_df)} roles")

    # Config sheet for provenance
    config_df = pd.DataFrame(
        [
            {"key": "instance_url", "value": url},
            {"key": "env_prefix", "value": args.env},
            {"key": "profile", "value": args.profile},
            {"key": "tables_requested", "value": len(tables)},
            {"key": "tables_found", "value": len(tables_df)},
            {"key": "fields_total", "value": len(fields_df)},
            {
                "key": "exported_at_utc",
                "value": pd.Timestamp.utcnow().isoformat(),
            },
        ]
    )

    out_path = (
        Path(args.out)
        if args.out
        else PROJECT_ROOT
        / "data"
        / f"sn_schema_{args.env.lower()}_{args.profile}.xlsx"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Writing {out_path}...")
    with pd.ExcelWriter(out_path, engine="openpyxl") as xw:
        tables_df.to_excel(xw, sheet_name="Tables", index=False)
        fields_df.to_excel(xw, sheet_name="Fields", index=False)
        references_df.to_excel(xw, sheet_name="References", index=False)
        choices_df.to_excel(xw, sheet_name="Choices", index=False)
        roles_df.to_excel(xw, sheet_name="Roles", index=False)
        config_df.to_excel(xw, sheet_name="Config", index=False)
    logger.info(f"Done: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
