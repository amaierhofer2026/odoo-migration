# Strukturvergleich Odoo 11 Prod ↔ Odoo 18: Kontakte → Kontaktformular → Support Ticket

Stand: 15.09.2026 (Session 112)
Quellen: Odoo 11 Prod `portal.it-kommunal.at` (DB `ITK_V1_a`, nur gelesen) und Odoo 18 (lokal + VM `k001959vsx.ipax.at`, DB `odoo18_test`)

Auftrag von Anna: Felder, Labels, Typen, Relationen, Ansichten, Buttons und Funktionen prüfen; klären, ob alle
Odoo-11-Informationen in Odoo 18 eindeutig abbildbar sind; eindeutige strukturelle Unterschiede migrationsgerecht
beheben; moderne Odoo-18-Funktionen beibehalten.

## 1. Ergebnis vorab

Odoo 11 und Odoo 18 nutzen **verschiedene Helpdesk-Systeme**:

| | Odoo 11 Prod | Odoo 18 |
|---|---|---|
| Modul | `website_support` (Website Help Desk / Support Ticket) + `website_support_billing`, `website_support_analytic_timesheets` | **OCA `helpdesk_mgmt`** (Helpdesk Management) + `helpdesk_mgmt_sla`, `helpdesk_mgmt_project`, `helpdesk_mgmt_timesheet`, ITK `itk_helpdesk_compat`, `itk_helpdesk_category_user` |
| Ticket-Modell | `website.support.ticket` (65 Felder, **1.210 Datensätze**) | `helpdesk.ticket` (87 Felder, 1 Testdatensatz) |
| Reiter am Kontakt | 2 Felder: `sla_id` (SLA) und `stp_ids` ("Support Ticket Zugriffskonto") | keine eigenen Felder – Reiter war **leer** (nur Platzhaltertext) |
| Ticket-Zugang | Smart-Button "Support Tickets" (`support_ticket_string`) | Smart-Button `action_view_helpdesk_tickets` mit `helpdesk_ticket_count` |

**Der Reiter ist damit vollständig abbildbar:** Die beiden Odoo-11-Felder haben in Odoo 18 kein Gegenstück, aber auch
**keinen einzigen Datenbestand** (0 von 5.842 Kontakten). Die fachliche Funktion des Reiters – die Support-Situation
eines Kontakts sehen – wird in Odoo 18 durch die Ticketliste des Kontakts erfüllt. Der Reiter zeigte bisher nur einen
Platzhaltertext und ist jetzt mit der Odoo-18-Ticketliste gefüllt (Abschnitt 5).

## 2. Feld-Mapping

| Odoo-11-Feld | Bedeutung | Odoo-18-Ziel | Feldtyp | Zuordnung |
|---|---|---|---|---|
| `sla_id` (Modul `website_support`) | SLA je Kontakt → `website.support.sla` | kein Feld am Kontakt; SLAs liegen in Odoo 18 im Ticket/Team (`helpdesk_mgmt_sla`) | many2one | **entfällt** (0 Kontakte mit Wert) |
| `stp_ids` (Modul `website_support`) | "Support Ticket Zugriffskonto" → `res.partner` | kein Gegenstück im OCA-Modul | many2many | **entfällt** (0 Kontakte mit Wert) |
| `support_ticket_string` (Statistikfeld des Buttons) | Anzahl Tickets am Button | `helpdesk_ticket_count`, `helpdesk_ticket_active_count`, `helpdesk_ticket_count_string` | integer/char, berechnet | **funktional gleichwertig/besser** – Ticketzähler und Öffnen der Ticketliste |
| Reiter-Inhalt "Support Ticket" | Support-Situation des Kontakts | Ticketliste des Kontakts (`helpdesk_ticket_ids`) | one2many `helpdesk.ticket` | **neu umgesetzt** (Abschnitt 5) |
| Tickets selbst (`website.support.ticket`) | 1.210 Support-Tickets | `helpdesk.ticket` | eigener Datentyp | **eigener Migrationsbereich** (Abschnitt 4) |

## 3. Felder, Labels, Buttons und Funktionen im Vergleich

| Prüfung | Odoo 11 | Odoo 18 |
|---|---|---|
| Reiter-Beschriftung | "Support Ticket" | "Support Ticket" (unverändert) |
| Felder im Reiter | `sla_id` (Label "SLA"), `stp_ids` (Label "Support Ticket Zugriffskonto") | `helpdesk_ticket_ids` ("Zugehörige Tickets"), nur lesend |
| Buttons | Smart-Button "Support Tickets" (Icon Ticket) | Smart-Button "Support Tickets" (Icon `fa-life-ring`) – Beschriftung in Session 112 auf den Odoo-11-Wortlaut gesetzt |
| Funktion des Buttons | Ticketliste des Kontakts öffnen | Ticketliste des Kontakts öffnen (Kontext: offene Tickets) – **gleichwertig** |
| Chatter | Ja (im Formular) | Ja (unverändert) |
| Pflichtfelder | keine | keine |

## 4. Umfang der späteren Ticket-Migration (eigener Bereich, hier nur dokumentiert)

**Odoo 11 Prod:**

| Objekt | Umfang |
|---|---|
| `website.support.ticket` | **1.210 Tickets** (483 mit Kontakt, 1.131 mit Bearbeiter, 1.202 mit Kategorie) |
| Status (`state` → `website.support.ticket.states`) | Open 26 · in Bearbeitung 12 · on Hold 1 · Geschlossen/Behoben 1.170 · an Partner weitergeleitet 0 · Verrechnung mit Kunde geklärt 1 |
| Kategorien | **18** (`amtsweg.gv.at` 627, Gemeindecloud/Verwaltungscloud 159, IFG-Portal 123, E-Learning 80, Amtssignatur 68, …) |
| SLA | 1 Datensatz ("Standard SLA Support ITK Produkte") |

**Odoo 18:** `helpdesk.ticket` (1 Testdatensatz), **6 Stufen** (Offen, in Bearbeitung, on Hold,
Geschlossen/Behoben, an Partner weitergeleitet, Verrechnung mit Kunde geklärt), **37 Kategorien**, 1 Team.

**Wichtig:** Die sechs Odoo-11-Statusnamen entsprechen **nahezu 1:1** den sechs Odoo-18-Stufen
(nur "Open" gegen "Offen"). Die Ticketstatus sind damit eindeutig zuordenbar. Für die Kategorien ist eine
Zuordnungstabelle nötig (18 gegen 37; im Odoo-18-Testbestand liegen die Kategorien des Testsystems).

## 5. Umgesetzte Änderung (Session 112, `itk_base_setup` 18.0.1.2.3)

Der Reiter "Support Ticket" enthielt nur den Platzhaltertext "Dem Kontakt zugeordnete Support-Tickets werden hier
angezeigt." Er zeigt jetzt die **Odoo-18-Ticketliste** des Kontakts (Modell `helpdesk.ticket`, Feld
`helpdesk_ticket_ids`), nur lesend gepflegt in der Helpdesk-App, mit den Spalten:
Ticketnummer, Titel, Erstellt am, Stufe, Team, Kategorie, Zugewiesener Benutzer.

Zusätzlich wurde der Smart-Button auf die Odoo-11-Beschriftung **"Support Tickets"** gesetzt (vorher "Tickets").

Keine Daten geändert oder migriert; keine Odoo-11-Technik nachgebaut.

## 6. Nachweis

`scripts/verify_s112_support_ticket.py` (read-only) prüft die Odoo-18-Felder, den gerenderten Arch des Reiters, die
Spalten und Beschriftungen, die Reiter-Reihenfolge, den Smart-Button und die Ticket-Stammdaten – lokal und auf der VM.
Zusätzlich Browser-Prüfung des Reiters im echten Chrome (Screenshot).

## 7. Offene Punkte (Entscheidungen, keine Strukturprobleme)

1. **Ticket-Migration als eigener Bereich:** 1.210 Tickets, 18 Kategorien und 1 SLA sind zu übertragen; die
   Status-Zuordnung ist eindeutig, für die Kategorien ist eine Zuordnungstabelle zu erstellen.
2. **SLA:** Der eine Odoo-11-SLA ("Standard SLA Support ITK Produkte") ist in Odoo 18 als SLA am Team zu hinterlegen
   (`helpdesk_mgmt_sla`) – zu entscheiden, welche Reaktionszeiten gelten.
3. **Kategorie-Dubletten:** Im Odoo-18-Testbestand liegen 37 Kategorien (u. a. aus den Testdaten); vor der Migration
   ist zu klären, welche davon bleiben (frühere KLÄRUNG "doppelte Helpdesk-Kategorien").
4. **Reiterliste nur lesend:** Tickets werden weiterhin in der Helpdesk-App gepflegt. Falls ITK das Anlegen direkt aus
   dem Kontakt wünscht, ist das ein Attribut (`readonly`) – jederzeit änderbar.
5. **Testdaten:** Der vorhandene Odoo-18-Testdatensatz (Ticket `HT00051`) hat keinen Kontaktbezug, deshalb ist die
   Liste im Testsystem leer (die Spalten sind sichtbar). Keine Änderung ohne Freigabe.
6. Der leere Reiter "Rechnungsstellung" bleibt weiterhin unangetastet.
