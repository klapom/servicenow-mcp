# TableHierarchy

Source: browser-use task 06582783-7ac1-4d23-815e-d61593fa4194
Steps: 27 | Cost: $0.162 | Success: True

The ServiceNow documentation site (docs.servicenow.com) failed to load the requested content, remaining stuck on a 'Loading application' screen across multiple attempts and direct URLs. Additionally, search engine tools were blocked by CAPTCHAs. Based on standard ServiceNow technical architecture, here is the information requested:

1) **Task Table Hierarchy**: The `task` table is the base table. Common extensions include:
   - `incident`
   - `problem`
   - `change_request`
   - `sc_req_item` (Requested Item)
   - `sc_task` (Catalog Task)
   - `kb_submission` (Knowledge Submission)
   - `hr_case` (HR Case)
   - `vtb_card` (Visual Task Board Card)

2) **Table Extension/Inheritance Model**:
   - **Table Per Class (TPC)**: Each table in the hierarchy has its own physical database table. Fields unique to the child are stored in the child's table.
   - **Table Per Hierarchy (TPH)**: Also known as 'Flattening'. The entire hierarchy is stored in a single physical database table (e.g., all task data in one big table). This improves performance for reporting across the hierarchy but has column limits.

3) **Field Inheritance**: Child tables inherit all fields from their parent tables. A field defined on the `task` table (like `short_description` or `number`) is automatically available and functional on the `incident` table. Changes to a parent field's configuration (like a label change) propagate down unless overridden by a 'Dictionary Override'.

4) **System Tables**:
   - `sys_db_object`: Contains a record for every table in the instance. Used to define table names, labels, and extensions.
   - `sys_dictionary`: Contains the definition for every field on every table. It defines data types, lengths, and default values.

5) **Dot-walking and Relationships**:
   - **Dot-walking**: A method to access fields on related tables through a reference field (e.g., `incident.caller_id.email` to get the email of the user who raised the incident).
   - **Relationships**: Defined via Reference fields (One-to-Many) or Many-to-Many (m2m) tables.

6) **Other Base System Tables**:
   - `sys_user`: Stores user records.
   - `sys_user_group`: Stores user groups.
   - `core_company`: Stores company records (vendors, customers, etc.).
   - `cmn_location`: Stores physical locations.
