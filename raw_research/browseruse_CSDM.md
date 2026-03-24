# CSDM

Source: browser-use task 0a2b4b4a-1ef5-4a90-a498-c23972f1cb49
Steps: 24 | Cost: $0.144 | Success: True

Based on the ServiceNow documentation, here is the comprehensive information regarding the Common Service Data Model (CSDM):

### 1. CSDM Overview and Purpose
The Common Service Data Model (CSDM) is a standard data model framework for ServiceNow products and applications. It provides prescriptive guidelines for defining configuration items (CIs) and their relationships in the CMDB to ensure data resides in the correct tables. Its purpose is to:
- Maximize the value of ServiceNow AI Platform applications.
- Provide a consistent and accurate service reporting structure.
- Support multiple configuration strategies with base-system tables.
- Enable unified data access and governance across the platform.

### 2. CSDM Layers (Domains)
- **Foundation:** Contains base referential data (Locations, Users, Groups, Companies, Products) used across other domains but not participating in CMDB relationships.
- **Design & Planning:** Focuses on the design of digital products. Key entities include Business Capabilities, Business Applications, and Information Objects.
- **Build & Integration:** Manages logical development components (SDLC Components) and AI System Digital Assets during the build phase.
- **Service Delivery:** Represents the operational environment, including Service Instances (Application Services), Technology Management Services, and offerings.
- **Service Consumption:** Enables consumers to request services via Service Catalogs and manages Business Services and Offerings.
- **Manage Portfolio:** An oversight layer for service owners to manage business applications and their instances across domains.

### 3. Service Types and Offerings
- **Business Service:** A service published to business users (e.g., 'Manage HR').
- **Technology Management Service (Technical Service):** Underpins business services and is managed by technical teams.
- **Service Offering:** A stratification of a service (Business or Technical) by options like geography, environment, or support levels (e.g., 'Manage Onboarding' as an offering of 'Manage HR').

### 4. Application Service vs. Business Capability
- **Business Capability:** A high-level, conceptual capability required by an organization (e.g., 'Manage Payroll'). It is used for strategic planning.
- **Application Service (Service Instance):** A logical representation of a deployed system or application stack (e.g., 'Payroll Production'). It is operational and used in Incident/Change management.

### 5. Implementation Stages
- **Foundation:** Preparing referential data (Users, Groups, Locations).
- **Crawl:** Focuses on Business Applications and their relationships to Service Instances for basic ITSM support.
- **Walk:** Expands to include technical service offerings and network infrastructure CIs.
- **Run/Fly:** Advanced stages focusing on service portfolio optimization and business outcome alignment.

### 6. Relationships and Integration
- CSDM integrates with the **CMDB** by providing a structured way to link logical entities (Business Applications) to physical infrastructure (Servers, Databases) through **Service Instances**.
- Common relationships include: *Business Capability -> Provides -> Business Application -> Consumes -> Service Instance -> Depends on -> Infrastructure CI*.

### 7. Compliance and Health
- ServiceNow provides **CSDM Health Dashboards** to monitor the completeness and correctness of data alignment with the CSDM framework, specifically tracking 'Service Instance' health and CI metadata like 'Managed by Group'.
