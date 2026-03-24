---
source_type: platform
topics:
  - scheduled jobs
  - scheduled script execution
  - fix scripts
  - background scripts
  - sys_trigger
  - automation
  - batch processing
---

# Scheduled Jobs

## Overview

Scheduled Jobs in ServiceNow allow administrators and developers to run server-side JavaScript scripts at defined intervals or specific times. They power recurring maintenance tasks, data quality checks, report generation, integration polling, and batch processing operations.

ServiceNow provides several related mechanisms for running code on a schedule, each suited to different use cases: Scheduled Script Executions for repeating jobs, Fix Scripts for one-time deployments, and Background Scripts for immediate ad-hoc execution.

---

## Types of Scheduled Automation

| Type | Table | Use Case | Frequency |
|------|-------|---------|-----------|
| Scheduled Script Execution | `sysauto_script` | Recurring automated tasks | Daily/Weekly/Monthly/Periodic |
| Scheduled Report | `sysauto_report` | Auto-generate and email reports | Any schedule |
| Scheduled Data Import | `sysauto_import` | Regular data load from external source | Any schedule |
| Fix Script | `sys_script_fix` | One-time config/data changes during deployment | One-time (on-demand) |
| Background Script | N/A (no persistence) | Ad-hoc immediate execution | Immediate |

---

## Scheduled Script Execution

The most common type of scheduled job for custom logic.

**Navigation:** System Scheduler → Scheduled Jobs → Scheduled Script Executions
**Table:** `sysauto_script`

### Scheduling Options (Run field)

| Option | Description |
|--------|-------------|
| Daily | Runs once per day at a specified time |
| Weekly | Runs on specified days of the week at a specified time |
| Monthly | Runs on a specific day of the month |
| Periodically | Runs every N seconds, minutes, hours |
| Once | Runs one time at a specified date/time, then deactivates |
| On Demand | Never runs automatically; must be triggered manually |
| Business Calendar | Runs according to a business calendar schedule |

### Key Configuration Fields

| Field | Description |
|-------|-------------|
| Name | Descriptive job name |
| Run | Scheduling frequency |
| Time | Specific time for daily/weekly/monthly jobs |
| Day of week/month | For weekly/monthly scheduling |
| Run as | User context for execution (default: System) |
| Active | Enable/disable the job |
| Conditional | If checked, a condition script controls whether the job runs |
| Condition | Script returning `true` to proceed or `false` to skip this run |
| Script | The JavaScript to execute |

### Conditional Execution

The "Conditional" checkbox enables a separate condition script evaluated before the main script runs:

```javascript
// Condition script: Only run on business days
var now = new GlideDateTime();
var dayOfWeek = now.getDayOfWeekLocalTime(); // 1=Sunday, 7=Saturday
if (dayOfWeek == 1 || dayOfWeek == 7) {
    return false; // Skip weekends
}
return true; // Run on weekdays
```

Condition scripts run in a restricted sandbox for security.

### Execution States

| State | Description |
|-------|-------------|
| Ready | Waiting for its scheduled execution time |
| Running | Currently executing |
| Queued | Scheduled to run; waiting for an available worker thread |
| Error | Last execution failed; check system log |

---

## Script Context in Scheduled Jobs

Scheduled job scripts run as server-side JavaScript with access to standard GlideRecord and GlideSystem APIs.

### Key Differences vs. Business Rules

| Aspect | Business Rule | Scheduled Job |
|--------|--------------|--------------|
| `current` available | Yes | No — no record context |
| `previous` available | Yes | No |
| User context | Session user | Configured "Run as" (default: System) |
| Execution trigger | Record event | Time/schedule |
| GlideRecord access | Yes | Yes |
| `gs.*` API | Yes | Yes |

### Typical Script Structure

```javascript
// Good: Use meaningful scope variables, handle errors, log progress
var startTime = new GlideDateTime();
gs.info('Job: Stale Incident Cleanup - Started at {0}', startTime.getDisplayValue());

var processedCount = 0;
var errorCount = 0;

try {
    var gr = new GlideRecord('incident');
    gr.addQuery('state', '6'); // Resolved
    gr.addQuery('resolved_at', '<', gs.daysAgo(30)); // Resolved > 30 days ago
    gr.addQuery('knowledge', false); // No KB article created
    gr.query();

    while (gr.next()) {
        try {
            gr.state = 7; // Closed
            gr.setWorkflow(false);
            gr.update();
            processedCount++;
        } catch(innerEx) {
            gs.error('Failed to close incident {0}: {1}', gr.number, innerEx.getMessage());
            errorCount++;
        }
    }
} catch(ex) {
    gs.error('Job: Stale Incident Cleanup - Fatal error: {0}', ex.getMessage());
}

gs.info('Job: Stale Incident Cleanup - Complete. Processed: {0}, Errors: {1}',
    processedCount, errorCount);
```

---

## Run As (Impersonation)

Scheduled jobs can be configured to run as a specific user, inheriting that user's roles and permissions:

| "Run as" Setting | Behavior |
|-----------------|---------|
| (blank) / System | Runs with full system access — bypasses most ACLs |
| Specific service account | Runs with that account's roles only |
| Specific named user | Runs with that person's access — fragile if person changes roles |

**Best practice:** Create a dedicated service account with only the permissions needed for the job. Running everything as "System" is expedient but bypasses access controls and creates compliance risks.

---

## Performance Considerations for Scheduled Jobs

### Batching Large Data Sets

Processing millions of records in a single job run can:
- Consume worker threads for extended periods (blocking other jobs)
- Cause memory pressure
- Time out or be killed by the system watchdog

**Batching pattern:**

```javascript
// Process max 500 records per run, use a tracker to resume next run
var BATCH_SIZE = 500;
var lastProcessedSysId = gs.getProperty('myjob.last_processed_sys_id', '');

var gr = new GlideRecord('incident');
gr.addQuery('state', '5'); // Some target state
if (lastProcessedSysId) {
    gr.addQuery('sys_id', '>', lastProcessedSysId); // Resume from last position
}
gr.orderBy('sys_id'); // Consistent ordering for resumption
gr.setLimit(BATCH_SIZE);
gr.query();

var lastId = '';
while (gr.next()) {
    // ... process record ...
    lastId = gr.sys_id.toString();
}

// Save last processed position for next run
gs.setProperty('myjob.last_processed_sys_id', lastId);
gs.info('Batch complete. Last processed: {0}', lastId);
```

### Avoid Long-Running Transactions
- Break processing into smaller database transactions using `gs.sleep()` between batches (sparingly)
- Use `setWorkflow(false)` and `setLimit()` to reduce overhead
- Avoid nested GlideRecord queries — use joins or pre-load data instead

### Staggering Job Schedules
Avoid scheduling multiple heavy jobs at the same time (e.g., all at midnight):
- Stagger jobs by 15-30 minutes
- Use "Periodically" option with varying offsets
- Monitor Worker Thread utilization in system diagnostics

---

## System Scheduler

The System Scheduler is the engine that manages all scheduled items.

**Navigation:** System Scheduler → Administration → Scheduled Jobs (list all)
**Table:** `sys_trigger` — stores all scheduled task triggers

**Important:** Do not directly manipulate `sys_trigger` records. Use the Scheduled Jobs module instead. Corrupted trigger records can prevent jobs from running.

### Viewing Running Jobs

Navigate to System Scheduler → Administration → Currently Running:
- See jobs currently executing
- Job name, start time, execution duration
- "Kill" option for runaway jobs (use cautiously)

### System Diagnostics: Worker Thread Threads
Navigate to System Diagnostics → Worker Threads:
- Shows all active worker threads
- Identifies which jobs are consuming threads
- Useful for diagnosing performance issues caused by scheduled jobs

---

## Event-Driven Scheduling

Jobs can be scheduled to run at a future time in response to an event using `gs.eventQueueScheduled()`:

```javascript
// In a Business Rule — schedule a follow-up check 4 hours after incident creation
gs.eventQueueScheduled(
    'incident.sla_check',    // Event name (must be registered)
    current,                  // GlideRecord
    current.number.toString(),// parm1
    '',                       // parm2
    gs.hoursAgo(-4)          // Execute 4 hours from now (negative = future)
);
```

This adds an entry to the `sysevent_schedule` table (not the same as `sysevent`). When the scheduled time arrives, the event fires and triggers any Script Actions or Notifications configured for that event.

---

## Fix Scripts

Fix Scripts are server-side scripts designed for one-time execution during application installation or upgrades. They are the preferred mechanism for deployable data migrations and configuration changes.

**Navigation:** System Update Sets → Fix Scripts (or System Definition → Fix Scripts)
**Table:** `sys_script_fix`

### Key Characteristics

| Property | Fix Script |
|----------|-----------|
| Execution model | Manual trigger or auto-run during update set commit |
| Frequency | Designed for one-time; can be re-run |
| Context | Same server-side JS context |
| Deployment | Part of Update Sets |
| Preferred over | Background Scripts for deployable changes |

### Example Fix Script

```javascript
// Fix Script: Migrate legacy incident categories to new taxonomy
// Author: John Smith — 2025-04-15
// Purpose: One-time migration of 'hardware' category to 'endpoint'

var migrated = 0;
var gr = new GlideRecord('incident');
gr.addQuery('category', 'hardware');
gr.addQuery('state', '7'); // Closed only — safe to migrate
gr.query();

while (gr.next()) {
    gr.category = 'endpoint';
    gr.subcategory = 'hardware_device';
    gr.setWorkflow(false);
    gr.update();
    migrated++;
}

gs.info('Fix Script: Migrated {0} closed incidents from hardware to endpoint category', migrated);
```

### Fix Script vs. Scheduled Script

| Factor | Fix Script | Scheduled Script |
|--------|-----------|-----------------|
| Runs automatically | Only during update set commit (optional) | Yes, on schedule |
| Part of deployment | Yes — included in Update Sets | No |
| Idempotent requirement | Should be safe to run multiple times | Depends on job |
| Use case | Data migration, config changes | Ongoing maintenance |

---

## Background Scripts

Background Scripts provide an immediate execution environment for ad-hoc scripts. They run synchronously and return output to the browser.

**Navigation:** System Definition → Background Scripts
**Access:** Admin role required (`background_script` sub-role)

### When to Use
- Emergency data corrections on production (with caution)
- Testing and debugging Script Includes or business logic
- One-off queries to check data state
- NOT for repeating tasks — use Scheduled Script Executions instead

### Example Background Script

```javascript
// Quick check: How many P1 incidents are open right now?
var ga = new GlideAggregate('incident');
ga.addQuery('priority', '1');
ga.addQuery('state', 'IN', '1,2,3');
ga.addAggregate('COUNT');
ga.query();
var count = ga.next() ? ga.getAggregate('COUNT') : 0;
gs.print('Open P1 Incidents: ' + count);
```

Output appears directly in the browser after execution.

**Security warning:** Background Scripts run with admin-level access. Access should be restricted to senior administrators. Audit log captures all executions.

---

## Best Practices

### Naming and Documentation
- Use descriptive names: "Nightly: Close Stale Resolved Incidents"
- Add a comment block at the top of every script with purpose, author, date, and modification history
- Document the job's impact (what records it modifies, how many)

### Error Handling
- Wrap all logic in try/catch blocks
- Log both start and completion with record counts
- Log individual record errors without stopping the entire batch
- Set up monitoring alerts for jobs that fail (use Script Actions on error events)

### Testing Before Production
- Test scheduled jobs in development using "On Demand" option
- Verify with limited data sets before running against full production data
- Confirm `setWorkflow(false)` is used appropriately to prevent unintended side effects

### Idempotency
Design scheduled jobs to be safely re-runnable:
- Check if work has already been done before doing it again
- Use state fields or marker fields to track processed records
- Avoid side effects (emails, external API calls) from being triggered multiple times

### Monitoring
- Review System Scheduler → Scheduled Jobs for jobs in Error state daily
- Set up Performance Analytics indicators for job success rates
- Alert on jobs that have not run within expected time window

---

## Common Patterns

### Nightly SLA Breach Report Email

```javascript
// Scheduled Script: Weekly SLA Breach Summary
// Run: Weekly, Monday 08:00

var ga = new GlideAggregate('task_sla');
ga.addQuery('has_breached', 'true');
ga.addQuery('end_time', '>=', gs.daysAgo(7));
ga.addQuery('end_time', '<=', gs.nowDateTime());
ga.addAggregate('COUNT', 'stage');
ga.groupBy('sla.name');
ga.query();

var report = [];
while (ga.next()) {
    report.push({
        sla: ga.getDisplayValue('sla.name'),
        breachCount: ga.getAggregate('COUNT', 'stage')
    });
}

// Send formatted email via event
gs.eventQueue('sla.weekly_breach_report',
    new GlideRecord('incident'), // dummy record
    JSON.stringify(report),
    gs.getUserID());
```

### Data Quality Check Job

```javascript
// Check for incidents with no assignment group and alert
var gr = new GlideRecord('incident');
gr.addQuery('state', 'IN', '1,2,3'); // Active states
gr.addQuery('assignment_group', 'ISEMPTY');
gr.addQuery('sys_created_on', '<', gs.hoursAgo(4)); // Older than 4 hours
gr.query();

while (gr.next()) {
    gs.eventQueue('incident.unassigned_alert', gr,
        gr.number.toString(), gr.priority.toString());
}
```
