# CMDB_v2

Source: browser-use task c25fa492-13c2-4255-8385-1c80eb478a16
Steps: 31 | Cost: $0.186 | Success: True

I have successfully extracted all requested information from the ServiceNow documentation:

1. **CMDB Overview**: Extracted the core purpose of CMDB, key features (Health, Identification and Reconciliation, Data Manager), and the 'Get started' guide for exploring, configuring, and managing CIs.
2. **CI Relationships**: Extracted a comprehensive table of relationship types including 'Runs on', 'Depends on', 'Hosted on', 'Contains', 'Manages', and others, along with their parent/child roles and descriptions.
3. **CMDB Table Hierarchy**: Identified the base hierarchy where 'cmdb' (Base Configuration Item) is the root for non-IT CIs, and 'cmdb_ci' (Configuration Item) is the root for IT CIs. Key sub-classes include Hardware, Computer, Server (and specialized servers like UNIX), Database, and Cloud classes.
4. **CSDM (Common Service Data Model)**: Extracted the landing page content explaining the CSDM framework, its role in ensuring data resides in appropriate tables for maximum AI Platform value, and the key principles (simplified concepts, design for reporting, prescribed relationships, etc.).

All data was extracted from the 'Australia' release version of the documentation as of March 2026.
