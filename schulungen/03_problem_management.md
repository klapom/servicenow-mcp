---
source_type: process
topics:
  - problem management
  - root cause analysis
  - known error
  - ITSM
  - workaround
  - knowledge base
---

# Problem Management

## Overview

Problem Management is the ITSM process responsible for identifying and eliminating the root causes of recurring incidents. While Incident Management restores service quickly (reactive), Problem Management investigates why the incident occurred in the first place and prevents recurrence (proactive and reactive).

The guiding principle: **"Incidents fix the pain; problems cure the disease."**

ServiceNow implements Problem Management through the `problem` table, which extends the `task` table. Problems are linked to incidents, change requests, and knowledge articles, forming a complete chain from symptom detection to permanent fix.

---

## Core Concepts

### Problem vs. Incident vs. Known Error

| Concept | Definition | Table |
|---------|-----------|-------|
| Incident | Unplanned disruption; goal is fast restoration | `incident` |
| Problem | Underlying cause of one or more incidents | `problem` |
| Known Error | A problem where root cause is identified but no permanent fix exists yet | `problem` (with known_error = true) + `kb_knowledge` |
| Workaround | Temporary relief that reduces/eliminates impact while permanent fix is planned | Documented on problem record |

### When to Create a Problem Record

A problem record should be created when:
- Multiple incidents share the same root cause
- A critical incident (P1/P2) has occurred and requires formal root cause analysis
- A trend analysis reveals recurring patterns in a category/subcategory
- Proactive monitoring identifies a potential failure before it causes an incident
- An incident is resolved with a workaround but no permanent fix

### Reactive vs. Proactive Problem Management

| Type | Trigger | Focus |
|------|---------|-------|
| Reactive | After recurring incidents | Stop recurrence |
| Proactive | Trend analysis, monitoring | Prevent incidents before they occur |

---

## Lifecycle States

| State | Description |
|-------|-------------|
| New | Initial logging; problem not yet analyzed |
| Assess | Problem Manager evaluates impact scope, affected services, and business priority |
| Root Cause Analysis (RCA) | Technical investigation of underlying causes; full investigation underway |
| Fix in Progress | Permanent solution planned; change request created and being implemented |
| Resolved | Fix verified; system monitored; resolution confirmed effective |
| Closed | Solution effectiveness confirmed; knowledge articles updated; record archived |

### State Transition Diagram

```
New → Assess → Root Cause Analysis → Fix in Progress → Resolved → Closed
                      ↓
              (Known Error documented)
                      ↓
              Fix in Progress (via Change)
                      ↓
              Risk Accepted (no fix possible/warranted)
                      ↓
              Resolved (with Risk Accepted close code)
```

### Risk Acceptance Path

From either Root Cause Analysis or Fix in Progress, a coordinator can accept the risk of not implementing a fix:
- Used when fix cost exceeds the risk/impact of the problem
- Used when root cause cannot be determined despite thorough analysis
- Resolution code: **"Risk Accepted"**
- Problem closes without a permanent technical fix; monitoring may be enhanced

---

## Root Cause Analysis Process

RCA is the core investigative phase of Problem Management. It transforms symptom data (from incidents) into a definitive understanding of the underlying cause.

### RCA Input Sources
1. Review all linked incidents for recurring patterns and commonalities
2. Analyze system logs and performance metrics around incident occurrence times
3. Review recent changes that may have introduced the defect
4. Consult support engineers, architects, and technical subject matter experts
5. Reproduce the issue in lower (non-production) environments when safe to do so
6. Examine CMDB for CI health, dependencies, and recent modifications

### RCA Documentation Fields

| Field | Purpose |
|-------|---------|
| `cause_notes` | Documented root cause explanation |
| `fix_notes` | Description of the permanent fix implemented or planned |
| `workaround` | Temporary relief procedure for use until permanent fix is in place |
| `problem_statement` | Clear, concise statement of the problem being investigated |

### RCA Tools and Techniques

#### Fishbone (Ishikawa) Diagram
Visualizes potential cause categories that may contribute to the problem:
- People (human error, training gaps)
- Process (procedure deficiencies)
- Technology (software bugs, hardware failures)
- Environment (infrastructure, configuration drift)

Each "bone" of the diagram represents a category; teams brainstorm specific causes within each category.

#### Five Whys Analysis
A systematic technique for drilling to root cause by repeatedly asking "Why?":

```
Problem: Application unavailable for 3 hours
Why 1: Application server crashed
Why 2: Memory exhausted on the server
Why 3: Memory leak in the application code
Why 4: Code change deployed without memory profiling
Why 5: Memory profiling not included in deployment checklist
Root Cause: Incomplete deployment checklist
Fix: Update checklist to include memory profiling step
```

#### Pareto Analysis
Identify the 20% of causes responsible for 80% of incidents:
- Sort incidents by category/subcategory frequency
- Focus problem investigations on highest-volume categories first
- Track reduction in incident volume after fixes are deployed

---

## Known Errors

A Known Error is the state when:
- The root cause of the problem has been identified
- No permanent fix has been implemented yet (fix is pending, planned, or impractical)
- A workaround is available to reduce incident impact

### Known Error Workflow in ServiceNow

1. During Root Cause Analysis, Problem Coordinator marks `known_error = true` on the problem record
2. **One-click creation:** The "Create Known Error Article" UI action creates a Knowledge Article in the designated Known Error Knowledge Base
3. The knowledge article is linked back to the problem record
4. Service Desk agents can find the workaround when handling future incidents related to the same issue
5. When the problem is permanently resolved, the known error article is retired

### Known Error Article Structure
- **Short Description:** Clear problem statement that agents can search for
- **Symptoms:** How end users experience this issue
- **Cause:** Root cause explanation (technical detail appropriate for resolver audience)
- **Workaround:** Step-by-step instructions to restore service temporarily
- **Status:** Linked change request number for tracking permanent fix progress

---

## Workarounds

A workaround is a temporary measure that reduces or eliminates the impact of a problem while a permanent fix is being developed.

### Workaround Characteristics
- Documented on the problem record in the `workaround` field
- Should be specific and actionable — not vague
- Should specify who can perform the workaround (end user vs. resolver vs. specialist)
- Should document any risks or side effects of the workaround

### Example Workaround Documentation
```
Problem: Email server rejects attachments over 10MB sporadically
Workaround:
1. User compresses attachment using 7-Zip before sending
2. If compression insufficient, upload to SharePoint and send link instead
3. IT Ops team: Restart the email gateway service (svc-emailgw) if error rate exceeds 5/hour
   (Command: systemctl restart email-gateway on srv-mail-01)
Note: Restart restores service for approximately 4-6 hours
Risk: Brief service interruption during restart (< 30 seconds)
```

---

## Integration with Other ITSM Processes

### Problem → Incident
- Multiple incidents can be linked to a single problem record (many-to-one)
- When a problem moves to Known Error state, the workaround is available to resolvers of new incidents
- When a problem is resolved, linked open incidents may be resolved with a reference to the problem fix

### Problem → Change Management
- At the "Fix in Progress" state, the Problem Coordinator creates a Change Request to implement the permanent fix
- The change request is linked to the problem record
- When the change completes successfully, the problem advances from Fix in Progress to Resolved
- If the change fails, the problem returns to Root Cause Analysis or Fix in Progress

### Problem → Knowledge Management
- Known Error articles are created in the Knowledge Base from problem records
- Post-resolution, a formal knowledge article documents the root cause and fix
- Articles are flagged as KCS (Knowledge-Centered Service) articles when created by qualified contributors

### Relationship Summary

```
Incidents (many) ──linked to──► Problem (one)
                                     │
                                     ├──creates──► Change Request
                                     │
                                     └──creates──► Knowledge Article (Known Error)
```

---

## Key Fields

| Field Name | Type | Description |
|-----------|------|-------------|
| `number` | String | Auto-generated PRB number (e.g., PRB0001234) |
| `state` | Integer (choice) | Current lifecycle state |
| `problem_state` | Integer (choice) | Extended problem-specific state values |
| `known_error` | Boolean | Whether root cause is known but unfixed |
| `workaround` | String | Temporary fix description |
| `workaround_applied` | Boolean | Whether workaround is currently in use |
| `cause_notes` | String | Root cause documentation |
| `fix_notes` | String | Permanent fix description |
| `problem_statement` | String | Clear problem description |
| `impact` | Integer (choice) | Business impact level |
| `urgency` | Integer (choice) | Time sensitivity |
| `priority` | Integer (choice) | Auto-calculated |
| `assignment_group` | Reference → sys_user_group | Team responsible |
| `assigned_to` | Reference → sys_user | Primary investigator |
| `cmdb_ci` | Reference → cmdb_ci | Affected CI |
| `business_service` | Reference → cmdb_ci | Affected service |
| `fix_by` | DateTime | Target date for permanent fix |
| `close_code` | String (choice) | Solution / Risk Accepted / Canceled |
| `close_notes` | String | Closure documentation |

---

## Key Roles

| Role | Responsibilities |
|------|----------------|
| Problem Manager | Owns the Problem Management process; ensures quality and SLA compliance |
| Problem Coordinator | Creates and manages individual problem records; drives investigation |
| Technical Lead / SME | Performs deep technical RCA; documents findings |
| Knowledge Manager | Reviews and publishes Known Error articles |
| Change Coordinator | Creates change requests to implement problem fixes |

### ServiceNow Roles

| Role Name | Access |
|-----------|--------|
| `itil` | Create and read problem records |
| `problem_coordinator` | Full problem lifecycle management |
| `problem_admin` | Administrative access; override and configuration |

---

## Best Practices

### When to Create a Problem vs. When to Link Incidents
- Create a problem when the same root cause appears in 3+ incidents, or after any P1/P2 incident
- Link all related incidents to the problem record for complete impact visibility
- Do not create one problem per incident — identify the common thread

### Problem Statement Quality
A good problem statement answers:
- **What** is failing? (specific component/service)
- **When** does it fail? (conditions, frequency, time patterns)
- **Who/What** is affected? (users, services, geography)
- **How** does it manifest? (error messages, symptoms, user experience)

### Workaround Documentation
- Test the workaround before documenting it
- Include specific commands, UI steps, or configuration settings
- Specify role/access requirements to perform the workaround
- Document known side effects and duration of effectiveness

### SLA and Target Dates
- Problem Management does not typically use the same SLA structure as Incident Management
- Use the `fix_by` target date field to track expected resolution timeline
- Set realistic target dates based on the complexity of the fix, not arbitrary deadlines

### Metrics and Reporting

| Metric | Formula | Target |
|--------|---------|--------|
| Recurring incident reduction | % decrease in incidents linked to known problems | >20% quarterly |
| Mean Time to Detect (MTTD) | Time from first incident to problem creation | Track trend |
| Mean Time to Resolve (MTTR) | Time from problem creation to closure | Track by priority |
| Known Error coverage | % of recurring incidents with documented workaround | >80% |
| Problem backlog age | Problems open > 90 days | <10% of backlog |

---

## Common Patterns

### Proactive Problem from Trend Analysis
Monthly or weekly scheduled report identifies:
- Incident categories with >5 recurrences in the past 30 days
- Assignment groups exceeding their incident volume baseline
- CIs with >3 incidents in 30 days

Problem Coordinator reviews the list and opens proactive problem records before the volume triggers executive escalation.

### P1 Incident → Problem Handoff
1. P1 incident resolved with workaround (not permanent fix)
2. Incident closed; Problem record created automatically or manually
3. Problem inherits affected CI, service, and incident details
4. Known Error article created with the workaround from the incident
5. Technical team begins RCA
6. Change request created when root cause identified
7. Change deployed; problem resolved; Known Error article retired

### Problem Backlog Review
Weekly or bi-weekly review meeting between Problem Manager and technical leads:
- Review all problems in RCA and Fix in Progress states
- Validate target dates are still realistic
- Escalate problems blocked on resource allocation
- Close problems where risk has been formally accepted
