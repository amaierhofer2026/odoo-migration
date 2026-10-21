# Uebergabe Session 134 -> 135 - Bereich Personal (Odoo 11 -> Odoo 18)

Stand 21.10.2026. Einstieg fuer die naechste Session.

## 1. Ergebnis

Personal ist umgesetzt und migriert. Modul `itk_hr` 18.0.1.0.1, Datenbestand:
25 Mitarbeiter (13 aktiv), 8 Arbeitszeitmodelle, 2 Arbeitsorte, 25 Urlaubsarten,
65 Urlaubsansprueche, 482 Urlaubsantraege, 192 Anwesenheiten - lokal und VM.

## 2. Dokumente

- `docs/o11-o18-strukturvergleich-personal.md` - read-only Bestandsaufnahme Odoo 11 gegen
  Odoo 18 (Menues, Reiter, Feldmapping mit 5 Spalten, Filter, Rechte, Beziehungen, Blocker).
- `docs/o11-o18-personal-migration.md` - Umsetzung, Datenmigration, Sonderfaelle,
  Kategorie-Anspruch-Nachweis, bewusste Abweichungen, Pruefungen.

## 3. Werkzeuge

`scripts/hr_sofortbefund.py`, `hr_menuebaum.py`, `hr_erhebe_o11.py`, `hr_erhebe_o18.py`,
`hr_feldbelegung_o11.py`, `hr_detail_o11.py`, `hr_detail_o18.py`,
`hr_gerenderte_ansicht.py`, `hr_rechte.py`, `hr_aktionen.py`, `hr_xmlids.py`,
`hr_mitarbeiter_vergleich.py`, `hr_vergleichsbericht.py` (erzeugt das Vergleichsdokument),
`hr_migration.py` (Trockenlauf/Schreiblauf), `hr_migration_cleanup.py` (nur eigene
Migrationsdaten), `hr_labels_de.py` (de_DE-Slots + Sprachpruefung),
`verify_personal.py`, `browser_personal_abnahme.py`.

## 4. Fallen dieser Session

- Odoo 18 legt neue `resource.calendar` mit 40h-Standardzeiten an -> Zeiten muessen
  explizit ersetzt werden, sonst stimmen Teilzeitmodelle nicht.
- `hr.leave.allocation` hat einen SQL-Constraint "Dauer > 0"; 0-Tage-Ansprueche sind nicht
  speicherbar (anders als 0-Tage-Antraege in `hr.leave`).
- Odoo 18 kennt keinen Entwurf fuer Abwesenheiten: `confirm` ist der Ausgangszustand und
  der einzige loeschbare Zustand (wichtig fuer Aufraeumen).
- `requires_allocation` laesst sich nicht mehr aendern, sobald Urlaube der Art existieren.
- `hr.employee.name` ist berechnet; Suche per `name ilike` ueber RPC ist unzuverlaessig ->
  ueber Arbeits-E-Mail oder Datum suchen.
- Der Mandanten-Kalender heisst in Odoo 11 "Standard 40 Hours/Week" (Odoo 18 schrieb
  "Standard 40 hours/week") - Namensangleich im Migrationsskript.
