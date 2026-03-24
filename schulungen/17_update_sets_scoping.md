---
source_type: platform
topics:
  - update sets
  - scoped applications
  - deployment
  - configuration management
  - source control
  - application scope
---

# Update Sets and Application Scoping

## Overview

Update Sets are ServiceNow's mechanism for capturing, packaging, and deploying configuration changes between instances (development → test → production). Application Scoping provides isolation between different applications on the same instance, preventing accidental interference and enabling independent lifecycle management.

Together, Update Sets and Scoping form the foundation of the ServiceNow SDLC (Software Development Lifecycle) for configuration changes.

---

## Update Sets

### What Is an Update Set?
An Update Set is a collection of configuration changes made in one ServiceNow instance that can be exported and applied to another instance. It acts as a "change package" for configurations.

**What Update Sets capture:**
- Business Rules, Client Scripts, UI Policies
- Script Includes, ACLs
- Tables, fields, dictionary entries
- Flows, Workflows, Actions
- Notifications, Scheduled Jobs
- Forms, Views, Lists
- Application menus, modules

**What Update Sets do NOT automatically capture:**
- Data records (incidents, users, etc.) — use Import Sets for data migration
- Some system properties (must be added manually via "Add to Update Set")
- Scheduled Job "last run" times
- Some attachment data

### Update Set Lifecycle

```
Development Instance
    └── Create Update Set
    └── Make configuration changes (captured automatically)
    └── Mark Complete
        ↓
    Export XML file
        ↓
Test Instance
    └── Import XML
    └── Preview (check for errors/conflicts)
    └── Commit (apply changes)
        ↓
Production Instance
    └── Import XML
    └── Preview
    └── Commit
```

### Creating and Managing Update Sets

**Navigation:** System Update Sets → Local Update Sets

#### Key Update Set Fields

| Field | Description |
|-------|-------------|
| Name | Descriptive name — convention: `[Ticket#] [Scope] [Description]` |
| Description | Full description of what the update set contains |
| State | In Progress, Complete, Ignore |
| Application | Application scope (Global or specific app) |
| Release date | Target release date |
| Parent | Reference to a parent batch update set |

#### Naming Convention Best Practice
`[Ticket#] [App Abbreviation] [Version] - [Description]`
Example: `JIRA-1234 INC v1.2 - Priority Auto-Calculate Fix`

Maximum 80 characters. The name should allow future administrators to understand what the update set contains without opening it.

### Setting the Current Update Set
Changes are captured in the currently active update set:
1. Click the "Current Update Set" link in the application navigator (top right area)
2. Select from the dropdown or create a new one
3. All configuration changes made afterward are recorded in this set

**Note:** Changes made in the "Default" system update set are captured but the Default set should not be used for deployment — it's a catch-all for incidental changes.

### Previewing an Update Set
Before committing to a target instance, Preview checks for:

| Problem Type | Description |
|-------------|-------------|
| Missing record | Update references a record that doesn't exist in the target |
| Remote update | Record in target was modified after the XML was created |
| Type conflict | Record has a different type in source vs. target |
| Unresolvable conflict | Cannot automatically determine correct action |

Preview results:
- **No problem:** Safe to commit
- **Remote update (accept remote):** Target's version will be overwritten
- **Remote update (accept local):** Source version wins; target changes lost
- **No action:** Skip this change (target already has a newer version)

### Committing an Update Set
After preview resolves all issues:
1. Click "Commit Update Set"
2. Changes are applied to the target instance
3. Commit log records what was applied, when, and by whom

**Backout:** ServiceNow provides a "Back Out" button after commit. However, this only works for straightforward changes and is not reliable for complex updates. **Fix-forward** is the recommended strategy — apply a corrected update set rather than backing out.

---

## Update Set Batches

For complex releases spanning multiple developers or multiple scopes, a **Batch Update Set** (parent) groups multiple child update sets:

```
Release v2.0 (Parent Batch)
  ├── INC-1234 Incident Priority Fix (Child)
  ├── CHG-567 Change Approval Flow Update (Child)
  └── KB-890 Knowledge Base Layout (Child)
```

Benefits:
- Single import/preview/commit for the entire release
- Child sets can be in different application scopes
- Dependency management between child sets

---

## Application Scoping

### What Is Application Scope?
A scope is a namespace for application artifacts. Scoped applications:
- Have a unique prefix (e.g., `x_myco_myapp_`)
- Protect their artifacts from modification by other scopes
- Can control cross-scope access explicitly
- Enable separate versioning and deployment

### Global vs. Scoped Applications

| Aspect | Global Scope | Scoped Application |
|--------|-------------|-------------------|
| Prefix | (none) | `x_[vendor]_[app]_` |
| Isolation | None — any admin can modify | Protected from other scopes |
| Cross-scope access | Can access anything | Explicit access declaration needed |
| Recommended for | Legacy/base system | New development |
| Update Set grouping | "Global" update set | App-specific update set |
| ServiceNow Store | No | Yes (can be published) |

### Scope Prefixes
Custom application scopes use the format: `x_[company_code]_[app_name]_`
Example: `x_myco_incident_ext_` for "MyCompany Incident Extension"

### Creating a Scoped Application
1. Navigate to System Applications → Studio
2. Create Application → define name, scope prefix
3. All artifacts created in Studio belong to the application scope
4. Application can be exported as a single XML file or source-controlled

### Scope Protection
Scoped application artifacts cannot be modified by:
- Other scoped applications
- Global scripts (unless the scope explicitly allows cross-scope access)

A scoped Business Rule on table `x_myco_myapp_task` cannot be modified from the Global scope without the owning application's permission.

### Cross-Scope Access
A scoped application can control what external scopes can do:

| Access Level | Description |
|-------------|-------------|
| Caller (private) | Only callable within the same scope |
| All application scopes | Callable from any scope |
| Specific scope | Callable only by named scope |

Configure via: Application → Access → Cross-Scope Access Policies

---

## Instance Strategy

### Three-Instance Model
Standard enterprise ServiceNow deployment:

```
DEV (Development)
    ↓ Update Sets / App Deployment
SIT/TEST (System Integration Test / QA)
    ↓ Update Sets / App Deployment
PROD (Production)
```

| Instance | Purpose |
|----------|---------|
| DEV | Active development; not stable |
| TEST/SIT | Integration testing; performance testing |
| PROD | Live; only approved, tested changes |

Some organizations add additional environments:
```
DEV → SIT → UAT (User Acceptance Test) → STAGING → PROD
```

### Sub-Production Refresh Strategy
Test and DEV instances should be periodically refreshed from PROD (cloned) to prevent configuration drift. After a clone, custom Update Sets must be re-applied.

---

## Source Control Integration

Modern ServiceNow development uses source control (Git) alongside Update Sets:

### Application Repository (GIT)
ServiceNow supports Git integration for scoped applications via Studio:
- Commit application changes to Git
- Branch, merge, and pull request workflows
- CI/CD pipelines can deploy applications from Git

**Navigation:** Studio → Source Control

### What Goes into Source Control
- Application XML (all application artifacts)
- Test suites (ATF test records)
- Application properties

### Update Sets vs. Source Control

| Aspect | Update Sets | Source Control |
|--------|------------|----------------|
| Granularity | All changes in a set | Commit-level granularity |
| Rollback | Limited (Back Out) | Git revert |
| Branching | Not supported | Full Git branching |
| Collaboration | Sequential (only one person active) | Parallel (merge conflicts resolved) |
| Best for | Global/mixed changes | Scoped application development |
| Recommended | Legacy approach | Modern approach |

---

## Instance Scan

Instance Scan checks for quality and best practice compliance before deploying Update Sets:

**Navigation:** System Diagnostics → Instance Scan

Scan categories:
- Security (ACL gaps, elevated access)
- Performance (unindexed queries, large scripts)
- Upgrade risk (deprecated API usage)
- Best practices (naming conventions, missing descriptions)

**Best practice:** Run Instance Scan on all Update Sets before promoting from DEV to TEST.

---

## Best Practices

### Update Set Governance
- Always create a named, purposeful update set before starting work — never work in Default
- One update set per story/ticket/change (enables targeted deployment and rollback)
- Mark update sets as Complete before requesting deployment
- Preview on target instance and resolve all issues before committing
- Do not deploy untested update sets to production

### Scope Management
- All new development should be in scoped applications, not Global
- Avoid modifying OOB (out-of-box) records — use extensions and alternatives
- Document cross-scope dependencies explicitly

### Data Handling
- Never put data records in Update Sets — use Import Sets with scripts
- Exception: reference data that must exist for configuration to work (lookup values, categories)
- Use "Add to Update Set" for system properties, schedules, and other normally-uncaptured records

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|---------|
| Preview shows missing record | Referenced record doesn't exist in target | Create the missing record in target first, or include it in the update set |
| Scope conflict error | Global change captured in scoped update set | Ensure update set application matches the scope of changes |
| Preview shows remote update | Target was modified independently | Decide: accept remote (target wins) or accept local (source wins) |
| Commit fails | Data integrity issue | Check sys_update_xml records; may need manual intervention |

---

## Common Patterns

### Standard Release Workflow

```
Developer creates Update Set: "JIRA-1234 Incident Priority v1.0"
    ↓
Developer completes work, marks set as Complete
    ↓
Lead reviews update set contents (sys_update_xml list)
    ↓
Export XML from DEV
    ↓
Import to SIT; Preview; resolve any issues
    ↓
SIT testing complete → promote to PROD
    ↓
Import to PROD; Preview; Commit
    ↓
Post-deployment validation
```

### Emergency Production Fix

When a critical issue needs immediate production fix:
1. Fix directly in PROD (emergency exception; document reason)
2. Capture the fix as an update set in PROD
3. Export and apply to DEV and SIT to keep instances in sync
4. Document in change management as an Emergency Change
