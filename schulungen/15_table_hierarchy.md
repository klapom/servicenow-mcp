---
source_type: platform
topics:
  - table hierarchy
  - table inheritance
  - task table
  - sys_db_object
  - sys_dictionary
  - dot-walking
  - table extension
---

# Table Hierarchy

## Overview

ServiceNow uses an object-oriented table inheritance model. Tables can extend other tables, inheriting all parent fields while adding their own. This design is central to how the platform works — understanding it enables efficient querying, report building, scripting, and customization.

The `task` table is the most important base table in the ITSM context: incidents, problems, change requests, catalog items, and dozens of other records all extend it, meaning they share common fields and behaviors.

---

## Table Inheritance Model

### Table Per Class (TPC)
ServiceNow uses the **Table Per Class** model:
- Each table in the hierarchy has its own physical database table
- The child table stores only fields unique to it
- When querying a child table, the database performs a JOIN with all ancestor tables
- All inherited fields are fully accessible and indexed

**Example:**
```
Database tables:
  task          — stores: number, state, priority, short_description, ...
  incident      — stores: caller_id, category, subcategory, close_code, ...

Query: SELECT * FROM incident
Actually: JOIN incident with task to get all fields
```

### Table Per Hierarchy (TPH) — "Flattening"
Some ServiceNow tables use TPH where the entire hierarchy is stored in a single physical table:
- All fields from all classes in one large table
- Better performance for cross-hierarchy queries (no JOIN required)
- Has column limits (ServiceNow has a per-table column cap)
- `cmdb_ci` base hierarchy uses TPH for performance reasons

---

## The Task Table

`task` is the root base table for all work items in ServiceNow. Any table that extends `task` inherits:

### Inherited Fields from `task`

| Field Name | Type | Description |
|-----------|------|-------------|
| `number` | String | Auto-generated record number (e.g., INC, CHG, PRB) |
| `short_description` | String | Brief summary |
| `description` | Text | Full detailed description |
| `state` | Integer (choice) | Lifecycle state |
| `priority` | Integer (choice) | Business priority |
| `impact` | Integer (choice) | Business impact level |
| `urgency` | Integer (choice) | Time sensitivity |
| `work_notes` | Journal | Internal notes (not visible to callers) |
| `comments` | Journal | Customer-visible notes |
| `activity_due` | DateTime | When next activity is due |
| `assignment_group` | Reference → sys_user_group | Team responsible |
| `assigned_to` | Reference → sys_user | Individual assigned |
| `opened_at` | DateTime | When task was created |
| `opened_by` | Reference → sys_user | Who created the task |
| `closed_at` | DateTime | When task was closed |
| `closed_by` | Reference → sys_user | Who closed the task |
| `sys_created_on` | DateTime | System creation timestamp |
| `sys_updated_on` | DateTime | Last updated timestamp |
| `sys_created_by` | String | User who created record |
| `sys_updated_by` | String | User who last updated record |
| `watch_list` | List → sys_user | Users receiving notifications |
| `work_notes_list` | List → sys_user | Users copied on work notes |
| `knowledge` | Boolean | Flag to create KB article |
| `upon_approval` | String (choice) | Action on approval |
| `upon_reject` | String (choice) | Action on rejection |
| `approval` | String (choice) | Approval state |
| `approval_set` | DateTime | When approval was set |
| `sla_due` | DateTime | SLA due date (displayed to users) |
| `time_worked` | Duration | Time spent on the task |
| `parent` | Reference → task | Parent task (for sub-tasks) |
| `made_sla` | Boolean | Whether SLA was met |
| `follow_up` | DateTime | Follow-up reminder date |
| `contact_type` | String (choice) | How was task initiated |
| `company` | Reference → core_company | Company/customer |
| `location` | Reference → cmn_location | Location |
| `sys_domain` | Reference → sys_user_list | Domain (for multi-tenant) |

### Tables That Extend `task`

| Table | Label | Number Prefix |
|-------|-------|--------------|
| `incident` | Incident | INC |
| `problem` | Problem | PRB |
| `change_request` | Change Request | CHG |
| `change_task` | Change Task | CTASK |
| `sc_request` | Request | REQ |
| `sc_req_item` | Requested Item | RITM |
| `sc_task` | Catalog Task | SCTASK |
| `hr_case` | HR Case | HR |
| `sn_hr_case` | HR Service Delivery Case | HR |
| `vtb_card` | Visual Task Board Card | (none) |
| `kb_submission` | Knowledge Submission | (none) |
| `pm_project_task` | Project Task | (project-based) |
| `planned_task` | Planned Task | (project/plan) |
| `incident_task` | Incident Task | (subtask of incident) |
| `cert_follow_on_task` | Follow-On Task | (certification) |

---

## Key System Tables

### `sys_db_object` — Table Registry
Contains one record for every table in the instance.

| Field | Description |
|-------|-------------|
| `name` | Table name (e.g., `incident`) |
| `label` | Display label (e.g., `Incident`) |
| `super_class` | Reference to parent table's `sys_db_object` record |
| `is_extendable` | Whether this table can be extended |
| `access` | Table access setting |
| `number_ref` | Reference to auto-number configuration |
| `sys_scope` | Application scope that owns the table |

**Usage:** Query `sys_db_object` to discover all tables, their hierarchy, and scope ownership.

### `sys_dictionary` — Field Registry
Contains one record for every field on every table.

| Field | Description |
|-------|-------------|
| `name` | Table name this definition belongs to |
| `element` | Field name (e.g., `short_description`) |
| `column_label` | Display label |
| `internal_type` | Data type (string, integer, reference, boolean, etc.) |
| `max_length` | Maximum field length |
| `default_value` | Default value for new records |
| `mandatory` | Whether field is required |
| `active` | Whether field is active |
| `reference` | For reference fields: the target table |

**Dictionary Override:** Child tables can override parent field properties (label, mandatory, default value) without creating a new field. This is done via a Dictionary Override record (`sys_dictionary` entry for the child table that references the parent field).

---

## Field Inheritance

When a table extends a parent, all parent fields are automatically available:

```
task.short_description  ← defined on task
incident.short_description  ← inherited from task (no duplicate definition needed)
incident.caller_id  ← defined on incident only
```

### Dot-Walking
Dot-walking traverses reference field relationships to access fields on related tables:

```javascript
// Access caller's manager's email via the incident record
var managerEmail = current.caller_id.manager.email;  // incident → user → user → field

// In GlideRecord
var gr = new GlideRecord('incident');
gr.query();
while (gr.next()) {
    var callerDept = gr.caller_id.department.name.toString();  // 3 levels deep
    var assigneeEmail = gr.assigned_to.email.toString();       // 2 levels deep
}
```

### Dot-Walking in Queries
```javascript
var gr = new GlideRecord('incident');
// Find incidents where caller's department is IT
gr.addQuery('caller_id.department.name', 'Information Technology');
// Find incidents where assignee's manager is a specific person
gr.addQuery('assigned_to.manager', managerSysId);
gr.query();
```

### Dot-Walking in Encoded Queries (URL/Reports)
```
caller_id.department=sys_id_of_department
assigned_to.manager.department.name=IT
```

**Performance caution:** Deep dot-walking (3+ levels) in queries can be slow on large tables. Add appropriate indexes or denormalize data if performance is critical.

---

## Many-to-Many Relationships

When a table needs a many-to-many relationship with another table, a junction (m2m) table is used.

### Example: Incident ↔ Problem

| Junction Table | Parent | Child |
|---------------|--------|-------|
| `task_rel_task` | `task` (parent) | `task` (child) |
| `problem_task` | `problem` | `incident` |
| `sc_item_option_mtom` | `sc_req_item` | `sc_item_option` |
| `sys_user_grmember` | `sys_user_group` | `sys_user` |
| `sys_user_has_role` | `sys_user` | `sys_user_role` |

### Querying via Junction Table
```javascript
// Find all incidents linked to a specific problem
var gr = new GlideRecord('problem_task');
gr.addQuery('problem', problemSysId);
gr.query();
while (gr.next()) {
    var incidentNum = gr.related_task.number.toString();
    gs.info('Linked incident: ' + incidentNum);
}
```

---

## Other Important Base Tables

### `sys_user` — User Table
The central user directory. All platform users have a record here.

| Key Field | Description |
|-----------|-------------|
| `user_name` | Login username |
| `email` | Email address |
| `first_name`, `last_name` | Name |
| `manager` | Reference to sys_user (reporting manager) |
| `department` | Reference to cmn_department |
| `company` | Reference to core_company |
| `location` | Reference to cmn_location |
| `time_zone` | User's timezone |
| `active` | Account status |
| `vip` | VIP flag |
| `sys_roles` | Comma-separated roles (denormalized) |

### `sys_user_group` — Group Table
Teams, assignment groups, and approval groups.

| Key Field | Description |
|-----------|-------------|
| `name` | Group name |
| `manager` | Reference to sys_user (group manager) |
| `email` | Group email address |
| `parent` | Reference to parent group (for hierarchy) |
| `type` | Group type classification |
| `active` | Active status |

### `core_company` — Company Table
Vendors, customers, and internal organizations.

### `cmn_location` — Location Table
Physical and logical locations, organized hierarchically (country → city → building → floor).

### `cmn_department` — Department Table
Organizational departments, with parent-child hierarchy.

### `sys_choice` — Choice Lists
All dropdown/choice field options stored here. Fields: `name` (table), `element` (field), `value` (stored value), `label` (display text), `sequence` (order).

---

## Custom Tables and Extensions

### Creating a Custom Extension of Task
When building a custom case management table:
1. Navigate to System Definition → Tables → New
2. Set `Extends table = task`
3. ServiceNow creates the table and inherits all task fields
4. Add custom fields unique to the new table
5. Auto-numbering is configured separately (Administration → Number Maintenance)
6. Forms and views are inherited from task and can be customized

### When to Extend vs. When to Create a Fresh Table
| Extend `task` | Create Fresh Table |
|--------------|-------------------|
| Work items with assignment, state, SLA | Reference/lookup data (categories, products) |
| Needs work notes/comments | Configuration records |
| Benefits from task-based workflows | Simple data stores |
| Needs SLA, approval, notifications | No lifecycle management needed |

---

## Performance Implications

### Index Strategy
- Foreign key fields used in frequent queries should be indexed
- `sys_id` is always indexed
- Inherited fields from `task` are indexed at the task table level
- Custom fields added to child tables may need explicit indexes

### Column Limits
- ServiceNow has a per-table column limit (~500-600 fields depending on type)
- Extending task adds ~100+ inherited columns
- Plan custom field additions carefully; avoid broad "catch-all" tables

### Query Performance
- Queries against child tables (e.g., `incident`) JOIN with `task` — two table reads
- Tables using TPH (like CMDB) avoid this JOIN but have wider rows
- `sys_class_name` field filters queries to the correct class in TPH tables

---

## Common Patterns

### Finding All Tables That Extend Task
```javascript
var gr = new GlideRecord('sys_db_object');
gr.addQuery('super_class.name', 'task'); // Direct children only
gr.query();
while (gr.next()) {
    gs.info(gr.name + ' — ' + gr.label);
}
```

### Querying Across the Task Hierarchy
```javascript
// Find all task-based records assigned to a user, regardless of type
var gr = new GlideRecord('task');
gr.addQuery('assigned_to', targetUserSysId);
gr.addQuery('state', 'IN', '1,2,3'); // Active states
gr.query();
while (gr.next()) {
    gs.info('{0} ({1}): {2}', gr.number, gr.sys_class_name, gr.short_description);
    // sys_class_name tells you what type: incident, change_request, etc.
}
```

### Dictionary Override for Label Change
When a child table needs a different field label than the parent:
1. Navigate to System Definition → Dictionary
2. Find the field on the child table (not parent)
3. If no override exists, create one: same table/element, change only the label
4. Overrides are stored in `sys_dictionary` with the child table name
