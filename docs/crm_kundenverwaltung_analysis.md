# CRM / Kundenverwaltung: Odoo 11 → 18 Vollständige Analyse

Erstellt: 30.07.2026
Branch: `crm-kundenverwaltung-migration`
Quelldaten: JSON-RPC-Abfragen Odoo 11 (`ITK_V1_a`) + Odoo 18 (`odoo18_test`)

---

## 1. Menü-Struktur: Odoo 11 → Odoo 18 Mapping

### 1.1 Odoo 11 (technische DB-Namen + DE-Übersetzung)

| DB-Name | DE-Anzeige | ID | Parent |
|---------|-----------|----|--------|
| CRM | Kundenverwaltung | 195 | - |
| Pipeline | Pipeline | 205 | 195 |
| Leads | Interessenten | 207 | 205 |
| Pipeline (2) | Pipeline | 208 | 205 |
| Quotations | Angebote | 351 | 205 |
| Customers | Kunden | 206 | 195 |
| Activities | Aktivitäten | 414 | 195 |
| Reporting | Berichtswesen | 200 | 195 |
| Leads (Report) | Interessenten | 214 | 200 |
| Pipeline (Report) | Pipeline | 213 | 200 |
| Activities (Report) | Aktivitäten | 212 | 200 |
| Sales Channels (Report) | Vertriebskänale | 203 | 200 |
| Configuration | Konfiguration | 196 | 195 |
| Settings | Einstellungen | 199 | 196 |
| Sales Channels | Vertriebskänale | 201 | 196 |
| Activity Types | Aktivitätstypen | 202 | 196 |
| Lead Tags | Lead Tags | 209 | 196 |
| Lost Reasons | Ablehnungsgründe | 210 | 196 |
| Leads & Opportunities | Interessenten und Chancen | 197 | 196 |

### 1.2 Odoo 18 (aktuell)

| Name | ID | Parent | Seq | Action |
|------|----|--------|-----|--------|
| CRM | 143 | - | 25 | - |
| Sales | 144 | 143 | 1 | - |
| My Pipeline | 145 | 144 | 1 | server,196 |
| My Activities | 146 | 144 | 2 | window,211 |
| Teams | 147 | 144 | 4 | window,185 |
| Customers | 148 | 144 | 5 | window,56 |
| My Quotations | 294 | 144 | 2 | window,431 |
| Leads | 149 | 143 | 5 | window,210 |
| Reporting | 150 | 143 | 20 | - |
| Forecast | 151 | 150 | 1 | server,197 |
| Pipeline | 152 | 150 | 2 | window,220 |
| Leads | 153 | 150 | 3 | window,221 |
| Activities | 154 | 150 | 4 | window,218 |
| Configuration | 155 | 143 | 25 | server,196 |
| Settings | 156 | 155 | 0 | window,217 |
| Sales Teams | 158 | 155 | 5 | window,186 |
| Activities (Config) | 160 | 155 | 8 | - |
| Activity Types | 161 | 160 | 10 | window,188 |
| Activity Plans | 162 | 160 | 11 | window,216 |
| Recurring Plans | 163 | 155 | 12 | window,204 |
| Pipeline (Config) | 164 | 155 | 15 | - |
| Tags | 166 | 164 | 1 | window,183 |
| Lost Reasons | 167 | 164 | 6 | window,205 |
| Lead Generation | 169 | 155 | 20 | - |
| Lead Mining Requests | 170 | 169 | 0 | window,232 |

### 1.3 Menü-Anpassungen: Plan

| O11 DE-Anzeige | O18 ID | Aktueller Name | Ziel-Name | Aktion |
|---------------|--------|---------------|-----------|--------|
| Kundenverwaltung | 143 | CRM | Kundenverwaltung | `write({"name":"Kundenverwaltung"})` |
| Pipeline | 144 | Sales | Pipeline | `write({"name":"Pipeline"})` |
| Pipeline | 145 | My Pipeline | Pipeline | `write({"name":"Pipeline"})` |
| Aktivitäten | 146 | My Activities | Aktivitäten | `write({"name":"Aktivitäten"})`, parent_id → 143 |
| Interessenten | 149 | Leads | Interessenten | `write({"name":"Interessenten"})`, parent_id → 144 |
| Angebote | 294 | My Quotations | Angebote | `write({"name":"Angebote"})` |
| Kunden | 148 | Customers | Kunden | `write({"name":"Kunden"})`, parent_id → 143 |
| Berichtswesen | 150 | Reporting | Berichtswesen | `write({"name":"Berichtswesen"})` |
| Konfiguration | 155 | Configuration | Konfiguration | `write({"name":"Konfiguration"})` |
| Vertriebskanäle | 158 | Sales Teams | Vertriebskanäle | `write({"name":"Vertriebskanäle"})` |
| Aktivitätstypen | 161 | Activity Types | Aktivitätstypen | `write({"name":"Aktivitätstypen"})` |
| Interessenten und Chancen | 164 | Pipeline | Interessenten und Chancen | `write({"name":"Interessenten und Chancen"})` |

**NICHT ändern/löschen, da O18-Features:**
- Teams (147) → behalten (O18-Feature: Team-Übersicht)
- Forecast (151) → behalten
- Activity Plans (162) → behalten
- Recurring Plans (163) → behalten
- Lead Generation (169) → behalten
- Lead Mining Requests (170) → behalten
- Tags (166) → behalten (entspricht O11 Lead Tags)

**Menü-Reihenfolge (sequence) anpassen:**
- Aktivitäten (146) → seq=0 unter Kundenverwaltung
- Pipeline (144) → seq=1
- Interessenten (149) → seq=2 unter Pipeline
- Angebote (294) → seq=3 unter Pipeline
- Kunden (148) → seq=5
- Berichtswesen (150) → seq=20
- Konfiguration (155) → seq=25

---

## 2. Pipeline-Stages: Odoo 11 → Odoo 18

### 2.1 Odoo 11 Stages (technisch)

| ID | Name (DB) | DE-Anzeige | Seq | Prob | Fold | Team |
|----|-----------|-----------|-----|------|------|------|
| 1 | New | Neu | 0 | 10 | false | - |
| 10 | Angebotsphase | Angebotsphase | 1 | 10 | false | - |
| 15 | On-Hold | On-Hold | 2 | 10 | false | - |
| 13 | Positive Rückmeldung | Positive Rückmeldung | 3 | 10 | false | - |
| 4 | Won | Erfolgreich | 4 | 100 | false | - |
| 11 | Zur Verrechnung bereit | Zur Verrechnung bereit | 5 | 10 | false | - |
| 5 | Verloren | Verloren | 6 | 0 | false | Team 1 |
| 14 | Verrechnet | Verrechnet | 7 | 10 | false | - |

### 2.2 Odoo 18 Stages (aktuell)

| ID | Name | Seq | Fold | is_won |
|----|------|-----|------|--------|
| 1 | New | 1 | false | false |
| 2 | Qualified | 2 | false | false |
| 3 | Proposition | 3 | false | false |
| 4 | Won | 70 | false | true |

### 2.3 Stage-Mapping: Plan

| Seq | O11 (DE) | O11 DB-Name | O18 Stage-ID | Aktion |
|-----|----------|------------|-------------|--------|
| 1 | Neu | New | 1 (New) | `write({"name":"Neu", "sequence":1})` |
| 2 | Angebotsphase | Angebotsphase | 2 (Qualified) | `write({"name":"Angebotsphase", "sequence":2})` |
| 3 | On-Hold | On-Hold | 3 (Proposition) | `write({"name":"On-Hold", "sequence":3})` |
| 4 | Positive Rückmeldung | Positive Rückmeldung | **NEU** | `create({"name":"Positive Rückmeldung", "sequence":4})` |
| 5 | Erfolgreich | Won | 4 (Won) | `write({"name":"Erfolgreich", "sequence":5, "is_won":true})` |
| 6 | Zur Verrechnung bereit | Zur Verrechnung bereit | **NEU** | `create({"name":"Zur Verrechnung bereit", "sequence":6})` |
| 7 | Verloren | Verloren | **NEU** | `create({"name":"Verloren", "sequence":7, "fold":true})` |
| 8 | Verrechnet | Verrechnet | **NEU** | `create({"name":"Verrechnet", "sequence":8, "fold":true})` |

**PITFALL: `probability` existiert NICHT auf `crm.stage` in Odoo 18!** 
In Odoo 18 wird die Wahrscheinlichkeit über `crm.lead.automated_probability` gesteuert, nicht mehr auf der Stage.
Das alte `crm.stage.probability`-Feld gibt es nicht mehr — nicht versuchen zu schreiben.

**Wichtig für Migration:** 
- O18 `is_won=True` auf Stage "Erfolgreich" (id=4) setzen
- `fold=True` für "Verloren" und "Verrechnet" setzen (ausgeblendete Stages)
- requirements von O11 können übernommen werden (sind reine Textfelder)

---

## 3. crm.lead Feld-Mapping: Odoo 11 → Odoo 18

### 3.1 Direkte Feld-Entsprechungen

| O11 Feld | O11 Typ | O11 Label | O18 Feld | O18 Typ | O18 Label | Migration |
|----------|---------|-----------|----------|---------|-----------|-----------|
| name | char | Opportunity | name | char | Opportunity | 1:1 |
| partner_id | m2o | Customer | partner_id | m2o | Customer | 1:1 |
| partner_name | char | Customer Name | partner_name | char | Company Name | Label-Änderung |
| user_id | m2o | Salesperson | user_id | m2o | Salesperson | 1:1 |
| team_id | m2o | Sales Channel | team_id | m2o | Sales Team | Label-Änderung |
| stage_id | m2o | Stage | stage_id | m2o | Stage | Stage-Mapping nötig |
| planned_revenue | float | Expected Revenue | expected_revenue | monetary | Expected Revenue | **FELDNAME-ÄNDERUNG!** |
| probability | float | Probability | probability | float | Probability | 1:1 (Feld existiert auf lead) |
| date_deadline | date | Expected Closing | date_deadline | date | Expected Closing | 1:1 |
| activity_date_deadline | date | Next Activity Deadline | activity_date_deadline | date | Next Activity Deadline | 1:1 |
| activity_type_id | m2o | Next Activity Type | activity_type_id | m2o | Next Activity Type | 1:1 |
| activity_summary | char | Next Activity Summary | activity_summary | char | Next Activity Summary | 1:1 |
| description | text | Notes | description | html | Notes | Typ-Änderung: text→html |
| priority | selection | Priority | priority | selection | Priority | 1:1 |
| type | selection | Type | type | selection | Type | 1:1 (lead/opportunity) |
| email_from | char | Email | email_from | char | Email | 1:1 |
| phone | char | Phone | phone | char | Phone | 1:1 |
| lost_reason | m2o | Lost Reason | lost_reason_id | m2o | Lost Reason | **FELDNAME-ÄNDERUNG!** |
| date_open | datetime | Assigned | date_open | datetime | Assignment Date | 1:1 |
| date_closed | datetime | Closed Date | date_closed | datetime | Closed Date | 1:1 |
| referred | char | Referred By | referred | char | Referred By | 1:1 |
| active | boolean | Active | active | boolean | Active | 1:1 |
| company_id | m2o | Company | company_id | m2o | Company | 1:1 |
| color | integer | Color Index | color | integer | Color Index | 1:1 |

### 3.2 Neue Felder in Odoo 18 (existierten nicht in O11)

| Feld | Typ | Label | Bemerkung |
|------|-----|-------|-----------|
| automated_probability | float | Automated Probability | Ersetzt Stage-Probability |
| lead_properties | properties | Properties | Neues O18-Feature |
| recurring_revenue | monetary | Recurring Revenues | Neu |
| recurring_plan | m2o | Recurring Plan | Neu |
| campaign_id | m2o | Campaign | UTM-Tracking |
| medium_id | m2o | Medium | UTM-Tracking |
| source_id | m2o | Source | UTM-Tracking |
| order_ids | o2m | Orders | Verknüpfung zu sale.order |
| tag_ids | m2m | Tags | Statt Lead Tags |
| duplicate_lead_ids | m2m | Potential Duplicate Lead | Duplikaterkennung |
| email_state | selection | Email Quality | Neu |
| phone_state | selection | Phone Quality | Neu |
| date_last_stage_update | datetime | Last Stage Update | Tracking |
| date_conversion | datetime | Conversion Date | Neu |
| day_open/day_close | float | Days to Assign/Close | Berechnet |

**Empfehlung:** Diese Felder bleiben erhalten. Sie stören nicht und können nützlich sein. Keine Migration nötig (werden automatisch befüllt oder bleiben leer).

---

## 4. Custom-Felder: Odoo 11 → Odoo 18

### 4.1 Status in Odoo 18

| O11 Feld | O11 Typ | O11 Label | O18 Feld | O18 Typ | Problem |
|----------|---------|-----------|----------|---------|---------|
| x_Lead_Quelle | **selection** (24 Optionen) | Lead Quelle | x_Lead_Quelle | **char** | **Typ-Änderung!** Selection-Keys→Text |
| x_Produktinteresse | **selection** (10 Optionen) | Produktinteresse | x_Produktinteresse | **char** | **Typ-Änderung!** Selection-Keys→Text |
| x_lead_status | **selection** (12 Optionen) | Lead Status | x_lead_status | **char** | **Typ-Änderung!** Selection-Keys→Text |
| x_Anrede_Lead | selection (3 Optionen) | Anrede Lead | **FEHLT!** | - | **Muss neu angelegt werden!** |

### 4.2 Empfehlung Custom-Felder

1. **x_Lead_Quelle, x_Produktinteresse, x_lead_status**: Typ von `char` auf `selection` ändern und Selection-Optionen aus O11 wiederherstellen. Das ist essenziell für die Migration, da die Selection-Keys aus O11 kommen und in O18 wieder als Selection erkannt werden müssen.

2. **x_Anrede_Lead**: Als Selection-Feld neu anlegen mit denselben Optionen wie in O11:
   - `sg_Frau`: Sehr geehrte Frau
   - `sg_Herr`: Sehr geehrter Herr  
   - `sg_Damen_Herren`: Sehr geehrte Damen und Herren

---

## 5. itk_crm Modul: Odoo 11 → Odoo 18

### 5.1 Status

`itk_crm` ist in **beiden** Systemen installiert.

O18 hat bereits folgende Modelle von itk_crm:
- `itk_crm.communitycode` (Community Code)
- `itk_crm.communitymagnitude` (Community Magnitude)
- `itk_crm.statusofcommunity` (Status of Community)
- `itk_crm.statusofpartner` (Status of Partner)
- `itk_crm.titleputinback` (Title put in Back)
- `itk_crm.titleputinfront` (Title put in Front)

### 5.2 O11 Automated Action

In Odoo 11 existiert eine Automated Action:
- Name: "Interessent 'zur Verrechnung bereit'"
- Modell: crm.lead
- Trigger: on_write
- Aktion: email

**Diese muss in Odoo 18 nachgebaut werden**, da die Funktionalität (Benachrichtigung bei Stage-Wechsel zu "Zur Verrechnung bereit") geschäftskritisch ist.

---

## 6. Datenmigration: Mapping-Tabelle

### 6.1 Lead/Interessent-Daten (6.932 Leads, davon 320 Opportunities, 6.612 Leads)

| O11 Quelldaten | O11 Feld | O18 Zielfeld | Migrationslogik |
|---------------|----------|-------------|-----------------|
| Interessenten (type=lead) | crm.lead | crm.lead | 1:1 mit type='lead' |
| Chancen (type=opportunity) | crm.lead | crm.lead | 1:1 mit type='opportunity' |
| Pipeline-Phase (Stage) | stage_id | stage_id | Mapping über Stage-Namen (s. 2.3) |
| Verantwortlicher Verkäufer | user_id | user_id | User-Mapping nötig |
| Kunde | partner_id | partner_id | Partner-Mapping (bereits migriert?) |
| Angebot | via sale.order | order_ids | Verknüpfung über order.opportunity_id |
| Erwarteter Umsatz | planned_revenue | expected_revenue | Feldname-Änderung! |
| Wahrscheinlichkeit | probability | probability | 1:1 |
| Nächste Aktivität | activity_summary | activity_summary | 1:1 |
| Aktivitätstyp | activity_type_id | activity_type_id | Typ-Mapping |
| Geplantes Datum | date_deadline | date_deadline | 1:1 |
| Vertriebskanal (Team) | team_id | team_id | Team-Mapping nötig |
| Status Gewonnen | stage_id=4 (Won) | stage_id=4 (mit is_won=True) | Stage-ID-Mapping |
| Status Verloren | stage_id=5 | NEUE Stage (Verloren) | Stage-Mapping |
| Status Verrechnet | stage_id=14 | NEUE Stage (Verrechnet) | Stage-Mapping |
| Lead-Quelle | x_Lead_Quelle (selection) | x_Lead_Quelle (muss selection werden) | Selection-Key→Text→Selection-Key |
| Produktinteresse | x_Produktinteresse (selection) | x_Produktinteresse (muss selection werden) | Selection-Key→Text→Selection-Key |
| Lead Status | x_lead_status (selection) | x_lead_status (muss selection werden) | Selection-Key→Text→Selection-Key |
| Anrede | x_Anrede_Lead (selection) | x_Anrede_Lead (neu anlegen) | 1:1 |
| Ablehnungsgrund | lost_reason | lost_reason_id | Feldname-Änderung! |

### 6.2 Lost Reasons Mapping

| O11 ID | O11 Name | O18 ID | O18 Name | Aktion |
|--------|----------|--------|----------|--------|
| 1 | Too expensive | 1 | Too expensive | Behalten |
| 2 | Im Moment keinen Bedarf | 2 | We don't have people/skills | Umbenennen oder neu |
| 4 | Bedarf zu gering | NEU | Bedarf zu gering | Neu anlegen |
| 5 | Später kontaktieren | NEU | Später kontaktieren | Neu anlegen |
| 6 | Mitbewerb | NEU | Mitbewerb | Neu anlegen |

### 6.3 Teams (Vertriebskanäle) Mapping

| O11 ID | O11 Name | Bemerkung |
|--------|----------|-----------|
| 1 | Vertriebskanäle (Intern) | Hauptteam, 35 Mitglieder |
| 2 | Webseite | |
| 3 | Webinar | Leader: Breit Christiane |
| 4 | Newsletter | Leader: Breit Christiane |
| 5 | Telefon | Leader: Breit Christiane |
| 6 | Persönlicher Kontakt | Leader: Breit Christiane |
| 7 | Suche / Liste | |
| 8 | Interne Weitergabe | |

O18 hat nur 1 Team: "Sales". Die O11-Teams müssen migriert werden (crm.team).

---

## 7. Risiken bei der Datenmigration

### 7.1 Kritisch (Blockierend)

1. **`planned_revenue` → `expected_revenue`**: Feldname-Änderung. Bei direktem SQL-Import muss Spaltenname gemappt werden.
2. **`lost_reason` → `lost_reason_id`**: Feldname-Änderung.
3. **Custom-Felder Typ-Änderung (selection→char)**: Selection-Keys aus O11 müssen korrekt in Selection-Keys in O18 konvertiert werden — nicht als reiner Text.
4. **`probability` auf `crm.stage` nicht mehr vorhanden**: Die alten Stage-Wahrscheinlichkeiten gehen verloren. Die `automated_probability` in O18 wird anders berechnet.

### 7.2 Mittel (Workaround nötig)

5. **Stage-IDs ändern sich**: O11 Stage-IDs (1,10,15,13,4,11,5,14) weichen von O18 ab (1,2,3,4 + neue). Mapping nötig.
6. **User-IDs**: O11 User-IDs (z.B. 46=Breit Christiane) müssen auf O18 User-IDs gemappt werden.
7. **Team-IDs**: O11 Teams müssen erst in O18 angelegt werden.

### 7.3 Gering (Optional)

8. **description text→html**: O11 plain text wird in O18 HTML — Migration unkritisch, könnte Formatierung verlieren.
9. **Automated Action "Zur Verrechnung bereit"**: Muss manuell nachgebaut werden.

---

## 8. Empfehlung: Was Standard bleiben soll

| Element | Empfehlung |
|---------|-----------|
| O18 Teams-Menü (147) | Behalten — O18-Feature |
| Forecast (151) | Behalten — neues O18-Feature |
| Activity Plans (162) | Behalten |
| Recurring Plans (163) | Behalten |
| Lead Generation + Mining (169,170) | Behalten |
| Tags (166) statt Lead Tags | Behalten — O18-Standard |
| lead_properties | Behalten — O18-Feature |
| UTM-Felder (campaign, medium, source) | Behalten — O18-Standard |
| duplicate_lead_ids | Behalten — O18-Feature |
| recurring_revenue | Behalten — kann ignoriert werden |
| automated_probability | Behalten — O18-Mechanismus |

---

## 9. Umsetzungsplan (Reihenfolge)

1. **Menüs umbenennen** (JSON-RPC write auf ir.ui.menu)
2. **Stages anpassen** (umbenennen + neue anlegen, `is_won`/`fold` setzen)
3. **Lost Reasons anpassen**
4. **Custom-Felder korrigieren** (x_Lead_Quelle etc. von char→selection)
5. **x_Anrede_Lead neu anlegen**
6. **Automated Action "Zur Verrechnung bereit" nachbauen**
7. **Browser-Verifikation** (Pflicht nach jeder DB-Änderung!)
8. **Teams migrieren** (erst nach Freigabe der Kontaktmigration)

---

## 10. Nächste Schritte

Nach Freigabe dieser Analyse:
1. Umsetzung der Menü-Umbenennungen
2. Umsetzung der Stage-Anpassungen  
3. Korrektur der Custom-Felder
4. Browser-Verifikation nach jedem Schritt
5. Dokumentation in PROJECT_KNOWLEDGE.md
