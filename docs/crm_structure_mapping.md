# CRM / Kundenverwaltung — Strukturvergleich Odoo 11 → Odoo 18

Stand: 28. Juli 2026
Datenbasis: Odoo 11 (DB ITK_V1_a, 6.932 Leads) vs. Odoo 18 (DB odoo18_test, 0 Leads)

## Pipeline-Stages (Mapping per Name)

| O11 Stage | Leads O11 | → O18 Stage | is_won |
|---|---|---|---|
| New (seq=0) | 6.613 | Neu (seq=1) | — |
| Angebotsphase (seq=1) | 9 | Angebotsphase (seq=2) | — |
| On-Hold (seq=2) | 0 | On-Hold (seq=3) | — |
| Positive Rückmeldung (seq=3) | 0 | Positive Rückmeldung (seq=4) | — |
| Won (seq=4) | 7 | Erfolgreich (seq=5) | ✓ |
| Zur Verrechnung bereit (seq=5) | 0 | Zur Verrechnung bereit (seq=6) | — |
| Verloren (seq=6) | 125 | Verloren (seq=7) | — |
| Verrechnet (seq=7) | 178 | Verrechnet (seq=8) | — |

## Vertriebsteams

Alle 8 O11-Teams per Name in O18 angelegt (JSON-RPC):
Interne Weitergabe, Newsletter, Persönlicher Kontakt, Suche / Liste,
Telefon, Vertriebskanäle (Intern), Webinar, Webseite

## Lost Reasons

7 Einträge in O18: Too expensive, We don't have people/skills, Not enough stock,
Im Moment keinen Bedarf, Bedarf zu gering, Später kontaktieren, Mitbewerb

Mapping per Name. 0 O11-Leads mit lost_reason_id.

## crm.lead Feld-Mapping

### Kernfelder (1:1 bzw. per Name/Login/Code)
name, partner_id (per ref/GKZ), user_id (per Login), team_id (per Name),
stage_id (per Name), type, probability, date_deadline, date_closed,
email_from, phone, mobile, contact_name, partner_name,
street/zip/city, state_id (per Code), country_id (per Code),
active, company_id (per Name), tag_ids (per Name), function, title,
color, day_open, day_close, create_date, write_date,
campaign_id (0 Leads), medium_id (25 Leads), source_id (0 Leads),
referred (0 Leads)

### Priority-Mapping (⚠ kritisch)

| O11 Key | O11 Label | Leads | → O18 Key | O18 Label |
|---|---|---|---|---|
| 0 | Normal | 6.861 | 1 | Medium |
| 1 | Low | 12 | 0 | Low |
| 2 | High | 21 | 2 | High |
| 3 | Very High | 38 | 3 | Very High |

### planned_revenue → expected_revenue
Typ float → monetary, Währung EUR, Werte 1:1 (315 Leads)

### description
Typ text → html, Werte 1:1 (472 Leads)

## ITK-Eigenfelder

| Feld | O11 Typ | #gefüllt | O18 Status | Maßnahme |
|---|---|---|---|---|
| x_Lead_Quelle | selection (24 Werte) | 6.468 | char | Als Text importieren oder selection umbauen |
| x_Produktinteresse | selection (10 Werte) | 6.591 | char | Als Text importieren oder selection umbauen |
| x_lead_status | selection (12 Werte) | 6.711 | char | Als Text importieren oder selection umbauen |
| x_Anrede_Lead | selection (3 Werte) | 1.835 | **FEHLT** | In O18 als selection neu anlegen |
| opt_out | boolean | 21 | **FEHLT** | In O18 als boolean ergänzen oder mail.blacklist |

### x_Lead_Quelle — 24 Werte
Excel Leads (230317), Versand Hinweis (230307), Webinar VKÖ/VÖWG (230306),
Webinar OGD (230321), Versand Hinweis Intern (230411/230419/230502/230620),
Versand Intrakommuna (2307), Versand Online Formulare (231206),
IFG Webinare (2025-02-05/02-19/03-12/03-26/04-24/05-27/06-11/07-22/07-31),
Recherchierte Adressen April 2025, Anonym-Portal (2025-04-23/05-15),
ITK & VÖWG Webinar (2025-06-24)

### x_Produktinteresse — 10 Werte
OGD Publikationsservice, Hinweisportal, Acta Nova, Communex,
Online Formulare, Gemeindecloud, Sonstiges, Verwaltungsmanager,
IFG, Anonym-Portal

### x_lead_status — 12 Werte
Lead angelegt, Lead aufbereitet, Lead kontaktiert,
Nicht erreicht / Rückruf, On-Hold, Lead verloren,
VK-Chance vorhanden, Event/Webinar angemeldet, Bereits Kunde,
Termin vereinbart, Event/Webinar teilgenommen,
Webinar teilgenommen bzw. angemeldet

### x_Anrede_Lead — 3 Werte
Sehr geehrte Frau, Sehr geehrter Herr, Sehr geehrte Damen und Herren

## Datenbank-Änderungen (JSON-RPC, reproduzierbar)

- 8 crm.stage: Namen korrigiert, Duplikate gelöscht
- 8 crm.team: Aus O11 per Name übernommen
- 4 crm.lost.reason: Aus O11 per Name übernommen
- ir.module.module crm: shortdesc = "Kundenverwaltung"
- ir.ui.view 575/567/572/568: sample="1" entfernt
- community_magnitude Codes 10-15: Werte auf O11-Stand korrigiert

## Offene Punkte

- Menü-Übersetzungen: PO-Dateien überschreiben DB-Namen (App-Drawer zeigt "CRM")
- x_Anrede_Lead und opt_out in O18 nachrüsten
- ITK-Felder char→selection umstellen (optional)
- Kontaktmigration: Datenprüfung nach Strukturfreigabe
