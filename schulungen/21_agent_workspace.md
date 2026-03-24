---
source_type: platform
topics:
  - agent workspace
  - configurable workspace
  - next experience
  - UI builder
  - playbooks
  - agent assist
  - workspace configuration
---

# Agent Workspace

## Overview

Agent Workspace (also called Configurable Workspace) is ServiceNow's modern work interface designed for customer service agents and ITSM resolvers. It replaces the classic ServiceNow UI with a purpose-built, component-based interface that consolidates all tools an agent needs into a single view.

The workspace provides context-aware assistance, real-time metrics, multi-tab work management, and AI-powered recommendations — all designed to reduce resolution time and increase agent efficiency.

---

## Why Agent Workspace?

### Classic UI Limitations
The classic ServiceNow form interface was designed as a general-purpose administrative interface:
- Separate browser tabs for each record
- No agent-specific workflow guidance
- No real-time metrics or KPIs on the work surface
- Limited context aggregation (related records require separate navigation)

### Agent Workspace Advantages

| Feature | Classic UI | Agent Workspace |
|---------|-----------|----------------|
| Multi-record navigation | Multiple browser tabs | Single-window multi-tab |
| SLA visibility | Separate SLA related list | Built into record view ribbon |
| Knowledge suggestions | Manual KB search | AI-powered agent assist panel |
| Related records | Separate tab navigation | Expandable side panels |
| Metrics/KPIs | Dashboard (separate) | Embedded in landing page |
| Playbooks | Not available | Guided resolution steps |
| Chat integration | Limited | Native multi-session support |

---

## Workspace Architecture

### Pages

Workspaces are composed of pages, each serving a specific purpose:

| Page Type | Purpose |
|-----------|---------|
| Landing Page | Starting point with filtered lists, KPIs, and performance metrics |
| List Page | Browsable/filterable record lists |
| Record Page | Detailed view of a single record |
| Dashboard | Reports and performance analytics overview |

### Components

Pages are built from reusable **Next Experience UI components**:
- Form sections
- Related lists
- Activity stream
- SLA countdown timers
- KPI tiles
- Recommendations panels
- Playbook panels

### Navigation

| Element | Description |
|---------|-------------|
| Navigation bar | Left sidebar with workspace sections |
| Tab bar | Open records/sessions as tabs |
| Ribbon | Top-of-form context strip showing key record fields at a glance |
| Side panel | Expandable right panel with tabs for different contexts |

---

## Landing Page

The landing page is the first screen an agent sees when opening the workspace.

### Landing Page Components

| Component | Contents |
|-----------|---------|
| Filtered lists | Queue of work items matching agent's groups and filters |
| KPI tiles | Real-time counts: open incidents, SLA at risk, unassigned, etc. |
| Performance tracking | Individual agent metrics: resolved today, average handle time |
| Notifications | Urgent items requiring attention |
| Shortcuts | Quick-access links to common actions |

### Configuring the Landing Page
Administrators configure landing pages in **UI Builder**:
- Add/remove/reorder components
- Set default filters for lists (e.g., show only P1/P2 incidents for this workspace)
- Configure which KPI tiles appear and their data sources

---

## Record Page Layout

### Form Ribbon
The ribbon appears at the top of every record page and shows:
- Record number and title
- Key status fields (State, Priority, Assignment Group)
- SLA progress bar / timer
- Quick action buttons (Update, Assign to Me)
- Configurable fields for at-a-glance context

### Main Form Area
The record form with fields organized into sections:
- Field layout configurable via workspace form views
- "Related Items" shows linked records (incidents, tasks, changes)
- Can show multiple related lists in the form body

### Side Panel Tabs

The right-side panel provides context without navigating away from the record:

| Tab | Contents |
|-----|---------|
| Record Information | SLA details, CI information, service overview |
| Recommended Actions | AI-suggested KB articles, similar cases, next steps |
| Agent Assist | Real-time knowledge suggestions based on record content |
| Activity Stream | Work notes, comments, system activity timeline |
| Templates | Form templates, response templates, email templates |
| Attachments | File attachments with quick view |
| Playbook | Current playbook step and guided resolution |
| Related Lists | Accordion panels for related records (linked incidents, tasks, etc.) |

---

## Agent Assist and AI Recommendations

### Agent Assist Panel
The Agent Assist panel uses the record's **Short Description** to perform real-time AI search:

- As the agent types or views the short description, suggestions appear automatically
- Results include Knowledge Base articles, similar past incidents, and recommended solutions
- Agents can view articles without leaving the record
- Agents can "use" an article to link it to the incident and track its effectiveness

### Recommended Actions
A dedicated tab provides AI-driven suggestions for:
- Next actions to take based on incident type and history
- Similar cases that were resolved — view how they were solved
- Knowledge articles most relevant to this exact symptom
- Agent flagging: mark suggestions as helpful/not helpful to improve the model

---

## Playbooks

Playbooks provide **guided, step-by-step resolution processes** for standardized workflows.

### What Playbooks Do
- Define a sequence of steps an agent should follow
- Each step may require an action (fill a form, make a call, update a field)
- Steps can include decision branches ("Was the issue reproduced in QA?")
- Progress is tracked — managers can see which step each case is at
- Ensures compliance with defined procedures (SOP adherence)

### Playbook Components
- **Playbook:** The overall process definition
- **Lane:** A phase or stage within the playbook (e.g., Investigation, Resolution, Communication)
- **Step:** Individual action within a lane
- **Condition:** Logic that determines which steps appear next

### Configuring Playbooks
1. Navigate to Process Automation → Playbooks
2. Create playbook definition with lanes and steps
3. Associate playbook with a record type/condition (e.g., "P1 Incidents")
4. Playbook appears in agent workspace when conditions are met

---

## Multi-Tab Interface

### Tab Management
Agents can work on multiple records simultaneously:
- Each open record appears as a tab in the tab bar
- Chat conversations open as separate tabs
- Tabs can be pinned to prevent accidental closure
- Tab state is preserved when switching between records

### Link Manager
The ServiceNow Link Manager facilitates multi-record contexts:
- Related records can be opened in new tabs without losing the current record
- "Back" navigation returns to the previous record context

---

## Workspace Configuration

### UI Builder
Workspaces are configured in **UI Builder** (System UI → UI Builder):
- Visual drag-and-drop component editor
- Configure which components appear on each page
- Set data sources, filters, and display conditions for each component
- Preview changes before publishing

### Workspace Builder (App Engine Studio)
For administrators creating new workspaces from scratch:
1. Navigate to App Engine Studio or Now Platform → Workspaces
2. Create new workspace or clone an existing one
3. Define workspace pages, navigation, and component layout
4. Configure permissions for who can access the workspace

### Role-Based Access
Different workspace configurations can be created for different roles:
- **Service Desk Workspace:** Focused on incident triage and quick resolution
- **L2 Technical Workspace:** More technical details, CI relationship maps
- **Manager Workspace:** Team metrics, SLA dashboards, escalation management

---

## Workspace vs. Classic UI: Key Differences

| Feature | Workspace | Classic UI |
|---------|----------|-----------|
| Interface design | Next Experience (React-based) | Legacy Jelly/DocType |
| Multi-record | Tab-based single window | Multiple browser tabs |
| AI integration | Native (Agent Assist, recommendations) | Limited, requires navigation |
| SLA visibility | Ribbon + timer | Related list |
| Performance | Optimized for agents | General purpose |
| Customization | UI Builder (no-code) | Form designer + custom code |
| Deprecation status | Active development | Legacy (eventually deprecated) |

### Migration Path
ServiceNow is gradually deprecating Classic UI in favor of Next Experience workspaces. Organizations should:
- Plan workspace migrations for major ITSM modules
- Validate all Client Scripts and UI Policies work in Next Experience context
- Test Business Rules that modify UI behavior
- Update training materials and documentation

---

## Performance Analytics Integration

Agent Workspace can surface Performance Analytics data:

- **KPI Tiles** on landing page pull from Performance Analytics indicators
- **Embedded dashboards** show team and individual performance
- Breakdown by time period (today, this week, this month)
- Real-time indicators (data collected via scheduled jobs)

---

## Best Practices

### Workspace Design for Agents
- Keep landing pages focused — agents should see their queue and key metrics, not everything
- Configure filters to show only records relevant to the agent's groups
- Embed the most-used related lists in the record page (not hidden behind navigation)
- Tune Agent Assist relevance by ensuring knowledge articles are well-maintained

### Rollout and Training
- Pilot workspace rollout with a volunteer group before full deployment
- Train agents specifically on workspace navigation — it is significantly different from classic UI
- Create workspace-specific job aids and videos
- Gather agent feedback in first 30 days and adjust configuration

### Playbook Governance
- Design playbooks for the top 10 most common incident types first
- Review and update playbooks quarterly based on resolution pattern analysis
- Measure playbook adherence as a quality metric
- Don't over-prescribe — leave room for agent judgment on novel cases

---

## Common Patterns

### Standard Incident Workspace Configuration

**Landing Page:**
- Queue: Incidents assigned to agent's groups, sorted by Priority + SLA age
- KPI tiles: Open P1/P2 count, SLA at risk count, Unassigned count
- Performance: Incidents resolved today, average SLA compliance (week)

**Record Page Ribbon:**
- Number, Short Description, State, Priority, SLA countdown timer

**Side Panel Tabs:**
- Tab 1: Record Info (SLA details, CI info, business service)
- Tab 2: Agent Assist (KB recommendations)
- Tab 3: Activity Stream (work notes and comments)
- Tab 4: Related Lists (linked problems, changes, KB articles)

**Playbook:** Active for P1/P2 incidents, showing escalation steps

### Manager Dashboard Workspace
- Team queue overview (all incidents for all managed groups)
- SLA compliance trending (this week vs. last week)
- Agent workload distribution chart
- Escalation alerts for at-risk SLAs
- No individual record editing — read-only overview focus
