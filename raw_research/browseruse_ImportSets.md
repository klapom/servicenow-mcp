# ImportSets

Source: browser-use task ded75526-5605-437c-83b9-3bbba711c8af
Steps: 24 | Cost: $0.144 | Success: True

I have extracted comprehensive information regarding ServiceNow Import Sets and Transform Maps.

### 1. Import Set Architecture
- **Staging Tables:** Act as temporary holding areas for raw data. Fields are auto-generated based on input. Avoid manual modifications to columns.
- **Transform Maps:** Define relationships between staging table fields and target table fields.
- **Robust Import Set Transformers:** An alternative to transform maps that separates transformation and processing, allowing a single read operation to load data into multiple target tables (ETL functionality).

### 2. Data Sources
- **File:** Local or remote files.
- **JDBC:** Databases (Oracle, MySQL, SQL Server, etc.).
- **LDAP:** Directory services (Ports 389/636).
- **REST/Data Stream:** Integration Hub-based data retrieval.
- **Custom:** Data loaded via custom scripts.

### 3. Transform Map Scripts (Events)
- **onStart:** Runs before any rows are processed.
- **onBefore:** Runs before each row transformation; can skip rows using `ignore = true`.
- **onAfter:** Runs after a row is saved to the target table.
- **onForeignInsert:** Runs before a new referenced record is created.
- **onChoiceCreate:** Runs before a new choice value is created.
- **onReject:** Runs when a foreign record or choice creation is rejected.
- **onComplete:** Runs after all rows are processed.
- **Available Objects:** `source`, `target`, `import_set`, `map`, `log`, `action`, `ignore`, `error`.

### 4. Coalesce Fields and Matching
- **Purpose:** Determines if a record should be updated or a new one created.
- **Types:** 
  - *Single-field:* Matches one field.
  - *Multiple-field:* All specified fields must match.
  - *Conditional:* Scripted logic (returning `sys_id` of target).
- **Options:** 
  - *Coalesce empty fields:* Allows matching on null/empty values.
  - *Coalesce case sensitive:* Enforces exact case matching.

### 5. Scheduled Imports & Import Set API
- **Scheduled Imports:** Allow for recurring data loads at defined intervals.
- **Import Set API:** A REST API that allows external systems to post data directly to import set staging tables, triggering synchronous transformations.

### 6. Error Handling and Logs
- **Logging:** Use `log.info()`, `log.warn()`, or `log.error()` in scripts. Enable via `glide.importlog.log_to_table`.
- **Error Flags:** Setting `error = true` in event scripts can halt the transformation process.
