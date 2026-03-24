# ACL

Source: browser-use task be0b0594-0e7a-4fcc-9aff-0c89af53b121
Steps: 27 | Cost: $0.162 | Success: True

The ServiceNow documentation site was inaccessible due to a persistent cross-origin cookie banner that blocked all automated interaction attempts. However, based on the information gathered from search results and official documentation snippets during the session, here is the summary for the requested topics:

1) **ACL Types**:
- **Record**: Most common type, controls access to table records.
- **Field**: Controls access to specific fields within a record.
- **client_callable_script_include**: Specifically for securing Script Includes that are called from the client side.
- **REST_endpoint**: Secures access to specific REST API endpoints.

2) **ACL Evaluation Order**:
- ServiceNow evaluates ACLs in a specific order: **Roles -> Conditions -> Script**. All three must evaluate to true for access to be granted.
- **Matching Order**: 
  1. `table.field` (Most specific)
  2. `parent_table.field`
  3. `*.field`
  4. `table.*`
  5. `parent_table.*`
  6. `*.*` (Least specific)

3) **OOB Roles**:
- **admin**: Full access to all system features and data.
- **itil**: Standard role for IT service management users (can create/update incidents, etc.).
- **itil_admin**: Higher level ITIL role with more management capabilities.
- **catalog_admin**: Manages the Service Catalog.
- **knowledge_admin**: Manages the Knowledge Base.

4) **Role Hierarchy**:
- Roles can contain other roles. If Role A contains Role B, any user assigned Role A automatically inherits all permissions of Role B.

5) **Row-level Security**:
- Implemented via 'Record' type ACLs where the field is set to '-- None --'. This controls whether a user can see the record at all.

6) **Contextual Security**:
- Refers to security that depends on the context of the request. 'Before' query business rules are often used alongside ACLs to filter data before it is even retrieved from the database, improving performance and security.

7) **Elevated Privileges**:
- Roles like `security_admin` require the user to manually 'elevate' their session to gain the permissions, even if they have the role assigned. This is a protection against accidental high-impact changes.

Due to the technical blocks on the ServiceNow documentation site (TrustArc iframe cross-origin restrictions), I could not extract the full text from every individual page as requested.
