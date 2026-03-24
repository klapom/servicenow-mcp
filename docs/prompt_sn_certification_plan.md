# Prompt: Persönlicher ServiceNow Zertifizierungs- und Schulungsplan

Kopiere den folgenden Text in Claude Desktop:

---

Du bist ein erfahrener ServiceNow Karriereberater und Zertifizierungsexperte. Erstelle einen persönlichen Trainings- und Zertifizierungsplan für mich.

## Mein Profil

**Rolle:** IT-Consultant (Pommer IT-Consulting GmbH), Projektleitung und technische Umsetzung im PHOENIX-Projekt
**Schwerpunkt:** ServiceNow CMDB, Integrationen, ITSM
**Erfahrungsstand:** Ich arbeite aktiv in ServiceNow (Yokohama Release) und habe folgende Themen praktisch umgesetzt — aber noch keine formalen SN-Zertifizierungen:

### Was ich praktisch beherrsche (belegt durch aktuelle Projektarbeit)

**CMDB & Configuration Management:**
- Tabellenvererbung (cmdb_ci Base Table → Child Tables wie cmdb_ci_server, cmdb_ci_rack, cmdb_ci_chassis_server)
- Custom Fields via sys_dictionary anlegen (verschiedene Typen: String, Integer, Date, URL, Reference)
- CI-Relationen (cmdb_rel_ci, Relation Types: Contains, Runs on)
- CI Lifecycle Management (life_cycle_stage, life_cycle_stage_status, Retire-Flows)
- CMDB Health, Duplikat-Management (duplicate_of Logik)
- Model Management (cmdb_model, Hardware Models, Model Categories)

**Scripting & Entwicklung:**
- Business Rules (before/after/async, Order-Logik, Execution Pipeline, filter_condition, setAbortAction)
- Script Includes (Server-side JavaScript, Class.create Pattern, API-Name, Client callable)
- GlideRecord API (Queries, Inserts, Updates, Dot-walking, setWorkflow)
- REST Messages (sys_rest_message, HTTP Methods, Variable Substitution, OAuth2 Integration)
- Scheduled Jobs (sysauto_script, run_type, Cron-Scheduling)
- REST/Table API (GET, POST, PATCH, DELETE, sysparm_query, sysparm_fields, sysparm_display_value)

**Integration:**
- Bidirektionale REST-API-Integration (ServiceNow ↔ externes System)
- OAuth2 Konfiguration (oauth_entity, Application Registry, client_credentials Grant, Inbound + Outbound)
- Idempotency-Pattern (Duplikat-Schutz bei API-Calls)
- Last-Write-Wins Conflict Resolution via Timestamps
- Error Handling Pattern (4xx/5xx Unterscheidung, Retry-Logik, Reconciliation als Safety Net)
- Import Sets, Transform Maps, Field Mappings, Data Sources

**Administration:**
- Update Set Management (Erstellen, Scoping, Promotion DEV→TEST→PROD)
- System Properties (sys_properties)
- Connection & Credential Aliases (sys_alias, sys_connection)
- User Management (sys_user, Rollen, Identity Types: Human/Machine/AI Agent)
- System Dictionary (sys_dictionary, Feldtypen, Vererbung, read_only)

**ITSM-Kontext:**
- Incident Management (107k+ Incidents im System)
- Change Management (Change Requests, Approval Flows)
- Knowledge Management
- Service Catalog

## Ziel

Ich möchte meine praktische Erfahrung durch offizielle **ServiceNow-Zertifizierungen** untermauern. Erstelle einen Plan der:

1. **Die passenden Zertifizierungen identifiziert** — welche ServiceNow Zertifizierungen passen zu meinem Profil? Berücksichtige:
   - Certified System Administrator (CSA)
   - Certified Implementation Specialist (CIS) — ITSM, ITOM, HR, etc.
   - Certified Application Developer (CAD)
   - Certified Technical Architect (CTA)
   - Micro-Certifications (CMDB Health, Flow Designer, etc.)
   - Welche davon sind Voraussetzung für andere?

2. **Die optimale Reihenfolge vorschlägt** — basierend auf meinem Wissensstand, was kann ich schnell absolvieren vs. wo muss ich noch lernen?

3. **Lücken identifiziert** — welche SN-Themen deckt mein Profil noch NICHT ab, die für Zertifizierungen relevant sind? Z.B.:
   - Flow Designer / IntegrationHub
   - Service Portal / UI Builder
   - ITOM Discovery / Service Mapping
   - HRSD, CSM, oder andere Module
   - Performance Analytics
   - Domain Separation
   - ATF (Automated Test Framework)

4. **Konkrete Lernressourcen empfiehlt** — für jede Zertifizierung:
   - ServiceNow Now Learning Kurse (mit konkreten Kursnamen)
   - Prüfungsformat (Fragen, Dauer, Passing Score)
   - Geschätzter Vorbereitungsaufwand für mich (mit meiner Vorerfahrung)
   - Kosten
   - Gültigkeitsdauer und Renewal

5. **Einen Zeitplan vorschlägt** — realistisch, neben laufender Projektarbeit:
   - Welche Zertifizierung zuerst (Quick Wins)?
   - Welche haben den höchsten Marktwert?
   - Zeitachse über 12 Monate

6. **Den Business Value bewertet** — welche Zertifizierungen sind für einen IT-Consultant mit CMDB/Integrations-Fokus am wertvollsten am Markt?

Bitte erstelle den Plan in Deutsch, als strukturierte Tabellen mit Priorisierung, Zeitaufwand und Abhängigkeiten. Markiere Quick Wins (basierend auf meinem bestehenden Wissen) explizit.
