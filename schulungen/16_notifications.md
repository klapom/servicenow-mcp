---
source_type: platform
topics:
  - notifications
  - email notifications
  - SMS
  - push notifications
  - inbound email
  - notification templates
  - digest notifications
---

# Notifications

## Overview

ServiceNow's notification system alerts users about record changes, process milestones, and business events through multiple channels: email, SMS, push notifications, and integrations with collaboration platforms like Slack and Microsoft Teams. Notifications are the primary mechanism for keeping stakeholders informed without requiring them to actively monitor ServiceNow.

Notifications are configured in the `sysevent_email_action` table (for event-based) and `sysevent_email_style` (templates). They can be triggered by record changes or by system events.

---

## Notification Channels

| Channel | Use Case | Configuration Location |
|---------|---------|----------------------|
| Email | Primary channel; formal notifications | System Notification → Email → Notifications |
| SMS | Urgent alerts; on-call paging | System Notification → SMS → Notifications |
| Push (Mobile) | ServiceNow Mobile App alerts | System Notification → Push → Notifications |
| Slack | Collaboration channel alerts | Now Actions / IntegrationHub Slack Spoke |
| Microsoft Teams | Collaboration alerts | Now Actions / IntegrationHub Teams Spoke |

---

## Email Notifications

Email notifications are the most commonly used notification type. They can be triggered by:
1. **Record changes** — when a field value matches specified conditions
2. **Events** — when a specific system event is fired

### Notification Configuration (Three Sections)

Every email notification has three key configuration sections:

#### When (Trigger)
Defines when the notification fires:

| Setting | Description |
|---------|-------------|
| Table | The table to watch (e.g., `incident`) |
| Trigger | "Record Change" or "Event is fired" |
| Inserted | Fire when a new record is created |
| Updated | Fire when an existing record is updated |
| Condition | Filter conditions (when to fire vs. when to skip) |
| Send when | "Inserted or Updated", "Inserted only", "Updated only" |
| Event name | For event-triggered notifications: the event to listen for |

**Important:** Conditions are evaluated both before and after the change. A notification fires if conditions are TRUE after the change.

#### Who (Recipients)
Defines who receives the notification:

| Recipient Type | Description |
|---------------|-------------|
| Users | Specific named users (sys_id or user field reference) |
| Groups | All members of specified groups |
| Roles | All users with specified roles |
| Fields | Dynamic recipients from record fields (e.g., `assigned_to`, `caller_id`) |
| User field | Dot-walking to related user (e.g., `assigned_to.manager`) |
| Subscriptions | Users who have subscribed to this notification type |

**Exclude delegates/users:** Specific users or groups can be excluded from receiving the notification.

#### What (Content)
Defines the notification content:

| Setting | Description |
|---------|-------------|
| Subject | Email subject line (supports variables) |
| Body (HTML/Text) | Email body with dynamic content using `${field_name}` syntax |
| Template | Reusable email template from `sysevent_email_style` |
| From name | Sender display name |
| Reply-to | Reply email address |
| Include workflow | Whether to include workflow history |
| Content type | Text or HTML |

### Email Variables in Notifications

Use `${...}` syntax to embed dynamic values from the record:

| Variable | Output |
|----------|--------|
| `${number}` | Record number (e.g., INC0001234) |
| `${short_description}` | Short description field value |
| `${assigned_to.name}` | Display name of assigned user (dot-walk) |
| `${state}` | State display value |
| `${priority}` | Priority display value |
| `${URI}` | Link to the record |
| `${URI_REF}` | Full URL to the record |
| `${event.parm1}` | First event parameter (event-based only) |
| `${event.parm2}` | Second event parameter (event-based only) |

### Notification Templates (`sysevent_email_style`)
Templates define reusable HTML/text email layouts. A notification can reference a template to apply:
- Corporate branding (logo, header, footer)
- Standard disclaimer text
- Consistent formatting across all notifications

Templates support the same `${...}` variable syntax.

---

## Notification Conditions and Filtering

### Field Change Conditions
Most notifications should only fire when relevant data changes — not on every record update:

```
// Good: Only fire when assignment group changes
Field Changes: assignment_group

// Good: Only fire when state changes to Resolved
State is Resolved AND State changes
```

### "Advanced Condition" Script
For complex conditions not expressible in the condition builder:

```javascript
// Only send notification if SLA is at risk (> 75% elapsed)
var taskSLA = new GlideRecord('task_sla');
taskSLA.addQuery('task', current.sys_id);
taskSLA.addQuery('stage', 'in_progress');
taskSLA.setLimit(1);
taskSLA.query();
if (taskSLA.next()) {
    return parseFloat(taskSLA.business_percentage) >= 75;
}
return false;
```

### Preventing Notification Storms
Without careful filtering, a busy system generates too many emails:
- Always specify the exact field change that triggers the notification
- Use conditions to limit notification scope (e.g., only for P1/P2)
- Use digest notifications for high-volume recurring alerts
- Consider user notification preferences and subscriptions

---

## Inbound Email Actions

Inbound email actions process incoming emails and perform actions in ServiceNow — the reverse of outbound notifications.

**Navigation:** System Notification → Email → Inbound Actions
**Table:** `sys_email_action`

### Common Inbound Email Scenarios

| Action | Description |
|--------|-------------|
| Create incident | Email to help@company.com creates an incident |
| Update incident | Reply to incident notification updates the work notes |
| Close incident | Email with "RESOLVED" keyword closes the incident |
| Reply-all to caller | Responder emails from ServiceNow; response reaches caller |

### Inbound Action Configuration

| Setting | Description |
|---------|-------------|
| Name | Action name |
| Table | Target table (where to create/update records) |
| Active | Enable/disable |
| Rule type | Self-generated (auto-detect) or user-initiated |
| Condition | When to apply this action |
| Script | JavaScript to execute on the incoming email |

### Inbound Email Script Context

Available objects in inbound email action scripts:

| Object | Description |
|--------|-------------|
| `email` | The incoming email GlideRecord |
| `email.body_text` | Plain text body |
| `email.body` | HTML body |
| `email.subject` | Email subject |
| `email.from` | Sender email address |
| `email.to` | Recipient email address |
| `email.headers` | Email headers |
| `current` | The task/record being created or updated |
| `template` | Template being used (if any) |

### Example: Auto-Create Incident from Email

```javascript
// Inbound action script — fires when email to helpdesk@company.com received
current.caller_id.setDisplayValue(email.from_address);
current.short_description = email.subject;
current.description = email.body_text;
current.contact_type = 'email';
current.category = 'software'; // Default category

// Try to determine category from subject keywords
if (/network|vpn|wifi|internet/i.test(email.subject)) {
    current.category = 'network';
} else if (/printer|hardware|laptop/i.test(email.subject)) {
    current.category = 'hardware';
}
```

### Stopping Notification Loops
Email → creates incident → incident creates notification → notification replied to → loop

Prevention:
1. Mark auto-generated emails so they don't trigger inbound actions
2. Check `email.header.x-servicenow-generated` before processing
3. Use "Self-generated" rule type to filter SN-generated emails

---

## SMS Notifications

SMS notifications are typically used for:
- On-call alerting for P1 incidents
- Time-sensitive approval requests
- Critical system alerts

### SMS Configuration
- Requires an SMS provider integration (e.g., Twilio, OpenMarket)
- Configured similarly to email notifications
- Users must have a mobile phone number on their user record
- SMS content is limited in length — keep messages concise

---

## Push Notifications (Mobile)

Push notifications appear on users' mobile devices via the ServiceNow Mobile App:

- Supported for incidents, changes, approvals, and custom records
- Requires ServiceNow Mobile configuration
- Supports actionable notifications (approve/reject directly from notification)
- Configured at: System Notification → Push → Notifications

---

## Slack and Microsoft Teams Integration

### Slack
Via IntegrationHub Slack Spoke:
- Post messages to channels
- Send direct messages to users
- Receive slash command responses
- Interactive messages with buttons (approve/reject)

Flow Designer step: "Send a Message to Slack Channel"

### Microsoft Teams
Via IntegrationHub Teams Spoke or adaptive cards:
- Post cards to Teams channels
- Actionable notifications (user clicks buttons in Teams to approve/update)
- Webhook-based for simpler integrations

---

## Notification Preferences and Subscriptions

Users can manage their notification preferences:
- **Navigation:** User profile → Notifications
- Subscribe or unsubscribe from specific notification types
- Set preferred channel (email, SMS, push)
- Configure "Do Not Disturb" hours

### Subscription Types
Administrators can configure which notifications are subscribable:
- **Mandatory:** Cannot be unsubscribed (SLA breach, security alerts)
- **Subscribable:** Users opt in (progress updates, team activity)

### Digest Notifications
Digest notifications bundle multiple individual notifications into a single periodic summary email:
- Prevents inbox flooding from high-volume activities (e.g., many comment updates)
- Scheduled at user-defined intervals (hourly, daily)
- Configured per notification type

---

## Notification Troubleshooting

### Why Isn't My Email Being Sent?

**Step 1: Check Outbound Email**
Navigate to System Mailboxes → Outbound:
- Are emails being generated and queued?
- Check status: Ready, Sent, Error, Skipped

**Step 2: Check SMTP Configuration**
System Properties → Email → Outbound:
- SMTP server configured?
- SSL/TLS settings correct?
- Authentication configured?

**Step 3: Check Notification Conditions**
Review the specific notification record:
- Are conditions being met?
- Is the notification Active?
- Are recipients populated?

**Step 4: System Property Check**
- `glide.email.smtp.active = true` — Global email sending enabled
- `glide.email.outbound.enabled = true` — Outbound email enabled
- `glide.email.test.user` — If set, ALL emails go to this address (testing mode)

**Step 5: Email Logs**
Navigate to System Mailboxes → Inbound/Outbound → view specific email record for error details.

### Email Log Fields

| Field | Description |
|-------|-------------|
| `type` | Inbound or Outbound |
| `from` | Sender |
| `to` | Recipient |
| `subject` | Subject line |
| `created_on` | When email was generated |
| `sent` | Whether email was sent |
| `error_msg` | Error details if sending failed |
| `state` | Ready, Sent, Draft, Error |

---

## Best Practices

### Notification Design
- One notification per business event (avoid duplicating similar notifications)
- Name notifications clearly: `[Table] - [Event] - [Audience]` (e.g., "Incident - Assigned - Assignee")
- Always test with impersonation using a non-admin account before going live
- Check notification frequency — frequent updates on busy tables can generate email spam

### Content Quality
- Include a link to the record in every notification (`${URI_REF}`)
- Include the record number and short description in the subject line
- Keep emails concise — excessive detail is not read
- Use HTML templates for professional branding

### Performance
- Avoid synchronous GlideRecord queries in notification "advanced condition" scripts
- Use events for notifications triggered by complex conditions — fire event in Business Rule, notification listens to event
- Schedule digest notifications for high-volume update events

### Governance
- Document all notifications and their triggers in a notification registry
- Review and disable obsolete notifications annually
- Monitor email volume metrics — spikes may indicate misconfigured conditions

---

## Common Patterns

### Assignment Notification
Fire when `assignment_group` or `assigned_to` changes:
- Recipients: New `assigned_to`, `assignment_group.manager`
- Subject: `[${priority}] ${number} assigned to you: ${short_description}`
- Body: Record details + link + SLA due date

### Caller Resolution Notification
Fire when `state` changes to 6 (Resolved):
- Recipients: `caller_id`, `watch_list`
- Subject: `${number} Resolved: ${short_description}`
- Body: Resolution notes + link to confirm/reopen

### Manager SLA Alert
Triggered by SLA event at 75%:
- Recipients: `assigned_to.manager`, `assignment_group.manager`
- Subject: `SLA Warning: ${number} approaching breach in ${sla_due}`
- Body: Current status + SLA elapsed percentage + action required

### On-Hold Notification to Caller
Fire when `state` changes to 3 (On Hold) and `hold_reason` is 1 (Awaiting Caller):
- Recipients: `caller_id`
- Subject: `Action Required: ${number} - Information Needed`
- Body: Explanation of what information is needed + link to provide response
