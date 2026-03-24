---
source_type: platform
topics:
  - events
  - event queue
  - script actions
  - gs.eventQueue
  - sysevent
  - event registry
  - notifications
  - asynchronous processing
---

# Events System

## Overview

The ServiceNow Events System is an asynchronous messaging mechanism that decouples the detection of a business occurrence from the processing of its consequences. A Business Rule fires an event ("something happened"), and Script Actions and Notifications respond to that event in the background.

Events enable loose coupling: the code that detects a condition doesn't need to know what should happen as a result. This makes the system more modular, testable, and maintainable.

---

## Core Components

### Events (sysevent table)
An event record is a message published to the system indicating that something occurred. It sits in a queue until processed by an event processor.

**Key event record fields:**

| Field | Description |
|-------|-------------|
| `name` | Event identifier (e.g., `incident.resolved`) |
| `instance` | sys_id of the record that triggered the event |
| `table` | Table name of the triggering record |
| `parm1` | Optional first parameter (string) |
| `parm2` | Optional second parameter (string) |
| `state` | Ready, Processing, Processed, Error, Transferred |
| `queue` | Which processor queue to use |
| `claimed_by` | Node that picked up the event for processing |
| `fired_by` | User or system that fired the event |

### Event Registry (sysevent_register table)
Events must be registered before they can be used. The registry:
- Makes events selectable in the Notification "When" picker and Script Action selector
- Documents what events exist in the system
- Controls which events trigger Email, SMS, or other notification channels

### Script Actions (sysevent_action)
Server-side scripts that execute when specific events fire:
- One script action per event name (or multiple actions per event)
- Run asynchronously in the background
- Have access to `current` (the triggering record) and `event` (the event record)

### Notifications
Email and other notifications can be configured to trigger on specific events — the notification fires when the event fires.

---

## How Events Work

### Flow of an Event

```
1. Business Rule fires gs.eventQueue('incident.resolved', current, parm1, parm2)
   ↓
2. New record inserted into sysevent table (state: Ready)
   ↓
3. Event Processor (background thread) picks up the event
   ↓
4. Script Actions for 'incident.resolved' execute
   ↓
5. Notifications configured for 'incident.resolved' are sent
   ↓
6. sysevent record state updated to 'Processed'
```

### gs.eventQueue Syntax

```javascript
gs.eventQueue(
    eventName,  // String: registered event name
    glideRecord, // GlideRecord: the record context (provides table + instance)
    parm1,      // String: optional first parameter
    parm2,      // String: optional second parameter
    queue       // String: optional queue name (default: 'event')
);
```

**Examples:**

```javascript
// Simple event with no parameters
gs.eventQueue('incident.resolved', current, '', '');

// Event with meaningful parameters
gs.eventQueue('incident.major_incident_started',
    current,
    current.assignment_group.toString(),  // parm1: group sys_id
    current.priority.toString()           // parm2: priority value
);

// Event using display values in parameters
gs.eventQueue('change.approved',
    current,
    current.assignment_group.getDisplayValue(), // parm1: group name
    gs.getUserDisplayName()                      // parm2: approver name
);
```

---

## Creating Custom Events

### Step 1: Register the Event

Navigate to System Policy → Events → Registry → New

| Field | Value |
|-------|-------|
| Name | `my_app.incident_escalated` (use dot notation: `scope.description`) |
| Table | `incident` (or leave blank for generic events) |
| Description | When and why this event fires |

### Step 2: Create the Trigger (Business Rule)

```javascript
// After Business Rule on 'incident' — fires when priority changes to 1
(function executeRule(current, previous) {
    if (current.priority == '1' && current.priority.changes()) {
        gs.eventQueue(
            'myapp.incident_escalated_p1',
            current,
            current.assignment_group.toString(),
            current.caller_id.toString()
        );
    }
})(current, previous);
```

### Step 3: Create the Handler (Script Action)

Navigate to System Policy → Events → Script Actions → New

```javascript
// Script Action for 'myapp.incident_escalated_p1'
// Available objects: event, current

var assignmentGroup = event.parm1;  // Group sys_id from the event
var callerSysId = event.parm2;      // Caller sys_id from the event

// Create a bridge conference
var bridge = new sn_ws.RESTMessageV2('ConferenceBridgeAPI', 'createBridge');
bridge.setStringParameterNoEscape('incident_number', current.number.toString());
var response = bridge.execute();
var bridgeData = JSON.parse(response.getBody());

// Update the incident with bridge information
var gr = new GlideRecord('incident');
if (gr.get(current.sys_id)) {
    gr.work_notes = 'P1 Bridge created: ' + bridgeData.url;
    gr.setWorkflow(false);
    gr.update();
}
```

### Step 4: Create Notifications (Optional)

Configure an Email Notification:
- When: Event is fired
- Event name: `myapp.incident_escalated_p1`
- Recipients: `${event.parm1}` (group from parm1), specific role, or field reference
- Subject: `[P1 ESCALATION] ${number}: ${short_description}`

---

## Script Action Context

Script Actions have access to these objects:

| Object | Type | Description |
|--------|------|-------------|
| `event` | GlideRecord (`sysevent`) | The event record itself |
| `event.parm1` | String | First event parameter |
| `event.parm2` | String | Second event parameter |
| `event.name` | String | Event name |
| `event.instance` | String | sys_id of triggering record |
| `event.table` | String | Table of triggering record |
| `current` | GlideRecord | The triggering record (looked up from event.instance) |

### Accessing the Triggering Record

```javascript
// current is automatically populated from event.instance + event.table
// If you need to access fields not on current, re-query
var incident = new GlideRecord(event.table);
incident.get(event.instance);
gs.info('Processing event for incident: ' + incident.number);
```

---

## Events vs. Business Rules: Decision Guide

| Use Events When... | Use Business Rules When... |
|-------------------|--------------------------|
| Processing can be deferred | Logic must happen before DB write |
| Multiple handlers may respond | Single deterministic outcome needed |
| External integrations | Same-transaction field modifications |
| Long-running operations | Quick calculations |
| Notifications to users | Validation/abort |
| Cross-record operations | Setting `current` fields |
| Decoupling is desirable | Tight coupling is acceptable |

**Practical guideline:** If an Async Business Rule would work, consider using an Event + Script Action instead. The event approach is more discoverable and extensible (multiple handlers can respond to the same event without modifying existing code).

---

## Event States and Lifecycle

| State | Description |
|-------|-------------|
| Ready | Event is queued and waiting for an available processor |
| Processing | An event processor node has claimed and is executing the event |
| Processed | All handlers completed successfully |
| Error | One or more handlers failed |
| Transferred | Event was moved to a different node for processing |

### Processing Guarantees
- Events are processed **at least once** — in failure scenarios, they may be retried
- Script Actions should be **idempotent** where possible (safe to run multiple times)
- Order of processing within the same queue is generally FIFO but not guaranteed

---

## Event Log and Debugging

### Event Log
Navigate to System Policy → Events → Event Log (or System Policy → Events → System Events)

Displays all fired events with state, timing, and error details.

**Useful queries on sysevent:**
- All Ready/Error events: `state=Ready^ORstate=Error`
- Events for a specific record: `instance=<sys_id>`
- Recent errors: `state=Error^sys_created_on>javascript:gs.hoursAgo(1)`

### Debugging Event Processing

**Check if an event was fired:**
```javascript
// In a test script (Background Script):
var ge = new GlideRecord('sysevent');
ge.addQuery('name', 'incident.resolved');
ge.addQuery('instance', targetIncidentSysId);
ge.orderByDesc('sys_created_on');
ge.setLimit(5);
ge.query();
while (ge.next()) {
    gs.print(ge.name + ' | ' + ge.state + ' | ' + ge.sys_created_on);
}
```

**Force immediate processing (testing):**
System Policy → Events → Event Log → find event → "Process event" UI action

---

## Scheduled Events (gs.eventQueueScheduled)

Events can be scheduled to fire at a future time:

```javascript
// Fire an event 4 hours from now (for SLA follow-up)
gs.eventQueueScheduled(
    'incident.sla_followup_check',
    current,
    current.number.toString(),
    '',
    gs.hoursAgo(-4)  // Negative hours = future
);
```

Scheduled events are stored in `sysevent_schedule` and fired by the event scheduler at the specified time.

**Use cases:**
- Escalation reminders at defined intervals after incident creation
- Pre-change notification firing 24 hours before scheduled change
- Follow-up checks on problem records after a fixed period

---

## Notification Events

Notifications can be triggered directly by events, using event parameters in recipient lists and content:

### Event-Based Notification Configuration

| Setting | Value |
|---------|-------|
| When to Send | Event is fired |
| Event name | `incident.resolved` |
| Recipients | Can use `${event.parm1}` as a user sys_id recipient |
| Subject | `${number}: Your incident has been resolved` |
| Body | Can reference `${event.parm1}` and `${event.parm2}` |

### Using Event Parameters in Notifications
```
// In notification body (HTML):
This incident has been resolved by the ${event.parm1} team.
Resolution notes: ${close_notes}
Resolved by: ${resolved_by.name}
```

---

## Event Queues

Events can be routed to different named queues for priority processing:

| Queue | Purpose |
|-------|---------|
| Default (`event`) | Standard processing queue |
| `slow` | Low-priority, non-urgent processing |
| `immediate` | High-priority events (processed with higher frequency) |

```javascript
// Route to immediate queue for P1 incidents
gs.eventQueue('incident.p1_created', current, parm1, parm2, 'immediate');
```

---

## Best Practices

### Event Naming Conventions
Use the format: `table_name.description`
- `incident.resolved`
- `change_request.approved`
- `problem.known_error_created`
- `myapp.external_sync_failed`

Consistent naming enables easy filtering in the event log and makes the event registry self-documenting.

### Parameter Usage
- Use `parm1` for the primary context value (usually a sys_id or key identifier)
- Use `parm2` for secondary context (state, count, category)
- Document what each parameter contains in the event registry description
- Keep parameters as sys_ids rather than display values where possible (more stable)

### Idempotent Script Actions
Design Script Actions to be safe if executed multiple times:
```javascript
// Bad: Creates duplicate notification every time
sendNotification(current.caller_id);

// Better: Check if notification already sent
var existing = new GlideRecord('sys_notification_log');
existing.addQuery('related_record', current.sys_id);
existing.addQuery('sys_created_on', '>', gs.minutesAgo(5));
existing.setLimit(1);
existing.query();
if (!existing.next()) {
    sendNotification(current.caller_id);
}
```

### Avoiding Event Queue Congestion
- Do not fire events in loops without rate limiting
- Use `gs.eventQueueScheduled()` for batch notifications with staggered timing
- Monitor event queue depth — large backlogs indicate processing capacity issues

---

## Common Patterns

### Decoupled Integration via Events

**Pattern:** BusinessRule → Event → Script Action → External API

Benefits:
- External API failure doesn't fail the user's save operation
- New integrations can be added by creating new Script Actions without modifying existing code
- Integration failures are retryable (re-process the event)

```
1. Incident resolved → Business Rule fires 'incident.resolved'
2. Script Action A: Send to external ticketing system
3. Script Action B: Update ITSM metrics dashboard
4. Notification X: Email caller
5. Notification Y: SMS on-call if was P1
```

All four responses are triggered by the same event. Adding a fifth (e.g., update Jira) requires only adding a new Script Action — no code changes to existing Business Rules.

### Retry Pattern for Transient Failures

```javascript
// Script Action for 'myapp.sync_to_external'
try {
    var result = callExternalAPI(current);
    gs.info('Sync successful for: ' + current.number);
} catch(ex) {
    // Re-queue the event for retry in 5 minutes
    gs.eventQueueScheduled(
        'myapp.sync_to_external_retry',
        current,
        event.parm1,
        event.parm2,
        gs.minutesAgo(-5)  // 5 minutes from now
    );
    gs.warn('Sync failed, queued retry: ' + ex.getMessage());
}
```
