# Zeiterfassung: Umsetzung und Abnahme (Struktur/Funktion) - Session 135

Stand: 22.10.2026. Sprache: nur Deutsch, einfache Zeichen.

## 0. Zwei getrennte Ergebnisse (bitte nicht vermischen)

**A) Zeiterfassung strukturell/funktional fertig:** ja, lokal umgesetzt und im
echten Browser geprueft (VM-Abnahme siehe Abschnitt 8).

**B) Datenmigration noch ausstehend:** keine einzige Zeiterfassungszeile wurde
geschrieben. Grund: die Zeiterfassung haengt an Projekten und Aufgaben, und das
Modul Projekt ist noch nicht abgenommen. Der Schreiblauf ist im Migrationsskript
technisch gesperrt (`--projekt-abgeschlossen` fehlt -> Abbruch).

## 1. Umgesetztes Modul

`addons/itk_timesheet`, Version 18.0.1.0.3, Abhaengigkeiten hr_timesheet,
sale_timesheet, project_timesheet_time_control, helpdesk_mgmt_timesheet.
Reine Anzeige-/Bedienschicht plus Laufzeit-Setup fuer Menue-/Aktionsnamen; keine
Datenmigration, keine Aenderung an Odoo 11.

| Punkt | Umsetzung |
|---|---|
| Liste "Meine Stundenzettel"/"Alle Zeiterfassungen" | Spalten wie Odoo 11: Datum, (Mitarbeiter), Projekt, Aufgabe, Beschreibung, Zeit (Stunden); Zusatzspalten Auftragsposition/Ticket/Ticketpartner/Endzeit als optionale Spalten aus |
| Spaltenlabel/Summe | "Zeit (Stunden)" mit Summe "Gesamtdauer" (Odoo 18: "Zeitaufwand"/"Gesamt") |
| Formular | Datum sichtbar (Odoo 18 blendete es aus), Beschreibung Pflicht, Startzeit/Endzeit deutsch |
| Suche | Filter "Meine Stundenzettel", "Mit Ticket", "Abrechenbare Stunden", "Projekte mit Festpreis", "Nicht abrechenbare Stunden"; Gruppierung "Monatliche Zeiterfassung"; **neuer Filter "Dieser Monat"** (Odoo 11) |
| Menues | 664 "Meine Stundenzettel", Aktion 1187 "Meine Stundenzettel", 947 "Nach Abrechnungsrate", 672 "Anwesenheit" |
| Bericht | neues Menue + Aktion "Kosten und Erloese" unter Berichtswesen (Pivot auf timesheets.analysis.report: Stunden, abrechenbare/nicht abrechenbare Zeit, Kosten, Umsatz, Marge) |
| Favorit | "Abrechnungsrate" wieder angelegt (Standardfilter, Spaltengruppierung Monat + Abrechnungsart) |
| Odoo-18-Zusätze | alle erhalten: Start/Stopp inkl. Menue "Arbeit starten", Kanban/Graph/Pivot, Berichte auf dem Reportmodell (Abteilung, Manager, Ticket, Auftragsposition), Helpdesk-Zeiterfassung, Verkaufsbezug |

Begruendung der Wortlaute: Label-Regel (Odoo-11-Bezeichnung, wo fachlich 1:1).
Odoo-18-spezifische Funktionen behalten ihre eigenen Bezeichnungen.

Technische Lehre (wieder bestaetigt): Menue- und Aktionsnamen sind Moduldaten mit
`noupdate`; ein Upgrade setzt nur die Quelle zurueck, die alte de_DE-Uebersetzung
bleibt stehen. Deshalb schreibt `setup_runtime.setze_menue_wortlaute()` /
`setze_aktions_wortlaute()` Quelle + de_DE + en_US, aufgerufen aus
`post_init_hook` und aus `migrations/<version>/post-migration.py`. Ein blosses
Versionsbump im Manifest wirkt erst nach `docker restart` + `update_list`.

## 2. Rechte (Odoo-11-Rechtekonzept, nicht aufgeweicht)

Ableitung aus Odoo 11 (read-only gemessen):

- Gruppe "Zeiterfassung / Benutzer" (42 Benutzer) durfte eigene Zeilen anlegen und
  aendern; Record Rule `account.analytic.line.timesheet.user` erlaubte Schreiben
  nur bei `user_id = user.id`.
- Schreiben auf **alle** Projekt-Zeilen erlaubte nur "Projekt / Manager" (20
  Benutzer) ueber `account.analytic.line.timesheet.manager`.

Umsetzung in Odoo 18 (`scripts/zeiterfassung_rechte.py`, idempotent, Trockenlauf
ist Standard):

| Gruppe | Mitglieder vorher | Mitglieder nachher | Regel |
|---|---|---|---|
| 607 "Benutzer: nur eigene Zeiterfassungen" | 2 | **13** | alle aktiven internen Benutzer, die in Odoo 11 in der Zeiterfassungsgruppe waren |
| 608 "Benutzer: Alle Zeiterfassungen" | 2 | **12** | nur der Odoo-11-Kreis der Projektmanager |

Nicht zugeordnet: christiane.breit (in Odoo 11 nicht in der Zeiterfassungsgruppe),
sowie die 10 neu anzulegenden inaktiven Benutzer (inaktiv, kein Bedarf).
Bestehende Mitglieder wurden nicht entfernt.

Wichtiger Zuordnungsfall: der Login lautet in Odoo 11 `lorenz.galler@it-kommunal.at`
(Benutzername "Breiteneder Lorenz"), in Odoo 18 `lorenz.breiteneder@...`. Ein
reiner Login-Vergleich uebersieht genau den Hauptzeiterfasser (7.080 Zeilen); das
Skript ordnet deshalb zusaetzlich ueber den Benutzernamen zu.

## 3. Favoriten

| Odoo-11-Favorit | Status |
|---|---|
| 25 "Abrechnungsrate" (Standard, project_id != False, Spaltengruppierung Datum/Monat + Abrechnungsart) | uebernommen als `itk_timesheet.filter_timesheet_abrechnungsrate_itk` |
| 360 "Meine Stundenzettel" (Gruppierung Projekt) | nicht uebernommen: die Gruppierung ist ueber "Projekt" im Suchmenue direkt erreichbar, kein Standardfilter |
| 131 "Support Ticket Arbeitszeittabelle Bericht" | **nicht abbildbar, begruendet:** die Domain lautet `[('project_id','=','Sendhybrid Aufwaende verrechenbar')]`; in Odoo 11 gibt es kein Projekt dieses Namens (0 Treffer), nur eine Kostenstelle (id 31, ohne Projekt). Der Favorit war schon in Odoo 11 ein Filter ohne Ergebnis. Zusaetzlich gibt es in Odoo 18 keine migrierten Helpdesk-Tickets. Kein Nachbau, damit kein irrefuehrender Filter entsteht. |

## 4. Support-Ticket-Verweise der 308 Zeilen (Entscheidung und technische Loesung)

Entscheidung (Anna, 22.10.2026): Helpdesk startet in Odoo 18 neu, es werden
**keine** historischen Tickets und **keine** Ersatz-Tickets angelegt. Es darf
keine falsche Relation entstehen, die historische Referenz muss aber erhalten
bleiben.

Technische Loesung in der Migrationslogik:

- Kein Schreiben von `ticket_id` (keine Verknuepfung zu Odoo-18-Helpdesk-Tickets).
- Die Odoo-11-Ticketnummer wird als historische Referenz in das Freifeld `ref`
  geschrieben, Format `O11-Ticket <Nummer>` (Beispiel: `O11-Ticket 15`).
- Betroffen: 308 Zeilen, 295 verschiedene Tickets, Zeitraum ab 2020-01.
- Nachvollziehbarkeit: Nummer steht in der Zeile, zusaetzlich bleibt der
  urspruengliche Beschreibungstext unveraendert; die Ticketnummern wurden in
  Odoo 11 read-only erhoben (`website.support.ticket.ticket_number`).

## 5. Migrationslogik (vorbereitet, gesperrt)

`scripts/zeiterfassung_migration.py`:

- Trockenlauf ist Standard; Schreiben nur mit
  `--ausfuehren --ich-habe-freigabe --projekt-abgeschlossen`, sonst Abbruch mit
  Klartext ("Migration gesperrt - Modul Projekt ist noch nicht abgenommen").
- Ziel-DB muss auf `odoo18_test` enden; Odoo 11 wird ausschliesslich gelesen.
- Zuordnung ueber fachliche Schluessel: Mitarbeiter ueber Arbeits-E-Mail (24 von
  25), sonst Name (1); Projekt ueber Namen; Aufgabe ueber Titel innerhalb des
  Projekts; Stufe/Stichwort ueber Namen; Benutzer ueber den Odoo-18-Mitarbeiter,
  sonst Login. Bei Mehrdeutigkeit Abbruch, kein Raten.
- Sonderregeln: Zeilen ohne Projekt -> Sammelprojekt "Ohne Projekt (Uebernahme
  Odoo 11)"; Startzeit = 00:00 des Odoo-11-Datums; `non_billable_project` ->
  `non_billable`; Betrag 0; Einheit Stunde; Abwesenheitsbezug ueber Mitarbeiter +
  Beginn der Abwesenheit; archivierte Mitarbeiter nur fuer den Import kurz aktiv,
  danach wieder archiviert; 10 fehlende Benutzerkonten als inaktive Benutzer.
- Idempotenz: Zeilen werden ueber (Datum, Mitarbeiter, Projekt, Aufgabe, Dauer,
  Beschreibung) gegen den Odoo-18-Bestand geprueft; ein zweiter Lauf muss
  0 Neuanlagen melden.

### Trockenlauf-Ergebnis (22.10.2026, lokal, keine Schreibzugriffe)

| Punkt | Wert |
|---|---|
| Odoo-11-Zeilen (live erhoben) | **12.886** (Schnappschuss; zwischen den Messungen +1 Zeile, Odoo 11 wird weiter benutzt) |
| Summe Dauer | 16.812,05 Stunden |
| Projekte im Plan | 33 + Sammelprojekt = 34 neu |
| Aufgaben im Plan | 714 neu |
| Stufen | 84 neu (3 bereits vorhanden) |
| Stichwoerter | 13 neu |
| Benutzerkonten anzulegen (inaktiv) | 10 |
| Zeilen mit Ticket-Referenz (`ref`) | 308 |
| Zeilen ohne Projekt (Sammelprojekt) | 282 |
| Zeilen mit Abwesenheitsbezug | 1.131 |
| davon Abwesenheit eindeutig zugeordnet | 1.127 |
| davon ohne Treffer | 0 |
| davon mehrdeutig | 4 (Odoo-11-Abwesenheit 147, zwei Treffer in Odoo 18) |
| Blocker | 0 |

Offene Punkte fuer den Schreiblauf: die 4 mehrdeutigen Abwesenheitszeilen (O11
147) sind vor dem Lauf zu klaeren; zwei Projektkunden fehlen in Odoo 18
("[70101] Statutarstadt Innsbruck", "[WLV-Voeslau] Wasserleitungsverband ...") -
Kundenprojekt-Migration ist offen, die Projekte werden ohne Kunde angelegt und
der Punkt dokumentiert.

## 6. Pruefwerkzeuge

| Werkzeug | Zweck |
|---|---|
| `scripts/verify_s135_zeiterfassung.py --instanz lokal|vm` | Struktur, Wortlaute, Menues, Bericht, Favorit, Gruppen (read-only) |
| `scripts/browser_zeiterfassung_abnahme.py --instanz lokal|vm` | echter Browser: Menues, Spalten, Formularfelder, Suche, Favorit, Bericht, Start/Stopp, Screenshots |
| `scripts/zeiterfassung_rechte.py --instanz ... [--ausfuehren --ich-habe-freigabe]` | Gruppenmitglieder nach Odoo-11-Konzept |
| `scripts/zeiterfassung_migration.py --instanz ... [--plan-schreiben]` | Trockenlauf/Migration (gesperrt bis Projekt-Abnahme) |
| `scripts/erhebe_zeiterfassung.py`, `zeiterfassung_aktionen.py`, `zeiterfassung_arch_auswerten.py`, `zeiterfassung_sofort.py` | read-only Bestandsaufnahme Odoo 11/Odoo 18 |

## 7. Browserbeleg lokal (22.10.2026)

Echter Browser (Chrome via Playwright), Login als anna.maierhofer:

- Liste "Meine Stundenzettel": Spalten Datum, Projekt, Aufgabe, Beschreibung,
  Zeit (Stunden); Spaltensumme unten (Beispiel 18:00); Favorit "Abrechnungsrate"
  als Facette aktiv.
- Liste "Alle Zeiterfassungen": zusaetzlich Spalte Mitarbeiter; Pager 1-19 von 19.
- Suchmenue: "Meine Stundenzettel", "Mit Ticket", "Projekte mit Festpreis",
  "Abrechenbare Stunden", "Abrechnung nach Meilensteinen", "Manuell abgerechnet",
  "Nicht abrechenbare Stunden", "Datum" (Untermenue mit "Dieser Monat",
  "Diese Woche", "Heute", "Letzte Woche"), Gruppierungen "Monatliche
  Zeiterfassung", Projekt, Hauptaufgabe, Aufgabe, Abteilung, Manager, Mitarbeiter,
  Auftragsposition, Rechnung, Abrechnungsart; Favorit "Abrechnungsrate".
- Formular: Labels Projekt, Aufgabe, Ticket, Mitarbeiter, Datum, Startzeit,
  Endzeit, Zeit (Stunden).
- Bericht "Kosten und Erloese" oeffnet als Pivot.
- Start/Stopp: Menue "Arbeit starten" oeffnet den OCA-Assistenten; er meldet
  "3 laufende Timer gefunden" - das sind drei Altzeilen aus frueheren Sitzungen
  (ids 1, 2, 7, Administrator, Dauer 0, ohne Endzeit), **nicht** aus dieser
  Session; sie werden nicht geloescht (fremder Bestand).

Screenshots: `%TEMP%\zeit_abn\lokal_1_liste_meine.png` ... `_6_start_stopp.png`,
Messwerte `%TEMP%\zeit_abn\lokal.json`.

## 8. VM-Abnahme (22.10.2026, Abnahmeumgebung)

- Deploy: Branch `s135-zeiterfassung-struktur` auf der VM geprueft, danach
  `main` (Merge-Commit `4909edf`, PR #231), `docker compose restart odoo`,
  Modul `itk_timesheet` 18.0.1.0.3 installiert/aktualisiert.
- `verify_s135_zeiterfassung.py --instanz vm`: **50 OK / 0 FEHLER** (lokal
  ebenfalls 50/0).
- Rechte auf der VM gesetzt (gleiches Skript): Gruppe 607 + 11 Benutzer,
  Gruppe 608 + 10 Benutzer; Endstand VM 607 = 13, 608 = 12 - identisch zu lokal.
- Browser auf der VM (Chrome/Playwright, https://k001959vsx.ipax.at):
  Spalten "Datum, Projekt, Aufgabe, Beschreibung, Zeit (Stunden)" (alle Zeiten
  zusaetzlich "Mitarbeiter"), Breadcrumb/Aktion "Meine Stundenzettel",
  Formularlabels "Projekt, Aufgabe, Ticket, Mitarbeiter, Datum, Startzeit,
  Endzeit, Zeit (Stunden)", Favorit "Abrechnungsrate", Bericht
  "Kosten und Erloese" oeffnet, Start/Stopp-Assistent antwortet.
- Regression: Verkauf/Abrechnung **881 OK / 0 FEHL** in 11 Prueflaeufen,
  Personal **54 OK / 0 FEHL** (lokal).

### Pruefzahlen im Ueberblick

| Pruefung | lokal | VM |
|---|---|---|
| `verify_s135_zeiterfassung.py` | 50 / 0 | 50 / 0 |
| Browserabnahme (Spalten, Formular, Suche, Favorit, Bericht, Start/Stopp) | bestanden | bestanden |
| Regression Verkauf/Abrechnung | 881 / 0 | (Referenzstand 881 / 0) |
| Regression Personal | 54 / 0 | (Referenzstand 54 / 0) |

## 9. Offene Punkte

1. **Datenmigration** gesperrt bis Modul Projekt abgenommen ist (Anna).
2. 4 Zeilen mit mehrdeutigem Abwesenheitsbezug (O11-Abwesenheit 147).
3. Zwei Projektkunden fehlen in Odoo 18 (Partner-/Kundenmigration offen).
4. 19 vorhandene Testzeilen und 3 offene Timer aus frueheren Sitzungen:
   dokumentiert, nicht geloescht (fremder Bestand).
5. Favorit 131 nicht abbildbar (siehe Abschnitt 3).

### Dreistand

`main` = lokal = GitHub = VM = Merge-Commit `4909edf` (PR #231), Arbeitsbaeume
sauber; VM-Strukturpruefung 50/0.

## 10. Session 136 (27.10.2026): Datenmigration abgeschlossen (lokal)

Odoo 11 wird produktiv weiterbenutzt, deshalb wurde der Bestand vor dem Lauf neu
erhoben. Endstand lokal: **12.917 Zeilen / 16.832,47 Stunden** (Zeitraum
2019-08-12 bis 2026-10-27, 22 Mitarbeiter, 27 Projekte mit Zeilen). Waehrend der
Arbeit kamen 4 neue Odoo-11-Zeilen hinzu; ein zweiter (idempotenter) Lauf hat nur
diese 4 Zeilen nachgezogen (12.913 uebersprungen, 4 neu).

### 10.1 Ergebnisse lokal

| Punkt | Wert |
|---|---|
| Zeilen Odoo 11 (live) | 12.917 |
| davon nach Odoo 18 uebernommen | 12.917 (0 fehlend, 0 doppelt) |
| Zeilen Odoo 18 gesamt | 12.936 (12.917 migriert + 19 fremder Testbestand) |
| Stunden | 16.832,47 = 16.832,47 |
| Zeilen ohne Projekt -> Sammelprojekt | 282 (Kostenstelle bleibt als Referenz) |
| Zeilen mit privater Odoo-11-Aufgabe | 267 (Aufgabenname bleibt als Referenz) |
| Zeilen mit Ticket-Referenz | 308 (`ref` = "O11-Ticket <Nummer>") |
| Zeilen mit Abwesenheitsbezug | 1.131, alle eindeutig zugeordnet |
| Zeilen archivierter Mitarbeiter | 1.605 (11 Mitarbeiter kurz aktiviert, danach wieder archiviert) |
| Zeilen auf archivierten Projekten | 1.226 |
| Zeilen auf archivierten Aufgaben | 4.362 |
| Neue Helpdesk-Tickets | 0 (keine Verknuepfung, `ticket_id` leer) |
| Pruefung | `verify_s136_zeiterfassung.py`: **80 OK / 0 FEHLER** |
| Strukturpruefung | `verify_s135_zeiterfassung.py`: **56 OK / 0 FEHLER** |

### 10.2 Die vier mehrdeutigen Abwesenheitszeilen (Odoo-11-Abwesenheit 147)

Odoo-11-Abwesenheit 147 = Soritz Gerd, 2020-09-01 bis 2020-09-06, 4 Tage,
Status `validate`. Betroffene Zeilen: O11 #394 bis #397 ("Urlaub (1/4)" bis
"(4/4)", je 8 h, Projekt "Internal Project", Aufgabe "Leaves").

Odoo 18 hat am 2020-09-01 **zwei** Abwesenheiten dieses Mitarbeiters:

| Odoo-18-Abwesenheit | Zeitraum | Tage | Status |
|---|---|---|---|
| #1078 | 2020-09-01 bis 2020-09-06 | 4,0 | gebucht (`validate`) |
| #1060 | 2020-09-01 bis 2020-09-07 | 5,0 | abgelehnt (`refuse`) |

Aufloesung ohne Rueckfrage, weil technisch eindeutig: abgelehnte und offene
Antraege sind keine gebuchten Abwesenheiten. Kandidaten sind nur Zeilen mit
Status `validate`; bei mehreren Treffern entscheidet zusaetzlich die gleiche
Tagesanzahl. Ergebnis: alle vier Zeilen -> **#1078**. Ueber alle 1.131
Abwesenheitszeilen: 1.131 eindeutig, 0 ohne Treffer, 0 mehrdeutig.

### 10.3 Zwei technische Sperren von Odoo 18 und ihre Folgen

1. **Private Aufgaben tragen keine Zeiterfassung.** Odoo 18 antwortet "Fuer eine
   private Aufgabe koennen keine Zeiterfassungen erstellt werden" - auch wenn im
   selben Aufruf ein Projekt mitgegeben wird (am 27.10.2026 belegt). Die 267
   Zeilen der 5 projektlosen Odoo-11-Aufgaben (FSW Update, FSW update, 3x BRZ
   Wahlkartenantraege) gehen deshalb ins Sammelprojekt; der Aufgabentitel bleibt
   als `ref` = "O11-Aufgabe <Name>" erhalten. Die Aufgaben selbst wurden nicht
   veraendert (Modul Projekt bleibt unangetastet).
2. **Zeiterfassungen mit Abwesenheitsbezug sind schreibgeschuetzt.** Ein
   nachtraegliches Zurueckschreiben von Beschreibungen ist bei 298 Zeilen
   gesperrt. Deshalb werden Beschreibungen einheitlich ohne Rand-Leerzeichen
   geschrieben: 665 Odoo-11-Zeilen hatten solche (" (1/1)", "neues Formular
   erstellt "), der Text selbst ist unveraendert (Pruefung: 0 inhaltliche
   Abweichungen, 665 reine Leerzeichen-Abweichungen).

### 10.4 Weitere Befunde aus dem Bestand (unveraendert uebernommen)

- **7 Zeilen** haben eine Aufgabe aus einem **anderen** Projekt (IFG-Portal-Zeilen
  mit der Aufgabe "Neue Features" aus "ITK-Formularserver - Entwicklung"). Odoo 11
  erlaubt das; die Zeilen bleiben genau so.
- **Doppelaufgaben**: "Overhead" existiert 2x in "IFG-Portal - Entwicklung",
  "[31622] Gemeinde Hochleithen" 2x in "Datenschutz in den Gemeinden". Zuordnung
  1:1 ueber exakt gleichen Namen bzw. Reihenfolge der IDs; die 14 Zeilen der
  Odoo-11-Aufgabe 320 liegen auf Odoo-18-Aufgabe 692.
- **Startzeit**: gespeichert wird 00:00 UTC des Odoo-11-Datums (Odoo 11 kannte
  keine Startzeit). Die Oberflaeche zeigt Wiener Zeit, also 01:00 bzw. 02:00; das
  Datum und die Dauer sind exakt. Die Endzeit setzt Odoo 18 selbst auf
  Startzeit + Dauer (0 Abweichungen bei 12.917 Zeilen).
- **Abrechenbarkeit**: Odoo 11 hat ausschliesslich `non_billable` (12.779),
  `non_billable_project` (122) und leer (12). Odoo 18 berechnet den Typ selbst;
  alle migrierten Zeilen stehen auf "Nicht abrechenbar".
- **Eine historische Benutzerzuordnung** weicht ab: eine Zeile von Breiteneder
  Lorenz wurde in Odoo 11 unter dem Benutzer von Agnes Tiefling erfasst; die
  Zuordnung bleibt so erhalten.
- **Eigener Login**: der Browser-Login `anna.maierhofer@...` ist in Odoo 18 der
  Benutzer "Administrator" (id 2), nicht "Maierhofer Anna" (id 16). "Meine
  Stundenzettel" zeigt daher 7 eigene Zeilen des Administrators; die 339 Zeilen
  von Maierhofer Anna sind ueber "Alle Zeiterfassungen" bzw. die Gruppierung
  sichtbar. Kein Datenfehler, nur eine Login-Zuordnung.

### 10.5 Modul-Zusatz (Version 18.0.1.0.6)

- Optionale Spalte **"Referenz"** in beiden Listen, Formularfeld "Referenz"
  (schreibgeschuetzt), Suchfilter **"Mit historischer Referenz"**.
- Menuezeile `hr_timesheet.timesheet_menu_activity_user` heisst jetzt ebenfalls
  "Meine Stundenzettel" (Odoo 11); vorher stand dort "Meine Zeiterfassungen".
- Lehre: `hr_timesheet.timesheet_view_form_user` und `..._tree_user` **erben** von
  den Basisansichten. Ein Feld, das in Basis- und Folgeansicht eingefuegt wird,
  erscheint doppelt (im Formular sichtbar als "O11-Ticket 15O11-Ticket 15").
  Felder deshalb nur in der Basisansicht ergaenzen.

### 10.6 Browserabnahme lokal (echter Browser, 27.10.2026)

| Pruefung | Ergebnis |
|---|---|
| "Meine Stundenzettel" | Spalten Datum, Projekt, Aufgabe, Beschreibung, Zeit (Stunden); Favorit "Abrechnungsrate"; 7 eigene Zeilen des Logins |
| "Alle Zeiterfassungen" | Spalten inkl. Mitarbeiter; Liste zeigt "10000+" (Odoo-Obergrenze der Anzeige), echte Zahl 12.936 per RPC |
| Suche "IFG-Portal" | 81 Treffer |
| Filter "Mit historischer Referenz" | 575 Zeilen (= 308 Ticket + 267 Aufgabe) |
| Filter "Dieser Monat" | 258 Zeilen |
| Gruppierung "Projekt" | 29 Gruppen, darunter "Ohne Projekt (Uebernahme Odoo 11) (282) 90:25" |
| Formular einer migrierten Zeile | Projekt, Aufgabe, Ticket leer, Mitarbeiter, Datum 02.01.2020, Startzeit, Endzeit, Zeit 00:15, Beschreibung, Referenz "O11-Ticket 15" |
| Projekt-/Aufgabenformular aus der Zeile | beide oeffnen mit richtigem Titel |
| Zeile eines archivierten Mitarbeiters | oeffnet, Mitarbeiter und Beschreibung korrekt |
| Bericht "Kosten und Erloese" | Pivot mit Monatsspalten ab August 2019 |
| Start/Stopp | Assistent antwortet ("3 laufende Timer gefunden" = Altbestand) |
| Rechte Gruppe 607 (Testbenutzer) | leere Liste, fremde Zeile per URL -> Zugriffsfehler, Suche 0 Treffer |
| Rechte Gruppe 608 (Testbenutzer) | 12.936 Zeilen sichtbar, fremde Zeile oeffnet |
| Testbenutzer | beide nach der Pruefung geloescht |

Screenshots: `%TEMP%\zeit_daten_*.png`, `%TEMP%\zeit_rechte_*.png`; Messwerte
`%TEMP%\zeit_daten.json`, `%TEMP%\zeit_rechte.json`.

### 10.7 Regression (lokal, nach der Migration)

| Bereich | Ergebnis |
|---|---|
| Verkauf/Abrechnung (11 Prueflaeufe) | 881 OK / 0 FEHL |
| Personal | 54 OK / 0 FEHL |
| Projekt | 20 OK / 0 FEHL (Sammelprojekt der Zeiterfassung ausgenommen) |
| Zeiterfassung Struktur | 56 OK / 0 FEHL |
| Zeiterfassung Daten | 80 OK / 0 FEHL |

Das Sammelprojekt "Ohne Projekt (Uebernahme Odoo 11)" ist das einzige neue
Projekt; die 33 migrierten Projekte und 715 Aufgaben des Projektmoduls sind
unveraendert (Pruefung zaehlt sie ohne Sammelprojekt).
