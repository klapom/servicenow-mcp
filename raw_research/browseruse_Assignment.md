# Assignment

Source: browser-use task 84d49ca4-36d5-4de8-a79b-ac91b95d04b9
Steps: 24 | Cost: $0.144 | Success: True

I have extracted the following details regarding ServiceNow Assignment Rules and Auto-assignment:

1. **Assignment Rules (Core Platform):**
   - **Table:** Apply to task tables (e.g., Incident, Change).
   - **Conditions:** Automatically set `assigned_to` and `assignment_group` when specific conditions are met.
   - **Criteria:** Only run if the record is currently unassigned. They follow the 'first match' principle (lowest order runs first) and do not overwrite existing values.

2. **Data Lookup Rules:**
   - **Capabilities:** Can change any field value, not just assignment fields.
   - **Execution:** Can run on form change (unsaved changes), record insert, or update.
   - **Precedence:** Can be configured to replace existing values, unlike standard assignment rules.

3. **Rule Precedence:**
   - **Order:** 1) 'Before' Business Rules (order < 1000), 2) 'Before' Engines (includes Assignment Rules, Data Lookup, etc. in no specific order), 3) 'Before' Business Rules (order >= 1000), 4) Database Operation, 5) 'After' Business Rules/Engines.

4. **Advanced Work Assignment (AWA) & Skills-Based Routing:**
   - **Mechanism:** Automatically assigns work items based on agent availability, capacity, and skills.
   - **Routing:** Uses work item queues, routing conditions, and assignment criteria to 'push' work to qualified agents.

5. **Auto-assignment in Specific Modules:**
   - **Incident/Request:** Baseline rules exist to route based on category or item type (e.g., 'Network' category to 'Network' group).
   - **Service Catalog:** Requests can be assigned via specific rules or workflow engines.

6. **Agent Intelligence / Predictive Intelligence:**
   - While not detailed in the specific AWA landing page, it is used for predictive routing and auto-categorization to assist the assignment engines by predicting the correct assignment group based on short descriptions.

Note: Detailed 'round-robin' logic is typically handled within AWA assignment groups or via custom scripts in legacy assignment rules.
