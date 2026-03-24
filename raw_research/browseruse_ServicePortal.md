# ServicePortal

Source: browser-use task ff22ac9c-77bd-424f-a7e9-d24d13111e65
Steps: 22 | Cost: $0.132 | Success: True

I have successfully extracted all the requested information regarding ServiceNow Service Portal. Here is the comprehensive summary:

### 1. Service Portal Architecture
- **Framework**: A set of APIs, Angular services, directives, and tools.
- **Portal**: A group of pages linked by page IDs. The URL suffix determines the portal and its theme.
- **Pages**: Store portal content and have no fixed relationship to portal records; they exist independently.
- **Widgets**: The modular components of a page. Each instance of a widget on a page is a 'Widget Instance'.
- **Themes**: Define the overall look and feel, which can be overridden by specific style configurations.

### 2. Portal Configuration
- **Access**: Via 'Service Portal > Service Portal Configuration' or by appending `/sp_config` to the instance URL.
- **Branding & Navigation**: Managed through the configuration page tiles (Branding Editor, Designer, Page Editor).
- **Header/Footer**: Configured at the Portal record level, allowing for custom widgets to be used as headers or footers.

### 3. Widget Development
- **HTML Template**: Renders the dynamic view using AngularJS.
- **Client Script**: Acts as the controller, processing data and handling user input via the `c.data` and `c.options` objects.
- **Server Script**: Initializes the widget state, queries the database, and sends data to the client via the `data` object.
- **Interaction**: The server script runs first, then the client script. `server.update()` is used to send data from the client back to the server.

### 4. Angular Providers and Data Binding
- **Types**: Directive, Factory, and Service.
- **Benefits**: Used to share context between widgets, persist state, and create reusable UI behaviors.
- **Implementation**: Registered in the 'Widget Angular Provider' table and injected into widget client controllers.

### 5. sp_widget Table and Widget Instances
- **sp_widget**: The table where the base definition of a widget (HTML, CSS, Scripts) is stored.
- **Widget Instances**: Represent a specific application of a widget on a page. Instances can have unique 'options' (defined via Option Schema) that change their behavior without altering the base widget code.

### 6. URL Structure and Routing
- **Format**: `https://<instance>/<portal suffix>/<guest language>/<keywords>?id=<page id>&lang=<language>&<page parameters>`
- **Routing**: The `id` parameter determines which page is loaded within the portal frame.

### 7. Service Portal vs. Employee Center
- **Employee Center**: Best-practice based, highly scalable, uses unified taxonomy for AI Search, and is multi-departmental.
- **Service Portal**: Often starts from a 'demo' design, requires manual creation of topic pages, and content is typically siloed by department.

### 8. Performance Optimization
- **Performance Analyzer**: A tool to evaluate pages against benchmarks like Widget Load Time, ACL Execution, and DB Call Execution.
- **Optimization**: Focuses on optimizing server scripts, reducing synchronous AJAX calls, and minimizing heavy database queries within widgets.
