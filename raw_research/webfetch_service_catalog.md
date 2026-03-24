# Service Catalog & Request Fulfillment
Source: WebFetch (servicenowelite.com, servicenowspectaculars.com, reco.ai)

## Core Tables
| Table | Name | Purpose |
|-------|------|---------|
| `sc_request` | Request (REQ) | The cart/order container |
| `sc_req_item` | Requested Item (RITM) | Individual item within request |
| `sc_task` | Catalog Task | Actual work unit assigned to a person/group |

## Hierarchy & Relationships
- One REQ can have multiple RITMs (different catalog items in one cart)
- One RITM can have multiple sc_tasks
- **Requests and RITMs are NOT assigned** — only sc_task is assigned to group/user
- Closure cascades up: closed tasks → RITM closes → REQ closes

## Catalog Components
- **Catalog Items** — requestable services (e.g., "Request New Laptop")
- **Categories** — organize items logically (IT, HR, Facilities)
- **Variables** — user input fields (Single Line, Multiple Choice, Reference, Checkbox, Date)
- **Variable Sets** — reusable groupings across multiple catalog items
- **Record Producers** — create entries in target tables with auto-filled fields
- **Order Guides** — multi-item bundles with a single request

## Fulfillment Workflow
Two OOB workflows per request:
1. **Request level** (sc_request) — approval for entire cart
2. **RITM level** (sc_req_item) — item-specific workflow

RITM Stage Field tracks: Waiting for Approval → Fulfillment → Rejected → Closed

## Approval Types (Step-Based Fulfillment)
- **Manager approval** — routes to the requested-for user's manager
- **Custom approval** — specific users/groups with conditions
- **Task creation** — creates sc_task for fulfillment work

## Modern Approach: Flow Designer (Step-Based)
- Recommended over legacy Workflow Editor
- Add fulfillment steps: approval, task creation, notifications
- Supports conditional logic, parallel branches

## Request vs. Incident
| Feature | Request | Incident |
|---------|---------|---------|
| Purpose | Formal service request | Service disruption |
| Cart | Yes (multi-item) | No |
| Approval | Yes | Not typically |
| Workflow | Yes | Assignment-based |

## Best Practices
- Naming conventions for items and variables
- Use order numbers to sort variables logically
- Group related variables with containers
- Test in impersonation mode
- Optimize reference fields for form load performance
- Leverage catalog item templates for standardization

## Key RITM Fields
- state, stage, approval, assigned_to, assignment_group
- Variables stored in sc_item_option_mtom (m2m) table
