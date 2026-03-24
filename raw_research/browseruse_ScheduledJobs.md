# ScheduledJobs

Source: browser-use task 36e4bb16-f39e-4b71-b1f2-f06ae71242f0
Steps: 27 | Cost: $0.162 | Success: True

I have extracted the following information from the ServiceNow documentation:

1) **Scheduled Jobs Types**:
   - **Basic Types**: Include automatically generating and distributing reports, and generating/scheduling entities of records (incidents, change items, etc.) from templates.
   - **Execute Script**: Jobs that run custom scripts at specific times or intervals.
   - **States**: Ready (waiting for next interval), Running (executing), Queued (waiting in scheduler), and Error.

2) **Scheduled Script Executions**:
   - **Creation**: Created via the 'Scheduled Script Execution' module (sysauto_script table).
   - **Scheduling (Run field)**: Options include Daily, Weekly, Monthly, Periodically, Once, On Demand, and Business Calendar.
   - **Conditional Execution**: A 'Conditional' checkbox enables a 'Condition' script field. The job only runs if the script evaluates to true.
   - **Script Field**: Contains the JavaScript to be executed.

3) **Fix Scripts**:
   - **Purpose**: Used to automate configuration changes or data migrations, typically during application installation or upgrades.
   - **Execution**: Designed for one-time execution but can be run multiple times if needed. They are preferred over Background Scripts for deployable changes.

4) **Background Scripts**:
   - **Purpose**: An admin utility for running arbitrary JavaScript code on the server immediately. Used for troubleshooting or one-off data corrections.

5) **System Scheduler**:
   - **sys_trigger table**: The core table where all scheduled tasks (including Scheduled Jobs) are stored as individual 'Schedule Items'.
   - **Recommendation**: Do not manually manipulate records in sys_trigger; use the Scheduled Jobs module instead.

6) **Job Execution Context and Impersonation**:
   - **Run As**: Scheduled jobs can be configured to run as a specific user (impersonation). If left blank, they typically run as 'System'.
   - **Sandbox**: Conditional scripts run in a restricted sandbox for security.

7) **Performance Considerations**:
   - Long-running jobs can consume worker threads. It is recommended to optimize scripts and avoid long-running loops. Large data processing should be batched.

8) **Event-driven Scheduling**:
   - Actions can be scheduled to occur after a specific event using the 'gs.eventQueueScheduled()' method, which adds an entry to the scheduler to fire an event at a future time.
