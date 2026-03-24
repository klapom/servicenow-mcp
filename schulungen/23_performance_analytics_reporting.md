---
source_type: platform
topics:
  - performance analytics
  - reporting
  - indicators
  - breakdowns
  - data collection
  - dashboards
  - KPIs
---

# Performance Analytics and Reporting

## Overview

ServiceNow provides two distinct but complementary analytics capabilities: **Reporting** (point-in-time snapshots of current data) and **Performance Analytics** (historical trending over time using collected data snapshots).

Reports answer: "What does the data look like right now?"
Performance Analytics answers: "How has the data changed over time, and where are we trending?"

Both capabilities feed into Dashboards that provide visual management overviews for ITSM, CSM, and business process owners.

---

## Reporting

### Report Types

| Type | Best For |
|------|---------|
| List | Tabular data; detailed record-level view |
| Bar Chart | Comparing values across categories |
| Horizontal Bar | Same as bar; better for long category names |
| Pie/Donut | Proportional breakdown (use sparingly) |
| Line | Trend over time using report creation date |
| Area | Same as line; fills area under the curve |
| Spline | Smoothed line trend |
| Pivot Table | Cross-tabulation of two dimensions |
| Funnel | Progress through stages |
| Heat Map | Two-dimensional intensity visualization |
| Box Plot | Statistical distribution |
| Single Score | Single KPI number |
| Gauge | Progress toward a target |
| Map | Geographic distribution |

### Creating a Report

1. Navigate to Reports → Create New (or from any list: right-click column header → "Group By")
2. Select Table
3. Choose Type (chart, list, etc.)
4. Configure Grouping fields (for charts)
5. Set Filters (Conditions)
6. Apply Aggregation (COUNT, SUM, AVG, MIN, MAX)
7. Set Sort order
8. Name and Save
9. Share with others (Public, Roles, Users, Groups)

### Report Configuration Fields

| Setting | Description |
|---------|-------------|
| Table | Data source table |
| Type | Report visualization type |
| Group by | Field for X-axis or grouping |
| Stack by | Second grouping dimension (stacked bar/area) |
| Filter | Record filter conditions |
| Aggregation | COUNT, SUM, AVG, MIN, MAX on a numeric field |
| Per | Time period for trend reports |
| Chart width/height | Display dimensions |
| Refresh interval | Auto-refresh on dashboards |

### Report Scheduling
Reports can be emailed on a schedule:
- Navigate to report → "Scheduled Reports" related list
- Set frequency: Daily, Weekly, Monthly
- Set recipients: Users, Groups, Email addresses
- Format: PDF, CSV, Excel, HTML

---

## Performance Analytics Architecture

Performance Analytics (PA) introduces the concept of **collecting and storing scores over time** — rather than querying current data, it queries a historical data store of indicators.

### Level 0: Data Sources (Tables)
The raw ServiceNow tables (incident, change_request, etc.) where operational data lives.

### Level 1: Indicator Sources and Breakdown Sources

**Indicator Source:** A saved query that defines the population of records to measure.
Example: "All Incidents" = table: incident, filter: none

**Breakdown Source:** A set of categories used to slice indicator data.
Example: "Priority" = the distinct values of `incident.priority`

---

## Indicators

Indicators are the measurements tracked over time in Performance Analytics.

### Automated Indicators
- Based on an Indicator Source (a saved query)
- Score calculated by Data Collection Job
- Score = aggregate function (COUNT, SUM, AVG) applied to records matching the query at collection time

**Example:** "Open P1 Incidents" indicator
- Source: Incident table, filter: state IN (1,2,3) AND priority = 1
- Function: COUNT
- Score at collection: The number of open P1 incidents at that moment

### Formula Indicators
- Calculated at view-time using mathematical operations on other indicator scores
- No data collection needed — computed dynamically

**Example:** "SLA Compliance Rate" formula indicator
- Formula: (Resolved Incidents Meeting SLA / Total Resolved Incidents) × 100
- References two other indicators: "Incidents Met SLA" and "Total Resolved Incidents"

### Indicator Configuration

| Field | Description |
|-------|-------------|
| Name | Indicator display name |
| Source | The Indicator Source (query definition) |
| Aggregate | COUNT, SUM, AVG, MIN, MAX |
| Field | For SUM/AVG: which field to aggregate |
| Active | Enable/disable collection |
| Frequency | How often scores are collected (Daily, Weekly, Monthly) |
| Direction | Higher is better / Lower is better |
| Target | Goal value for comparison |
| Threshold | Warning/alert value |

---

## Breakdowns

Breakdowns enable indicators to be segmented by category:

**Example:** "Open Incidents by Priority" uses the "Open Incidents" indicator with a "Priority" breakdown.

### Breakdown Sources
A Breakdown Source defines the possible segments:
- **Field-based:** Distinct values of a table field (Priority, Assignment Group, Category)
- **Relationship-based:** Records from a related table

### Using Breakdowns in Reports
When viewing an indicator, users can apply a breakdown:
- "Show Open Incidents by: Priority" → bar chart with P1, P2, P3, P4 columns
- "Show Open Incidents by: Assignment Group" → segmented by team
- "Drill down": click a bar to see the records in that segment

---

## Data Collection Jobs

Data Collection Jobs run on a schedule and create the historical score records that Power Analytics queries.

**Navigation:** Performance Analytics → Data Collector → Jobs

### Job Types

| Type | Description |
|------|-------------|
| Historical Job | Backfills historical data from past dates (one-time catch-up) |
| Daily Collection Job | Runs daily to collect current-day scores |

### Job Configuration

| Setting | Description |
|---------|-------------|
| Name | Job name |
| Frequency | Daily, Weekly, Monthly |
| Run time | When to execute |
| Indicators | Which indicators to collect during this job |
| Run at completion | Immediately update dashboards after collection |
| Date range (historical) | For historical jobs: date range to backfill |

### Required Roles

| Role | Access |
|------|--------|
| `pa_data_collector` | Run data collection jobs; view indicator data |
| `pa_admin` | Full PA administration |
| `admin` | Inherits all PA roles |

### Collection Operators

For historical jobs, two operator types control which date is used for each collected record:

| Operator Type | Description |
|---------------|-------------|
| Fixed | Use a specific field value (e.g., sys_created_on) as the data point date |
| Relative | Use a calculated date relative to another field |

---

## Targets and Thresholds

### Targets
A target is a goal value for an indicator:
- "Resolved Incidents": target = 50 per day
- "SLA Compliance": target = 95%
- Shown as a horizontal reference line on trend charts

### Thresholds
Thresholds trigger visual alerts when indicators cross defined values:
- Warning threshold: indicator enters caution zone
- Critical threshold: indicator enters critical zone
- Color coding: green → yellow → red progression

---

## Dashboards

Dashboards aggregate multiple reports, PA widgets, and KPIs into a single management view.

### Dashboard Components

| Widget Type | Description |
|-------------|-------------|
| Report | Any saved report displayed as a chart or list |
| PA Score Widget | Current score of a PA indicator |
| PA Trend Widget | Historical trend line for a PA indicator |
| PA Breakdown Widget | PA indicator segmented by breakdown |
| PA Trend Breakdown | Trend with breakdown segments |
| Single Score | Simple number display |
| Gauge | Progress toward target |
| URL | Embedded external content |

### Dashboard Configuration

**Navigation:** Reports → Dashboards → New

1. Create dashboard with name and description
2. Add tabs (for different views on the same dashboard)
3. Add widgets to each tab by dragging from the widget library
4. Configure each widget's data source and display options
5. Set sharing (who can see and edit the dashboard)
6. Pin to navigation or share with users/groups

### Dashboard Personas
Dashboards are most useful when designed for a specific audience:

| Audience | Dashboard Focus |
|----------|----------------|
| Service Desk Agent | Personal queue, daily throughput, SLA status |
| Team Manager | Team metrics, SLA compliance, volume trends |
| IT Director | Cross-team performance, incident trends, capacity planning |
| Executive | Business impact, cost per ticket, strategic SLA compliance |

---

## Analytics Hub (Now Intelligence)

The Analytics Hub provides a unified experience for PA and reporting:
- Single access point for all analytics
- AI-driven insights and anomaly detection
- Natural language queries ("How many P1 incidents were created this week?")
- Automated alerting on threshold breaches
- Root cause analysis suggestions for unusual trends

---

## Best Practices

### Report Design
- Choose the right visualization type: bar charts for comparison, line charts for trends, lists for drill-down detail
- Avoid pie charts with more than 5 segments — difficult to read
- Always add a meaningful title and description explaining what the report shows
- Specify a filter — unfiltered reports on large tables are slow and overwhelming
- Use "Group by" appropriately — too many groups make charts unreadable

### Performance Analytics Strategy
- Start with a small set of critical indicators (10-15) rather than collecting everything
- Align indicators to business outcomes, not just technical metrics
- Ensure data quality before implementing PA — garbage in, garbage out
- Run historical data collection after setting up PA to enable trend analysis from day one

### Dashboard Governance
- Each dashboard should have an owner who reviews it regularly
- Review dashboard usage monthly — remove unused dashboards
- Version dashboards before making significant layout changes
- Use dashboard groups to organize related dashboards

---

## Key Metrics by Process

### Incident Management KPIs

| Metric | Indicator | Target |
|--------|-----------|--------|
| SLA Compliance Rate | % Incidents Meeting Resolution SLA | >95% |
| Mean Time to Resolve (MTTR) | Avg. resolution time (business hours) | <4hr P1, <8hr P2 |
| First Call Resolution | % resolved at L1 without escalation | >70% |
| Reopened Incident Rate | % incidents reopened after resolution | <5% |
| Incident Volume | Count of new incidents per day/week | Track trend |
| P1/P2 Incident Rate | % critical incidents of total | Track trend (should decline) |

### Change Management KPIs

| Metric | Indicator | Target |
|--------|-----------|--------|
| Change Success Rate | % changes Closed as Successful | >98% |
| Change-Induced Incident Rate | Incidents caused by changes | <5% of changes |
| Emergency Change Ratio | Emergency changes / total changes | <10% |
| CAB Rejection Rate | % changes rejected at CAB | <10% |

### Service Catalog KPIs

| Metric | Indicator |
|--------|-----------|
| Self-Service Rate | % requests submitted via catalog vs. phone/email |
| Average Fulfillment Time | Avg. days from RITM to closure |
| Catalog Adoption | Unique users submitting catalog requests |
| Rejection Rate | % RITMs rejected by approvers |

---

## Common Patterns

### Scheduled Weekly SLA Report
1. Create a Bar Chart report: incident, grouped by priority, filter: state=6 (Resolved) + resolved this week, aggregation: count with color by `made_sla`
2. Schedule: Every Monday at 08:00
3. Recipients: IT Management distribution list
4. Format: PDF attachment

### Management Dashboard
1. Tab 1 - Incident Overview: Open by Priority (bar), Volume Trend (line, 30 days), MTTR by Group (horizontal bar)
2. Tab 2 - SLA Performance: SLA Compliance trend, Breach count by group
3. Tab 3 - Capacity: Incident volume by day of week (heat map), Queue depth by group (single score tiles)
4. Refresh: Every 15 minutes
5. Shared with: IT management role
