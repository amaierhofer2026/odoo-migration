# Uebergabe Session 134 -> 135 (Bereich Personal abgeschlossen)

Stand 21.10.2026. Diese Datei ist der Einstieg fuer die naechste Session.

## 1. Was in Session 134 erledigt wurde

Bereich **Personal** ist umgesetzt, migriert und abgenommen (Browserabnahme lokal und VM).

- Modul `addons/itk_hr` 18.0.1.0.1 (nur Ansichten/Rechte): Gruppen "Kontaktinformationen"
  und "Position", Feld `notes` als "Weitere Informationen", Wortlaut Position/Ausbilder/
  Arbeitsstelle, Gruppierung "Ausbilder", Listentitel und Menues "Personal", Leserecht
  interne Benutzer auf `hr.employee`/`hr.job`, Menue "Abteilungen" nur Personalsachbearbeiter.
- Datenmigration: 25 Mitarbeiter (13 aktiv), 8 Arbeitszeitmodelle mit Odoo-11-Zeiten,
  2 Arbeitsorte, 25 Urlaubsarten, 65 Urlaubsansprueche, 482 Urlaubsantraege (von 482),
  192 Anwesenheiten. Keine Zeiterfassung (Projektbereich).
- Belege: `verify_personal.py` 54/0, `browser_personal_abnahme_voll.py` 70/0,
  Regression Verkauf/Abrechnung 881/0 - jeweils lokal und VM.
- Dreistand zum Abschluss: main = lokal = GitHub = VM = `e5d0bbd` (PR #227, #228, #229).

Dokumente:

- `docs/o11-o18-strukturvergleich-personal.md` (read-only Bestandsaufnahme O11 gegen O18)
- `docs/o11-o18-personal-migration.md` (Umsetzung, Sonderfaelle, Abweichungen)
- `docs/o11-o18-personal-abnahme.md` (Browserabnahme, Berechtigungsprobe, O11-Drift)

## 2. Wichtige Lehren aus dieser Session

1. **Odoo 11 ist Produktion und wird waehrend des Projekts weiter bearbeitet.** Am 21.10.2026
   wurden um 12:30/12:31 zwei Mitarbeiter und eine Stelle durch den Benutzer geaendert; die
   Migration ist ein Schnappschuss. Vor jedem Abnahmebericht: `verify_personal.py` erneut
   laufen lassen, Abweichungen als Drift benennen und Odoo 18 mit dem idempotenten Lauf
   nachziehen (`hr_migration.py --ausfuehren --ich-habe-freigabe [--ohne-belegdaten]`).
2. **Odoo 18 legt neue Arbeitszeitmodelle mit 40h-Standardzeiten an** - Zeiten immer explizit
   ersetzen, sonst stimmen Teilzeitmodelle nicht.
3. **Gating datengetrieben setzen:** `requires_allocation` nur "yes", wenn in Odoo 11 jeder
   Antrag der Art durch einen persoenlichen Anspruch gedeckt war (Odoo 11 fuehrt `limit`
   nur als Hinweis). Sonst blockiert Odoo 18 Altantraege hart.
4. **Ueberschneidungen:** fuer historische Daten `context={'leave_skip_date_check': True}`
   nur im Anlage-Aufruf (Quelle `hr_holidays/models/hr_leave.py:572`); nie global abschalten.
5. **0-Tage:** `hr.leave` erlaubt 0 Tage, `hr.leave.allocation` nicht (SQL-Constraint).
6. **Odoo 18 kennt keinen Entwurf** bei Abwesenheiten: `confirm` ist Ausgangs- und einziger
   loeschbarer Zustand (wichtig fuer Aufraeumen mit `hr_migration_cleanup.py`).
7. **Browserabnahme-Praxis:** Odoo 18 zeigt Filter/Gruppierungen nur im Such-Dropdown;
   Listen sind auf 80 Zeilen paginiert (Gesamtzahl aus dem Pager lesen); Werte in Reitern
   sind erst nach dem Reiterwechsel im DOM; `hr.employee.name` ist berechnet (nicht per
   `ilike` suchen).
8. **Berechtigungen pruefen** mit temporaerem internem Benutzer (nur `base.group_user`),
   im selben Lauf loeschen und Benutzerzahl vorher/nachher belegen.

## 3. Naechster Schritt: naechstes Modul waehlen

Kandidaten (noch nicht bearbeitet, Zahlen aus der Erhebung):

| Bereich | Odoo-11-Bestand | Besonderheit |
|---|---|---|
| Zeiterfassung | 12.854 Zeiterfassungszeilen mit Mitarbeiterbezug | haengt an Projekten/Aufgaben/Leistungsarten; ersetzt `hr_timesheet`-Anteil, den Personal bewusst nicht migriert hat |
| Kontakte/Partner (Datenmigration) | 5.848 aktive Partner (2.380 Firmen, 3.461 Personen) | Struktur ist fertig; jetzt Daten, Adresstypen, Ansprechpartner |
| Produkte/Produktstammdaten | 653 Vorlagen | Feldebene vertiefen, Produktart, Steuern, Kategorien |
| Preislisten/Regeln | siehe Abrechnung | Regeln und Zuweisungen |
| CRM/Partner-Gegenpruefung | - | Gegenprobe der bereits migrierten Kontakte |

Vorgehen wie bisher: read-only Erhebung Odoo 11 -> Vergleichsdokument mit 5-Spalten-Mapping
-> Rueckmeldung der Entscheidungspunkte -> Umsetzung -> Browser lokal und VM -> Regression
-> Doku -> PR -> Merge -> VM-Nachzug -> Dreistand.

## 4. Arbeitsregeln (unveraendert)

- Odoo 11 ausschliesslich lesend.
- Keine Datenmigration ohne ausdrueckliche Freigabe; Schreiblaeufe nur mit
  `--ausfuehren --ich-habe-freigabe`, Protokoll ausserhalb des Repos.
- Abnahme nur mit echtem Browserbild, lokal und VM; VM ist die Abnahmeumgebung.
- Personal wird nicht mehr angefasst (abgeschlossen).
