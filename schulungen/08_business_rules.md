---
source_type: platform
topics:
  - business rules
  - server-side scripting
  - GlideRecord
  - current
  - previous
  - g_scratchpad
  - execution order
  - before rules
  - after rules
  - async rules
---

# Business Rules

## Overview

Business Rules are server-side scripts that execute automatically when database records are displayed, inserted, updated, deleted, or queried. They run on the server regardless of how the data is accessed — through the UI, REST API, import sets, or other integration methods. This makes them a universal data processing mechanism.

Business Rules are one of the core automation tools in ServiceNow, alongside Flow Designer, Client Scripts, and UI Policies. Choosing the right tool for each scenario is critical for performance and maintainability.

---

## When to Use Business Rules vs. Other Tools

| Scenario | Best Tool | Reason |
|----------|-----------|--------|
| Make field mandatory/visible/read-only | UI Policy | No code; better performance; handles reverse logic |
| Client-side form validation | Client Script (onSubmit) | Runs in browser; immediate feedback |
| Complex cross-field logic on form | Client Script (onChange) | Real-time without save |
| Validate/modify data before database write | Before Business Rule | Server authority; runs for all access methods |
| Auto-populate related records after save | After Business Rule | Record has been saved; safe to reference sys_id |
| Send email/call external API after save | Async Business Rule | Non-blocking; doesn't delay user |
| Pass server data to client on form load | Display Business Rule + g_scratchpad | Server-to-client bridge |
| Multi-step automation with approvals | Flow Designer | Visual; no-code; more maintainable |
| Reusable business logic across multiple BRs | Script Include | DRY principle; testable in isolation |

**Key guidance from ServiceNow:** Use Flow Designer unless specific execution sequencing with other Business Rules is required, or logic must run immediately before/after database writes in the same transaction thread.

---

## Business Rule Types

### 1. Before Business Rules

Executes **after form submission** but **before the database write**. Changes made to `current` are automatically saved — no explicit `current.update()` needed.

**Use for:**
- Data validation (abort save if invalid data)
- Field population/normalization before save
- Calculating values based on other field inputs
- Enforcing business rules before data is committed

**Key characteristic:** Changes to `current` are part of the same transaction — they are saved along with the original changes.

```javascript
(function executeRule(current, previous) {
    // Validate that short_description is not a single word
    if (current.short_description.toString().split(' ').length < 3) {
        current.setAbortAction(true);
        gs.addErrorMessage('Short description must be at least 3 words');
    }

    // Auto-populate category based on CI
    if (current.cmdb_ci.changes() && !current.category.changes()) {
        current.category = current.cmdb_ci.getRefRecord().getDisplayValue('category');
    }
})(current, previous);
```

**WARNING:** Never call `current.update()` inside a Before Business Rule — it causes infinite recursion (the update triggers the Business Rule again, which calls update again, etc.).

### 2. After Business Rules

Executes **after the database commit**. The record has been written to the database. Runs synchronously — the user waits for After BRs to complete before the page loads.

**Use for:**
- Updating related records that need the primary record's `sys_id`
- Triggering events (`gs.eventQueue()`)
- Audit logging to related tables
- Updating parent records based on child record changes

**Key characteristic:** The database write has already occurred. Calling `current.update()` creates a second update transaction, which should be done with caution.

```javascript
(function executeRule(current, previous) {
    // Fire an event when incident is resolved
    if (current.state == 6 && previous.state != 6) {
        gs.eventQueue('incident.resolved', current, current.assignment_group, current.resolved_by);
    }

    // Update related task records when parent changes
    if (current.state == 7) { // Closed
        var relatedTask = new GlideRecord('sc_task');
        relatedTask.addQuery('parent', current.sys_id);
        relatedTask.addQuery('state', '!=', 3); // Not Closed
        relatedTask.query();
        while (relatedTask.next()) {
            relatedTask.state = 3; // Closed Complete
            relatedTask.setWorkflow(false); // Prevent recursion
            relatedTask.update();
        }
    }
})(current, previous);
```

**CAUTION:** Use `setWorkflow(false)` when updating records in After BRs to prevent triggering workflows/flows on the related records unless explicitly intended.

### 3. Async Business Rules

Executes **asynchronously via the system scheduler** — the user's action completes immediately and the async BR runs in the background. Non-blocking.

**Use for:**
- Email notifications (use Events instead when possible)
- External API calls (webhooks, REST calls to third parties)
- SLA recalculations
- Heavy data processing that doesn't need to delay the user
- Generating reports or documents

**Key characteristic:** `previous` object is null in async BRs — only `current` is available. Async BRs appear as "ASYNC: [BR Name]" entries in the System Scheduler.

```javascript
(function executeRule(current, previous /*null for async*/) {
    // Call external webhook with incident details
    var rm = new sn_ws.RESTMessageV2('Webhook Notification', 'post');
    rm.setStringParameterNoEscape('sys_id', current.sys_id.toString());
    rm.setStringParameterNoEscape('number', current.number.toString());
    rm.setStringParameterNoEscape('priority', current.priority.toString());
    var response = rm.execute();

    gs.info('Webhook called for ' + current.number + ': HTTP ' + response.getStatusCode());
})(current, previous);
```

### 4. Display Business Rules

Executes **when a form is loaded** in the browser, before the form is rendered to the user. Read-only access to database data — cannot modify records. Primary purpose: populate `g_scratchpad` for use by Client Scripts.

**Use for:**
- Querying related data to pass to Client Scripts
- Computing values that are expensive to calculate client-side
- Pre-loading lookup values for client-side use

**Key limitation:** Only runs on form load — NOT on list views, REST API calls, or insert/update operations.

```javascript
(function executeRule(current, previous) {
    // Pass manager information to client
    var user = new GlideRecord('sys_user');
    if (user.get(current.caller_id)) {
        g_scratchpad.caller_manager_name = user.manager.getDisplayValue();
        g_scratchpad.caller_manager_id = user.manager.toString();
        g_scratchpad.caller_vip = user.vip.toString();
    }

    // Pass count of open incidents for this CI
    var ga = new GlideAggregate('incident');
    ga.addQuery('cmdb_ci', current.cmdb_ci);
    ga.addQuery('state', 'IN', '1,2,3'); // New, In Progress, On Hold
    ga.addAggregate('COUNT');
    ga.query();
    g_scratchpad.ci_open_incident_count = ga.next() ? ga.getAggregate('COUNT') : 0;
})(current, previous);
```

### 5. Before Query Business Rules

Executes **before every database query** on the specified table. Used to automatically filter query results.

**Use for:**
- Row-level security (hiding records without showing a restriction message)
- Automatic data scoping (tenants only see their own data)
- Injecting additional conditions into every query

**WARNING:** Significant performance impact. Runs on every list view, report, and API call for the table. Use sparingly and with precise conditions.

```javascript
(function executeRule(current, previous) {
    // Only show incidents created in the last 90 days to non-admins
    if (!gs.hasRole('itil_admin')) {
        var cutoff = new GlideDateTime();
        cutoff.addDaysLocalTime(-90);
        current.addQuery('sys_created_on', '>', cutoff);
    }
})(current, previous);
```

---

## Execution Order

The complete sequence when a record is saved:

| Step | What Executes |
|------|--------------|
| 1 | onSubmit Client Scripts (browser validation) |
| 2 | Before Business Rules with Order < 1000 |
| 3 | ServiceNow Engines (Workflows, Assignment Rules, Data Lookup — Order = 1000) |
| 4 | Before Business Rules with Order ≥ 1000 |
| 5 | Database Operation (INSERT / UPDATE / DELETE) |
| 6 | After Business Rules (synchronous — user waits) |
| 7 | Async Business Rules (background scheduler — non-blocking) |

Within the same type and order range: **lower Order number executes first**.

### Execution Order Best Practices
- Order 100: Validation BRs (abort saves early)
- Order 200-500: Data normalization and field population
- Order 900: Final pre-save calculations
- Order 1001+: Post-engine processing
- Keep critical BRs at low order numbers to execute before other BRs might depend on their output

---

## Key Script Objects

### `current`
The GlideRecord of the record being processed. Contains the **new values** (after the user's changes).

```javascript
current.short_description  // New value
current.state              // New state value
current.getValue('state')  // Returns raw value (integer as string)
current.getDisplayValue('state')  // Returns display label ("In Progress")
current.changes()          // Returns true if any field has changed
current.short_description.changes()  // Returns true if this specific field changed
current.setAbortAction(true)  // Abort the save operation
```

### `previous`
The GlideRecord with **original values before modification**. Only available in Before and After BRs (not available in Async BRs — will be null).

```javascript
previous.state             // Value before the user's change
previous.getValue('state') // Returns raw previous value

// Common pattern: detect state change
if (current.state == 2 && previous.state == 1) {
    // Incident moved from New to In Progress
}
```

### `g_scratchpad`
An object for passing data from a Display Business Rule (server-side) to a Client Script (browser-side). Data set in Display BR is available in onLoad Client Scripts as `g_scratchpad.property_name`.

```javascript
// Display BR (server-side):
g_scratchpad.user_vip = current.caller_id.vip.toString();
g_scratchpad.escalation_group = 'Service Desk Escalation';

// onLoad Client Script (browser-side):
if (g_scratchpad.user_vip === 'true') {
    g_form.showFieldMsg('caller_id', 'VIP Customer - Handle with priority', 'info');
}
```

---

## Script Structure and Context

### Standard Business Rule Script Template

```javascript
(function executeRule(current, previous) {

    // Check if this is an insert operation (new record)
    if (current.operation() == 'insert') {
        // Logic for new records
    }

    // Check if this is an update
    if (current.operation() == 'update') {
        // Logic for updates

        // Check if a specific field changed
        if (current.priority.changes()) {
            // Handle priority change
        }
    }

    // Check if this is a delete
    if (current.operation() == 'delete') {
        // Logic for deletions
    }

})(current, previous);
```

### Available Operations
- `current.operation()`: Returns `'insert'`, `'update'`, or `'delete'`
- When condition field (outside script): Select Insert, Update, Delete independently

---

## When Conditions

Business Rules have a visual condition builder and an "Advanced" checkbox for scripted conditions:

### Simple Condition (no script)
Use the condition builder:
- When: Insert / Update / Delete / Display
- Table: incident
- Condition: Priority = 1 (Critical)

### Advanced Condition (script)
When the condition checkbox is ticked:
```javascript
// Only run when state changes TO Resolved
current.state == 6 && current.state.changes()
```

The "When" script (condition) executes before the "Script" body. If the condition returns false, the script body is skipped — better performance than checking conditions inside the script body.

---

## Performance and Pitfalls

### Common Anti-Patterns

| Anti-Pattern | Problem | Solution |
|-------------|---------|---------|
| `current.update()` in Before BR | Infinite recursion | Never call update() in Before BRs; changes save automatically |
| GlideRecord query in Before BR with no abort | Deadlock potential on busy tables | Use GlideAggregate for counts; limit queries |
| `gs.log()` in scoped app | Compilation error | Use `gs.info()`, `gs.debug()`, `gs.warn()`, `gs.error()` |
| No condition specified | BR runs on every record save | Always specify table + conditions |
| Synchronous REST calls in After BR | Blocks user session | Move REST calls to Async BR |
| `setWorkflow(false)` forgotten on related updates | Recursive workflow/flow triggers | Always use `setWorkflow(false)` when updating records in BRs |

### Performance Guidelines
- Monitor BR execution time via System Diagnostics → Session Debug
- Business Rules taking > 100ms should be investigated and optimized
- Prefer `GlideAggregate` over loading all records just to count them
- Use `setLimit()` on GlideRecord queries when only a few records are needed
- Specify table conditions as precisely as possible — overly broad conditions cause BRs to fire unnecessarily

---

## Debugging

### Session Debug
Navigate to System Diagnostics → Session Debug → Debug Business Rule:
- Activates verbose logging in the browser
- Shows each BR that fires, its name, table, when/order, and execution time
- Shows whether condition evaluated to true/false

### Script Tracer
System Diagnostics → Script Debugger:
- Step-through debugging for synchronous BRs
- Set breakpoints, inspect variable values
- Not available for Async BRs (run in background)

### Logging
```javascript
gs.info('Incident {0} processed — old state: {1}, new state: {2}',
    current.number, previous.state, current.state);
// Output visible in: System Logs > System Log > Application Log
// Also queryable in sys_log table
```

Log levels: `gs.debug()` < `gs.info()` < `gs.warn()` < `gs.error()`

---

## Best Practices

### Keep Business Rules "Thin"
Extract reusable logic into Script Includes:
```javascript
// Instead of putting 50 lines of logic in a BR:
(function executeRule(current, previous) {
    var util = new IncidentUtils();
    util.handlePriorityChange(current, previous);
})(current, previous);
```

### Use Meaningful Names
Name convention: `[Table] - [When] - [Action]`
- "Incident - Before - Validate Priority"
- "Change - After - Create Default Tasks"
- "Problem - Async - Notify Problem Manager"

### Document Complex Logic
Add comments explaining WHY, not just WHAT:
```javascript
// JIRA-1234: When priority escalates from P3/P4 to P1/P2,
// reassign to Major Incident group and notify MIM.
// Do NOT trigger for initial ticket creation.
if (current.operation() == 'update' && current.priority.changes()) {
    ...
}
```

### Test All Paths
Test: insert, update (changed field), update (unchanged field), delete, Display (form load)

---

## Common Patterns

### Auto-Populate Assignment Group from CI
```javascript
// Before BR on incident — When: Insert or Update, Condition: cmdb_ci changes
(function executeRule(current, previous) {
    if (current.cmdb_ci.changes() && current.cmdb_ci != '') {
        var ci = current.cmdb_ci.getRefRecord();
        if (!current.assignment_group.changes()) {
            // Only set if not manually changed in same save
            current.assignment_group = ci.getValue('support_group');
        }
    }
})(current, previous);
```

### Fire Event on State Change
```javascript
// After BR on incident — When: Update, Condition: state changes and state = 6
(function executeRule(current, previous) {
    gs.eventQueue('incident.resolved', current,
        current.assignment_group.toString(),
        current.resolved_by.toString());
})(current, previous);
```

### Pass Server Data to Client
```javascript
// Display BR on incident — When: Display
(function executeRule(current, previous) {
    g_scratchpad.sla_percentage = 0;
    var taskSLA = new GlideRecord('task_sla');
    taskSLA.addQuery('task', current.sys_id);
    taskSLA.addQuery('sla.target', 'resolution');
    taskSLA.addQuery('stage', 'in_progress');
    taskSLA.setLimit(1);
    taskSLA.query();
    if (taskSLA.next()) {
        g_scratchpad.sla_percentage = taskSLA.business_percentage.toString();
    }
})(current, previous);
```
