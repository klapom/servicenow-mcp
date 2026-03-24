---
source_type: platform
topics:
  - import sets
  - transform maps
  - data import
  - staging tables
  - ETL
  - coalesce
  - data sources
  - scheduled imports
---

# Import Sets and Transform Maps

## Overview

Import Sets are ServiceNow's ETL (Extract, Transform, Load) framework for loading data from external sources into target tables. They use a staging architecture: raw data is first loaded into temporary staging (import set) tables, then transformed and inserted/updated into target tables via Transform Maps.

This staging approach provides data validation, transformation scripting, error handling, and audit trails for all data imports — far more control than direct table inserts via REST API.

---

## Architecture

### Three-Layer Design

```
External Source               Staging Table             Target Table
(CSV, JDBC, REST)  →  Import  →  (u_imp_servers)  →  Transform  →  (cmdb_ci_server)
                      Set API        staging                Map
```

1. **Data Source:** Where the data comes from (file, database, API, LDAP)
2. **Staging Table (Import Set Table):** Temporary holding area with auto-generated columns matching the source data structure
3. **Transform Map:** Definition of how staging columns map to target table fields

### Import Set Tables
- Named with prefix `u_imp_` by convention (though any name is valid)
- Columns are auto-generated when data is first loaded
- Each row in the staging table = one record from the source
- Rows have a `u_import_set` reference to the Import Set that loaded them
- Rows are NOT automatically cleaned up — must be maintained via scheduled purge

### Import Set Record
The `sys_import_set` record tracks a batch import:

| Field | Description |
|-------|-------------|
| `sys_id` | Unique identifier for this import batch |
| `label` | Description of the import |
| `table_name` | The staging table used |
| `state` | Running, Complete, Error |
| `import_source` | What triggered the import |
| `total_count` | Total rows in source |
| `error_count` | Rows that failed |
| `insert_count` | New records created in target |
| `update_count` | Existing records updated |
| `skip_count` | Rows skipped (no change needed) |

---

## Data Sources

### File Sources
- **CSV:** Comma/tab/semicolon delimited files
- **Excel:** XLS, XLSX spreadsheets
- **XML:** XML documents
- **JSON:** JSON arrays or objects
- Location: Local upload, FTP, SFTP, HTTP/HTTPS URL, SMB share

### Database Sources (JDBC)
Direct database connections to:
- Oracle, SQL Server, MySQL, PostgreSQL, DB2
- Connection via JDBC driver (loaded on MID Server)
- SQL query defines what data to retrieve

### LDAP
Directory services for user/group imports:
- Microsoft Active Directory
- OpenLDAP, Novell eDirectory
- Ports: 389 (LDAP), 636 (LDAPS)
- Used for HR feed and user provisioning

### REST and Data Stream
- IntegrationHub Data Stream action triggers REST calls
- Response data auto-loaded into staging table
- Supports pagination and authentication

### Custom (Scripted)
A script on the Data Source populates staging data programmatically:
```javascript
// Custom data source script
var gr = new GlideRecord('custom_staging_table');
// populate records from any source
```

---

## Transform Maps

### What Is a Transform Map?
A Transform Map defines the relationship between staging table fields and target table fields. It specifies:
- Which staging columns map to which target fields
- Transformation logic (direct copy, value conversion, script)
- Coalesce fields (for matching existing records)
- Event scripts for custom processing

### Transform Map Configuration

| Setting | Description |
|---------|-------------|
| Name | Descriptive name |
| Source table | Staging table |
| Target table | Where data is written |
| Run business rules | Whether to trigger BRs on inserted/updated records |
| Run script | Whether transform event scripts run |
| Copy empty fields | Whether null staging values overwrite target values |
| Order | When multiple maps exist, execution order |

### Field Maps

Each field in the transform map defines how one staging column maps to one target field:

| Setting | Description |
|---------|-------------|
| Source field | Staging table column |
| Target field | Target table field |
| Coalesce | Whether this field is used for record matching |
| Type | Auto (direct copy), Translate (value mapping), Use source script |
| Default value | Value to use if source is empty |
| Source script | JavaScript to transform the value |

### Source Script (Field-Level Transformation)
```javascript
// Field map source script: Transform staging status to target state integer
var statusMap = {
    'active': '1',
    'inactive': '2',
    'retired': '6'
};
answer = statusMap[source.status.toLowerCase()] || '1';
```

---

## Coalesce Fields

Coalesce determines whether an imported row should **create a new record** or **update an existing record** in the target table.

### Coalesce Types

| Type | How It Works |
|------|-------------|
| Single-field | Match target record where one field equals staging value |
| Multiple-field | ALL specified fields must match (AND condition) |
| Conditional (script) | Script returns `sys_id` of matching target record, or empty string for insert |

### Coalesce Behavior

| Matching Result | Action |
|----------------|--------|
| No match found | INSERT — create new record |
| One match found | UPDATE — update existing record |
| Multiple matches | Conflict — may insert duplicate or throw error (depends on configuration) |

### Coalesce Configuration on Field Map
Enable "Coalesce" on one or more field maps:

```
Staging field: u_serial_number → Target field: serial_number [Coalesce: Yes]
Staging field: u_hostname → Target field: name [Coalesce: No]
```
This means: "Find a cmdb_ci_server where serial_number = staging.u_serial_number; if found, update it; if not, create a new one."

### Coalesce Options

| Option | Description |
|--------|-------------|
| Coalesce empty fields | Allow null/empty staging values to match target records (risky) |
| Coalesce case-sensitive | Exact case match required (default: case-insensitive) |

---

## Transform Event Scripts

Transform event scripts provide hooks for custom logic at different stages of the transformation process:

### onStart
Runs once before any rows are processed:
```javascript
// Initialize logging or validate configuration
gs.info('Import {0} started. Processing {1} rows.',
    import_set.label, import_set.total_count);
// Can abort the entire import:
// error = true;
```

### onBefore
Runs before each row is transformed and written:
```javascript
// Skip rows where hostname is empty
if (gs.nil(source.u_hostname)) {
    ignore = true; // Skip this row
    gs.info('Skipping row — empty hostname');
    return;
}

// Validate IP address format
if (!/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(source.u_ip_address.toString())) {
    error = true;
    error_message = 'Invalid IP address: ' + source.u_ip_address;
    return;
}
```

### onAfter
Runs after each row has been saved to the target table:
```javascript
// After a CI is created/updated, set the managed_by_group
if (action == 'insert' || action == 'update') {
    var gr = new GlideRecord('cmdb_ci');
    if (gr.get(target.sys_id)) {
        // Set based on location
        if (target.location.name.toString().startsWith('US-')) {
            gr.managed_by_group.setDisplayValue('US Infrastructure Team');
        } else {
            gr.managed_by_group.setDisplayValue('EMEA Infrastructure Team');
        }
        gr.setWorkflow(false);
        gr.update();
    }
}
```

### onComplete
Runs once after all rows are processed:
```javascript
// Send completion notification
gs.info('Import complete. Inserted: {0}, Updated: {1}, Errors: {2}',
    import_set.insert_count, import_set.update_count, import_set.error_count);

if (parseInt(import_set.error_count) > 10) {
    gs.eventQueue('import.high_error_count', new GlideRecord('sys_import_set'),
        import_set.sys_id, import_set.error_count.toString());
}
```

### onForeignInsert
Runs before a new reference record is created during import. A reference field in the staging data may reference a value that doesn't exist yet in the target table:
```javascript
// Before creating a new department during import
// Validate department name format
if (source.u_department.toString().length < 3) {
    reject = true; // Don't create the reference record
    return;
}
```

### onChoiceCreate
Runs before a new choice value is created during import:
```javascript
// Before creating a new category value
// Only allow values from an approved list
var approved = ['hardware', 'software', 'network', 'security'];
if (approved.indexOf(source.u_category.toLowerCase()) === -1) {
    reject = true;
    error_message = 'Unknown category: ' + source.u_category;
}
```

### onReject
Runs when a foreign record or choice creation is rejected:
```javascript
// Log rejected references for follow-up
gs.warn('Rejected reference: {0} = {1} for import row {2}',
    source_field, source_value, source.sys_id);
```

### Available Script Variables

| Variable | Type | Description |
|----------|------|-------------|
| `source` | GlideRecord | The staging table row being processed |
| `target` | GlideRecord | The target record being created/updated |
| `import_set` | GlideRecord | The Import Set batch record |
| `map` | GlideRecord | The Transform Map record |
| `log` | Object | Logging utilities |
| `action` | String | 'insert', 'update', 'skip' |
| `ignore` | Boolean | Set to true to skip this row |
| `error` | Boolean | Set to true to mark row as error |
| `error_message` | String | Error description when error=true |
| `reject` | Boolean | (onForeignInsert/onChoiceCreate) Reject the creation |

---

## Scheduled Imports

Scheduled Imports automate recurring data loads at defined intervals.

**Navigation:** System Import Sets → Scheduled Imports

### Configuration

| Setting | Description |
|---------|-------------|
| Name | Import name |
| Data source | The Data Source record defining connection and query |
| Run | Daily / Weekly / Monthly / Periodically |
| Active | Enable/disable |
| Transform map | Which transform map to run after loading |
| Load attachments | Whether to process attachments |
| Email notifications | Who to notify on completion/error |

### Scheduled Import Execution Sequence
1. Load data from source into staging table
2. Create Import Set record
3. Run Transform Map(s) against all new staging rows
4. Generate import log with results
5. (Optional) Send completion notification

---

## Import Set REST API

External systems can push data directly to import set staging tables via REST:

**Endpoint:** `POST /api/now/import/{stagingTableName}`

**Body:** JSON object matching staging table column names
```json
{
    "u_hostname": "web-server-01",
    "u_ip_address": "10.0.1.100",
    "u_environment": "production",
    "u_os": "RHEL 8"
}
```

**Response:** Contains the transformation result:
```json
{
    "result": {
        "status": "updated",
        "sys_id": "abc123...",
        "table": "cmdb_ci_unix_server"
    }
}
```

The import and transformation run synchronously in response to the API call — the caller gets the result immediately.

---

## Error Handling and Logging

### Import Log
**Navigation:** System Import Sets → Import Log

Shows all rows processed, their outcome (inserted/updated/error/skipped), and error messages for failed rows.

### Script Logging in Transform Scripts
```javascript
log.info('Processing server: ' + source.u_hostname);
log.warn('Missing department for row: ' + source.sys_id);
log.error('Failed to map location: ' + source.u_location);
```

Log outputs are stored in the Import Log associated with the Import Set.

### Enable Table-Level Logging
System property: `glide.importlog.log_to_table = true`
Enables detailed logging of each import action to the `sys_impex_log` table.

### Error Flags
- `error = true` in transform scripts: marks the row as errored; transformation halts for that row
- `ignore = true` in onBefore: row is silently skipped (not counted as error)

---

## Robust Import Set Transformers

An advanced alternative to standard Transform Maps — separates the "reading" phase from the "writing" phase:
- A single staging row read can write to multiple target tables
- True ETL pipeline behavior
- Useful for complex integrations where one source record creates/updates multiple target records

---

## Best Practices

### Staging Table Management
- Clean up old staging table rows periodically (Scheduled Job)
- Index frequently-queried staging columns if running large imports regularly
- Do not manually add columns to staging tables — load data with the correct structure

### Transform Map Design
- Always use Coalesce to prevent duplicate records on re-import
- Document the coalesce logic clearly — it is the most critical design decision
- Test with a small data set before running against production volumes

### Error Handling
- Validate data in `onBefore` before attempting transformation
- Use `ignore = true` for expected empty/irrelevant rows, `error = true` for genuine data problems
- Monitor error rates — high error rates indicate data quality issues at the source

### Performance
- Use JDBC Data Sources for large database imports (more efficient than file-based)
- Limit staging table rows — don't accumulate years of historical staging data
- Run heavy imports during off-peak hours
- Set reasonable batch sizes for very large imports

---

## Common Patterns

### HR User Import (CSV from Active Directory Export)

Staging table: `u_imp_hr_users`
Transform map target: `sys_user`

Coalesce field: `employee_number`

Field maps:
| Staging | Target | Notes |
|---------|--------|-------|
| `u_emp_id` | `employee_number` | Coalesce field |
| `u_first_name` | `first_name` | Direct copy |
| `u_last_name` | `last_name` | Direct copy |
| `u_email` | `email` | Direct copy |
| `u_department` | `department` | Reference lookup by name |
| `u_location` | `location` | Reference lookup by name |
| `u_status` | `active` | onBefore: map 'active' → true, 'inactive' → false |

### CMDB Server Import (JDBC from SCCM)

Staging table: `u_imp_sccm_servers`
Transform map target: `cmdb_ci_win_server` or `cmdb_ci_unix_server`

Coalesce field: `serial_number`

onBefore script to determine OS class:
```javascript
if (/windows/i.test(source.u_operating_system.toString())) {
    target.sys_class_name = 'cmdb_ci_win_server';
} else {
    target.sys_class_name = 'cmdb_ci_unix_server';
}
```
