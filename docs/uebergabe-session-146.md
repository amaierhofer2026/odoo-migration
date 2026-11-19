# Uebergabe Session 146 - Umfragen / Survey

**Status: Umfragen / Survey = MIGRIERT (lokal), VM-Abnahme offen.**
Nicht gesperrt, solange die VM nicht belegt ist.

## Auftrag dieser Sitzung

Bereich Umfragen / Survey nach dem ueblichen Verfahren: Odoo 11 read-only erheben,
Odoo 18 vergleichen, Vergleichsdokument, Datenmigration mit reproduzierbarem Skript
(Trockenlauf, Freigabeschalter, idempotent), Browserabnahme, Rechtepruefung, Regression,
Dokumentation, Branch/Push/PR/Merge, VM nachziehen.

## Was fertig und belegt ist (lokal)

**Bestand Odoo 11 (frisch gemessen 18.11.2026, read-only)**
- Module: `survey` 11.0.2.0 und `survey_crm` 11.0.2.0 installiert, `hr_recruitment_survey` nicht.
- 2 Umfragen, 2 Seiten, 2 Fragen (1x simple_choice, 1x textbox), 2 Antwortvorgaben,
  72 Teilnahmen (71 abgeschlossen, 1 neu), 71 Antworten (alle Freitext).
- 4 Umfrage-Stufen, kein Partner-/E-Mail-Bezug, keine Fristen, keine Punkte.
- Odoo 11 waechst weiter: die juengste Teilnahme entstand am Tag der Messung.

**Odoo 18**
- `survey` 18.0.3.7 war bereits installiert (lokal und VM), Bestand war leer.
- Seiten sind Fragen mit `is_page=True`, Vorgaben sind `survey.question.answer`,
  `textbox` heisst `text_box`, Stufen gibt es nicht mehr.

**Struktur/Doku**
- `docs/o11-o18-vergleich-survey.md` - vollstaendiges Mapping (Modelle, Felder,
  Statuswerte, Beziehungen, Menues, Ansichten, Filter, Rechte, Datenmigration),
  akzeptierte Abweichungen, offene Entscheidungen, Ergebnisabschnitt.
- `docs/migration/survey_migration.md` - Skriptdoku (Voraussetzungen, Aufrufe,
  Reihenfolge, Idempotenz, Sonderfaelle, Datenschutz, Laufprotokoll).
- `itk_migration_keys` **18.0.1.2.1**: Anker `itk_o11_id` auf `survey.survey`,
  `survey.question`, `survey.question.answer`, `survey.user_input`,
  `survey.user_input.line`; Zeitstempel-Importweg um diese Modelle erweitert
  (optional `spalte="id"`, weil Odoo-11-Seiten und -Fragen denselben ID-Raum teilen).

**Datenmigration**
- `scripts/migration/survey_migration.py` (Trockenlauf Standard, Schreiben nur
  `--ausfuehren --ich-habe-freigabe`), `survey_abgleich.py`, `survey_rechte_pruefung.py`,
  `scripts/browser_survey_abnahme.py`.
- Lokal: 2 Umfragen, 2 Abschnitte, 2 Fragen, 2 Vorgaben, 72 Teilnahmen, 71 Antworten.
- Idempotenz: 0 angelegt, 0 aktualisiert, 151 uebersprungen, 0 Fehler, 0 Dubletten.
- Abgleich: 409 Pruefungen OK, 0 Abweichungen (Antworttexte ueber Laenge und SHA-1,
  ohne Inhalte auszugeben). Erstell-/Bearbeitungsdatum und Ersteller auf Odoo-11-Stand.
- Browser lokal: 44 OK / 0 FEHL (Liste, Kanban, Formular, Fragen, Vorgaben, Teilnahmen,
  Filter, Gruppierung, Suche, Einzelteilnahme, Ergebnisseite, oeffentliche Umfrage
  inklusive Absenden und Danke-Seite, Anlegen mit Dialog "Abschnitte und Fragen
  erstellen", Testdaten entfernt).
- Rechte lokal: 17 OK / 0 FEHL (ohne Gruppe kein Zugriff, Benutzer/Administrator voll).

## Offene Punkte

1. **VM-Nachzug**: `itk_migration_keys` 18.0.1.2.1 installieren, Migration schreiben,
   Idempotenz, Abgleich, Browser (44 Pruefungen), Rechte. Erst danach sperren.
2. **Regression der gesperrten Bereiche** lokal (laeuft) und auf der VM.
3. **Entscheidung K1 (Stufen)**: Odoo 18 hat kein Stufenmodell. Vorschlag: Odoo-18-Standard
   belassen (Geschlossen = archiviert), dokumentiert. Kein Feld nachgebaut.
4. **Entscheidung K2 (Rechte)**: In Odoo 11 sah ein normaler Umfrage-Benutzer nur eigene
   Antworten, in Odoo 18 sieht "Umfragen / Benutzer" alle (betroffen: 1 echter Benutzer).
   Nichts geaendert; drei Optionen im Vergleichsdokument (Abschnitt 5.2).
5. Nach dem VM-Beleg: Checkliste, PROJECT_KNOWLEDGE, README und diese Datei auf
   "ABGENOMMEN UND GESPERRT" setzen und den Dreistand nachweisen.

## Technische Befunde

- **Produktfehler in `survey` 18.0.3.7**: `survey.question.create` ist ohne
  `@api.model_create_multi` definiert. JSON-RPC `create` scheitert mit
  `TypeError: SurveyQuestion.create() missing 1 required positional argument: 'vals_list'`.
  Die Oberflaeche legt Fragen ueber den Dialog "Abschnitte und Fragen erstellen" an
  (im Browser belegt); das Migrationsskript nutzt denselben Weg ueber die O2M
  `question_and_page_ids`. Kein Fehler der Migration.
- **ID-Ueberlappung**: Odoo-11-Seite 1 und -Frage 1 haben dieselbe ID. Zuordnung und
  Zeitstempel-Import trennen deshalb Seiten und Fragen (`is_page`, `spalte="id"`).
- **Relationsvergleich**: `read()` liefert Many2one als `[id, name]`; ohne Reduktion auf
  die ID meldet der Idempotenzvergleich jedes Feld als Abweichung (151 falsche
  Aktualisierungen im ersten Schreiblauf).
- **Odoo-18-Bedienung im Browser**: Umfragetitel ist ein `textarea`, die oeffentliche
  Umfrage hat eine Startseite mit "Umfrage starten", der Cookie-Hinweis liegt ueber den
  Knoepfen, Fragen entstehen ueber einen Dialog. Alles im Abnahmeskript beruecksichtigt.

## Zahlen zum Nachschlagen

| Kennzahl | Odoo 11 | Odoo 18 lokal | Odoo 18 VM |
|---|---|---|---|
| Umfragen | 2 | 2 | offen |
| Seiten/Abschnitte | 2 | 2 | offen |
| Fragen | 2 | 2 | offen |
| Antwortvorgaben | 2 | 2 | offen |
| Teilnahmen | 72 (71 done, 1 new) | 72 (71 done, 1 new) | offen |
| Antworten | 71 | 71 | offen |
| davon Freitext | 71 | 71 | offen |
| Punkte gesamt | 0,00 | 0,00 | offen |

## Fuer die naechste Sitzung

Der Bereich ist nach dem VM-Nachzug zu sperren; danach **kein naechstes Modul ohne Zuruf**.
Beim Arbeiten an anderen Bereichen beachten:

- Odoo 11 ist produktiv: Zahlen immer frisch messen.
- `survey.question.create` per RPC ist defekt - Fragen ueber die O2M anlegen.
- In `itk_migration_keys` neue Anker nur additiv ergaenzen (das Modul traegt alle
  Migrationsanker); Zeitstempel-Import nur fuer Modelle aus der Whitelist.
- Browserabnahme: Cookie-Hinweis wegklicken, Ansichtswechsel ueber die Knoepfe
  (URL-Parameter `view_type` greift nicht immer), Titel-Felder koennen `textarea` sein.
