---
source_type: process
topics:
  - approvals
  - approval engine
  - sysapproval
  - multi-level approvals
  - approval workflows
  - change approvals
  - catalog approvals
---

# Approval Engine

## Overview

ServiceNow's approval engine manages formal approval requests for records — determining who must approve, in what order, and what happens when they approve or reject. Approvals are used in Change Management (CAB authorization), Service Catalog fulfillment (manager sign-off), HR cases, financial approvals, and any other process requiring explicit authorization.

The approval engine is implemented through the `sysapproval_approver` table (individual approval records) and integrated into Flow Designer, legacy Workflows, and rules-based mechanisms.

---

## Core Tables

### `sysapproval_approver` — Approval Records
Each row represents one person's approval request for one specific record.

| Field | Description |
|-------|-------------|
| `sys_id` | Unique identifier |
| `document_id` | sys_id of the record being approved (e.g., change request) |
| `sysapproval` | Reference to the parent record (same as document_id in most cases) |
| `approver` | Reference to `sys_user` — who must approve |
| `state` | requested, approved, rejected, not_yet_requested, cancelled |
| `comments` | Approver's notes when approving or rejecting |
| `due_date` | When the approval is expected |
| `source_table` | Table of the record being approved |
| `approval_source` | How the approval was created (user_input, script, workflow) |
| `group` | Reference to `sys_user_group` (for group-level approvals) |
| `wf_activity` | Reference to workflow activity that created this approval |

### `sysapproval_group` — Group Approval Records
Used when an approval is assigned to a group rather than an individual:
- One `sysapproval_group` record per group
- Individual `sysapproval_approver` records auto-created for each group member

### `approval` field on parent records
The parent record (e.g., `change_request.approval`, `sc_req_item.approval`) reflects the consolidated approval state:

| Value | Meaning |
|-------|---------|
| `not requested` | No approval has been requested yet |
| `requested` | One or more approval requests are pending |
| `approved` | All required approvals have been granted |
| `rejected` | At least one required approver has rejected |
| `cancelled` | Approval process was cancelled |

---

## Approval States

### Individual Approval State Machine

```
not_yet_requested → requested → approved
                              ↘ rejected
                    ↓
                 cancelled
```

| State | Description |
|-------|-------------|
| `not_yet_requested` | Approval record created but not yet active (queued in multi-step) |
| `requested` | Active — approver has been notified and must respond |
| `approved` | Approver granted approval |
| `rejected` | Approver denied approval |
| `cancelled` | Approval cancelled (e.g., record was withdrawn or superseded) |

### Approval on Parent Record

The `approval` field on the parent record reflects the aggregate state:
- Any `rejected` → parent approval = `rejected`
- All required = `approved` → parent approval = `approved`
- Any `requested` active, none rejected → parent approval = `requested`

---

## Approval Mechanisms

### 1. Flow Designer — Ask for Approval Action

The modern, recommended approach. The "Ask for Approval" action in Flow Designer:

```
Ask for Approval:
  Table: change_request
  Record: [data pill: trigger record]
  Approval Field: approval
  Rules:
    - Anyone approves: User = "change_manager_sys_id"
    - Everyone approves: Group = "CAB Group"
  Due in: 3 days

→ Approved branch: continue flow
→ Rejected branch: handle rejection
→ Cancelled branch: (optional)
```

**Approval rules in Flow Designer:**

| Rule | Behavior |
|------|---------|
| Anyone Approves | First approval from any specified approver satisfies the requirement |
| Everyone Must Approve | All specified approvers must grant approval |

### 2. Legacy Workflow — Approval Activities

For existing legacy workflows:

| Activity | Description |
|----------|-------------|
| `Approval - User` | Request approval from a specific user |
| `Approval - Group` | Request approval from group members |
| `Approval - Coordinator` | Request from assigned coordinator |
| `Wait for Approval` | Pause workflow until approval state changes |

### 3. Rules-Based Approvals (Catalog)

For Service Catalog items without explicit flows, approval rules can auto-generate approval requests:

**Navigation:** Service Catalog → Catalog Policy → Approval Policy

Conditions-based auto-approval creation:
- "If RITM price > $500, request approval from requested_for.manager"
- "If category = Software, request approval from software_licensing_team"

---

## Multi-Level Approvals

Multi-level approvals require sequential approvals from different approvers — each level is triggered only after the previous level approves.

### Sequential Approval Pattern in Flow Designer

```
Level 1: Ask for Approval — Manager
  ↓ Approved
Level 2: Ask for Approval — Director
  ↓ Approved
Level 3: Ask for Approval — CAB Group (Everyone approves)
  ↓ Approved
→ Proceed with fulfillment
```

### Implementation via Workflow (Legacy)
Approval activities are chained with transitions:
```
[Approval - Manager] → (approved) → [Approval - Director] → (approved) → [Continue]
                    ↘ (rejected)  ↓                        ↘ (rejected) ↓
                              [Reject notification and close]
```

### Parallel Approvals
Multiple approvals can run simultaneously using Flow Designer's "Do the following in parallel" block:

```
Do in parallel:
  Branch A: Ask for Approval — Security Team
  Branch B: Ask for Approval — Finance Team
  Branch C: Ask for Approval — Technical Architect

All branches complete (all approved)
  → Continue to implementation
Any rejection
  → Reject handler
```

---

## Approval for Change Management

### Normal Change CAB Approval Flow

Standard ServiceNow CAB approval process:

1. Change reaches **Authorize** state
2. System evaluates risk — if High or Moderate:
   - `cab_required` = true
   - CAB approval group's members receive `sysapproval_approver` records
3. CAB members vote in ServiceNow (UI action: Approve / Reject)
4. When all required CAB members approve → change state transitions to Scheduled
5. If any member rejects → change returns to Assess with rejection reason

### CAB Approval Configuration
- CAB group: `sys_user_group` record with CAB members
- Approval rule: "All members must approve" OR "Any member approves" depending on organization policy
- Email notifications: `change_request.authorized` event triggers CAB notification
- CAB meeting scheduling: `cab_date_time` field on change_request

### Emergency Change (ECAB)
For emergency changes:
- A smaller ECAB group (subset of CAB) handles approval
- "Anyone approves" rule (one ECAB member sufficient)
- Speed is prioritized over thoroughness
- Post-implementation review is mandatory

---

## Approval for Service Catalog

### RITM-Level Approval

The most common catalog approval pattern: manager approval for the requesting user.

**Flow Designer implementation:**
```javascript
// In Flow Designer: Ask for Approval step
Table: sc_req_item
Record: [Trigger RITM]
Approver: [Trigger RITM].requested_for.manager

// Script to get manager:
var requestedFor = fd_data.trigger.current.requested_for;
var manager = requestedFor.manager;
// Pass manager sys_id as approver
```

**Direct field reference in flow:**
- Approver: `[Trigger Record]→Requested For→Manager`

### Handling Manager Absence
When a manager is absent or inactive:
```javascript
// Script Action or Flow Script step: Find active manager or skip-level
function getActiveManager(userSysId) {
    var user = new GlideRecord('sys_user');
    user.get(userSysId);
    var manager = user.manager.toString();

    // Check if manager is active
    var mgr = new GlideRecord('sys_user');
    if (mgr.get(manager) && mgr.active.toString() === 'true') {
        return manager;
    }
    // Escalate to skip-level
    if (mgr.active.toString() !== 'true' && !mgr.manager.nil()) {
        return getActiveManager(mgr.sys_id.toString()); // Recursive
    }
    // No active manager found — route to default approver group
    return gs.getProperty('catalog.default.approver_group', '');
}
```

---

## Approving and Rejecting

### UI Actions on `sysapproval_approver`
When an approver opens a record with a pending approval request, they see:
- **Approve** button: Sets `sysapproval_approver.state = approved`
- **Reject** button: Opens dialog for rejection reason; sets state = rejected

### Approving via Email
If email-based approval is configured:
- Approver receives email with approval request details
- Email contains clickable "Approve" and "Reject" links
- Clicking updates the `sysapproval_approver` record without requiring login

### Approving via Mobile
ServiceNow Mobile App surfaces approval requests:
- Push notification when new approval is assigned
- Quick approve/reject directly from notification or mobile UI

### Approving via REST API
External systems can approve programmatically:
```http
PATCH /api/now/table/sysapproval_approver/{sys_id}
{
    "state": "approved",
    "comments": "Approved via automated compliance check"
}
```

---

## Approval Delegation

When an approver is unavailable, they can delegate approval authority:

**Navigation:** Self-Service → Approval Delegation (or via user profile)

| Setting | Description |
|---------|-------------|
| Delegate | The user to receive delegated approvals |
| Active | Whether delegation is currently in effect |
| Date range | From/to dates for the delegation period |
| Table | Which type of approval requests are delegated (or All) |

When delegation is active:
- Delegated approvals appear in the delegate's approval queue
- The original approver's name still shows on the approval record
- The delegate approves "on behalf of"

---

## Approval Notifications

### Standard Approval Notification Flow
1. Approval request created (`sysapproval_approver` state = requested)
2. Event `approval.requested` fires
3. Notification sent to approver with:
   - Record details (summary of what is being approved)
   - Approve/Reject buttons (embedded links)
   - Due date for response
   - Context (why approval is needed)

### Overdue Approval Reminders
Scheduled Job checks for overdue approvals:
```javascript
// Check approvals past due date and send reminders
var gr = new GlideRecord('sysapproval_approver');
gr.addQuery('state', 'requested');
gr.addQuery('due_date', '<', gs.nowDateTime());
gr.addQuery('due_date', 'ISNOTEMPTY');
gr.query();
while (gr.next()) {
    gs.eventQueue('approval.overdue',
        gr.sysapproval.getRefRecord(),
        gr.approver.getDisplayValue(),
        gr.due_date.getDisplayValue());
}
```

---

## Approval Reporting

### Key Metrics

| Metric | Query |
|--------|-------|
| Pending approvals | `sysapproval_approver` where state = requested |
| Average approval cycle time | Avg time from state=requested to state=approved |
| Rejection rate | Count rejected / total completed approvals |
| Overdue approvals | State=requested AND due_date < now |
| Approvals by approver | Group by approver field |

### Approval Audit Trail
Every approval action (approve/reject) is logged in:
- `sysapproval_approver` record updates (sys_updated_on, sys_updated_by)
- `sys_audit` table (audit log for all field changes)
- Work notes on the parent record (if configured)

---

## Best Practices

### Approval Design
- Keep approval chains short — each additional level adds delays
- Use parallel approvals where approvers are independent (reduce cycle time)
- Define clear escalation paths for non-responsive approvers
- Document the business reason for each approval requirement

### Approver Availability
- Always configure delegation for key approvers
- For CAB: ensure the group has enough active members to avoid blocking changes
- Consider "first in group to approve" rather than "all must approve" for efficiency

### Rejection Handling
- Always require a rejection reason (mandatory comments field)
- Notify the requestor with the rejection reason and how to resubmit
- Track rejection reasons for process improvement (high rejection rates indicate unclear requirements or miscalibrated policies)

### SLA on Approvals
- Set due dates on approval requests to create urgency
- Configure reminders at 50% and 75% of the due date
- Escalate to approver's manager if approval is not received by due date

---

## Common Patterns

### Self-Approval Prevention
Prevent the requestor from approving their own request:
```javascript
// In the approval generation script or Flow:
if (requestedFor.sys_id == approverSysId) {
    // Route to skip-level manager instead
    approverSysId = requestedFor.manager.manager.sys_id.toString();
}
```

### Conditional Multi-Level Based on Amount
```javascript
// Flow logic: determine approval levels based on cost
var price = parseFloat(ritm.price);
if (price > 10000) {
    // Level 1: Manager
    // Level 2: Director
    // Level 3: VP Finance
} else if (price > 1000) {
    // Level 1: Manager
    // Level 2: Director
} else {
    // Level 1: Manager only
}
```

### Auto-Approve Low-Risk Standard Changes
```javascript
// Business Rule or Flow: Auto-approve standard changes with risk = low
if (current.type == 'standard' && current.risk == '3') {
    var approval = new GlideRecord('sysapproval_approver');
    approval.addQuery('sysapproval', current.sys_id);
    approval.addQuery('state', 'requested');
    approval.query();
    while (approval.next()) {
        approval.state = 'approved';
        approval.comments = 'Auto-approved: Standard low-risk change';
        approval.setWorkflow(false);
        approval.update();
    }
}
```
