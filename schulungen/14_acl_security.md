---
source_type: platform
topics:
  - ACL
  - security
  - access control
  - roles
  - row-level security
  - elevated privileges
  - field security
---

# ACL Security

## Overview

Access Control Lists (ACLs) are ServiceNow's primary mechanism for controlling which users can perform which operations on which data. ACLs evaluate before any data is returned to the browser or API consumer, ensuring that security is enforced uniformly regardless of how data is accessed.

ServiceNow's security model is layered: **Roles** (broad permissions) → **ACLs** (granular table and field access) → **Before Query Business Rules** (row-level filtering). Understanding how these layers interact is essential for building secure applications.

---

## ACL Types

| Type | What It Controls |
|------|----------------|
| `record` (table) | Whether a user can read/write/create/delete records in a table |
| `field` | Whether a user can read/write a specific field |
| `client_callable_script_include` | Whether a user can call a specific client-callable Script Include via GlideAjax |
| `REST_endpoint` | Whether a user can access a specific Scripted REST API endpoint |

### Operation Types

Each ACL is defined for a specific **operation**:

| Operation | Meaning |
|-----------|---------|
| `read` | View a record or field in UI/API |
| `write` | Update an existing record or field |
| `create` | Insert a new record |
| `delete` | Delete a record |
| `execute` | Run a script include (client_callable) or access REST endpoint |
| `report_on` | Use the table/field in reports |
| `personalize_form` | Customize form view for the table |

---

## ACL Evaluation

ServiceNow evaluates ACLs following a strict precedence order:

### Evaluation Components (All Three Must Pass)
For access to be granted, ALL three conditions must evaluate to true:

1. **Roles check:** Does the user have any of the required roles?
2. **Conditions check:** Does the record/field meet the condition criteria?
3. **Script check:** Does the ACL script evaluate to true?

If any one of these fails, access is denied.

### Field/Table Specificity Order
ServiceNow finds the most specific matching ACL:

| Priority | ACL Pattern | Example |
|----------|------------|---------|
| 1 (most specific) | `table.field` | `incident.close_notes` |
| 2 | `parent_table.field` | `task.close_notes` |
| 3 | `*.field` | `*.close_notes` |
| 4 | `table.*` | `incident.*` |
| 5 | `parent_table.*` | `task.*` |
| 6 (least specific) | `*.*` | `*.*` (global fallback) |

If no ACL is found for an operation, the **default behavior** is controlled by system properties:
- `glide.security.use_default_deny`: If true, deny access when no ACL matches (secure-by-default)
- Default behavior without this property: access may be allowed if no ACL explicitly controls it

---

## Role Hierarchy

Roles can contain other roles. Assigning a parent role automatically grants all child role permissions.

### Common Role Hierarchy

```
admin
  └── security_admin (separate — requires elevation)
  └── itil_admin
        └── itil
              └── ITIL_template (base template role)

catalog_admin
  └── catalog_editor
        └── catalog

knowledge_admin
  └── knowledge_manager
        └── knowledge

asset
  └── asset_manager (extends asset)
```

### Key OOB Roles

| Role | Access Level |
|------|-------------|
| `admin` | Full system access; bypasses most ACLs |
| `security_admin` | Security administration; requires elevation |
| `itil` | Standard IT service management user |
| `itil_admin` | Extended ITIL management capabilities |
| `catalog_admin` | Service Catalog administration |
| `catalog_editor` | Edit catalog items; not full admin |
| `knowledge_admin` | Full Knowledge Management administration |
| `knowledge` | Create and edit KB articles |
| `report_admin` | Report administration |
| `report_group_admin` | Report group administration |
| `asset` | Asset Management read/write |
| `rest_api_explorer` | Access the REST API Explorer tool |
| `web_service_admin` | Manage web service configurations |

---

## Creating ACLs

### ACL Configuration Fields

| Field | Description |
|-------|-------------|
| Type | record, field, client_callable_script_include, REST_endpoint |
| Operation | read, write, create, delete, execute, report_on |
| Name | Table name or `*` |
| Field | Field name or `*` (for record-level), `none` (for row ACL) |
| Roles | Required roles (comma-separated; any role grants access) |
| Condition | Filter condition built with condition builder |
| Script | JavaScript returning true/false |
| Advanced | Enable scripted condition |
| Active | Enable/disable ACL |

### Row-Level ACL (Record without Specific Field)
To control whether a user can see a record at all (not just specific fields):
- Type: `record`
- Field: `-- None --`
- Operation: `read`

This is the record-level ACL. If denied, the user cannot see the record in lists or forms.

---

## ACL Script Examples

### Simple Role Check
```javascript
// ACL Script — return true if user has any valid role
answer = gs.hasRole('itil') || gs.hasRole('itil_admin');
```

### Context-Based Access
```javascript
// ACL Script on incident — user can read their own incidents
if (gs.hasRole('itil')) {
    answer = true; // ITIL users see everything
} else {
    // Callers can see their own incidents
    answer = (current.caller_id == gs.getUserID());
}
```

### Field-Level Access Based on Record State
```javascript
// ACL on incident.close_notes write operation
// Only allow editing resolution notes before closure
answer = gs.hasRole('itil') && (current.state != 7); // Not Closed
```

### Condition-Based (No Script)
Using the condition builder only (no script needed):
- Condition: `Assignment Group is [Network Operations] AND State is 2`
- Roles: `network_ops`
- This ACL allows network_ops users to write to incidents assigned to their group while In Progress

---

## Elevated Privileges

Certain sensitive roles require manual session elevation even when assigned to the user:

### security_admin
The `security_admin` role controls the most sensitive security settings (ACLs, roles, data policies). Even users with this role must explicitly elevate:

1. Click the user avatar or profile
2. Select "Elevate Role"
3. Enter multi-factor authentication (if configured)
4. Session is elevated for a configurable time period (default: 1 session or N minutes)

**Why:** Prevents accidental or unauthorized changes to security configuration during normal work sessions.

### admin Role Elevation
The `admin` role also has elevation behavior in high-security configurations. A common pattern is to have admin users with a "base" admin role that doesn't grant full administrative access until elevated.

---

## Row-Level Security

Row-level security prevents users from even seeing records they shouldn't access — different from field-level security (can see the record but not specific fields).

### Method 1: Record ACL with Script
```javascript
// ACL: incident, None (row-level), read operation
// ACL Script:
if (gs.hasRole('itil_admin')) {
    answer = true;
} else if (gs.hasRole('itil')) {
    // Standard agents can only see incidents in their assignment group(s)
    var userGroups = new GlideRecord('sys_user_grmember');
    userGroups.addQuery('user', gs.getUserID());
    userGroups.query();
    var groups = [];
    while (userGroups.next()) {
        groups.push(userGroups.getValue('group'));
    }
    answer = groups.indexOf(current.assignment_group.toString()) > -1;
} else {
    // End users can see their own incidents
    answer = current.getValue('caller_id') === gs.getUserID();
}
```

### Method 2: Before Query Business Rule
A Before Query Business Rule adds conditions to every database query on the table — effectively filtering data before it's retrieved:

```javascript
// Before Query Business Rule on 'incident' table
// Order: 100, When: Before Query
if (!gs.hasRole('itil_admin')) {
    if (gs.hasRole('itil')) {
        // Add group membership filter
        current.addQuery('assignment_group.sys_id', 'IN',
            gs.getUserGroups().join(','));
    } else {
        // End users see only their incidents
        current.addQuery('caller_id', gs.getUserID());
    }
}
```

**Before Query BR vs. ACL for row-level security:**
- Before Query BR: No "access denied" message — records simply don't appear
- ACL: User sees a "Security restriction" message for denied records
- Before Query BR: Better performance for large tables (filters at query time)
- ACL: More declarative and auditable

---

## ACL Debugging

### Debug Security
Navigate to System Diagnostics → Session Debug → Debug Security:
- Activates verbose ACL evaluation logging in the browser
- Shows each ACL that was evaluated, whether it passed/failed, and why

### Check ACLs for a Record
From any record form: right-click title bar → Security → Show Security

This shows all ACLs that applied to the current record and their pass/fail results.

### Script Debugger for ACL Scripts
Breakpoints can be set in ACL scripts using the Script Debugger for step-by-step debugging.

---

## Data Policies vs. ACLs

Data Policies are a different security mechanism that enforces mandatory and read-only constraints at the server side — they apply to all access methods (UI, API, import sets), unlike UI Policies which are client-side only.

| Feature | Data Policy | ACL |
|---------|------------|-----|
| Purpose | Field mandatory/read-only constraints | Access control (read/write/create/delete) |
| Scope | All access methods | All access methods |
| Configurability | No-code condition builder | Roles + conditions + scripts |
| Performance | Light | Moderate (script evaluation) |

---

## Best Practices

### Least Privilege Principle
- Grant users the minimum roles required for their job function
- Avoid assigning `admin` role to service accounts used for integrations
- Create custom roles for specific functional areas rather than granting broad roles

### ACL Design
- Define ACLs at the most specific level possible (table.field > table.* > *.*)
- Document the business reason for each ACL in the description field
- Test ACLs with impersonation — impersonate different user types to verify behavior

### Avoiding ACL Gaps
- Run security checks after every major deployment that adds new tables or fields
- New custom tables should have ACLs created explicitly — don't rely on inherited `*.*` ACLs
- Use `glide.security.use_default_deny = true` for high-security instances

### Role Naming Conventions
- Custom roles: `{app_prefix}_{function}` (e.g., `myapp_read`, `myapp_admin`)
- Document role purpose and what access it grants
- Use role descriptions in the role record

### Audit and Compliance
- `sys_user_role` table: All role assignments (who has what role)
- `sys_security_acl` table: All ACL definitions (what controls exist)
- `syslog_transaction` table: Transaction-level security evaluations (can be verbose)
- Enable transaction logging for sensitive tables to track access patterns

---

## Common Patterns

### Manager Can See Team's Incidents Only

```javascript
// ACL Script on incident (row-level read)
if (gs.hasRole('itil_admin')) {
    answer = true;
    return;
}

// Group managers can see incidents assigned to their group
var mgr = new GlideRecord('sys_user_group');
mgr.addQuery('manager', gs.getUserID());
mgr.query();
var managedGroups = [];
while (mgr.next()) {
    managedGroups.push(mgr.sys_id.toString());
}

// Also include groups the user is a member of
var membership = new GlideRecord('sys_user_grmember');
membership.addQuery('user', gs.getUserID());
membership.query();
while (membership.next()) {
    managedGroups.push(membership.getValue('group'));
}

answer = managedGroups.indexOf(current.assignment_group.toString()) > -1;
```

### Field Protected by Classification

```javascript
// ACL on change_request.backout_plan (write) — only change coordinator/manager can edit
answer = gs.hasRole('change_coordinator') ||
         gs.hasRole('change_manager') ||
         current.assignment_group.manager.toString() === gs.getUserID();
```

### Service Account Limited to Specific Tables

Create a custom role `api_incident_writer`:
- Assign ACL: `incident` — create, write — role: `api_incident_writer`
- Do NOT grant `itil` (gives too much access)
- Service account gets only `api_incident_writer` role
- Result: Service account can create and update incidents, nothing else
