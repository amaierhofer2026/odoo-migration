# CRM / Kundenverwaltung — Strukturvergleich Odoo 11 → Odoo 18

Stand: 28. Juli 2026. Datenbasis: O11 (6.932 Leads) vs. O18 (0 Leads, vorbereitet)

## Pipeline-Stages (Mapping per Name)

| O11 Stage | Leads | → O18 Stage | is_won |
|---|---|---|---|
| New (seq=0) | 6.613 | Neu (seq=1) | — |
| Angebotsphase (seq=1) | 9 | Angebotsphase (seq=2) | — |
| On-Hold (seq=2) | 0 | On-Hold (seq=3) | — |
| Positive Rückmeldung (seq=3) | 0 | Positive Rückmeldung (seq=4) | — |
| Won (seq=4) | 7 | Erfolgreich (seq=5) | ✓ |
| Zur Verrechnung bereit (seq=5) | 0 | Zur Verrechnung bereit (seq=6) | — |
| Verloren (seq=6) | 125 | Verloren (seq=7) | — |
| Verrechnet (seq=7) | 178 | Verrechnet (seq=8) | — |

## Vertriebsteams (alle in O18 angelegt per Name)

Interne Weitergabe, Newsletter, Persönlicher Kontakt, Suche / Liste,
Telefon, Vertriebskanäle (Intern), Webinar, Webseite

## Lost Reasons (7 in O18, Mapping per Name)

Too expensive, We don't have people/skills, Not enough stock,
Im Moment keinen Bedarf, Bedarf zu gering, Später kontaktieren, Mitbewerb

## crm.lead Kernfelder (1:1 mapping)

name, partner_id (per ref/GKZ), user_id (per Login), team_id (per Name),
stage_id (per Name), type, probability, date_deadline, date_closed,
email_from, phone, mobile, contact_name, partner_name,
street/zip/city, state_id, country_id, active, company_id,
tag_ids (per Name), function, title, color, day_open, day_close,
create_date, write_date, campaign_id (0 leads), medium_id (25 leads),
source_id (0 leads), referred (0 leads)

## Priority-Mapping (⚠ mapping nötig)

| O11 Key | O11 Label | Leads | → O18 Key | O18 Label |
|---|---|---|---|---|
| 0 | Normal | 6.861 | 1 | Medium |
| 1 | Low | 12 | 0 | Low |
| 2 | High | 21 | 2 | High |
| 3 | Very High | 38 | 3 | Very High |

## planned_revenue → expected_revenue
float → monetary, EUR, Werte 1:1

## description
text → html, Werte 1:1

## ITK-Eigenfelder

| Feld | O11 Typ | Gefüllt | O18 | Aktion |
|---|---|---|---|---|
| x_Lead_Quelle | selection (24) | 6.468 | char | Werte als Text importieren |
| x_Produktinteresse | selection (10) | 6.591 | char | Werte als Text importieren |
| x_lead_status | selection (12) | 6.711 | char | Werte als Text importieren |
| x_Anrede_Lead | selection (3) | 1.835 | FEHLT | In O18 als selection nachrüsten |
| opt_out | boolean | 21 | FEHLT | In O18 nachrüsten |

## DB-Änderungen (JSON-RPC)

- 8 crm.stage: Namen korrigiert, Duplikate gelöscht
- 8 crm.team: Aus O11 übernommen
- 4 crm.lost.reason: Aus O11 übernommen
- ir.module.module crm: shortdesc = "Kundenverwaltung"
- ir.ui.view 575/567/572/568: sample="1" entfernt
- community_magnitude Codes 10-15: Werte auf O11 korrigiert
