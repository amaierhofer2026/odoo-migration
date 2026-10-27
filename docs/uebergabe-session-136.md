# Uebergabe Session 136 -> 137

Stand: 27.10.2026. Diese Datei ist der Einstieg fuer die naechste Session.

## 1. Ergebnis dieser Session

**Modul ZEITERFASSUNG: abgeschlossen** (Struktur, Datenmigration, lokal und VM).

- Odoo-11-Bestand live neu erhoben: **12.917 Zeilen, 16.832,47 Stunden**,
  2019-08-12 bis 2026-10-27, 22 Mitarbeiter, 27 Projekte mit Zeilen.
- Nach Odoo 18 migriert: **12.917 Zeilen** (12.936 inkl. 19 Zeilen fremder
  Testbestand), Summe 16.832,47 = 16.832,47, 0 fehlend, 0 doppelt.
- Die Migration ist idempotent; waehrend der Session kamen 4 neue Odoo-11-Zeilen
  dazu, ein zweiter Lauf hat genau diese 4 Zeilen nachgezogen.
- Endstand lokal und VM identisch: 12.917 migrierte Zeilen, Sammelprojekt
  "Ohne Projekt (Uebernahme Odoo 11)" mit 282 Zeilen (90:25 h).

Pruefzahlen:

| Pruefung | lokal | VM |
|---|---|---|
| `verify_s136_zeiterfassung.py` | 81 OK / 0 FEHLER | 81 OK / 0 FEHLER |
| `verify_s135_zeiterfassung.py` (Struktur) | 56 OK / 0 FEHLER | 56 OK / 0 FEHLER |
| Browserabnahme Daten (`browser_zeiterfassung_daten.py`) | bestanden | bestanden |
| Browserabnahme Rechte (`browser_zeiterfassung_rechte.py`) | bestanden | bestanden |
| Regression Verkauf/Abrechnung | 881 OK / 0 FEHL | Referenz |
| Regression Personal | 54 OK / 0 FEHL | Referenz |
| Regression Projekt | 20 OK / 0 FEHL | Referenz |

## 2. Die vier mehrdeutigen Anwesenheitszuordnungen (geloest, ohne Rueckfrage)

Odoo-11-Abwesenheit 147 = Soritz Gerd, 2020-09-01 bis 2020-09-06, 4 Tage,
Status `validate`. Zeilen O11 #394 bis #397 ("Urlaub (1/4)" bis "(4/4)", je 8 h).

Odoo 18 hat am 2020-09-01 zwei Abwesenheiten dieses Mitarbeiters:
- #1078: 2020-09-01 bis 2020-09-06, 4 Tage, **gebucht** (`validate`)
- #1060: 2020-09-01 bis 2020-09-07, 5 Tage, **abgelehnt** (`refuse`)

Regel: nur gebuchte Antraege sind Kandidaten; bei mehreren Treffern entscheidet
die gleiche Tagesanzahl. Alle vier Zeilen -> **#1078**. Ueber alle 1.131
Abwesenheitszeilen: 1.131 eindeutig, 0 mehrdeutig, 0 ohne Treffer.

## 3. Fachliche Entscheidungen dieser Session

1. **Private Aufgaben tragen keine Zeiterfassung.** Odoo 18 verweigert es
   ("Fuer eine private Aufgabe koennen keine Zeiterfassungen erstellt werden",
   auch mit Projekt im selben Aufruf). 267 Zeilen der 5 projektlosen Odoo-11-
   Aufgaben -> Sammelprojekt, Aufgabentitel als `ref` = "O11-Aufgabe <Name>".
   Die Aufgaben selbst wurden nicht veraendert (Modul Projekt unangetastet).
2. **Aufgabe aus einem fremden Projekt** (7 Zeilen, IFG-Portal mit Aufgabe aus
   "ITK-Formularserver"): Odoo 18 setzt die Aufgabe beim Anlegen zurueck. Projekt
   bleibt wie in Odoo 11, Aufgabentitel als Referenz. Lokal und VM gleich.
3. **Doppelaufgaben** ("Overhead" 2x, "[31622] Gemeinde Hochleithen" 2x): 1:1
   ueber exakt gleichen Namen bzw. ID-Reihenfolge.
4. **Abwesenheit nicht gebucht (VM)**: 11 Zeilen (Odoo-11-Abwesenheit 168, Koch
   Katharina, 2021-06-01) haben auf der VM keine Verknuepfung, weil die
   Abwesenheit dort nur im Status "Zu genehmigen" (`confirm`, #87) vorliegt -
   lokal gebucht (`validate`, #1090). Nach dem Buchen zieht ein erneuter Lauf den
   Bezug nach. Keine erfundenen Abwesenheiten.
5. **Startzeit** = 00:00 UTC des Odoo-11-Datums (Odoo 11 hatte keine Startzeit).
   Anzeige in Wiener Zeit daher 01:00/02:00; Datum und Dauer exakt, Endzeit setzt
   Odoo 18 auf Startzeit + Dauer.
6. **Beschreibungen** ohne Rand-Leerzeichen (665 Odoo-11-Zeilen hatten solche;
   bei 298 Abwesenheitszeilen waere ein Zurueckschreiben technisch gesperrt).
   Inhalt unveraendert (0 inhaltliche Abweichungen).

## 4. Modul itk_timesheet 18.0.1.0.6

- Optionale Spalte **"Referenz"** in beiden Listen, Formularfeld "Referenz"
  (schreibgeschuetzt), Filter **"Mit historischer Referenz"**.
- Menuezeile `hr_timesheet.timesheet_menu_activity_user` heisst jetzt "Meine
  Stundenzettel" (vorher "Meine Zeiterfassungen").
- **Lehre**: `hr_timesheet.timesheet_view_form_user` und `..._tree_user` **erben**
  von den Basisansichten. Felder nur in der Basis ergaenzen, sonst doppelte
  Anzeige (war als "O11-Ticket 15O11-Ticket 15" sichtbar).
- **Lehre**: Schreiben auf Zeiterfassungen mit Abwesenheitsbezug ist gesperrt
  (`project_timesheet_holidays`), auch fuer einzelne Felder.

## 5. Werkzeuge

| Datei | Zweck |
|---|---|
| `scripts/zeiterfassung_migration.py` | Migration (Trockenlauf Standard; `--ausfuehren --ich-habe-freigabe --projekt-abgeschlossen`; `--grenze N` Pilot; `--reparatur-beschreibung`) |
| `scripts/verify_s136_zeiterfassung.py` | Datenabnahme: Multimengen, Felder, Summen je Mitarbeiter/Projekt/Jahr/Monat, Beziehungen, Rechte |
| `scripts/browser_zeiterfassung_daten.py` | Browserabnahme der Daten (Listen, Suche, Filter, Gruppierung, Formular, Pivot, Start/Stopp) |
| `scripts/browser_zeiterfassung_rechte.py` | Browserabnahme der Rechte mit zwei Testbenutzern (607/608), loescht sie danach |
| `scripts/verify_s135_zeiterfassung.py` | Struktur/Wortlaute (jetzt mit Referenz-Spalte, ohne veraltete Datenzahlen) |
| `scripts/verify_s135_projekt.py` | Projektabnahme; zaehlt das Zeiterfassungs-Sammelprojekt aus |

Protokolle: `%LOCALAPPDATA%\Temp\zeiterfassung_migration\` (u. a. `ergebnis_lokal.json`,
`ergebnis_vm.json`, `abnahme_lokal.json`, `abnahme_vm.json`).
Screenshots: `%LOCALAPPDATA%\Temp\zeit_daten_*.png`, `zeit_rechte_*.png`.

## 6. Offene Punkte

1. **Abwesenheit #87 auf der VM** (Koch Katharina, 2021-06-01) ist "Zu genehmigen";
   nach dem Buchen 11 Zeilen nachziehen (`zeiterfassung_migration.py --instanz vm
   --ausfuehren ...`, idempotent).
2. Zwei Projektkunden fehlen in Odoo 18 ("[70101] Statutarstadt Innsbruck",
   "[WLV-Voeslau] Wasserleitungsverband ...") - Kundenmigration offen.
3. 19 Zeilen fremder Testbestand und 3 offene Alt-Timer bleiben stehen
   (bewusst nicht geloescht).
4. Favorit 131 (Support-Ticket-Bericht) bewusst nicht uebernommen (in Odoo 11
   schon ohne Treffer).

## 7. Git-Stand

`main` = lokal = GitHub = VM, Arbeitsbaeume sauber; Merge-Commits PR #235 und
PR #236. VM-Stash (`S124: VM-Altsstand der Vorsession`) unangetastet.
