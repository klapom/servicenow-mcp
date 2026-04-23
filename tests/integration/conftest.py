"""Fixtures for integration tests — require a live Neo4j with the sn_mcp namespace.

Tests are marked `@pytest.mark.integration` and skip automatically if:
  - Neo4j is unreachable, OR
  - the sn_mcp namespace has no seed TABLE entities (import_sn_schema.py
    has not been run against this Neo4j yet).

Environment overrides (defaults target the local dev stack):
  NEO4J_URI       (default bolt://localhost:7687)
  NEO4J_USER      (default neo4j)
  NEO4J_PASSWORD  (default aegis-rag-neo4j-password)
"""
from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

pytest.importorskip("neo4j")
from neo4j import GraphDatabase  # noqa: E402

NAMESPACE = "sn_mcp"

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv(
    "NEO4J_PASSWORD", "aegis-rag-neo4j-password"
)


# OOTB ServiceNow tables — present in every instance regardless of customization.
# Used as generic anchors for graph-shape assertions so the suite works across
# customer installations.
OOTB_TABLES = ("task", "incident", "problem", "change_request", "sys_user")


@pytest.fixture(scope="session")
def neo4j_driver() -> Iterator:
    """Shared Neo4j driver; skips the module if the DB is unreachable."""
    try:
        driver = GraphDatabase.driver(
            NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
        driver.verify_connectivity()
    except Exception as e:  # pragma: no cover - skip path
        pytest.skip(f"Neo4j unreachable at {NEO4J_URI}: {e}")
    yield driver
    driver.close()


@pytest.fixture(scope="session")
def seeded_graph(neo4j_driver) -> None:
    """Ensure the graph has been seeded from *some* SN instance.

    Does not care *which* instance — only that at least the core OOTB tables
    are present as :Entity nodes with source='seed'. Skips otherwise.
    """
    with neo4j_driver.session() as s:
        count = s.run(
            "MATCH (t:Entity {sub_type:'TABLE', namespace_id:$ns}) "
            "WHERE t.name IN $names "
            "AND t.source IN ['seed', 'seed+doc'] "
            "RETURN count(t) AS c",
            ns=NAMESPACE,
            names=list(OOTB_TABLES),
        ).single()["c"]
    if count < 3:
        pytest.skip(
            f"Seed graph not populated in {NAMESPACE} namespace "
            f"(only {count}/{len(OOTB_TABLES)} OOTB tables found). "
            f"Run scripts/export_sn_schema.py + import_sn_schema.py first."
        )


@pytest.fixture(scope="session")
def knowledge_engine(neo4j_driver, seeded_graph):
    """An initialized ServiceNowKnowledgeMCP with only Neo4j wired up.

    Skips Qdrant/vLLM/Redis since graph smoke tests do not need them.
    """
    from servicenow_mcp.knowledge.config import ServiceNowConfig
    from servicenow_mcp.knowledge.knowledge_mcp import (
        ServiceNowKnowledgeMCP,
    )

    cfg = ServiceNowConfig.from_env()
    engine = ServiceNowKnowledgeMCP(cfg)
    engine.neo4j_driver = neo4j_driver  # bypass full connect()
    return engine
