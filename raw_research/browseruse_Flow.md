# Flow

Source: browser-use task 21811f8d-6eaf-4754-b6e5-7c809c986953
Steps: 29 | Cost: $0.174 | Success: True

I have extracted comprehensive documentation for ServiceNow Flow Designer from the official documentation site. 

Key Findings:
1. **Overview**: Flow Designer is a no-code automation tool on the ServiceNow AI Platform, recommended over legacy workflows.
2. **Flow Designer vs. Business Rules**: Use Flow Designer unless specific execution sequencing with other Business Rules is required, or logic must run immediately before/after database writes in the same thread.
3. **Flows, Subflows, and Actions**: 
   - Flows are automated workflows triggered by conditions.
   - Subflows and Actions are modular components managed within Workflow Studio.
4. **Triggers**:
   - **Record-based**: Created, Updated, or Created/Updated.
   - **Schedule-based**: Daily, Weekly, Monthly, Run Once, and Repeat.
   - **Application-based**: Includes Service Catalog, SLA Task, Kafka Message, and MetricBase.
5. **Flow Logic**:
   - **If**: Conditional execution.
   - **For Each**: Loop through a list of records.
   - **Do the following until**: Repeat until a condition is met.
   - **Do the following in parallel**: Run separate paths simultaneously.
6. **Architecture & Best Practices**: Emphasizes single-purpose flows, reusability via subflows, and using connection aliases for IntegrationHub.

Note: Due to step limits, the specific migration guide for legacy Workflow Editor and detailed integration steps for Incident/Change were not fully extracted, but the overview confirms Flow Designer is the primary tool for these processes moving forward.
