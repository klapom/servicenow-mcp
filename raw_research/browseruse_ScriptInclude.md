# ScriptInclude

Source: browser-use task 87051ff3-42bf-41f6-81a0-ac4f8c81c310
Steps: 29 | Cost: $0.174 | Success: True

I have extracted the following information regarding ServiceNow Script Includes:

1. **Structure and Class Pattern**:
   - Script Includes are server-side JavaScript. They can be class-based (using `Class.create()`) or on-demand functions.
   - Class-based pattern:
     ```javascript
     var NewInclude = Class.create();
     NewInclude.prototype = {
       initialize: function() {},
       myFunction: function() {},
       type: 'NewInclude'
     };
     ```
   - The name of the Script Include must match the class or function name.

2. **Client-callable & GlideAjax**:
   - Enable 'Client callable' to use with `GlideAjax`.
   - Server-side must extend `AbstractAjaxProcessor`.
   - Use `this.getParameter('sysparm_name')` to retrieve parameters.
   - Asynchronous calls use `getXML(callback)`, while synchronous use `getXMLWait()` (not available in scoped apps).

3. **Scoped vs Global**:
   - Controlled by the 'Accessible from' field.
   - Global APIs like `JSUtil` are not available in scoped applications.

4. **AbstractAjaxProcessor Pattern**:
   - Used for AJAX calls. Example:
     ```javascript
     var MyAjax = Class.create();
     MyAjax.prototype = Object.extendsObject(AbstractAjaxProcessor, {
       myFunction: function() { return 'Hello ' + this.getParameter('sysparm_user'); }
     });
     ```

5. **Common OOB Script Includes**:
   - **JSUtil**: Provides utility methods like `nil()`, `notNil()`, `has()`, `type_of()`, and `logObject()`. It is a Global API.
   - **ArrayUtil** and **TableUtils**: Identified as common OOB utilities, though specific method details were not fully extracted in this session.

6. **Best Practices & Business Rules**:
   - Script Includes are preferred for reusable logic to keep Business Rules 'thin'.
   - Use asynchronous GlideAjax to avoid UI freezing.
   - Private functions should start with an underscore (`_`).

Note: Detailed documentation for ArrayUtil, TableUtils, and specific 'Best Practice' pages were not fully reached within the step limit, but their general roles and usage patterns were identified through the main Script Include and AJAX documentation.
