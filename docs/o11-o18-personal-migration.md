# Bereich PERSONAL: Umsetzung und Datenmigration (Odoo 11 -> Odoo 18)

Status: **technisch fertig, manuelle Abnahme durch Anna offen** (21.10.2026).
Die Migration ist ausgefuehrt und automatisiert geprueft; die fachliche Abnahme erfolgt
durch Annas eigene Browserkontrolle gegen Odoo 11. Bis dahin werden keine Personaldaten
mehr geaendert.

Stand 21.10.2026. Grundlage: `docs/o11-o18-strukturvergleich-personal.md` (read-only
Bestandsaufnahme). Odoo 11 wurde ausschliesslich gelesen.

## 1. Struktur (Modul itk_hr)

`addons/itk_hr` 18.0.1.0.1, nur Ansichten und Rechte, keine Datensaetze:

- Gruppenueberschriften "Kontaktinformationen" und "Position" im Kopfbereich
  (Odoo 11 hatte sie, Odoo 18 zeigte die Felder ohne Ueberschrift).
- Feld `notes` als "Weitere Informationen" am Ende des Reiters "Arbeitsinformationen"
  (Feld war vorhanden, aber in keiner Ansicht eingebaut).
- Wortlaut: `job_id` = "Position" (statt "Stelle"), `coach_id` = "Ausbilder" (statt "Coach"),
  Gruppierung `group_job` = "Arbeitsstelle".
- Gruppierung "Ausbilder" in der Mitarbeitersuche (Odoo 11 hatte sie).
- Mitarbeiterliste: Aktivitaetsspalten standardmaessig ausgeblendet, Listentitel "Personal".
- Menues/Aktion auf "Personal" (App, Untermenue, Liste) - Odoo-11-Wortlaut.
- Leserecht fuer alle internen Benutzer auf `hr.employee` und `hr.job` (Odoo-11-Stand);
  Menue "Abteilungen" nur fuer Personalsachbearbeiter (Odoo-11-Stand).
- de_DE-Slots der vier Menue-/Aktionstexte ueber `scripts/hr_labels_de.py --setzen`
  (der Modul-Record setzt nur den Basistext, die Oberflaeche liest de_DE).

Bewusst nicht nachgebaut: `is_absent_totay` (Odoo 18: `is_absent`), `manual_attendance`,
`is_address_home_a_company`, `timesheet_cost` (Odoo 18: `hourly_cost`), `address_home_id`
(Odoo 18 fuehrt Privatadresse in `private_*`). Odoo-18-Zusatzfunktionen (employee_type,
departure_*, skills, badges, private_*) bleiben unveraendert.

## 2. Datenmigration

Aufruf: `python scripts/hr_migration.py --instanz lokal|vm`
(Standard = Trockenlauf; Schreiben nur mit `--ausfuehren --ich-habe-freigabe`).
Ruecknahme der eigenen Migrationsdaten: `scripts/hr_migration_cleanup.py`.

Zuordnung der Mitarbeiter (keine IDs):

1. Arbeits-E-Mail normalisiert -> 23 Mitarbeiter
2. Name normalisiert (nur wenn keine E-Mail) -> 1 Mitarbeiter (Buchinger Hannah)
3. Benutzer-Login nur als Gegenprobe (bei Breiteneder Lorenz abweichend)

Ergebnis: 24 vorhandene Odoo-18-Mitarbeiter wurden feldweise ueberschrieben,
1 Mitarbeiter neu angelegt (Meraner Daniel), keine Dublette, keine Loeschung.

Stammdaten:

- Arbeitszeitmodelle: 9 Odoo-11-Modelle -> 8 Odoo-18-Modelle, weil zwei Modelle
  ("Arbeitsstunden von IT-Kommunal GmbH") identischen Namen UND identische Zeiten haben.
  Die Zeiten wurden exakt aus Odoo 11 uebernommen (Odoo legt neue Modelle mit 40h-Standard an);
  Null-Zeilen (0-0) wurden nicht uebernommen.
- Arbeitsorte: 2 (aus 3 Odoo-11-Texten; "…A-1210 Wien" und "…1210 Wien" sind dieselbe Adresse).
- Urlaubsarten: 28 Odoo-11-Eintraege -> 20 Namen -> 19 neu angelegt, 1 vorhanden ("Unbezahlt").
  Fuenf Namen waren in Odoo 11 mehrfach belegt (z. B. "gesetzlicher Jahresurlaub" 3x) und
  zeigen jetzt auf dieselbe Odoo-18-Art.

Belegdaten:

| Objekt | Odoo 11 | uebernommen | Anmerkung |
|---|---|---|---|
| Mitarbeiter | 25 (13 aktiv) | 25 (13 aktiv) | 12 archiviert wie in Odoo 11 |
| Anwesenheiten | 192 | 192 | 2026, ein Mitarbeiter |
| Urlaubsansprueche | 69 | 65 | 1 ohne Mitarbeiter, 2 mit 0 Tagen, 1 gleichwertige Dublette |
| Urlaubsantraege | 482 | 482 | inkl. 2 ueberschneidender und 9 Antraege mit 0 Tagen |
| Zeiterfassung | 12.854 | 0 | gehoert zum Projekt-/Zeiterfassungsbereich |

## 3. Die 16 Sonderfaelle (vollstaendig geloest)

Ursachen und Loesung:

1. **5 Antraege ohne persoenlichen Anspruch** (Breiteneder Lorenz 3x Augleichstage,
   Czarnecki Clemens 1x Krankheitsstaende, Mohammad Fahad 1x Krankheitsstaende).
   Ursache war nicht der Kategorie-Anspruch, sondern das Odoo-18-Gating: Odoo 11 fuehrt
   `limit` als Hinweis, hat Antraege ohne Anspruch aber zugelassen. Loesung:
   `requires_allocation` = "yes" nur, wenn in Odoo 11 JEDER Antrag der Art durch einen
   persoenlichen Anspruch gedeckt war; sonst "no". Datengetrieben, nichts erfunden.
2. **2 ueberschneidende genehmigte Altantraege** (Waiss Martina 16.-22.07.2023,
   Tiefling Agnes 12.02.2025). Odoo 18 verbietet Ueberschneidungen. Fuer die Migration
   wird der vorgesehene Kontextschalter `leave_skip_date_check=True` **nur im
   Anlage-Aufruf** verwendet (Quelle: `hr_holidays/models/hr_leave.py:572`). Fuer die
   normale Benutzererfassung bleibt die Pruefung unveraendert aktiv.
3. **9 Antraege mit 0 Tagen**: Odoo 11 hat selbst 0 Tage gespeichert (Krankmeldungen und
   einzelne andere Arten, Datumsspanne ohne verrechenbare Arbeitszeit, u. a. weil die
   Zeitstempel ausserhalb der Arbeitszeit liegen). Sie wurden mit den Originaldaten
   uebernommen; Odoo 18 berechnet ebenfalls 0 Tage. Es wurde nichts aufgerundet.

## 4. Kategorie-Urlaubsanspruch Odoo 11 ID 7 (read-only geprueft)

- Datensatz: `hr.holidays` ID 7, `type=add`, `holiday_type=category`,
  `employee_id` leer, `category_id` = "IT-Kommunal GmbH", Urlaubsart
  "gesetzlicher Jahresurlaub ", 25 Tage, Status genehmigt, ohne Datum,
  angelegt am 27.08.2019.
- Kategorie-Mitglieder laut `hr.employee.category_ids`: 10 Mitarbeiter
  (IDs 4, 13, 14, 17, 18, 19, 22, 23, 27, 29).
- **Nachweis, dass daraus KEIN persoenlicher Anspruch wurde:**
  `hr.holidays.status.get_days` liefert fuer den angemeldeten Benutzer
  (Maierhofer Anna, Mitglied der Kategorie) `max_leaves = 0`;
  die 25 Tage erscheinen dort nicht als Anspruch.
- Die fuenf nicht migrierbaren Antraege sind **nicht** durch diesen Anspruch gedeckt:
  sie betreffen die Arten "Augleichstage" und "Krankheitsstaende", nicht
  "gesetzlicher Jahresurlaub"; zwei der Betroffenen (Breiteneder Lorenz, Mohammad Fahad)
  sind nicht einmal Mitglied der Kategorie.
- Folge: **keine** persoenlichen Ansprueche aus ID 7 abgeleitet (nichts geraten).
  Der Datensatz bleibt als Ausnahme dokumentiert (Odoo 18 kennt keine
  Kategorie-Ansprueche).

## 5. Bewusste Abweichungen gegenueber Odoo 11

| Punkt | Odoo 11 | Odoo 18 nach Migration | Grund |
|---|---|---|---|
| Resturlaub-Guthaben | fuer alle Arten gerechnet | nur bei Arten mit Anspruchspflicht (4 von 25) | Odoo 18 zeigt ein Guthaben nur bei `requires_allocation=yes`; fuer die Arten mit ungedeckten Altantraegen ist die Pflicht aus (Datenlage) |
| Kategorie-Anspruch | 25 Tage fuer eine Mitarbeiter-Kategorie | nicht uebertragbar | Odoo 18 kennt nur persoenliche Ansprueche |
| 0-Tage-Ansprueche | 2 Datensaetze | nicht uebertragbar | SQL-Constraint `hr_leave_allocation`: Dauer > 0 |
| Private Felder | fuer alle internen Benutzer sichtbar | Feldrechte `hr.group_hr_user` | Odoo 18 gated diese Felder auf Feldebene; Freigabe der HR-Gruppe wuerde Schreibrechte geben |
| Urlaubsarten | 28 Eintraege, davon 5 Namen mehrfach | 20 Namen | Leerzeichen-Varianten zusammengefuehrt |
| Arbeitszeitmodelle | 9 | 8 | zwei Modelle mit identischem Namen und identischen Zeiten |

## 6. Pruefungen

- `scripts/verify_personal.py --instanz lokal|vm`: Modulstand, Menues, Formularaufbau,
  Labels, Filter/Domains, Rechte, Zaehlungen, Feldvergleich ALLER Mitarbeiter gegen Odoo 11,
  Manager-Zuordnung, Beziehungen, Sonderfaelle, Sprache. Lokal: **54 OK / 0 FEHL**.
- `scripts/browser_personal_abnahme.py lokal|vm` (echter Chrome): **22 OK / 0 FEHL** lokal.
- Regression der bereits fertigen Bereiche: `scripts/abschluss_verkauf_regression.py`.
