# Incident Management
Source: WebFetch (s2-labs.com, servicenow.com/community)

## Definition
Incident Management prevents unplanned incidents from hindering IT services. An incident is any unplanned service disruption or quality reduction.

## Lifecycle States
| State | Description |
|-------|-------------|
| New | Logged but not yet investigated |
| In Progress | Assigned and under investigation |
| On Hold | Paused — reasons: Awaiting Caller, Awaiting Change, Awaiting Problem, Awaiting Vendor |
| Resolved | Fix or workaround applied; resolution code + notes mandatory |
| Closed | Confirmed restored; becomes historical record |
| Canceled | Duplicate, unnecessary, or invalid |

**On Hold behavior:** If On Hold reason = "Awaiting Caller", incident moves to In Progress when caller updates it. All other On Hold reasons require manual state change.

## Priority Matrix (Impact × Urgency)
Priority is read-only and auto-calculated from Impact and Urgency fields.
- Impact: effect on business (High/Medium/Low)
- Urgency: how much delay can be tolerated (High/Medium/Low)
- Priority values: 1-Critical, 2-High, 3-Moderate, 4-Low
- Stored in data lookup rules (dl_u_priority table)

## SLA Behavior
- SLA timer starts at incident creation
- SLA cancels and restarts if priority changes
- On Hold pauses SLA (protects SLA integrity)
- SLA determined by Priority value

## 8-Step Process Flow
1. Detection & Logging — via phone, email, walk-ins, or automated channels
2. Notification & Escalation — alerts based on categorization
3. Categorization — category/sub-category for faster routing
4. Prioritization — based on impact, urgency, financial loss
5. Routing & Assignment — to Assignment Group with incident owner
6. Investigation & Diagnosis — within SLA timeframe
7. Resolution — temporary workaround or permanent fix
8. Closure — communicated to stakeholders; lessons logged

## Key Roles
- **End Users/Callers:** Report disruption and confirm restoration
- **Service Desk:** Intake and triage; data quality focus
- **Group Managers:** Workload and accountability
- **Level 3 Specialists (Resolvers):** Deep technical investigation

## Design Principles
- Anchor incidents to **services and CIs** (not just categories) — enables inherited assignment/escalation
- CSDM alignment is foundational — pre-defined service ownership enables automation
- On Hold must reflect genuine dependencies; avoid using as convenience
- Resolution requires documenting fix vs. workaround distinction

## Major Incident Management
- Separate portal for P1/P2 incidents
- Major Incident Manager role
- Dedicated communication channels
- PIR (Post-Incident Review) after closure

## Table
- Primary table: `incident` (extends `task`)
- Key fields: state, priority, impact, urgency, assignment_group, assigned_to, caller_id, category, subcategory, close_code, resolution_notes
