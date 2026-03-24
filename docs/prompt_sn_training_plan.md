# Prompt: ServiceNow CMDB Training & Schulungsplan

Kopiere den folgenden Text in Claude Desktop:

---

Du bist ein erfahrener ServiceNow Consultant und Trainer. Erstelle einen detaillierten Trainings- und Schulungsplan für das PHOENIX-Projekt. Der Plan soll Mitarbeiter befähigen, die neu implementierte FNT Command ↔ ServiceNow CMDB-Integration zu verstehen, zu betreiben und weiterzuentwickeln.

## Projektkontext

**Projekt:** PHOENIX — Integration von FNT Command (Kabelmanagement/Infrastruktur) mit ServiceNow CMDB
**Ansatz:** Option C — Pragmatic Interface (bidirektionale REST-API-Integration)
**SN-Version:** Yokohama (Patch 10, Feb 2026)
**Instanzen:** phoenixdev (DEV), phoenixtest (TEST), phoenix (PROD)

### Was wurde implementiert

**Custom Fields auf cmdb_ci (Base Table):**
- u_fnt_elid (String 14) — Primärer Cross-System Key
- u_fnt_arrival_date (Date) — Lieferdatum aus FNT
- u_fnt_campus (String) — Campus-Bezeichnung aus FNT
- u_fnt_gebaeude (String) — Gebäude-Bezeichnung aus FNT
- u_fnt_rack_units (Integer) — Höheneinheiten (ersetzt OOTB rack_units)
- u_fnt_link (URL) — Deep-Link zum FNT-Objekt

**Business Rules auf cmdb_ci:**
- FNT Idempotency Check (before insert, Order 10) — Verhindert doppelte CI-Erstellung
- FNT Timestamp Check (before update, Order 50) — Last-Write-Wins via Timestamp-Vergleich
- FNT Outbound Sync (after update, Order 200) — Pusht Delta-Payload an FNT bei Feldänderung

**Script Includes:**
- FNTCIClassDeriver — Leitet SN CI-Klasse aus FNT-Attributen ab (Chassis→cmdb_ci_chassis_server, Server→cmdb_ci_server, Schaltschrank→cmdb_ci_rack)
- FNTFieldMapper — Feldmapping SN ↔ FNT mit Sync-Richtung (bidirectional, toSN, toFNT)

**REST Message:** FNT Command API mit 4 HTTP Methods (Update CI, Get Products, Get Objects, Get Relations)

**OAuth:** Inbound (FNT→SN) + Outbound (SN→FNT) OAuth2 Konfiguration

**Scheduled Jobs:**
- FNT Product Sync (nightly 02:00) — Produktdaten-Import in cmdb_model
- FNT Daily Reconciliation (daily 03:00) — Drift-Erkennung und -Korrektur

**Update Set:** "CMDB FNT-SN Interface" enthält alle Artefakte

### Bestehendes Umfeld
- 78.775 CIs in der CMDB, davon 8.224 Server, 204 Racks, 83 Chassis
- 30 bestehende Business Rules auf cmdb_ci (OOTB + Custom)
- 50 Custom Fields (u_*) auf cmdb_ci (CIA, Leasing, CrowdStrike, Monitoring etc.)
- Legacy-Migration aus OMNITRACKER über "Green"-Staging-Tabellen (u_cmdb_green_*) abgeschlossen
- Integration-User: "INTERFACE | FNT Command" (Machine Identity Type)
- Bestehende Integrationen: Service Bridge, CrowdStrike, Lansweeper, Azure

### CI-Klassen Phase 1
| FNT Klasse | SN Tabelle | Relation |
|---|---|---|
| Rack (Schaltschrank) | cmdb_ci_rack | Contains → Server/Chassis |
| Chassis | cmdb_ci_chassis_server | Runs on → Blade Server |
| Server (Rack) | cmdb_ci_server | — |
| Server (Blade, IS_CARD=Y) | cmdb_ci_server | — |

### Datenflüsse
1. FNT → SN: Create CI (POST), Update CI (PATCH delta), Retire CI (lifecycle), Create Relation
2. SN → FNT: Update CI (Business Rule → REST Message, delta)
3. Nightly: Product Master Sync (FNT → cmdb_model)
4. Daily: Reconciliation (Drift-Korrektur)
5. Einmalig: Initial Load (ELID Back-Population + CI Import)

### Error Handling (Option C)
- 4xx → Log + Alert, kein Retry
- 5xx → 1x Retry nach 5 Minuten
- Daily Reconciliation als Safety Net

## Anforderungen an den Trainingsplan

Erstelle einen Schulungsplan mit folgender Struktur:

### 1. Zielgruppen definieren
- **SN Administratoren** — Betrieb, Monitoring, Troubleshooting
- **SN Entwickler / Consultants** — Weiterentwicklung, Phase 2/3
- **FNT Administratoren** — Gegenseite der Integration
- **Service Desk / ITSM Agents** — Auswirkung auf tägliche Arbeit
- **Management / Stakeholder** — Überblick, Governance

### 2. Für jede Zielgruppe
- Lernziele (was sollen sie nach der Schulung können?)
- Inhalte (konkrete Themen, Bezug zu den implementierten Artefakten)
- Format (Workshop, Hands-on Lab, Präsentation, Dokumentation)
- Dauer
- Voraussetzungen

### 3. Themenblöcke (mindestens)
- CMDB-Grundlagen und Tabellenvererbung (cmdb_ci → Child Tables)
- FNT Integration Architektur (Datenflüsse, Option C)
- Custom Fields und ihre Bedeutung (u_fnt_* Felder)
- Business Rules Execution Pipeline (Order, Timing, Abhängigkeiten)
- REST Messages und OAuth2 Konfiguration
- Scheduled Jobs (Product Sync, Reconciliation)
- Script Includes (CIClassDeriver, FieldMapper)
- Update Set Management und Promotion (DEV → TEST → PROD)
- Error Handling und Troubleshooting (Logs, Reconciliation-Reports)
- Lifecycle Management (Retire-Flow, Last-Write-Wins)
- Relation Management (Contains, Runs on)
- Monitoring und Alerting
- Phase 2/3 Erweiterbarkeit (neue CI-Klassen, neue Felder)

### 4. Zeitplan
- Vorschlag für Schulungsreihenfolge und -zeitpunkte
- Was muss VOR Go-Live geschult werden, was kann danach kommen?

### 5. Materialien
- Welche Dokumentation wird benötigt?
- Hands-on Labs / Übungsaufgaben mit konkreten Szenarien
- Quick-Reference Cards für den täglichen Betrieb

Bitte erstelle den Plan in Deutsch, strukturiert als Tabellen und Checklisten, mit konkreten Zeitangaben und priorisierten Empfehlungen.
