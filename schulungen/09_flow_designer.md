---
source_type: platform
topics:
  - flow designer
  - automation
  - subflows
  - actions
  - triggers
  - workflow studio
  - IntegrationHub
  - no-code
---

# Flow Designer

## Overview

Flow Designer is ServiceNow's no-code/low-code automation platform for building process automations. It replaces the legacy Workflow Editor as the recommended tool for automating multi-step processes, approvals, integrations, and notifications.

Flow Designer is built on a component model: **Flows** orchestrate process logic, **Subflows** provide reusable logic blocks, and **Actions** encapsulate discrete operations (including integrations via IntegrationHub). Together they are managed in **Workflow Studio**.

ServiceNow recommends Flow Designer for new automation development. Use legacy Workflow Editor only for maintaining existing workflows that are too complex to migrate immediately.

---

## Core Components

### Flows
A Flow is an automated process triggered by a condition or schedule. It executes a sequence of steps including logic, approvals, tasks, notifications, and subflows.

**Key characteristics:**
- Triggered automatically (no user action required after setup)
- Visual, drag-and-drop step editor
- Supports conditional logic, loops, parallel paths
- Versioned — multiple versions can exist; one is active
- Scoped to an application (or Global)

### Subflows
Reusable blocks of logic that can be called from multiple Flows (or other Subflows). Analogous to functions/methods in traditional programming.

**When to use subflows:**
- Logic that appears in multiple flows (e.g., "send manager notification")
- Complex logic you want to isolate and test independently
- Shared business logic owned by a specific team

**Input/Output:** Subflows define input variables (passed in when called) and output variables (returned to the calling flow).

### Actions
Pre-built operations for specific tasks. Actions are the building blocks placed inside flows and subflows.

| Category | Examples |
|----------|---------|
| Record operations | Create Record, Update Record, Delete Record, Look Up Record |
| Approvals | Ask for Approval |
| Notifications | Send Email, Send Notification |
| Logic | Create Catalog Task |
| Utility | Log, Set Flow Variable, Wait |
| IntegrationHub | REST, SOAP, Slack, Jira, ServiceNow Spoke |
| AI/ML | Predict Category, Extract Data |

**Custom Actions:** Organizations can build custom actions for their specific integrations or reusable operations.

---

## Triggers

Triggers determine when a flow starts. ServiceNow provides three categories:

### Record-Based Triggers
| Trigger | When It Fires |
|---------|--------------|
| Created | A new record is inserted into the specified table |
| Updated | An existing record is updated (fields match trigger conditions) |
| Created or Updated | Either insertion or update |
| Deleted | A record is deleted |

**Trigger conditions:** Can include field-level conditions (e.g., "Fire when incident.state changes to 2 (In Progress)")

**Note on "Updated" trigger:** Set specific field conditions to avoid running flows on every record update. An unfiltered Updated trigger on `incident` would fire on every comment, work note, and field change.

### Schedule-Based Triggers
| Trigger | Description |
|---------|-------------|
| Daily | Runs every day at a specified time |
| Weekly | Runs on specific days of the week |
| Monthly | Runs on a specific day of the month |
| Run Once | Runs at a specific date/time, then deactivates |
| Repeat | Runs every N minutes/hours |

### Application-Based Triggers
| Trigger | Use Case |
|---------|---------|
| Service Catalog | RITM created or state changes — primary trigger for catalog fulfillment |
| SLA Task | SLA reaches a percentage threshold (25%, 50%, 75%, 100%) |
| Inbound Email | Incoming email matching criteria |
| MetricBase | Metric crosses a threshold |
| Kafka Message | Event from Kafka topic (requires EventManagement) |

---

## Flow Logic Components

### If / Else If / Else
Conditional branching based on data values:

```
If: incident.priority == 1 (Critical)
  → [steps for P1]
Else If: incident.priority == 2 (High)
  → [steps for P2]
Else
  → [steps for P3/P4]
```

### For Each
Iterate over a list of records returned by a lookup:

```
Look Up Records: Get all SCTASKs where request_item = RITM [sys_id]
For Each SCTASK:
  → Update Record: Set state = Closed Complete
```

### Do the Following Until
Loop until a condition becomes true:

```
Do the following until: task.state == 7 (Closed)
  → Wait for condition: [any update to the task]
  → If task.state == 3 (On Hold): Log warning
```

### Do the Following in Parallel
Run multiple branches simultaneously. All branches must complete before the flow continues:

```
Do the following in parallel:
  Branch 1: Send email to requester's manager
  Branch 2: Create SCTASK for fulfillment team
  Branch 3: Send Slack notification to channel
All branches complete → Continue flow
```

### Wait for Condition
Pause flow execution until a specified record condition becomes true. The flow consumes no resources while waiting.

```
Create Catalog Task (assignment_group = IT Procurement)
Wait for condition: Catalog Task.state = Closed Complete
→ Continue to next step
```

### Try/Catch
Error handling in flows:
```
Try:
  → REST action: POST to external API
Catch (any error):
  → Log error
  → Send notification to integration team
  → Update RITM with error message
```

---

## Approvals in Flow Designer

The **Ask for Approval** action is the standard mechanism for all approval workflows in Flow Designer.

### Ask for Approval Step Configuration

| Setting | Description |
|---------|-------------|
| Table | The record being approved (e.g., sc_req_item, change_request) |
| Record | The specific record (use data pill from trigger) |
| Approval field | Which approval field to update |
| Rules | Who approves and under what conditions |

### Approval Rules

| Rule Type | Description |
|-----------|-------------|
| Anyone Approves | First approval from any approver satisfies the requirement |
| Everyone Must Approve | All specified approvers must approve |
| Approve/Reject routing | Go to different branches based on outcome |

### Approval Outcomes
After the Ask for Approval step, the flow branches on:
- **Approved** → fulfillment path
- **Rejected** → rejection handling path (notify requester, close RITM)
- **Cancelled** → (optional) if approval request cancelled manually

### Specifying Approvers
Approvers can be specified as:
- **User:** Specific user (use data pill or hardcoded sys_id)
- **Group:** All members of a group, or any member
- **Dynamic:** Script returning a user or group
- **Reference field:** `current.requested_for.manager` (manager of the person requesting)

---

## Data Pills

Data pills are the mechanism for passing data between flow steps. They reference the output of previous steps.

Examples:
- `[Trigger]→Record→sys_id` — the sys_id of the record that triggered the flow
- `[Step 1 - Look Up Record]→Incident→priority` — priority from a looked-up record
- `[Step 2 - Ask for Approval]→Approval State` — result of approval step
- `[Step 3 - Create Record]→Record→sys_id` — sys_id of newly created record

Data pills prevent hardcoding and make flows reusable across different record contexts.

---

## Flow Variables

Flow variables store data that needs to be shared across multiple steps:

```
Set Flow Variable: escalation_required = false
For Each incident (priority = 1):
  Set Flow Variable: escalation_required = true
If escalation_required == true:
  → Send escalation notification
```

Variables are scoped to the flow execution instance — each flow run has its own variable state.

---

## IntegrationHub

IntegrationHub extends Flow Designer with pre-built spoke connectors for external systems:

| Spoke | System |
|-------|--------|
| REST | Any REST API |
| SOAP | Any SOAP service |
| Slack | Slack messaging |
| Microsoft Teams | Teams messaging |
| Jira | Jira issue management |
| ServiceNow | Cross-instance operations |
| AWS | Amazon Web Services |
| Azure | Microsoft Azure |
| Okta | Identity management |
| Workday | HR system |

### Connection Aliases
Connection Aliases store authentication credentials (OAuth tokens, API keys) separately from flow logic:
- Flow references the Connection Alias by name
- Credentials can be updated without modifying the flow
- Different aliases can be used in different environments (dev/test/prod)

---

## Flow Designer vs. Workflow Editor

| Feature | Flow Designer | Legacy Workflow Editor |
|---------|--------------|----------------------|
| Interface | Visual step-based editor | Drag-and-drop activity diagram |
| Skill required | No-code (business users) | Low-code (developers) |
| Performance | More efficient (condition evaluation) | Heavier; runs complete activity graph |
| Version control | Built-in versioning | Limited |
| IntegrationHub | Yes (native) | Via REST activity only |
| Parallel branches | Yes (native) | Limited |
| Recommended for new dev | Yes | No |
| Catalog fulfillment | Yes (primary approach) | Still supported |
| SLA escalation | Yes | Legacy approach |

### When to Still Use Workflow Editor
- Maintaining complex existing workflows where migration cost is high
- Specific execution sequencing requirements that rely on workflow activities
- Processes that must run synchronously in the same transaction as a Business Rule (Workflow Editor can run in-line, Flow Designer typically does not)

---

## Flow Execution Context

### How Flows Run
- Flows run in the background (asynchronously by default)
- They do not block the user's save action
- Flow execution is tracked in the `sys_flow_context` table
- Each step execution is logged in `sys_flow_action_instance`

### Execution User
By default, flows run as the user who triggered the action (the current session user). This can be overridden:
- Set "Run As" to a specific service account
- Important for flows that need elevated permissions not available to all users

### Flow Activation and Versioning
- Only one version of a flow can be active at a time
- New versions can be created and tested before activating
- Deactivating a flow does not cancel in-progress executions

---

## Testing and Debugging

### Test Flow
The "Test" button in Flow Designer opens a test dialog:
- Provide a record to run the flow against
- Execute in a controlled context
- Review step-by-step execution results
- Check outputs and errors for each step

### Execution Detail
Navigate to Process Automation → Flow Designer → Executions:
- See all flow runs with status (Waiting, Running, Completed, Error)
- Click an execution to see step-by-step results and data values
- Error details available for each failed step

### Logging
Use the "Log" action in flows for debug output:
```
Log: "Approval outcome: " + [Ask for Approval]→Approval State
```
Log entries visible in System Logs → Application Log.

---

## Best Practices

### Flow Architecture
- **Single Purpose:** Each flow should do one thing well. Complex processes should use subflows for discrete phases.
- **Reusability:** Extract any logic used in multiple flows into a Subflow with documented inputs/outputs
- **Naming conventions:**
  - Flows: `[Process] - [Trigger Event]` (e.g., "Incident - Priority 1 Escalation")
  - Subflows: `[Action]` (e.g., "Notify Manager with SLA Status")
  - Actions: `[Verb] [Object]` (e.g., "Create Default Change Tasks")

### Performance
- Add specific conditions to Updated triggers — avoid running flows on every field change
- Use Wait for Condition rather than polling loops
- Avoid retrieving large record sets in For Each loops — filter aggressively
- Use Connection Aliases for all external integrations (enables credential rotation without flow changes)

### Error Handling
- Add Try/Catch around external API calls
- Log errors with meaningful context (record number, step name, error message)
- Send notifications to an integration operations team for persistent errors
- Use Flow error emails (configured in Flow properties) for automatic alerting

### Governance
- Test all flows in development/test environment before production deployment
- Document flow purpose in the Description field
- Use Application Scoping to control which applications own each flow
- Version flows before making changes — allows rollback if issues arise

---

## Common Patterns

### Service Catalog Fulfillment with Approval
```
Trigger: Service Catalog — RITM Created
1. Ask for Approval: requested_for.manager
2. If Approved:
   → Create Catalog Task: assignment_group = IT Provisioning
   → Wait for Condition: Catalog Task closed
   → Send Email: "Your request is fulfilled"
   → Update RITM: stage = Closed, state = Closed Complete
3. If Rejected:
   → Send Email: "Your request was denied — [reason]"
   → Update RITM: stage = Rejected, state = Closed Incomplete
```

### Incident P1 Escalation
```
Trigger: Record Updated — incident, When: priority changes to 1
1. Update Record: assignment_group = Major Incident Team
2. Do in Parallel:
   Branch A: Send Email to MIM distribution list
   Branch B: Post to Slack #major-incidents
   Branch C: Create bridge conference call link (Zoom action)
3. Create Work Note on incident: "P1 escalation actions completed"
4. Wait for Condition: incident.state = 6 (Resolved)
5. Send Email: Resolution notification to stakeholders
```

### Change Conflict Notification
```
Trigger: Record Updated — change_request, When: state changes to Scheduled
1. Look Up Records: change_conflict where change = [this record]
2. If conflicts found:
   → For Each conflict:
     → Send Email to change.assignment_group.manager
     → Create Work Note: "Conflict detected with CHG[number]"
   → Update Record: on_hold = true, on_hold_reason = "Conflict review required"
```
