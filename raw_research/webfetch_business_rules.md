# Business Rules
Source: WebFetch (servicenowwithrunjay.com, jitendrazaa.com)

## Definition
Server-side scripts that run when records are displayed, inserted, updated, deleted, or queried. Execute on the server regardless of data access method (UI, API, import).

## Four Main Types

### 1. Before Business Rules
- Runs AFTER form submission but BEFORE database write
- Changes auto-save — no `current.update()` needed
- Use for: data validation, field population, aborting saves (`current.setAbortAction(true)`)

### 2. After Business Rules
- Runs AFTER database commit (synchronous, blocks user)
- Use for: updating related records, triggering events, audit logging
- CAUTION: using `current.update()` risks recursion; use `setWorkflow(false)` if necessary

### 3. Async Business Rules
- Runs asynchronously via scheduler (non-blocking)
- User continues immediately
- **Preferred over After BRs** for better UX
- Use for: email notifications, external API calls, SLA calculations, heavy processing
- Appear as "ASYNC: [BR Name]" in System Scheduler

### 4. Display Business Rules
- Runs when form loads (read/display only)
- Primary use: populate `g_scratchpad` for client-side access
- Scope: forms only — NOT list views, APIs, insert/update

### 5. Before Query (special type)
- Runs before every table query
- Use for: row-level security, automatic data filtering
- Alternative to ACLs (no restriction message shown to users)
- WARNING: significant performance impact; use sparingly

## Execution Order (complete transaction flow)
1. onSubmit Client Scripts (browser validation)
2. Before Business Rules (Order < 1000)
3. ServiceNow Engines/Workflows (Order = 1000)
4. Before Business Rules (Order ≥ 1000)
5. Database Operation (insert/update/delete)
6. After Business Rules (synchronous)
7. Async Business Rules (background scheduler)

Within same type: lower Order number executes first.

## Key Objects
- `current` — GlideRecord of record being processed (new values)
- `previous` — GlideRecord with original values before modification (Before/After on updates only)
- `g_scratchpad` — server-to-client bridge (set in Display BR, read in onLoad Client Script)

## Best Practices
| Scenario | Recommended approach |
|----------|---------------------|
| Field mandatory/visible/read-only | UI Policy (no code) |
| Complex client validation | Client Script |
| Validate/modify before save | Before BR |
| Auto-create related records | After BR |
| Email/API notifications | Async BR |
| Pass server data to form | Display BR + g_scratchpad |

## Performance & Pitfalls
- **NEVER** use `current.update()` in Before BRs → infinite recursion
- Use `GlideAggregate` for counts, not loading all records
- Replace `gs.log()` with `gs.info()/gs.debug()` in scoped apps
- Specify conditions precisely — unneeded BRs impact performance
- Monitor transaction logs for BRs over 100ms

## Debugging
- Session Debug: System Diagnostics > Session Debug > Debug Business Rule
- Script Tracer: detailed execution tracking with timing
- Logs: `gs.info()` → sys_log table

## Script Structure
```javascript
(function executeRule(current, previous) {
    // current = record being processed
    // previous = original values (null for async)
})(current, previous);
```
