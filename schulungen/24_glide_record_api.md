---
source_type: platform
topics:
  - GlideRecord
  - GlideSystem
  - GlideDateTime
  - GlideAggregate
  - server-side scripting
  - database API
  - JavaScript API
---

# GlideRecord API

## Overview

GlideRecord is the primary server-side JavaScript API for querying, creating, updating, and deleting records in ServiceNow database tables. Every server-side script (Business Rules, Script Includes, Scheduled Jobs, Flow Designer script steps) uses GlideRecord to interact with data.

Understanding GlideRecord deeply is the most important single skill for ServiceNow development. This document covers GlideRecord, the GlideSystem (gs) global object, GlideDateTime, and GlideAggregate.

---

## GlideRecord Basics

### Instantiation
```javascript
var gr = new GlideRecord('incident');  // Create a GlideRecord for the incident table
```

### CRUD Operations

#### Query (Read)
```javascript
var gr = new GlideRecord('incident');
gr.addQuery('state', '2');           // state = In Progress
gr.addQuery('priority', '1');        // AND priority = 1 (Critical)
gr.orderByDesc('sys_created_on');    // ORDER BY created date descending
gr.query();                          // Execute the query

while (gr.next()) {                  // Iterate through results
    gs.info(gr.number + ': ' + gr.short_description);
}
```

#### Get by sys_id
```javascript
var gr = new GlideRecord('incident');
if (gr.get('abc123def456...')) {     // Get single record by sys_id
    gs.info('Found: ' + gr.number);
}
```

#### Get by Field Value
```javascript
var gr = new GlideRecord('incident');
if (gr.get('number', 'INC0001234')) { // Get by specific field value
    gs.info('State: ' + gr.getDisplayValue('state'));
}
```

#### Create (Insert)
```javascript
var gr = new GlideRecord('incident');
gr.initialize();                     // Initialize a new record (clears defaults)
gr.short_description = 'VPN outage affecting all remote users';
gr.caller_id.setDisplayValue('john.smith');
gr.category = 'network';
gr.impact = '1';
gr.urgency = '1';
var newSysId = gr.insert();          // Insert and return sys_id
gs.info('Created: ' + newSysId);
```

#### Update
```javascript
var gr = new GlideRecord('incident');
gr.get('abc123...');
gr.state = '6';                      // Resolved
gr.close_code = 'Solved (Permanently)';
gr.close_notes = 'VPN service restored by restarting the gateway service.';
gr.update();
```

#### Delete
```javascript
var gr = new GlideRecord('incident');
gr.get('abc123...');
gr.deleteRecord();
```

#### Delete Multiple Records
```javascript
var gr = new GlideRecord('sys_temp_data');
gr.addQuery('sys_created_on', '<', gs.daysAgo(30));  // Older than 30 days
gr.deleteMultiple();                 // Delete all matching records
```

---

## Query Methods

### addQuery
```javascript
gr.addQuery('field', 'value');           // field = value
gr.addQuery('field', '!=', 'value');     // field != value
gr.addQuery('field', '>', 5);            // field > 5
gr.addQuery('field', 'CONTAINS', 'text'); // field CONTAINS 'text'
gr.addQuery('field', 'STARTSWITH', 'INC'); // field STARTS WITH
gr.addQuery('field', 'IN', '1,2,3');     // field IN (list)
gr.addQuery('field', 'NOT IN', '6,7');   // field NOT IN (list)
gr.addQuery('field', 'ISEMPTY');         // field IS NULL or empty
gr.addQuery('field', 'ISNOTEMPTY');      // field has value
```

### addOrCondition
Build OR conditions:
```javascript
var qc = gr.addQuery('state', '1');      // state = 1
qc.addOrCondition('state', '2');         // OR state = 2
qc.addOrCondition('state', '3');         // OR state = 3
// Result: state IN (1, 2, 3)
```

### addEncodedQuery
Use ServiceNow encoded query strings:
```javascript
gr.addEncodedQuery('state=2^priority=1^assignment_groupSTARTSWITHNetwork');
```

Encoded queries can be copied from list view filter breadcrumbs.

### Dot-Walking in Queries
```javascript
gr.addQuery('caller_id.department.name', 'Information Technology');
gr.addQuery('assigned_to.manager.active', 'true');
```

### Query Limits and Ordering
```javascript
gr.setLimit(100);              // Maximum 100 records
gr.setLimit(1);                // First match only
gr.orderBy('priority');        // ASC order
gr.orderByDesc('sys_created_on'); // DESC order
gr.chooseWindow(0, 100);       // Pagination: first 100 records
gr.chooseWindow(100, 200);     // Next 100
```

---

## Reading Field Values

### Getting Values
```javascript
gr.field_name                  // Returns GlideElement object
gr.field_name.toString()       // Raw stored value (e.g., '2' for state)
gr.getValue('field_name')      // Same as toString() — raw value
gr.getDisplayValue('field_name') // Human-readable label (e.g., 'In Progress')
gr.field_name.getDisplayValue() // Same on GlideElement

// Reference fields
gr.assigned_to                 // GlideElement (sys_id of referenced user)
gr.assigned_to.toString()      // sys_id string
gr.assigned_to.getDisplayValue() // User's display name
gr.assigned_to.name            // Access referenced record's field (auto dot-walk)

// Check if reference field is populated
gr.assigned_to.nil()           // Returns true if empty
!gr.assigned_to.nil()          // Returns true if populated
```

### Checking Changes (in Business Rules)
```javascript
current.state.changes()        // Returns true if this field changed
current.changes()              // Returns true if ANY field changed
current.state.changesFrom('1') // Changed FROM value 1
current.state.changesTo('6')   // Changed TO value 6
```

---

## Setting Field Values

```javascript
gr.field_name = 'value';               // Direct assignment (raw value)
gr.setValue('field_name', 'value');    // Equivalent

// Reference fields by sys_id
gr.assignment_group = 'sys_id_of_group';

// Reference fields by display value
gr.assignment_group.setDisplayValue('Network Operations');
gr.caller_id.setDisplayValue('john.smith'); // Sets by username

// Setting Journal fields (work notes / comments)
gr.work_notes = 'Investigation started — checking server logs';
gr.comments = 'We are investigating your issue and will update you shortly.';
```

---

## GlideRecord Methods Reference

### Query and Navigation

| Method | Description |
|--------|-------------|
| `query()` | Execute the query |
| `get(sys_id)` | Get single record by sys_id |
| `get(field, value)` | Get single record by field value |
| `next()` | Advance to next record; returns false when done |
| `hasNext()` | Check if more records exist without advancing |
| `getRowCount()` | Number of rows returned (call after query) |

### Record Operations

| Method | Description |
|--------|-------------|
| `insert()` | Insert new record; returns sys_id |
| `update()` | Update current record |
| `deleteRecord()` | Delete current record |
| `deleteMultiple()` | Delete all records matching query |
| `initialize()` | Reset to new blank record |
| `newRecord()` | Initialize for insert (alternate to initialize) |

### Field Operations

| Method | Description |
|--------|-------------|
| `getValue(field)` | Get raw value |
| `getDisplayValue(field)` | Get display value |
| `setValue(field, value)` | Set raw value |
| `setAbortAction(true)` | Abort the current database operation (Before BR) |
| `setWorkflow(false)` | Prevent workflows/flows from triggering on update |
| `setForceUpdate(true)` | Force update even if no fields changed |
| `autoSysFields(false)` | Don't update sys_updated_on/by (use with caution) |

### Metadata

| Method | Description |
|--------|-------------|
| `operation()` | Returns 'insert', 'update', or 'delete' |
| `getTableName()` | Returns table name string |
| `getClassDisplayValue()` | Returns class display name |
| `isNewRecord()` | True if record hasn't been saved yet |
| `isValid()` | True if record was found |
| `sys_id` | sys_id of current record |

---

## GlideAggregate

GlideAggregate performs aggregation queries efficiently — use it instead of loading all records just to count them.

```javascript
var ga = new GlideAggregate('incident');
ga.addQuery('state', 'IN', '1,2,3');    // Filter: active states
ga.addAggregate('COUNT');               // Count all matching records
ga.query();
if (ga.next()) {
    var count = parseInt(ga.getAggregate('COUNT'));
    gs.info('Open incidents: ' + count);
}
```

### Grouping with Aggregates
```javascript
var ga = new GlideAggregate('incident');
ga.addQuery('state', 'IN', '1,2,3');
ga.addAggregate('COUNT');
ga.groupBy('priority');                 // Count per priority
ga.orderBy('priority');
ga.query();
while (ga.next()) {
    gs.info('Priority ' + ga.getDisplayValue('priority') +
            ': ' + ga.getAggregate('COUNT') + ' open incidents');
}
```

### Multiple Aggregation Functions
```javascript
var ga = new GlideAggregate('sc_req_item');
ga.addQuery('state', '3'); // Closed
ga.addAggregate('COUNT');
ga.addAggregate('SUM', 'price');
ga.addAggregate('AVG', 'price');
ga.query();
if (ga.next()) {
    gs.info('Total requests: ' + ga.getAggregate('COUNT'));
    gs.info('Total revenue: $' + ga.getAggregate('SUM', 'price'));
    gs.info('Average price: $' + ga.getAggregate('AVG', 'price'));
}
```

### Available Aggregate Functions

| Function | Description |
|----------|-------------|
| `COUNT` | Count of records |
| `SUM` | Sum of field values |
| `AVG` | Average of field values |
| `MIN` | Minimum field value |
| `MAX` | Maximum field value |
| `COUNT DISTINCT` | Count unique values |

---

## GlideSystem (gs)

The `gs` object provides global system utilities available in all server-side scripts.

### Logging
```javascript
gs.debug('Debug message: {0}', variable);   // DEBUG level
gs.info('Info message: {0}', variable);     // INFO level
gs.warn('Warning: {0}', variable);          // WARN level
gs.error('Error occurred: {0}', message);   // ERROR level
gs.print('Output: ' + value);               // Background Scripts only
```

Log output goes to `sys_log` table. View at: System Logs → System Log → Application Log.

### User and Session
```javascript
gs.getUserID()              // sys_id of current user
gs.getUserName()            // Login username
gs.getUserDisplayName()     // Full display name
gs.hasRole('itil')         // Check role membership
gs.isInteractive()          // True if user is in a browser session (not API/background)
gs.getSession()             // GlideSession object for current session
```

### Date and Time
```javascript
gs.now()                    // Current datetime as GlideDateTime string
gs.nowDateTime()            // Current datetime string
gs.daysAgo(5)              // DateTime 5 days in the past
gs.daysAgo(-5)             // DateTime 5 days in the future (negative)
gs.hoursAgo(2)             // DateTime 2 hours ago
gs.minutesAgo(30)          // DateTime 30 minutes ago
gs.beginningOfToday()      // 00:00:00 today
gs.endOfToday()            // 23:59:59 today
gs.beginningOfLastWeek()   // Start of last week
```

### System Properties
```javascript
gs.getProperty('property.name')                    // Get property value
gs.getProperty('property.name', 'default')         // Get with default
gs.setProperty('property.name', 'value')           // Set property value
```

### Events
```javascript
gs.eventQueue('event.name', glideRecord, parm1, parm2)  // Fire event
gs.eventQueueScheduled('event.name', gr, p1, p2, future_time) // Scheduled event
```

### Utility
```javascript
gs.nil(value)               // Returns true if null/undefined/empty
gs.notNil(value)            // Opposite of nil
gs.generateGUID()           // Generate random GUID/sys_id
gs.addErrorMessage('msg')   // Add error to current session
gs.addInfoMessage('msg')    // Add info message to session
gs.include('ScriptInclude') // Include a Script Include (legacy pattern; use new SI() instead)
```

---

## GlideDateTime

GlideDateTime handles date and time operations with timezone awareness.

### Creating GlideDateTime Objects
```javascript
var now = new GlideDateTime();                        // Current UTC time
var specific = new GlideDateTime('2024-01-15 10:00:00'); // Specific datetime
var fromField = new GlideDateTime(gr.sys_created_on);  // From GlideElement
```

### Reading Values
```javascript
gdt.getDisplayValue()       // Formatted string in user's timezone
gdt.getValue()              // UTC value as string: 'YYYY-MM-DD HH:MM:SS'
gdt.getDate()               // Date portion only
gdt.getTime()               // Time portion only
gdt.getYear()               // Year integer
gdt.getMonth()              // Month (1-12)
gdt.getDayOfMonthLocalTime() // Day of month (1-31)
gdt.getDayOfWeekLocalTime()  // Day of week (1=Sunday, 7=Saturday)
gdt.getNumericValue()       // Milliseconds since epoch
```

### Arithmetic
```javascript
gdt.addDays(7)              // Add 7 days (modifies object)
gdt.addDaysLocalTime(-3)    // Subtract 3 days (in local time)
gdt.addMonths(1)            // Add 1 month
gdt.addYears(-1)            // Subtract 1 year
gdt.addSeconds(3600)        // Add 3600 seconds (1 hour)

// Comparison
gdt1.compareTo(gdt2)        // -1 (before), 0 (equal), 1 (after)
gdt1.before(gdt2)           // boolean: gdt1 is before gdt2
gdt1.after(gdt2)            // boolean: gdt1 is after gdt2
gdt1.equals(gdt2)           // boolean: same datetime
```

### Duration between Dates
```javascript
var start = new GlideDateTime('2024-01-01 09:00:00');
var end = new GlideDateTime('2024-01-01 17:00:00');
var diff = GlideDateTime.subtract(start, end);  // Returns GlideDuration
gs.info('Duration: ' + diff.getDisplayValue()); // "0 00:08:00:00" (8 hours)
```

### GlideDuration
```javascript
var dur = new GlideDuration();
dur.setDayPart(1);                // 1 day
dur.setDisplayValue('2 00:04:00:00'); // 2 days, 4 hours
dur.getDayPart()                  // Integer days
dur.getDisplayValue()             // Human-readable string
dur.getValue()                    // Raw value string
```

---

## Performance Best Practices

### Always Use setLimit()
```javascript
// Bad: loads all matching records into memory
var gr = new GlideRecord('incident');
gr.addQuery('state', '2');
gr.query();
var count = 0;
while (gr.next()) { count++; } // counting all records — slow!

// Good: use GlideAggregate for counts
var ga = new GlideAggregate('incident');
ga.addQuery('state', '2');
ga.addAggregate('COUNT');
ga.query();
ga.next();
var count = parseInt(ga.getAggregate('COUNT')); // Fast!
```

### Use Field Lists
```javascript
// Bad: retrieves ALL fields (all columns joined from task + incident)
var gr = new GlideRecord('incident');
gr.query();

// Good: specify only fields needed
var gr = new GlideRecord('incident');
// ServiceNow doesn't have direct field list restriction for GlideRecord
// But for REST API calls, use sysparm_fields
// For GlideRecord, be deliberate about not traversing reference fields unnecessarily
```

### Avoid N+1 Queries
```javascript
// Bad: one extra query per record in the outer loop
while (outerGR.next()) {
    var innerGR = new GlideRecord('related_table');
    innerGR.addQuery('parent', outerGR.sys_id);
    innerGR.query(); // N+1 queries!
    while (innerGR.next()) { ... }
}

// Better: pre-load related data, or use encoded query to get all needed records upfront
```

### setWorkflow(false) for Batch Updates
```javascript
var gr = new GlideRecord('incident');
gr.addQuery('state', '5');  // Some target state
gr.query();
while (gr.next()) {
    gr.state = '6';
    gr.setWorkflow(false);   // Prevent BRs/workflows firing during batch
    gr.update();
}
```

---

## Common Patterns

### Safe Get or Create
```javascript
function getOrCreateGroup(groupName) {
    var gr = new GlideRecord('sys_user_group');
    gr.addQuery('name', groupName);
    gr.setLimit(1);
    gr.query();
    if (gr.next()) {
        return gr.sys_id.toString();
    }
    // Create if not found
    var newGr = new GlideRecord('sys_user_group');
    newGr.initialize();
    newGr.name = groupName;
    newGr.active = true;
    return newGr.insert();
}
```

### Batch State Transition
```javascript
// Close all resolved incidents older than 30 days
var gr = new GlideRecord('incident');
gr.addQuery('state', '6'); // Resolved
gr.addQuery('resolved_at', '<', gs.daysAgo(30));
gr.query();
while (gr.next()) {
    gr.state = '7'; // Closed
    gr.setWorkflow(false);
    gr.update();
}
```

### Check Record Exists Without Loading It
```javascript
var ga = new GlideAggregate('sys_user_group');
ga.addQuery('name', 'Network Operations');
ga.addAggregate('COUNT');
ga.query();
var exists = ga.next() && parseInt(ga.getAggregate('COUNT')) > 0;
```
