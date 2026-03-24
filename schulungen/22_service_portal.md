---
source_type: platform
topics:
  - service portal
  - widgets
  - AngularJS
  - portal configuration
  - self-service
  - employee center
  - sp_config
---

# Service Portal

## Overview

Service Portal is ServiceNow's end-user self-service interface. Built on AngularJS, it provides a modern, responsive web experience where employees can submit requests, search knowledge, track their tickets, and interact with IT and other service departments — all without requiring access to the main ServiceNow administrative UI.

Service Portal is configured via the `/sp_config` page and implemented through a portal-page-widget hierarchy. Each portal has its own URL suffix, branding, and collection of pages.

---

## Architecture

### Hierarchy

```
Portal
  └── Pages (1..n)
        └── Containers (layout rows)
              └── Columns (layout columns)
                    └── Widget Instances (1..n)
                          └── Widgets (base definition)
```

### Portal (`sp_portal`)
A named collection of pages with:
- Unique URL suffix (e.g., `/sp` for default portal)
- Associated theme (CSS variables, fonts, colors)
- Default home page
- Header widget
- Footer widget
- User and guest authentication behavior
- Default knowledge base

### Pages (`sp_page`)
Independent content containers identified by a `page_id`:
- Pages exist independently of portals (a page can be used in multiple portals)
- URL routing: `https://instance/sp?id=kb_home` → loads page with `page_id=kb_home`
- Pages store layout: containers (rows) and columns
- Each page has a `page_id` used in URL navigation

### Widgets (`sp_widget`)
Self-contained UI components — the fundamental building block of Service Portal:
- Each widget has: HTML template, Client Script (controller), Server Script, CSS, and option schema
- **Widget Instance** (`sp_instance`): A specific placement of a widget on a page, with its own configuration options

### Themes
Define the visual appearance:
- CSS variables (colors, fonts, spacing)
- Bootstrap-based responsive framework
- Can override at portal level or widget level

---

## Portal Configuration

### Accessing Configuration

**URL:** Append `/sp_config` to your instance URL: `https://instance.service-now.com/sp_config`

Or: Service Portal → Service Portal Configuration

### Configuration Tiles

| Tile | Purpose |
|------|---------|
| Branding Editor | Edit portal name, logo, colors, fonts |
| Pages | Manage all pages in the portal |
| Designer | Visual drag-and-drop page editor |
| Page Editor | Edit individual pages and their widget layout |
| CSS Editor | Edit portal-level custom CSS |
| Portals | Manage multiple portals on the instance |

### Creating a New Portal
1. Go to `/sp_config` → Portals → New
2. Set URL suffix, title, homepage
3. Assign theme
4. Configure header/footer widgets
5. Add pages via Pages tile or Designer

---

## Widget Architecture

### Four Components of a Widget

#### 1. HTML Template
AngularJS template for rendering:
```html
<div class="panel panel-default">
  <div class="panel-heading">{{::data.title}}</div>
  <div class="panel-body">
    <p ng-repeat="item in data.items track by $index">
      {{item.name}} — {{item.priority}}
    </p>
    <button ng-click="c.submitRequest()">Request Now</button>
  </div>
</div>
```

#### 2. Client Script (AngularJS Controller)
Runs in the browser. Handles user interaction and bidirectional data binding:
```javascript
function($scope, $http, spUtil) {
    var c = this;
    // c.data is bound to the server script's data object

    c.submitRequest = function() {
        // Send data back to server script
        c.server.update().then(function() {
            // Server has processed; c.data is refreshed
            spUtil.addTrivialMessage(c.data.confirmation_message);
        });
    };

    c.filterItems = function(searchTerm) {
        c.data.filter = searchTerm;
        c.server.update(); // Re-run server script with new filter
    };
}
```

#### 3. Server Script
Runs on the server when the widget is first loaded and on `server.update()` calls:
```javascript
(function() {
    // data object is shared between server and client scripts
    data.title = 'Open Incidents';
    data.confirmation_message = '';

    // Query incidents
    var filter = input ? input.filter : '';
    var gr = new GlideRecord('incident');
    gr.addQuery('caller_id', gs.getUserID());
    gr.addQuery('state', 'NOT IN', '6,7,8'); // Active states
    if (filter) {
        gr.addQuery('short_description', 'CONTAINS', filter);
    }
    gr.orderByDesc('priority');
    gr.query();

    data.items = [];
    while (gr.next()) {
        data.items.push({
            sys_id: gr.sys_id.toString(),
            number: gr.number.toString(),
            name: gr.short_description.toString(),
            priority: gr.getDisplayValue('priority'),
            state: gr.getDisplayValue('state'),
            link: '/sp?id=record&table=incident&sys_id=' + gr.sys_id
        });
    }

    // Handle form submission from client
    if (input && input.action === 'submitRequest') {
        // process the request
        data.confirmation_message = 'Your request has been submitted!';
    }
})();
```

#### 4. CSS (Widget-Scoped)
CSS that applies only within the widget's DOM scope:
```css
.panel-heading {
    background-color: #0070d2;
    color: white;
}
.priority-1 { color: red; font-weight: bold; }
.priority-2 { color: orange; }
```

### Server-Client Data Flow

```
Page Load:
  Server Script runs → populates data object
  data sent to client
  AngularJS template renders using data values

User Interaction:
  Client Script sets input object values
  c.server.update() called
  Server Script runs again (with input available)
  Updated data sent back to client
  Template re-renders
```

---

## Widget Options (Option Schema)

Widgets can be configured with options — parameters that customize behavior without code changes:

```javascript
// Option Schema definition (JSON):
[
    {
        "name": "max_items",
        "label": "Maximum Items",
        "hint": "Maximum number of items to display",
        "default_value": "10",
        "type": "integer"
    },
    {
        "name": "show_priority",
        "label": "Show Priority",
        "default_value": "true",
        "type": "boolean"
    }
]
```

Accessing in server script:
```javascript
var maxItems = options.max_items || 10;
var showPriority = options.show_priority !== 'false';
```

**Widget Instances** store unique option values — the same base widget can be used multiple times on a page with different configurations.

---

## AngularJS Providers

Angular Providers are shared services that can be injected into multiple widgets on the same page:

| Type | Description |
|------|-------------|
| Factory | Returns a function or object |
| Service | Returns a class instance |
| Directive | DOM manipulation |

### Registration
Navigate to Service Portal → Angular Providers

```javascript
// Provider name: 'NavigationService'
function($rootScope, spModal) {
    return {
        goToRecord: function(table, sysId) {
            $rootScope.$emit('sp.navigate', {
                id: 'record',
                table: table,
                sys_id: sysId
            });
        }
    };
}
```

Usage in widget client script:
```javascript
function($scope, NavigationService) {
    var c = this;
    c.openRecord = function(item) {
        NavigationService.goToRecord('incident', item.sys_id);
    };
}
```

---

## URL Structure and Routing

```
https://<instance>/<portal_suffix>?id=<page_id>&<parameters>
```

Examples:
```
https://company.service-now.com/sp?id=index                  # Home page
https://company.service-now.com/sp?id=sc_home               # Catalog
https://company.service-now.com/sp?id=kb_home               # Knowledge
https://company.service-now.com/sp?id=catalog_item&sys_id=abc123  # Specific catalog item
https://company.service-now.com/sp?id=record&table=incident&sys_id=def456  # Specific incident
```

### Deep Links
Most Service Portal pages support deep links via URL parameters. Bookmarkable links can be shared directly to specific items or records.

---

## Service Portal vs. Employee Center

### Service Portal
- Older platform; based on AngularJS
- Typically department-specific portals (IT portal, HR portal)
- Requires manual topic page creation
- Content is siloed — each portal has its own search scope
- Starting point: built from demo portal design
- Good for: simple, focused departmental portals

### Employee Center (EC)
- Modern, recommended for new deployments
- Uses unified taxonomy for AI Search across all departments
- Multi-departmental: one portal for IT, HR, Finance, Facilities
- Topic-based navigation with automated content population
- Built-in Knowledge, Catalog, and Community features
- Requires Employee Center plugin
- Best for: enterprise-wide employee self-service

**Decision guidance:** New portal implementations should use Employee Center. Service Portal is appropriate for maintaining existing portals and specialized use cases.

---

## Performance Optimization

### Performance Analyzer
Available at: `/sp_config` → Performance Analyzer

Benchmarks portal pages against:
- Widget load time
- ACL execution time
- Database call execution time
- Total page load time

### Optimization Techniques

| Technique | Impact |
|-----------|--------|
| Move GlideRecord queries from server script to deferred loading | Reduces initial page load |
| Use `gr.setLimit()` on all queries | Prevents large data loads |
| Cache reference data in GlideCache or system properties | Reduces repeated queries |
| Minimize synchronous `server.update()` calls | Reduces round trips |
| Use `$http` with REST API for data that doesn't need session context | Can be cached by browser |
| Lazy-load below-the-fold widgets | Defers non-critical widget loading |

### Common Performance Pitfalls
- Server scripts with unfiltered GlideRecord queries on large tables
- Heavy ACL evaluation on frequently-accessed widgets
- Multiple `server.update()` calls triggered by single user action
- Widget loading all records when only 10-20 will be displayed

---

## Security in Service Portal

### Access Control
- Service Portal respects all ACLs — users can only see data they have access to
- Portal-level access: set login policy on the portal record (login required, guest allowed)
- Widget-level: check `gs.isLoggedIn()` in server script for authenticated content

```javascript
// Server script: ensure user is logged in
if (!gs.isLoggedIn()) {
    data.error = 'Authentication required';
    return;
}
```

### Guest Access
- Some portals allow anonymous (guest) access for public knowledge bases
- Guest users get a limited role (typically `guest` or `public`)
- Sensitive widgets should check `gs.hasRole('some_role')` in server script

---

## Best Practices

### Widget Development
- Keep widgets single-purpose — a widget for displaying a list, a separate widget for form submission
- Use option schemas for any configurable values — avoid hardcoding
- Test on mobile viewports — Service Portal uses Bootstrap's responsive grid
- Minimize server round trips — load data needed for interaction in the initial load

### Portal Governance
- Assign a portal owner responsible for content and maintenance
- Review and remove obsolete pages and widgets annually
- Monitor portal usage analytics to understand which pages and items are most used
- Keep catalog items up to date — outdated items erode user trust in the portal

---

## Common Patterns

### Catalog Item Landing Page

**Page:** `sc_cat_item`
**Key widgets:**
1. **Catalog Item widget:** Form variables, "Add to Cart" / "Request Now" button
2. **Knowledge Articles widget:** Related articles for this item
3. **Popular Items widget:** What others frequently request

### My Requests Page

**Page:** `my_requests`
**Key widgets:**
1. **Requested Items widget:** List of user's open/recent RITMs with state and stage
2. **Quick Status widget:** Summary counts (pending approval, in progress, fulfilled)
3. **Request Details widget:** Individual RITM detail view

### Knowledge Home Page

**Page:** `kb_home`
**Key widgets:**
1. **Knowledge Base List:** Browsable knowledge bases
2. **Top Articles widget:** Most viewed articles
3. **Search widget:** Full-text knowledge search with filters
4. **Recent Articles widget:** Newly published articles
