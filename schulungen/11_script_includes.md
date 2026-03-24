---
source_type: platform
topics:
  - script includes
  - server-side scripting
  - GlideAjax
  - AbstractAjaxProcessor
  - reusable code
  - Class.create
  - scoped applications
---

# Script Includes

## Overview

Script Includes are reusable server-side JavaScript libraries stored in ServiceNow. They are not triggered automatically by record events — instead, they are called explicitly by Business Rules, Flow Designer Actions, other Script Includes, scheduled jobs, or REST API scripts.

The primary purpose of Script Includes is the **DRY principle** (Don't Repeat Yourself): complex logic written once in a Script Include can be invoked from many places without duplication. This improves maintainability, testability, and consistency.

---

## Why Script Includes Matter

Without Script Includes:
- Logic is copy-pasted across multiple Business Rules
- A bug fix requires updating every copy
- Code is hard to unit test in isolation
- Business Rules become long and difficult to read

With Script Includes:
- Business Rules are "thin" orchestrators that delegate to Script Includes
- Logic is centralized and versioned in one place
- Individual Script Include methods can be tested independently
- Complex calculations are encapsulated and named meaningfully

---

## Script Include Structure

### Class-Based Pattern (Recommended)

The standard pattern uses `Class.create()` to define an object-oriented class:

```javascript
var IncidentUtils = Class.create();
IncidentUtils.prototype = {

    // Constructor — called when new IncidentUtils() is invoked
    initialize: function() {
        this.incidentTable = 'incident';
        this.logger = new GSLog('incident.utils', this.type);
    },

    // Calculate escalation group based on priority and service
    getEscalationGroup: function(priority, serviceSysId) {
        if (priority == 1) {
            return this._getMajorIncidentGroup(serviceSysId);
        }
        var gr = new GlideRecord('cmdb_ci_service');
        if (gr.get(serviceSysId)) {
            return gr.getValue('support_group');
        }
        return '';
    },

    // Check if incident qualifies for major incident process
    isMajorIncident: function(current) {
        if (current.priority == 1 && !JSUtil.nil(current.cmdb_ci)) {
            var ciClass = current.cmdb_ci.sys_class_name.toString();
            return (ciClass === 'cmdb_ci_service' || ciClass === 'cmdb_ci_server');
        }
        return false;
    },

    // Private helper — convention: underscore prefix
    _getMajorIncidentGroup: function(serviceSysId) {
        // implementation
        return 'Major Incident Team';
    },

    type: 'IncidentUtils'  // Required — identifies the class in logs/debugging
};
```

### Function-Based Pattern (Simpler, Less OO)

For simple utility collections without state:

```javascript
var DateUtils = Class.create();
DateUtils.prototype = {
    initialize: function() {},

    addBusinessDays: function(startDate, days) {
        var gdt = new GlideDateTime(startDate);
        // ... implementation
        return gdt;
    },

    formatForDisplay: function(gdt) {
        return gdt.getDisplayValue();
    },

    type: 'DateUtils'
};
```

### Standalone Function (Non-Class)

A Script Include can also be a simple function rather than a class. The name must match the function name exactly:

```javascript
// Script Include name: "getIncidentCount"
function getIncidentCount(assignmentGroup) {
    var ga = new GlideAggregate('incident');
    ga.addQuery('assignment_group', assignmentGroup);
    ga.addQuery('state', 'IN', '1,2,3');
    ga.addAggregate('COUNT');
    ga.query();
    return ga.next() ? parseInt(ga.getAggregate('COUNT')) : 0;
}
```

---

## Client-Callable Script Includes (GlideAjax)

When a Script Include needs to be called from a **Client Script** in the browser, it must:
1. Have the **"Client callable"** checkbox enabled
2. Extend **`AbstractAjaxProcessor`**

This makes the Script Include accessible via the `GlideAjax` client-side API.

### Server-Side (AbstractAjaxProcessor)

```javascript
var IncidentClientHelper = Class.create();
IncidentClientHelper.prototype = Object.extendsObject(AbstractAjaxProcessor, {

    // Method called from client via: ajax.addParam('sysparm_name', 'getAssignmentGroup')
    getAssignmentGroup: function() {
        var ciSysId = this.getParameter('sysparm_ci_sys_id');
        var categoryVal = this.getParameter('sysparm_category');

        var gr = new GlideRecord('cmdb_ci');
        if (gr.get(ciSysId) && !JSUtil.nil(gr.support_group)) {
            return gr.support_group.getDisplayValue();
        }

        // Fallback: lookup assignment rule for category
        var rule = new GlideRecord('assignment_lookup_rules');
        rule.addQuery('category', categoryVal);
        rule.setLimit(1);
        rule.query();
        if (rule.next()) {
            return rule.assignment_group.getDisplayValue();
        }
        return 'Service Desk';
    },

    // Return multiple values as JSON string
    getCallerInfo: function() {
        var userSysId = this.getParameter('sysparm_user_id');
        var user = new GlideRecord('sys_user');
        var result = { vip: false, manager: '', department: '' };
        if (user.get(userSysId)) {
            result.vip = user.vip.toString() === 'true';
            result.manager = user.manager.getDisplayValue();
            result.department = user.department.getDisplayValue();
        }
        return JSON.stringify(result);
    },

    type: 'IncidentClientHelper'
});
```

### Client-Side Call

```javascript
var ajax = new GlideAjax('IncidentClientHelper');
ajax.addParam('sysparm_name', 'getCallerInfo');
ajax.addParam('sysparm_user_id', g_form.getValue('caller_id'));

ajax.getXML(function(response) {
    var jsonStr = response.responseXML.documentElement.getAttribute('answer');
    var info = JSON.parse(jsonStr);
    if (info.vip) {
        g_form.showFieldMsg('caller_id', 'VIP: ' + info.manager, 'warning');
    }
});
```

### GlideAjax Parameter Retrieval

| Method | Description |
|--------|-------------|
| `this.getParameter('sysparm_name')` | Get the function name to call (auto-dispatched) |
| `this.getParameter('sysparm_custom_param')` | Get any custom parameter |
| `this.getXMLWait()` | Synchronous call (client-side) — avoid in scoped apps |
| `ajax.getXML(callback)` | Asynchronous call (client-side) — recommended |

The `sysparm_name` parameter is automatically dispatched to the method with that name in the AbstractAjaxProcessor subclass.

---

## Scope: Global vs. Scoped Applications

The **"Accessible from"** field on a Script Include controls scope:

| Setting | Behavior |
|---------|---------|
| All application scopes | Available to any scoped app and Global |
| This application scope only | Only available within the owning scoped app |
| Same application (default for scoped) | Can be called by other scripts in the same scoped app |

### Global-Only APIs
Some ServiceNow utility classes are only available in the Global scope:
- `JSUtil` — cannot be used in scoped applications
- `ArrayUtil` — not available in scoped apps (use native JS Array methods instead)
- `GlideAjaxProcessor` (legacy) — replaced by `AbstractAjaxProcessor`

In scoped apps, use:
- `gs.nil()` instead of `JSUtil.nil()`
- Native Array methods instead of `ArrayUtil`

### Cross-Scope Access Pattern
If a scoped app needs logic from a Global Script Include:
1. Create the Script Include in Global scope with `accessible from = All application scopes`
2. Call it from the scoped app's scripts
3. Be aware of scope protection — Global scripts run with Global permissions

---

## Common Built-In Script Includes

### JSUtil (Global only)

```javascript
JSUtil.nil(value)        // Returns true if value is null, undefined, empty string
JSUtil.notNil(value)     // Returns true if value has content
JSUtil.type_of(value)    // Returns type string: 'string', 'number', 'boolean', etc.
JSUtil.has(obj, key)     // Returns true if object has the property
JSUtil.logObject(obj)    // Logs object properties to system log
```

### ArrayUtil (Global only)

```javascript
var au = new ArrayUtil();
au.contains(myArray, 'value')      // Check if array contains value
au.indexOf(myArray, 'value')       // Get index of value (-1 if not found)
au.concat(array1, array2)          // Combine two arrays
au.unique(myArray)                 // Remove duplicates
au.diff(array1, array2)            // Elements in array1 not in array2
```

### TableUtils

```javascript
var tu = new TableUtils('incident');
tu.tableExists()                   // Check if table exists
tu.isExtension('task')             // Check if table extends another
tu.getHierarchy()                  // Get array of table hierarchy
tu.getAllExtensions()               // Get all tables extending this table
```

### GSLog (Logging Utility)

```javascript
var logger = new GSLog('my.application.log', 'ClassName');
logger.setLevel('debug');  // Set log level for this instance
logger.debug('Debug message: {0}', variable);
logger.info('Processing record: {0}', record.number);
logger.warn('Unexpected value encountered');
logger.error('Failed to connect: {0}', errorMessage);
```

### GlideStringUtil

```javascript
GlideStringUtil.escapeHTML(str)    // Escape HTML special characters
GlideStringUtil.escapeQueryTermSeparators(str)  // Escape query strings
GlideStringUtil.isBase64(str)      // Check if string is Base64
GlideStringUtil.base64Encode(str)  // Base64 encode
GlideStringUtil.base64Decode(str)  // Base64 decode
GlideStringUtil.nil(str)           // Check if null/empty (same as JSUtil.nil for strings)
```

---

## Calling Script Includes from Business Rules

```javascript
// In a Business Rule:
(function executeRule(current, previous) {
    var utils = new IncidentUtils();

    // Use the Script Include's method
    if (utils.isMajorIncident(current)) {
        current.assignment_group = utils.getEscalationGroup(current.priority, current.cmdb_ci);
        gs.eventQueue('incident.major_incident_detected', current, current.assignment_group, '');
    }
})(current, previous);
```

---

## Calling Script Includes from Flow Designer

In a Flow Designer "Script" step or custom Action:
```javascript
(function execute(inputs, outputs) {
    var helper = new ChangeValidationUtils();
    outputs.validation_result = helper.validateChangeReadiness(inputs.change_sys_id);
    outputs.error_message = helper.getLastError();
})(inputs, outputs);
```

---

## Calling Script Includes from Scheduled Jobs

```javascript
// In a Scheduled Script Execution:
var cleanup = new StaleRecordCleanup();
var count = cleanup.archiveResolvedIncidents(90); // Archive incidents > 90 days old
gs.info('Archived {0} resolved incidents', count);
```

---

## Best Practices

### Naming Conventions
- Names should be descriptive nouns describing the utility's purpose:
  - `IncidentUtils` — incident-specific utilities
  - `CatalogFulfillmentHelper` — catalog fulfillment logic
  - `DateCalculationUtils` — date/time calculations
  - `ExternalAPIIntegration` — wrapper for a specific external API
- The Script Include name **must exactly match** the class name or function name

### Private Methods
By convention, prefix private (internal) methods with underscore:
```javascript
// Public (callable by consumers)
getUserDetails: function(userSysId) { ... },

// Private (internal implementation detail)
_buildUserQuery: function(userSysId) { ... },
_validateSysId: function(sysId) { ... },
```

### Error Handling
```javascript
getConfigValue: function(key) {
    try {
        var prop = gs.getProperty(key);
        if (JSUtil.nil(prop)) {
            gs.warn('IncidentUtils: Property {0} not found, using default', key);
            return this._getDefaultValue(key);
        }
        return prop;
    } catch(e) {
        gs.error('IncidentUtils.getConfigValue failed for key {0}: {1}', key, e.message);
        return '';
    }
},
```

### Logging
```javascript
initialize: function() {
    // Use a specific log source for filtering
    this._log = 'com.company.incident_utils';
},

myMethod: function(param) {
    gs.debug('{0}.myMethod called with param: {1}', this.type, param);
    // ...
},
```

### Testing
Script Includes can be tested via:
1. **Background Script:** Instantiate the class and call methods
2. **Fix Script:** Run a test scenario
3. **ATF (Automated Test Framework):** Unit tests via the ServiceNow test framework

```javascript
// Background script for quick testing:
var utils = new IncidentUtils();
var result = utils.getEscalationGroup('1', 'some_ci_sys_id');
gs.info('Escalation group result: ' + result);
```

---

## Common Script Include Patterns

### Configuration Wrapper
Centralizes system property access:
```javascript
var AppConfig = Class.create();
AppConfig.prototype = {
    initialize: function() {
        this._prefix = 'com.myapp.';
    },
    get: function(key, defaultValue) {
        return gs.getProperty(this._prefix + key, defaultValue || '');
    },
    getBoolean: function(key, defaultValue) {
        return gs.getProperty(this._prefix + key, String(defaultValue)) === 'true';
    },
    type: 'AppConfig'
};
```

### REST Integration Wrapper
Encapsulates all calls to a specific external API:
```javascript
var ExternalCMDBSync = Class.create();
ExternalCMDBSync.prototype = {
    initialize: function() {
        this._baseUrl = gs.getProperty('external.cmdb.url');
        this._apiKey = gs.getProperty('external.cmdb.apikey');
        this._lastError = '';
    },

    syncCI: function(ciSysId) {
        var rm = new sn_ws.RESTMessageV2();
        rm.setEndpoint(this._baseUrl + '/cis/' + ciSysId);
        rm.setHttpMethod('PUT');
        rm.setRequestHeader('Authorization', 'Bearer ' + this._apiKey);
        rm.setRequestBody(this._buildCIPayload(ciSysId));
        var response = rm.execute();
        if (response.getStatusCode() !== 200) {
            this._lastError = response.getErrorMessage();
            return false;
        }
        return true;
    },

    getLastError: function() { return this._lastError; },

    _buildCIPayload: function(ciSysId) {
        // Build JSON payload from CMDB data
        var gr = new GlideRecord('cmdb_ci');
        gr.get(ciSysId);
        return JSON.stringify({ name: gr.name.toString(), ip: gr.ip_address.toString() });
    },

    type: 'ExternalCMDBSync'
};
```
