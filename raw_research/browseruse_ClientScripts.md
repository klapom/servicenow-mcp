# ClientScripts

Source: browser-use task b30cbcac-8d81-4b01-a031-4b3cc7b73e33
Steps: 24 | Cost: $0.144 | Success: True

I have successfully extracted the requested information from the ServiceNow documentation. Here is the complete summary:

### 1. Client Script Types
- **onLoad()**: Runs when a form is first rendered, before users can enter data. Used for setting default values or manipulating the form layout.
- **onSubmit()**: Runs when a form is submitted. Used for validation; returning `false` cancels the submission.
- **onChange()**: Runs when a specific field value changes. Parameters include `control`, `oldValue`, `newValue`, `isLoading`, and `isTemplate`. Note: `control` is not accessible in Mobile/Service Portal.
- **onCellEdit()**: Runs when a cell value is changed in a list. Applies to list editing rather than form editing.

### 2. g_form API Methods
- **setValue(fieldName, value)**: Sets the value of a field.
- **getValue(fieldName)**: Retrieves the current value of a field.
- **setVisible(fieldName, visible)**: Shows or hides a field.
- **setMandatory(fieldName, mandatory)**: Makes a field mandatory or optional.
- **setReadOnly(fieldName, readOnly)**: Makes a field read-only or editable.
- **addOption(fieldName, value, label)**: Adds an option to a choice list.
- **clearOptions(fieldName)**: Removes all options from a choice list.

### 3. g_user Object Properties
- **userName**: The username of the current user.
- **userID**: The `sys_id` of the current user.
- **hasRole(roleName)**: A method to check if the current user has a specific role.

### 4. UI Policies
- **Conditions**: Built using the condition builder; evaluated when the form loads and when fields change manually.
- **Actions**: Can set fields to Mandatory, Visible, or Read-only (True/False/Leave alone).
- **Reverse if false**: If checked, the action is undone when the condition evaluates to false.
- **Scripting**: 'Execute if true' and 'Execute if false' scripts can be used for advanced logic.

### 5. Client Script vs. UI Policy: When to Use Which
- **UI Policies** should be preferred for making fields mandatory, visible, or read-only because they offer **faster load times** and better performance.
- **Client Scripts** should be used for more complex logic that UI Policies cannot handle, such as validating data on submission or complex field-level calculations.

### 6. Performance Best Practices
- **GlideAjax**: Use asynchronous `GlideAjax` for server calls to prevent the browser from freezing (avoid synchronous calls).
- **Minimize Server Calls**: Reduce the number of calls to the server to improve form responsiveness.
- **Strict Mode**: New scripts run in strict mode with limited DOM access to ensure better performance and compatibility.

### 7. Mobile and Service Portal Considerations
- **API Limitations**: Not all `g_form` methods or JavaScript APIs are supported in Mobile or Service Portal environments.
- **UI Type**: UI Policies and Client Scripts have a 'UI Type' field to specify if they should run on Desktop, Mobile/Service Portal, or Both.
- **Compatibility**: Client scripts are generally not supported on legacy ServiceNow mobile applications; modern mobile apps require scripts to be compatible with the mobile API subset.
