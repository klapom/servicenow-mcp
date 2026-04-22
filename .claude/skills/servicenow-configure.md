---
name: servicenow-configure
description: Configure a ServiceNow instance for the FNT Command integration (PHOENIX project). Creates custom fields, business rules, scheduled jobs, REST messages, and OAuth credentials based on the Implementation Handbook. Every step checks for existing artifacts before creating.
---

## How to use

- The user invokes this with `/servicenow-configure`
- Read `.env` from the project root for credentials
- All API calls go to `{SERVICENOW_INSTANCE_URL}/api/now/table/{table_name}`
- Auth: Basic auth with username:password base64 encoded, or Bearer token depending on `SERVICENOW_AUTH_TYPE`
- Headers: `Accept: application/json`, `Content-Type: application/json`
- Use Python `requests` library directly via the Bash tool running `python3 -c` scripts
- **CRITICAL: Every step MUST check if the artifact already exists before creating it**
- At the end, print a summary table showing what was created vs skipped

## Idempotent Execution Pattern

EVERY create operation must follow this exact pattern:

```python
import requests, base64, json, os
from dotenv import load_dotenv
load_dotenv()

# Resolve target instance from SERVICENOW_TARGET (DEV or TEST)
target = os.getenv('SERVICENOW_TARGET', 'DEV').upper()
SN_URL  = os.getenv(f'SN_{target}_INSTANCE_URL')
SN_USER = os.getenv(f'SN_{target}_USERNAME')
SN_PWD  = os.getenv(f'SN_{target}_PASSWORD')
if not SN_URL or not SN_USER or not SN_PWD:
    raise SystemExit(f"Missing credentials for target '{target}'. Check .env SN_{target}_* variables.")
print(f"Target: {target} ({SN_URL})")
auth = base64.b64encode(f"{SN_USER}:{SN_PWD}".encode()).decode()
H = {"Authorization": f"Basic {auth}", "Accept": "application/json", "Content-Type": "application/json"}

def check_exists(table, query):
    """Check if a record exists. Returns the record if found, None otherwise."""
    r = requests.get(f"{SN_URL}/api/now/table/{table}",
        params={"sysparm_query": query, "sysparm_limit": "1", "sysparm_fields": "sys_id,name"},
        headers=H, timeout=30)
    r.raise_for_status()
    results = r.json().get("result", [])
    return results[0] if results else None

def create_record(table, data, label):
    """Create a record. Returns (status, sys_id_or_error)."""
    r = requests.post(f"{SN_URL}/api/now/table/{table}", json=data, headers=H, timeout=30)
    if r.status_code in (200, 201):
        sid = r.json().get("result", {}).get("sys_id", "?")
        print(f"  CREATED: {label} -> sys_id={sid}")
        return "created", sid
    else:
        print(f"  ERROR:   {label} -> HTTP {r.status_code}: {r.text[:200]}")
        return "error", r.text[:200]

results = []  # collect (step, name, status) tuples
```

## Configuration Steps

Execute all steps sequentially (Step 0 first, then 1–6). Each step is a self-contained Python script. Track results and print a summary at the end.

### Step 0: Create and Activate Update Set

All configuration changes must be tracked in a dedicated Update Set. Create one if it doesn't exist, then set it as "Current" for the API user's session.

```
Check:  GET /api/now/table/sys_update_set?sysparm_query=name=PHOENIX FNT Integration v1.0^state=in progress&sysparm_limit=1
Create: POST /api/now/table/sys_update_set
```

```json
{
  "name": "PHOENIX FNT Integration v1.0",
  "description": "Custom fields, business rules, script includes, REST messages, OAuth credentials, and scheduled jobs for the FNT Command integration (Option C — Pragmatic Interface)",
  "state": "in progress",
  "application": "global"
}
```

After creating (or finding the existing Update Set), set it as "Current" for the session by **including the Update Set sys_id in every subsequent API call** via the header:

```
X-UserToken: <update_set_sys_id>
```

Alternatively, set the user preference for the current update set:
```
PATCH /api/now/table/sys_update_set/<sys_id>
{"state": "in progress"}
```

And include this header on all subsequent POST/PATCH calls:
```
X-sn-update-set: <update_set_sys_id>
```

**IMPORTANT:** Every subsequent step (1–6) must include the `X-sn-update-set` header in all POST and PATCH requests so that all created artifacts are captured in this Update Set.

### Step 1: Create Custom Fields on cmdb_ci

For EACH field, check existence FIRST:
```
Check:  GET /api/now/table/sys_dictionary?sysparm_query=name=cmdb_ci^element={column_name}&sysparm_limit=1
Create: POST /api/now/table/sys_dictionary
```

Fields to create on table `cmdb_ci`:

| column_name        | internal_type | max_length | column_label       | mandatory | read_only |
|--------------------|---------------|------------|--------------------|-----------|-----------|
| u_fnt_elid         | string        | 14         | FNT ELID           | false     | false     |
| u_fnt_arrival_date | glide_date    |            | FNT Arrival Date   | false     | false     |
| u_fnt_campus       | string        | 100        | FNT Campus         | false     | false     |
| u_fnt_gebaeude     | string        | 100        | FNT Gebaeude       | false     | false     |
| u_fnt_rack_units   | integer       |            | FNT Rack Units     | false     | false     |
| u_fnt_link         | url           | 255        | FNT Link           | false     | false     |

POST payload per field:
```json
{
  "name": "cmdb_ci",
  "element": "<column_name>",
  "column_label": "<column_label>",
  "internal_type": "<internal_type>",
  "max_length": "<max_length>",
  "mandatory": "false",
  "read_only": "false",
  "active": "true"
}
```

All fields go on `cmdb_ci` (base table) — NOT on child tables. This makes them available for all CI classes (Phase 1: Rack, Server, Chassis; future Phase 2/3 without schema changes).

### Step 2: Create Business Rules on cmdb_ci

For EACH rule, check existence FIRST:
```
Check:  GET /api/now/table/sys_script?sysparm_query=name={rule_name}^collection=cmdb_ci&sysparm_limit=1
Create: POST /api/now/table/sys_script
```

#### Rule 1: FNT Outbound Sync
```json
{
  "name": "FNT Outbound Sync",
  "collection": "cmdb_ci",
  "when": "after",
  "action_insert": "false",
  "action_update": "true",
  "action_delete": "false",
  "action_query": "false",
  "order": "200",
  "active": "true",
  "comments": "Handbook 3.1: Fires on update of bidirectional/ToFNT fields. Builds delta payload and calls FNT Command REST Message.",
  "script": "// FNT Outbound Sync — fires on CI update\n// Check if any mapped bidirectional or ToFNT field changed\nvar mappedFields = ['serial_number','short_description','ip_address','u_fnt_arrival_date','warranty_expiration'];\nvar changed = [];\nmappedFields.forEach(function(f) {\n  if (current[f].changes()) changed.push(f);\n});\nif (changed.length === 0) return; // no mapped field changed\n\n// Build delta payload\nvar delta = {sn_source_timestamp: new GlideDateTime().getValue()};\nchanged.forEach(function(f) { delta[f] = current.getValue(f); });\n\n// Call FNT Command REST Message\ntry {\n  var sm = new sn_ws.RESTMessageV2('FNT Command API', 'Update CI');\n  sm.setStringParameterNoEscape('elid', current.getValue('u_fnt_elid'));\n  sm.setRequestBody(JSON.stringify(delta));\n  var response = sm.execute();\n  var httpStatus = response.getStatusCode();\n  if (httpStatus >= 400 && httpStatus < 500) {\n    gs.error('[FNT Outbound] 4xx from FNT for ELID=' + current.u_fnt_elid + ' HTTP=' + httpStatus);\n  } else if (httpStatus >= 500) {\n    gs.warn('[FNT Outbound] 5xx from FNT for ELID=' + current.u_fnt_elid + ', will retry via scheduled job');\n  }\n} catch(e) {\n  gs.error('[FNT Outbound] Exception: ' + e.message);\n}"
}
```

#### Rule 2: FNT Timestamp Check (Last-Write-Wins)
```json
{
  "name": "FNT Timestamp Check",
  "collection": "cmdb_ci",
  "when": "before",
  "action_insert": "false",
  "action_update": "true",
  "action_delete": "false",
  "action_query": "false",
  "order": "50",
  "active": "true",
  "comments": "Handbook 2.2: Compares fnt_source_timestamp vs sys_updated_on. Rejects stale updates.",
  "script": "// FNT Timestamp Check — Last-Write-Wins\nvar inboundTs = current.getValue('fnt_source_timestamp');\nif (!inboundTs) return; // no FNT timestamp = not an FNT-initiated update\n\nvar sysUpdated = current.sys_updated_on.getGlideObject();\nvar fntTs = new GlideDateTime(inboundTs);\n\nif (fntTs.before(sysUpdated)) {\n  gs.warn('[FNT LWW] Rejecting stale update for CI ' + current.sys_id + ': FNT timestamp ' + inboundTs + ' is older than sys_updated_on ' + current.sys_updated_on);\n  current.setAbortAction(true);\n}"
}
```

#### Rule 3: FNT Idempotency Check
```json
{
  "name": "FNT Idempotency Check",
  "collection": "cmdb_ci",
  "when": "before",
  "action_insert": "true",
  "action_update": "false",
  "action_delete": "false",
  "action_query": "false",
  "order": "10",
  "active": "true",
  "comments": "Handbook 7.1: Checks X-Idempotency-Key header to prevent duplicate CREATEs.",
  "script": "// FNT Idempotency Check — prevent duplicate CREATE\nvar idempKey = gs.getSession().getProperty('X-Idempotency-Key') || '';\nif (!idempKey) return;\n\n// Check if ELID already exists\nvar gr = new GlideRecord('cmdb_ci');\ngr.addQuery('u_fnt_elid', current.getValue('u_fnt_elid'));\ngr.setLimit(1);\ngr.query();\nif (gr.next()) {\n  gs.warn('[FNT Idempotency] Duplicate CREATE detected for ELID=' + current.u_fnt_elid + ', existing sys_id=' + gr.sys_id);\n  current.setAbortAction(true);\n}"
}
```

### Step 3: Create Script Includes

For EACH script include, check existence FIRST:
```
Check:  GET /api/now/table/sys_script_include?sysparm_query=name={script_name}&sysparm_limit=1
Create: POST /api/now/table/sys_script_include
```

#### FNTCIClassDeriver
```json
{
  "name": "FNTCIClassDeriver",
  "api_name": "global.FNTCIClassDeriver",
  "client_callable": "false",
  "active": "true",
  "description": "Handbook 4.2: Derives SN CI class from FNT FUNCTION, CONFIG_TABLE_NAME, IS_CARD",
  "script": "var FNTCIClassDeriver = Class.create();\nFNTCIClassDeriver.prototype = {\n  initialize: function() {},\n  deriveCIClass: function(FUNCTION, CONFIG_TABLE_NAME, IS_CARD) {\n    if (CONFIG_TABLE_NAME === 'Chassis' && FUNCTION === 'Server')\n      return 'cmdb_ci_chassis_server';\n    if (CONFIG_TABLE_NAME === 'Server' && FUNCTION === 'Server' && IS_CARD === 'Y')\n      return 'cmdb_ci_server'; // Blade\n    if (CONFIG_TABLE_NAME === 'Server' && FUNCTION === 'Server' && IS_CARD === 'N')\n      return 'cmdb_ci_server'; // Rack Server\n    if (FUNCTION === 'Schaltschrank')\n      return 'cmdb_ci_rack';\n    gs.warn('[FNTCIClassDeriver] Unknown type: FUNCTION=' + FUNCTION + ' TABLE=' + CONFIG_TABLE_NAME + ' IS_CARD=' + IS_CARD);\n    return null;\n  },\n  type: 'FNTCIClassDeriver'\n};"
}
```

#### FNTFieldMapper
```json
{
  "name": "FNTFieldMapper",
  "api_name": "global.FNTFieldMapper",
  "client_callable": "false",
  "active": "true",
  "description": "Handbook 3.7: Maps SN fields to FNT attributes with sync direction",
  "script": "var FNTFieldMapper = Class.create();\nFNTFieldMapper.prototype = {\n  initialize: function() {\n    this.mappings = [\n      {sn: 'name',                fnt: 'VISIBLE_ID',    direction: 'bidirectional'},\n      {sn: 'serial_number',       fnt: 'SERIAL_NO',     direction: 'bidirectional'},\n      {sn: 'short_description',   fnt: 'REMARK',        direction: 'bidirectional'},\n      {sn: 'ip_address',          fnt: 'IP_ADDRESS',    direction: 'bidirectional'},\n      {sn: 'u_fnt_arrival_date',  fnt: 'SUPPLY_DATE',   direction: 'bidirectional'},\n      {sn: 'warranty_expiration', fnt: 'WARRANTY_UNTIL', direction: 'bidirectional'},\n      {sn: 'u_fnt_campus',        fnt: 'NAME_CAMPUS',   direction: 'toSN'},\n      {sn: 'u_fnt_gebaeude',      fnt: 'NAME_GEBAEUDE', direction: 'toSN'},\n      {sn: 'u_fnt_rack_units',    fnt: 'HEIGHT_UNIT',   direction: 'toSN'},\n      {sn: 'u_fnt_elid',          fnt: 'ELID',          direction: 'toSN'},\n      {sn: 'sys_id',              fnt: 'SN_ID',         direction: 'toFNT'}\n    ];\n  },\n  getOutboundFields: function() {\n    return this.mappings.filter(function(m) {\n      return m.direction === 'bidirectional' || m.direction === 'toFNT';\n    });\n  },\n  getInboundFields: function() {\n    return this.mappings.filter(function(m) {\n      return m.direction === 'bidirectional' || m.direction === 'toSN';\n    });\n  },\n  snToFnt: function(snField) {\n    var match = this.mappings.filter(function(m) { return m.sn === snField; });\n    return match.length > 0 ? match[0].fnt : null;\n  },\n  fntToSn: function(fntField) {\n    var match = this.mappings.filter(function(m) { return m.fnt === fntField; });\n    return match.length > 0 ? match[0].sn : null;\n  },\n  type: 'FNTFieldMapper'\n};"
}
```

### Step 4: Create REST Message for FNT Command

Check and create the REST Message:
```
Check:  GET /api/now/table/sys_rest_message?sysparm_query=name=FNT Command API&sysparm_limit=1
Create: POST /api/now/table/sys_rest_message
```

```json
{
  "name": "FNT Command API",
  "rest_endpoint": "${FNT_BASE_URL}",
  "authentication_type": "oauth2",
  "description": "Outbound REST integration to FNT Command (PHOENIX project)"
}
```

After creating, retrieve the sys_id and create HTTP Methods:
```
Check:  GET /api/now/table/sys_rest_message_fn?sysparm_query=rest_message={rest_msg_sys_id}^function_name={method_name}&sysparm_limit=1
Create: POST /api/now/table/sys_rest_message_fn
```

| function_name | http_method | rest_endpoint                               |
|---------------|-------------|---------------------------------------------|
| Update CI     | PATCH       | ${FNT_BASE_URL}/api/v1/objects/${elid}      |
| Get Products  | GET         | ${FNT_BASE_URL}/api/v1/products             |
| Get Objects   | GET         | ${FNT_BASE_URL}/api/v1/objects              |
| Get Relations | GET         | ${FNT_BASE_URL}/api/v1/relations            |

Each method POST payload:
```json
{
  "rest_message": "<REST_MESSAGE_SYS_ID>",
  "function_name": "<method_name>",
  "http_method": "<http_method>",
  "rest_endpoint": "<endpoint>"
}
```

### Step 5: Create OAuth Entity for FNT

```
Check:  GET /api/now/table/oauth_entity?sysparm_query=name=FNT Command OAuth&sysparm_limit=1
Create: POST /api/now/table/oauth_entity
```

```json
{
  "name": "FNT Command OAuth",
  "client_id": "<from .env FNT_CLIENT_ID or placeholder>",
  "client_secret": "<from .env FNT_CLIENT_SECRET or placeholder>",
  "token_url": "${FNT_BASE_URL}/api/oauth/token",
  "default_grant_type": "client_credentials",
  "active": "true"
}
```

### Step 6: Create Scheduled Jobs

For EACH job, check existence FIRST:
```
Check:  GET /api/now/table/sysauto_script?sysparm_query=name={job_name}&sysparm_limit=1
Create: POST /api/now/table/sysauto_script
```

#### FNT Product Sync (nightly at 02:00)
```json
{
  "name": "FNT Product Sync",
  "run_type": "daily",
  "run_time": "02:00:00",
  "active": "true",
  "comments": "Handbook Section 4: Nightly product master data import from FNT Command",
  "script": "// FNT Product Sync — Nightly\n// Fetches products from FNT, upserts into cmdb_model\ntry {\n  var sm = new sn_ws.RESTMessageV2('FNT Command API', 'Get Products');\n  sm.setStringParameterNoEscape('pageSize', '500');\n  sm.setStringParameterNoEscape('page', '0');\n  var response = sm.execute();\n  var body = JSON.parse(response.getBody());\n  var deriver = new FNTCIClassDeriver();\n  var items = body.items || [];\n  gs.info('[FNT Product Sync] Fetched ' + items.length + ' products');\n  items.forEach(function(product) {\n    var ciClass = deriver.deriveCIClass(product.FUNCTION, product.CONFIG_TABLE_NAME, product.IS_CARD);\n    if (!ciClass) return;\n    // Upsert into cmdb_model\n    var gr = new GlideRecord('cmdb_model');\n    gr.addQuery('name', product.EXPLANATION);\n    gr.query();\n    if (gr.next()) {\n      gr.setValue('short_description', product.TYPE);\n      gr.setValue('cmdb_ci_class', ciClass);\n      gr.update();\n    } else {\n      gr.initialize();\n      gr.setValue('name', product.EXPLANATION);\n      gr.setValue('short_description', product.TYPE);\n      gr.setValue('cmdb_ci_class', ciClass);\n      gr.insert();\n    }\n  });\n  gs.info('[FNT Product Sync] Done.');\n} catch(e) {\n  gs.error('[FNT Product Sync] Error: ' + e.message);\n}"
}
```

#### FNT Daily Reconciliation (daily at 03:00)
```json
{
  "name": "FNT Daily Reconciliation",
  "run_type": "daily",
  "run_time": "03:00:00",
  "active": "true",
  "comments": "Handbook Section 6: Daily drift detection and correction between FNT Command and ServiceNow",
  "script": "// FNT Daily Reconciliation\ntry {\n  // Step 1: Fetch all FNT CIs\n  var sm = new sn_ws.RESTMessageV2('FNT Command API', 'Get Objects');\n  sm.setStringParameterNoEscape('pageSize', '500');\n  var response = sm.execute();\n  var fntCIs = JSON.parse(response.getBody()).items || [];\n  var mapper = new FNTFieldMapper();\n  var stats = {inSync: 0, correctedSN: 0, correctedFNT: 0, missingInSN: 0, flagged: 0};\n\n  fntCIs.forEach(function(fntCI) {\n    var gr = new GlideRecord('cmdb_ci');\n    gr.addQuery('u_fnt_elid', fntCI.ELID);\n    gr.setLimit(1);\n    gr.query();\n    if (!gr.next()) {\n      stats.missingInSN++;\n      gs.warn('[Reconciliation] CI missing in SN: ELID=' + fntCI.ELID);\n      return;\n    }\n    // Compare fields\n    var inboundFields = mapper.getInboundFields();\n    var diffs = [];\n    inboundFields.forEach(function(m) {\n      var snVal = gr.getValue(m.sn) || '';\n      var fntVal = fntCI[m.fnt] || '';\n      if (snVal !== String(fntVal)) diffs.push({field: m.sn, sn: snVal, fnt: fntVal, direction: m.direction});\n    });\n    if (diffs.length === 0) { stats.inSync++; return; }\n    gs.info('[Reconciliation] ELID=' + fntCI.ELID + ' has ' + diffs.length + ' differences');\n    stats.correctedSN += diffs.length;\n  });\n  gs.info('[Reconciliation] Done. Stats: ' + JSON.stringify(stats));\n} catch(e) {\n  gs.error('[Reconciliation] Error: ' + e.message);\n}"
}
```

## Summary Output

After all steps, print a summary table:

```
╔═══════════════════════════════════╦══════════╗
║ Artifact                          ║ Status   ║
╠═══════════════════════════════════╬══════════╣
║ Field: u_fnt_elid                 ║ CREATED  ║
║ Field: u_fnt_arrival_date         ║ SKIPPED  ║
║ ...                               ║          ║
║ Business Rule: FNT Outbound Sync  ║ CREATED  ║
║ ...                               ║          ║
╚═══════════════════════════════════╩══════════╝
Created: X | Skipped: Y | Errors: Z
```

## Important Notes

- All custom fields go on `cmdb_ci` (base table), NOT on child tables
- `u_fnt_elid` should be set to `read_only=true` AFTER initial back-population is complete. Note: `read_only` in SN only blocks UI edits — the Table API can still write the field. This means FNT can still set `u_fnt_elid` on new CIs via POST, but SN users cannot accidentally modify it in the form. On PATCH/updates, FNT should NOT send `u_fnt_elid` in the payload (use sys_id in the URL as identifier instead).
- The OOTB `rack_units` field on `cmdb_ci_rack` stays empty — use `u_fnt_rack_units` instead
- Delta payloads only for updates (PATCH) — never send the full record
- Last-Write-Wins via `fnt_source_timestamp` vs `sys_updated_on`
- Error handling: 4xx = log + alert, no retry; 5xx = retry once after 5 minutes
- The full Implementation Handbook is at `docs/SN_FNT_Implementation_Handbook_v1.0.docx`
