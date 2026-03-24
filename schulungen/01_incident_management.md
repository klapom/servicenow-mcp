---
source_type: process
topics:
  - incident management
  - ITSM
  - SLA
  - priority matrix
  - major incident
  - task table
---

# Incident Management

## Overview

Incident Management is the ITSM process responsible for restoring normal service operation as quickly as possible following an unplanned disruption, minimizing adverse impact on business operations. An incident is defined as any unplanned interruption to an IT service or reduction in the quality of an IT service.

The primary goal of Incident Management is **speed of restoration**, not root cause analysis. It is a reactive process with a strong SLA-driven urgency component. Longer-term root cause work is handed off to Problem Management.

ServiceNow implements Incident Management through the `incident` table, which extends the base `task` table, inheriting all common task fields and behavior.

---

## Core Concepts

### Incident vs. Request vs. Problem

| Dimension | Incident | Service Request | Problem |
|-----------|----------|-----------------|---------|
| Trigger | Unplanned disruption | User or business need | Recurring incidents or known error |
| Goal | Restore service fast | Fulfill demand | Eliminate root cause |
| SLA type | Resolution SLA | Fulfillment SLA | Target date |
| Table | `incident` | `sc_req_item` | `problem` |
| Reactive/Proactive | Reactive | Both | Both |

### What qualifies as an incident
- System outage or unavailability
- Performance degradation below agreed thresholds
- Security breach or suspected breach
- Failed change causing service disruption
- Application errors preventing business operations

---

## Lifecycle States

The incident state machine drives SLA behavior, routing logic, and communication triggers.

| State | Numeric Value | Description |
|-------|--------------|-------------|
| New | 1 | Logged but not yet assigned or investigated |
| In Progress | 2 | Assigned to a resolver; active investigation underway |
| On Hold | 3 | Work paused — requires a mandatory On Hold reason |
| Resolved | 6 | Fix or workaround applied; resolution code and notes are mandatory |
| Closed | 7 | Confirmed restored; becomes a historical read-only record |
| Canceled | 8 | Duplicate, invalid, or unnecessary — removed from active queue |

### On Hold Behavior

On Hold is a protected state with four sub-reasons that govern automated behavior:

| On Hold Reason | Automatic Transition Back |
|---------------|--------------------------|
| Awaiting Caller | Automatically moves to In Progress when the caller adds a work note or comment |
| Awaiting Change | Manual state change required after linked change completes |
| Awaiting Problem | Manual state change required after linked problem is resolved |
| Awaiting Vendor | Manual state change required after vendor response received |

**Design principle:** On Hold should reflect genuine external dependencies, not be used to artificially pause SLA timers. SLA integrity depends on accurate state usage.

### State Transition Rules

```
New → In Progress (assignment)
In Progress → On Hold (blocked by dependency)
On Hold → In Progress (dependency resolved)
In Progress → Resolved (fix applied)
Resolved → Closed (automatic after configured days, or manual)
Resolved → In Progress (reopened — caller disputes resolution)
Any state → Canceled (validated as invalid)
```

---

## Priority Matrix

Priority is a **read-only, auto-calculated field** derived from Impact and Urgency. It cannot be set manually by the resolver. This design ensures consistent prioritization across the organization.

### Impact Definition
Impact measures the effect on the business, typically defined by number of users affected or criticality of the affected service:
- **High (1):** Entire organization or critical business function affected
- **Medium (2):** Department or multiple users affected
- **Low (3):** Single user or non-critical function affected

### Urgency Definition
Urgency measures how much delay can be tolerated before significant business impact occurs:
- **High (1):** Immediate action required; every hour matters
- **Medium (2):** Action required within hours
- **Low (3):** Action can be deferred to next business cycle

### Priority Calculation Matrix

| | Urgency: High | Urgency: Medium | Urgency: Low |
|---|---|---|---|
| **Impact: High** | 1 - Critical | 2 - High | 3 - Moderate |
| **Impact: Medium** | 2 - High | 3 - Moderate | 4 - Low |
| **Impact: Low** | 3 - Moderate | 4 - Low | 4 - Low |

Priority values and their SLA targets:
| Priority | Label | Typical Response SLA | Typical Resolution SLA |
|----------|-------|---------------------|----------------------|
| 1 | Critical | 15 minutes | 1 hour |
| 2 | High | 1 hour | 4 hours |
| 3 | Moderate | 4 hours | 8 hours |
| 4 | Low | 8 hours | 3 business days |

**Technical note:** The priority calculation matrix is stored in the `dl_u_priority` table (Data Lookup rules). Administrators can modify the mapping without scripting.

---

## SLA Behavior

SLA timers are managed through the `task_sla` table and the `contract_sla` SLA Definition records.

### Key SLA Rules for Incidents

1. **SLA timer starts at incident creation** (retroactive start applies if created via email or integration)
2. **Priority change cancels and restarts the SLA** — the new priority's SLA attaches fresh
3. **On Hold pauses the SLA clock** — elapsed time is preserved; SLA resumes on state change back to In Progress
4. **Resolved state stops the Resolution SLA** — the task_sla record transitions to Completed or Breached
5. **Response SLA** measures time to first assignment; **Resolution SLA** measures time to Resolved state

### SLA Breach Notifications
- **50%** of resolution time elapsed: Notifies assignee and CI's "Supported by" contact
- **75%** of resolution time elapsed: Notifies assignee and their manager
- **100%** (breach): Notifies assignee, manager, and assignment group manager

---

## 8-Step Incident Process Flow

### Step 1: Detection and Logging
Incidents are detected and created through multiple channels:
- **Self-service:** End users submit via Service Portal or Employee Center
- **Service Desk:** Phone, walk-in, email intake; agent creates incident record
- **Automated monitoring:** Integration with monitoring tools (SolarWinds, Dynatrace, SCOM) creates incidents via REST API or Import Sets
- **Email inbound action:** Inbound email rules parse emails and auto-create incidents

Key fields to capture at creation:
- Short Description, Description
- Caller (caller_id — reference to sys_user)
- Category, Subcategory
- Service, Service Offering, Business Service
- Configuration Item (cmdb_ci)
- Impact, Urgency (drives Priority)
- Contact type (phone, email, self-service, monitoring)

### Step 2: Notification and Escalation
- Automated notifications fire based on categorization and priority
- Assignment Group managers receive notifications for P1/P2 incidents
- Major Incident workflow triggers for Critical incidents meeting criteria

### Step 3: Categorization
Categorization drives routing, reporting, and SLA selection:
- **Category:** High-level service domain (Hardware, Software, Network, Security, Application)
- **Subcategory:** Specific area within category (e.g., Software → Email, Software → ERP)

Best practice: Anchor incidents to a **Configuration Item** (CI) and **Business Service**. When a CI is selected, the assignment group and support group can be inherited automatically from the CI's "Support group" and "Managed by group" fields.

### Step 4: Prioritization
Priority is auto-calculated from Impact and Urgency. SLA attaches immediately. Resolvers should not attempt to lower priority to avoid SLA breach; this is a governance and audit concern.

### Step 5: Routing and Assignment
- **Assignment Group:** The team responsible (e.g., "Network Operations", "Desktop Support")
- **Assigned To:** The individual resolver within the group
- Assignment can be automatic via Assignment Rules, Skills-Based Routing (AWA), or manual
- CI-based routing: Assignment group inherited from the CI record

### Step 6: Investigation and Diagnosis
- Work notes document investigation steps (internal only — not visible to caller)
- Known error articles are checked in the Knowledge Base
- Problem records are linked if a systemic issue is identified
- Escalation to L2/L3 if L1 cannot resolve within SLA threshold

### Step 7: Resolution
Resolution requires:
- **Close Code (close_code):** Category of resolution (e.g., "Solved (Permanently)", "Solved (Work Around)", "Not Solved (Not Reproducible)")
- **Resolution Notes (close_notes):** Human-readable description of what was done
- A distinction must be documented between permanent fix and workaround

### Step 8: Closure
- Incident moves to Closed state automatically after configured number of days post-resolution (default: 3 days in most configurations)
- Stakeholders receive closure notification
- Lessons learned may be logged as Knowledge Article
- For Major Incidents: Post-Incident Review (PIR) is mandatory before closure

---

## Key Roles

| Role | Responsibilities |
|------|----------------|
| End User / Caller | Reports the disruption; confirms service restoration at closure |
| Service Desk Agent | Intake, triage, categorization, initial diagnosis; data quality owner |
| Assignment Group Manager | Workload oversight; SLA accountability; escalation decisions |
| L2/L3 Resolver (Specialist) | Deep technical investigation; root cause determination within incident scope |
| Major Incident Manager | Coordinates P1/P2 response; manages communication bridge; owns PIR |
| Problem Manager | Receives escalated incidents for root cause analysis |

### ServiceNow Roles for Incident Management

| Role Name | Access Level |
|-----------|-------------|
| `itil` | Create, read, update incidents; standard resolver role |
| `itil_admin` | Full incident management including reassignment and override |
| `sn_incident_read` | Read-only access to incidents |
| `major_incident_manager` | Access to major incident portal and P1/P2 workflows |

---

## Major Incident Management

Major incidents are P1 (Critical) incidents with widespread business impact that require a coordinated response beyond normal channels.

### Criteria for Major Incident
- Priority 1 (Critical) incidents
- Multiple VIP users affected
- Business-critical systems unavailable
- Revenue-impacting outage

### Major Incident Process
1. **Identification:** Triggered when incident reaches Priority 1 or manually promoted
2. **Major Incident Manager assignment:** Dedicated coordinator takes ownership
3. **Communication bridge opened:** War room (Teams/Zoom) with all stakeholders
4. **Stakeholder notifications:** Executive-level communications at defined intervals
5. **Timeline tracking:** All actions documented with timestamps
6. **Resolution:** Standard resolution with additional stakeholder sign-off
7. **Post-Incident Review (PIR):** Mandatory retrospective within 5 business days

### Major Incident Portal
ServiceNow provides a dedicated Major Incident Management portal showing:
- Active major incidents and their current state
- Timeline of actions and communications
- Linked change records and known errors
- PIR status tracking

---

## Table Structure

### Primary Table: `incident`
Extends `task`. All `task` fields are inherited.

| Field Name | Type | Description |
|-----------|------|-------------|
| `number` | String | Auto-generated INC number (e.g., INC0001234) |
| `caller_id` | Reference → sys_user | The user reporting the incident |
| `state` | Integer (choice) | Current lifecycle state |
| `impact` | Integer (choice) | Business impact (1-3) |
| `urgency` | Integer (choice) | Time sensitivity (1-3) |
| `priority` | Integer (choice) | Auto-calculated (1-4) |
| `category` | String (choice) | Service domain |
| `subcategory` | String (choice) | Specific area within category |
| `assignment_group` | Reference → sys_user_group | Responsible team |
| `assigned_to` | Reference → sys_user | Individual resolver |
| `cmdb_ci` | Reference → cmdb_ci | Affected configuration item |
| `business_service` | Reference → cmdb_ci | Affected business service |
| `hold_reason` | Integer (choice) | On Hold sub-reason |
| `close_code` | String (choice) | Resolution category |
| `close_notes` | String | Resolution description |
| `resolved_at` | DateTime | When incident was resolved |
| `resolved_by` | Reference → sys_user | Who resolved it |
| `reopen_count` | Integer | Number of times reopened |
| `made_sla` | Boolean | Whether resolution SLA was met |
| `knowledge` | Boolean | Flag to create KB article from incident |

### Related Tables

| Table | Relationship | Purpose |
|-------|-------------|---------|
| `task_sla` | One-to-many | SLA instances attached to incident |
| `sys_journal_field` | One-to-many | Work notes and comments |
| `incident_task` | One-to-many | Sub-tasks within incident |
| `problem_task` | Many-to-many | Linked problem records |
| `change_request` | Many-to-many | Linked change records |
| `kb_knowledge` | Many-to-many | Linked knowledge articles |

---

## Design Principles and Best Practices

### CSDM Alignment
Linking incidents to Business Services and Configuration Items (CIs) is foundational:
- Enables automatic assignment group population from CI ownership data
- Supports service impact reporting (which services are most affected)
- Feeds Problem Management with data on systemic issues
- Enables CI-based escalation and notification routing

### Resolution Quality
- **Always document the distinction** between permanent fix and workaround in close_notes
- Resolution notes should be written for the next person encountering the same issue
- Enable "Knowledge" checkbox when resolution could benefit others — triggers KB article creation workflow

### State Discipline
- Do not use On Hold to artificially pause SLA timers without a genuine dependency
- Reopening incidents (moving Resolved back to In Progress) increments `reopen_count` — track this metric for quality management
- Canceled incidents should have a documented reason in work notes

### Categorization Accuracy
- Category/subcategory should be reviewed and corrected post-resolution, not just at intake
- Accurate categorization drives trend analysis in Problem Management and Performance Analytics

### Performance Considerations
- Avoid custom Business Rules on the incident table that perform synchronous GlideRecord queries — use Async Business Rules or Flow Designer flows
- Index custom fields added to incident for reporting performance
- Use Assignment Rules to automate routing rather than manual dispatcher workflows

---

## Common Patterns

### Auto-Assignment via CI
When `cmdb_ci` is populated, a Business Rule or Flow can copy the CI's `support_group` to `assignment_group`. This reduces manual routing work and ensures the correct team receives the incident immediately.

### Email-to-Incident Integration
Inbound email actions parse incoming emails to:
- Create new incidents (subject line → short_description)
- Update existing incidents by INC number in subject
- Set state to In Progress when response received from resolver

### Monitoring Integration
Monitoring tools (Dynatrace, Nagios, Zabbix) push alerts via REST API:
- Alert maps to a CI in the CMDB
- Incident created or updated automatically
- Alert clears when monitoring resolves → incident auto-resolved

### Knowledge Article Creation
After resolving a P1/P2 incident:
1. Resolver checks the `knowledge` checkbox on the incident
2. Incident KCS Article template maps short_description and close_notes to KB fields
3. Article enters Draft state and routes for review
4. Published article is linked back to the incident and future similar incidents

### SLA Breach Response Automation
Flow Designer flow triggered at 75% SLA elapsed:
1. Sends notification to assignee and manager
2. Creates a work note on the incident with escalation timestamp
3. Optionally reassigns to escalation group if still unassigned
