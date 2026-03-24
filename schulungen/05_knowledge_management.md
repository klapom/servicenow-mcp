---
source_type: process
topics:
  - knowledge management
  - knowledge base
  - KCS
  - knowledge articles
  - article lifecycle
  - AQI
---

# Knowledge Management

## Overview

ServiceNow Knowledge Management (KM) enables organizations to create, organize, review, publish, and consume knowledge. A well-run KM program reduces incident resolution time (agents find answers faster), increases self-service rates (users solve their own issues), and preserves institutional knowledge across personnel changes.

The system is built on the `kb_knowledge` table for articles and `kb_knowledge_base` for container/base records. It integrates with Incident Management (article creation from incidents), Problem Management (Known Error articles), Service Portal (self-service search), and Employee Center (unified knowledge search).

---

## Core Components

### Knowledge Bases (`kb_knowledge_base`)
A Knowledge Base is a top-level container that groups articles by subject domain, audience, or organizational ownership.

| Property | Purpose |
|----------|---------|
| Title | Display name |
| Description | Purpose and audience |
| Owner | Knowledge Manager responsible for the KB |
| Owner group | Team that manages content |
| Workflow | Publish/Retire workflow assigned to articles in this KB |
| Access | User criteria controlling who can see the KB |
| Default valid to | Article expiration default (if not set on individual article) |
| Active | Whether the KB is visible to users |

Examples of Knowledge Bases in a typical enterprise:
- IT Support Knowledge Base (resolver-facing)
- Self-Service Knowledge Base (end-user-facing)
- HR Policies (HR-specific, audience-restricted)
- Known Errors (linked from incident/problem workflows)
- Security Advisories (restricted access)

### Knowledge Articles (`kb_knowledge`)
Articles are the individual content records. Each article belongs to exactly one Knowledge Base.

| Field Name | Type | Description |
|-----------|------|-------------|
| `number` | String | Auto-generated KB number (e.g., KB0001234) |
| `short_description` | String | Title — shown in search results |
| `text` | HTML | Full article body |
| `knowledge_base` | Reference | Parent Knowledge Base |
| `category` | String | Article category within the KB |
| `workflow_state` | String | Current lifecycle state |
| `valid_to` | Date | Expiration date (default: 2100-01-01) |
| `valid_from` | Date | Publication date |
| `author` | Reference → sys_user | Article creator |
| `kb_knowledge_base.owner` | Reference | KB manager (via dot-walk) |
| `view_count` | Integer | Number of times article has been read |
| `flagged` | Boolean | Flagged for review/improvement |
| `use_count` | Integer | Times article was used to resolve an incident |
| `meta_description` | String | SEO-style search teaser |
| `published` | Date | When article was published |
| `article_type` | String | Text, Video, External URL |

### Categories
Categories within a Knowledge Base organize articles for browsing:
- Hierarchical (parent/child categories)
- Independent per Knowledge Base
- Used in search filters and navigation

---

## Article Lifecycle States

| State | Description |
|-------|-------------|
| Draft | Initial creation; visible only to the author and KB managers |
| Review | Submitted for review; reviewers can comment and request changes |
| Scheduled for Publish | Approved; awaiting the `valid_from` date to become active |
| Published | Live and visible to authorized users based on access criteria |
| Pending Retirement | Submitted for retirement review; still visible during review |
| Retired | No longer visible to general users; archived for administrative reference |
| Outdated | Superseded by a newer version (when versioning is enabled) |

### State Transition Diagram

```
Draft → Review → Scheduled for Publish → Published
                                              ↓
                                    Pending Retirement → Retired

                                         Published → Outdated (version replacement)
```

### Transitions Requiring Approval vs. Instant
Behavior depends on the workflow assigned to the Knowledge Base:

| Workflow Type | Publish Behavior | Retire Behavior |
|--------------|-----------------|----------------|
| Instant Publish | Draft → Published immediately upon action | Published → Retired immediately |
| Approval Publish | Draft → Review → Published (requires approver action) | Published → Pending Retirement → Retired |

---

## Knowledge Workflows

### 1. Instant Publish / Retire
- Articles are published or retired immediately upon author or manager action
- No approval step required
- Suitable for trusted contributor pools or rapid-update knowledge bases
- Risk: lower quality control; inappropriate for compliance-sensitive content

### 2. Approval Publish / Retire
- Articles require manual approval before state changes
- Knowledge Manager or designated group reviews content
- Approval request generated when author submits for review
- Approver can: Approve (advances state), Reject (returns to Draft with feedback), or Redirect (sends to another reviewer)

### 3. Flow Designer (Modern)
- Replaces legacy workflow activities with Flow Designer flows
- More flexible logic: conditional approval based on category, custom notifications, integration with external review tools
- Recommended for new implementations (post-Orlando/Yokohama releases)

---

## KCS (Knowledge-Centered Service)

KCS is a methodology for integrating knowledge creation into the incident resolution workflow. Rather than creating knowledge articles as a separate activity, agents create and improve articles as part of every resolution.

**Required Plugin:** `com.snc.knowledge_kcs_capabilities`

### KCS Confidence States

| Confidence State | Description | Who Sets It |
|-----------------|-------------|------------|
| Work in Progress | Article is in Draft or Review — not yet validated | Author |
| Validated | Published by a KCS-qualified user (Publisher or Coach) | KCS Publisher / Coach |
| Not Validated | Published by a user without KCS Publisher/Coach role | Standard user |
| Archived | Retired articles — preserved for reference | System / Manager |

### AQI (Article Quality Index)
The AQI is a scoring system used by Knowledge Coaches to evaluate and improve article quality.

Process:
1. Knowledge Coach creates an AQI Checklist (assessment criteria)
2. Checklist is assigned to one or more Knowledge Bases
3. Coach reviews articles against checklist: each criterion marked Pass/Fail/N-A
4. AQI score is calculated as a percentage of passed criteria
5. Coach provides feedback; author improves article
6. Target AQI score (e.g., 80%) can be set at the KB level as a quality gate

AQI Checklist criteria examples:
- Does the article have a clear, searchable title?
- Is the cause clearly explained?
- Is the solution specific and actionable?
- Are screenshots included where helpful?
- Is the content free of jargon unexplained for the target audience?

### KCS Roles

| Role | Permissions |
|------|------------|
| `kcs_candidate` | Creates articles in Draft; cannot publish |
| `kcs_contributor` | Creates and edits articles; can submit for review |
| `kcs_publisher` | Can publish articles directly; articles get Validated confidence |
| `knowledge_coach` | Reviews AQI; coaches contributors; marks articles for improvement |

---

## Knowledge Management Roles

| Role Name | Scope |
|-----------|-------|
| `knowledge_admin` | Full administrative access to all KBs and articles; manages system configuration |
| `knowledge_manager` | Manages a specific KB; approves/retires articles; manages feedback |
| `knowledge` (Contributor) | Creates, edits, and reads articles within permitted KBs |
| `knowledge_coach` | KCS quality review; AQI scoring |
| `public` | No role required — accesses publicly visible KBs |

---

## Integration with ITSM

### Article Creation from Incidents
Agents can create Knowledge Articles directly from resolved incidents:

**Method 1:** Check the `knowledge` checkbox on the incident record
- Triggers a workflow/flow to create a Draft KB article
- Incident KCS Article template maps:
  - `incident.short_description` → `kb_knowledge.short_description`
  - `incident.close_notes` → `kb_knowledge.text` (resolution becomes article body)
  - `incident.cmdb_ci` → article metadata

**Method 2:** Use the "Create Knowledge" UI action button
- Presents the full article editor pre-populated with incident data
- Author can enhance content before submitting

### Known Error Articles from Problems
When a problem record reaches Known Error status:
- "Create Known Error Article" UI action creates a KB article
- The problem record links to the article via related list
- Article is categorized as a Known Error
- When the problem is resolved, the article is retired

### Article Usage Tracking
When agents use a KB article to resolve an incident:
- The article is linked to the incident record
- `kb_knowledge.use_count` increments
- This creates reporting data showing which articles are most valuable
- High-use articles should be reviewed for accuracy and completeness regularly

---

## Valid Dates and Article Expiration

### Expiration Logic
- **`valid_to` date:** When this date is reached, the article is excluded from search results (still accessible to KB managers)
- **Default value:** January 1, 2100 (effectively never expires)
- **KB-level default:** The Knowledge Base can set a default expiration window (e.g., "articles expire 2 years after publication")

### Expiration Notifications
- Monthly email notifications sent to article authors and KB managers for articles approaching expiration
- Authors can extend the `valid_to` date or retire the article
- Articles past expiration remain in Retired state until formally reviewed

### Article Versioning
When versioning is enabled on a Knowledge Base:
- New versions can be created without retiring the original
- Original version transitions to "Outdated" state
- New version goes through the normal workflow
- Readers always see the current version; previous versions are accessible to managers

---

## Search and Discovery

### Full-Text Search
Articles are searchable by:
- Short description (title)
- Article body text
- Keywords/meta description
- Category

### AI Search Integration
Modern ServiceNow instances use **AI Search** (Elastic-based):
- Semantic search understanding intent, not just keywords
- Spell correction and synonym matching
- Federated search across multiple knowledge bases and external sources
- Relevance ranking based on recency, use count, and quality score

### Search Logging
`sys_search_query` table captures:
- Search terms used
- Whether results were found
- Which results users clicked on
- Failed searches (no results) — valuable for identifying content gaps

---

## Best Practices

### Knowledge Base Architecture
- Maintain a small number of well-organized KBs rather than many fragmented ones
- Separate internal resolver content from self-service user content (different access criteria)
- One KB per major domain or department with clear ownership

### Article Quality Standards
- Titles should describe the symptom from the user's perspective: "Cannot log in to VPN" not "VPN Authentication Issue"
- Include: Symptom → Cause (if known) → Resolution → Prevention
- Add screenshots for UI-related procedures
- Keep articles focused on a single issue or procedure — split if covering multiple topics

### Lifecycle Governance
- Review articles older than 12 months for accuracy
- Set `valid_to` dates based on technology lifecycle (OS articles expire sooner than policy articles)
- Assign KB ownership — every KB must have an active owner responsible for content quality

### Content Maintenance Metrics

| Metric | Target | Action if Below Target |
|--------|--------|----------------------|
| % articles validated (KCS) | >60% | Coach review; author training |
| Average AQI score | >75% | Quality review campaign |
| % articles reviewed in 12 months | >80% | Forced review reminder campaign |
| Self-service resolution rate | >30% | Improve article findability and quality |
| Article use per incident | >0.5 | Promote KB usage in resolver training |

---

## Common Patterns

### New Article from Scratch
1. Navigate to Knowledge → Create New
2. Select Knowledge Base
3. Write short description (searchable title)
4. Write body (HTML editor): Symptom → Cause → Resolution
5. Set category and keywords
6. Set valid_to date if applicable
7. Submit for approval (or publish directly if Instant Publish)

### Article Improvement from Feedback
1. User flags article as unhelpful
2. Flag creates feedback record linked to the article
3. KB Manager reviews flagged articles weekly
4. Article assigned to subject matter expert for update
5. Updated article goes back through approval workflow
6. Feedback record closed with note on improvement made

### Bulk Expiration Management
Scheduled Job runs monthly:
1. Queries articles where `valid_to` is within 60 days
2. Sends notification to article author and KB manager
3. If no action taken within 30 days, automatically moves article to Pending Retirement
4. KB Manager performs final review before retirement is confirmed
