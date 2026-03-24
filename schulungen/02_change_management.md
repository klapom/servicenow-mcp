---
source_type: process
topics:
  - change management
  - CAB
  - change types
  - change workflow
  - risk assessment
  - ITSM
---

# Change Management

## Overview

Change Management is the ITSM process that governs the lifecycle of all changes to IT services and infrastructure. Its purpose is to ensure that standardized methods and procedures are used for efficient and prompt handling of all changes, minimizing the impact of change-related incidents and improving day-to-day operations.

In ServiceNow, Change Management is implemented through the `change_request` table (extending `task`), with child change tasks in the `change_task` table. Out-of-the-box, six workflow types cover the most common change scenarios, from routine standard changes to complex DevOps pipelines.

A "change" in ITSM terms is any modification to the IT environment that could affect services, including software deployments, configuration updates, hardware replacements, and network reconfigurations.

---

## Core Concepts

### Why Change Management Matters
Without a controlled change process:
- Uncoordinated changes cause unexpected outages
- Change conflicts (two teams modifying the same system simultaneously) go undetected
- No audit trail for compliance and forensic analysis
- No ability to perform structured rollback (backout)

### Change vs. Incident vs. Problem

| Dimension | Change | Incident | Problem |
|-----------|--------|----------|---------|
| Purpose | Controlled modification | Service restoration | Root cause elimination |
| Planned? | Yes (except emergency) | No | Partially |
| Triggers CAB? | Sometimes | No | No |
| Has backout plan? | Yes | No | No |
| Table | `change_request` | `incident` | `problem` |

---

## Change Types

### Standard Change
- Pre-authorized, low-risk changes that follow a fully documented and approved procedure
- Risk has been assessed and deemed acceptable in advance
- No CAB approval required per occurrence — approval was granted when the standard change template was created
- Examples: routine password resets, standard software deployments to a pre-approved list, recurring certificate renewals
- Lifecycle: New → Scheduled → Implement → Closed

### Normal Change
- Any change that is not standard or emergency
- Requires full assessment, review, and authorization (CAB approval for high/moderate risk)
- Examples: new software deployments, infrastructure upgrades, significant configuration changes
- Lifecycle: New → Assess → Authorize → Scheduled → Implement → Review → Closed

### Emergency Change
- Required for urgent situations that cannot wait for normal approval cycles
- Used when there is an active incident or imminent risk of a production outage
- Approved by Emergency CAB (ECAB) — a subset of CAB members who can be convened quickly
- Post-implementation review is mandatory
- Lifecycle: New → Authorize → Scheduled → Implement → Review → Closed (bypasses group/peer review)

---

## Six Out-of-the-Box Workflow Types

ServiceNow ships with six pre-built change workflow templates:

| # | Workflow Name | Description | When to Use |
|---|--------------|-------------|-------------|
| 1 | Default Normal Change Management | Full review cycle: Coordinator → Manager → CAB → Implement → Close | Standard enterprise changes |
| 2 | Default Standard Change Management | Simplified: Coordinator → Change Manager → Implement | Pre-approved repeatable changes |
| 3 | Default Emergency Change Management | Coordinator direct OR ECAB (all members OR any one member) | Production/network emergencies |
| 4 | Default Break Fix Change Management | Minor fixes: Coordinator → Change Management review | Quick break-fix scenarios |
| 5 | Major Change Management | Multi-team, complex flow with IT Support evaluation | Large-scale infrastructure changes |
| 6 | DevOps Change Management | SSH/Release Automation: Assessment → Plan → CAB → Build → Test → Implement | CI/CD pipeline integration |

---

## State Progression

### Normal Change States

```
New → Assess → Authorize → Scheduled → Implement → Review → Closed
```

| State | Description | Key Activities |
|-------|-------------|---------------|
| New | Change request created | Initial data entry; basic validation |
| Assess | Impact and risk evaluated | Risk assessment completion; planning documents |
| Authorize | CAB/approver review | CAB voting; approval or rejection |
| Scheduled | Approved and planned | Implementation window confirmed; resources assigned |
| Implement | Work in progress | Change tasks executed; implementation team working |
| Review | Post-implementation review | Verification that change achieved desired outcome |
| Closed | Change completed | Final documentation; lessons learned |

### Standard Change States (Simplified)

```
New → Scheduled → Implement → Closed
```

### Emergency Change States

```
New → Authorize → Scheduled → Implement → Review → Closed
```

Note: Emergency changes bypass the Assess state and go directly to Authorize (ECAB).

---

## CAB (Change Advisory Board)

The Change Advisory Board is the governance body that reviews and approves high-risk and moderate-risk normal changes.

### CAB Structure

| Group | Composition | Scope |
|-------|-------------|-------|
| CAB | IT management, architects, operations leads, business representatives | Normal changes with high/moderate risk |
| ECAB | On-call CAB subset (available 24/7) | Emergency changes requiring immediate approval |
| Local CAB | Departmental or regional advisory group | Low-moderate changes within a specific domain |

### CAB Process in ServiceNow

1. Change reaches **Authorize** state
2. High and moderate-risk changes **automatically** generate CAB approval request
3. CAB members receive notification with change details, risk assessment, and planning documents
4. Members vote: Approve or Reject (with mandatory reason for rejection)
5. **Approval outcome:**
   - All required approvals received → change moves to Scheduled
   - Any rejection → change returns to New (or Assess) with rejection reason populated
6. Change Coordinator reviews rejections and either revises the plan or cancels

### CAB Approval Logic

ServiceNow CAB approvals are implemented via the approval engine (`sysapproval_approver` table):
- One approval record per CAB member
- State transitions: Requested → Approved / Rejected / Not Yet Requested
- Change state advances when approval conditions are satisfied (all approved, or majority approved, depending on configuration)

---

## Risk Assessment

Risk levels drive the approval workflow selected:

| Risk Level | Description | CAB Required |
|-----------|-------------|-------------|
| High | Significant potential impact; complex change; new technology | Yes — full CAB |
| Moderate | Moderate impact; tested procedure with some unknowns | Yes — CAB required |
| Low | Minimal impact; well-understood procedure | No — manager approval only |
| None | Trivial change with no service impact | No — self-authorized |

### Risk Assessment Fields

| Field | Purpose |
|-------|---------|
| `risk` | Overall risk level (High/Moderate/Low) |
| `impact` | Scope of impact on services and users |
| `justification` | Business reason for the change |
| `backout_plan` | Documented steps to revert if change fails |
| `test_plan` | How the change will be validated |
| `implementation_plan` | Step-by-step execution instructions |
| `change_plan` | High-level change description and objectives |

Risk can also be calculated via the **Risk Calculator** — a questionnaire that generates a risk score based on answers to questions about change scope, testing, and rollback options.

---

## Key Roles

| Role | Responsibilities |
|------|----------------|
| Change Initiator / Requestor | Identifies the need for change; submits the request |
| Change Coordinator | Creates, updates, and manages the change record; ensures documentation quality; submits to CAB |
| Change Manager | Reviews changes; approves/rejects; chairs CAB meetings; owns the process |
| CAB Member | Reviews changes in Authorize state; votes approve/reject |
| Implementer | Executes the change tasks during the implementation window |
| Change Owner | Accountable for the change delivering the stated outcome |

### ServiceNow Roles for Change Management

| Role Name | Access |
|-----------|--------|
| `itil` | Create and read change requests |
| `change_coordinator` | Full change lifecycle management; submit to CAB |
| `change_manager` | Approve, reject, override change states |
| `change_approver_user` | Approve changes assigned to them |
| `cab_manager` | Manage CAB meetings and agendas |

---

## Change Tasks (`change_task`)

Change tasks are the individual work items within a change request. They represent discrete steps performed by different teams or individuals.

| Field | Description |
|-------|-------------|
| `change_task.state` | Open, Work in Progress, Closed Complete, Closed Incomplete |
| `change_task.assignment_group` | Team responsible for this specific task |
| `change_task.assigned_to` | Individual performing the task |
| `change_task.planned_start_date` | When this task should begin |
| `change_task.planned_end_date` | When this task should complete |
| `change_task.type` | Planning, Implementation, Testing, Review |

A change request moves to Closed only when all child change tasks are closed.

---

## Table Structure

### Primary Table: `change_request`
Extends `task`.

| Field Name | Type | Description |
|-----------|------|-------------|
| `number` | String | Auto-generated CHG number (e.g., CHG0001234) |
| `type` | String (choice) | standard, normal, emergency |
| `state` | Integer (choice) | Current lifecycle state |
| `risk` | Integer (choice) | Risk level |
| `impact` | Integer (choice) | Impact level |
| `priority` | Integer (choice) | Business priority |
| `category` | String (choice) | Change category |
| `assignment_group` | Reference → sys_user_group | Responsible team |
| `assigned_to` | Reference → sys_user | Change coordinator |
| `start_date` | DateTime | Planned implementation start |
| `end_date` | DateTime | Planned implementation end |
| `cab_required` | Boolean | Whether CAB review is required |
| `cab_date_time` | DateTime | Scheduled CAB meeting time |
| `change_plan` | String (HTML) | Change plan documentation |
| `backout_plan` | String (HTML) | Rollback procedure |
| `test_plan` | String (HTML) | Testing/validation plan |
| `implementation_plan` | String (HTML) | Step-by-step implementation |
| `justification` | String | Business justification |
| `cmdb_ci` | Reference → cmdb_ci | Primary CI being changed |
| `business_service` | Reference → cmdb_ci | Affected business service |
| `on_hold` | Boolean | Whether change is currently on hold |
| `on_hold_reason` | String | Reason for on-hold status |
| `close_code` | String (choice) | Outcome: Successful, Unsuccessful, Canceled |
| `close_notes` | String | Post-implementation notes |

### Related Tables

| Table | Purpose |
|-------|---------|
| `change_task` | Individual implementation tasks within the change |
| `sysapproval_approver` | Approval records for CAB members |
| `change_conflict` | Detected conflicts with other changes |
| `change_collision` | CI-level collision detection with other changes |
| `task_sla` | SLA instances (if configured) |
| `incident` | Linked incidents that triggered the change |
| `problem` | Linked problem records (root cause change) |

---

## Conflict Detection

ServiceNow Change Management includes built-in conflict detection:

### Types of Conflicts
1. **CI Conflict:** Two changes are scheduled on the same CI within overlapping implementation windows
2. **Blackout Period Conflict:** Change is scheduled during a defined maintenance blackout window
3. **Maintenance Window Conflict:** Change is outside its designated maintenance window

Conflicts are surfaced in the **Conflicts** related list on the change record and can block state transitions if conflict prevention is enabled.

---

## DevOps Change Management

Modern organizations integrate Change Management with CI/CD pipelines via the **DevOps Change Management** plugin:

- Automated change requests created from pipeline tools (Jenkins, GitLab, Azure DevOps)
- Change state updated programmatically as pipeline stages progress
- Standard and normal change templates mapped to pipeline workflows
- Approval gates in the pipeline check ServiceNow change state before proceeding

---

## Best Practices

### Planning Documentation
- Every change must have a completed `backout_plan` before reaching Authorize state
- `test_plan` should specify success criteria, not just test steps
- `implementation_plan` should be detailed enough for a different team to execute

### Change Freeze Windows
Define blackout periods (typically around major business events, year-end, holidays):
- Navigate to Change → Administration → Blackout Schedules
- Changes scheduled during blackout periods generate conflicts
- Emergency changes may override blackout periods with explicit ECAB approval

### Standard Change Template Governance
- Review standard change templates annually
- Require re-authorization if the procedure changes
- Track standard change usage to ensure templates remain current and relevant

### Metrics to Track
| Metric | Purpose |
|--------|---------|
| Change success rate | Percentage of changes closed as "Successful" |
| Change-induced incidents | Incidents caused by failed or unplanned changes |
| Emergency change ratio | Emergency changes as % of total — should be low |
| CAB rejection rate | Indication of change quality at submission |
| Lead time | Average time from New to Implement |
| Change freeze compliance | Changes attempted during blackout periods |

---

## Common Patterns

### Change Triggered by Problem Resolution
When Problem Management identifies a root cause requiring infrastructure modification:
1. Problem moves to "Fix in Progress" state
2. Problem record automatically or manually creates a `change_request`
3. Change record is linked back to the problem via related list
4. When change closes successfully, problem can advance to Resolved

### Emergency Change for Incident Resolution
For P1 incidents requiring a production configuration change:
1. Incident Manager requests Emergency Change
2. Change Coordinator creates change with type = Emergency
3. ECAB approves via phone/Teams/email and records approval in ServiceNow
4. Change implemented; incident resolved
5. Post-implementation review completed within 24 hours

### Standard Change Template Creation Process
1. Identify a change that has been performed multiple times successfully
2. Document the procedure completely including risk mitigation
3. Submit for Change Manager approval as a Standard Change Template
4. Once approved, future instances use the template without individual CAB review
5. Track usage and review template effectiveness quarterly
