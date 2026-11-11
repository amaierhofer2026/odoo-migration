# Inventur der Migrationsskripte (Stand 12.11.2026, Session 142)

Grundlage: verbindliche Projektregel `docs/MIGRATIONSREGEL.md` (Freigabe Anna Maierhofer,
12.11.2026). Geprueft wurde, ob je Bereich ein reproduzierbares Migrationsskript im
Repository liegt: Trockenlauf als Standard, ausdruecklicher Schreibschalter, idempotent.

**Wichtig:** Diese Inventur dokumentiert nur den Ist-Zustand. Bereits ABGENOMMENE UND
GESPERRTE Module wurden NICHT veraendert.

## 1 Module mit eigenem Migrationsskript

| Bereich | Skript | Trockenlauf | Schreibschalter | Status |
|---|---|---|---|---|
| Personal | `scripts/hr_migration.py` | Standard | `--ausfuehren --ich-habe-freigabe` | abgenommen, Skript vorhanden |
| Zeiterfassung | `scripts/zeiterfassung_migration.py` | Standard | `--ausfuehren --ich-habe-freigabe` | abgenommen, Skript vorhanden |
| Anwesenheiten | `scripts/anwesenheiten_migration.py` | Standard | `--ausfuehren --ich-habe-freigabe` | abgenommen, Skript vorhanden |
| Projekt | `scripts/projekt_migration.py` | Standard | `--ausfuehren --ich-habe-freigabe` | abgenommen, Skript vorhanden |
| Events | `scripts/events_migration.py` | Standard | `--ausfuehren --ich-habe-freigabe` | abgenommen, Skript vorhanden |
| E-Mail-Marketing | `scripts/marketing_migration.py` | Standard | `--ausfuehren --ich-habe-freigabe` | abgenommen, Skript vorhanden |
| Abrechnung (Testmigration) | `scripts/testmigration_abrechnung.py` | Standard | `--ausfuehren --ich-habe-freigabe` (`--plan`, `--aufraeumen`) | in Arbeit, Skript vorhanden |
| **Website/Webinhalte** | **`scripts/migration/website_migration.py`** (Logik `scripts/migrate_website.py`) | Standard | `--ausfuehren --ich-habe-freigabe` | **abgenommen (12.11.2026)** |

Zusatzskripte ohne eigenen Bereichsbezug: `scripts/hr_migration_cleanup.py` (Aufraeumen nach
der Personal-Migration).

## 2 Module OHNE reproduzierbares Migrationsskript (offen)

Diese Bereiche sind abgenommen bzw. in Arbeit, haben aber **kein** eigenstaendiges
Migrationsskript im Sinne der neuen Regel. Nach der Regel gilt das fuer kuenftige
Aenderungen als Luecke; die Bereiche werden NICHT rueckwirkend veraendert, solange kein
neuer Auftrag vorliegt.

| Bereich | Was vorhanden ist | Was fehlt |
|---|---|---|
| Verkauf | `scripts/analyse_verkauf_*.py`, `scripts/abschluss_verkauf_*.py`, `scripts/pruefe_verkauf_migrationscheck_*.py`, `scripts/baue_verkauf_migrationsregeln.py`, Doku `docs/o11-o18-verkauf-migrationscheck.md` | ein `scripts/migration/verkauf_migration.py` mit Trockenlauf/Schreibschalter/Zusammenfassung |
| Abonnements | `scripts/abgleich_abonnements_1..5.py` (read-only Abgleich), `scripts/abo_labels_setzen.py` | ein Migrationsskript; die Abo-Daten wurden ueber die Abo-Module/Importwege uebernommen |
| Helpdesk | `scripts/verify_*helpdesk*`, Modul `itk_helpdesk_compat` | kein Datenmigrationsskript (bewusste Entscheidung: **keine** historischen Tickets) |
| Massenbearbeitung | `scripts/analyse_o11_massenbearbeitung.py`, `scripts/apply_massenbearbeitung.py --pruefen` | kein Datentransfer-Skript (die 20 Massenaktionen sind Struktur, kein Datenbestand) |
| Kontakte / CRM | `scripts/o11_o18_mapping.py`, Pruefskripte | kein abschliessendes Migrationsskript (Kontakte sind personenbezogen, eigener Auftrag noetig) |
| Umfragen (Survey) | - | noch nicht bearbeitet (Odoo 11: 2 Umfragen, 73 Teilnahmen) |
| Valorisierung, Lager/Bestand | - | noch nicht bearbeitet |

## 3 Empfehlung fuer die naechsten Sitzungen

1. Fuer **Verkauf** und **Abonnements** je ein `scripts/migration/<bereich>_migration.py`
   nach dem Muster des Website-Skripts anlegen (Freigabeschalter, Mapping-Export,
   Zusammenfassung), ohne die abgenommenen Daten zu veraendern - reiner Trockenlauf-Nachweis.
2. Bei Helpdesk und Massenbearbeitung die Ausnahme in der Bereichsdoku ausdruecklich
   festhalten ("kein Datentransfer, weil ..."), damit die Regel nicht ins Leere laeuft.
3. Neue Bereiche (Umfragen, Valorisierung, Lager) von Anfang an mit Skript unter
   `scripts/migration/` beginnen.
