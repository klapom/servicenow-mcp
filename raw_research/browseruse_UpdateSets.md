# UpdateSets

Source: browser-use task 84e000f6-2a72-4476-a07c-3b59e5aaedc7
Steps: 22 | Cost: $0.132 | Success: True

The official ServiceNow documentation and developer sites are currently inaccessible in this environment (stuck on loading screens). I have extracted the following information from alternative ServiceNow Community sources:

1) **Update Sets (Creating & Naming)**:
- Use naming conventions like `[Requirement ID] [Scope Acronym] [Increment]`.
- Naming should be descriptive (max 80 chars) to allow traceability.
- **Capturing & Committing**: Update sets capture configuration changes. Before committing, use 'Preview' to check for errors. If scope mismatches occur (e.g., global updates in a scoped update set), they must be resolved before committing.

2) **Application Scope**:
- **Global vs. Scoped**: Global is for legacy/base system changes; Scoped apps provide isolation and protection.
- **Scope Issues**: Mixing scopes in an update set causes commit errors. Prevention involves manual checks or automated tools to sort updates into correct sets.

3) **Best Practices & Governance**:
- **Batching**: Group multiple update sets (including across different scopes) under a single parent for easier deployment.
- **Instance Scan**: Run scans before moving update sets upstream to ensure best practices.
- **Backout Strategy**: Avoid 'Back Out' if possible; prefer 'Fix-Forward' strategies.
- **Data Capture**: Not all data is captured by default; use utilities like 'Add to Update Set' for records like schedules or system properties.

4) **Team Development & Source Control**:
- While specific details on Source Control integration were limited due to site access issues, it is recommended to use Update Set Batches for complex releases and to verify all child sets are completed before closing the parent batch.

I recommend the user check the official documentation directly for 'Scope protection policies' and 'Source control integration' once the site is accessible, as these require specific technical diagrams and tables not fully available in community summaries.
