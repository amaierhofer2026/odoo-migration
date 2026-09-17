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

## 4. Ticket-Migration: **selektiv**, nicht vollständig (verbindliche Vorgabe Session 113)

**Vorgabe von Anna:** Die 1.210 Odoo-11-Tickets werden **nicht automatisch** nach Odoo 18 migriert. Vor der eigentlichen
Migration ist eine **Auswahlregel** zu definieren — z. B. anhand von

- **Status** (nur offene bzw. noch relevante Tickets),
- **Alter / Erstell- bzw. Abschlussdatum**, insbesondere: **alte, bereits abgeschlossene Tickets werden nicht
  automatisch übernommen**,
- **fachlicher Relevanz**,
- ggf. **Kategorie**.

**Noch keine Entscheidung** darüber, welche konkreten Tickets migriert werden — offener Migrationspunkt.

### 4.1 Zahlen als Entscheidungsgrundlage (Odoo 11 Prod, read-only)

| Status | Tickets |
|---|---|
| Geschlossen/Behoben | **1.170** |
| Open | 26 |
| in Bearbeitung | 12 |
| on Hold | 1 |
| Verrechnung mit Kunde geklärt | 1 |
| an Partner weitergeleitet | 0 |
| **Summe** | **1.210** |

Weitere Verteilung: 483 Tickets mit Kontaktbezug (727 ohne), 1.131 mit Bearbeiter, 1.202 mit Kategorie.
Zeitliche Spanne und Zuordnung zu Kategorien sind vor der Auswahlregel auszuwerten (u. a. `close_date`/`close_time`,
`create_date`).

### 4.2 Strukturelle Aufnahmefähigkeit von Odoo 18 (geprüft am 15.09.2026 auf der VM)

Odoo 18 (`helpdesk.ticket`) ist für die später ausgewählten Tickets vollständig aufnahmefähig:

| Erforderliche Angabe | Odoo-18-Feld | Typ | direkt beschreibbar |
|---|---|---|---|
| Kontaktbezug | `partner_id` | many2one `res.partner` | **ja** |
| Bearbeiter | `user_id` | many2one `res.users` | **ja** |
| Status / Stufe | `stage_id` | many2one `helpdesk.ticket.stage` | **ja** (6 Stufen, siehe 4.3) |
| Kategorie | `category_id` | many2one `helpdesk.ticket.category` | **ja** (37 im Testbestand) |
| Team | `team_id` | many2one `helpdesk.ticket.team` | **ja** |
| Titel | `name` | char | **ja** |
| Ticketnummer | `number` | char | Feld vorhanden, aber **schreibgeschützt** (automatische Nummer „/“ + Sequenz beim Anlegen) → **technischer Importweg nötig**, wenn die Odoo-11-Ticketnummer erhalten bleiben soll |
| Erstellzeitpunkt | `create_date` | datetime | vorhanden, aber **schreibgeschützt** → technischer Importweg nötig |
| Ersteller | `create_uid` | many2one `res.users` | vorhanden, aber **schreibgeschützt** → technischer Importweg nötig |
| Inhalte / Notizen | `description` (html) + Chatter (`message_ids`, `mail.message`) | html / one2many | **ja** (Odoo-11-Konversationsprotokoll → Chatter) |
| Anhänge | `attachment_ids` | one2many `ir.attachment` | **ja** |
| Abschluss | `closed_date`, `close_comment`, `closed` | datetime / text / boolean | `closed_date` und `close_comment` **ja**; `closed` ist berechnet (ergibt sich aus der Stufe) |
| Priorität | `priority` | selection | **ja** |

**Fazit:** Alle von Anna genannten Angaben sind abbildbar. Drei Felder (Ticketnummer, Erstellzeitpunkt, Ersteller) sind
in der Oberfläche schreibgeschützt; sollen die Odoo-11-Werte erhalten bleiben, ist beim Import ein technischer Weg
(Datenbank/Expertenschreibzugriff) nötig — kein Hindernis, aber vorab einzuplanen.

### 4.3 Status-Zuordnung (nahezu 1:1)

| Odoo 11 (`website.support.ticket.states`) | Odoo 18 (`helpdesk.ticket.stage`) | Tickets Odoo 11 |
|---|---|---|
| Open | Offen | 26 |
| in Bearbeitung | in Bearbeitung | 12 |
| on Hold | on Hold | 1 |
| Geschlossen/Behoben | Geschlossen/Behoben | 1.170 |
| an Partner weitergeleitet | an Partner weitergeleitet | 0 |
| Verrechnung mit Kunde geklärt | Verrechnung mit Kunde geklärt | 1 |

Nur „Open“ gegen „Offen“ weicht ab. Die Kategorien (Odoo 11: 18) brauchen eine Zuordnungstabelle zu den
Odoo-18-Kategorien (37 im Testbestand).

### 4.4 Kontaktbezug in Odoo 11

483 der 1.210 Odoo-11-Tickets haben einen Kontaktbezug (`partner_id`), 727 nicht (dort ist der Bezug nur über
E-Mail/Name im Ticket enthalten). Bei der Auswahl ist zu entscheiden, ob Tickets ohne Kontaktbezug überhaupt
Gegenstand der Migration sind.
## 5. Umgesetzte Änderung (Session 112, `itk_base_setup` 18.0.1.2.3)

Der Reiter „Support Ticket“ enthielt nur den Platzhaltertext „Dem Kontakt zugeordnete Support-Tickets werden hier
angezeigt.“ Er zeigt jetzt die **Odoo-18-Ticketliste** des Kontakts (`helpdesk_ticket_ids`, nur lesend, gepflegt wird in der
Helpdesk-App) mit den Spalten: Ticketnummer, Titel, Erstellt am, Stufe, Team, Kategorie, Zugewiesener Benutzer.
Zusätzlich wurde der Smart-Button auf die Odoo-11-Beschriftung **„Support Tickets“ gesetzt (vorher „Tickets“).

Keine Daten geändert oder migriert, keine Odoo-11-Technik nachgebaut, keine Ticketdaten übernommen.

## 6. Endstand-Verifikation auf der VM (Session 113, verbindliche Abnahmeumgebung)

| Prüfung | Ergebnis |
|---|---|
| `itk_base_setup` auf der VM | **18.0.1.2.3** installiert, `latest_version` identisch |
| `scripts/verify_s112_support_ticket.py` | lokal 35 OK / 0 FEHL, **VM 35 OK / 0 FEHL** |
| Felder | `helpdesk_ticket_ids` (one2many → helpdesk.ticket), Zähler- und Bezeichnungsfelder vorhanden |
| Entfallene Odoo-11-Felder | `sla_id`, `stp_ids` existieren in Odoo 18 nicht mehr |
| Reiter-Arch | Ticketliste mit allen 7 Spalten und deutschen Beschriftungen, nur lesend, kein Platzhaltertext |
| Smart-Button | `action_view_helpdesk_tickets` mit Beschriftung „Support Tickets“
| Browser-Test (echter Chrome, Kontakt 72) | Reiter gefunden; sichtbare Spalten: Ticketnummer, Titel, Erstellt am, Stufe, Team, Kategorie, Zugewiesener Benutzer; keine Bearbeiten-Buttons |
| Reiterleiste in der Browseransicht | Kontakte & Adressen · Interne Notizen · Verkauf & Einkauf · Abrechnung · Gemeinde-Information · Support Ticket |
| Screenshot | `Desktop\Odoo18-Layoutvergleich-Session95\21_VM_SupportTicket.png` |
| Ticket-Stammdaten VM | 6 Stufen, 37 Kategorien, 1 Team |
| Kontrollzahlen | 70 Kontakte unverändert; 1 Ticket im Testbestand, 0 Tickets mit Kontaktbezug (Testdaten) |

**Hinweis zur leeren Liste:** Der vorhandene Testdatensatz `HT00051` hat keinen Kontaktbezug, deshalb zeigt die Liste im
Testsystem keine Zeile an (die Spalten sind sichtbar). Eine Verknüpfung wäre eine Datenänderung und erfolgt nur auf Freigabe.

**Bereich Support Ticket ist damit strukturell migrationsbereit.**

## 7. Werkzeuge

- `scripts/verify_s112_support_ticket.py` — Felder, Reiter-Arch, Spalten, Beschriftungen, Reiterfolge, Smart-Button, Stammdaten
- `scripts/browser_reiter_pruef.py` — prüft einen Formular-Reiter im echten Browser (sichtbare Felder, Spaltenköpfe, Buttons, Zeilen;
  löscht vorher das Browserprofil, weil Odoo ab Version 17 Ansichten im Browser cached)

## 8. Offene Punkte (Entscheidungen, keine Strukturprobleme)

1. **Auswahlregel für die selektive Ticket-Migration (offener Migrationspunkt, Vorgabe Session 113):** Kriterien
   Status/Alter/fachliche Relevanz/Kategorie; alte, abgeschlossene Tickets nicht automatisch übernehmen.
   Keine Entscheidung getroffen, welche konkreten Tickets migriert werden.
2. **Technischer Importweg** für die schreibgeschützten Felder Ticketnummer, Erstellzeitpunkt und Ersteller, falls diese
   Odoo-11-Werte erhalten bleiben sollen.
3. **Kategorien:** Zuordnungstabelle Odoo 11 (18) → Odoo 18 (37 im Testbestand); frühere KLÄRUNG zu Kategorie-Dubletten.
4. **SLA:** Der eine Odoo-11-SLA („Standard SLA Support ITK Produkte“) ist in Odoo 18 am Team zu hinterlegen
   (`helpdesk_mgmt_sla`); Reaktionszeiten festzulegen.
5. **Tickets ohne Kontaktbezug:** 727 der 1.210 Odoo-11-Tickets haben keinen Kontaktbezug — vorab zu entscheiden, ob sie
   Gegenstand der Migration sind.
6. **Reiterliste nur lesend:** Falls ITK das Anlegen direkt aus dem Kontakt wünscht, ist das ein Attribut (`readonly`).
7. Der leere Reiter „Rechnungsstellung“ bleibt weiterhin unangetastet.
