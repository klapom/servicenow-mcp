---
source_type: platform
topics:
  - client scripts
  - UI policies
  - g_form
  - g_user
  - GlideAjax
  - form scripting
  - browser-side automation
---

# Client Scripts and UI Policies

## Overview

Client Scripts and UI Policies are browser-side automation mechanisms that control the behavior of ServiceNow forms. They run in the user's browser (not the server) and enable real-time form interactions: hiding fields, making fields mandatory, validating input, and dynamically loading data.

**Key distinction from Business Rules:** Client Scripts and UI Policies only execute when a user is interacting with a form. They do not run during REST API calls, import set processing, or background jobs. Server-side validation via Business Rules is always required for data integrity.

---

## Client Script Types

### onLoad()
Executes when a form is first rendered, before the user can interact with it. Used for:
- Setting default field values based on context
- Hiding or showing fields based on user or record attributes
- Pre-populating fields with data from `g_scratchpad`
- Establishing initial form state

```javascript
function onLoad() {
    // Hide cost fields for non-finance users
    if (!g_user.hasRole('finance')) {
        g_form.setVisible('cost', false);
        g_form.setVisible('budget_code', false);
    }

    // Pre-populate from scratchpad data (set by Display Business Rule)
    if (g_scratchpad.caller_vip === 'true') {
        g_form.showFieldMsg('caller_id', 'VIP Customer - Escalate immediately', 'warning');
    }
}
```

### onChange(control, oldValue, newValue, isLoading, isTemplate)
Executes when a specific field's value changes. Has access to both the old and new values.

| Parameter | Description |
|-----------|-------------|
| `control` | DOM control object (NOT available in Mobile/Service Portal) |
| `oldValue` | The field's value before the change |
| `newValue` | The field's current value after the change |
| `isLoading` | `true` if the change occurs during form load (not user-initiated) |
| `isTemplate` | `true` if the change is from applying a template |

**Important:** Always check `isLoading` if logic should only run on actual user changes, not form initialization.

```javascript
function onChange(control, oldValue, newValue, isLoading, isTemplate) {
    if (isLoading || newValue === '') {
        return; // Don't process during form load or when cleared
    }

    // Dynamically show/hide subcategory based on category selection
    if (newValue === 'Network') {
        g_form.setVisible('subcategory', true);
        // Filter subcategory choices
        g_form.clearOptions('subcategory');
        g_form.addOption('subcategory', 'connectivity', 'Connectivity Issue');
        g_form.addOption('subcategory', 'performance', 'Performance Degradation');
        g_form.addOption('subcategory', 'dns', 'DNS Resolution');
    } else {
        // Load standard subcategories or hide the field
        g_form.setVisible('subcategory', newValue !== '');
    }
}
```

### onSubmit()
Executes when the form is submitted (Save button clicked). Returning `false` cancels the submission.

```javascript
function onSubmit() {
    // Validate that resolution notes are meaningful
    var closeNotes = g_form.getValue('close_notes');
    if (g_form.getValue('state') == '6' && closeNotes.length < 50) {
        g_form.showFieldMsg('close_notes',
            'Resolution notes must be at least 50 characters',
            'error');
        return false; // Cancel the save
    }

    // Confirm major change submit
    if (g_form.getValue('risk') == '1' /* High */) {
        if (!confirm('This is a high-risk change. Are you sure you want to submit?')) {
            return false;
        }
    }
    return true; // Allow submission
}
```

### onCellEdit(sysIDs, table, oldValues, newValue, callback)
Executes when a cell value is changed in a list view (inline list editing). Different signature from form scripts.

| Parameter | Description |
|-----------|-------------|
| `sysIDs` | Array of record sys_ids being edited |
| `table` | Table name |
| `oldValues` | Array of previous values |
| `newValue` | New value being applied |
| `callback` | Must be called to commit or cancel the edit |

```javascript
function onCellEdit(sysIDs, table, oldValues, newValue, callback) {
    // Validate that state change from list is permitted
    if (newValue == '6' /* Resolved */ && table == 'incident') {
        alert('Please open the record to provide resolution notes before closing.');
        callback(false); // Cancel the edit
        return;
    }
    callback(true); // Allow the edit
}
```

---

## g_form API

The `g_form` object is the primary interface for Client Scripts to interact with form fields.

### Field Value Operations

| Method | Description |
|--------|-------------|
| `g_form.getValue(fieldName)` | Get the current raw value of a field |
| `g_form.getDisplayValue(fieldName)` | Get the display value (label, not stored value) |
| `g_form.setValue(fieldName, value, displayValue)` | Set a field's value; optional display value for reference fields |
| `g_form.clearValue(fieldName)` | Clear a field's value |

### Field State Operations

| Method | Description |
|--------|-------------|
| `g_form.setVisible(fieldName, visible)` | Show (true) or hide (false) a field |
| `g_form.setMandatory(fieldName, mandatory)` | Make a field required (true) or optional (false) |
| `g_form.setReadOnly(fieldName, readOnly)` | Make a field read-only (true) or editable (false) |
| `g_form.setDisabled(fieldName, disabled)` | Disable (true) or enable a field |

### Choice List Operations

| Method | Description |
|--------|-------------|
| `g_form.addOption(fieldName, value, label, index)` | Add an option to a choice/select field |
| `g_form.clearOptions(fieldName)` | Remove all options from a choice field |
| `g_form.removeOption(fieldName, value)` | Remove a specific option |

### Message Operations

| Method | Description |
|--------|-------------|
| `g_form.showFieldMsg(fieldName, message, type)` | Show inline message: `'info'`, `'warning'`, `'error'` |
| `g_form.hideFieldMsg(fieldName)` | Remove inline field message |
| `g_form.addErrorMessage(message)` | Show error banner at top of form |
| `g_form.addInfoMessage(message)` | Show info banner at top of form |
| `g_form.clearMessages()` | Clear all form banners |

### Section and Related List Operations

| Method | Description |
|--------|-------------|
| `g_form.setSectionDisplay(sectionName, display)` | Show/hide a form section |
| `g_form.isMandatory(fieldName)` | Check if a field is currently mandatory |
| `g_form.isVisible(fieldName)` | Check if a field is currently visible |

---

## g_user Object

The `g_user` object provides information about the currently logged-in user.

| Property/Method | Description |
|----------------|-------------|
| `g_user.userName` | Login username (e.g., `john.smith`) |
| `g_user.userID` | The `sys_id` of the current user |
| `g_user.firstName` | First name |
| `g_user.lastName` | Last name |
| `g_user.hasRole(roleName)` | Returns `true` if user has the specified role |
| `g_user.hasRoleExactly(roleName)` | Returns `true` only if user has that exact role (not via inheritance) |
| `g_user.hasRoles()` | Returns `true` if user has any roles (not a basic end-user) |

```javascript
// Show advanced fields only for ITIL users
if (g_user.hasRole('itil') || g_user.hasRole('itil_admin')) {
    g_form.setVisible('caused_by', true);
    g_form.setVisible('workaround', true);
}
```

---

## GlideAjax: Server Calls from Client Scripts

Client Scripts run in the browser and cannot directly query the database. GlideAjax provides an asynchronous mechanism to call a server-side Script Include and return data to the client.

**Always use asynchronous GlideAjax** — synchronous calls (`getXMLWait()`) freeze the browser and are not available in scoped applications.

### Server-Side Script Include (extends AbstractAjaxProcessor)

```javascript
var IncidentClientHelper = Class.create();
IncidentClientHelper.prototype = Object.extendsObject(AbstractAjaxProcessor, {

    // Get open incident count for a CI
    getCIOpenIncidentCount: function() {
        var ciSysId = this.getParameter('sysparm_ci_sys_id');
        var ga = new GlideAggregate('incident');
        ga.addQuery('cmdb_ci', ciSysId);
        ga.addQuery('state', 'IN', '1,2,3');
        ga.addAggregate('COUNT');
        ga.query();
        if (ga.next()) {
            return ga.getAggregate('COUNT');
        }
        return '0';
    },

    // Get user manager name
    getUserManagerName: function() {
        var userSysId = this.getParameter('sysparm_user_sys_id');
        var user = new GlideRecord('sys_user');
        if (user.get(userSysId)) {
            return user.manager.getDisplayValue();
        }
        return '';
    },

    type: 'IncidentClientHelper'
});
```

### Client-Side GlideAjax Call

```javascript
function onChange(control, oldValue, newValue, isLoading, isTemplate) {
    if (isLoading || !newValue) return;

    // Async call to Script Include
    var ga = new GlideAjax('IncidentClientHelper');
    ga.addParam('sysparm_name', 'getCIOpenIncidentCount');
    ga.addParam('sysparm_ci_sys_id', newValue);

    ga.getXML(function(response) {
        var answer = response.responseXML.documentElement.getAttribute('answer');
        if (parseInt(answer) > 3) {
            g_form.showFieldMsg('cmdb_ci',
                'Warning: ' + answer + ' open incidents on this CI',
                'warning');
        }
    });
}
```

---

## UI Policies

UI Policies provide a no-code/low-code alternative to Client Scripts for controlling field visibility, mandatory state, and read-only state.

### Why Use UI Policies Instead of Client Scripts
- **Performance:** UI Policies evaluate faster than equivalent Client Scripts
- **No code:** Business analysts can create UI Policies without JavaScript knowledge
- **"Reverse if false" logic:** Automatically reverses the action when condition becomes false
- **Visual clarity:** Conditions are visible in the condition builder without reading code

### UI Policy Configuration

| Property | Description |
|----------|-------------|
| Table | The table where this policy applies |
| Conditions | When the policy actions apply (condition builder) |
| On load | Whether to evaluate the policy when the form loads |
| Reverse if false | Undo the actions when the condition becomes false |
| Global | Apply regardless of UI type |
| Active | Enable/disable the policy |

### UI Policy Actions

For each field, each UI Policy Action can set:
| Property | Values |
|----------|--------|
| Mandatory | True / False / Leave Alone |
| Visible | True / False / Leave Alone |
| Read Only | True / False / Leave Alone |

### Advanced UI Policy Scripting

For logic too complex for the condition builder, UI Policies support "Execute if true" and "Execute if false" scripts:

```javascript
// Execute if true script
function onCondition() {
    g_form.setValue('impact', '1'); // Force impact to High when condition met
    g_form.showFieldMsg('impact', 'Impact set to High automatically', 'info');
}
```

---

## Client Scripts vs. UI Policies: Decision Guide

| Need | Recommendation |
|------|----------------|
| Make field mandatory when other field has a value | UI Policy |
| Hide field based on user role | Client Script (g_user.hasRole) or UI Policy with "Roles" condition |
| Set field value dynamically when another field changes | Client Script (onChange) |
| Validate data on form submit | Client Script (onSubmit) |
| Query the database and show result on form | Client Script (onChange + GlideAjax) |
| Show/hide field based on simple condition | UI Policy (no code) |
| Complex cascading field logic | Client Script |
| Multiple fields all becoming mandatory together | UI Policy (one policy, multiple actions) |

---

## Mobile and Service Portal Considerations

### API Limitations

Not all g_form methods work in all UI contexts:

| Method | Desktop | Service Portal | Mobile |
|--------|---------|---------------|--------|
| `g_form.getValue()` | Yes | Yes | Yes |
| `g_form.setValue()` | Yes | Yes | Yes |
| `g_form.setVisible()` | Yes | Yes | Limited |
| `g_form.addOption()` | Yes | Limited | No |
| `g_form.showFieldMsg()` | Yes | Yes | Limited |
| `control` in onChange | Yes | No | No |
| DOM manipulation | Yes | No | No |

### UI Type Field
Both Client Scripts and UI Policies have a **UI Type** field:
- **All:** Applies to Desktop, Mobile, and Service Portal
- **Desktop:** Desktop UI only
- **Mobile / Service Portal:** Both mobile and SP

**Best practice:** Create separate scripts for Desktop and Mobile/Service Portal when they require different behavior or when specific APIs are not available.

### Service Portal Angular Context
Service Portal widgets use AngularJS, not the g_form API. Client Scripts do not work in SP widgets — widget client controllers must handle all client-side logic using AngularJS patterns (`c.data`, `c.server.update()`).

---

## Performance Best Practices

### Minimize Server Calls
Each GlideAjax call adds network latency. Strategies:
- Batch multiple data needs into a single GlideAjax call (return JSON with multiple values)
- Use Display Business Rules + g_scratchpad to pre-load data needed on form load
- Cache values in form variables rather than making repeated calls for the same data

### Avoid Synchronous Calls
`getXMLWait()` is synchronous — it freezes the browser until the response arrives. This is:
- Not available in scoped applications
- Poor UX (browser becomes unresponsive)
- Blocked in strict mode

Always use `getXML(callback)` for asynchronous processing.

### Script Scope and Strict Mode
New Client Scripts run in strict mode:
- `var` declarations required (no implicit globals)
- Limited DOM access for security and compatibility
- `document.getElementById()` and jQuery available but discouraged — use g_form API instead

### Avoid Heavy onLoad Processing
`onLoad` scripts delay form rendering. If complex processing is needed:
- Move data retrieval to Display Business Rules + g_scratchpad
- Defer non-critical logic to a timeout
- Use GlideAjax asynchronously so the form renders before data arrives

---

## Common Patterns

### Dynamic Subcategory Based on Category

```javascript
// onChange on 'category' field
function onChange(control, oldValue, newValue, isLoading, isTemplate) {
    if (isLoading) return;
    g_form.clearOptions('subcategory');
    g_form.setValue('subcategory', '');
    if (!newValue) {
        g_form.setMandatory('subcategory', false);
        return;
    }
    var ajax = new GlideAjax('CategoryHelper');
    ajax.addParam('sysparm_name', 'getSubcategories');
    ajax.addParam('sysparm_category', newValue);
    ajax.getXML(function(response) {
        var subcats = JSON.parse(response.responseXML.documentElement.getAttribute('answer'));
        subcats.forEach(function(s) {
            g_form.addOption('subcategory', s.value, s.label);
        });
        g_form.setMandatory('subcategory', subcats.length > 0);
    });
}
```

### VIP Caller Warning

```javascript
// onLoad + onChange on 'caller_id' field
function checkVIP(callerId) {
    if (!callerId) return;
    var ajax = new GlideAjax('UserInfoHelper');
    ajax.addParam('sysparm_name', 'isVIP');
    ajax.addParam('sysparm_user_id', callerId);
    ajax.getXML(function(response) {
        var isVip = response.responseXML.documentElement.getAttribute('answer');
        if (isVip === 'true') {
            g_form.showFieldMsg('caller_id', 'VIP User — Prioritize this incident', 'warning');
            if (g_form.getValue('impact') !== '1') {
                g_form.setValue('impact', '1');
            }
        } else {
            g_form.hideFieldMsg('caller_id');
        }
    });
}
```

### Mandatory Resolution Notes on Close

```javascript
// onSubmit client script on 'incident' table
function onSubmit() {
    var state = parseInt(g_form.getValue('state'));
    if (state === 6 || state === 7) { // Resolved or Closed
        var notes = g_form.getValue('close_notes');
        if (!notes || notes.trim().length < 30) {
            g_form.showFieldMsg('close_notes',
                'Please provide detailed resolution notes (minimum 30 characters)',
                'error');
            return false;
        }
    }
    return true;
}
```
