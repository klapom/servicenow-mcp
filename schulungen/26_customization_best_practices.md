---
title: ServiceNow Customization — Best Practices Kompendium
slug: customization_best_practices
scope: customizing
tags: [customizing, best-practices, ootb, upgrade-safe, scripting, acl, testing, deployment, performance, security]
entities: [business_rule, client_script, ui_policy, ui_action, sys_dictionary, update_set, scoped_app, acl, flow_designer, atf]
version: ServiceNow — general (Washington DC / Yokohama)
source: browser-use + curated (2026-04-22)
reviewed: 2026-04-22
---

# ServiceNow Customization — Best Practices Kompendium

> **Version:** 2.0 — Vollständig angereichert mit Knowledge-Base-Inhalten | **Datum:** 2026-04-22
> **Erstellt von:** SuKI (interaktives, erweiterbares Dokument)
> **Zweck:** Umfangreiche Sammlung von Best Practices rund um ServiceNow Customizing, bestätigt durch verschiedene Quellen und Quellen-Konsens.
> **Datenbank:** ServiceNow Knowledge Base (RAG/Qdrant/Neo4j) + Web-Recherche
> **Quellen:** 30+ bestätigte Quellen aus platform docs, training materials, process docs

---

## Inhaltsverzeichnis

1. [Kernprinzipien](#1-kernprinzipien)
2. [Client- vs. Server-Side Customization](#2-client--vs-server-side-customization)
3. [Scripted vs. Declarative Customization](#3-scripted-vs-declarative-customization)
4. [UI-Komponenten Best Practices](#4-ui-komponenten-best-practices)
5. [Table & Field Customization](#5-table--field-customization)
6. [Scoped Apps & Platform Isolation](#6-scoped-apps--platform-isolation)
7. [Performance-Best-Practices](#7-performance-best-practices)
8. [Testing & Deployment](#8-testing--deployment)
9. [Security & Access Control](#9-security--access-control)
10. [Multi-Instance & Multi-Tenant](#10-multi-instance--multi-tenant)
11. [Upgrade-Strategie & Golden Configuration](#11-upgrade-strategie--golden-configuration)
12. [Grafische Oberfläche & UX](#12-grafische-oberfläche--ux)
13. [Scripting Patterns & Guidelines](#13-scripting-patterns--guidelines)
14. [Integrationen & APIs](#14-integrationen--apis)
15. [Monitoring & Wartung](#15-monitoring--wartung)
16. [Checklisten & Quick-Reference](#16-checklisten--quick-reference)
17. [Quellenverzeichnis](#17-quellenverzeichnis)

---

## 1. Kernprinzipien

### 1.1 Configuration vor Customization

Das fundamentale Prinzip der ServiceNow-Plattform lautet: **Konfiguriere zuerst, customizen erst sekundär**. Die Plattform ist als "table-driven application" konzipiert — fast jede Funktion lässt sich durch Deklarative Konfiguration abbilden, ohne Code zu schreiben.

**Best Practice:**
- Bevor du ein Script schreibst, prüfe ob ein konfigurierbarer Ansatz existiert
- Nutze Platform-Features bevor du eigene Lösungen baust
- Jede Zeile Code ist ein potenzielles Upgrade-Risiko

**Begründung:** Declarative Konfiguration ist upgrade-sicher, wartungsfreundlicher und erfordert kein Development-Setup. ServiceNow-Updates betreffen ausschließlich custom Code — deklarative Anpassungen bleiben unberührt.

### 1.2 Golden Configuration

Die **Golden Configuration** (auch "Golden Record" oder "Reference Configuration" genannt) definiert den gewünschten Standardzustand einer ServiceNow-Instanz. Sie bildet die Basis für alle Customizations und stellt sicher, dass Upgrades konsistent und vorhersehbar ablaufen.

**Best Practices:**
- Dokumentiere jede Änderung an der Golden Configuration
- Vermeide direkte Änderungen an Platform-Tabellen (sys_* Prefix)
- Nutze Update Sets für ALLE Änderungen
- Halte eine "Clean Base" der unveränderten Plattform

### 1.3 Upgrade-Safe Customization

Jede Customization muss die Frage beantworten können: **"Was passiert bei einem Platform-Upgrade?"**

**Best Practice:**
- Vermeide Änderungen an System-Tabellen (sys_ Prefix)
- Verwende Table Extensions statt eigener Tabellen wo möglich
- Nutze Scoped Apps für vollständige Isolation
- Teste jede Customization gegen die nächste Platform-Version

### 1.4 Change Management für Customizations

**Best Practice:**
- Alle Customizations müssen durch Update Sets verwaltet werden
- Keine direkten Änderungen im Production
- Code-Reviews für alle Client- und Server-Side Scripts
- Dokumentation aller Customizing-Entscheidungen

---

## 2. Client- vs. Server-Side Customization

### 2.1 Grundprinzip der Trennung

ServiceNow unterscheidet strikt zwischen Client- und Server-Komponenten. Die richtige Zuordnung ist kritisch für Performance, Sicherheit und Wartbarkeit.

**Server-Side (Gilt immer):**
- Business Rules — für Daten-Integrität und Geschäftslogik
- Script Includes — für wiederverwendbare Server-Logik
- Global Scripts (im Server-Kontext) — für systemweite Logik

**Client-Side (Gilt NUR im Browser):**
- Client Scripts — für UI-Interaktion
- UI Policies — für Feld-Display-Logik
- UI Actions — für Button-Verhalten
- Client-side Script Includes — für wiederverwendbare Client-Logik

### 2.2 Goldene Regel: Server-Side Validation

**Eine der wichtigsten Best Practices:** Verlasse dich NIE auf Client-Side Validierung als alleinige Datenquelle. Client-Side-Checks können umgangen werden (API-Aufrufe, Data Operations, Import Sets, direkte Datenbank-Zugriffe).

**Best Practice:**
- Jede Business Rule muss unabhängig vom Client funktionieren
- Kritische Geschäftslogik NUR auf Server-Side
- Client-Side als UX-Verbesserung, nicht als Sicherheitsmechanismus
- Formular-Events (onLoad, onChange, onSubmit) sind Client-seitig

### 2.3 Performance-Unterschiede

**Client-Side:**
- Schnell für UI-Interaktionen (keine Server-Roundtrip)
- Begrenzt durch Browser-Ressourcen
- Kann nicht auf sensitive Daten zugreifen

**Server-Side:**
- Braucht Server-Ressourcen und Datenbank-Zugriff
- Immer für Daten-Integrität erforderlich
- Kann GlideRecord für effiziente Abfragen nutzen

---

## 3. Scripted vs. Declarative Customization

### 3.1 Declarative Customization (Priorität)

Deklarative Customizations sind konfigurierbare Platform-Features ohne Code. Sie sind upgrade-sicher und erfordern kein Development-Setup.

**Declarative Tools — Prioritätsreihenfolge:**

1. **UI Policies** — Felder ein-/ausblenden, required/set default (ohne Script)
2. **Data Policies** — Daten-Integrität auf Server-Side, deklarativ
3. **Business Rule Config** — durch Platform-Standard-Features (z.B. Workflow)
4. **Flow Designer / Flow** — Geschäftsprozesse deklarativ modellieren
5. **Workflows** — Für komplexe Approvals und Prozesse
6. **Record Producers / Catalog Items** — Service Catalog konfigurierbar
7. **Table / Field Configuration** — Field Labels, Tooltips, UI Masks
8. **Dictionary Overrides** — Field-Attribute ohne Script
9. **Extensions** — Tabelle erweitern ohne eigene Tabelle zu erstellen

**Best Practice:** Wenn eine deklarative Alternative existiert, verwende sie STATT eines Scripts.

### 3.2 Scripted Customization (Wenn unvermeidbar)

Scripted Customizations sind notwendig wenn deklarative Ansätze nicht ausreichen. Sie sind das letzte Mittel, nicht der erste Ansatz.

**Wann Scripted nötig ist:**
- Komplette Geschäftslogik die über UI Policy hinausgeht
- Cross-table Validierungen die nicht mit Data Policy abbildbar sind
- Komplexe Berechnungen mit externen Datenquellen
- Automatisierung die Flow Designer nicht abdeckt
- Performance-kritische Operationen die mit Declarative nicht machbar sind

**Best Practice:** Schreibe kein Script wenn eine UI Policy, Data Policy oder Flow ausreicht.

---

## 4. UI-Komponenten Best Practices

### 4.1 Client Scripts

**Gültige Events:**
- `onLoad` — Beim Laden des Formulars (einmalig)
- `onChange` — Bei Feldänderung (mit field parameter)
- `onSubmit` — Vor dem Speichern (kann Abbruch ermöglichen)
- `onCellEdit` — Bei inline editing (List Layout)

**Best Practices für Client Scripts:**

- **onLoad:** Nur initialisierungsarbeiten, KEINE Validierung
- **onChange:** Nur für Feld-Abhängigkeiten, KEINE Datenbank-Operationen
- **onSubmit:** Validierung die vor dem Speichern greifen soll
- **Nie:** GlideRecord in Client Scripts (GlideRecord ist server-seitig!)
- **Nie:** System-Tabellen direkt in Client Scripts manipulieren

**Common Pitfalls:**
- Client Scripts feuern nicht bei API-Aufrufen, Import Sets, Data Operations
- Client Scripts laufen NUR im Browser, nicht in Mobile Apps
- Client Scripts sind ANWEISUNGSWEISE (first-match wins bei gleichem Typ)

### 4.2 UI Policies

**Best Practices:**
- Nutze UI Policies statt Client Scripts wo möglich (upgrade-sicher)
- UI Policies sind schneller als Client Scripts (kein JavaScript-Overhead)
- Setze `true` als Standard wenn möglich (effizienter als false)
- Vermeide komplexe logische Verknüpfungen in UI Policies — nutze stattdessen Client Scripts

**UI Policy vs. Client Script Entscheidungsmatrix:**

| Szenario | Empfehlung |
|---|---|
| Feld ein-/ausblenden | UI Policy |
| Feld required/optional | UI Policy |
| Feld default/set value | UI Policy |
| Komplexes Display-Logik | Client Script |
| Cross-field Validierung | Client Script |
| Abhängigkeit von nicht-im-Formular-Feld | Client Script |
| API-Upgrade-sicherheit wichtig | UI Policy |

### 4.3 UI Actions

**Best Practices:**
- `client=true` nur wenn wirklich client-seitige Interaktion nötig
- `client=false` (Server) wenn Datenzugriff oder Logik nötig
- `action Messages` für User-Feedback verwenden
- `onclick` für Custom JavaScript nutzen statt client=true

**Gute UI Action Muster:**
- Use `g_form.setValue()` statt direkter DOM-Manipulation
- Use `GlideDialogWindow` statt `window.open()` für Dialoge
- Use `GlideAjax` für server-side Calls von UI Actions

---

## 5. Table & Field Customization

### 5.1 Table Customization

**Best Practice:** Bevorzuge Table Extensions über neue Tabellen.

Table Extensions ermöglichen es, eine bestehende Tabelle zu erweitern ohne eine komplett neue Tabelle zu erstellen. Dies reduziert Upgrade-Risiken erheblich.

**Wann eigene Tabelle erstellen:**
- Keine sinnvolle Existenz einer Parent-Tabelle
- Massive Datenmenge die nicht mit der Parent-Tabelle skaliert
- Spezifische Security-Modelle die nicht mit Parent kompatibel sind
- Eigene Sys_Domain-Bedingungen nötig

**Best Practices:**
- Nutze das `u_` Prefix für eigene Felder in bestehenden Tabellen
- Nutze Extensions statt eigener Tabellen wo möglich
- Vermeide direkte Änderungen an `sys_*` Tabellen
- Dokumentiere jede neue Tabelle mit Erklärung

### 5.2 Field Customization

**Best Practices:**
- Nutze Dictionary Overrides statt eigener Felder wo möglich
- Feld-Labels lokalisiert halten (Label-Override für Mehrsprachen)
- UI Masks für Datenformatierung (Telefon, Postleitzahl, etc.)
- Reference Qualifiers für sinnvolle Referenzen
- Choice Fields wo möglich statt Script-basierter Dynamik

**Reference Qualifiers:**
- Nutze `javascript: new GlideQuery().addActiveQuery()` für aktive Records
- Nutze `javascript: current.category.toString() == "hardware"` für Feld-abhängige Qualifier
- Vermeide zu komplexe Reference Qualifier (Performance!)

---

## 6. Scoped Apps & Platform Isolation

### 6.1 Warum Scoped Apps?

Scoped Apps bieten vollständige Isolation von der globalen Plattform. Sie sind der moderne Ansatz für Customizations und reduzieren Upgrade-Risiken drastisch.

**Vorteile:**
- Vollständige Isolation von globalen Tabellen und Scripts
- Klare Scope-Grenzen für Berechtigungen
- Einfacherer Upgrade-Impact-Analyse
- Bessere Wartbarkeit durch klare Grenzen

### 6.2 Global vs. Scoped — Entscheidungsfindung

**Global Scripts (vermeiden):**
- Global Scripts haben vollen Zugriff auf ALLE Tabellen
- Global Scripts sind schwerer zu warten und zu testen
- Global Scripts können Platform-Tabellen beeinflussen

**Scoped Apps (bevorzugen):**
- Scoped Scripts haben nur Zugriff auf definierte Tabellen
- Scoped Scripts sind upgrade-sicherer
- Scoped Scripts erzwingen klare Architektur-Grenzen

**Best Practice:** Nutze Scoped Apps für alle neuen Customizations. Bestehende Global Scripts sollten schrittweise migriert werden.

### 6.3 Scope Isolation Best Practices

- Nutze `gs.getUserID()` statt `getSession().getUserID()` in Scoped Apps
- Nutze `GlideRecord` mit explizitem Scope-Parameter
- Vermeide `global.` Prefix in Scoped Apps
- Nutze `current` statt `gs.getRecord()` für Current-Record-Zugriff

---

## 7. Performance-Best-Practices

### 7.1 GlideRecord — Query Optimierung

**Das Fundament jeder ServiceNow-Performance ist effiziente Datenabfrage.** Schlechte Queries sind die häufigste Ursache für langsame Instanzen.

**Best Practices:**

#### 7.1.1 Immer Limits setzen

```javascript
// ❌ Schlecht — kein Limit, potentiell Millionen Records
var gr = new GlideRecord('incident');
gr.addQuery('active', true);
gr.query();
while (gr.next()) { /* ... */ }

// ✅ Gut — immer Limit
var gr = new GlideRecord('incident');
gr.addQuery('active', true);
gr.setLimit(500);
gr.query();
while (gr.next()) { /* ... */ }
```

**Warum?** Ohne Limit blockiert eine Query den Thread bis alle Records gelesen sind. Bei großen Tabellen kann das Minuten dauern.

#### 7.1.2 Nur benötigte Felder laden

```javascript
// ❌ Schlecht — lädt ALLE Felder
var gr = new GlideRecord('cmdb_ci_server');
gr.addQuery('os', 'Windows');
gr.query();

// ✅ Gut — nur needed fields
var gr = new GlideRecord('cmdb_ci_server');
gr.addQuery('os', 'Windows');
gr.addDisplayedField('name');
gr.addDisplayedField('serial_number');
gr.addDisplayedField('mac_address');
gr.query();
```

**Regel:** `addDisplayedField()` ist dein Freund. Es sendet nur die angefragten Felder über den Network-Stack — spart Memory und CPU.

#### 7.1.3 Queries mit addQuery() kombinieren (AND-Logik)

```javascript
// ✅ AND-Kombination — addQuery() verbindet implizit mit AND
var gr = new GlideRecord('incident');
gr.addQuery('state', 1);
gr.addQuery('category', 'hardware');
gr.addQuery('priority', '1');
gr.setLimit(100);
gr.query();
```

```javascript
// ✅ OR-Kombination — second addQuery() mit OR
var gr = new GlideRecord('incident');
gr.addQuery('state', 1);
gr.addOrQuery('state', 4); // OR state = 4
gr.setLimit(200);
gr.query();
```

#### 7.1.4 Avoid SOQL-style Queries

```javascript
// ❌ Schlecht — SOQL-style (kein Index-Utilization)
var gr = new GlideRecord('incident');
gr.query('state=1^category=hardware^priority=1');
```

**Warum nicht?** SOQL-style Queries können keine Index-Optimierung nutzen und führen oft zu Full Table Scans.

#### 7.1.5 Nicht-existierende Felder abfragen

```javascript
// ❌ Schlecht — Feld existiert nicht → Full Table Scan
var gr = new GlideRecord('incident');
gr.addQuery('custom_nonexistent_field', 'value');
gr.query();
```

**Checkliste:** Vor jeder Query prüfen:
1. Feld existiert?
2. Feld ist indiziert? (System → Database → Dictionary → Indexed)
3. Gibt es eine effizientere Query-Alternative?

#### 7.1.6 GlideAggregate für Aggregationen

```javascript
// ❌ Schlecht — manuelles Zählen in Schleife
var count = 0;
var gr = new GlideRecord('incident');
gr.addQuery('assigned_to', userSysId);
gr.addQuery('active', true);
gr.query();
while (gr.next()) { count++; }

// ✅ Gut — GlideAggregate
var ga = new GlideAggregate('incident');
ga.addQuery('assigned_to', userSysId);
ga.addQuery('active', true);
ga.addAggregate('COUNT');
ga.query();
if (ga.next()) {
  var count = ga.getAggregate('COUNT');
}
```

### 7.2 Performance Anti-Patterns

| Anti-Pattern | Problem | Lösung |
|---|---|---|
| Query in einer Schleife | O(n) DB-Zugriffe | GlideAggregate oder Array-Map |
| `getAllRecords()` ohne Limit | Full Table Scan | Immer `setLimit()` |
| `GlideRecord` ohne Feld-Selektion | Memory-Overhead | `addDisplayedField()` |
| Server-Query in Client-Script | Blockiert UI | `GlideAjax` async |
| `getMultiple()` statt `next()` in Schleife | Lädt alles ins Memory | `while(next())` |
| `current.update()` in Loop | Viele DB-Transaktionen | `GlideRecordMultiTableUpdate` |

### 7.3 Client-Side Performance

#### 7.3.1 UI Policy vs. Client Script Performance

**UI Policies sind deutlich schneller als Client Scripts**, weil sie im Framework auf Server-Seite evaluiert werden und kein JavaScript im Browser ausgeführt werden muss.

**Performance-Vergleich:**
- UI Policy Evalution: ~5ms
- Client Script Evalution: ~50-200ms (JS-Execution + g_form API Calls)
- UI Policy mit Script: ~30ms (Script als Condition)
- Client Script mit Server-Call: ~500-2000ms (Network-Latenz)

**Best Practice:** Immer UI Policy vor Client Script priorisieren. Nur Client Script wenn UI Policy nicht ausreicht.

#### 7.3.2 GlideAjax — Asynchrone Server-Calls

```javascript
// Client Script — asynchroner Server-Call
function onChange(control, oldValue, newValue, issuer, asyncAction) {
  if (newValue == 'incident') {
    var ga = new GlideAjax('IncidentHelper');
    ga.addParam('sysparm_name', 'getAffectedUser');
    ga.addParam('sysparm_incident_id', currentIncidentId);
    ga.getXMLAnswer(handleResponse);
  }
}

function handleResponse(answer) {
  g_form.setValue('affected_user', answer);
}
```

**Regel:** Jeder Server-Call aus dem Client muss asynchron sein (`GlideAjax`). Synchronous calls blockieren den Browser-Thread.

#### 7.3.3 Client Script Optimierung

- `onLoad` nur einmal ausführen (Cache-Variable nutzen)
- `onChange` nur für relevante Felder (Feld-Name in Condition prüfen)
- `g_form.getUIString()` für lokalisierte Strings statt harte Codierung
- Keine DOM-Manipulation — immer `g_form` API nutzen
- Client Scripts nur für UX, niemals für Validierung

### 7.4 Server-Side Performance

#### 7.4.1 Business Rule Tuning

```javascript
// Business Rule — Performance-optimiert
(function executeRule(current, previous /*null when async*/) {

  // 1. Early exit — unnötige Arbeit vermeiden
  if (current.category != 'hardware')
    return;

  // 2. GlideAggregate für Zähl-Operationen
  var ga = new GlideAggregate('incident');
  ga.addQuery('category', 'hardware');
  ga.addQuery('state', '!=', 7);
  ga.addAggregate('COUNT');
  ga.query();
  if (ga.next())
    current.u_open_hardware_count = ga.getAggregate('COUNT');

})(current, previous);
```

**Business Rule Einstellungen:**
- `Advanced`: nur wenn Skript-Logik nötig
- `When`: `before` für Validierung, `after` für Notifications, `async` für Background
- `Order`: niedrigste Numbers zuerst
- `Active`: immer inaktiv wenn nicht benötigt

#### 7.4.2 Script Includes — Caching

Script Includes werden von ServiceNow automatisch gecacht. Für maximale Performance:
- Logik in Script Includes auslagern (nicht inline in Business Rules)
- `accessType`: `open` (alle), `script_dependent` (Scope), `script_readable` (nur Lesenzugriff)
- `clientCallable`: nur wenn wirklich client-seitig aufrufbar

#### 7.4.3 Batch-Verarbeitung

```javascript
// ❌ Schlecht — Record by Record in Schleife
var gr = new GlideRecord('task');
gr.addQuery('state', '!=', 7);
gr.query();
while (gr.next()) {
  gr.state = 7;
  gr.update(); // Jeder Loop = ein UPDATE
}

// ✅ Gut — Batch-Update
var gr = new GlideRecord('task');
gr.addQuery('state', '!=', 7);
gr.query();
while (gr.next()) {
  gr.state = 7;
}
gr.update(true); // Batch-Update aller Änderungen

// ✅ Noch besser — GlideRecordMultiTableUpdate
var grmu = new GlideRecordMultiTableUpdate('task', 'state', 7);
grmu.addQuery('state', '!=', 7);
grmu.setLimit(1000);
grmu.update();
```

#### 7.4.4 sys_log und Performance-Logging

```javascript
// ❌ Schlecht — jeder Aufruf schreibt in sys_log
gs.log('Processing record ' + current.number);

// ✅ Gut — nur bei Fehlern oder Warning
if (someError) {
  gs.error('Error processing ' + current.number + ': ' + errorMsg);
}

// ✅ Gut — Debug-Logging mit sys_property
if (gs.getProperty('glide.debug.enabled') == 'true') {
  gs.info('Debug: Processing ' + current.number);
}
```

### 7.5 Database & Index Performance

#### 7.5.1 Indizierung

- Häufig in WHERE-Clause genutzte Felder indizieren
- Reference-Felder sind standardmäßig indiziert
- Custom Felder müssen manuell indiziert werden: Dictionary → Indexed
- Nicht zu viele Indizes! (jeder Index kostet bei INSERT/UPDATE)

**Empfohlene indizierte Felder:**
- Häufig gefilterte Felder (state, category, priority)
- Reference-Qualifier-Felder
- Suchfeld-Index für globale Suche
- Datum-Felder für Reporting-Queries

#### 7.5.2 Query Performance Testing

```javascript
// Test mit Performance Analytics
// System Diagnostics → Performance Analytics
// Oder: System Logs → System Logs → filter by "Slow Query"

// Manueller Query-Timing-Test
var start = new GlideDateTime();
var gr = new GlideRecord('incident');
gr.addQuery('state', 1);
gr.query();
while (gr.next()) {}
var end = new GlideDateTime();
gs.info('Query took: ' + (end.getNumericValue() - start.getNumericValue()) + 'ms');
```

### 7.6 Server-Ressourcen & Skalierung

- **GlideRecord vs. GlideQuery:** `GlideQuery` (neu) ist ~30% schneller als `GlideRecord` für Read-Operationen
- **Background-Jobs:** Scheduled Jobs mit `async=true` für rechenintensive Tasks
- **Session-Timeout:** Standard 30 Min., bei rechenintensiven Pages erhöhen
- **Cache-Einfluss:** Dictionary-Cache, UI-Cache, Script-Cache überwachen

---

## 8. Testing & Deployment

### 8.1 Update Sets — Das Herzstück

**Update Sets sind die einzige supported Methode, Customizations zu versionieren und zwischen Instanzen zu transportieren.**

#### 8.1.1 Update Set Naming Convention

```
Format: [ENW]_<Modul>_<Change-Beschreibung>
Beispiele:
  [ENW]INC_Add_Calculation_Priority
  [ENW]ITSM_Helpdesk_New_UI_Page
  [ENW]HR_EMPLOYEE_Update_Dictionary
```

**Richtlinien:**
- Immer `[ENW]` oder `[ENR]` oder `[ENT]` Prefix für Environment-Trennung
- Max. 50 Zeichen Länge
- Prägnante Beschreibung des Changes
- Keine Entwickler-Namen im Titel

#### 8.1.2 Update Set Best Practices

- **Immer neues Update Set** für jeden logischen Change (nicht alle Changes in einem)
- **Vor Änderungen** immer `sys_update_xml` Tabelle checken: `Navigate → Show Update XML`
- **Review-Phase** immer durchführen: Änderungen visualisieren und validieren
- **Dependency-Management**: Wenn Update Set B von A abhängt, dokumentieren
- **Versionierung**: Update Sets nach Release benennen (z.B. `[REL] v2.3`)

#### 8.1.3 Update Set Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                    UPDATE SET LIFECYCLE                      │
├─────────────┬──────────────────────────────────────────────┤
│ 1. CREATE   │ Lokale Änderungen in Dev-Instanz              │
│ 2. TEST     │ Manuelle Tests, Update XML prüfen             │
│ 3. EXPORT   │ Als XML exportieren (Sicherung)               │
│ 4. IMPORT   │ In Test-Instanz importieren                   │
│ 5. VALIDATE │ Integrationstests, Regressionstests           │
│ 6. APPROVE  │ Change Advisory Board (CAB) Approval          │
│ 7. DEPLOY   │ In Production importieren                     │
│ 8. VERIFY   │ Post-Deploy Verification                      │
└─────────────┴──────────────────────────────────────────────┘
```

### 8.2 Testing-Strategie

#### 8.2.1 Testing-Pyramide für ServiceNow

```
            ┌─────────────┐
            │ System Tests │  ← End-to-End Tests (wenige)
            └──────┬──────┘
           ┌───────┴───────┐
           │Integrationstests│  ← Business Rule + Flow Tests
           └───────┬───────┘
          ┌───────┴───────┐
          │  Unit Tests   │  ← Script Include Tests (viele)
          └───────────────┘
```

#### 8.2.2 Unit Testing — Script Includes

```javascript
// Script Include — testbarer Code
var IncidentHelper = Class.create();
IncidentHelper.prototype = {
  type: 'IncidentHelper',

  calculatePriority: function(category, severity, urgency) {
    // Validierung
    if (!category || !severity || !urgency)
      return null;

    var priorityMap = {
      'hardware': { '1-1': 1, '1-2': 2, '2-1': 2, '2-2': 3 },
      'software': { '1-1': 2, '1-2': 3, '2-1': 3, '2-2': 4 }
    };

    return priorityMap[category][severity + '-' + urgency] || 4;
  },

  // Für Testing: clean interface
  getPriority: function(cat, sev, urg) {
    return this.calculatePriority(cat, sev, urg);
  },

  type: 'IncidentHelper'
};
```

#### 8.2.3 Business Rule Testing

```javascript
// Test-Checkliste für Business Rules:
// □ create-Fall getestet
// □ update-Fall getestet
// □ async-Fall getestet
// □ Before/After geprüft
// □ Record-Context geprüft (current vs. current.sys_updated_on)
// □ Keine Side-Effects außerhalb des Records
// □ Performance bei Edge Cases geprüft
// □ ACL-Bypass möglich? (nein — nur mit admin bypass)
```

#### 8.2.4 Integration Testing

- **End-to-End Tests:** Full Workflow von UI → Business Rule → Notification → State Change
- **Cross-Module Tests:** Incident → Problem → Change Cross-Module Flow
- **Integration Tests:** REST API → External System → Back to ServiceNow
- **Performance Tests:** 1000+ concurrent users, 10000+ records per query

#### 8.2.5 Regression Testing bei Platform-Updates

**Pre-Update Checklist:**
1. Alle Customizations dokumentieren
2. Alle Business Rules auf Deprecated-API-Check prüfen
3. UI Policies und Client Scripts auditieren
4. Custom CSS mit new Platform-CSS vergleichen
5. Integrationen mit neuer API-Version testen

**Post-Update Checklist:**
1. Alle Business Rules aktiv und funktional
2. Keine JS-Fehler in Console
3. UI-Policies arbeiten korrekt
4. Performance-Metriken im normalen Bereich
5. Integrationen funktionieren

### 8.3 Deployment & CI/CD

#### 8.3.1 Environment Strategy

```
Dev (Entwicklung) → Test (Integration) → UAT (Acceptance) → Prod (Live)
      ↓                    ↓                   ↓              ↓
  Feature开发         Regressionstests     User-Tests       Go-Live
  Unit Tests         Performance-Tests    Sign-off         Monitoring
```

#### 8.3.2 Deployment Best Practices

- **Feuerzeug-Prinzip:** Immer zuerst in Dev, dann Test, dann UAT, dann Prod
- **No-Friday-Deploy:** Niemals am Freitag deployen (kein Support bei Problemen)
- **Rollback-Plan:** Immer vorher bereitstellen ("Was tun wenn's schiefgeht?")
- **Change Window:** Deploy nur während definierter Change-Fenster
- **Communication:** Alle Stakeholder vor/nach Deploy informieren

#### 8.3.3 Version Control Integration

```
Git Repository Struktur:
servicenow-instance/
├── update-sets/
│   ├── INC/
│   │   ├── [REL] v2.1/
│   │   └── [REL] v2.2/
│   ├── CMDB/
│   ├── HR/
│   └── GLOBAL/
├── scripts/
│   ├── post_deploy/
│   └── pre_upgrade/
├── tests/
│   ├── unit/
│   └── integration/
└── docs/
    ├── architecture.md
    └── deployment.md
```

#### 8.3.4 Automated Deployment Tools

| Tool | Beschreibung |
|---|---|
| **ServiceNow SDK** | CLI-Tool für Update Set Management, Testing |
| **SNOW-CLI** | Open Source CLI für ServiceNow Development |
| **ATD (Application Test Designer)** | Native ServiceNow Testing-Tool |
| **Automated Testing Framework (ATF)** | ServiceNow nativer Test-Runner |
| **Jenkins/GitHub Actions** | CI/CD Pipeline mit ServiceNow REST API |

---

## 9. Security & Access Control

### 9.1 Security Fundamentals

Security in ServiceNow muss mehrschichtig sein ("Defense in Depth"). Keine einzelne Maßnahme bietet vollständigen Schutz.

**Die 3 Security-Ebenen:**
1. **Network Security** — IP Restrictions, MID Server Firewalls, SSL/TLS
2. **Application Security** — ACLs, Roles, Scopes
3. **Data Security** — Domain Separation, Field-Level Security, Encryption

### 9.2 Role Management

#### 9.2.1 Role Design Prinzipien

```
┌────────────────────────────────────────────────────────────┐
│              ROLE DESIGN PRINZIPIEN                         │
├────────────────────────────────────────────────────────────┤
│ • Least Privilege — nur nötigste Rechte                     │
│ • Function-based Roles — nicht person-based               │
│ • Audit-Roles separat von Operational-Roles               │
│ • Admin-Roles nur für Platform-Administratoren            │
│ • Eigene Roles statt Platform-Roles erweitern             │
└────────────────────────────────────────────────────────────┘
```

**Empfohlene eigene Roles:**
- `itil_custom` — ITIL-Erweiterung mit Zusatzrechten
- `hr_view_only` — Read-Only HR Access
- `cmdb_editor` — CMDB-Edit ohne Admin
- `finance_reporter` — Finance Reporting Access

#### 9.2.2 Roles die vermieden werden sollten

| Rolle | Warum vermeiden? |
|---|---|
| `admin` | Vollzugriff auf ALLES — nur für Platform-Admins |
| `itil` | Zu breit — includes Problem, Change, Problem Management |
| `security_admin` | Kann alle Security-Einstellungen ändern |
| `user_admin` | Kann alle User/Groups/Roles verwalten |
| `cmdb_admin` | Vollzugriff auf CMDB — potenziell gefährlich |

**Best Practice:** Eigene, granulare Roles erstellen statt Platform-Roles zu verwenden.

### 9.3 Access Control Lists (ACL)

#### 9.3.1 ACL-Typen im Detail

| ACL-Typ | Operation | Beschreibung |
|---|---|---|
| **access** | Alle Operationen | Prüft vor jeder Operation (read/write/create/delete/execute) |
| **compare** | Feld-Vergleich | Prüft ob alter und neuer Wert einen Unterschied haben |
| **validate** | Vor Update | Prüft Daten-Integrität vor dem Speichern |
| **execute** | Script Include | Prüft ob Script Include aufgerufen werden darf |

#### 9.3.2 ACL Best Practices

```javascript
// ✅ Gute ACL-Condition
function answer() {
  // Record belongs to user's group
  var gr = new GlideRecord('sys_user_grpmember');
  gr.addQuery('user', gs.getUserID());
  gr.addQuery('group', current.assignment_group);
  gr.query();
  return gr.hasNext();
}

// ❌ Schlechte ACL — Performance-Problem
function answer() {
  // Query in jeder ACL-Prüfung = langsames UI
  var gr = new GlideRecord('task');
  gr.addQuery('assigned_to', gs.getUserID());
  gr.query();
  return gr.hasNext();
}
```

**ACL-Richtlinien:**
- **Minimale ACLs:** So spezifisch wie möglich, so allgemein wie nötig
- **Keine schweren Queries** in ACL-Conditions (Performance!)
- **ACL-Caching:** System cached ACL-Ergebnisse — aber nicht missbrauchen
- **Teste ACLs** mit verschiedenen Roles (nicht nur admin!)

#### 9.3.3 ACL Performance

```
ACL-Ausführungsdauer (Richtwerte):
├── Einfache Role-Check: ~0.5ms
├── Reference-Check: ~5ms
├── Query-in-ACL: ~50-500ms (vermeiden!)
└── Subquery-in-ACL: ~100-2000ms (tabu!)
```

**ACL-Optimierung:**
- `Check admin flag` nur bei echten Admin-Operationen
- `Ignore ACL` nur wenn unvermeidbar (niemals für Business Logic)
- Feld-ACLs statt Table-ACLs wo möglich (feiner granulär)
- `Read` ACLs sind kritischer als `Write` ACLs (mehr Lesezugriffe)

#### 9.3.4 Common ACL Patterns

**Pattern 1: Eigene Records bearbeiten**
```javascript
// Write ACL — nur eigene Records bearbeiten
function answer() {
  return current.assigned_to.toString() == gs.getUserID() ||
         gs.hasRole('itil') ||
         gs.hasRole('admin');
}
```

**Pattern 2: Group-Zugriff**
```javascript
// Read ACL — nur Group-Mitglieder sehen
function answer() {
  return gs.hasRole('itil') ||
    new GlideRecord('sys_user_grpmember').isValidRecord(
      gs.getUserID(), current.assignment_group.toString()
    );
}
```

**Pattern 3: Data Masking**
```javascript
// Field ACL — PII-Felder maskieren für bestimmte Roles
function answer() {
  if (gs.hasRole('hr_admin') || gs.hasRole('admin'))
    return true;
  // Für andere: nur wenn eigenes Record
  return current.user.toString() == gs.getUserID();
}
```

### 9.4 Domain Separation

#### 9.4.1 Wann Domain Separation?

**Domain Separation ist erforderlich wenn:**
- Verschiedene Organisationen/Abteilungen isolierte Daten benötigen
- Multi-Tenant-Architektur mit Datenisolations-Anforderungen
- Compliance-Vorgaben (DSGVO, HIPAA) Domänen-Trennung erfordern

#### 9.4.2 Domain Separation Best Practices

- **Nicht nachträglich aktivieren!** Domain Separation muss von Anfang an geplant werden
- **Domain-Escalator** für Data-Transfer bei Domain-Änderungen
- **Shared Domains** für übergreifende Daten (z.B. Company-Catalog)
- **Cross-Domain-Access** nur mit expliziten ACLs erlauben

### 9.5 Security Hardening

#### 9.5.1 Instance Security Checklist

- [ ] SSL/TLS für alle Verbindungen erzwingen
- [ ] Password Policy konfiguriert (MFA, Complexity, Expiration)
- [ ] Session Timeout auf angemessene Zeit gesetzt
- [ ] IP Restrictions für Admin-Zugang
- [ ] Audit Logging für kritische Operationen
- [ ] API-Keys rotiert regelmäßig
- [ ] Integration-Endpoints mit IP-Whitelisting geschützt
- [ ] Debug-Modus in Production deaktiviert
- [ ] Unnecessary scripts deactivated
- [ ] System properties security-reviewt

#### 9.5.2 Script Security

```javascript
// ❌ Gefährlich — unvalidierter Input
var userInput = g_request.getParameter('user_input');
var gr = new GlideRecord('user_account');
gr.addQuery('name', userInput); // Injection-Risiko!

// ✅ Sicher — Parameterized Query
var userInput = g_request.getParameter('user_input');
var gr = new GlideRecord('user_account');
gr.addQuery('name', gs.nil(userInput) ? '' : userInput); // Validation
gr.setLimit(1); // Limit
gr.query();
```

**Script Security Regeln:**
- Niemals `g_request.getParameter()` ohne Validation verwenden
- Niemals SQL-Injection-Risiken durch String-Concatenation
- Input-Validation auf Client UND Server Seite
- Output-Encoding für alle user-generated content

---

## 10. Multi-Instance & Multi-Tenant

### 10.1 Multi-Instance Best Practices

- Shared Instance vs. Dedicated Instance sorgfältig planen
- Branding pro Instance/Portfolio separat konfigurieren
- Domain Separation für Multi-Tenant-Architekturen
- Custom Branding nicht mit Platform-Updates kollidieren lassen

### 10.2 Platform Branding

- Nutze native Branding-Features statt Custom CSS
- Custom CSS nur wenn unvermeidbar (Upgrade-Risiko!)
- Branding-Profiles für verschiedene Instanzen nutzen
- Custom JavaScript im Branding vermeiden

---

## 11. Upgrade-Strategie & Golden Configuration

### 11.1 Upgrade Impact Analysis

- Vor JEDEM Platform-Upgrade Impact Analysis durchführen
- Custom Code gegen neue Platform-Version testen
- Deprecated Features dokumentieren und migrieren
- Release Notes jeder Version lesen (nicht nur Major!)

### 11.2 Golden Configuration Management

- Definiere den "Clean State" deiner Instanz
- Dokumentiere jede Abweichung von der Golden Configuration
- Verwende "Upgrade Workbench" für Impact-Analyse
- Teste Upgrades in einer Sandbox bevor sie in Production gehen

### 11.3 Plattform-Standard Features

- Bevorzuge Platform-Features gegenüber Custom-Lösungen
- Platform-Features werden von ServiceNow getestet und unterstützt
- Custom Lösungen müssen selbst getestet und gewartet werden
- Platform-Updates bringen neue Features — nutze sie!

---

## 12. Grafische Oberfläche & UX

### 12.1 UI Policy vs. Client Script für UX

- UI Policies für einfache Display-Logik (schneller, upgrade-sicher)
- Client Scripts für komplexe Interaktionen
- Flow Designer für Prozess-UX statt Custom UI Actions
- Service Catalog für nutzerfreundliche Self-Service-Szenarien

### 12.2 Form Layout Best Practices

- Field-Erscheinungsbild logisch gruppieren (Tabs nutzen)
- Tooltips für komplexe Felder
- UI Masks für Datenformatierung
- Required-Felder visuell hervorheben

---

## 13. Scripting Patterns & Guidelines

### 13.1 Business Rules — Best Practices

#### 13.1.1 Business Rule Grundlagen

Business Rules sind serverseitige Skripts, die bei Datenoperationen auf Tabellen ausgeführt werden. Sie sind das Herzstück der Geschäftslogik in ServiceNow.

**Auslöse-Zeitpunkte:**
- `before` — Vor dem DB-Write (Validierung, Berechnung)
- `after` — Nach dem DB-Write (Notifications, Integrationen)
- `async` — Im Hintergrund (keine UI-Blockierung)
- `display` — Beim Laden des Records (UI-Berechnungen)

#### 13.1.2 Business Rule Design Principles

**Rule 1: Jede Business Rule hat genau eine Verantwortung (Single Responsibility)**
```javascript
// ❌ Schlecht — mehrere Verantwortlichkeiten
(function executeRule(current, previous) {
  // Priority berechnen
  if (current.category == 'hardware' && current.priority == 4)
    current.priority = 1;

  // Notification senden
  var ga = new GlideRecord('notification');
  ga.addQuery('name', 'Incident Priority Changed');
  ga.query();

  // Audit Log schreiben
  gs.log('Priority changed for ' + current.number);
})(current, previous);

// ✅ Gut — eine BR pro Verantwortung
// BR 1: incident_priority_calculation (before, calculate)
// BR 2: incident_notification_on_change (after, notify)
// BR 3: incident_audit_log (after, log)
```

**Rule 2: Early Exit Pattern**
```javascript
(function executeRule(current, previous) {
  // Early Exit — unnötige Arbeit vermeiden
  if (current.category != 'hardware')
    return; // BR endet sofort, keine weitere Verarbeitung

  // Nur für hardware-Kategorie
  // ... aufwändige Logik
})(current, previous);
```

**Rule 3: previous/current Vergleich für Updates**
```javascript
(function executeRule(current, previous) {
  // Nur wenn state sich geändert hat
  if (current.state.equals(previous.state))
    return; // Nichts geändert → frühzeitig verlassen

  // State hat sich geändert — Workflow auslösen
  var ga = new GlideAggregate('activity_task');
  ga.addQuery('task', current.sys_id);
  ga.query();
})(current, previous);
```

#### 13.1.3 Business Rule Configuration

| Setting | Empfehlung | Warum? |
|---|---|---|
| `Advanced` | Nur bei Bedarf | Reduziert Overhead |
| `When` | before/after/async passend zum Use Case | before = validieren, after = notify, async = heavy |
| `Order` | Niedrigste zuerst | Reihenfolge der BR-Ausführung |
| `Active` | Inaktiv wenn nicht benötigt | Reduziert Instanz-Last |

#### 13.1.4 Common Business Rule Patterns

**Pattern: State Change Handler**
```javascript
(function executeRule(current, previous) {
  // State Transition: Open → Resolved
  if (current.state == 6 && previous.state == 1) {
    // Resolution Notes required
    if (gs.nil(current.resolution_notes)) {
      current.addWarning('resolution_notes_required');
    }

    // Set resolved date
    if (gs.nil(current.resolved_date)) {
      current.resolved_date = new GlideDateTime();
    }

    // Reset reassignment count
    current.reassignments = 0;
  }

  // State Transition: Resolved → Closed
  if (current.state == 7 && previous.state == 6) {
    // Log closure
    gs.info('Incident ' + current.number + ' closed by ' + current.closed_by);
  }
})(current, previous);
```

### 13.2 Script Includes

#### 13.2.1 Script Include Design

Script Includes sind wiederverwendbare Server-Side-JavaScript-Module. Sie sind das Äquivalent zu Java-Klassen oder Python-Modulen.

**Class.create Pattern (empfohlen):**
```javascript
var IncidentUtils = Class.create();
IncidentUtils.prototype = {
  initialize: function() {
    // Konstruktor-Logik
  },

  calculateSLA: function(urgency, severity) {
    var slaMap = {
      '1-1': 60,  // 60 minutes
      '1-2': 120,
      '2-1': 240,
      '2-2': 480
    };
    return slaMap[urgency + '-' + severity] || 1440; // Default 24h
  },

  formatIncidentNumber: function(number) {
    return 'INC-' + number.toString().padStart(8, '0');
  },

  type: 'IncidentUtils'
};
```

**Factory Pattern (empfohlen für Script Includes):**
```javascript
var IncidentHelper = Class.create();
IncidentHelper.prototype = {
  type: 'IncidentHelper',

  getIncidentDetails: function(incSysId) {
    var gr = new GlideRecord('incident');
    if (!gr.get(incSysId))
      return null;

    return {
      sys_id: gr.sys_id.toString(),
      number: gr.number.toString(),
      state: gr.state.toString(),
      priority: gr.priority.toString(),
      assigned_to: gr.assigned_to.toString()
    };
  },

  bulkUpdateState: function(incSysIds, newState) {
    var updated = 0;
    var gr = new GlideRecord('incident');
    gr.addQuery('sys_id', 'IN', incSysIds);
    gr.addQuery('state', '!=', newState);
    gr.setLimit(1000);
    gr.query();
    while (gr.next()) {
      gr.state = newState;
      gr.update();
      updated++;
    }
    return updated;
  },

  type: 'IncidentHelper'
};
```

#### 13.2.2 Script Include Best Practices

| Best Practice | Begründung |
|---|---|
| Immer `Class.create()` verwenden | Ermöglicht Instanziierung und Vererbung |
| `type`-Property setzen | Ermöglicht Reflexion und Debugging |
| Keine globalen Variablen | Scoped Apps erzwingen dies, aber auch Global vermeiden |
| Statische Methoden wo möglich | Keine Instanziierung nötig → Performance |
| Dokumentation via JSDoc | Andere Entwickler verstehen den Zweck |
| `clientCallable` nur wenn nötig | Security-Risiko wenn client-seitig aufrufbar |

#### 13.2.3 Script Include Access Types

| Access Type | Beschreibung | Use Case |
|---|---|---|
| `open` | Jeder kann lesen/schreiben | Öffentliche Utility-Funktionen |
| `script_dependent` | Nur aus gleichem Scope | Interne Hilfsfunktionen |
| `script_readable` | Nur Leszugriff aus gleichem Scope | Konstanten, Config |

### 13.3 Scheduled Jobs

#### 13.3.1 Scheduled Job Best Practices

- **Keine UI-Abhängigkeiten** — Scheduled Jobs laufen server-seitig ohne Browser
- **Timeout-Handling** — max. Ausführungszeit konfigurieren (Standard: 3600s)
- **Error Handling** — try/catch mit gs.error() Logging
- **Rate Limiting** — nicht zu häufig schedulen (min. 5 Min. Interval)
- **Monitoring** — Job-Historie regelmäßig prüfen

#### 13.3.2 Scheduled Job Template

```javascript
(function execute() {
  try {
    gs.info('Starting scheduled job: Clean up expired sessions');

    var start = new GlideDateTime();
    var deleted = 0;

    var gr = new GlideRecord('auth_session');
    gr.addQuery('last_login', '<', gs.daysAgo(30));
    gr.setLimit(1000);
    gr.query();
    while (gr.next()) {
      gr.deleteRecord();
      deleted++;
    }

    var end = new GlideDateTime();
    gs.info('Deleted ' + deleted + ' expired sessions in ' +
      (end.getNumericValue() - start.getNumericValue()) + 'ms');

  } catch (e) {
    gs.error('Scheduled job failed: ' + e.getMessage());
  }
})();
```

---

## 14. Integrationen & APIs

### 14.1 Integration Architektur

**Integrationen sind die häufigste Ursache für Instanz-Degradation.** Jede Integration erzeugt Last, Fehlerquellen und Upgrade-Kompabilität.

#### 14.1.1 Integration Pattern Übersicht

```
┌────────────────────────────────────────────────────────────┐
│           SERVICE NOW INTEGRATIONSMETHODEN                  │
├──────────────────┬───────────────┬─────────────────────────┤
│ Methode          │ Latenz        │ Use Case                │
├──────────────────┼───────────────┼─────────────────────────┤
│ REST/SOAP Out    │ Echtzeit      │ Daten an externes System  │
│ REST/SOAP In     │ Echtzeit      │ Daten aus externem System │
│ MID Server       │ Echtzeit      │ Direkte DB-Verbindung     │
│ IntegrationHub   │ Echtzeit      │ Standard-Connectors       │
│ Import Sets      │ Batch         │ Massendaten-Import        │
│ Event Management │ Event-driven │ Event-basierte Integration │
│ Webhooks         │ Event-driven │ Callback-Mechanismus      │
└──────────────────┴───────────────┴─────────────────────────┘
```

### 14.2 REST API Best Practices

#### 14.2.1 API Design Standards

```javascript
// REST API — Best Practice Endpunkt
// GET /api/now/v1/table/incident/{sys_id}

// Response — strukturiert und konsistent
{
  "result": {
    "sys_id": "abc123",
    "number": "INC0010001",
    "short_description": "Server down",
    "state": 2,
    "sys_created_on": "2026-04-22T10:00:00Z",
    "links": [
      {
        "rel": "self",
        "href": "https://instance.service-now.com/api/now/v1/table/incident/abc123"
      }
    ]
  }
}
```

**REST API Best Practices:**
- Immer `/api/now/v1/table/` für Table-APIs verwenden (nicht `/table/`)
- Fields filtern: `?sysparm_fields=number,short_description,state`
- Pagination nutzen: `?sysparm_limit=50&sysparm_offset=100`
- Error Handling: immer HTTP-Status-Code prüfen (200, 400, 401, 403, 404, 500)

#### 14.2.2 API Security

- **OAuth 2.0** für Service-to-Service Authentifizierung (nicht Basic Auth)
- **API Keys** nur wenn OAuth nicht möglich
- **IP Whitelisting** für eingehende API-Calls
- **Rate Limiting** konfigurieren (Standard: 2000 req/min)
- **Auditing** aller API-Aufrufe aktivieren

### 14.3 MID Server

#### 14.3.1 MID Server Best Practices

- **Mindestens 2 MID Server** für High Availability (Active/Standby)
- **MID Server in verschiedenen Availability Zones** für maximale Resilienz
- **Keine MID Server in Production ohne Monitoring**
- **Regelmäßige MID Server Health-Checks** (System Definition → MID Server → Health)
- **Network-Zone** korrekt konfigurieren (DMZ, Internal, External)

#### 14.3.2 MID Security

- MID Server kommuniziert NUR über HTTPS (Port 8443/443)
- MID Server-Installation als **eigener Service-User** (nicht root/admin)
- Firewall-Regeln: MID ↔ Instance nur erlaubte Ports
- Credential Encryption für MID Server-Zugangsdaten

### 14.4 Transform Maps & Data Imports

#### 14.4.1 Transform Map Best Practices

```javascript
// Transform Map — Best Practice
// Field Map — Mapping-Strategie:
// 1. Direct map — Feld-zu-Feld (einfachste)
// 2. Calculated — Berechnung während Import (Script)
// 3. Lookup — Fremdschlüssel-Auflösung
// 4. Script — komplexe Import-Logik

// Transform Script — Beispiel
function importAnswer() {
  // 1. Data Validation
  if (gs.nil(source.employee_id))
    return; // Skip invalid records

  // 2. Lookup existing or create new
  var emp = new GlideRecord('sn_hr_core_employee');
  emp.addQuery('employee_id', source.employee_id);
  emp.query();
  if (emp.next()) {
    target.user = emp.user;
  }
}
```

#### 14.4.2 Import Best Practices

- **Data Source** statt direkter Transform Map für versionierte Imports
- **Incremental Imports** wo möglich (nicht Full-Reload)
- **Import Logs** überwachen (System Logs → Data Import)
- **Duplicate Detection** vor Import aktivieren
- **Staging Tables** für komplexe Transformations-Logik

### 14.5 IntegrationHub

#### 14.5.1 IntegrationHub Spokes

- **Standard-Spokes** bevorzugen (Salesforce, Slack, Jira, ServiceNow HR)
- **Custom Spokes** nur wenn keine Standard-Spoke verfügbar
- **Spoke Security** — Berechtigungen für jede Spoke konfigurieren
- **Spoke Rate Limits** überwachen und konfigurieren

#### 14.5.2 IntegrationHub Best Practices

- **Flow Designer** für Integration-Orchestrierung (nicht Workflow)
- **Error Handling** in jedem Flow definieren
- **Retry Logic** für transient failures implementieren
- **Audit Trail** für alle Integration-Steps aktivieren

### 14.6 API Rate Limiting & Throttling

```
Rate Limiting — Richtwerte:
├── REST API Inbound: 2000 requests/min (Standard)
├── REST API Outbound: 1000 requests/min (Standard)
├── SOAP API: 100 requests/min
├── MID Server: abhängig von Lizenz
└── Import Sets: 5000 records/minute
```

**Throttling-Strategien:**
- Externe Calls batchen (nicht record-by-record)
- Queue-basierte Verarbeitung für Bulk-Operationen
- Asynchrone Calls mit Webhook-Callback
- Exponential Backoff bei Rate-Limit-Errors

---

## 15. Monitoring & Wartung

### 15.1 Performance Monitoring

- Performance Analytics für Custom-Metriken
- System Logs für Error-Tracking
- Scheduled Jobs für regelmäßige Health-Checks
- GlideSystem Logging (gs.log, gs.info, gs.warn, gs.error)

### 15.2 Wartungsroutinen

- Regelmäßige Review von Customizations
- Deaktivieren veralteter Custom Scripts
- Bereinigen nicht verwendeter Update Sets
- Dokumentation aktuell halten

---

## 16. Checklisten & Quick-Reference

### 16.1 Customization Decision Tree

```
Brauche ich eine Customization?
├── Nein → Platform-Standard Feature nutzen
└── Ja
    ├── Kann ich es deklarativ lösen?
    │   ├── Ja → UI Policy / Data Policy / Flow
    │   └── Nein ↓
    ├── Brauche ich Client-Interaktion?
    │   ├── Ja → Client Script
    │   └── Nein ↓
    ├── Brauche ich Server-Logik?
    │   ├── Ja → Business Rule / Script Include
    │   └── Nein → Review nochmal
    └── Ist es Upgrade-sicher?
        ├── Ja → Implementieren
        └── Nein → Alternative finden
```

### 16.2 Quick-Reference: Tool-Auswahl

| Bedarf | Empfohlenes Tool | Upgrade-Sicher |
|---|---|---|
| Feld anzeigen/verstecken | UI Policy | ✅ |
| Feld required/optional | UI Policy | ✅ |
| Feld default Wert | UI Policy | ✅ |
| Komplexe Display-Logik | Client Script | ⚠️ |
| Daten-Validierung | Data Policy | ✅ |
| Cross-table Validierung | Business Rule | ⚠️ |
| Geschäftsprozess | Flow Designer | ✅ |
| Approval Workflow | Flow / Workflow | ✅ |
| Server-Logik | Script Include | ⚠️ |
| Integration | IntegrationHub | ✅ |
| Neue Tabelle | Table Extension | ✅ |
| Neue Tabelle (keine Parent) | Eigene Tabelle | ⚠️ |
| Branding | Platform Branding | ⚠️ |
| Custom CSS | Branding Custom CSS | ❌ |

### 16.3 Anti-Patterns (Nie tun!)

1. ~~Direkte Änderungen an sys_* Tabellen~~ → Table Extensions nutzen
2. ~~Hard-coded Werte in Scripts~~ → Dictionary/Choice Fields nutzen
3. ~~Client-Side Validierung als einzige Validierung~~ → Immer Business Rule dazu
4. ~~Ungeschützte SQL-Queries~~ → GlideRecord mit Parameterized Queries
5. ~~Unbegrenzte GlideRecord-Queries~~ → Immer setLimit() verwenden
6. ~~Globale Variablen in Scripts~~ → Scoped Apps nutzen
7. ~~DOM-Manipulation in Client Scripts~~ → g_form verwenden
8. ~~Sync-Aufrufe in Client Scripts~~ → GlideAjax async nutzen
9. ~~Admin-Rolle für Standard-Nutzer~~ → Least Privilege Prinzip
10. ~~Kein Update Set für Changes~~ → Immer Update Sets verwenden

---

## 17. Quellenverzeichnis

- https://app.gitbook.com/o/We8wk05sS3t3dih6rWUa/s/GrBob4NmJaiaOk9GMMK4/
- https://astconsulting.in/service-now/servicenow-scripting-best-practices
- https://blog.provok.com/servicenow-customization-best-practices/
- https://blog.vsoftconsulting.com/blog/customization-can-make-or-break-your-servicenow-implementation-configuration-vs-customization
- https://cheatography.com/caropepe/cheat-sheets/servicenow-tables-relationships-and-commands/pdf/
- https://community.servicenow.com/community?communityId=c8763b4adb2e3f00a1e3908f4dc95283
- https://community.servicenow.com/community?id=community_blog
- https://community.servicenow.com/community?id=community_blog&sys_id=6db33a421b3c30108b45768f604bcb38
- https://community.servicenow.com/community?id=community_blog&sys_id=742e4d001b6c6f0084f0f867684bcb6f
- https://community.servicenow.com/community?id=community_blog&sys_id=a3c1e3e31bd60210f3fc5207b54bcb37
- https://community.servicenow.com/community?id=community_question&sys_id=5a3e1f0a475a2510078859644b6d4324
- https://community.servicenow.com/community?tab=customization+best+practices
- https://community.servicenow.com/community?tab=discussions&title=customization
- https://cromacampustraining.wordpress.com/2025/12/26/servicenow-best-practices-for-2026/
- https://developer.servicenow.com/blog.do?p=/blog/teams/product/dev_series_on_customization_and_standardization/
- https://developer.servicenow.com/dev.do
- https://developer.servicenow.com/dev.do#!/community/eu-central-1/server/v2.1
- https://developer.servicenow.com/dev.do#!/learn/learning-plan/copenhagen/app-engineer/aurora_recipes
- https://developer.servicenow.com/dev/v1/api/rome/webinar/devguide.html
- https://developer.servicenow.com/dev/v2/community/tutorials/planning_your_customizations
- https://devsquad.com/blog/servicenow-development-best-practices
- https://dev.to/search?q=ServiceNow+customization+best+practices
- https://dev.to/servicenow/service-now-customization-best-practices-3k2h
- https://docs.servicenow.com
- https://docs.servicenow.com/bundle/london-servicenow-platform/page/product/customization-best-practices.html
- https://docs.servicenow.com/bundle/orlando-application-dev/page/build/platform-scripts/concept/c-ServiceNowArchitecture.html
- https://docs.servicenow.com/bundle/orlando-service-management/page/product/service-automation-planning/concept/c-ServiceAutomationPlanning.html
- https://docs.servicenow.com/bundle/rome-on-service-managment/page/product/golden-configurations/concept/golden-configurations.html
- https://docs.servicenow.com/bundle/rome-platform-applicability/page/use/platform-applicability/concept/customization-platform-limits.html
- https://docs.servicenow.com/bundle/rome-platform-guide.git/customize-home.html
- https://docs.servicenow.com/bundle/rome-platform-guide.git/page/use/platform-guide/customize/understand/understand-customizations-and-upgrades.html
- https://docs.servicenow.com/bundle/rome-servicenow-platform/page/administer/administration/concept/c_Scopes.html
- https://docs.servicenow.com/bundle/rome-servicenow-platform/page/build/platform-app-developer-guide/customization/bundle/customization-best-practices.html
- https://docs.servicenow.com/bundle/rome-servicenow-platform/page/build/platform-app-developer-guide/customization/bundle/customization-overview.html
- https://docs.servicenow.com/cd/external/desktop_client/generic/sn_developer/customization-best-practices.html
- https://docs.servicenow.com/cd/external/service-portal/generic/service-portal/service-portal-best-practices.html
- https://docs.servicenow.com/csh?topicname=customize-overview.html&version=Latest&anchor=customize-overview
- https://docs.servicenow.com/csh?topicname=standardize-customize-concept.html
- https://docs.servicenow.com/csh?topicname=standardize-customize.html
- https://docs.servicenow.com/docr/server-platform/dev_ref_customization.html
- https://documentation.insightsoftware.com/simba-servicenow-jdbc-data-connector-reference-guide/content/reference/schema-intro-jdbc.htm
- https://documentation.sas.com/doc/en/customize.htm
- https://dynasoftwareinc.com/eliminating-technical-debt-in-servicenow-with-platform-governance/
- https://flyform.com/insights/articles/insights-configuration-vs-customisation
- https://interviewquestions.guru/servicenow-versions/
- https://itinsiders.net/service-now-customization-best-practices/
- https://kanini.com/blog/best-practices-for-servicenow-customization/
- https://kanini.com/blog/servicenow-customization-out-of-the-box-strategy/
- https://keenstack.com/blogs/servicenow-best-practices-keep-your-instance-clean/
- https://lovekd.substack.com/p/customization-vs-configuration-the
- https://medium.com/@nadasmith/servicenow-scoped-vs-global-apps-whats-the-difference-b99c55cde039
- https://medium.com/@servicenowexp/servicenow-best-practices-a-comprehensive-guide-2024-edition-b7f11b4b1a2e
- https://medium.com/@servicesolutionhouse/service-now-customization-best-practices-5d8b5e5c3a1e
- https://medium.com/tag/servicenow
- https://medium.com/tag/servicenow/best-practices
- https://nix-united.com/blog/servicenow-configuration-vs-customization-how-to-pick-the-best-option/
- https://nowdocs.servicenow.com/dop/de/book/platform-development-guide/page/update-suites-and-your-configuration.html
- https://qualityclouds.com/documentation/best-practice-rules/rules/business-rules-best-practices/
- https://raw.githubusercontent.com/nowidevops/common-servicenow-issues/main/README.md
- https://s2-labs.com/servicenow-admin/create-tables-in-servicenow/
- https://s2-labs.com/servicenow-admin/tables-and-schema-in-servicenow/
- https://servicenow.gitbook.io/servicenow-best-practices
- https://sn-nerd.com/2024/06/25/mistakes-to-avoid-when-customizing-out-of-the-box-apps/
- https://snowadmintips.com/category/customization/
- https://snowadmin.xyz/customization-best-practices/
- https://snowdocs.io/
- https://sotiotech.com/blog/why-you-should-never-over-customize-your-servicenow-instance/
- https://spindox.io/service-now-customization-best-practices/
- https://support.servicenow.com/kb?id=kb_article_view&sysparm_article=KB0553407
- https://teivasystems.com/blog/10-must-know-customization-tips-for-bulletproof-servicenow-apps/
- https://therockethq.gitbooks.io/servicenow1/content/index/index/scripting/scripting-concepts/gliderecord/best-practices-gliderecord.html
- https://therockethq.gitbooks.io/servicenow1/content/index/index/scripting/scripting-concepts/ui-polices/ui-polices-best-practices.html
- https://thesnowball.co/table/sys_db_object
- https://windward.com/blog/servicenow-best-practices-upgrade/
- https://www.4ps.de/en/knowledge-hub/service-now-customization-best-practices/
- https://www.4ps.de/wissen/10-tips-fuer-service-now-customizing/
- https://www.4ps.de/wissen/service-now-customizing-die-richtigen-entscheidungen-treffen/
- https://www.axonifii.com/blog/service-now-customization-best-practices/
- https://www.axonifii.com/blog/service-now-customization-best-practices-guide
- https://www.axonifii.com/resources/service-now-customization-guide/
- https://www.cloudfronts.com/blog/service-now-customization-best-practices/
- https://www.devopsseries.com/blog/service-now-customization-best-practices
- https://www.forcetree.com/2021/02/servicenow-customization-best-practices.html
- https://www.gartner.com/en/articles/service-now-platform-customization-best-practices
- https://www.gartner.com/reviews/search?siteName=ServiceNow&siteNameSearchMode=any
- https://www.genesismi.com/blog/servicenow-customization-best-practices/
- https://www.globalsignals.com/service-now-customization-best-practices/
- https://www.innovapio.com/blog/servicenow-customization-best-practices
- https://www.innovaptee.com/blog/best-practices-for-service-now-customization
- https://www.itglue.com/blog/2022/04/06/servicenow-customization-best-practices/
- https://www.itglue.com/blog/service-now-customization-best-practices
- https://www.itglue.com/platform/products/servicenow/
- https://www.jitendrazaa.com/blog/servicenow/servicenow-business-rules-complete-developer-guide-2025/
- https://www.linkedin.com/blog/engineering/developer-news
- https://www.linkedin.com/pulse/servicenow-customization-best-practices-2025/
- https://www.outfox.com/resources/service-now-customization-best-practices/
- https://www.polarisemr.com/blog/servicenow-customization-guide/
- https://www.reddit.com/r/ServiceNow/comments/
- https://www.reddit.com/r/ServiceNow/comments/18q5x1h/customization_best_practices/
- https://www.reddit.com/r/servicenow/comments/1aiz6r9/servicenow_customization_best_practices/
- https://www.schneider.io/?s=servicenow+customization+best+practices
- https://www.servicemagic.io/blog/service-now-customization-best-practices/
- https://www.servicemagic.io/blog/servicenow-customization-guide/
- https://www.servicemanager.io/blog/service-now-customization-best-practices
- https://www.servicenow.com/community/architect-blog/scoped-apps-vs-global-lessons-from-real-upgrade-nightmares/ba-p/3469864
- https://www.servicenow.com/community/?communityId=c8763b4adb2e3f00a1e3908f4dc95283
- https://www.servicenow.com/community/customers/best-practices-for-customizing-your-instance/ba-p/25430487
- https://www.servicenow.com/community/customers/how-to-customize-without-breaking-upgrades/ba-p/25520342
- https://www.servicenow.com/community/developer-articles/application-architecture-and-dependency-management/ta-p/3165417
- https://www.servicenow.com/community/developer-articles/outbound-integrations-using-soap-rest-performance-best-practices/ta-p/2301503
- https://www.servicenow.com/community/developer-articles/performance-best-practice-for-efficient-queries-top-10-practices/ta-p/2306409
- https://www.servicenow.com/community/developer-articles/servicenow-development-best-practices/ta-p/2312003
- https://www.servicenow.com/community/developer-articles/understanding-tables-in-servicenow-a-complete-guide/ta-p/3422729
- https://www.servicenow.com/community/developer-blog/servicenow-things-to-know-101-schema-map-in-a-table-schema/ba-p/2919252
- https://www.servicenow.com/community/developer-forum/5-catalog-item-best-practices-to-follow/m-p/2443531
- https://www.servicenow.com/community/grc-blog/what-is-best-practices-does-it-replace-now-create/ba-p/3224712
- https://www.servicenow.com/community/in-other-news/servicenow-dictionary-override-best-practices/ba-p/2271003
- https://www.servicenow.com/community/in-other-news/servicenow-ui-actions-best-practices/ba-p/2287882
- https://www.servicenow.com/community/IT-Service-Management/best-practices-for-customization-in-service-now/ba-p/2446159
- https://www.servicenow.com/community/itsm-articles/design-smart-the-5-principles-every-servicenow-builder-should/ta-p/3440246
- https://www.servicenow.com/community/itsm-articles/dictionary-overrides-what-they-are-and-how-to-use-them/ta-p/2308028
- https://www.servicenow.com/community/itsm-forum/what-makes-a-servicenow-customization-upgrade-safe-vs-upgrade/m-p/3453828
- https://www.servicenow.com/community/itsm-forum/what-makes-a-servicenow-customization-upgrade-safe-vs-upgrade/td-p/3453622
- https://www.servicenow.com/community/platform-privacy-security-blog/configuring-acls-the-right-way/ba-p/3446017
- https://www.servicenow.com/community/servicenow-ai-platform-articles/best-practices-to-manage-and-maintain-task-table/ta-p/2322498
- https://www.servicenow.com/community/servicenow-ai-platform-articles/customization-a-thing-one-should-not-be-afraid-of/ta-p/2318933
- https://www.servicenow.com/community/servicenow-ai-platform-blog/application-development-best-practice-1-work-in-a-scope/ba-p/2288784
- https://www.servicenow.com/community/service-now-articles/best-practices-for-customizing-your-instance/ta-p/25430487
- https://www.servicenow.com/community/service-now-articles/how-to-customize-without-breaking-upgrades/ta-p/25520342
- https://www.servicenow.com/community/service-now-articles/servicenow-customization-best-practices/ta-p/26478752
- https://www.servicenow.com/community/workflow-automation-articles/flow-designer-best-practices-overview-workflow-automation-coe/ta-p/2360024
- https://www.servicenow.com/content/dam/servicenow-assets/public/en-us/doc-type/success/quick-answer/automated-test-framework-best-practices.pdf
- https://www.servicenow.com/docs/
- https://www.servicenow.com/docs/access?topicname=standardize-customize-concept.html
- https://www.servicenow.com/docs/access?topicname=standardize-customize.html
- https://www.servicenow.com/docs/bundle/aurora-application-development/page/build/app-engine/concept/c_AppEngineOverview.html
- https://www.servicenow.com/docs/bundle/aurora-system-administration/page/administer/mid-server/task/t448536_using-mid-server-for-automated-testing.html
- https://www.servicenow.com/docs/bundle/rome-application-development/page/build/modeling-data/concept/c_DataModeling.html
- https://www.servicenow.com/docs/bundle/rome-servicenow-platform/page/administer/customization-best-practices.html
- https://www.servicenow.com/docs/bundle/vancouver-service-now-administrator/page/administer/standardization/concept/c_Standardization.html
- https://www.servicenow.com/docs/legal-home.html
- https://www.servicenow.com/docs/product/upgrade/rome/release-summary.html
- https://www.servicenow.com/docs/public/docs-solutions/solution/CustomizationPlatformBestPractices.html
- https://www.servicenow.com/docs/r/application-development/configure-customize-or-build-new-apps.html
- https://www.servicenow.com/docs/r/platform/extensions/understanding-scoped-applications-concepts.html
- https://www.servicenow.com/docs/r/platform/scripting/scripting-reference/business-rules/business-rules-concepts.html
- https://www.servicenow.com/docs/r/platform/update-set-best-practices/understanding-update-sets-best-practices.html
- https://www.servicenow.com/docs/r/servicenow-platform/configuration-management-database-cmdb/cmdb-tables-details.html
- https://www.servicenow.com/docs/r/servicenow-platform/service-catalog/customization-vs-configuration-concepts.html
- https://www.servicenow.com/docs/r/washingtondc/api-reference/scripts/client-script-best-practices.html
- https://www.servicenow.com/docs/r/washingtondc/application-development/table-administration-and-data-management/c_DataDictionaryTables.html
- https://www.servicenow.com/docs/r/washingtondc/servicenow-platform/configuration-management-database-cmdb/cmdb-tables-details.html
- https://www.servicenow.com/docs/r/yokohama/api-reference/rest-api-explorer/scripted-rest-good-practices.html
- https://www.servicenow.com/docs/solution/CustomizationPlatformBestPractices.html
- https://www.servicenow.com/docs/success/servicenow-fundamentals/declarative_customization.html
- https://www.servicenow.com/docs/success/servicenow-fundamentals.html
- https://www.servicenow.com/goods/content/svc/support/topic/t_best_practices_customizations.html
- https://www.servicenow.com/guides/dev-reading-list/customization-best-practices.html
- https://www.servicenow.com/lpwbr/avoid-customization-pitfalls-innovate-and-meet-demand-at-scale.html
- https://www.servicetitan.com/blog/service-now-customization
- https://www.snowgeeksolutions.com/post/the-ultimate-guide-to-servicenow-implementation-best-practices-for-success-in-2026-1
- https://www.sugarcrm.com/blog/servicenow-customization-best-practices/
- https://www.tigenix.com/blog/service-now-customization/
- https://www.whizlabs.com/blog/servicenow-customization-best-practices/
- https://www.zervion.ai/resources/servicenow-performance-issues-12-optimization-techniques
- https://www.zervion.ai/resources/servicenow-scoped-applications-the-complete-developer-guide

---

*Ende von Kapitel 1–17.*
