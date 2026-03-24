# Problem Management
Source: WebFetch (nowben.com, servicenow.com/community)

## Definition
Problem Management identifies and resolves underlying causes of recurring incidents. "Incidents fix the pain; problems cure the disease."

## Lifecycle States
1. **New** — Initial logging
2. **Assess** — Problem Manager evaluates impact scope and affected services
3. **Root Cause Analysis (RCA)** — Technical investigation of underlying causes
4. **Fix in Progress** — Permanent solution planned and implemented via change requests
5. **Resolved** — Fix verified; system monitored
6. **Closed** — Solution effectiveness confirmed; knowledge articles updated

## Root Cause Analysis Process
- Review linked incidents for recurring patterns
- Analyze system logs and performance alerts
- Consult support engineers and technical teams
- Reproduce issues in lower environments
- Document findings in cause notes and fix notes

### RCA Tools
- **Cause-and-Effect Diagrams (Fishbone/Ishikawa)** — visualize cause categories
- **Five Whys Analysis** — drill down by asking "why" repeatedly
- **Pareto Analysis** — identify most significant contributing causes

## Incident vs. Problem
| Aspect | Incident | Problem |
|--------|----------|---------|
| Focus | Service restoration speed | Root cause identification |
| Nature | Reactive | Proactive/Reactive |
| Users | User-facing | Backend technical teams |
| Timeframe | Short-term fix | Long-term permanent solution |

## Known Errors
- Documented when root cause is found but permanent fix not yet implemented
- One-click creates Known Error Article in Knowledge Base
- Enables faster response to recurring issues with proven workarounds

## Workarounds
- Temporary service restoration while permanent fix is in progress
- Example: restart application while planning memory patch deployment
- Documented on problem record for reuse

## Key Fields
- Problem Statement, Description, Related Incidents
- Impact/Urgency/Priority (auto-calculated)
- Workaround, Cause Notes, Fix Notes
- Work Notes (internal tracking)
- State, Assignment Group

## Risk Acceptance
- From RCA or Fix in Progress states, coordinator can accept risk of not fixing
- Resolution code: "Risk Accepted"
- Used when fix cost > risk, or fix cannot be determined

## Integration
- Problem → creates Change Request (Fix in Progress state)
- Problem → creates Known Error Article in KB
- Multiple Incidents → linked to one Problem

## Table
- Primary table: `problem` (extends `task`)
