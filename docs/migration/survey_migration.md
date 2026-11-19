# Umfragen / Survey: Migrationsskript

## Zweck

Überträgt die fachlichen Umfrage-Daten aus Odoo 11 Prod (`ITK_V1_a`) nach Odoo 18.
Read-only gegen die Quelle, schreibend nur gegen das Ziel und nur mit ausdrücklicher
Freigabe. Teil des ITK-Migrationsprojekts, ausgeführt unter Freigabe von Anna Maierhofer
(Session 146, 18.11.2026).

| Datei | Aufgabe |
|---|---|
| `scripts/migration/survey_migration.py` | Migration der Umfragen, Seiten, Fragen, Vorgaben, Teilnahmen und Antworten |
| `scripts/migration/survey_abgleich.py` | Read-only Abgleich Odoo 11 gegen Odoo 18 (Mengen, Beziehungen, Status, Punkte, Datumsfelder, Antwortinhalte über Prüfsumme) |
| `scripts/migration/survey_rechte_pruefung.py` | Rechteprüfung mit drei temporären Rollen |
| `scripts/browser_survey_abnahme.py` | Browserabnahme im echten Chrome (Playwright) |

## Voraussetzungen

- `.env` im Repo-Wurzelverzeichnis mit `ODOO11_USER`, `ODOO11_PWD` (Produktion, nur lesend),
  `ODOO18_DB`, `ODOO18_USER`, `ODOO18_PWD`, optional `ODOO18_URL`.
- Zielmodul `itk_migration_keys` **18.0.1.2.1 oder höher** – es stellt das Feld
  `itk_o11_id` auf `survey.survey`, `survey.question`, `survey.question.answer`,
  `survey.user_input` und `survey.user_input.line` sowie den Zeitstempel-Importweg
  für diese Modelle bereit.
- Modul `survey` (Odoo 18.0.3.7) muss installiert sein – es ist auf lokal und VM installiert.

## Trockenlauf (Standard, schreibt nichts)

```
python scripts/migration/survey_migration.py --instanz lokal
python scripts/migration/survey_migration.py --instanz vm
```

Der Trockenlauf liest Odoo 11 vollständig, plant die Ziel-Datensätze und meldet
„würde anlegen“, „nicht zuordenbar“ und alle Sonderfälle. Ein Schreibschutz-Wrapper
bricht jeden Schreibaufruf ab, falls doch einer versucht wird.

## Produktiver Lauf

```
python scripts/migration/survey_migration.py --instanz lokal --ausfuehren --ich-habe-freigabe
python scripts/migration/survey_migration.py --instanz vm    --ausfuehren --ich-habe-freigabe
```

Ohne `--ich-habe-freigabe` bricht das Skript mit Rückgabewert 2 ab.
`--mapping <pfad>` schreibt einen Mapping-Export (Odoo-11-ID → Odoo-18-ID) außerhalb des
Repos; `--grenze N` begrenzt die Zahl der Teilnahmen für Tests.

## Reihenfolge und Zuordnung

1. Umfragen (`survey.survey`)
2. Seiten (`survey.page` → `survey.question` mit `is_page=True`)
3. Fragen (`survey.question`, Fragetyp `textbox` → `text_box`)
4. Antwortvorgaben (`survey.label` → `survey.question.answer`)
5. Teilnahmen (`survey.user_input`, `token` → `access_token`, `date_create` → `start_datetime`)
6. Antworten (`survey.user_input_line`, `value_text` → `value_text_box`)
7. Zeitstempel (Erstellungs-/Bearbeitungsdatum, Ersteller) über `itk.migration.zeitstempel`

Die vollständige Feldtabelle steht in `docs/o11-o18-vergleich-survey.md`.

## Idempotenz

Anker ist `itk_o11_id` je Modell. Ein zweiter Lauf erkennt jeden bereits migrierten Satz
wieder, vergleicht die Zielwerte (Relationsfelder auf die ID reduziert, weil `read()` sie
als `[id, name]` liefert) und meldet „übersprungen“ oder „aktualisiert“.
Der Zielbestand wird immer mit `active_test=False` gelesen, damit archivierte Sätze nicht
bei jedem Lauf neu entstehen.

**Seiten und Fragen teilen sich in Odoo 11 denselben ID-Raum** (Seite 1 und Frage 1).
Die Zuordnung führt deshalb zwei Namensräume (`page`, `question`) und unterscheidet über
`is_page`. Aus demselben Grund schreibt der Zeitstempel-Import über die Ziel-ID
(`spalte="id"`), nicht über den Odoo-11-Anker.

## Bekannte Sonderfälle

| Fall | Behandlung |
|---|---|
| Odoo-11-Stufe „Geschlossen“ | Umfrage wird archiviert (`active=False`); alle anderen Stufen bleiben aktiv |
| Teilnahme ohne Antwortzeile (angefangen, nicht beantwortet) | wird übernommen, `state='new'`, kein `end_datetime` |
| `end_datetime` | Odoo 11 führt kein Abschlussdatum – gesetzt wird der Zeitpunkt der letzten Antwort |
| `user_input.type` (`manually`) | in Odoo 18 nicht vorhanden, wird nicht übertragen |
| `quizz_score`, `tot_*`, `public_url` | in Odoo 18 berechnet, wird nicht geschrieben |
| `survey.mail.compose.message` | 0 Datensätze, Funktion nicht mehr benötigt |

## Produktfehler in Odoo 18.0.3.7 (nicht durch die Migration verursacht)

`survey.question.create` ist im Modul `survey` **ohne** `@api.model_create_multi`
definiert. Ein JSON-RPC-Aufruf `create` scheitert deshalb mit
`TypeError: SurveyQuestion.create() missing 1 required positional argument: 'vals_list'`.
Das Skript legt Seiten und Fragen daher über die One2many `question_and_page_ids` der
Umfrage an – derselbe Weg, den die Umfrage-Maske und der Dialog „Abschnitte und Fragen
erstellen“ verwenden. In der Oberfläche ist das Anlegen damit möglich (im Browser belegt),
nur der direkte Modellaufruf über RPC ist betroffen.

## Validierung nach der Migration

```
python scripts/migration/survey_abgleich.py --instanz lokal
python scripts/migration/survey_rechte_pruefung.py --instanz lokal
python scripts/browser_survey_abnahme.py --instanz lokal
```

Der Abgleich vergleicht Antworttexte über Länge und SHA-1-Prüfsumme, ohne Inhalte
auszugeben. Erwartet werden 0 Abweichungen.

## Datenschutz

Die Antworten enthalten Freitexte von Teilnehmern. Konsole, Mapping-Datei, Logs und
Dokumentation enthalten ausschließlich Mengen, IDs, Längen und Status – keine
Antwortinhalte, Namen oder E-Mail-Adressen. In Odoo 11 hat keine Teilnahme einen
Partner- oder E-Mail-Bezug; die Zuordnung läuft ausschließlich über technische IDs.

## Laufprotokoll

| Datum | Instanz | Commit | Ergebnis |
|---|---|---|---|
| 18.11.2026 | lokal | Stand vor Commit (Arbeitsbranch `survey-migration`) | 151 gelesen, 151 angelegt, 0 Fehler, 0 Dubletten; 2. Lauf 0/0/151 |
| 18.11.2026 | VM | derselbe Stand | siehe Abschlussbericht |
