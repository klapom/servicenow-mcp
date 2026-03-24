---
source_type: process
topics:
  - service catalog
  - request fulfillment
  - RITM
  - sc_request
  - catalog items
  - flow designer
  - variables
---

# Service Catalog and Request Fulfillment

## Overview

The Service Catalog is a self-service portal where users can browse and request IT and business services. It transforms informal requests (email to IT, Slack messages, hallway conversations) into structured, tracked, and auditable service requests with defined fulfillment workflows, approval chains, and SLAs.

ServiceNow Request Fulfillment is built on three core tables: `sc_request` (the cart), `sc_req_item` (individual items), and `sc_task` (the work units). Understanding how these relate to each other is essential for designing effective catalog implementations.

---

## Core Concepts

### Request vs. Incident vs. Change

| Feature | Service Request | Incident | Change Request |
|---------|----------------|---------|----------------|
| Purpose | Fulfill a business/IT need | Restore service after disruption | Controlled infrastructure modification |
| Initiated by | User actively requesting something | User/system reporting a problem | IT team planning a modification |
| SLA type | Fulfillment SLA (days) | Resolution SLA (hours) | Implementation window |
| Approval required | Yes (configurable) | Rarely | Yes (depends on type) |
| Cart support | Yes (multiple items) | No | No |
| Table | `sc_request` / `sc_req_item` | `incident` | `change_request` |

---

## The Three-Table Model

### `sc_request` (REQ — The Request / Cart)

The container for everything a user orders in a single session. Like an online shopping cart — one request can contain multiple items.

- **Number format:** REQ0001234
- **Does NOT have assignment** — the request itself is never assigned to a person or group
- **Approval at request level** covers the entire order (e.g., manager approval for any catalog request)
- Closes automatically when all its `sc_req_item` records are closed

Key fields:
| Field | Description |
|-------|-------------|
| `requested_for` | The user the request is FOR (may differ from `opened_by`) |
| `opened_by` | The user who submitted the request |
| `state` | Request state (Submitted, In Progress, Closed Complete, Closed Incomplete, Canceled) |
| `approval` | Approval state for the entire request (Not Requested, Requested, Approved, Rejected) |
| `price` | Total price of all items in the request |
| `special_instructions` | Free-text instructions from the requester |

### `sc_req_item` (RITM — Requested Item)

Each individual catalog item ordered. When a user requests a laptop AND a software license, that creates two RITMs under one REQ.

- **Number format:** RITM0001234
- **Does NOT have assignment** — the RITM itself is not assigned to a person or group
- Has its own approval, workflow/flow, and stage tracking
- Variables (user input from the catalog form) are stored and linked to the RITM

Key fields:
| Field | Description |
|-------|-------------|
| `request` | Reference to parent `sc_request` |
| `cat_item` | Reference to the `sc_cat_item` catalog item definition |
| `state` | RITM state (Pending, Open, Work in Progress, Closed Complete, Closed Incomplete, Canceled) |
| `stage` | Human-readable stage label (Waiting for Approval, Fulfillment, Rejected, Closed) |
| `approval` | Approval state for this specific item |
| `requested_for` | The user this item is being fulfilled for |
| `assignment_group` | Inherited from catalog item or set by workflow |
| `assigned_to` | Can be set but rarely used directly on RITM |
| `quantity` | Number of units requested |
| `price` | Price per unit |
| `cat_item.delivery_time` | Expected fulfillment time |

### `sc_task` (Catalog Task — SCTASK)

The actual work units. These ARE assigned to individuals and groups and represent discrete fulfillment steps.

- **Number format:** SCTASK0001234
- **Assignment lives here** — the group and person doing the actual work
- Multiple sc_tasks can be created per RITM (sequential or parallel)
- A RITM closes when all its sc_tasks are closed

Key fields:
| Field | Description |
|-------|-------------|
| `request_item` | Reference to parent `sc_req_item` |
| `state` | Task state |
| `assignment_group` | Team performing this task |
| `assigned_to` | Individual performer |
| `short_description` | What needs to be done |
| `type` | Fulfillment, Information Required, etc. |

### Closure Cascade

```
SCTASK (closed) ──triggers──► RITM closes ──triggers──► REQ closes
```

All SCTASKs must be closed → RITM closes. All RITMs must be closed → REQ closes.

---

## Catalog Components

### Catalog Items (`sc_cat_item`)
The requestable services in the catalog. Examples:
- "Request a New Laptop"
- "Provision VPN Access"
- "New Employee Onboarding"
- "Request Leave of Absence" (HR)
- "Reset Active Directory Password"

Key configuration on a catalog item:
| Property | Description |
|----------|-------------|
| Name | Display name in the catalog |
| Short Description | Brief explanation shown in search results |
| Description | Full details (HTML-formatted) shown on item page |
| Category | Catalog category for navigation |
| Icon / Picture | Visual branding |
| Price | Optional cost shown to requester |
| Delivery Time | Estimated fulfillment time |
| Active | Whether item is visible in catalog |
| Available for | User criteria controlling who can see/request the item |
| Fulfillment group | Default assignment group for fulfillment tasks |
| Flow | Associated Flow Designer flow for fulfillment |

### Categories
Organize catalog items into logical groups:
- IT (Hardware, Software, Access, Network)
- HR (Benefits, Onboarding, Policies)
- Facilities (Workspace, Equipment)
- Security (Access Requests, Security Tools)

Categories can be nested (parent/child hierarchy).

### Variables
Variables are the form fields presented to the user when requesting a catalog item. They capture the information needed to fulfill the request.

| Variable Type | Description | Use Case |
|--------------|-------------|---------|
| Single Line Text | Free-form text input | Name, description fields |
| Multi Line Text | Textarea | Extended description, justification |
| Multiple Choice | Dropdown or radio buttons | Select from predefined options |
| Checkbox | Boolean true/false | Agree to terms, optional add-ons |
| Reference | Lookup to another table | Select a user, CI, location |
| Date | Date picker | Required-by date, start date |
| Date/Time | Date and time picker | Scheduled time slots |
| Email | Email address validation | Contact email |
| Lookup Multiple Choice | Dynamic choices from a table | Select multiple options |
| Table Name | Table selector | Advanced lookups |
| UI Page | Embedded custom page | Complex input scenarios |
| Masked | Password-style hidden input | Secrets (use sparingly) |

Variable configuration:
| Setting | Purpose |
|---------|---------|
| Order | Controls display sequence (lower = higher on form) |
| Mandatory | Whether field is required |
| Read only | Display-only (used in Order Guides for summary) |
| Show on summary | Whether to show in request summary email |
| Map to field | Directly populate a field on the RITM record |

### Variable Sets
Reusable groups of variables that can be applied to multiple catalog items:

- **Standard Variable Set:** Applied to multiple items — changes to the set propagate to all items
- **Single-use Variable Set:** Item-specific, not reused
- Common use cases: standard approval justification fields, shipping address fields, cost center allocation

### Record Producers
A special type of catalog item that creates a record in any ServiceNow table (not just sc_req_item). The form populates fields on the target record directly.

Example: An HR Record Producer that creates an `hr_case` record when an employee submits a policy question.

Key difference from regular catalog item:
- Creates a record in the target table
- User sees a regular catalog-style form
- No RITM is created — the target record IS the output

### Order Guides
Multi-item bundles that allow a single request to cover a set of related catalog items:

- User answers qualification questions
- Order Guide logic determines which items to include
- All items are added to the cart automatically
- Example: "New Employee Setup" includes laptop + software + network access + email

---

## Fulfillment Workflow

### Legacy Workflow Editor (Classic)
The original workflow-based approach uses the visual Workflow Editor with activities:
- Approval activities
- Notification activities
- Catalog Task generation activities
- Condition branches

Still supported but not recommended for new development.

### Flow Designer (Recommended)
Modern flows replace legacy workflows. Benefits:
- No-code/low-code visual editor
- Reusable subflows and actions
- Better performance and error handling
- Native integration with IntegrationHub

#### Fulfillment Flow Steps

Common steps in a catalog fulfillment flow:

1. **Trigger:** Service Catalog — RITM created or RITM state changed
2. **Approval step:** Ask for approval from manager or specific group
   - Approved → continue to fulfillment
   - Rejected → update RITM stage to Rejected, notify requester
3. **Create Catalog Task:** Create SCTASK assigned to fulfillment group
4. **Wait for condition:** Wait for SCTASK to close
5. **Notification:** Notify requester that request is fulfilled
6. **Close RITM:** Update RITM state to Closed Complete

#### Approval Logic in Flow

| Approval Type | How It Works |
|--------------|-------------|
| Manager Approval | Approval request sent to `requested_for.manager` |
| Group Approval | Approval request sent to all members of a specified group |
| User Approval | Approval request sent to a specific user by sys_id or criteria |
| Multi-level | Sequential approvals through multiple approvers/groups |
| Parallel | Multiple approvals can be completed in any order |

---

## Variables Storage

Variables entered by the user are stored in:
- `sc_item_option` — individual variable option records
- `sc_item_option_mtom` — many-to-many join between RITM and variable values

To read variable values in scripts:
```javascript
// In a flow or script accessing a RITM's variables
var ritm = new GlideRecord('sc_req_item');
ritm.get('sys_id_of_ritm');
// Access via the catalog item API
var value = ritm.variables.variable_name.getValue();
```

---

## RITM Stage Field

The `stage` field on `sc_req_item` provides a human-readable status for end users:

| Stage | Meaning |
|-------|---------|
| Waiting for Approval | Approval has been requested but not yet completed |
| Fulfillment | Approved and fulfillment tasks are in progress |
| Waiting for Delivery | Hardware order placed; waiting for physical delivery |
| Delivered | Delivered to the user |
| Rejected | Approval was denied |
| Closed | Request fulfilled and closed |
| Cancelled | Request was canceled before completion |

---

## Access Control: User Criteria

User Criteria (`user_criteria` table) controls who can see or request catalog items:

| Criterion Type | Condition |
|---------------|-----------|
| User | Specific users |
| Group | Members of specific groups |
| Role | Users with specific roles |
| Company | Users from specific companies |
| Location | Users at specific locations |
| Department | Users in specific departments |
| Script | Custom script returning true/false |

Multiple criteria can be combined with AND/OR logic. Items can have:
- **Available for:** Users who can see the item
- **Not available for:** Users explicitly excluded

---

## Best Practices

### Item Design
- Keep forms short — request only information that is genuinely needed for fulfillment
- Use reference fields for CIs, users, and locations rather than free-text — prevents typos and enables reporting
- Use order numbers (100, 200, 300...) with gaps to allow future insertions
- Group related variables with Variable Set Containers for visual clarity
- Test in impersonation mode as a non-admin user before going live

### Naming Conventions
- Catalog item names should be written from the user's perspective: "Request a New Laptop" not "Laptop Provisioning"
- Variable names (field names) should use snake_case: `requested_software`, `business_justification`
- Variable labels should be plain language: "Business Justification" not "justification_text"

### Performance
- Avoid reference variables with no filter — they cause slow form loads
- Add appropriate filters on reference variables (e.g., Active CIs only, Active Users only)
- Use `sc_variables` display rules to show/hide variables dynamically instead of creating multiple items for minor variations

### Governance
- Review catalog items annually for relevance — retire obsolete items
- Track fulfillment rates and average completion time per item
- Monitor rejection rates — high rejection suggests approval policy needs review
- Use catalog item ownership fields to assign accountability

### Multi-Fulfillment Group Items
For items requiring multiple teams (e.g., laptop provisioning requires Procurement + IT + Network):
1. Flow creates sequential catalog tasks for each team
2. Each team receives and completes their task before the next team is notified
3. Or parallel tasks if teams can work simultaneously

---

## Common Patterns

### Manager Approval Flow
```
RITM Created
  → Request approval from: requested_for.manager
  → If Approved:
      → Create SCTASK → Fulfillment Group
      → Wait for SCTASK closed
      → Notify requester: fulfilled
      → Close RITM
  → If Rejected:
      → Update RITM stage: Rejected
      → Notify requester: rejected with reason
      → Close RITM
```

### Hardware Order with Delivery
```
RITM Created
  → Manager Approval
  → Create SCTASK: Procurement (order hardware)
  → Update RITM stage: Waiting for Delivery
  → Wait for Procurement SCTASK closed
  → Create SCTASK: IT Setup (image and configure)
  → Wait for IT Setup SCTASK closed
  → Update RITM stage: Delivered
  → Notify requester
  → Close RITM
```

### Access Request with Justification Review
```
RITM Created
  → Security Team Approval (review justification variable)
  → If Approved:
      → Create SCTASK: Identity Team (provision access)
      → Set RITM variable: approved_access_level = requested_level
      → Wait for SCTASK
      → Close RITM
  → If Rejected:
      → Notify requester with rejection reason
      → Offer to submit an alternative access level request
      → Close RITM
```

---

## Metrics and Reporting

| Metric | Purpose |
|--------|---------|
| Mean Time to Fulfill | Average days from RITM creation to closure |
| Approval cycle time | Average time for approvals to complete |
| Rejection rate by item | Flags items with poorly calibrated approval criteria |
| Self-service adoption | % of requests submitted via catalog vs. phone/email |
| Catalog item usage | Most/least requested items — informs catalog curation |
| SLA compliance | % of RITMs fulfilled within delivery time commitment |
