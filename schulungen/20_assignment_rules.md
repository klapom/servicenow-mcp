---
source_type: platform
topics:
  - assignment rules
  - auto-assignment
  - data lookup rules
  - AWA
  - skills-based routing
  - predictive intelligence
---

# Assignment Rules

## Overview

Assignment Rules automatically set the `assignment_group` and `assigned_to` fields on task records when specified conditions are met. They replace manual dispatcher workflows by routing work items to the correct team or individual based on data attributes of the record.

ServiceNow provides several layers of assignment automation, from simple rule-based routing (Assignment Rules) to AI-driven skills-based routing (Advanced Work Assignment).

---

## Assignment Rule Mechanisms

### 1. Assignment Rules (Classic)
The simplest form. Evaluates a condition against incoming records and sets assignment fields.

**Table:** `sys_assignment_rule`
**Navigation:** System Policy → Rules → Assignment Rules

**Key characteristics:**
- Only run if `assignment_group` is **currently empty**
- Follow "first match wins" — lowest Order number that matches wins
- Do NOT overwrite existing assignment values
- Can set both `assignment_group` and `assigned_to`

### 2. Data Lookup Rules
More powerful than assignment rules — can change ANY field, not just assignment fields.

**Navigation:** System Policy → Data Lookup and Chart Color → Data Lookup Definitions

**Key differences from Assignment Rules:**
- Can modify any field on the record (category, priority, subcategory, etc.)
- CAN overwrite existing values (configurable)
- Can run on form change (before save), insert, or update events

### 3. Advanced Work Assignment (AWA)
Agent capacity and skills-based routing. Actively "pushes" work to qualified available agents.

### 4. Agent Intelligence / Predictive Intelligence
Machine learning-based auto-categorization and assignment prediction.

---

## Assignment Rules in Detail

### Configuration Fields

| Field | Description |
|-------|-------------|
| Name | Descriptive rule name |
| Table | Task table to monitor (e.g., `incident`) |
| Priority | Execution order (lower = higher priority) |
| Conditions | When this rule applies |
| Assignment group | Group to assign to |
| Assign to | Individual user to assign to (optional) |
| Active | Enable/disable |

### Execution Behavior

Assignment rules execute during the "Before Engines" phase of record save, alongside other platform engines (order ~1000). They run before Business Rules with order >= 1000.

**"First match" principle:**
```
Rules evaluated in order by Priority (ascending):
  Priority 100: Category = 'Network' → assignment_group = Network Ops
  Priority 200: Category = 'Software' → assignment_group = App Support
  Priority 300: Category = 'Hardware' → assignment_group = Desktop Support
  Priority 999: (catch-all) → assignment_group = Service Desk

First rule that matches is applied; remaining rules are not evaluated.
```

### Only When Unassigned
Assignment Rules only run when `assignment_group` is empty. If a dispatcher has already manually set the group, the rule does not overwrite it. This is the "don't overwrite" behavior.

To override (use Data Lookup Rules instead), or to create a Business Rule that runs regardless.

### Example Configurations

**Route network incidents:**
- Table: incident
- Conditions: Category = Network AND State = New
- Assignment group: Network Operations Center

**Route VPN incidents specifically:**
- Table: incident
- Conditions: Category = Network AND Subcategory = VPN
- Assignment group: VPN Support Team
- Priority: 50 (runs before the general Network rule at 100)

---

## Data Lookup Rules

Data Lookup Rules are evaluated via the Data Lookup engine and can modify multiple fields simultaneously.

### Configuration

1. **Data Lookup Definition:** Defines which table and which fields to populate
2. **Lookup Table:** A structured lookup table where rows define conditions and output values
3. **Match Criteria:** Which input fields determine the output values

### When Data Lookup Runs

| Event | Description |
|-------|-------------|
| On Change | When specified input fields change (before save) |
| On Insert | When a new record is created |
| On Update | When a record is modified |

### Priority Field Resolution
Data Lookup is the mechanism behind the **Priority Matrix** for incidents:
- Input fields: Impact, Urgency
- Output field: Priority
- Lookup table: `dl_u_priority` (data lookup matrix)
- Mapping: Impact=High + Urgency=High → Priority=1 (Critical)

This is why Priority is read-only and auto-calculated — it's set by a Data Lookup Rule.

---

## Advanced Work Assignment (AWA)

AWA moves beyond passive rule-matching to active work distribution. It monitors agent availability and capacity, then "pushes" appropriate work items to agents rather than waiting for agents to pull from queues.

### AWA Components

| Component | Description |
|-----------|-------------|
| Work Item Queue | Collection of unassigned work items waiting for assignment |
| Routing Criteria | Conditions that filter which work items enter which queue |
| Assignment Criteria | Skills, capacity, and availability requirements for agents |
| Agent Capacity | Maximum number of simultaneously active work items per agent |
| Skills | Competencies required for specific types of work |
| Availability | Whether agent is logged in and available |

### AWA Assignment Flow

```
New Incident Created
    ↓
Routing Criteria Evaluation
    → Does this match a configured queue?
    ↓
Work Item enters Queue
    ↓
AWA Engine evaluates available agents:
    - Available (logged in, not at capacity)
    - Has required skills (e.g., 'Network Troubleshooting')
    - In the correct assignment group
    ↓
Work Item pushed to best-matching agent
    ↓
Agent receives notification; work item appears in their workspace
```

### Skills-Based Routing
Skills are defined on:
1. **Work Items:** Required skills for this type of work (set via routing criteria)
2. **Agents:** Skills the agent possesses (with proficiency level 1-10)

The AWA engine matches work item requirements to agent skills, preferring:
- Agents with higher proficiency in required skills
- Agents with the lowest current workload (within capacity)
- Agents in the correct time zone or location (if configured)

### AWA vs. Classic Assignment Rules

| Feature | Assignment Rules | AWA |
|---------|----------------|-----|
| Assignment model | Pull (agent takes from queue) | Push (work sent to agent) |
| Agent availability awareness | No | Yes |
| Capacity management | No | Yes |
| Skills matching | No | Yes |
| Setup complexity | Simple | More complex |
| Best for | Simple routing | Contact center, high-volume queues |

---

## Agent Intelligence / Predictive Intelligence

ServiceNow's ML capabilities can predict assignment group based on historical data.

### Predictive Routing
- Analyzes historical incident assignments
- Builds a model that predicts `assignment_group` from `short_description`, `category`, `cmdb_ci`
- Can set assignment group with a confidence score
- High-confidence predictions can be auto-applied; low-confidence shown as suggestions

**Plugin:** `com.snc.itsm.agent.intelligence`

### Auto-Categorization
Beyond assignment, Predictive Intelligence can also predict:
- `category` and `subcategory` from short description text
- Priority recommendations based on historical patterns
- CI association suggestions based on keywords

### Training and Model Management
- Models are trained on historical records
- Minimum training data: typically 100+ resolved records with consistent assignment patterns
- Models should be retrained periodically as patterns change
- Available in: Now Platform → Predictive Intelligence → Solutions

---

## Execution Order Context

Understanding when assignment rules execute relative to other automation:

```
Save triggered (insert or update)
  ↓
Step 1: onSubmit Client Scripts (browser validation)
  ↓
Step 2: Before Business Rules (Order < 1000)
  ↓
Step 3: Before Engines (Order ~1000):
  - Assignment Rules
  - Data Lookup Rules
  - SLA Calculation
  - (other engines)
  These have no guaranteed order relative to each other
  ↓
Step 4: Before Business Rules (Order ≥ 1000)
  ↓
Step 5: Database write
  ↓
Step 6: After Business Rules
  ↓
Step 7: Async Business Rules (background)
```

**Implication:** A Before Business Rule with Order < 1000 runs before Assignment Rules. This means a BR can pre-populate `assignment_group` and prevent the Assignment Rule from running (since it only runs when the field is empty).

---

## Combining Assignment Mechanisms

### Tiered Assignment Strategy

1. **CI-based assignment (Before BR, Order 100):**
   - If incident has a CI, copy CI's `support_group` to `assignment_group`
   - Most accurate; reflects actual CI ownership

2. **Service-based assignment (Before BR, Order 200):**
   - If business service is populated and no CI, copy service's `support_group`

3. **Assignment Rule fallback (Order 300-999):**
   - Category-based rules catch incidents not assigned by BR
   - Priority-ordered rules from most specific to most general

4. **AWA queue (real-time):**
   - For contact center-style teams, AWA pushes to available agents after initial group assignment

---

## Best Practices

### Rule Ordering
- Be explicit and deliberate with Priority values — use gaps (100, 200, 300) to allow insertion
- Most specific rules should have lower (higher priority) order numbers
- Always have a catch-all rule at a high order number to ensure everything gets assigned

### Avoiding Over-Assignment
- Assignment Rules set the group; individual assignment (`assigned_to`) should often be left empty to allow the group to self-manage via AWA or manual selection
- Forcing `assigned_to` can bottleneck throughput if that person is unavailable

### Testing
- Test with impersonation — create an incident as a non-admin user
- Verify the correct rule fired using Session Debug → Debug Assignment Rule
- Test all rule conditions, including edge cases (empty fields, unusual category combinations)

### Maintenance
- Review assignment rules quarterly
- Remove or update rules for retired teams or reorganized categories
- Track unassigned incidents as a metric — high unassigned rates indicate rule gaps

---

## Common Patterns

### CI-Based Auto-Assignment Business Rule

```javascript
// Before BR on incident — Order: 100
// When: Insert, Condition: cmdb_ci is not empty AND assignment_group is empty
(function executeRule(current, previous) {
    if (!current.cmdb_ci.nil() && current.assignment_group.nil()) {
        var ci = new GlideRecord('cmdb_ci');
        if (ci.get(current.cmdb_ci)) {
            if (!ci.support_group.nil()) {
                current.assignment_group = ci.support_group;
                gs.info('Assignment: CI {0} support group applied to {1}',
                    ci.name, current.number);
            }
        }
    }
})(current, previous);
```

### Round-Robin Assignment (Custom)

ServiceNow doesn't include round-robin natively in basic assignment rules. A common custom approach:

```javascript
// Script Include: RoundRobinAssigner
var RoundRobinAssigner = Class.create();
RoundRobinAssigner.prototype = {
    initialize: function(groupSysId) {
        this.groupSysId = groupSysId;
    },

    getNextAgent: function() {
        var members = [];
        var gm = new GlideRecord('sys_user_grmember');
        gm.addQuery('group', this.groupSysId);
        gm.query();
        while (gm.next()) {
            members.push(gm.getValue('user'));
        }
        if (members.length === 0) return '';

        // Use a counter stored in a system property
        var counterKey = 'rr_counter_' + this.groupSysId;
        var counter = parseInt(gs.getProperty(counterKey, '0'));
        var nextIndex = counter % members.length;
        gs.setProperty(counterKey, String(counter + 1));
        return members[nextIndex];
    },

    type: 'RoundRobinAssigner'
};
```
