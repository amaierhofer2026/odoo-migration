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
