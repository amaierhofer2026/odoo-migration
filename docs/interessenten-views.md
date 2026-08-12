# Interessenten-Ansichten (Lead Views) — Odoo 18

Stand: 2026-08-07 | Session: Interessenten List + Form

> **Stand 12.08.2026:** Die Views/Action sind seit itk_crm 18.0.1.3.0 als Modulcode persistiert:
> `addons/itk_crm/data/interessenten_views.xml` (Basis-Views 567 Liste / 566 Formular, Action 1459,
> `_validate_module_views` gruen). Dieses Dokument bleibt die Spezifikation.

## Übersicht

Die Interessenten-Ansicht zeigt ausschließlich `crm.lead`-Datensätze mit `type = 'lead'`.
Pipeline/Opportunities (`type = 'opportunity'`) sind getrennt und unverändert.

## Menü-Struktur

```
Kundenverwaltung (143)
├── Aktivitäten (894)
├── Pipeline (892)
│   ├── Pipeline (897) → ir.actions.server,196  (My Pipeline Kanban)
│   ├── Interessenten (895) → ir.actions.act_window,1469
│   ├── Angebote (898)
│   └── Teams (147)
├── Kunden (148)
├── Berichtswesen (150)
└── Konfiguration (155)
```

## Action 1469 — "Interessenten"

| Feld | Wert |
|------|------|
| name | Interessenten |
| res_model | crm.lead |
| domain | `[('type', '=', 'lead')]` |
| view_mode | list,kanban,calendar,pivot,graph,form |
| view_id | 567 (crm.lead.list.lead) |
| view_ids | 474 |

## Listenansicht — O11-Spaltenreihenfolge

**Base View 567** (crm.lead.list.lead):
- `sample="1"` entfernt
- `string="Interessenten"`

**ITK Inherited View 4005** (crm.lead.list.lead.inherit.itk, priority=99):

| # | Spalte | Technisches Feld | Aktion |
|---|--------|-----------------|--------|
| 1 | Erstellt am | create_date | optional="show" |
| 2 | Zuletzt aktualisiert am | write_date | after create_date |
| 3 | Interessent | name | (Base View) |
| 4 | Anrede Lead | x_Anrede_Lead | after name |
| 5 | Ansprechpartner | contact_name | optional="show", string="Ansprechpartner" |
| 6 | Stadt | city | vor email_from verschoben (original column_invisible) |
| 7 | E-Mail | email_from | (Base View) |
| 8 | Telefon | phone | optional="show" |
| 9 | Lead Quelle | x_Lead_Quelle | after phone |
| 10 | Produktinteresse | x_Produktinteresse | after x_Lead_Quelle |
| 11 | Verkäufer | user_id | string="Verkäufer" |
| 12 | Vertriebskanal | team_id | string="Vertriebskanal" |
| 13 | Lead Status | x_lead_status | after team_id |

Ausgeblendet: partner_name, company_id, state_id, country_id, campaign_id, medium_id,
source_id, probability, tag_ids, priority

## Formularansicht

**ITK Inherited View 4007** (crm.lead.form.inherit.itk, priority=99):

| Bereich | Aktion |
|---------|--------|
| lead_info group | x_Anrede_Lead vor function eingefügt |
| Nach lead_priority | Neue Gruppe "Lead Classification" (x_lead_status, x_Produktinteresse, x_Lead_Quelle) |
| Labels | user_id → "Verkäufer", team_id → "Vertriebskanal" |

Automatisch nur für Leads sichtbar (Gruppen erben `invisible="type == 'opportunity'"`).

## Custom-Felder (alle selection, bereits vorhanden)

| Technisch | Label | Optionen |
|-----------|-------|----------|
| x_Anrede_Lead | Anrede Lead | sg_Frau, sg_Herr, sg_Damen_Herren |
| x_Lead_Quelle | Lead Quelle | 24 Optionen |
| x_Produktinteresse | Produktinteresse | 10 Optionen |
| x_lead_status | Lead Status | 12 Optionen |

## Testdaten

| ID | Name | Typ | Anmerkung |
|----|------|-----|-----------|
| 5 | Test Interessent GmbH | lead | Alle Felder befüllt |
| 6 | Musterstadt IT | lead | Alle Felder befüllt |
| 7 | Gemeinde Testdorf | lead | Alle Felder befüllt, neu angelegt |

## Pipeline (unverändert)

- Kanban-Ansicht mit 8 Stages (Neu, Angebotsphase, On-Hold, Positive Rückmeldung, Erfolgreich, Zur Verrechnung bereit, Verloren, Verrechnet)
- Zeigt nur `type = 'opportunity'`
- Action 196 (ir.actions.server): Crm: My Pipeline
