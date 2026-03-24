#!/usr/bin/env python3
"""
Build the ServiceNow knowledge graph in Neo4j.

Node types:
  - Table     — ServiceNow tables (incident, change_request, cmdb_ci, ...)
  - Field     — Table fields (state, priority, assigned_to, ...)
  - Process   — ITIL processes (Incident Management, Change Management, ...)
  - State     — Workflow/lifecycle states (New, In Progress, Resolved, ...)
  - Role      — ServiceNow roles (itil, admin, change_manager, ...)
  - Pattern   — Implementation patterns (approval flows, SLA configs, ...)

Edge types:
  - EXTENDS        — Table inheritance (incident -> task)
  - HAS_FIELD      — Table owns a field (incident -> state)
  - USES_TABLE     — Process operates on table (Incident Management -> incident)
  - HAS_STATE      — Table has a lifecycle state (incident -> New)
  - TRANSITIONS_TO — State transition (New -> In Progress)
  - TRIGGERED_BY   — Business rule/flow trigger (e.g. triggered by priority change)
  - REQUIRES_ROLE  — Process/table requires a role (Change Management -> change_manager)
  - APPLIES_TO     — Pattern applies to table/process (Approval Pattern -> change_request)
  - RELATED_TO     — Generic relationship between knowledge nodes
  - REFERENCES     — Field references another table (assigned_to -> sys_user)

Usage:
    python scripts/build_sn_graph.py [--rebuild]
    python scripts/build_sn_graph.py --neo4j-uri bolt://localhost:7687
"""

import argparse
import logging
import os

from neo4j import GraphDatabase

logger = logging.getLogger(__name__)

NAMESPACE = "sn_mcp"


def clear_namespace(session) -> None:
    """Delete all nodes and edges in the sn_mcp namespace."""
    session.run(
        "MATCH (n {namespace_id: $ns}) DETACH DELETE n",
        ns=NAMESPACE,
    )
    logger.info(f"Cleared all nodes in namespace '{NAMESPACE}'.")


def create_constraints(session) -> None:
    """Create uniqueness constraints for key node types."""
    constraints = [
        ("Table", "name"),
        ("Field", "qualified_name"),
        ("Process", "name"),
        ("State", "qualified_name"),
        ("Role", "name"),
        ("Pattern", "name"),
    ]
    for label, prop in constraints:
        try:
            session.run(
                f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE (n.{prop}, n.namespace_id) IS UNIQUE"
            )
        except Exception as e:
            logger.warning(f"Could not create constraint for {label}.{prop}: {e}")


# ── Core table definitions ───────────────────────────────────────────────────
# These are hardcoded examples for the most important ServiceNow tables.
# TODO: In production, populate this from:
#   - sys_db_object (table definitions)
#   - sys_dictionary (field definitions)
#   - sys_documentation (field descriptions)
#   - ServiceNow REST API: /api/now/table/sys_db_object
#   - Exported XML/JSON from the instance

CORE_TABLES = {
    "task": {
        "description": "Base table for all task-based records in ServiceNow",
        "extends": None,  # Root table
        "fields": {
            "number": {"type": "string", "description": "Auto-generated unique task number"},
            "state": {"type": "integer", "description": "Current lifecycle state of the task"},
            "priority": {"type": "integer", "description": "Priority (1=Critical, 2=High, 3=Moderate, 4=Low)"},
            "assigned_to": {"type": "reference", "description": "User assigned to this task", "ref_table": "sys_user"},
            "assignment_group": {"type": "reference", "description": "Group assigned to this task", "ref_table": "sys_user_group"},
            "short_description": {"type": "string", "description": "Brief summary of the task"},
            "description": {"type": "string", "description": "Detailed description"},
            "opened_by": {"type": "reference", "description": "User who opened this task", "ref_table": "sys_user"},
            "opened_at": {"type": "glide_date_time", "description": "Date/time when the task was opened"},
            "closed_at": {"type": "glide_date_time", "description": "Date/time when the task was closed"},
            "work_notes": {"type": "journal", "description": "Internal work notes (not visible to caller)"},
            "comments": {"type": "journal", "description": "Additional comments (visible to caller)"},
            "sys_created_on": {"type": "glide_date_time", "description": "Record creation timestamp"},
            "sys_updated_on": {"type": "glide_date_time", "description": "Record last update timestamp"},
        },
    },
    "incident": {
        "description": "Incident records for IT service disruptions and requests",
        "extends": "task",
        "fields": {
            "caller_id": {"type": "reference", "description": "User who reported the incident", "ref_table": "sys_user"},
            "category": {"type": "string", "description": "Incident category (e.g. Network, Hardware, Software)"},
            "subcategory": {"type": "string", "description": "Incident subcategory"},
            "impact": {"type": "integer", "description": "Impact level (1=High, 2=Medium, 3=Low)"},
            "urgency": {"type": "integer", "description": "Urgency level (1=High, 2=Medium, 3=Low)"},
            "severity": {"type": "integer", "description": "Severity level (1=High, 2=Medium, 3=Low)"},
            "resolved_by": {"type": "reference", "description": "User who resolved the incident", "ref_table": "sys_user"},
            "resolved_at": {"type": "glide_date_time", "description": "Date/time of resolution"},
            "close_code": {"type": "string", "description": "Closure code (Solved, Not Solved, etc.)"},
            "close_notes": {"type": "string", "description": "Closure notes"},
            "problem_id": {"type": "reference", "description": "Related problem record", "ref_table": "problem"},
            "caused_by": {"type": "reference", "description": "Change that caused this incident", "ref_table": "change_request"},
        },
    },
    "change_request": {
        "description": "Change request records for planned IT changes",
        "extends": "task",
        "fields": {
            "type": {"type": "string", "description": "Change type (Standard, Normal, Emergency)"},
            "risk": {"type": "integer", "description": "Risk assessment level"},
            "impact": {"type": "integer", "description": "Impact assessment level"},
            "category": {"type": "string", "description": "Change category"},
            "start_date": {"type": "glide_date_time", "description": "Planned start date"},
            "end_date": {"type": "glide_date_time", "description": "Planned end date"},
            "cab_required": {"type": "boolean", "description": "Whether CAB approval is required"},
            "cab_date": {"type": "glide_date_time", "description": "CAB meeting date"},
            "implementation_plan": {"type": "string", "description": "Implementation plan details"},
            "backout_plan": {"type": "string", "description": "Backout/rollback plan"},
            "test_plan": {"type": "string", "description": "Testing plan"},
            "review_status": {"type": "string", "description": "Peer review status"},
        },
    },
    "problem": {
        "description": "Problem records for root cause analysis of recurring incidents",
        "extends": "task",
        "fields": {
            "category": {"type": "string", "description": "Problem category"},
            "subcategory": {"type": "string", "description": "Problem subcategory"},
            "cause_notes": {"type": "string", "description": "Root cause analysis notes"},
            "fix_notes": {"type": "string", "description": "Fix/workaround notes"},
            "known_error": {"type": "boolean", "description": "Whether this is a known error"},
            "first_reported_by_task": {"type": "reference", "description": "First incident that reported this problem", "ref_table": "incident"},
            "related_incidents": {"type": "integer", "description": "Count of related incidents"},
        },
    },
    "cmdb_ci": {
        "description": "Base configuration item table in the CMDB",
        "extends": None,
        "fields": {
            "name": {"type": "string", "description": "CI display name"},
            "asset_tag": {"type": "string", "description": "Asset tag identifier"},
            "serial_number": {"type": "string", "description": "Serial number"},
            "category": {"type": "string", "description": "CI category (Hardware, Software, etc.)"},
            "subcategory": {"type": "string", "description": "CI subcategory"},
            "operational_status": {"type": "integer", "description": "Operational status (1=Operational, 2=Non-Operational, etc.)"},
            "install_status": {"type": "integer", "description": "Install status"},
            "assigned_to": {"type": "reference", "description": "User responsible for this CI", "ref_table": "sys_user"},
            "support_group": {"type": "reference", "description": "Support group for this CI", "ref_table": "sys_user_group"},
            "location": {"type": "reference", "description": "Physical location", "ref_table": "cmn_location"},
            "company": {"type": "reference", "description": "Company that owns this CI", "ref_table": "core_company"},
        },
    },
    "kb_knowledge": {
        "description": "Knowledge base articles for self-service and agent reference",
        "extends": None,
        "fields": {
            "number": {"type": "string", "description": "Knowledge article number (KB00xxxxx)"},
            "short_description": {"type": "string", "description": "Article title/summary"},
            "text": {"type": "html", "description": "Article body content (HTML)"},
            "kb_knowledge_base": {"type": "reference", "description": "Knowledge base this article belongs to", "ref_table": "kb_knowledge_base"},
            "kb_category": {"type": "reference", "description": "Article category", "ref_table": "kb_category"},
            "workflow_state": {"type": "string", "description": "Publication state (draft, review, published, retired)"},
            "author": {"type": "reference", "description": "Article author", "ref_table": "sys_user"},
            "valid_to": {"type": "glide_date", "description": "Expiration date"},
            "rating": {"type": "float", "description": "Average user rating"},
            "view_count": {"type": "integer", "description": "Number of views"},
        },
    },
}


# ── ITIL process definitions ─────────────────────────────────────────────────
# TODO: Expand with more detailed subprocess/activity nodes from documentation.
# TODO: Link to actual training material source files once indexed.

PROCESSES = [
    {
        "name": "Incident Management",
        "description": "Restore normal service operation as quickly as possible and minimize adverse impact on business operations",
        "tables": ["incident"],
        "roles": ["itil", "incident_manager"],
        "tags": ["ITSM", "incident", "service restoration", "SLA"],
        "source_file": None,  # TODO: link to indexed doc
    },
    {
        "name": "Change Management",
        "description": "Control the lifecycle of all changes to enable beneficial changes with minimum disruption to IT services",
        "tables": ["change_request"],
        "roles": ["itil", "change_manager", "cab_approver"],
        "tags": ["ITSM", "change", "CAB", "approval", "risk assessment"],
        "source_file": None,
    },
    {
        "name": "Problem Management",
        "description": "Prevent problems and resulting incidents, eliminate recurring incidents, and minimize impact of unavoidable incidents",
        "tables": ["problem"],
        "roles": ["itil", "problem_manager"],
        "tags": ["ITSM", "problem", "root cause", "known error", "workaround"],
        "source_file": None,
    },
    {
        "name": "Knowledge Management",
        "description": "Share perspectives, ideas, experience, and information to ensure these are available in the right place at the right time",
        "tables": ["kb_knowledge"],
        "roles": ["knowledge_manager", "knowledge_author"],
        "tags": ["KCS", "knowledge", "self-service", "articles"],
        "source_file": None,
    },
    {
        "name": "Configuration Management",
        "description": "Maintain information about configuration items required to deliver IT services, including their relationships",
        "tables": ["cmdb_ci"],
        "roles": ["itil", "cmdb_editor", "asset_manager"],
        "tags": ["CMDB", "configuration", "CI", "discovery", "relationships"],
        "source_file": None,
    },
]


# ── State definitions ────────────────────────────────────────────────────────
# TODO: Pull actual state choices from sys_choice table via REST API.
# TODO: Add transition rules from business rules / workflow activities.

STATES = {
    "incident": [
        {"value": 1, "label": "New", "transitions_to": ["In Progress", "On Hold"]},
        {"value": 2, "label": "In Progress", "transitions_to": ["On Hold", "Resolved"]},
        {"value": 3, "label": "On Hold", "transitions_to": ["In Progress"]},
        {"value": 6, "label": "Resolved", "transitions_to": ["Closed", "In Progress"]},
        {"value": 7, "label": "Closed", "transitions_to": []},
    ],
    "change_request": [
        {"value": -5, "label": "New", "transitions_to": ["Assess"]},
        {"value": -4, "label": "Assess", "transitions_to": ["Authorize", "New"]},
        {"value": -3, "label": "Authorize", "transitions_to": ["Scheduled", "Assess"]},
        {"value": -2, "label": "Scheduled", "transitions_to": ["Implement"]},
        {"value": -1, "label": "Implement", "transitions_to": ["Review"]},
        {"value": 0, "label": "Review", "transitions_to": ["Closed"]},
        {"value": 3, "label": "Closed", "transitions_to": []},
    ],
    "problem": [
        {"value": 1, "label": "New", "transitions_to": ["Assess"]},
        {"value": 2, "label": "Assess", "transitions_to": ["Root Cause Analysis", "New"]},
        {"value": 3, "label": "Root Cause Analysis", "transitions_to": ["Fix in Progress"]},
        {"value": 4, "label": "Fix in Progress", "transitions_to": ["Resolved"]},
        {"value": 5, "label": "Resolved", "transitions_to": ["Closed"]},
        {"value": 7, "label": "Closed", "transitions_to": []},
    ],
}


# ── Role definitions ─────────────────────────────────────────────────────────
# TODO: Pull actual roles from sys_user_role and sys_user_has_role tables.

ROLES = [
    {"name": "admin", "description": "Full system administrator with unrestricted access"},
    {"name": "itil", "description": "Standard ITSM user role for incident, problem, change, and CMDB access"},
    {"name": "incident_manager", "description": "Manages the incident management process, handles major incidents"},
    {"name": "change_manager", "description": "Manages the change management process, chairs CAB meetings"},
    {"name": "problem_manager", "description": "Manages the problem management process and root cause analysis"},
    {"name": "cab_approver", "description": "Change Advisory Board member with approval authority"},
    {"name": "knowledge_manager", "description": "Manages knowledge base content and publication workflow"},
    {"name": "knowledge_author", "description": "Creates and maintains knowledge base articles"},
    {"name": "cmdb_editor", "description": "Edits configuration items in the CMDB"},
    {"name": "asset_manager", "description": "Manages IT asset lifecycle and inventory"},
]


# ── Graph population ─────────────────────────────────────────────────────────

def populate_tables(session) -> None:
    """Create Table and Field nodes with EXTENDS and HAS_FIELD edges."""
    for table_name, table_def in CORE_TABLES.items():
        # Create Table node
        session.run(
            """
            MERGE (t:Table {name: $name, namespace_id: $ns})
            SET t.description = $desc
            """,
            name=table_name, ns=NAMESPACE, desc=table_def["description"],
        )

        # Create EXTENDS edge
        if table_def["extends"]:
            session.run(
                """
                MATCH (child:Table {name: $child, namespace_id: $ns})
                MATCH (parent:Table {name: $parent, namespace_id: $ns})
                MERGE (child)-[:EXTENDS]->(parent)
                """,
                child=table_name, parent=table_def["extends"], ns=NAMESPACE,
            )

        # Create Field nodes and HAS_FIELD edges
        for field_name, field_def in table_def["fields"].items():
            qualified_name = f"{table_name}.{field_name}"
            session.run(
                """
                MERGE (f:Field {qualified_name: $qname, namespace_id: $ns})
                SET f.name = $fname, f.field_type = $ftype, f.description = $desc
                WITH f
                MATCH (t:Table {name: $tname, namespace_id: $ns})
                MERGE (t)-[:HAS_FIELD]->(f)
                """,
                qname=qualified_name, ns=NAMESPACE,
                fname=field_name, ftype=field_def["type"], desc=field_def["description"],
                tname=table_name,
            )

            # Create REFERENCES edge for reference fields
            if field_def.get("ref_table"):
                # Ensure the referenced table exists (it might not be in CORE_TABLES)
                session.run(
                    """
                    MERGE (rt:Table {name: $ref_table, namespace_id: $ns})
                    WITH rt
                    MATCH (f:Field {qualified_name: $qname, namespace_id: $ns})
                    MERGE (f)-[:REFERENCES]->(rt)
                    """,
                    ref_table=field_def["ref_table"], ns=NAMESPACE,
                    qname=qualified_name,
                )

    logger.info(f"Created {len(CORE_TABLES)} tables with fields.")


def populate_processes(session) -> None:
    """Create Process nodes with USES_TABLE and REQUIRES_ROLE edges."""
    for proc in PROCESSES:
        session.run(
            """
            MERGE (p:Process {name: $name, namespace_id: $ns})
            SET p.description = $desc,
                p.tags = $tags,
                p.source_file = $source_file
            """,
            name=proc["name"], ns=NAMESPACE, desc=proc["description"],
            tags=proc["tags"], source_file=proc.get("source_file"),
        )

        # USES_TABLE edges
        for table_name in proc["tables"]:
            session.run(
                """
                MATCH (p:Process {name: $pname, namespace_id: $ns})
                MATCH (t:Table {name: $tname, namespace_id: $ns})
                MERGE (p)-[:USES_TABLE]->(t)
                """,
                pname=proc["name"], tname=table_name, ns=NAMESPACE,
            )

        # REQUIRES_ROLE edges
        for role_name in proc["roles"]:
            session.run(
                """
                MATCH (p:Process {name: $pname, namespace_id: $ns})
                MERGE (r:Role {name: $rname, namespace_id: $ns})
                MERGE (p)-[:REQUIRES_ROLE]->(r)
                """,
                pname=proc["name"], rname=role_name, ns=NAMESPACE,
            )

    logger.info(f"Created {len(PROCESSES)} processes with relationships.")


def populate_states(session) -> None:
    """Create State nodes with HAS_STATE and TRANSITIONS_TO edges."""
    for table_name, states in STATES.items():
        for state_def in states:
            qualified_name = f"{table_name}.{state_def['label']}"
            session.run(
                """
                MERGE (s:State {qualified_name: $qname, namespace_id: $ns})
                SET s.name = $label, s.value = $value, s.table_name = $tname
                WITH s
                MATCH (t:Table {name: $tname, namespace_id: $ns})
                MERGE (t)-[:HAS_STATE]->(s)
                """,
                qname=qualified_name, ns=NAMESPACE,
                label=state_def["label"], value=state_def["value"], tname=table_name,
            )

        # Create TRANSITIONS_TO edges
        for state_def in states:
            for target_label in state_def["transitions_to"]:
                src_qname = f"{table_name}.{state_def['label']}"
                tgt_qname = f"{table_name}.{target_label}"
                session.run(
                    """
                    MATCH (s:State {qualified_name: $src, namespace_id: $ns})
                    MATCH (t:State {qualified_name: $tgt, namespace_id: $ns})
                    MERGE (s)-[:TRANSITIONS_TO]->(t)
                    """,
                    src=src_qname, tgt=tgt_qname, ns=NAMESPACE,
                )

    logger.info(f"Created states for {len(STATES)} tables with transitions.")


def populate_roles(session) -> None:
    """Create/update Role nodes with descriptions."""
    for role in ROLES:
        session.run(
            """
            MERGE (r:Role {name: $name, namespace_id: $ns})
            SET r.description = $desc, r.tags = []
            """,
            name=role["name"], ns=NAMESPACE, desc=role["description"],
        )
    logger.info(f"Created/updated {len(ROLES)} roles.")


# TODO: Add more population functions as the knowledge base grows:
#
# def populate_business_rules(session) -> None:
#     """Create BusinessRule nodes linked to tables via TRIGGERED_BY edges.
#     Source: sys_script table — export via REST API or XML."""
#     pass
#
# def populate_acls(session) -> None:
#     """Create ACL nodes linked to tables and roles.
#     Source: sys_security_acl table."""
#     pass
#
# def populate_ui_policies(session) -> None:
#     """Create UIPolicy nodes linked to tables.
#     Source: sys_ui_policy table."""
#     pass
#
# def populate_workflows(session) -> None:
#     """Create Workflow nodes with activity chains.
#     Source: wf_workflow and wf_activity tables."""
#     pass
#
# def populate_flow_designer(session) -> None:
#     """Create Flow nodes from Flow Designer definitions.
#     Source: sys_hub_flow table."""
#     pass
#
# def populate_from_instance(session, instance_url, credentials) -> None:
#     """Pull live data from a ServiceNow instance via REST API.
#     Queries sys_db_object, sys_dictionary, sys_choice, sys_documentation
#     to build a complete graph of the instance schema."""
#     pass


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    parser = argparse.ArgumentParser(description="Build ServiceNow knowledge graph in Neo4j")
    parser.add_argument("--neo4j-uri", default=os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    parser.add_argument("--neo4j-user", default=os.getenv("NEO4J_USER", "neo4j"))
    parser.add_argument("--neo4j-password", default=os.getenv("NEO4J_PASSWORD", "aegis-rag-neo4j-password"))
    parser.add_argument("--rebuild", action="store_true", help="Clear existing sn_mcp graph before building")
    args = parser.parse_args()

    logger.info(f"Connecting to Neo4j at {args.neo4j_uri}...")
    driver = GraphDatabase.driver(
        args.neo4j_uri,
        auth=(args.neo4j_user, args.neo4j_password),
    )
    driver.verify_connectivity()
    logger.info("Connected.")

    with driver.session(database="neo4j") as session:
        if args.rebuild:
            clear_namespace(session)

        logger.info("Creating constraints...")
        create_constraints(session)

        logger.info("Populating tables and fields...")
        populate_tables(session)

        logger.info("Populating ITIL processes...")
        populate_processes(session)

        logger.info("Populating states and transitions...")
        populate_states(session)

        logger.info("Populating roles...")
        populate_roles(session)

    driver.close()
    logger.info("Graph build complete.")


if __name__ == "__main__":
    main()
