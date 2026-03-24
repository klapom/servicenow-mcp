---
source_type: platform
topics:
  - REST API
  - Table API
  - Scripted REST API
  - Import Set API
  - Aggregate API
  - Attachment API
  - OAuth
  - authentication
  - integration
---

# REST API

## Overview

ServiceNow exposes a comprehensive REST API surface that enables external systems to read and write data, trigger processes, and integrate with the platform. The API layer covers standard table operations, aggregations, imports, attachments, and fully custom scripted endpoints.

All REST APIs are accessible at `https://<instance>.service-now.com/api/...` and support JSON as the primary content format. Authentication is required for all API calls.

---

## Authentication Methods

### Basic Authentication
Simple username/password authentication encoded in Base64:
```
Authorization: Basic base64(username:password)
```
Suitable for service accounts in non-production or lower-trust environments. Not recommended for production integrations — credentials are long-lived and revocation requires password change.

### OAuth 2.0 (Recommended)
OAuth 2.0 is the recommended authentication method for production integrations.

#### Flows Supported
| Flow | Use Case |
|------|---------|
| Authorization Code | User-interactive applications; user grants access |
| Client Credentials | System-to-system (machine-to-machine); no user interaction |
| Password (Resource Owner) | Legacy integrations; direct credential exchange |
| Refresh Token | Extending token validity without re-authentication |

#### Token Endpoints
```
POST /oauth_token.do        ← Obtain access token
POST /oauth_token.do        ← Refresh token (with grant_type=refresh_token)
POST /logout.do             ← Revoke token
```

#### OAuth Configuration in ServiceNow
- System OAuth → Application Registry: Create OAuth applications
- System OAuth → Manage Tokens: View active tokens
- System Properties → OAuth: Configure token expiry times

### Basic Auth for Service Accounts
Service accounts used for API access should:
- Have minimum required roles
- Not be tied to a real person (no personal email)
- Have login restrictions (IP allow-list if possible)
- Rotate passwords on a defined schedule

---

## Table API

The Table API is the primary interface for CRUD operations on any ServiceNow table.

**Base URL:** `/api/now/table/{tableName}`

### Operations

| Method | Endpoint | Operation |
|--------|----------|-----------|
| GET | `/api/now/table/{table}` | Query multiple records |
| GET | `/api/now/table/{table}/{sys_id}` | Get a single record by sys_id |
| POST | `/api/now/table/{table}` | Create a new record |
| PATCH | `/api/now/table/{table}/{sys_id}` | Update specific fields |
| PUT | `/api/now/table/{table}/{sys_id}` | Replace entire record |
| DELETE | `/api/now/table/{table}/{sys_id}` | Delete a record |

### Query Parameters (GET)

| Parameter | Description | Example |
|-----------|-------------|---------|
| `sysparm_query` | Encoded query string | `state=1^priority=2` |
| `sysparm_fields` | Comma-separated fields to return | `sys_id,number,state,priority` |
| `sysparm_limit` | Maximum records to return (default: 10, max: 10000) | `100` |
| `sysparm_offset` | Records to skip (for pagination) | `100` |
| `sysparm_display_value` | Return display values: `true`, `false`, `all` | `true` |
| `sysparm_exclude_reference_link` | Omit reference links from response | `true` |
| `sysparm_view` | Apply a specific form view | `mobile` |
| `sysparm_no_count` | Skip total count calculation (performance) | `true` |
| `sysparm_suppress_auto_sys_field` | Prevent auto-update of sys fields | `true` |

### Query Operators (sysparm_query)

| Operator | Description | Example |
|----------|-------------|---------|
| `=` | Equals | `state=2` |
| `!=` | Not equals | `state!=6` |
| `>` | Greater than | `priority>2` |
| `<` | Less than | `sys_created_on<2024-01-01` |
| `>=` | Greater than or equal | `priority>=2` |
| `IN` | In list | `state IN 1,2,3` |
| `NOT IN` | Not in list | `state NOT IN 6,7` |
| `STARTSWITH` | Starts with string | `number STARTSWITH INC` |
| `CONTAINS` | Contains string | `short_description CONTAINS email` |
| `ISEMPTY` | Field is null/empty | `assignment_group ISEMPTY` |
| `ISNOTEMPTY` | Field has a value | `assignment_group ISNOTEMPTY` |
| `^` | AND condition | `state=2^priority=1` |
| `^OR` | OR condition | `state=1^ORstate=2` |
| `ORDERBY` | Sort ascending | `ORDERBY sys_created_on` |
| `ORDERBYDESC` | Sort descending | `ORDERBYDESC priority` |

### Example: Create an Incident

**Request:**
```http
POST /api/now/table/incident HTTP/1.1
Host: instance.service-now.com
Authorization: Bearer {access_token}
Content-Type: application/json
Accept: application/json

{
    "short_description": "Cannot access VPN from home office",
    "caller_id": "6816f79cc0a8016401c5a33be04be441",
    "category": "network",
    "subcategory": "vpn",
    "impact": "2",
    "urgency": "2",
    "description": "User reports VPN connection drops every 10 minutes..."
}
```

**Response (201 Created):**
```json
{
    "result": {
        "sys_id": "1234567890abcdef1234567890abcdef",
        "number": "INC0045678",
        "state": {"value": "1", "display_value": "New"},
        "priority": {"value": "3", "display_value": "Moderate"}
    }
}
```

### Example: Query Open P1 Incidents

```http
GET /api/now/table/incident?sysparm_query=state%3D2%5Epriority%3D1&sysparm_fields=number,short_description,assigned_to,sys_created_on&sysparm_display_value=true&sysparm_limit=50
```

### sysparm_display_value Behavior

| Setting | Value Field | Link Field |
|---------|------------|-----------|
| `false` (default) | Raw value (sys_id for references, integer for choices) | Yes |
| `true` | Display value only (human-readable) | No |
| `all` | Both raw and display value | No |

**Example with `sysparm_display_value=all`:**
```json
{
    "state": {
        "value": "2",
        "display_value": "In Progress"
    },
    "assignment_group": {
        "value": "d625dccec0a8016700a222a0f7900d9b",
        "display_value": "Service Desk",
        "link": "https://instance.service-now.com/api/now/table/sys_user_group/d625dccec0..."
    }
}
```

---

## Aggregate API

The Aggregate API performs COUNT, SUM, MIN, MAX, AVG operations without returning full records.

**Base URL:** `/api/now/stats/{tableName}`

| Parameter | Description |
|-----------|-------------|
| `sysparm_count` | Include total count (true/false) |
| `sysparm_avg_fields` | Comma-separated fields to average |
| `sysparm_sum_fields` | Comma-separated fields to sum |
| `sysparm_min_fields` | Comma-separated fields to get min |
| `sysparm_max_fields` | Comma-separated fields to get max |
| `sysparm_group_by` | Group results by this field |
| `sysparm_query` | Filter conditions (same as Table API) |

**Example: Count open incidents by priority:**
```http
GET /api/now/stats/incident?sysparm_count=true&sysparm_group_by=priority&sysparm_query=state%3D2
```

---

## Import Set API

Loads data into a staging (import set) table for transformation and insertion into target tables.

**Base URL:** `/api/now/import/{stagingTableName}`

```http
POST /api/now/import/u_my_import_table
Content-Type: application/json

{
    "u_hostname": "web-server-01",
    "u_ip_address": "192.168.1.100",
    "u_environment": "production"
}
```

Response includes transformation result: `inserted`, `updated`, `ignored`, `error`.

---

## Attachment API

Manage file attachments on records.

**Base URL:** `/api/now/attachment`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/now/attachment?table_name=incident&table_sys_id={id}` | List attachments |
| GET | `/api/now/attachment/{sys_id}/file` | Download attachment content |
| POST | `/api/now/attachment/file` | Upload attachment |
| DELETE | `/api/now/attachment/{sys_id}` | Delete attachment |

**Upload attachment:**
```http
POST /api/now/attachment/file?table_name=incident&table_sys_id=abc123&file_name=error.log
Content-Type: text/plain
Content-Length: 1234

[file content as binary or text]
```

---

## Scripted REST APIs

Scripted REST APIs allow developers to create fully custom REST endpoints with custom URL paths, HTTP methods, and scripted request handling.

### Creating a Scripted REST API
1. Navigate to System Web Services → Scripted REST APIs
2. Create a new API with Name and API ID (used in URL)
3. Add **Resources** (individual endpoints with path, method, and script)

### URL Structure
```
/api/{namespace}/{api_id}/{resource_path}
```
Example: `/api/mycompany/incident_integrations/bulk_update`

### Resource Script Context

```javascript
(function process(/*RESTAPIRequest*/ request, /*RESTAPIResponse*/ response) {

    // Read path parameters
    var incidentId = request.pathParams.incident_id;

    // Read query parameters
    var format = request.queryParams.format || 'json';

    // Read request body (JSON)
    var body = request.body.data;

    // Process
    var gr = new GlideRecord('incident');
    if (!gr.get(incidentId)) {
        response.setStatus(404);
        response.setBody({ error: 'Incident not found', sys_id: incidentId });
        return;
    }

    // Build response
    response.setStatus(200);
    response.setHeader('Content-Type', 'application/json');
    response.setBody({
        number: gr.number.toString(),
        state: gr.getDisplayValue('state'),
        priority: gr.getDisplayValue('priority'),
        assigned_to: gr.assigned_to.getDisplayValue()
    });

})(request, response);
```

### RESTAPIRequest Methods

| Method | Description |
|--------|-------------|
| `request.body.data` | Parsed JSON body (object) |
| `request.body.dataString` | Raw body string |
| `request.body.dataStream` | Body as input stream |
| `request.pathParams.{name}` | URL path parameter |
| `request.queryParams.{name}` | Query string parameter |
| `request.getHeader(name)` | Get request header value |
| `request.uri` | Full request URI |
| `request.httpMethod` | GET, POST, PUT, etc. |

### RESTAPIResponse Methods

| Method | Description |
|--------|-------------|
| `response.setStatus(code)` | HTTP status code (200, 201, 400, 404, 500) |
| `response.setBody(object)` | Set JSON response body |
| `response.setHeader(name, value)` | Set response header |
| `response.setContentType(type)` | Set Content-Type header |
| `response.setError(error)` | Return standard error response |

---

## REST Message (Outbound REST)

ServiceNow can make outbound REST calls to external systems using REST Messages.

### REST Message Configuration
1. Navigate to System Web Services → Outbound → REST Messages
2. Create REST Message with base URL
3. Add HTTP methods (GET, POST, PUT, DELETE) with endpoint paths
4. Configure authentication (Basic, OAuth, MutualAuth)

### Calling via Script

```javascript
// In a Business Rule, Script Include, or Flow Designer script step:
var rm = new sn_ws.RESTMessageV2('MyExternalAPI', 'createTicket');
rm.setStringParameterNoEscape('external_id', current.number.toString());
rm.setStringParameterNoEscape('summary', current.short_description.toString());
rm.setStringParameterNoEscape('priority', current.priority.toString());

var response = rm.execute();
var statusCode = response.getStatusCode();
var responseBody = response.getBody();

if (statusCode == 200 || statusCode == 201) {
    var parsedBody = JSON.parse(responseBody);
    current.correlation_id = parsedBody.ticketId;
    gs.info('External ticket created: ' + parsedBody.ticketId);
} else {
    gs.error('External API call failed: HTTP {0} — {1}', statusCode, responseBody);
}
```

### Dynamic REST Calls (No REST Message Record)

```javascript
var rm = new sn_ws.RESTMessageV2();
rm.setEndpoint('https://api.external.com/v1/tickets');
rm.setHttpMethod('POST');
rm.setRequestHeader('Content-Type', 'application/json');
rm.setRequestHeader('Authorization', 'Bearer ' + gs.getProperty('external.api.token'));
rm.setRequestBody(JSON.stringify({
    title: current.short_description.toString(),
    priority: current.priority.toString()
}));

rm.setHttpTimeout(30000); // 30 second timeout

try {
    var response = rm.execute();
    gs.info('Response: ' + response.getBody());
} catch(ex) {
    gs.error('REST call failed: ' + ex.getMessage());
}
```

---

## Rate Limiting and Throttling

ServiceNow implements rate limiting on REST API endpoints:

| Limit Type | Default | Notes |
|-----------|---------|-------|
| Requests per hour | Varies by license | Check instance property `glide.rest.rate_limiter` |
| Concurrent connections | Instance-level cap | Prevents API from overwhelming instance |
| Record limit per call | 10,000 (Table API) | Use pagination for larger datasets |
| Response size | Configurable | Large responses may be paginated automatically |

### Pagination Pattern
```http
# First page
GET /api/now/table/incident?sysparm_limit=100&sysparm_offset=0

# Second page
GET /api/now/table/incident?sysparm_limit=100&sysparm_offset=100

# Third page
GET /api/now/table/incident?sysparm_limit=100&sysparm_offset=200
```

Response headers include `X-Total-Count` for total record count when `sysparm_no_count=false`.

---

## Response Codes

| Code | Meaning |
|------|---------|
| 200 OK | Successful GET, PUT, PATCH |
| 201 Created | Successful POST (record created) |
| 204 No Content | Successful DELETE |
| 400 Bad Request | Invalid request (malformed query, missing required field) |
| 401 Unauthorized | Invalid or missing credentials |
| 403 Forbidden | Authenticated but lacks ACL permission |
| 404 Not Found | Record or endpoint not found |
| 405 Method Not Allowed | HTTP method not supported on endpoint |
| 429 Too Many Requests | Rate limit exceeded |
| 500 Internal Server Error | Server-side error |

---

## Security Considerations

### ACL for API Access
REST API calls are subject to the same ACL rules as UI access:
- If a user lacks READ access to a field, the field is omitted from API responses
- If a user lacks WRITE access, PATCH/PUT will fail with 403 for that field
- Admin role bypasses ACLs by default

### Scripted REST API Security
Protect custom endpoints with:
```javascript
// Check role at start of resource script
if (!gs.hasRole('my_api_consumer_role')) {
    response.setStatus(403);
    response.setBody({ error: 'Insufficient permissions' });
    return;
}
```

Or configure ACLs on the Scripted REST API resource directly (REST_endpoint type ACLs).

### Field Exclusion for Sensitive Data
Specify `sysparm_fields` to limit response to only needed fields — reduces exposure of sensitive data and improves performance.

---

## Best Practices

### API Integration Design
- Always use service accounts (not personal accounts) for integrations
- Implement OAuth 2.0 with client credentials for system-to-system integrations
- Rotate API credentials on a defined schedule
- Log all API errors for monitoring

### Performance
- Always specify `sysparm_fields` — returning all fields is wasteful
- Use `sysparm_no_count=true` for large table queries where total count isn't needed
- Implement pagination for queries that may return more than 100 records
- Cache authentication tokens until expiry rather than re-authenticating per request

### Error Handling
- Check HTTP status codes before parsing response body
- Implement retry logic with exponential backoff for transient errors (5xx)
- Do not retry on 4xx errors (client errors) without fixing the request first
- Log correlation IDs (`X-Request-ID`) for troubleshooting
