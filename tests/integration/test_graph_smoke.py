"""Smoke tests for graph_traverse against a live Neo4j seeded from any SN.

Assertions rely only on OOTB ServiceNow entities (task, incident,
change_request, sys_user, cmdb_ci) that exist on every instance — so the
suite runs unchanged on PHOENIX, a PDI, or any customer deployment.

Skips cleanly if Neo4j is unreachable or the seed graph is missing.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


# ══════════════════════════════════════════════════════════════════════
# Shape / correctness of low-level graph helpers
# ══════════════════════════════════════════════════════════════════════
def test_incident_extends_task(knowledge_engine) -> None:
    """Core inheritance — incident must extend task on any SN instance."""
    extensions = knowledge_engine._graph_table_extensions("task")
    children = {e["child_table"] for e in extensions}
    # incident, problem, change_request are ALL OOTB task descendants.
    assert "incident" in children, (
        f"Expected 'incident' among task children, got {children}"
    )


def test_task_has_standard_fields(knowledge_engine) -> None:
    """Every SN has these OOTB task fields; assert presence, not exhaustive set."""
    fields = knowledge_engine._graph_table_fields("task")
    names = {f["field"] for f in fields}
    expected_subset = {"assigned_to", "assignment_group", "state", "priority"}
    missing = expected_subset - names
    assert not missing, f"OOTB task fields missing from graph: {missing}"


def test_reference_types_populated(knowledge_engine) -> None:
    """Seed fields must carry field_type metadata (the whole point of the import)."""
    fields = knowledge_engine._graph_table_fields("task")
    typed = [f for f in fields if f.get("field_type")]
    assert len(typed) >= 10, (
        f"Expected ≥10 task fields with field_type, got {len(typed)}"
    )


def test_reference_edge_to_sys_user(knowledge_engine) -> None:
    """assigned_to on task is a reference to sys_user in every SN."""
    fields = knowledge_engine._graph_table_fields("task")
    assigned_to = next(
        (f for f in fields if f["field"] == "assigned_to"), None
    )
    assert assigned_to is not None, "assigned_to field missing on task"
    assert assigned_to["references_table"] == "sys_user", (
        f"assigned_to should reference sys_user, got "
        f"{assigned_to['references_table']!r}"
    )


# ══════════════════════════════════════════════════════════════════════
# Path-finding
# ══════════════════════════════════════════════════════════════════════
def test_path_incident_to_task(knowledge_engine) -> None:
    """EXTENDS relation reachable via shortestPath."""
    path = knowledge_engine._graph_find_path("incident", "task")
    assert path, "No path found from incident → task"
    rel_types = [step["rel_type"] for step in path]
    assert "EXTENDS" in rel_types, f"Expected EXTENDS in path, got {rel_types}"


def test_path_incident_to_sys_user_via_reference(knowledge_engine) -> None:
    """Incident → sys_user must be discoverable via the caller_id reference."""
    path = knowledge_engine._graph_find_path("incident", "sys_user")
    assert path, "No path from incident → sys_user (caller_id edge missing?)"
    # Expect either direct HAS_FIELD→REFERENCES or through inherited task field
    rel_types = [step["rel_type"] for step in path]
    assert "REFERENCES" in rel_types, (
        f"sys_user must be reached via REFERENCES edge, got {rel_types}"
    )


# ══════════════════════════════════════════════════════════════════════
# High-level graph_traverse behaviour
# ══════════════════════════════════════════════════════════════════════
def test_graph_search_returns_structured_payload(knowledge_engine) -> None:
    """The top-level orchestrator must return the expected dict shape."""
    result = knowledge_engine._graph_search(
        "fields of incident", start_node="incident"
    )
    assert isinstance(result, dict)
    assert "fields_of_incident" in result
    assert len(result["fields_of_incident"]) > 0


def test_not_found_signal_for_unknown_table(knowledge_engine) -> None:
    """Unknown start_node must surface an explicit not_found marker."""
    result = knowledge_engine._graph_search(
        "Tell me about sn_fake_xyz_does_not_exist",
        start_node="sn_fake_xyz_does_not_exist",
    )
    assert result.get("not_found") == ["sn_fake_xyz_does_not_exist"], (
        f"Expected not_found signal, got keys {list(result)}"
    )
    # Must NOT leak noisy keyword results when the only input was bogus
    assert "knowledge_nodes" not in result, (
        "Unknown start_node should short-circuit, not fall through to "
        "keyword search"
    )


def test_keyword_search_drops_english_stopwords(knowledge_engine) -> None:
    """Regression: question with only stopwords must not flood knowledge_nodes.

    Earlier versions matched .description on 3-char tokens like 'the',
    'which', 'are' → every role description leaked into results.
    """
    result = knowledge_engine._graph_search(
        "What are the tables which extend task?", start_node="task"
    )
    knodes = result.get("knowledge_nodes", [])
    # If keyword stopwording works, the stopword-only parts of the question
    # produce no matches; any node that appears must actually contain one
    # of the meaningful tokens in its *name* (not just description).
    meaningful_tokens = {"task"}  # "extend"/"tables" are in stopword list
    for kn in knodes:
        name_lower = (kn.get("name") or "").lower()
        assert any(tok in name_lower for tok in meaningful_tokens), (
            f"Knowledge node {kn.get('name')!r} matched on stopwords "
            f"only — stopword filter regressed"
        )


# ══════════════════════════════════════════════════════════════════════
# Provenance / source merging (only meaningful if doc extraction also ran)
# ══════════════════════════════════════════════════════════════════════
def test_seed_and_doc_coexist_when_both_populated(
    knowledge_engine, neo4j_driver
) -> None:
    """If the doc-extraction pipeline has also run, verify source merging."""
    with neo4j_driver.session() as s:
        doc_count = s.run(
            "MATCH (e:Entity {namespace_id:'sn_mcp'}) "
            "WHERE e.source IN ['doc', 'seed+doc'] RETURN count(e) AS c"
        ).single()["c"]
    if doc_count == 0:
        pytest.skip("Doc extraction not run — source merging not applicable")

    with neo4j_driver.session() as s:
        merged = s.run(
            "MATCH (e:Entity {namespace_id:'sn_mcp', source:'seed+doc'}) "
            "RETURN count(e) AS c"
        ).single()["c"]
    assert merged > 0, (
        "Both seed and doc entities exist but none merged — key scheme "
        "divergence between import_sn_schema.py and extract_sn_entities.py"
    )
