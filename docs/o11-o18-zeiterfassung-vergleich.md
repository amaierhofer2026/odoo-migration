# Zeiterfassung: Odoo 11 gegen Odoo 18 - Bestandsaufnahme, 5-Spalten-Zuordnung, Migrationsregeln

Stand: 22.10.2026, Session 135. Sprache: nur Deutsch, einfache Zeichen.
Alles in diesem Dokument ist read-only erhoben (keine Aenderung in Odoo 11, keine
Aenderung in Odoo 18).

Auftrag (Anna): Modul ZEITERFASSUNG vollstaendig erheben, mit Odoo 18 vergleichen,
funktional mindestens auf Odoo-11-Stand bringen und die Daten **vollstaendig**
migrieren (gesamte Historie, auch ausgeschiedene/archivierte Mitarbeiter).
Personal ist abgeschlossen und wird nicht mehr angefasst.

## 0. Quellen, Werkzeuge, Rohdaten

Messung am 22.10.2026, ca. 12:00-13:30 (Odoo 11 wird laufend weiter benutzt; die
Zahlen sind ein Schnappschuss und werden vor der Migration erneut erhoben).

- Odoo 11 Produktion: `portal.it-kommunal.at`, DB `ITK_V1_a` (nur Leseabfragen).
- Odoo 18 lokal: `http://localhost:8069`, DB `odoo18_test`.
- Odoo 18 VM: `https://k001959vsx.ipax.at`, DB `odoo18_test` (Strukturpruefung folgt
  nach der Umsetzung; die VM ist die Abnahmeumgebung).
- Neue Werkzeuge (alle read-only): `scripts/erhebe_zeiterfassung.py` (Teile 1-7),
  `scripts/zeiterfassung_sofort.py`, `scripts/zeiterfassung_aktionen.py`,
  `scripts/zeiterfassung_arch_auswerten.py`.
- Rohdaten: `%USERPROFILE%\Desktop\Odoo18-Zeiterfassung-Session135\rohdaten\`.

## 1. Odoo-11-Iststand

### 1.1 Module (installiert)

| Modul | Version | Bedeutung |
|---|---|---|
| hr_timesheet | 11.0.1.0 | Zeiterfassung auf Aufgaben |
| hr_timesheet_attendance | 11.0.1.0 | Bericht Anwesenheit/Zeiterfassung |
| project_timesheet_holidays | 11.0.1.0 | Zeiterfassungszeilen aus Abwesenheiten |
| sale_timesheet | 11.0.1.0 | Abrechnung nach Aufwand, Abrechnungsart |
| website_support_analytic_timesheets | 11.0.1.0.6 | Zeiterfassung am Support-Ticket |
| project / analytic / hr | 11.0.1.1 | Basis |
| itk_projectcategory | 11.0.0.1 | ITK-Projektkategorie |

`hr_timesheet_sheet` (Stundenzettel-Freigabe) ist **nicht** installiert - es gibt in
Odoo 11 also keinen Freigabe-Workflow und keinen Stundenzettel-Kopf.

### 1.2 Datenbestand (Schnappschuss 22.10.2026)

| Punkt | Wert |
|---|---|
| Zeiterfassungszeilen `account.analytic.line` | **12.885** |
| Summe Dauer | **16.811,8 Stunden** |
| Zeitraum | 2019-08 bis 2026-10 |
| Zeilen mit Projekt | 12.603 (26 verschiedene Projekte) |
| Zeilen mit Aufgabe | 12.744 (216 verschiedene Aufgaben) |
| Zeilen ohne Projekt | 282 (davon 267 mit Aufgabe, 15 ohne alles) |
| Zeilen ohne Aufgabe | 141 (davon 126 mit Projekt) |
| Zeilen mit Mitarbeiter | 12.885 (100 %, 22 verschiedene Mitarbeiter) |
| Zeilen von heute archivierten Mitarbeitern | **1.605** (11 Mitarbeiter) |
| Zeilen mit Abwesenheitsbezug (`holiday_id`) | 1.131 (8.182,23 h, alle Projekt "Internal Project", Aufgabe "Leaves") |
| Zeilen mit Support-Ticket | 308 (295 verschiedene Tickets) |
| Dauer 0 | 17 |
| Dauer negativ | 0 |
| Zeilen ohne Beschreibung | 0 |
| Zeilen in der Zukunft | 0 |
| Betrag (`amount`) | 0,00 in allen Zeilen |
| Auftragsposition (`so_line`) | 0 Zeilen (Verkauf/Zeiterfassung ungenutzt) |
| Stichwoerter, Ref., Code, Produkt, Buchungszeile, Partner | je 0 Zeilen (nicht benutzt) |
| Einheit | Stunde in allen Zeilen |
| Firma | 1 (IT-Kommunal GmbH) |
| Abrechnungsart | non_billable 12.751, non_billable_project 122, leer 12 |

Zeilen je Mitarbeiter (vollstaendig, inkl. archiviert):

| Mitarbeiter | Zeilen | in Odoo 11 aktiv |
|---|---|---|
| Breiteneder Lorenz | 7.080 | ja |
| Tiefling Agnes | 2.899 | ja |
| Osagie Jonathan | 926 | nein |
| Maierhofer Anna | 339 | ja |
| Wuerrer Florian | 263 | ja |
| Mohammad Fahad | 209 | nein |
| Soritz Gerd | 206 | ja |
| Waiss Martina | 186 | ja |
| ausgeschieden/Steinecker Julia | 179 | nein |
| Pellkvist Tobias | 160 | ja |
| Sallmann Alexander | 104 | ja |
| Al Janabi/ausgeschieden Noor | 104 | nein |
| Breit Christiane | 80 | nein |
| ausgeschieden/Vercimak Daniel | 48 | nein |
| Czarnecki Clemens | 32 | nein |
| Mystek Jakub | 24 | ja |
| ausgeschieden/Koch Katharina | 15 | nein |
| Blagojevic Dejvid | 13 | ja |
| Meraner Daniel | 6 | ja |
| ausgeschieden/Horniak Guenter | 6 | nein |
| Daniel Miglar | 3 | nein |
| Buchinger Lorenz | 3 | nein |

Jahressummen (Stunden): 2019: 198,10 - 2020: 1.311,71 - 2021: 1.180,67 -
2022: 1.100,22 - 2023: 1.625,56 - 2024: 3.305,81 - 2025: 3.479,47 - 2026: 4.610,40.

### 1.3 Menuebaum (deutsche Anzeige, IDs)

```
Zeiterfassung (278, Sequenz 55)
  Zeiterfassung (279, Sequenz 5)
    Meine Stundenzettel (280)      -> Aktion 406
    Alle Zeiterfassungen (281)     -> Aktion 407
  Konfiguration (282)
    Einstellungen (283)            -> Aktion 408 (res.config.settings, module=hr_timesheet)
  Berichtswesen (284)
    Zeiterfassung (285)
      Nach Mitarbeiter (286)       -> Aktion 411
      Nach Projekt (287)           -> Aktion 412
      Nach Aufgabe (288)           -> Aktion 413
      Nach Abrechnungsrate (354)   -> Aktion 483
    Anwesenheit (332)              -> Aktion 459 (hr.timesheet.attendance.report)
    Kosten und Erloese (355)       -> Aktion 484
```

Zusaetzlich (ausserhalb der Wurzel Zeiterfassung): Projekt/Aufgaben/Formular hat
einen Knopf "Zeiterfassung" (Aktion 409) mit Kontext `default_project_id` und
`search_default_project_id`, und die Aufgabensicht eine Aktion 410
"Zeiterfassungseintraege" mit `default_task_id`/`search_default_task_id`.

### 1.4 Ansichten je Aktion (Odoo 11)

| Aktion | Ansichtsmodelle | Domain | Kontext |
|---|---|---|---|
| 406 Meine Stundenzettel | tree 973, kanban 980, form 976, calendar 978 | project_id != False, user_id = uid | search_default_week=1 |
| 407 Alle Zeiterfassungen | tree 974, form 977, calendar 978 | project_id != False | - |
| 411 Nach Mitarbeiter | pivot 975, tree 973, form 976 | project_id != False | search_default_groupby_employee=1 |
| 412 Nach Projekt | pivot 975, tree 973, form 976 | project_id != False | search_default_groupby_project=1 |
| 413 Nach Aufgabe | pivot 975, tree 973, form 976 | project_id != False | search_default_groupby_task=1 |
| 483 Nach Abrechnungsrate | pivot, graph (Standard) | project_id != False | search_default_week=1 |
| 484 Kosten und Erloese | pivot 1234 (Umsatz), tree 974, form 977 | project_id != False | - |
| 459 Anwesenheit | pivot (hr.timesheet.attendance.report) | - | search_default_week=True |

Inhalt der Ansichten (deutsch, gerendert):

- Liste 973 "Meine Stundenzettel": Datum, Beschreibung, Projekt (Pflicht), Aufgabe
  (Auswahl auf Projekt eingeschraenkt), "Zeit (Stunden)" (widget float_time, Summe
  "Gesamtdauer"). Kein Mitarbeiter.
- Liste 974 "Alle Zeiterfassungen": Datum, Mitarbeiter (Pflicht, nicht verlinkt),
  Benutzer (unsichtbar), Beschreibung, Projekt (Pflicht), Aufgabe, "Zeit (Stunden)".
- Formular 976 (eigene Zeilen): Datum, Beschreibung, Projekt (Pflicht), Aufgabe,
  Betrag, Dauer, Firma/Waehrung unsichtbar. **Kein** Mitarbeiterfeld.
- Formular 977 (alle Zeilen): zusaetzlich Mitarbeiter (Pflicht, nicht verlinkt),
  Benutzer unsichtbar.
- Kanban 980: Datum, Benutzer, Beschreibung, Projekt, Aufgabe, Dauer (float_time).
- Pivot 975: Mitarbeiter, Datum, Dauer (float_time).
- Kalender 978: Beschreibung, Projekt.
- Graph/Pivot der Standardmodelle: Kostenstelle, Partner, Menge, Betrag.

### 1.5 Felder `account.analytic.line` (45 Felder, deutsch)

Fachlich benutzt (mit Daten belegt): `date`, `name`, `unit_amount`, `employee_id`,
`user_id`, `project_id`, `task_id`, `account_id`, `product_uom_id`,
`timesheet_invoice_type`, `holiday_id`, `support_ticket_id`, `department_id`.

Vorhanden, aber **ohne einen einzigen Datensatz**: `amount` (ueberall 0,00),
`amount_currency`, `analytic_amount_currency`, `general_account_id`, `move_id`,
`partner_id`, `product_id`, `ref`, `code`, `tag_ids`, `so_line`,
`timesheet_invoice_id`, `timesheet_revenue`.

Vom Support-Ticket durchgereicht (nur Anzeige, nicht gespeichert): `open_time`,
`close_time`, `state`, `person_name`, `ticket_number_display`, `planned_hours`,
`remaining_hours`, `total_hours`, `effective_hours`.

Pflichtfelder in Odoo 11: `date`, `name`, `account_id`, `amount`.
`company_id` und `partner_id` sind berechnet (readonly).

### 1.6 Suche, Filter, Gruppierungen, Favoriten (Odoo 11)

Suchansicht 979 (`hr_timesheet.hr_timesheet_line_search`):
Suchfelder Datum, Mitarbeiter, Projekt, Aufgabe, Beschreibung, Abrechnungsart,
Rechnung.

Filter: "Meine Stundenzettel" (user_id = uid), "Diese Woche", "Dieser Monat",
"Abrechenbare Stunden", "Projekte mit Festpreis", "Nicht abrechenbare Stunden".
Gruppierungen: Mitarbeiter, Projekt, Aufgabe, "Monatliche Zeiterfassung" (Datum).

Gespeicherte Filter (`ir.filters`):

| ID | Name | Modell | Inhalt | Standard |
|---|---|---|---|---|
| 25 | Abrechnungsrate | account.analytic.line | project_id != False, Spaltengruppierung Datum/Monat + Abrechnungsart | ja |
| 360 | Meine Stundenzettel | account.analytic.line | Gruppierung Projekt | nein |
| 131 | Support Ticket Arbeitszeittabelle Bericht | account.analytic.line | project_id = 'Sendhybrid Aufwaende verrechenbar' | ja |

### 1.7 Rechte, Gruppen, Regeln (Odoo 11)

| Gruppe | Wirkung auf Zeiterfassung |
|---|---|
| Zeiterfassung / Benutzer (`hr_timesheet.group_hr_timesheet_user`) | eigene Zeilen R/W/C/D, Aufgabe R/W, Projekt nur lesen, Kostenstelle R/W |
| Projekt / Benutzer | Projekt R/W/C, Aufgabe R/W/C/D, Kostenstelle lesen |
| Projekt / Manager | alles |
| Personal / Mitarbeiter | Projekt/Kostenstelle/Aufgabe nur lesen |

Record Rules: "Analytic line multi company", `account.analytic.line.timesheet.user`
(Schreiben nur eigene Zeilen, R0W1C1D1), `account.analytic.line.timesheet.manager`
(nur Zeilen mit Projekt), Frontend-/Portal-Regeln, `billing.user`.

### 1.8 Automatiken, Aktionen, Workflow

- Keine `base.automation`, kein `ir.cron` und keine Server-Aktion auf
  Zeiterfassungszeilen (nur eine Server-Aktion "Projekt: Beispielprojekt
  aktivieren" auf Projekt).
- Kein Statusfeld, kein Workflow, keine Freigabe. Eine Zeile ist sofort gueltig.
- Berechnungen: `amount` (Betrag) ist in Odoo 11 ein eigenes Feld, in der Praxis
  immer 0; `total_hours`/`remaining_hours`/`effective_hours` werden aus der Aufgabe
  gelesen; `department_id`/`partner_id` sind Durchreichungen.

## 2. Odoo-18-Ausgangszustand (lokal)

### 2.1 Module

hr_timesheet 18.0.1.1, hr_timesheet_attendance 18.0.1.1, project_timesheet_holidays
18.0.1.0, project_timesheet_time_control 18.0.1.0.7 (OCA, Start/Stopp),
sale_timesheet 18.0.1.0, sale_project 18.0.1.0 (seit Session 133 installiert),
helpdesk_mgmt_timesheet 18.0.1.1.3, itk_projectcategory 18.0.1.0.3.
`timesheet_grid` ist nicht installierbar (Enterprise) - bleibt weg.

### 2.2 Bestand lokal

| Punkt | Wert |
|---|---|
| Zeiterfassungszeilen | 19 (Testdaten aus frueheren Sitzungen, **nicht** loeschen) |
| Projekte | 5 (Intern, 3 Abo-Testprojekte, Helpdesk Test-Projekt) - Testdaten |
| Aufgaben | 8 - Testdaten |
| Mitarbeiter | 25 (13 aktiv) - aus Session 134 |
| Benutzer | 18 (14 aktiv) |
| Helpdesk-Tickets | 0 |

### 2.3 Menuebaum (deutsch, IDs)

```
Zeiterfassung (661, Sequenz 75)
  Zeiterfassung (663, Sequenz 5)
    Meine Zeiterfassungen (664)   -> Aktion 1187
    Alle Zeiterfassungen (665)    -> Aktion 1190
    Arbeit starten (756)          -> Aktion 1341
  Meine Zeiterfassungen (662)     -> Aktion 1187 (Doppelung auf oberster Ebene)
  Berichtswesen (666)
    Zeiterfassung (667)
      Nach Mitarbeiter (668)      -> Aktion 1194 (timesheets.analysis.report)
      Nach Projekt (669)          -> Aktion 1195
      Nach Aufgabe (670)          -> Aktion 1196
      Nach Abrechnungsart (947)   -> Aktion 1574
    Analyse von Zeiterfassung/Anwesenheiten (672) -> Aktion 1202
  Konfiguration (671)             -> Aktion 1193
```

Odoo 18 hat **kein** Menue "Kosten und Erloese" und **kein** Menue "Anwesenheit"
(heisst "Analyse von Zeiterfassung/Anwesenheiten").

### 2.4 Ansichten je Aktion (Odoo 18)

| Aktion | Ansichtsmodelle | Domain | Kontext |
|---|---|---|---|
| 1187 Meine Zeiterfassungen | list 2657, form 2667, kanban 2672, pivot 2661, graph 2663 | project_id != False, user_id = uid | search_default_week=1, is_timesheet=1, is_my_timesheets=1 |
| 1190 Alle Zeiterfassungen | list 2659, form 2668, kanban 2672, pivot 2660, graph 2664 | project_id != False | search_default_week=1, is_timesheet=1 |
| 1194/1195/1196/1574 Berichte | timesheets.analysis.report (pivot, graph, list) | project_id != False | - |
| 1202 Anwesenheit | hr.timesheet.attendance.report (graph, pivot) | - | - |
| 1341 Arbeit starten | account.analytic.line | - | Start/Stopp-Steuerung |

Inhalt der Ansichten:

- Liste 2659 (alle): Datum, Startzeit (`date_time`, Pflicht), Endzeit
  (`date_time_end`, optional versteckt), Mitarbeiter (Pflicht, Avatar, nicht
  verlinkt), Projekt (Pflicht, keine Neuanlage), Aufgabe (Widget mit Stunden,
  optional), Beschreibung (optional, **nicht** Pflicht), Handelspartner,
  Auftragsposition (nur wenn abrechenbar), Ticket, **Zeitaufwand** (Summe "Gesamt",
  Widget timesheet_uom, rot bei > 24 h, grau bei 0), Firma, Benutzer.
  Knoepfe: Arbeit fortsetzen / Stoppen (nur bei laufender Zeit).
- Liste 2657 (meine): gleiche Spalten ohne Mitarbeiter-Pflicht.
- Formular 2668: Projekt (Pflicht), Aufgabe, Auftragsposition, Ticket, Mitarbeiter
  (Pflicht), **Datum unsichtbar**, Startzeit (Pflicht), Endzeit, Zeitaufwand,
  Beschreibung als mehrzeiliges Textfeld. Knoepfe: Arbeit fortsetzen/Stoppen,
  Verkaufsauftrag, Rechnung.
- Pivot/Graph: Mitarbeiter, Datum, Zeitaufwand; Berichte laufen ueber das
  SQL-Reportmodell `timesheets.analysis.report` (29 Felder).

### 2.5 Suche, Filter, Gruppierungen (Odoo 18)

Suchansicht 2669 (`account.analytic.line.search`) und 2671 (eigene Zeiten):
Suchfelder Beschreibung, Ticket, Ticketpartner, Datum, Mitarbeiter, Projekt,
Aufgabe, Verkaufsauftrag, Hauptaufgabe, Abteilung, Manager.

Filter: "Meine Zeiterfassungen", "With ticket", "Abrechnung zum Festpreis",
"Abrechnung nach Zeiterfassung", "Abrechnung nach Meilensteinen", "Manuell
abgerechnet", "Nicht abrechenbar", "Datum" (Monat), "Diese Woche", "Heute",
"Letzte Woche".
Gruppierungen: Datum, Projekt, Hauptaufgabe, Aufgabe, Abteilung, Manager, Ticket,
Ticketpartner, Mitarbeiter, Auftragsposition, Rechnung, Abrechnungsart.

Gegenueber Odoo 11 **fehlt** der Filter "Dieser Monat" (Odoo 11 hatte "Diese Woche",
"Dieser Monat"). Neu sind "Heute", "Letzte Woche", Ticket, Meilensteine, manuell.

### 2.6 Rechte, Gruppen (Odoo 18)

| Gruppe | Zugriff auf Zeiterfassungszeilen |
|---|---|
| Zeiterfassung / Benutzer: nur eigene Zeiterfassungen (607) | R/W/C/D, Regel: nur eigene Zeilen |
| Zeiterfassung / Benutzer: Alle Zeiterfassungen (608) | implizit alle Zeilen |
| Projekt / Benutzer | Projekt nur lesen, Aufgabe R/W/C/D (ueber Regeln) |
| Projekt / Administrator | alles |

Odoo 11 hatte **eine** Gruppe "Zeiterfassung / Benutzer" ohne Unterscheidung
"nur eigene / alle"; das Schreiben war per Record Rule auf eigene Zeilen begrenzt.

### 2.7 Technisch bindende Unterschiede fuer die Migration

1. **`date_time` (Startzeit)** ist in Odoo 18 in Liste und Formular Pflicht; Odoo 11
   kannte nur das Datum. `date` ist in Odoo 18 ein eigenes, schreibbares Feld; wird
   nur `date` geschickt, setzt `project_timesheet_time_control._eval_date` die
   Startzeit auf Datum + aktuelle Uhrzeit.
2. **Archivierte Mitarbeiter**: `account.analytic.line.create` in Odoo 18 lehnt
   Zeilen fuer archivierte Mitarbeiter hart ab ("Timesheets must be created with an
   active employee in the selected companies"), weil die Mitarbeitersuche mit
   `active_test` laeuft. Fuer 1.605 historische Zeilen (11 Mitarbeiter) ist das der
   entscheidende Punkt.
3. **`user_id`** wird in Odoo 18 aus `employee_id.user_id` berechnet und beim
   Anlegen ueberschrieben. 11 der 25 Odoo-18-Mitarbeiter haben **kein**
   Benutzerkonto (in Odoo 11 hatten alle 25 eines); betroffen sind 605 Zeilen.
4. **Zeilen ohne Projekt** koennen in Odoo 18 keine Zeiterfassung sein; zusaetzlich
   verlangt `account.analytic.line` mindestens eine Kostenstelle. Betroffen: 282
   Zeilen (90,42 h) auf den Kostenstellen "amtsweg.gv.at - Dritte" (266),
   "Customer Support" (13), "Sendhybrid Aufwaende verrechenbar" (2), "Testprojekt" (1).
5. **Projekt wird aus der Aufgabe abgeleitet**: bei 7 Zeilen gehoert die Aufgabe zu
   einem anderen Projekt als in der Zeile eingetragen (Projekt "IFG-Portal -
   Entwicklung" gegen Aufgabe 497 "Bugfixes" aus Projekt 67). Odoo 18 setzt das
   Projekt der Aufgabe.
6. **Support-Ticket**: 308 Zeilen verweisen auf 295 Odoo-11-Tickets
   (`website.support.ticket`). In Odoo 18 gibt es 0 Helpdesk-Tickets; die
   Ticketverknuepfung kann ohne Ticketmigration nicht erhalten werden.
7. **Abwesenheitszeilen**: 1.131 Zeilen (8.182,23 h) stammen aus
   `project_timesheet_holidays` und haengen an einer Abwesenheit (`holiday_id`).
   Die Abwesenheiten wurden in Session 134 migriert, die Zuordnung ist also moeglich.
8. **Projekt-/Aufgabenstammdaten fehlen in Odoo 18**: Odoo 11 hat 33 Projekte
   (5 archiviert), 714 Aufgaben (110 archiviert), 87 Stufen, 13 Stichwoerter.
   Odoo 18 hat nur 5 Testprojekte und 8 Testaufgaben. Ohne diese Stammdaten ist
   keine Zeiterfassungszeile mit Projekt/Aufgabe zuordenbar.

## 3. 5-Spalten-Zuordnung Odoo 11 -> Odoo 18

Legende Status: EINDEUTIG (technisch klar, wird umgesetzt) / ENTSCHEIDUNG (Anna) /
DOKUMENTIERT (Abweichung ohne Handlungsbedarf).

### 3.1 Menues

| Odoo-11-Bereich/Feld/Funktion | Odoo-11-Verwendung bzw. Ist-Zustand | Odoo-18-Entsprechung | notwendige Anpassung/Migrationsregel | Status / offene Entscheidung |
|---|---|---|---|---|
| Zeiterfassung (Wurzel, Sequenz 55) | eigene App mit 3 Untermenues | Zeiterfassung (661, Sequenz 75) | Wurzel bleibt; Sequenz angleichen (55) oder Odoo-18-Wert behalten | ENTSCHEIDUNG (Anzeige) |
| Zeiterfassung/Zeiterfassung/Meine Stundenzettel | Aktion 406, eigene Zeilen, Woche vorfiltert | Meine Zeiterfassungen (664, Aktion 1187) | Wortlaut auf Odoo 11 "Meine Stundenzettel" setzen (Label-Regel) | EINDEUTIG (Wortlaut) |
| Zeiterfassung/Zeiterfassung/Alle Zeiterfassungen | Aktion 407 | Alle Zeiterfassungen (665, Aktion 1190) | 1:1, keine Aenderung | EINDEUTIG |
| Zeiterfassung/Konfiguration/Einstellungen | Aktion 408 (module=hr_timesheet) | Konfiguration (671, Aktion 1193) | 1:1 | EINDEUTIG |
| Zeiterfassung/Berichtswesen/Zeiterfassung/Nach Mitarbeiter | Aktion 411, Pivot zuerst, Gruppierung Mitarbeiter | Nach Mitarbeiter (668, Aktion 1194, Reportmodell) | Bericht bleibt; Gruppierung ist im Odoo-18-Bericht voreingestellt | EINDEUTIG |
| .../Nach Projekt | Aktion 412 | Nach Projekt (669) | 1:1 | EINDEUTIG |
| .../Nach Aufgabe | Aktion 413 | Nach Aufgabe (670) | 1:1 | EINDEUTIG |
| .../Nach Abrechnungsrate | Aktion 483 (pivot, graph) | Nach Abrechnungsart (947, Aktion 1574) | Wortlaut Odoo 11 "Nach Abrechnungsrate" setzen | EINDEUTIG (Wortlaut) |
| Zeiterfassung/Berichtswesen/Anwesenheit | Aktion 459 (hr.timesheet.attendance.report) | Analyse von Zeiterfassung/Anwesenheiten (672, Aktion 1202) | Menue auf "Anwesenheit" umbenennen | EINDEUTIG (Wortlaut) |
| Zeiterfassung/Berichtswesen/Kosten und Erloese | Aktion 484 (Umsatz-Pivot + Liste) | fehlt | Menue anlegen (Aktion 484 gibt es in Odoo 18 nicht; Umsatzfelder sind in `timesheets.analysis.report` vorhanden) | ENTSCHEIDUNG |
| (kein Gegenstueck) | - | Menue "Arbeit starten" (756) | Odoo-18-Zusatz (Start/Stopp), stoert nicht | DOKUMENTIERT / ENTSCHEIDUNG (behalten) |
| (kein Gegenstueck) | - | Menue "Meine Zeiterfassungen" doppelt auf oberster Ebene (662) | Doppelung entfernen oder belassen | ENTSCHEIDUNG (Anzeige) |
| Projekt/Aufgabe: Knopf "Zeiterfassung" (Aktion 409) | Zeiten zur aktiven Aufgabe/Projekt | in Odoo 18 Smart Button "Zeiterfassung" in Projekt/Aufgabe | 1:1 vorhanden | EINDEUTIG |

### 3.2 Ansichten

| Odoo-11-Bereich/Feld/Funktion | Odoo-11-Verwendung bzw. Ist-Zustand | Odoo-18-Entsprechung | notwendige Anpassung/Migrationsregel | Status / offene Entscheidung |
|---|---|---|---|---|
| Liste eigene Zeiten (973) | Datum, Beschreibung, Projekt, Aufgabe, Zeit | Liste 2657 | Spalten angleichen: Beschreibung nicht optional, Startzeit/Endzeit ausblenden? | ENTSCHEIDUNG (Startzeit-Spalte) |
| Liste alle Zeiten (974) | + Mitarbeiter (Pflicht) | Liste 2659 | Mitarbeiter bleibt; zusaetzliche Spalten (Ticket, Auftragsposition, Handelspartner) ausblenden | ENTSCHEIDUNG |
| Formular eigene Zeilen (976) | Datum, Beschreibung, Projekt, Aufgabe, Dauer | Formular 2667 | Datum ist in Odoo 18 unsichtbar (nur Startzeit) -> Datum sichtbar machen | EINDEUTIG (Odoo-11-Bedienung) |
| Formular alle Zeilen (977) | + Mitarbeiter Pflicht | Formular 2668 | wie oben, Mitarbeiter bleibt Pflicht | EINDEUTIG |
| Kanban (980) | Datum, Benutzer, Beschreibung, Projekt, Aufgabe, Dauer | Kanban 2672 | 1:1 vorhanden | EINDEUTIG |
| Kalender (978) | Beschreibung, Projekt | in Odoo 18 nicht in der Aktion verdrahtet (nur list/form/kanban/pivot/graph) | Kalenderansicht in die Aktion aufnehmen | EINDEUTIG (Odoo-11-Funktion) |
| Pivot (975) | Mitarbeiter, Datum, Dauer | Pivot 2660/2661 | 1:1 | EINDEUTIG |
| Spalte "Zeit (Stunden)" | Widget float_time, Summe "Gesamtdauer" | "Zeitaufwand", Widget timesheet_uom, Summe "Gesamt" | Wortlaut und Summenlabel auf Odoo 11 setzen | EINDEUTIG (Wortlaut) |
| Pflicht Beschreibung | Odoo 11: Pflichtfeld, immer sichtbar | Odoo 18: `required=0`, `optional=show` | Beschreibung wieder Pflicht und sichtbar | EINDEUTIG (Odoo-11-Bedienung) |

### 3.3 Felder

| Odoo-11-Bereich/Feld/Funktion | Odoo-11-Verwendung bzw. Ist-Zustand | Odoo-18-Entsprechung | notwendige Anpassung/Migrationsregel | Status / offene Entscheidung |
|---|---|---|---|---|
| date | Datum der Leistung, Pflicht, 12.885 Zeilen | date (Datum, schreibbar) | Wert 1:1 uebernehmen | EINDEUTIG |
| (kein Gegenstueck) | - | date_time (Startzeit, Pflicht in der Ansicht) | Startzeit je Zeile setzen: 00:00 des Odoo-11-Datums | ENTSCHEIDUNG (Uhrzeit) |
| (kein Gegenstueck) | - | date_time_end (Endzeit, berechnet) | berechnet sich aus Startzeit + Dauer | EINDEUTIG |
| name | Beschreibung, Pflicht, alle Zeilen gefuellt | name (Beschreibung, char) | 1:1 uebernehmen (keine Kuerzung) | EINDEUTIG |
| unit_amount | Dauer in Stunden, Summe 16.811,8 | unit_amount (Stunden, UoM Stunde) | 1:1, Gleitkomma unveraendert | EINDEUTIG |
| employee_id | Mitarbeiter, 12.885 Zeilen, 22 Mitarbeiter | employee_id | Zuordnung ueber Arbeits-E-Mail, sonst Name; 25 von 25 eindeutig | EINDEUTIG |
| user_id | Benutzer, in Odoo 11 eigenes Feld | user_id (aus employee_id.user_id berechnet) | wird beim Anlegen ueberschrieben; 11 Mitarbeiter ohne Odoo-18-Benutzer | ENTSCHEIDUNG |
| project_id | Projekt, 12.603 Zeilen | project_id | Projektstammdaten zuerst migrieren, dann ueber Odoo-11-Projekt-ID zuordnen | EINDEUTIG (Reihenfolge) |
| task_id | Aufgabe, 12.744 Zeilen | task_id | Aufgabe zuerst migrieren; Odoo 18 setzt Projekt aus der Aufgabe | EINDEUTIG |
| account_id | Kostenstelle, Pflicht | account_id (Projekt-Kostenstelle, automatisch) | entsteht mit dem Projekt; bei Zeilen ohne Projekt siehe Sonderfall | EINDEUTIG (aus Projekt) |
| amount | Betrag, Pflicht, immer 0,00 | amount (Pflicht, Standard 0) | 0,00 setzen | EINDEUTIG |
| product_uom_id | Stunde in allen Zeilen | product_uom_id (Stunde) | Stunde setzen | EINDEUTIG |
| timesheet_invoice_type | non_billable 12.751, non_billable_project 122, leer 12 | billable_time/billable_fixed/non_billable/... | non_billable -> non_billable; non_billable_project -> non_billable (kein Odoo-18-Gegenwert); leer -> non_billable | EINDEUTIG (mappen und dokumentieren) |
| holiday_id | 1.131 Zeilen aus Abwesenheiten | holiday_id (hr.leave) | ueber die in Session 134 migrierten Abwesenheiten zuordnen | EINDEUTIG (Zuordnung pruefen) |
| support_ticket_id | 308 Zeilen, 295 Tickets | ticket_id (helpdesk.ticket) | Odoo 18 hat 0 Tickets -> Ticketnummer in `ref` erhalten | ENTSCHEIDUNG |
| department_id | 4.591 Zeilen mit Abteilung | department_id (aus Mitarbeiter berechnet) | nichts schreiben; Odoo 18 setzt die Abteilung des Mitarbeiters | DOKUMENTIERT |
| partner_id | berechnet aus Kostenstelle, 0 Zeilen mit Wert | partner_id (aus Projekt/Commercial Partner) | nichts schreiben | DOKUMENTIERT |
| so_line | 0 Zeilen | so_line | nichts migrieren | DOKUMENTIERT |
| tag_ids | 0 Zeilen | entfaellt (analytische Plaene) | nichts migrieren | DOKUMENTIERT |
| ref, code | 0 Zeilen | ref, code vorhanden | frei fuer Ticketnummer (siehe oben) | ENTSCHEIDUNG |
| product_id, general_account_id, move_id, timesheet_invoice_id | 0 Zeilen | vorhanden bzw. umbenannt (move_line_id) | nichts migrieren | DOKUMENTIERT |
| open_time, close_time, state, person_name, ticket_number_display | nur Anzeige aus dem Ticket | entfaellt | entfaellt mit dem Ticket | DOKUMENTIERT |
| planned_hours, remaining_hours, total_hours, effective_hours | Durchreichung aus der Aufgabe | entfaellt bzw. aus Aufgabe | nichts migrieren | DOKUMENTIERT |
| (kein Gegenstueck) | - | parent_task_id, manager_id, job_title | berechnet, nur Anzeige | DOKUMENTIERT |
| (kein Gegenstueck) | - | milestone_id, order_id, sale_order_state | Odoo-18-Zusatz (Verkauf/Meilensteine) | DOKUMENTIERT |

### 3.4 Filter, Gruppierungen, Suche, Favoriten

| Odoo-11-Bereich/Feld/Funktion | Odoo-11-Verwendung bzw. Ist-Zustand | Odoo-18-Entsprechung | notwendige Anpassung/Migrationsregel | Status / offene Entscheidung |
|---|---|---|---|---|
| Filter "Meine Stundenzettel" | user_id = uid | "Meine Zeiterfassungen" (mine) | Wortlaut auf Odoo 11 setzen | EINDEUTIG (Wortlaut) |
| Filter "Diese Woche" | Datumsbereich | "Diese Woche" vorhanden | 1:1 | EINDEUTIG |
| Filter "Dieser Monat" | Datumsbereich | fehlt | Filter "Dieser Monat" ergaenzen | EINDEUTIG (Odoo-11-Funktion) |
| Filter "Abrechenbare Stunden" | timesheet_invoice_type = billable_time | "Abrechnung nach Zeiterfassung" | Wortlaut auf "Abrechenbare Stunden" | EINDEUTIG (Wortlaut) |
| Filter "Projekte mit Festpreis" | billable_fixed | "Abrechnung zum Festpreis" | Wortlaut angleichen | EINDEUTIG (Wortlaut) |
| Filter "Nicht abrechenbare Stunden" | non_billable | "Nicht abrechenbar" | Wortlaut angleichen | EINDEUTIG (Wortlaut) |
| Gruppierung "Mitarbeiter" | group_by employee_id | "Mitarbeiter" vorhanden | 1:1 | EINDEUTIG |
| Gruppierung "Projekt" / "Aufgabe" | group_by project_id / task_id | vorhanden | 1:1 | EINDEUTIG |
| Gruppierung "Monatliche Zeiterfassung" | group_by date | "Datum" | Wortlaut auf "Monatliche Zeiterfassung" | EINDEUTIG (Wortlaut) |
| Gruppierungen Abteilung, Manager, Ticket, Auftragsposition, Rechnung, Abrechnungsart | nicht vorhanden | vorhanden | Odoo-18-Zusatz, stoert nicht | DOKUMENTIERT / ENTSCHEIDUNG |
| Favorit 25 "Abrechnungsrate" | Standardfilter, Spaltengruppierung | - | nicht uebernehmen (kein Bedarf belegt: 0 Verkaeufe) | ENTSCHEIDUNG |
| Favorit 360 "Meine Stundenzettel" | Gruppierung Projekt | - | optional als Favorit anlegen | ENTSCHEIDUNG |
| Favorit 131 "Support Ticket Arbeitszeittabelle" | festes Projekt "Sendhybrid..." | - | nicht uebernehmen (Projekt wird nicht migriert bzw. ohne Tickets) | ENTSCHEIDUNG |

### 3.5 Rechte und Benutzergruppen

| Odoo-11-Bereich/Feld/Funktion | Odoo-11-Verwendung bzw. Ist-Zustand | Odoo-18-Entsprechung | notwendige Anpassung/Migrationsregel | Status / offene Entscheidung |
|---|---|---|---|---|
| Zeiterfassung / Benutzer | eigene Zeilen anlegen/aendern/loeschen | "Benutzer: nur eigene Zeiterfassungen" (607) | Odoo-11-Mitglieder dieser Gruppe uebernehmen | EINDEUTIG (Mitgliederliste messen) |
| (kein Gegenstueck) | - | "Benutzer: Alle Zeiterfassungen" (608) | neu in Odoo 18; wer bekommt sie? | ENTSCHEIDUNG |
| Record Rule "eigene Zeilen" | Schreiben nur eigene | gleiche Regel in Odoo 18 | 1:1 | EINDEUTIG |
| Projekt / Benutzer, Projekt / Manager | Projekt-/Aufgabenrechte | vorhanden (Odoo 18: Projekt nur lesen, Aufgabe ueber Regeln) | nichts nachbauen | DOKUMENTIERT |
| Portal-/Frontend-Zugriff | Zeiten im Portal | vorhanden | nichts nachbauen | DOKUMENTIERT |

### 3.6 Status, Workflows, Aktionen, Buttons

| Odoo-11-Bereich/Feld/Funktion | Odoo-11-Verwendung bzw. Ist-Zustand | Odoo-18-Entsprechung | notwendige Anpassung/Migrationsregel | Status / offene Entscheidung |
|---|---|---|---|---|
| Status/Workflow | keiner (Zeile sofort gueltig) | keiner | nichts nachbauen | EINDEUTIG |
| Freigabe/Stundenzettel | nicht installiert | nicht vorhanden (timesheet_grid fehlt) | nichts nachbauen | EINDEUTIG |
| Smart Button Projekt -> Zeiterfassung | Aktion 409 | vorhanden | 1:1 | EINDEUTIG |
| Button Aufgabe -> Zeiterfassungseintraege | Aktion 410 | vorhanden (Smart Button) | 1:1 | EINDEUTIG |
| (kein Gegenstueck) | - | Start/Stopp (project_timesheet_time_control) | Odoo-18-Zusatz, stoert die Odoo-11-Bedienung nicht | ENTSCHEIDUNG (behalten) |
| (kein Gegenstueck) | - | Buttons "Verkaufsauftrag"/"Rechnung" am Formular | nur sichtbar bei Auftragsbezug (0 Zeilen) | DOKUMENTIERT |
| Server-Aktionen/Automatiken | keine auf Zeiterfassung | keine | nichts nachbauen | EINDEUTIG |

### 3.7 Berechnungen, Abhaengigkeiten, Automatiken

| Odoo-11-Bereich/Feld/Funktion | Odoo-11-Verwendung bzw. Ist-Zustand | Odoo-18-Entsprechung | notwendige Anpassung/Migrationsregel | Status / offene Entscheidung |
|---|---|---|---|---|
| amount | eigenes Feld, immer 0 | berechnet/Standard 0 | 0 setzen, keine Formel nachbauen | EINDEUTIG |
| total/remaining/effective_hours | aus Aufgabe gelesen | vorhanden (aus Aufgabe) | nichts schreiben | EINDEUTIG |
| Abwesenheitszeilen erzeugen | project_timesheet_holidays | vorhanden | Einstellung "Abwesenheitsaufgabe" ist in Odoo 18 leer (Odoo 11: Aufgabe "Leaves") | ENTSCHEIDUNG (Einstellung setzen) |
| Zeilen aus Verkauf | sale_timesheet | vorhanden, ungenutzt | nichts nachbauen | EINDEUTIG |

### 3.8 Deutsche Bezeichnungen

| Odoo-11-Bereich/Feld/Funktion | Odoo-11-Verwendung bzw. Ist-Zustand | Odoo-18-Entsprechung | notwendige Anpassung/Migrationsregel | Status / offene Entscheidung |
|---|---|---|---|---|
| account.analytic.line: 5 Felder ohne de_DE-Slot in Odoo 11 | Code, ID, Partner, Ref., Support Ticket (fachlich nicht benutzt) | in Odoo 18 zusaetzlich 16 Felder ohne de_DE-Slot: Start Time, End Time, Encoding Uom, Global Time Off, Time Off Request, Job Title, Manager, Readonly Timesheet, sale_order_state, Show Time Control, Ticket, Ticket partner | sichtbare Felder deutsch setzen: Startzeit, Endzeit, Ticket, Ticketpartner | EINDEUTIG (Label-Regel) |
| Feldbezeichnung "Zeit (Stunden)" | sichtbar in Liste/Formular | "Zeitaufwand" | auf "Zeit (Stunden)" setzen | EINDEUTIG (Label-Regel) |
| Summenlabel "Gesamtdauer" | Spaltensumme | "Gesamt" | auf "Gesamtdauer" setzen | EINDEUTIG (Label-Regel) |
| Menue-/Filterwortlaute | siehe 3.1 und 3.4 | teils abweichend | angleichen (Wortlautliste oben) | EINDEUTIG (Label-Regel) |
| "With ticket" (Filter) | - | englisch | "Mit Ticket" | EINDEUTIG (Label-Regel) |

### 3.9 Odoo-18-Zusatzfunktionen (Vorschlag: erhalten)

| Odoo-11-Bereich/Feld/Funktion | Odoo-11-Verwendung bzw. Ist-Zustand | Odoo-18-Entsprechung | notwendige Anpassung/Migrationsregel | Status / offene Entscheidung |
|---|---|---|---|---|
| - | - | Start/Stopp-Zeitsteuerung, Kanban, Graph, Pivot | bleibt; keine Odoo-11-Funktion wird dadurch veraendert | ENTSCHEIDUNG (behalten) |
| - | - | Berichte auf `timesheets.analysis.report` (Abteilung, Manager, Ticket, Auftragsposition) | bleibt | ENTSCHEIDUNG |
| - | - | Helpdesk-Zeiterfassung (ticket_id) | bleibt; nutzbar, sobald Tickets migriert sind | ENTSCHEIDUNG |
| - | - | Meilenstein-/Auftragsbezug in Zeilen | bleibt (0 Zeilen betroffen) | DOKUMENTIERT |
| - | - | "Arbeit starten"-Menue | bleibt | ENTSCHEIDUNG |

## 4. Datenmigration: Umfang und Regeln

### 4.1 Reihenfolge (jeder Schritt idempotent, Trockenlauf ist Standard)

1. Projektstufen `project.task.type` (87 in Odoo 11) und Stichwoerter `project.tags`
   (13).
2. Projekte `project.project` (33, davon 5 archiviert) samt Kostenstelle,
   Projektmanager, Kunde, Sichtbarkeit, "Zeiterfassungen erlauben".
3. Aufgaben `project.task` (714, davon 110 archiviert) samt Stufe, Zustaendigem,
   Frist, geplanter Zeit, Startdatum (`itk_date_start`), Beschreibung.
4. Zeiterfassungszeilen `account.analytic.line` (12.885) in Bloecken, nach Datum
   sortiert.
5. Kontrollen: Anzahl, Summe Stunden, Summe je Mitarbeiter/Projekt/Jahr,
   Stichproben je Sonderfall.

### 4.2 Zuordnungsschluessel

- Mitarbeiter: Arbeits-E-Mail (24 von 25), sonst Name (1) - 25 von 25 eindeutig.
- Projekt: Odoo-11-Name (alle 33 Namen sind in Odoo 18 noch nicht vergeben).
- Aufgabe: Odoo-11-Name innerhalb des zugeordneten Projekts.
- Stufe/Stichwort: Name.
- Abwesenheit: Odoo-11-`holiday_id` -> migrierte Abwesenheit (Session 134).
- Kein Abgleich ueber Datenbank-IDs zwischen den Systemen.

### 4.3 Sonderfaelle mit Zahlen

| Fall | Zeilen | Vorschlag |
|---|---|---|
| Zeilen ohne Projekt (Kostenstellenbuchung) | 282 (90,42 h) | ENTSCHEIDUNG: Sammelprojekt "Ohne Projekt (Uebernahme Odoo 11)" oder als Kostenstellenbuchung ohne Projekt (dann nicht in der Zeiterfassung sichtbar) |
| Zeilen von archivierten Mitarbeitern | 1.605 (11 Mitarbeiter) | Mitarbeiter fuer den Import kurz aktivieren, danach wieder archivieren (Odoo 18 verweigert sonst das Anlegen) |
| Mitarbeiter ohne Odoo-18-Benutzerkonto | 605 Zeilen (11 Mitarbeiter) | ENTSCHEIDUNG: inaktive Benutzer anlegen oder `user_id` leer lassen (Mitarbeiter bleibt korrekt) |
| Zeilen mit Abwesenheitsbezug | 1.131 (8.182,23 h) | mit `holiday_id` uebernehmen |
| Zeilen mit Support-Ticket | 308 | ENTSCHEIDUNG: Ticketnummer in `ref` erhalten (Tickets selbst sind nicht migriert) |
| Dauer 0 | 17 | uebernehmen (Odoo 18 erlaubt 0, Liste markiert sie grau) |
| Aufgabe gehoert zu anderem Projekt als die Zeile | 7 | Odoo 18 setzt das Projekt der Aufgabe; Zeile wird damit korrekt zugeordnet |
| `user_id` weicht vom Benutzer des Mitarbeiters ab | 1 (2024-04-09) | Odoo 18 setzt den Benutzer des Mitarbeiters; Abweichung dokumentieren |
| Abrechnungsart `non_billable_project` | 122 | auf `non_billable` mappen |

## 5. Entscheidungspunkte fuer Anna

1. **Projekt-/Aufgabenstammdaten mitmigrieren** (33 Projekte, 714 Aufgaben, 87
   Stufen, 13 Stichwoerter) - ohne sie gibt es keine Beziehungen.
   Alternativ nur die tatsaechlich in Zeiten verwendeten 26 Projekte und 216
   Aufgaben.
2. **282 Zeilen ohne Projekt**: Sammelprojekt oder Kostenstellenbuchung ohne Projekt
   (dann nicht in der Zeiterfassung sichtbar) oder weglassen.
3. **Archivierte Mitarbeiter** (1.605 Zeilen): Mitarbeiter fuer den Import kurz
   aktivieren und danach wieder archivieren (empfohlen), oder Compat-Modul, das
   Zeilen fuer archivierte Mitarbeiter erlaubt.
4. **Fehlende Benutzerkonten** (11 Mitarbeiter, 605 Zeilen): inaktive Benutzer in
   Odoo 18 anlegen (Login wie Odoo 11) oder `user_id` leer lassen.
5. **Startzeit `date_time`** fuer historische Zeilen: 00:00, 08:00 oder Importzeit.
6. **Support-Ticket-Verweis** (308 Zeilen): Ticketnummer in `ref` schreiben oder
   ohne Verweis migrieren.
7. **Odoo-18-Zusaetze**: Start/Stopp, "Arbeit starten", Berichte auf dem
   Reportmodell, Helpdesk-Zeiterfassung - alle beibehalten?
8. **Wortlaute/Menues** (siehe 3.1, 3.4, 3.8): Odoo-11-Wortlaut uebernehmen
   (Label-Regel) - pauschal oder mit Ausnahmen?
9. **Menue "Kosten und Erloese"** und **Filter "Dieser Monat"** nachbauen?
10. **Gruppe "Benutzer: Alle Zeiterfassungen"**: wer soll sie bekommen?
11. **Favoriten** (Abrechnungsrate, Support-Ticket-Bericht): uebernehmen oder nicht?

## 6. Technisch eindeutig (wird ohne Rueckfrage umgesetzt, sobald die
Entscheidungspunkte beantwortet sind)

- Uebernahme aller 12.885 Zeilen mit Datum, Beschreibung, Dauer, Mitarbeiter,
  Projekt, Aufgabe, Abwesenheit, Abrechnungsart, Einheit, Betrag 0.
- Projekt-/Aufgaben-/Stufen-/Stichwortzuordnung ueber fachliche Schluessel mit
  Abbruch bei Mehrdeutigkeit (kein Raten, kein stilles Ueberspringen).
- Beschreibung als Pflichtfeld, Datum im Formular sichtbar, Beschreibungsspalte
  sichtbar, Wortlaute "Zeit (Stunden)"/"Gesamtdauer".
- Filter "Dieser Monat" ergaenzen; Filter-/Gruppierungswortlaute angleichen.
- Menue "Meine Stundenzettel", "Nach Abrechnungsrate", "Anwesenheit" angleichen.
- Startzeit-Spalte in den Listen optional (Odoo 11 kannte sie nicht).

## 7. Offene Punkte nach der Umsetzung

- VM-Abgleich (Struktur lokal gegen VM), Browserabnahme lokal und VM,
  Regression Verkauf/Abrechnung/Personal/Helpdesk, Testdaten entfernen,
  Dreistand main = lokal = GitHub = VM.
- Odoo 11 wird weiter benutzt: vor der Migration und vor der Abnahme wird der
  Bestand neu erhoben (Drift-Abgleich).

## 8. Umsetzung Session 135 (22.10.2026)

Entschieden und umgesetzt (Details, Zahlen und Browserbelege:
`docs/o11-o18-zeiterfassung-abnahme.md`):

- Modul `itk_timesheet` 18.0.1.0.3: Listen-/Formularspalten im Odoo-11-Wortlaut
  ("Zeit (Stunden)", Summe "Gesamtdauer"), Beschreibung Pflicht, Datum im Formular
  sichtbar, Startzeit/Endzeit als optionale Spalten, deutsch benannt.
- Suche: Odoo-11-Filterwortlaute, neuer Filter "Dieser Monat", Gruppierung
  "Monatliche Zeiterfassung".
- Menues/Aktionen: "Meine Stundenzettel" (Menue 664 und Aktion 1187),
  "Nach Abrechnungsrate" (947), "Anwesenheit" (672); neues Berichtsmenue
  "Kosten und Erloese".
- Favorit "Abrechnungsrate" wieder vorhanden; Favorit 131 begruendet nicht
  uebernommen (in Odoo 11 bereits ohne Treffer, zusaetzlich keine Helpdesk-Tickets).
- Rechte: Gruppe 607 (nur eigene) an den Odoo-11-Kreis der Zeiterfassungsbenutzer
  (13 Benutzer), Gruppe 608 (alle) nur an den Odoo-11-Kreis der Projektmanager
  (12 Benutzer); bestehende Mitglieder unangetastet, keine Aufweichung.
  Zuordnung ueber Login UND Benutzername (Login hat sich bei Breiteneder geaendert).
- Support-Ticket-Verweise: keine neuen Helpdesk-Tickets, Ticketnummer als
  historische Referenz im Feld `ref` ("O11-Ticket <Nummer>") - 308 Zeilen.
- Alle Odoo-18-Zusatzfunktionen bleiben erhalten (Start/Stopp inkl. Menue
  "Arbeit starten", Kanban/Graph/Pivot, Reportmodell-Berichte, Helpdesk-Zeiten,
  Verkaufsbezug).

**Datenmigration: vorbereitet, aber gesperrt** bis das Modul Projekt abgenommen ist
(`scripts/zeiterfassung_migration.py`, Schreibsperre ueber `--projekt-abgeschlossen`).
Trockenlauf 22.10.2026: 12.886 Zeilen, 16.812,05 Stunden, 34 Projekte, 714 Aufgaben,
84 Stufen, 13 Stichwoerter, 10 inaktive Benutzer, 308 Ticket-Referenzen,
282 Zeilen ins Sammelprojekt, 1.131 Abwesenheitszeilen (1.127 eindeutig), 0 Blocker.
