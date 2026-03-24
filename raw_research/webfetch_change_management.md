# Change Management
Source: WebFetch (servicenow.com/community, visualpath)

## Definition
Change Management manages change requests through their lifecycle, ensuring standardized methods minimize IT service disruptions.

## Change Types
| Type | Description | CAB Required |
|------|-------------|-------------|
| **Standard** | Pre-authorized, low-risk, follows documented procedure | No |
| **Normal** | Non-emergency, full review required | Yes (all high/moderate risk) |
| **Emergency** | Production/network downtime, rapid approval needed | ECAB only |

## Six OOB Workflow Types
1. **Default Normal Change Management** — Change Coordinator → Manager approval → CAB → Implement → Close
2. **Default Standard Change Management** — Simplified, Coordinator → Change Manager → Implement
3. **Default Emergency Change Management** — Coordinator direct OR ECAB (all members OR any one)
4. **Default Break Fix Change Management** — Minor fixes, Coordinator → Change Management review
5. **Major Change Management** — Multi-team, complex flow with IT Support evaluation
6. **DevOps Change Management** — SSH/Release Automation, Assessment → Plan → CAB → Build → Test → Implement

## State Progression
### Normal Change States:
New → Assess → Authorize → Scheduled → Implement → Review → Closed

### Standard Change States:
New → Scheduled → Implement → Closed (simplified)

### Emergency Change States:
New → Authorize → Scheduled → Implement → Review → Closed (bypasses group/peer review)

## CAB (Change Advisory Board)
- **Authorize state** handles CAB approval
- High and moderate-risk changes automatically require CAB group approval
- If approved at CAB → moves to Scheduled
- If rejected → returns to New with reason
- Emergency changes → ECAB (Emergency CAB)

## Risk Assessment
- Risk levels: High, Moderate, Low
- High/moderate-risk triggers mandatory CAB
- Risk drives approval workflow selection

## Key Roles
- Change Coordinator: creates, assesses, submits
- Change Manager: reviews, approves/rejects
- CAB members: approve at Authorize stage
- Implementer: executes change tasks

## Table
- Primary table: `change_request` (extends `task`)
- Key fields: type, state, risk, impact, priority, start_date, end_date, assignment_group, cab_required, change_plan, backout_plan, test_plan
- Change tasks: `change_task` table
