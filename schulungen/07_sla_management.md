---
source_type: platform
topics:
  - SLA
  - OLA
  - underpinning contract
  - task_sla
  - contract_sla
  - breach
  - escalation
  - schedules
---

# SLA Management

## Overview

Service Level Agreements (SLAs) define the time-based commitments for resolving or responding to tasks in ServiceNow. The SLA framework measures performance against defined targets, pauses timing during waiting periods, and triggers automated escalations as deadlines approach.

ServiceNow's SLA engine operates on any table that extends `task`. It supports three types of service-level agreements and provides a rich set of conditions, schedules, timezone handling, and escalation workflows.

---

## Core Concepts and Terminology

### SLA vs. OLA vs. UC

| Type | Full Name | Description |
|------|-----------|-------------|
| SLA | Service Level Agreement | Commitment to the customer/end user |
| OLA | Operational Level Agreement | Internal commitment between IT teams |
| UC | Underpinning Contract | Commitment from an external vendor/supplier |

All three types are managed using the same SLA Definition mechanism in ServiceNow. The `type` field on `contract_sla` distinguishes them.

### Response vs. Resolution SLA

| SLA Target | Measures | Starts When | Stops When |
|------------|---------|-------------|-----------|
| Response | Time to acknowledge/assign | Record created | Record assigned or first response |
| Resolution | Time to fully resolve | Record created (or SLA attachment) | Record moved to resolved/closed state |

---

## SLA Tables

### `contract_sla` (SLA Definition)
Stores the configuration of each SLA. One record per SLA definition.

| Field | Description |
|-------|-------------|
| `name` | SLA name (e.g., "P1 Resolution SLA") |
| `type` | SLA, OLA, or Underpinning Contract |
| `target` | Response or Resolution |
| `table` | The task table this SLA applies to (e.g., `incident`) |
| `duration` | Fixed time or Relative (scripted) |
| `duration_type` | User Specified or Scripted |
| `schedule` | Business hours schedule (blank = 24/7) |
| `timezone` | Timezone for duration calculation |
| `start_condition` | Script/condition when SLA attaches |
| `stop_condition` | Script/condition when SLA completes |
| `pause_condition` | Script/condition when timing pauses |
| `resume_condition` | Script/condition when timing resumes |
| `reset_condition` | Script/condition to cancel and restart SLA |
| `retroactive_start` | Use a past field value as start time |
| `retroactive_pause` | Back-calculate pause time from retroactive start |
| `flow` | Flow Designer flow to run at breach thresholds |
| `active` | Whether this SLA definition is enabled |

### `task_sla` (Task SLA Instance)
Stores each individual SLA timer attached to a specific task record. One record per SLA instance per task.

| Field | Description |
|-------|-------------|
| `task` | Reference to the task record (e.g., specific incident) |
| `sla` | Reference to `contract_sla` definition |
| `stage` | Current SLA state: In Progress, Paused, Completed, Breached, Cancelled |
| `start_time` | When the SLA timer started |
| `end_time` | When the SLA was completed or breached |
| `breach_time` | Calculated time when breach would occur |
| `original_breach_time` | Initial breach calculation (before any resets) |
| `pause_duration` | Total accumulated pause time |
| `business_elapsed` | Business time elapsed (within schedule) |
| `business_left` | Business time remaining |
| `business_percentage` | Percentage of SLA duration consumed |
| `actual_elapsed` | Wall-clock time elapsed (calendar) |
| `has_breached` | Boolean — true if breach occurred |
| `made_sla` | Boolean — true if resolved before breach |

---

## SLA Stages and States

The `task_sla` record transitions through stages during its lifecycle:

| Stage | Description |
|-------|-------------|
| In Progress | SLA is active; timer accumulating |
| Paused | Timer suspended (pause condition met) |
| Completed | Stop condition met before breach — SLA met |
| Breached | Elapsed time exceeded allowed duration — SLA missed |
| Cancelled | Start conditions no longer met, or cancel condition triggered |

### Stage Transition Diagram

```
(start condition met)
        ↓
   In Progress
   ↙        ↘
Paused    Completed (stop condition met, before breach)
   ↘        ↘
    In Progress   Breached (time expired)
                       ↘
                    Completed (resolved after breach — still marked Breached)
```

---

## SLA Conditions

SLA behavior is governed by four conditions evaluated against the task record:

### Start Condition
Determines when an SLA attaches to a task:
- Example: Incident state = "New" AND Priority = 1
- An SLA attaches when these conditions are first true
- Multiple SLAs can attach to the same task (e.g., both a Response SLA and a Resolution SLA)

### Stop Condition
Determines when the SLA is considered complete (successfully):
- Example: Incident state = "Resolved" OR Incident state = "Closed"
- When met, `task_sla.stage` → "Completed"
- `made_sla` = true if stop condition met before breach time

### Pause Condition
Defines when the SLA clock temporarily stops:
- Example: Incident On Hold = true (state = 3)
- Common pattern: SLA pauses when On Hold reason = "Awaiting Caller" or "Awaiting Vendor"
- When pause condition is true, `task_sla.stage` → "Paused"

### Resume Condition
Defines when the SLA clock restarts after a pause:
- Example: Incident On Hold = false (state = 2)
- Must be the logical inverse of or complement to the pause condition
- **Important:** If pause conditions are a strict subset of start conditions, the SLA may cancel rather than resume

### Cancel Condition
Cancels the SLA entirely (different from pause):
- Example: Incident is reassigned to a different assignment group after initial attachment
- Used when the original SLA definition is no longer relevant

---

## Duration Configuration

### User Specified (Fixed Duration)
The SLA expires after a fixed amount of time:
- Duration: 4 hours, 8 hours, 3 days, etc.
- Combined with a schedule for business-hours-only calculation

### Scripted Duration (Relative)
The duration is calculated by a script at SLA attachment time:
- Example: Duration varies based on customer tier or contract terms
- Script returns a `GlideDuration` object
- Used for dynamic SLA targets (e.g., VIP customers get 2-hour SLAs, standard customers get 4-hour)

### Duration Calculation Formula

```
Breach Time = Start Time + Duration (adjusted for schedule and timezone)
             - any excluded time from schedule (e.g., nights, weekends)
             + any accumulated pause duration

Business_percentage = (Business_Elapsed / Total_SLA_Duration) × 100
```

---

## Schedules and Timezones

### Schedules
Schedules define the "business hours" within which SLA time accumulates:

| Configuration | Behavior |
|--------------|---------|
| No schedule assigned | SLA runs 24/7; all time counts |
| "8x5" schedule | SLA counts Monday–Friday 8:00–17:00 only |
| "24x7" schedule | All time counts (explicit) |
| Holiday schedule included | Specific days excluded from SLA counting |

Days specified in the duration are converted to 24-hour blocks when no schedule is used. With a schedule, "1 day" = 8 business hours (on an 8-hour daily schedule).

### Timezone Resolution
Timezone for SLA calculation is sourced in this priority order:

1. SLA Definition `timezone` field (if explicitly set)
2. Caller's timezone (from `incident.caller_id.time_zone`)
3. CI Location timezone
4. Task Location timezone
5. System default timezone (fallback)

---

## Retroactive Start and Pause

### Retroactive Start
Adjusts the SLA start time backward to a past event:
- Instead of starting when the SLA definition is first matched, use the record's creation time or "Opened" field
- Prevents artificially extending SLA time by delaying SLA attachment
- Example: Incident created at 09:00, SLA definition matches at 09:15 → Retroactive Start sets SLA start to 09:00

### Retroactive Pause
Calculates and applies any pause time that should have occurred between the retroactive start and the attachment time:
- Prevents immediate breaches when SLA attaches to an already-old record
- Example: Incident was On Hold for 2 hours before SLA attached → retroactive pause credits those 2 hours

---

## SLA Breach Escalation

### Default SLA Notification Flow
The out-of-the-box SLA escalation flow triggers notifications at defined thresholds:

| Threshold | Notification Recipients |
|-----------|------------------------|
| 50% of SLA duration elapsed | Assignee + CI "Supported by" user |
| 75% of SLA duration elapsed | Assignee + Assignee's manager |
| 100% (breach) | Assignee + Manager + Assignment group manager |

### Custom Escalation Logic
Organizations can customize escalation behavior:
- Send to different groups at different thresholds
- Create work notes on the record at escalation points
- Reassign to an escalation group if still unassigned at 75%
- Open a Major Incident if P1 SLA breaches

### System Property: Breached SLA Workflows
`com.snc.sla.workflow.run_for_breached`: Controls whether the SLA flow/workflow triggers for SLAs that are already breached at the moment of attachment (e.g., when an old record gets an SLA attached retroactively).

---

## SLA Reset Scenarios

When a change cancels and restarts an SLA:

| Trigger | Behavior |
|---------|---------|
| Priority change on incident | Current SLA cancelled; new SLA for new priority attaches |
| Incident reopened | Resolution SLA resets; new SLA starts |
| Record assigned to different group (if configured) | SLA may cancel and reattach based on new group conditions |

---

## Multiple SLAs Per Task

A single task can have multiple simultaneous SLA instances:
- Response SLA (measures time to assignment)
- Resolution SLA (measures time to resolution)
- OLA for first-level support group
- OLA for escalation group (attaches when incident is reassigned)

Each generates its own `task_sla` record. Reporting can show compliance per SLA type.

---

## SLA Repair

The **SLA Repair** feature recalculates `task_sla` records when conditions change:
- System property: `com.snc.sla.repair.enabled = true`
- Used when SLA definitions are modified retroactively
- Can recalculate historical `task_sla` records to reflect new conditions
- Should be used carefully — running repair on large datasets has performance implications

---

## Key System Properties

| Property | Default | Description |
|----------|---------|-------------|
| `com.snc.sla.calculation.percentage` | 1000% | Cap on SLA percentage calculation; stops math for records breached by large margins |
| `com.snc.sla.repair.enabled` | false | Enables SLA Repair feature |
| `com.snc.sla.workflow.run_for_breached` | false | Run workflow/flow for already-breached SLAs |
| `com.snc.sla.pause_on_transfer` | false | Pause SLA when incident is transferred between groups |

---

## SLA Reporting

### Key Metrics to Track

| Metric | Query |
|--------|-------|
| SLA compliance rate | % of `task_sla` records with `made_sla = true` |
| Average business time to resolution | Average of `business_elapsed` on Completed records |
| Breach count by priority | Count of Breached records grouped by task priority |
| Breach count by assignment group | Identify teams consistently missing SLAs |
| SLA cancellation rate | High cancellation may indicate misconfigured conditions |

### Useful Reports
- **SLA Compliance by Priority:** Bar chart showing % met vs. breached per priority
- **SLA Performance Trend:** Line chart of compliance rate over time
- **Breached SLA Drill-down:** List of all breached SLAs with assignee and group details
- **Average Resolution Time vs. SLA Target:** Variance analysis

---

## Best Practices

### SLA Design
- Keep the number of SLA definitions manageable — avoid creating one SLA per group or per category
- Use priority-based SLAs that match your Priority Matrix for Incident Management
- Define clear, unambiguous start and stop conditions
- Test SLA behavior in a development instance before deploying to production

### Pause Condition Design
- Pause conditions should match meaningful external dependencies (On Hold states)
- Document which On Hold reasons pause the SLA — end users and agents need to understand this
- Avoid using On Hold/Pause to artificially manage SLA numbers — this undermines reporting integrity

### Schedule Configuration
- Business hours schedules must include timezone awareness
- Include holiday calendars in schedules to prevent breaches during known shutdowns
- Review schedules annually and update for changes in business hours

### Governance
- Report on SLA compliance monthly at the management level
- Investigate root causes of chronic SLA breaches — address staffing, tool, or process gaps
- Do not retroactively modify SLA definitions to fix compliance numbers — fix the underlying issues

---

## Common Patterns

### Priority-Based Incident SLA Set
Standard enterprise SLA configuration for incidents:

```
P1 Critical:  Response 15min, Resolution 1hr  — 24x7 schedule
P2 High:      Response 1hr,   Resolution 4hr  — 24x7 schedule
P3 Moderate:  Response 4hr,   Resolution 8hr  — 8x5 schedule
P4 Low:       Response 8hr,   Resolution 3 days — 8x5 schedule
```

All four SLA definitions have:
- Start condition: Incident.Priority = [X] AND Incident.State = 1 (New)
- Stop condition: Incident.State IN (6 = Resolved, 7 = Closed)
- Pause condition: Incident.On Hold = true
- Resume condition: Incident.On Hold = false

### OLA for Assignment Group
An OLA measures internal team response time:
- Start: Incident assigned to "Network Operations" group
- Stop: Incident state changed to "Resolved"
- Duration: 2 hours (business hours, 24x7 for network team)
- This runs alongside the customer-facing Resolution SLA
- If the OLA is breached, the group manager is notified separately from the SLA escalation
