# SLA

Source: browser-use task d4e881ad-8a06-470c-a639-c4ec241ddb4a
Steps: 22 | Cost: $0.132 | Success: True

I have successfully extracted all requested information regarding ServiceNow SLAs from the official documentation.

### 1) SLA Definitions and Task SLA Tables
- **SLA Definition Table (`contract_sla`)**: Stores the configuration of SLAs. Key fields include:
  - **Name**: Identifies the SLA.
  - **Type**: SLA, OLA, or Underpinning Contract (UC).
  - **Target**: Response or Resolution.
  - **Table**: Any table extending `task` (e.g., incident, change_request).
  - **Duration**: User-specified (fixed time) or Relative (scripted).
  - **Schedule**: Defines business hours (e.g., 8-5 weekdays).
- **Task SLA Table (`task_sla`)**: Stores individual SLA instances attached to tasks. It includes timing fields like:
  - **Start/Stop/Breach time**.
  - **Actual/Business Elapsed Time/Percentage/Left**.
  - **Original Breach Time**: The initial calculation of when the SLA would breach.

### 2) SLA Types
- **Response SLA**: Typically measures the time between when a task is created and when it is acknowledged or assigned.
- **Resolution SLA**: Measures the time to resolve the task.

### 3) SLA Stages and States
The `task_sla` record transitions through the following stages:
- **In Progress**: SLA is active and timing is accumulating.
- **Paused**: Timing is suspended based on pause conditions.
- **Completed**: Stop conditions were met before the breach.
- **Breached**: The elapsed time exceeded the allowed duration.
- **Cancelled**: Start conditions were no longer met or cancel conditions were triggered.

### 4) Pause and Resume Conditions
- **Pause Condition**: Defines when the SLA clock stops (e.g., State is 'On Hold').
- **Resume Condition**: Defines when the clock starts again (e.g., State is 'Active').
- *Note*: If Pause conditions are a subset of Start conditions, the SLA may cancel or remain permanently paused depending on configuration.

### 5) Retroactive Start and Pause
- **Retroactive Start**: Adjusts the SLA start time to a past event (e.g., 'Created' or 'Opened' time of the task) rather than the moment the SLA attached.
- **Retroactive Pause**: Calculates and applies any pause time that would have occurred between the retroactive start time and the current time, preventing immediate breaches.

### 6) SLA Breach and Escalation Workflows/Flows
- **Flows for SLA**: Modern replacement for workflows (starting Orlando/Yokohama).
- **Default SLA Flow**: Sends notifications at specific thresholds.
- **SLA Notification and Escalation Flow**:
  - **50%**: Notifies assignee and CI 'Supported by' user.
  - **75% & 100%**: Notifies assignee and their manager.
- **Workflow Property**: `com.snc.sla.workflow.run_for_breached` controls if workflows trigger for SLAs that are already breached upon attachment.

### 7) SLA Calculation (Schedules & Timezones)
- **Calculation Logic**: Breach time = Start Time + Duration + Pause Duration (within the defined schedule).
- **Schedules**: If no schedule is selected, the SLA runs 24/7. Days are converted to 24-hour blocks.
- **Timezones**: Can be sourced from the Caller, SLA Definition, CI Location, or Task Location. If empty, it falls back to the System Timezone.

### 8) Properties and Configuration
- **com.snc.sla.calculation.percentage**: Default 1000%; stops calculations for long-breached records.
- **com.snc.sla.repair.enabled**: Enables the SLA Repair feature to recalculate records.
- **Logging**: Adjustable levels (Info, Debug, etc.) for `TaskSLAController`, `SLAConditionBase`, and `SLARepair`.
