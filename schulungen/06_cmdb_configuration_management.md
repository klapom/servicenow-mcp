---
source_type: process
topics:
  - CMDB
  - configuration management
  - configuration items
  - CI relationships
  - CSDM
  - service mapping
  - identification and reconciliation
---

# CMDB and Configuration Management

## Overview

The Configuration Management Database (CMDB) is the central repository that stores information about all Configuration Items (CIs) in the IT environment and the relationships between them. It is the foundational data layer that powers Incident, Problem, Change, and Service Management processes.

The **Common Service Data Model (CSDM)** provides the prescriptive framework for how data should be organized within the CMDB to maximize the value of ServiceNow's AI Platform applications and ensure consistent, accurate service reporting.

---

## Core CMDB Concepts

### What is a Configuration Item (CI)?
A CI is any component of the IT environment that needs to be managed in order to deliver an IT service. CIs can be:
- Physical hardware (servers, routers, workstations)
- Virtual components (VMs, containers)
- Software (applications, databases, middleware)
- Services (business services, application services)
- Logical components (IP addresses, certificates)
- Documentation (records, configurations)

### What the CMDB Enables
| Capability | Business Value |
|-----------|---------------|
| Impact analysis | "If this server fails, which services are affected?" |
| Root cause analysis | "What changed on this CI before the incident started?" |
| Change risk assessment | "What other CIs depend on this one?" |
| Service mapping | Visualize end-to-end service topology |
| License management | Track software installations against entitlements |
| Compliance reporting | Demonstrate control over the IT environment |

---

## CMDB Table Hierarchy

### Base Table Architecture

The CMDB uses table inheritance (Table Per Class model):

```
cmdb                    ← Base CI (non-IT CIs: contracts, facilities)
  └── cmdb_ci           ← Base IT CI (root of all IT configuration items)
        ├── cmdb_ci_hardware
        │     ├── cmdb_ci_computer
        │     │     ├── cmdb_ci_server
        │     │     │     ├── cmdb_ci_unix_server
        │     │     │     ├── cmdb_ci_win_server
        │     │     │     └── cmdb_ci_linux_server
        │     │     └── cmdb_ci_pc (workstation)
        │     ├── cmdb_ci_storage
        │     └── cmdb_ci_network_adapter
        ├── cmdb_ci_network_gear
        │     ├── cmdb_ci_router
        │     ├── cmdb_ci_switch
        │     └── cmdb_ci_firewall
        ├── cmdb_ci_database
        │     ├── cmdb_ci_db_instance
        │     └── cmdb_ci_db_catalog
        ├── cmdb_ci_appl (Application)
        │     ├── cmdb_ci_app_server
        │     └── cmdb_ci_web_server
        ├── cmdb_ci_service (Service classes)
        │     ├── cmdb_ci_service_discovered
        │     └── cmdb_ci_service_auto
        └── cmdb_ci_cloud (Cloud infrastructure)
              ├── cmdb_ci_vm_instance
              └── cmdb_ci_cloud_service_account
```

### Key CI Classes

| Table Name | Label | Typical Instances |
|-----------|-------|-----------------|
| `cmdb_ci_server` | Server | Physical servers |
| `cmdb_ci_unix_server` | UNIX Server | Linux/AIX/Solaris servers |
| `cmdb_ci_win_server` | Windows Server | Windows servers |
| `cmdb_ci_computer` | Computer | Workstations, laptops |
| `cmdb_ci_database` | Database | DB catalog |
| `cmdb_ci_db_instance` | Database Instance | Oracle, SQL Server, MySQL instances |
| `cmdb_ci_appl` | Application | Deployed application instances |
| `cmdb_ci_network_gear` | Network Gear | Switches, routers, firewalls |
| `cmdb_ci_ip_router` | IP Router | Routing infrastructure |
| `cmdb_ci_firewall` | Firewall | Network security appliances |
| `cmdb_ci_storage_server` | Storage Server | SAN/NAS systems |
| `cmdb_ci_vm_instance` | Virtual Machine Instance | VMware, Hyper-V VMs |
| `cmdb_ci_cloud_service_account` | Cloud Service Account | AWS accounts, Azure subscriptions |

---

## CI Relationships

Relationships define how CIs are connected. They are stored in the `cmdb_rel_ci` table.

### Standard Relationship Types

| Relationship Type | Direction | Description |
|-----------------|-----------|-------------|
| Runs on | Parent runs on Child | Application runs on Server |
| Depends on | Parent depends on Child | Service depends on Database |
| Hosted on | Parent hosted on Child | VM hosted on Physical Host |
| Contains | Parent contains Child | Rack contains Server |
| Manages | Parent manages Child | Load Balancer manages Web Servers |
| Connects to | Parent connects to Child | Switch connects to Server |
| Provided by | Parent provided by Child | Service provided by Application |
| Uses | Parent uses Child | Application uses Database |
| Members of | Child is member of Parent | Server member of Cluster |
| Instantiates | Parent instantiates Child | Template instantiates VM |
| Virtualized by | Physical virtualized by Hypervisor | Server virtualized by VMware |

### Relationship Direction
Relationships are directional and affect how impact analysis and service maps are rendered:
- **Parent:** The upstream component in the dependency
- **Child:** The downstream component that the parent depends on

Example:
```
[SAP Application] ──Runs on──► [App Server]
[App Server] ──Depends on──► [Oracle DB Instance]
[Oracle DB Instance] ──Runs on──► [Database Server]
[App Server] ──Hosted on──► [VMware VM]
[VMware VM] ──Hosted on──► [Physical Host]
```

---

## CMDB Health, Identification, and Reconciliation

### CMDB Health
ServiceNow provides CMDB Health dashboards that track:
- **Completeness:** Are required fields populated? (e.g., does every server have a "Managed by group"?)
- **Correctness:** Are CI classes used appropriately?
- **Compliance:** Does data align with CSDM guidelines?
- **Staleness:** Are CIs being updated or are they aging without discovery runs?

### Identification and Reconciliation (IRE)

IRE is the engine that governs how discovered CI data is matched to existing CMDB records and merged from multiple sources.

**IRE Rules:**
1. **Identifier Rules:** Define how to match incoming data to existing CIs (e.g., match Server by `serial_number` OR `name + IP`)
2. **Reconciliation Rules:** When multiple discovery sources provide data for the same CI, which source wins for each field?

**Discovery Sources (precedence order):**
1. ServiceNow Discovery (highest trust)
2. SCCM / Intune
3. VMware vCenter
4. Manual entry (lowest trust)

If two sources disagree on a field value, the reconciliation rules determine which source is authoritative for that field.

---

## Common Service Data Model (CSDM)

### What is CSDM?
CSDM is a standard framework that prescribes which ServiceNow tables should store which types of data and how entities should relate to each other. Following CSDM ensures:
- Maximum value from ServiceNow AI features
- Consistent reporting across the enterprise
- Interoperability between ServiceNow applications
- Predictable upgrade paths

### CSDM Layers (Domains)

| Layer | Key Entities | Purpose |
|-------|-------------|---------|
| Foundation | Users, Groups, Locations, Companies, Products | Base referential data; used across all domains |
| Design & Planning | Business Capabilities, Business Applications, Information Objects | How the business designs and plans digital products |
| Build & Integration | SDLC Components, AI System Digital Assets | Development and build artifacts |
| Service Delivery | Service Instances (Application Services), Technology Management Services | Operational runtime environment |
| Service Consumption | Service Catalogs, Business Services, Offerings | How consumers access services |
| Manage Portfolio | Business Application portfolio oversight | Executive-level service portfolio view |

### Key CSDM Entity Types

#### Business Capability
- High-level, conceptual capability the organization needs
- Example: "Manage Payroll", "Process Customer Orders"
- Used for strategic planning and investment decisions
- Does NOT represent a deployed system

#### Business Application (`cmdb_ci_business_app`)
- Represents a logical software application (the product)
- Example: SAP, Workday, Salesforce CRM
- Bridges business capability to deployed technology

#### Application Service / Service Instance (`cmdb_ci_service_auto`)
- A deployed instance of a Business Application
- Example: "SAP Production", "Workday HR US"
- This is the entity linked to Incidents, Problems, and Changes
- Contains the CI relationship map showing servers, databases, middleware

#### Business Service (`cmdb_ci_service`)
- A service delivered to business users
- Example: "Manage HR" (which is powered by Workday)
- Published in the Service Catalog as an offering
- Higher-level than Application Service

#### Technology Management Service (Technical Service)
- Underpins business services; managed by technical teams
- Example: "Email Infrastructure Service" (supporting "Email" business service)

#### Service Offering
- A stratification of a service by options
- Example: "Manage Onboarding" as an offering of "Manage HR"
- Can vary by geography, support level, or environment

### CSDM Relationship Chain

```
Business Capability
    └── provides/supports ──►  Business Application
                                    └── instantiated as ──►  Application Service
                                                                  └── depends on ──►  Server, DB, Network CIs
                                    └── offered as ──►  Business Service
                                                           └── has offering ──►  Service Offering
```

### CSDM Implementation Stages

| Stage | Focus | CI Types |
|-------|-------|---------|
| Foundation | Basic referential data quality | Users, Groups, Locations correct |
| Crawl | Basic ITSM support | Business Applications + Service Instances for key services |
| Walk | Extended services | Technical service offerings, network infrastructure CIs |
| Run | Service portfolio | Full relationship maps, all services mapped |
| Fly | Business outcomes | AI-driven insights, full CSDM compliance |

---

## CMDB Population Methods

### ServiceNow Discovery
Agentless network scanning that auto-populates CMDB:
- Probes scan IP ranges and identify CIs
- Sensors classify CIs and extract attributes
- IRE matches discovered data to existing records
- Schedules: Discovery runs can be hourly, daily, or on-demand

### Integration Hub / REST API Push
External tools push CI data to ServiceNow:
- Import Sets with Transform Maps for bulk loads
- REST API (Table API) for real-time individual CI updates
- MID Server facilitates communication with internal networks

### Manual Entry
Used for:
- CIs not discoverable by automated means (contracts, configurations)
- Initial CMDB population before discovery is configured
- Highly classified CIs not accessible from discovery infrastructure

### Service Mapping
Automatic relationship discovery for application services:
- Top-down: starts from a known entry point (URL, IP) and maps dependencies
- Bottom-up: starts from discovered CIs and infers service membership
- Requires Service Mapping plugin and MID Server

---

## CMDB Governance

### CI Ownership Fields

Every CI should have these fields populated as a governance baseline:

| Field | Purpose |
|-------|---------|
| `managed_by` | Individual responsible for the CI |
| `managed_by_group` | Team responsible |
| `supported_by` | Individual providing technical support |
| `support_group` | Team providing technical support |
| `owned_by` | Business owner (accountability) |
| `company` | Organization owning the CI |
| `cost_center` | Cost allocation |
| `location` | Physical or logical location |
| `environment` | Production, Development, Test, etc. |

### CI Lifecycle States

| State | Meaning |
|-------|---------|
| On Order | Ordered but not yet received |
| In Stock | Received but not yet deployed |
| In Maintenance | Temporarily out of service for maintenance |
| In Use | Deployed and active |
| Retired | Decommissioned; no longer active |
| Disposed | Physically destroyed or sold |
| Stolen | Reported stolen |

---

## Integration with ITSM Processes

### Incident Management
- Incidents are linked to CIs via `cmdb_ci` field
- CI's `support_group` is used for automatic assignment
- CI impact determines default incident impact level
- CI outage/degradation creates incident context for SLA selection

### Change Management
- Changes are linked to affected CIs
- CI relationship map used for impact analysis before change authorization
- Conflict detection checks other changes on the same CI in the implementation window
- Post-change CI status should be updated

### Problem Management
- Problems are linked to CIs where the root cause resides
- CI history (recent changes, previous incidents) informs RCA
- Known Error articles are linked to affected CIs for discoverability

---

## Best Practices

### Data Quality
- Automate CI population via Discovery — manual entry is error-prone
- Define CMDB completeness targets per CI class (e.g., 95% of servers must have `managed_by_group`)
- Run CMDB Health checks monthly and address deficiencies systematically
- Establish a CI lifecycle process: CIs are created, maintained, and retired through formal processes

### CSDM Compliance
- Start with Foundation data quality before attempting Service Delivery layer
- Prioritize Application Service mapping for the top 20 business-critical services
- Use CSDM Health Dashboards to track compliance and set quarterly improvement targets

### Relationship Management
- Define a standard relationship vocabulary — avoid creating custom relationship types for needs that existing types cover
- Review stale relationships (CIs that are Retired but still show active relationships)
- Use Service Mapping for application services rather than manually creating relationship records

### CMDB Performance
- Do not store large volumes of data in custom fields on `cmdb_ci` — extend to a sub-class table
- Archive or retire stale CIs rather than leaving them in "In Use" state
- Use CMDB Deduplicate to merge duplicate CI records from multiple discovery sources

---

## Common Patterns

### Service Impact Analysis for an Incident
1. Agent selects CI on incident record
2. ServiceNow shows CI's support group (auto-populates assignment group)
3. Agent can view CI's relationship map to understand upstream services affected
4. Outage duration triggers notifications to business service owners
5. Multiple incidents on same CI suggest a Problem should be created

### Pre-Change CI Relationship Review
Before authorizing a change to a database server:
1. Open CI's relationship map
2. Identify all Applications that "Depend on" this database
3. Contact application owners for change communication
4. Schedule change in maintenance window agreed by all affected service owners
5. Confirm no conflicting changes on related CIs

### Discovery-Driven CMDB Population
1. Configure MID Server for network access
2. Define IP ranges and discovery schedule
3. Run Discovery → servers, VMs, and network gear auto-populated
4. IRE matches discovered data to existing records (or creates new)
5. Review unmatched/orphaned CIs weekly
6. Configure Reconciliation Rules to handle multi-source data for the same CI
