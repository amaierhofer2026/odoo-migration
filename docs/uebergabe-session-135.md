# Uebergabe Session 135 -> 136

Stand: 23.10.2026. Diese Datei ist der Einstieg fuer die naechste Session.

## 1. Ergebnis dieser Session

**Modul PROJEKT: abgeschlossen** (strukturell, fachlich und Datenmigration, lokal und VM).

- Odoo 11 live erhoben: 33 Projekte (28 aktiv, 5 archiviert), 715 Aufgaben
  (605 aktiv, 110 archiviert, 5 ohne Projekt), 87 Stufen, 13 Stichwoerter.
- Nach Odoo 18 migriert: 33 Projekte, 715 Aufgaben, 87 Stufen, 13 Stichwoerter,
  10 inaktive Benutzerkonten (fuer historische Bearbeiter).
- Endstand Odoo 18 lokal und VM: **38 Projekte** (33 aktiv), **723 Aufgaben**,
  **103 Stufen**, **13 Stichwoerter**, **28 Benutzer**.
- Rechte: Projekt/Benutzer 13, Projekt/Manager 12 (Odoo-11-Kreis).
- Pruefungen: `verify_s135_projekt.py` lokal 20/0 und VM 20/0; Browser S133-Abnahme
  26/0; Browser auf migrierten Daten bestanden (Projektformular mit Kostenrechnung,
  Aufgabe mit Startdatum/Bearbeiter/Stufe, Projektliste 1-32/32);
  Regression Verkauf 881/0, Personal 54/0.

**Modul ZEITERFASSUNG: strukturell/funktional fertig, Datenmigration GESPERRT.**

- Modul `itk_timesheet` 18.0.1.0.3: Spalten "Zeit (Stunden)"/Summe "Gesamtdauer",
  Beschreibung Pflicht, Datum im Formular sichtbar, Startzeit/Endzeit deutsch und
  optional; Suche mit Odoo-11-Wortlauten + Filter "Dieser Monat"; Menues
  "Meine Stundenzettel"/"Nach Abrechnungsrate"/"Anwesenheit"; Bericht
  "Kosten und Erloese"; Favorit "Abrechnungsrate".
- Rechte: 607 (nur eigene) 13 Benutzer, 608 (alle) 12 Benutzer.
- Pruefungen: `verify_s135_zeiterfassung.py` lokal 50/0, VM 50/0; Browser lokal und VM.
- Migration vorbereitet in `scripts/zeiterfassung_migration.py`, Schreibsperre ueber
  `--projekt-abgeschlossen`.

## 2. Naechster Schritt: Zeiterfassungsdaten migrieren

Reihenfolge und Bedingungen:

1. **Odoo-11-Bestand neu erheben** (Produktion wird weiter benutzt; waehrend S135
   stieg der Aufgabenbestand von 714 auf 715, Zeilen 12.885 -> 12.886).
2. **4 mehrdeutige Abwesenheitszeilen klaeren** (Odoo-11-Abwesenheit 147 hat zwei
   Treffer in Odoo 18) - vor dem Schreiblauf.
3. Trockenlauf `python scripts/zeiterfassung_migration.py --instanz lokal`, Zahlen
   pruefen, dann `--ausfuehren --ich-habe-freigabe --projekt-abgeschlossen`.
4. Danach: Kontrollen (Zeilen, Stunden, Verteilung je Mitarbeiter/Projekt/Jahr),
   Browser lokal und VM, Regression, Doku, PR, Dreistand.

Bereits festgelegte Regeln (Anna, S135):

- 282 Zeilen ohne Projekt -> Sammelprojekt "Ohne Projekt (Uebernahme Odoo 11)".
- Archivierte Mitarbeiter (1.605 Zeilen) fuer den Import kurz aktivieren, danach
  wieder archivieren (Odoo 18 verweigert Zeilen fuer archivierte Mitarbeiter).
- Startzeit historischer Zeilen: 00:00 des Odoo-11-Datums.
- 308 Zeilen mit altem Support-Ticket: **keine** Helpdesk-Tickets anlegen;
  Ticketnummer als `ref` = "O11-Ticket <Nummer>".
- `non_billable_project` -> `non_billable`.
- Alle Odoo-18-Zusaetze bleiben (Start/Stopp, Kanban/Graph/Pivot, Reportmodell).

## 3. Harte Lehren aus dieser Session

1. **Menue-/Aktionsnamen**: Quelle + de_DE + en_US schreiben, sonst ueberdeckt die
   alte de_DE-Uebersetzung die neue Quelle. Laeuft ueber `setup_runtime` im
   `post_init_hook` und in `migrations/<version>/post-migration.py`.
2. **Manifest-Versionsbump allein wirkt nicht**: `docker restart odoo18` +
   `--update-list` + Upgrade. Eine Post-Migration laeuft nur bei echtem
   Versionssprung.
3. **Harte Datenbank-IDs sind zwischen lokal und VM nicht stabil** (Menue 947 war auf
   der VM ein anderes Menue). Immer XML-IDs aufloesen.
4. **`create` mit `active=False` ist verboten** - bei `res.users` und `hr.employee`
   aktiv anlegen und sofort archivieren.
5. **Odoo 11 `date_start` ist Datetime**: `str(wert)[:10] + " 00:00:00"`, sonst
   `InvalidDatetimeFormat`.
6. **Projektzuordnung im Migrationsskript erst nach dem Anlegen der Projekte bauen**
   (sonst entstehen Aufgaben ohne Projekt). Reparatur ohne Loeschen:
   `scripts/projekt_reparatur.py` (Name + Startdatum, bei Mehrdeutigkeit Stufe).
7. **`partner_id` nur setzen, wenn der Partner in Odoo 18 existiert** (sonst
   FK-Verletzung `project_task_partner_id_fkey`).
8. **Login und Benutzername matchen**: Breiteneder Lorenz heisst in Odoo 11
   `lorenz.galler@...` - reiner Login-Vergleich uebersieht den Hauptzeiterfasser.
9. Feldnamen Odoo 18: `account_id` (nicht `analytic_account_id`), `user_ids`,
   `allocated_hours`, kein `kanban_state`, `project.task.type.project_ids`,
   `res.groups` ohne `xml_id`.
10. Browser: `thead th` liefert in Kanban-Ansichten nichts; Liste ueber
    `/odoo/project?view_type=list` erzwingen.

## 4. Werkzeuge aus dieser Session

| Datei | Zweck |
|---|---|
| `scripts/projekt_migration.py` | Projekt-/Aufgabenmigration (Trockenlauf Standard) |
| `scripts/projekt_reparatur.py` | Aufgaben ohne Projekt nachziehen (write, kein Loeschen) |
| `scripts/projekt_rechte.py` | Projektgruppen nach Odoo-11-Konzept |
| `scripts/verify_s135_projekt.py` | Projekt-Abnahme (XML-IDs, Datenbestand, Rechte) |
| `scripts/browser_projekt_daten.py` | Browserpruefung der migrierten Projektdaten |
| `scripts/erhebe_zeiterfassung.py` | read-only Bestandsaufnahme Zeiterfassung (Teile 1-7) |
| `scripts/zeiterfassung_migration.py` | Zeiterfassungsmigration (gesperrt bis `--projekt-abgeschlossen`) |
| `scripts/zeiterfassung_rechte.py` | Gruppen 607/608 |
| `scripts/verify_s135_zeiterfassung.py` | Zeiterfassungs-Abnahme |
| `scripts/browser_zeiterfassung_abnahme.py` | Browserpruefung Zeiterfassung |

Dokumente: `docs/o11-o18-projekt-vergleich.md`, `docs/o11-o18-projekt-abnahme.md`
(mit Abschnitt 6 = Session 135), `docs/o11-o18-zeiterfassung-vergleich.md`
(5-Spalten-Zuordnung), `docs/o11-o18-zeiterfassung-abnahme.md`.

## 5. Offene Punkte

1. Zeiterfassungsmigration (siehe Abschnitt 2) - gesperrt bis zur Freigabe.
2. 4 mehrdeutige Abwesenheitszeilen (O11-Abwesenheit 147).
3. Zwei Projektkunden fehlen in Odoo 18 ("[70101] Statutarstadt Innsbruck",
   "[WLV-Voeslau] Wasserleitungsverband ...") - Kundenmigration offen.
4. 5 projektlose Odoo-11-Aufgaben sind private Aufgaben (nur Ersteller sieht sie).
5. 19 Zeiterfassungs-Testzeilen und 3 offene Timer aus frueheren Sitzungen bleiben
   als fremder Bestand stehen (nicht loeschen).
6. Favorit 131 (Support-Ticket-Bericht) bewusst nicht uebernommen (in Odoo 11 schon
   ohne Treffer).

## 6. Git-Stand

main = lokal = GitHub = VM, Arbeitsbaeume sauber (Stand siehe Historie; letzter
Merge dieser Session: PR #233 Projekt-Datenmigration). Kein Force-Push, keine
Rohdaten/Credentials im Repo; Protokolle liegen unter
`%LOCALAPPDATA%\Temp\projekt_migration\` und `\zeiterfassung_migration\`.
