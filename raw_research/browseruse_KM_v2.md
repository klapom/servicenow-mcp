# KM_v2

Source: browser-use task 772469a2-2bb3-4fcc-9c05-1e6c0e144beb
Steps: 34 | Cost: $0.204 | Success: True

I have successfully extracted the requested ServiceNow Knowledge Management documentation for the Australia release (updated March 2026). Below is the structured summary of the information gathered:

### 1. Knowledge Management Overview
ServiceNow Knowledge Management (KM) allows for the creation, categorization, review, approval, and consumption of knowledge. 
- **Components:** Knowledge Bases, Knowledge Articles, Knowledge Workflows, and User Criteria (for access control).
- **Architecture:** Built on the ServiceNow platform, utilizing the `kb_knowledge` table for articles and `kb_knowledge_base` for containers. It integrates with Service Portal for consumption and ITSM processes for article creation.

### 2. Article Lifecycle States
Articles transition through the following states:
- **Draft:** Initial creation phase.
- **Review:** Article is being reviewed (often by a manager or subject matter expert).
- **Scheduled for Publish:** Approved and waiting for the 'Valid from' date.
- **Published:** Visible to users based on user criteria.
- **Pending Retirement:** Under review for removal.
- **Retired:** No longer visible to general users; archived for administrative reference.
- **Outdated:** Replaced by a newer version (when versioning is enabled).

### 3. Knowledge Workflows
- **Instant Publish/Retire:** Articles are published or retired immediately upon submission without manual approval.
- **Approval Publish/Retire:** Articles require manual approval from a Knowledge Manager or designated group before the state changes.
- **Flow Designer:** Modern implementations use Flow Designer for more complex, customizable logic compared to legacy workflows.

### 4. KCS (Knowledge-Centered Service)
- **Confidence States:** 
    - *Work in Progress:* Draft/Review states.
    - *Validated:* Published by a qualified KCS role (Publisher/Coach).
    - *Not Validated:* Published by a non-KCS qualified user.
    - *Archived:* Retired articles.
- **AQI (Article Quality Index):** A scoring system used by Knowledge Coaches to evaluate article quality based on checklists. Tasks include creating checklists, assigning them to knowledge bases, and performing reviews.
- **Required Plugin:** `com.snc.knowledge_kcs_capabilities`.

### 5. Knowledge Management Roles
- **knowledge_admin:** Full administrative access to KM settings and all articles.
- **knowledge_manager:** Manages specific knowledge bases, approvals, and feedback.
- **knowledge (Contributor):** Can create, edit, and read articles.
- **knowledge_coach:** Specifically for KCS; reviews AQI and coaches contributors.
- **kcs_publisher / kcs_contributor / kcs_candidate:** Specific roles for the KCS workflow.

### 6. Integration with Incident and Problem Management
- **Creation:** Articles can be created directly from Incidents using the 'Knowledge' checkbox or 'Create Knowledge' UI Action.
- **Templates:** The 'Incident KCS Article' template is commonly used to map Incident fields (Short Description, Resolution) to Knowledge fields.
- **Linking:** Articles can be attached to Incidents/Problems to assist in resolution, creating a 'Used in' relationship for reporting.

### 7. Valid Dates and Article Expiration
- **Valid to date:** Controls when an article expires. If blank, it defaults to January 1, 2100, or a date set at the Knowledge Base level.
- **Expiration:** Once the 'Valid to' date is reached, the article is excluded from search results.
- **Notifications:** The system sends monthly email notifications to authors/managers for articles approaching their expiration date.
