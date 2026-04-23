---
title: ServiceNow Customizing — Architektur-Leitlinien
slug: customization_architecture_guidelines
scope: customizing
tags: [customizing, architecture, abl, scoped-apps, upgrade-safe, scripting, dictionary-override, update-sets, integrations, platform-health]
entities: [business_rule, client_script, ui_policy, ui_action, sys_dictionary, sys_dictionary_override, scoped_app, update_set, sys_update_xml, scripted_rest_api, flow_designer, atf]
version: ServiceNow — general (April 2026)
source: browser-use + curated (2026-04-22)
reviewed: 2026-04-22
---

# ServiceNow Customizing — Best Practices & Architektur-Leitlinien

> **Stand:** April 2026
> **Zweck:** Umfassende Sammlung von Best Practices für ServiceNow Customizing, Configuration und Custom Development. Alle Empfehlungen sind quellenvalidiert und werden regelmäßig erweitert.
> **Inhaltsverzeichnis**
> - [1. Kernprinzipien](#1-kernprinzipien)
> - [2. Application Builder Layer (ABL)](#2-application-builder-layer-abl)
> - [3. Scripting: Business Rules & Client Scripts](#3-scripting-business-rules--client-scripts)
> - [4. UI Policies & Client Scripts im Vergleich](#4-ui-policies--client-scripts-im-vergleich)
> - [5. UI Actions & UX Design](#5-ui-actions--ux-design)
> - [6. Tables, Fields & Dictionary Overrides](#6-tables-fields--dictionary-overrides)
> - [7. Scoped Applications](#7-scoped-applications)
> - [8. Update Sets & Change Management](#8-update-sets--change-management)
> - [9. Integrations & APIs](#9-integrations--apis)
> - [10. Performance & Optimierung](#10-performance--optimierung)
> - [11. Testing (ATF)](#11-testing-atf)
> - [12. Upgrade-Safe Customization](#12-upgrade-safe-customization)
> - [13. Access Control Lists (ACLs)](#13-access-control-lists-acls)
> - [14. Flow Designer & Workflow Automation](#14-flow-designer--workflow-automation)
> - [15. Service Catalog & Variable Sets](#15-service-catalog--variable-sets)
> - [16. Scripted REST APIs](#16-scripted-rest-apis)
> - [17. Design Principles & Platform Health](#17-design-principles--platform-health)
> - [18. Reference Liste](#18-reference-liste)

---

## 1. Kernprinzipien

### 1.1 Configuration vs. Customization vs. Custom Development

| Begriff | Definition | Beispiel |
|---|---|---|
| **Configuration** | Anpassung der Standardfunktionalität ohne Baseline-Code-Änderung | UI-Policies, Flow Designer, Formulare, ACLs, System Properties |
| **Customization** | Änderung des bestehenden Baseline-Codes | Business Rules, Client Scripts, UI Scripts, Workflow-Änderungen |
| **Custom Development** | Vollständig neue Funktionalität | Eigene Tabellen, Scoped Applications, Script Includes, REST/SOAP APIs |

### 1.2 Die goldenen Regeln

1. **OOTB first (Out-of-the-Box zuerst):** Prüfe immer zuerst, ob Standardfunktionalität ausreicht.
2. **Configuration over Customization:** Konfiguration hat Vorrang vor Code-Änderungen.
3. **Low Code / No Code over High Code:** Nutze Flow Designer, UI Policies und IntegrationHub bevor du scriptest.
4. **Minimiere Customization:** Customization sollte die Ausnahme, nicht die Regel sein.
5. **Document all changes:** Jede Änderung muss dokumentiert und getestet werden.

### 1.3 Validierung: Der Bscore-Ansatz

Jede Customization sollte gegen einen Business Score (Bscore 1–5) geprüft werden:

| Bscore | Anforderung | Beispiele |
|---|---|---|
| **1** | Geringer Einfluss | Unwichtige Felder hinzufügen, UI-Policies |
| **2** | Moderater Einfluss | Etwas Customization, geringe Upgrade-Auswirkung |
| **3** | Erheblicher Einfluss | Table Extensions, UI Scripts — **Mindestanforderung für Extensions** |
| **4** | Schwerwiegender Einfluss | Baseline-Code ändern, große Upgrade-Auswirkung |
| **5** | Kritischer Einfluss | Baseline-Business Rules ändern — **nur mit starker Begründung** |

### 1.7 Build vs. Buy — Entscheidungshilfe

Bevor du etwas selbst baust:

- Prüfe erst **native Plattform-Funktionalität** — OOTB löst oft 80–100% der Anforderungen.
- Prüfe zuerst **Store Apps und zertifizierte Partner-Lösungen** — sie sind upgrade-sicher und gut dokumentiert.
- **Configurieren statt programmieren**: UI Policies, ACLs, Dictionary, Forms als Standard.
- **Custom Code als letztes Mittel**: Nicht als erste Wahl.

---

## 2. Application Builder Layer (ABL)

### 2.1 ABL-Schichten (von unten nach oben)

1. **Platform** (Base) — Kerntabellen, APIs, Framework
2. **Application Suites** — ITSM, HRSD, CSM, ITOM usw.
3. **Customization** — Änderungen an Suite-Assets
4. **Custom Development** — Eigene Scoped Applications

### 2.2 ABL-Best-Practices

- **Never copy objects** — update objects in place wherever possible.
- **Default to "add before edit"** — neue Felder hinzufügen statt bestehende Typen ändern.
- **Use the ServiceNow no- and low-code capabilities wherever possible.**
- **Use scoped applications as your default for any new custom development.**
- **Document all customizations** with business justification.
- **Create tests for all customizations** using ATF.
- **Use HealthScan regularly** to identify unnecessary customizations.

---

## 3. Scripting: Business Rules & Client Scripts

### 3.1 Business Rules — Best Practices

#### Core Principles
- Server-side scripts running on record operations (insert, update, delete, query, display).
- They ensure data integrity and run regardless of access method (UI, API, import).

#### Four Rule Types

| Typ | Zeitpunkt | Verwendung | Besonderheit |
|---|---|---|---|
| **Before** | Pre-commit | Validierung, Auto-Population, Abort-Kontrol | Modifications save automatically |
| **After** | Post-commit | Related Record Updates, Audit Logging | Requires explicit save commands, blocks user |
| **Async** | Background (Scheduler) | Emails, REST Calls, Heavy Processing | Non-blocking, avoids UI delays |
| **Display/Query** | Form-load / Pre-query | Form-load rules pass server data; query rules apply filters | Only runs when records are displayed/queried |

#### Execution Order
1. onSubmit Client Scripts
2. Before Business Rules (Order <1000)
3. Engines/Workflows (Order 1000)
4. Before Business Rules (Order ≥1000)
5. Database Commit
6. After Business Rules
7. Async Business Rules

#### Best Practices
- **Avoid global business rules** — always restrict to specific tables. Global Business Rules run on every table in the instance, which can significantly impact performance.
- **Always apply conditions** to limit rule scope.
- **Use Async rules** for external calls or heavy computation.
- **Never call update() inside a Before BR** — changes auto-commit; calling update() triggers infinite recursion.
- **Prefer declarative field assignments** over custom scripting.
- **Use `gs.log()` instead of `gs.info()` or `gs.debug()` in scoped apps** — legacy logging commands may fail silently.
- For post-save updates, **disable workflow triggers** to prevent loops.

---

### 3.2 Client Scripts — Best Practices

#### Core Principles
- Browser-side scripts — keep them lean to preserve performance.
- Cannot perform security checks (client-side code is visible).

#### Guidelines
- **Minimize DOM Manipulation** by leveraging platform APIs.
- **Use `g_form` API Efficiently:** for field interactions.
- **Debounce or Throttle Events** to restrict frequent triggers.
- **Never process confidential data** — browser-side code remains visible to users.
- Configure to load/execute on **specific tables only**.
- Consider **inheritance by child tables** carefully.
- Use UI policies instead of scripts where possible.
- Use `< 1000ms` performance threshold for rules.

#### Performance Tips
- Use a UI policy instead of script where possible.
- Keep client scripts small and focused.
- Avoid heavy DOM manipulation.
- Use `g_form.getValue()` and `g_form.setValue()` for field access.
- Use `g_form.setMandatory()` / `g_form.setDisplay()` for field control.
- Consider `g_form.addInfoMessage()` / `g_form.addErrorMessage()` for user feedback.

---

## 4. UI Policies & Client Scripts im Vergleich

### 4.1 Entscheidungsmatrix

| Anforderung | Empfohlene Lösung |
|---|---|
| Feld sichtbar/unsichtbar machen | **UI Policy** |
| Feld mandatory/read-only setzen | **UI Policy** |
| Default Value auf Formular setzen | **UI Policy** |
| Feldberechnung (clientseitig) | **Client Script** |
| Abhängige Felder mit Logik | **Client Script** |
| Komplexes Formular-Verhalten | **Client Script** |
| Best für basic UI modifications | **UI Policy** |
| Prioritize over Client Scripts for simple UI changes | **UI Policy** |

### 4.2 UI Policy Best Practices
- set **onLoad** to **false** if you do **not** need to execute on page load
- Use as **few** UI Policies as possible to avoid long page load times
- Apply conditions using the Condition **Builder** whenever **possible** so unnecessary UI Policy scripts do not load
- Use the **Short** description field to document the UI Policy
- Add the **Description** field to the form to thoroughly document the UI Policy
- **Comment** your scripts!!

---

## 5. UI Actions & UX Design

### 5.1 UI Action Best Practices
- **Give each UI action a distinct action name.**
- **Use conditions in UI actions** to control visibility.
- **Use buttons, menus, and links appropriately** in forms and lists.
- Give each UI action a clear, distinct name for easy organization.
- Use distinct and meaningful names — makes actions easy to find.
- Use conditions in UI actions to restrict when they appear.
- Use buttons for forms, menus for lists, and links for both.
- **Never let UI actions override table-level permissions** — they create dangerous security gaps.
- Align interactions with **Access Control Lists (ACLs)** and apply checks like `gs.hasRole()`.

### 5.2 UX Principles
- **Simplicity wins. Reduce clicks, clutter, and cognitive load.**
- Use UI Builder for component-based, reusable UI elements.
- Focus on enabling users to do their jobs effectively with minimal friction.

---

## 6. Tables, Fields & Dictionary Overrides

### 6.1 Table Extension vs. Custom Table

| Kriterium | Table Extension | Custom Table |
|---|---|---|
| Erbt Felder vom Parent | Ja | Nein |
| Erbt Business Rules | Ja | Nein |
| Erbt Workflows | Ja | Nein |
| Erbt SLAs/Assignments | Ja | Nein |
| Anwendungsbereich | Erweitert bestehende Funktionalität | Komplett neue, unabhängige Tabelle |

**Empfehlung:** Extend whenever possible — it "reuses existing fields, logic, and behavior from a parent table." Only create standalone tables when your data structure fundamentally differs from existing modules.

### 6.2 Dictionary Overrides — Best Practices

**When to Use:**
Apply when modifying a field property on a parent table would unintentionally propagate to unrelated child records. They isolate configurations to specific extended tables.

**What to Override:**
Modify specific dictionary entry properties like default values, mandatory flags, or reference qualifiers via the parent table's override related list.

**Guidelines:**
- Overrides cascade downward through the class hierarchy, requiring additional rules for deeper descendants.
- "Align state values across applications" and "try to keep them aligned across all the applications."
- This consistency allows teams to "make a report on the Task table, and see all closed tasks with one filter, rather than lots of OR conditions."

**Examples:**
1. Default States: Changing the `State` default on the `Task` table alters `Incident` and `Problem` unintentionally. Revert `Task` to its original value, then add an override specifically for the `Incident` table.
2. CMDB Hierarchy: Defining a default for `cmdb_ci.install_status` on `cmdb_ci_hardware` propagates to all hardware descendants. If `cmdb_ci_computer` needs a different value, create a separate override.

### 6.3 Task Table Management

- Keep **active task records < 10%** — "approximately 95% of all operations are related to the task table."
- **Timeboxing queries** — filter using indexed date/time fields (`opened_at`, `sys_created_on`, `sys_updated_on`).
- "Only returning data sets from the task table which have some kind of data/time field."
- "The 'task' table hierarchy could grow in terms of total number of records."
- Use **archiving** to offload historical data.
- "Exercising caution when designing/creating new custom tables which extend the task hierarchy."
- Use **database views** to simplify cross-table joins.

---

## 7. Scoped Applications

### 7.1 Why Scoped Applications?
Scoped applications function as isolated development environments. "Your table names, API endpoints, and class names live in a distinct scope." This prefix system prevents namespace collisions by automatically appending prefixes to all artifacts.

### 7.2 Benefits

| Benefit | Beschreibung |
|---|---|
| **Namespace Isolation** | Prefixes prevent naming conflicts across applications |
| **Upgrade Safety** | "ServiceNow updates the base platform; your scoped code is untouched." |
| **Security** | Independent security policies, but not complete isolation |
| **Packagability** | Export as update sets or publish directly to ServiceNow Store |
| **Multi-Tenant** | "Scoped apps ensure customer A's customizations don't leak into customer B's instance." |
| **Team Collaboration** | "Multiple developers can work on different scopes without merge conflicts." |

### 7.3 Security Considerations
- Scope isolation provides code separation but **not** complete security isolation.
- Admins with global privileges can still query scoped tables via backend scripts.
- "Design your scoped application assuming a knowledgeable admin might inspect it."
- Never hardcode credentials. Use ServiceNow's credential store.

### 7.4 Cross-Scope References
- Intentional global table references remain possible across boundaries.
- Use proper cross-scope reference patterns for controlled access.

### 7.5 Publishing & Distribution
- Applications export as XML update sets that automatically track dependencies.
- "The scoped app is the unit of delivery."
- After validation, products launch as versioned offerings supporting one-click installation.

---

## 8. Update Sets & Change Management

### 8.1 Best Practices

| Empfehlung | Beschreibung |
|---|---|
| **Work in a scope** | Create and collect additive changes in scoped applications |
| **Use scoped apps as default** | For any new custom development |
| **Document all customizations** | With business justification |
| **Create tests for all customizations** | Using ATF |
| **Use HealthScan regularly** | To identify unnecessary customizations |
| **Avoid copying objects** | Update objects in place wherever possible |
| **Add before edit** | Add fields, don't change existing field types |
| **Use no/low code** | Flow Designer, UI Policies, IntegrationHub over custom scripting |

---

## 9. Integrations & APIs

### 9.1 Integration Patterns

| Pattern | Verwendung | Performance |
|---|---|---|
| **Sync direct** | Simple calls, small payloads | Poor scalability, stalls thread |
| **Async direct (no response)** | Fire-and-forget | Scheduler lag, stalls worker |
| **Async direct (with response)** | BR processing needed | Double lag, stalls worker |
| **Async via MID (no response)** | Private endpoints | Lag, stalls MID |
| **Async via MID (with response)** | Full control | Multiple lags, stalls MID |

### 9.2 MID Server
- If no MID server is specified, integrations run directly from application nodes.
- Specify a MID server for private endpoints or to shift load away from instance threads.
- Runtime overrides via `setMIDServer()`.

### 9.3 Timeout Configuration
- **Connection timeout:** `glide.http.connection_timeout` (default 10s)
- **Request timeout:** `glide.http.timeout` (default 175s, via `setHttpTimeout()`)
- **ECC response timeout:** Capped at 30s with `glide.http.outbound.max_timeout`

### 9.4 Response Handling
- Avoid `setEccTopic()` for custom workflows on MID.
- Use `setEccCorrelator()` with `setEccParameter('skip_sensor', 'true')`.
- Capture replies via after-insert BR on `ecc_queue`.
- Never call `waitForResponse()`, `getBody()`, or `getStatusCode()` after `executeAsync()` — "effectively makes the system synchronous again."

### 9.5 Security
- Validate all user inputs.
- Store sensitive details in secure configuration files or encrypted fields.
- Use `gs.hasRole()` for permission checks.

---

## 10. Performance & Optimierung

### 10.1 Die 12 Techniken

| # | Technik | Beschreibung |
|---|---|---|
| 1 | **Strategic Database Indexing** | Create composite indexes on queried fields, monitor slow SQL log, remove unused indexes |
| 2 | **Optimize Business Rules** | Add timing logs, avoid nested queries, use `getValue()` instead of `getRecord()`, mark non-critical as async |
| 3 | **Refactor Flows** | Eliminate subflow-heavy flows, batch DB ops, migrate high-volume flows to BRs (40-60% faster) |
| 4 | **Configure GlideQuery API** | Faster than GlideRecord for filtering/aggregates, reduces memory overhead |
| 5 | **Database View Tables** | Pre-computed joins for complex reports, avoids runtime joins across 3+ tables |
| 6 | **Minimize Form Fields** | Remove unused fields, disable unnecessary lookups, use dependent dropdowns |
| 7 | **Intelligent Change Set Filters** | Filter by created date, state, active status to reduce memory/DB load |
| 8 | **Tune Scheduled Jobs** | Add conditions, schedule off-peak, batch large updates with limit/offset |
| 9 | **Configuration Caching** | Cache config data in memory/cache tables, reduces DB queries by 40-60% |
| 10 | **Real-Time Metrics** | System Diagnostics > Performance Analytics, monitor response time, DB CPU, slow transactions |
| 11 | **Optimize AI Agent Studio** | Cache LLM outputs, streamline input data, use timeouts, monitor logs |
| 12 | **Dedicated Instances** | Isolate heavy processing to dedicated instances |

### 10.2 GlideRecord Best Practices
- "Use the appropriate object methods based on your scope — GlideRecord or Scoped GlideRecord"
- Use GlideAggregate instead of `getRowCount()` for large tables
- Perform all record queries in server-side scripts
- Use `_next()` and `query()` for tables containing `next` and `query` columns
- "Always use hasNext() before calling next()" to prevent iteration errors
- "Look for ways to perform operations in bulk rather than looping through records"
- Index your query fields to enhance performance
- Combine pagination methods with sorting to avoid inconsistencies
- Use dynamic scripting techniques to adapt to changing table structures

### 10.3 Performance Rules
- "Avoid table scans, heavy scripts, excessive flows, and unnecessary triggers."
- "Use specific queries to retrieve only the necessary data."
- "Limit the Number of Fields Retrieved" to reduce network overhead.
- "Validate all user inputs to prevent script injection attacks."
- "Store sensitive details in secure configuration files or encrypted fields."
- Enable session debugging to view real-time outputs.
- Monitor the `sys_log` table for severity markers.
- Use the Script Tracer for detailed execution timelines.
- Check transaction logs to isolate rules exceeding the 100ms performance threshold.

---

## 11. Testing (ATF)

### 11.1 Automated Test Framework (ATF)

**What ATF can test:**
- Functional testing of business logic
- Browser compatibility testing
- Workflow validation
- Integration verification

**What ATF CANNOT do:**
- **NOT** a load testing or performance testing application
- **NOT** suitable for UI visual testing
- **NOT** for security penetration testing

### 11.2 ATF Best Practices
- Create tests for all customizations
- Automated tests must not depend on existing test data — create all required data within the test
- Use test suites for organized test execution
- Test critical business logic paths first
- Run tests after every upgrade
- Maintain test data separately from production data
- Use test conditions that cover edge cases
- Test both happy paths and error scenarios

---

## 12. Upgrade-Safe Customization

### 12.1 Safe vs. Unsafe Customizations

| Upgrade-Safe ✅ | Upgrade-Hostile ❌ |
|---|---|
| UI Policies instead of Client Scripts | Overriding or modifying OOTB scripts directly |
| Flow Designer instead of legacy Workflows | Heavy Client Script manipulation |
| Business Rules with clear conditions | Hard-coded sys_id references |
| Dictionary overrides (used sparingly) | Customizations that replicate OOTB logic |
| Script Includes (scoped, documented) | DOM manipulation or unsupported UI hacks |
| OOTB extension points | Changes without update set tracking |

### 12.2 The Core Rule
The fundamental distinction is whether changes extend or override the platform. "The key distinction is whether a customization extends the platform or overrides it." Safe approaches survive upgrades with minimal remediation.

### 12.3 Upgrade Checklist
- Prefer configuration over customization
- Audit client scripts and UI actions before every upgrade
- Remove deprecated or unused custom code
- Test upgrades with real production scenarios, not just happy paths
- Document the business reason for every customization
- Review skipped changes after each upgrade
- Use HealthScan to identify risky customizations
- Maintain thorough documentation and automated testing

---

## 13. Design Principles & Platform Health

### 13.1 The 5 Platform Health Principles

| Prinzip | Beschreibung |
|---|---|
| **Manageability** | "If the customer cannot maintain it, it is not a good design." |
| **Performance** | "Avoid table scans, heavy scripts, excessive flows, and unnecessary triggers." |
| **Security** | "Always follow least privilege, proper ACL patterns, and safe API practices." |
| **Upgradability** | "Stick to OOTB patterns. Customizations break during upgrades." |
| **User Experience** | "Simplicity wins. Reduce clicks, clutter, and cognitive load." |

### 13.2 Decision Framework

1. **Out-of-the-Box First:** Native features solve 80–100% of needs.
2. **Configure Before Code:** UI Policies, ACLs, Dictionary, Forms.
3. **Build vs. Buy:** Certified Store apps over custom integrations.
4. **Decision Trees:** Standardize architecture choices across the team.
5. **Solution Proposals:** Show OOTB alternatives, document risks and dependencies.

### 13.3 Smart Design Philosophy
"Smart design isn't about complexity — it's about sustainability." Architecture is about building sustainable systems, not complex ones.

---

## 14. Reference Liste

### Quellen
1. [ServiceNow: Customization vs Configuration](https://www.servicenow.com/docs/r/servicenow-platform/service-catalog/customization-vs-configuration-concepts.html)
2. [ServiceNow: Configure, Customize, or Build New Apps](https://www.servicenow.com/docs/r/application-development/configure-customize-or-build-new-apps.html)
3. [ServiceNow: Application Development - Best Practice #1 Work in a Scope](https://www.servicenow.com/community/servicenow-ai-platform-blog/application-development-best-practice-1-work-in-a-scope/ba-p/2288784)
4. [ServiceNow: Client Script Best Practices](https://www.servicenow.com/docs/r/washingtondc/api-reference/scripts/client-script-best-practices.html)
5. [ServiceNow: Outbound Integrations — SOAP/REST Performance](https://www.servicenow.com/community/developer-articles/outbound-integrations-using-soap-rest-performance-best-practices/ta-p/2301503)
6. [ServiceNow: UI Actions Best Practices](https://www.servicenow.com/community/in-other-news/servicenow-ui-actions-best-practices/ba-p/2287882)
7. [ServiceNow: Design Smart — The 5 Principles Every Builder Should Know](https://www.servicenow.com/community/itsm-articles/design-smart-the-5-principles-every-servicenow-builder-should/ta-p/3440246)
8. [ServiceNow: What Makes a Customization Upgrade-Safe](https://www.servicenow.com/community/itsm-forum/what-makes-a-servicenow-customization-upgrade-safe-vs-upgrade/td-p/3453622)
9. [ServiceNow: Avoid Customization Pitfalls](https://www.servicenow.com/lpwbr/avoid-customization-pitfalls-innovate-and-meet-demand-at-scale.html)
10. [ServiceNow: Customization — A Thing One Should Not Be Afraid Of](https://www.servicenow.com/community/servicenow-ai-platform-articles/customization-a-thing-one-should-not-be-afraid-of/ta-p/2318933)
11. [ServiceNow: Dictionary Overrides — What They Are and How to Use Them](https://www.servicenow.com/community/itsm-articles/dictionary-overrides-what-they-are-and-how-to-use-them/ta-p/2308028)
12. [ServiceNow: Best Practices to Manage and Maintain Task Table](https://www.servicenow.com/community/servicenow-ai-platform-articles/best-practices-to-manage-and-maintain-task-table/ta-p/2322498)
13. [SN Nerd: Mistakes to Avoid When Customizing OOTB Apps](https://sn-nerd.com/2024/06/25/mistakes-to-avoid-when-customizing-out-of-the-box-apps/)
14. [KeenStack: Keep Your Instance Clean](https://keenstack.com/blogs/servicenow-best-practices-keep-your-instance-clean/)
15. [V-Soft Consulting: Configuration vs Customization](https://blog.vsoftconsulting.com/blog/customization-can-make-or-break-your-servicenow-implementation-configuration-vs-customization)
16. [Kanini: ServiceNow Customization & OOTB Strategy](https://kanini.com/blog/servicenow-customization-out-of-the-box-strategy/)
17. [ServiceNow: GlideRecord Best Practices](https://therockethq.gitbooks.io/servicenow1/content/index/index/scripting/scripting-concepts/gliderecord/best-practices-gliderecord.html)
18. [ServiceNow: UI Policies Best Practices](https://therockethq.gitbooks.io/servicenow1/content/index/index/scripting/scripting-concepts/ui-polices/ui-polices-best-practices.html)
19. [AST Consulting: Scripting Best Practices](https://astconsulting.in/service-now/servicenow-scripting-best-practices)
20. [Jitendra Zaa: Business Rules Complete Guide](https://www.jitendrazaa.com/blog/servicenow/servicenow-business-rules-complete-developer-guide-2025/)
21. [ServiceNow: Scoped Applications — The Complete Developer Guide](https://www.zervion.ai/resources/servicenow-scoped-applications-the-complete-developer-guide)
22. [ServiceNow: Performance Optimization — 12 Techniques](https://www.zervion.ai/resources/servicenow-performance-issues-12-optimization-techniques)
23. [ServiceNow: ATF Best Practices](https://www.servicenow.com/content/dam/servicenow-assets/public/en-us/doc-type/success/quick-answer/automated-test-framework-best-practices.pdf)

---

*Dieses Dokument wird iterativ erweitert. Jede neue erwähnenswerte Quelle wird ergänzt und die Referenzliste aktualisiert.*
*Letzte Änderung: 2026-04-22*
