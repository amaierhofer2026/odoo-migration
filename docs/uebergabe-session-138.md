# Uebergabe Session 138 -> 139

Stand: 30.10.2026. Diese Datei ist der Einstieg fuer die naechste Session.

## 1. Ergebnis dieser Session

**Bereich EVENTS: ABGENOMMEN und GESPERRT** (30.10.2026).

- Odoo 11 live erhoben (read-only): 122 Veranstaltungen (121 aktiv, 1 archiviert),
  760 Teilnehmer, 2 Anlasskategorien, 170 Mailplaner, 758 Teilnehmer-Mailprotokolle,
  0 Fragen, 2.969 Nachrichten, 6 Teilnehmerausweis-PDFs, 29 referenzierte Kontakte.
- Kernbefund: der Bereich war in Odoo 18 **ueberhaupt nicht** installiert.
- Installiert: `event` 18.0.1.9, `website_event` 18.0.1.4 (lokal und VM).
- Neues Modul `itk_events_compat` 18.0.1.0.3: Menues im Odoo-11-Wortlaut, Statusphasen
  Nicht bestaetigt / Bestaetigt / Angekuendigt / Erledigt / Abgebrochen, Felder
  `x_is_online`, `x_seats_min`, `x_o11_id`, `x_o11_state`, `x_o11_registrations`,
  `x_o11_organizer_id`, `x_o11_address_id`, Listen-/Such-/Pivot-/Graph-Ansichten.
- Migriert (nur nicht personenbezogene Daten): 2 Kategorien, 122 Veranstaltungen,
  170 Mailplaner (alle `mail_done = True`), 760 Anmeldungen nur als Zaehlwert
  `x_o11_registrations`.
- **Keine Kontakte, Personen, Teilnehmer oder E-Mail-Adressen** angelegt oder uebernommen.
  Veranstalter und Ort bleiben leer; die Odoo-11-Kontakt-IDs stehen in den Referenzfeldern.
- Kein Mailversand moeglich: Cron "Event: Mail Scheduler" `active = False`, alle Planer
  `mail_done = True`, 0 Teilnehmer, keine `event.mail.registration`-Zeile,
  Odoo-18-Standardplaner an uebernommenen Veranstaltungen entfernt.

Pruefzahlen (lokal **und** VM):

| Pruefung | Ergebnis |
|---|---|
| `verify_s138_events.py` | 61 OK / 0 FEHLER |
| `browser_events_abnahme.py` (Chrome) | 35 OK / 0 FEHLER |
| `events_labels_de.py` | 0 offen |
| Rechteprobe (`events_rechte.py --pruefen`) | bestanden (Benutzer: lesen/anlegen/bearbeiten, kein Loeschen; Manager: alles) |
| `verify_personal.py` | 54 OK / 0 FEHL |
| `verify_s135_projekt.py` | 20 OK / 0 FEHLER |
| `abschluss_verkauf_regression.py` | 881 OK / 0 FEHL (11 Prueflaeufe) |

## 2. Entscheidungen von Anna

1. **Datenmigration ohne Personenbezug.** Kontakte, Unternehmen, Personen, Ansprechpartner,
   Teilnehmer und E-Mail-Adressen werden NICHT mit Events migriert; das kommt als eigener
   Bereich Kontakte/Personen. Keine `res.partner`-Datensaetze anlegen, keine bestehenden
   Kontakte ueber Name/E-Mail zusammenfuehren.
2. **Odoo-18-Rechte bleiben** (30.10.2026): kein Rueckbau auf die engeren Odoo-11-Rechte.
   Soll-Stand: Event-Benutzer lesen/anlegen/bearbeiten, kein Loeschen; Loeschen und
   administrative Funktionen nur Manager.
3. Odoo-18-Zusatzfunktionen bleiben erhalten, solange sie Odoo-11-Funktionen und -Daten
   nicht beeintraechtigen.

## 3. Werkzeuge dieses Bereichs

| Datei | Zweck |
|---|---|
| `scripts/events_migration.py` | Datenmigration (Trockenlauf Standard, `--ausfuehren --ich-habe-freigabe`) |
| `scripts/events_labels_de.py` | de_DE-Slots der Menues, Phasen und Filter (`--setzen`) |
| `scripts/events_rechte.py` | Odoo-11-Gruppen abbilden (`--setzen`), Rechteprobe (`--pruefen`) |
| `scripts/events_cron_schalten.py` | Mail-Cron ein-/ausschalten (derzeit aus) |
| `scripts/verify_s138_events.py` | Abnahme Struktur und Daten |
| `scripts/browser_events_abnahme.py` | Browserabnahme (Chrome) |

Protokolle: `%LOCALAPPDATA%\Temp\events_migration\`, Screenshots
`%LOCALAPPDATA%\Temp\events_abnahme\`.

Nachverknuepfung fuer die spaetere Kontaktmigration:
`docs/o11-o18-events-nachverknuepfung-lokal.csv` und `-vm.csv`
(je 1.126 Zeilen: Veranstaltungen, Veranstalter, Orte, Teilnehmer - nur Kennungen und
fachliche Schluessel, keine Namen, keine E-Mail-Adressen).

## 4. Harte Lehren aus diesem Bereich

1. Odoo 18 setzt `organizer_id` und `address_id` per Default auf den Firmenkontakt. Ohne
   ausdrueckliches `False` entsteht eine nicht belegte Beziehung.
2. Der Autovacuum-Lauf ruft `_gc_mark_events_done` und schiebt jede abgelaufene
   Veranstaltung in die Endphase - das hatte 100 uebernommene Status ueberschrieben.
   Im ITK-Modul so erweitert, dass Datensaetze mit `x_o11_id` unangetastet bleiben;
   Gegenprobe: ein vollstaendiger Autovacuum-Lauf laesst 100/15/7 unveraendert.
3. Ein Write auf `event_type_id` loest die Neuberechnung der Mailplaner aus (Odoo-18-
   Standardplaner entstehen neu) - unveraenderte Kategorie nicht schreiben.
4. Pivot/Graph brauchen gespeicherte Masszahlen: `seats_reserved`/`seats_taken` sind in
   Odoo 18 `store=False` und lassen den Pivot abstuerzen (`Hoppla`).
5. Das Anlegen von Testbenutzern erzeugt automatisch Kontakte; die Rechteprobe raeumt sie
   mit auf, sonst schlaegt "kein Kontaktzuwachs" an.
6. Uebersetzbare Datenfelder: ein Wert "Physical Event" erscheint auf Deutsch als
   "Physisches Event" (Uebersetzung greift auf den gespeicherten Wert).

## 5. Offene Punkte ausserhalb von Events

| Punkt | Bereich |
|---|---|
| Kontakt-/Teilnehmermigration, danach Nachverknuepfung der 122 Veranstalter/Orte und 760 Teilnehmer | Kontakte/Personen |
| Mailversand fuer Events wieder einschalten (`events_cron_schalten.py --aktiv`), wenn Teilnehmer vorhanden sind | Events-Nachzug |
| Odoo 11 waechst weiter (Anwesenheiten 197 vs. 196, Zeile 12691 neu; Zeiterfassung +33,8 h) - Nachzug mit den idempotenten Werkzeugen vor Produktivstart | Personal/Zeiterfassung |
| Bereiche offen: Kontakte/Kundenverwaltung, CRM, Abrechnung (migrationsbereit), E-Mail-Marketing (Start Session 139) | naechste Sessions |

## 6. Git-Stand

Der konkrete Stand ist immer `git log -1` (eine Doku-Datei kann ihren eigenen Commit nicht
enthalten). Diese Session hat gearbeitet mit:

- Branch `s138-events`, zwei Commits (Doku, Modul und Werkzeuge), PR **#244**, Merge nach
  `main`, danach ein Doku-/CSV-Nachzug auf `main`.
- Dreistand-Nachweis am Sitzungsende: lokal `HEAD` = GitHub `main` = VM `/opt/odoo18` `HEAD`,
  Baum-Hash lokal = VM, `git status --porcelain` auf allen drei Seiten leer.

## 7. Start der naechsten Session

```
cd C:\Odoo-Test
git status --short --branch && git log --oneline -3
python "$LOCALAPPDATA/Temp/vm_exec.py" "cd /opt/odoo18 && git log --oneline -1; git status --porcelain | wc -l"
```

Schnelle Regression vor dem ersten Eingriff (jeweils `--instanz lokal` und `vm`):

```
python scripts/verify_s138_events.py --instanz lokal
python scripts/verify_personal.py --instanz lokal
python scripts/verify_s135_projekt.py --instanz lokal
python scripts/abschluss_verkauf_regression.py
```

Naechster Bereich: **E-MAIL-MARKETING** (Odoo 11: `mass_mailing` 11.0.2.0,
`website_mass_mailing`, `mass_mailing_event` installiert; Odoo 18: `mass_mailing` 18.0.2.7
und `mass_mailing_themes` installiert). Gleiches Verfahren: read-only Bestand, Vergleich,
Entscheidungspunkte, dann Aufbau und Migration ohne Kontakte/Personen/E-Mail-Adressen,
kein historischer Versand.
