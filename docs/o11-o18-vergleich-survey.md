# Umfragen / Survey: Odoo 11 zu Odoo 18

Stand: 18.11.2026 (Session 146). Read-only erhoben gegen Odoo 11 Prod `ITK_V1_a`
und gegen Odoo 18 lokal (`odoo18_test`) und VM (`https://k001959vsx.ipax.at`).
Die Zahlen sind frisch gemessen - Odoo 11 ist produktiv und waechst zwischen zwei
Messungen.

Dieses Dokument enthaelt **keine** Antwortinhalte, Namen oder E-Mail-Adressen.
Wo Inhalte relevant sind, stehen nur Mengen, Laengen und technische Kennungen.

## 1 Bestand Odoo 11 (gemessen 18.11.2026)

### 1.1 Module

| Modul | Version | Status | Aufgabe |
|---|---|---|---|
| `survey` | 11.0.2.0 | installiert | Umfragen, Fragen, Teilnahmen, Auswertung |
| `survey_crm` | 11.0.2.0 | installiert | "Umfrage senden" aus Kontakt/Interessent (`survey.mail.compose.message`) |
| `hr_recruitment_survey` | 11.0.1.0 | **nicht** installiert | Bewerbungsfragebogen |

### 1.2 Datenbestand

| Objekt | Odoo 11 | Anmerkung |
|---|---|---|
| `survey.survey` | **2** | 1 Testumfrage (Stufe "Entwurf", 1 Seite, 1 Frage ja/nein), 1 offene Umfrage (Stufe "In Bearbeitung") |
| `survey.stage` | **4** | Entwurf, In Bearbeitung, Geschlossen, Dauerhaft |
| `survey.page` | **2** | je 1 Seite pro Umfrage |
| `survey.question` | **2** | 1x `simple_choice` (Pflichtfeld), 1x `textbox` (Pflichtfeld) |
| `survey.label` | **2** | Antwortvorgaben "ja"/"nein"; keine Matrixzeilen (`question_id_2` leer) |
| `survey.user_input` | **72** | 71 `done`, 1 `new` (angefangen, keine Antwort); alle `type='manually'`, `test_entry=False` |
| `survey.user_input_line` | **71** | alle `answer_type='text'`, keine uebersprungenen Zeilen, keine Matrixzeilen |
| Partnerbezug | **0** | keine Teilnahme hat `partner_id` oder `email` |
| Termine | **0** | kein `deadline` gesetzt |
| Punkte | 0,0 | `quizz_mode=False`, `quizz_score` ueberall 0,0 |

Zeitraum der Teilnahmen: 13.04.2021 bis 18.11.2026. Die juengste Teilnahme
(ID 1624, Zustand `new`) ist am Tag dieser Messung entstanden - ein Beleg dafuer,
dass Odoo 11 live weiterbenutzt wird.

### 1.3 Felder, die tatsaechlich verwendet werden

- Umfrage: `title`, `stage_id`, `active`, `auth_required` (False), `users_can_go_back` (False),
  `quizz_mode` (False), `color` (0), `page_ids`, `question_ids`, Kennzahlen
  `tot_sent_survey` / `tot_start_survey` / `tot_comp_survey` (berechnet).
- Seite: `title`, `sequence` (0), `description` (leer), `survey_id`.
- Frage: `question`, `type`, `sequence` (0), `constr_mandatory` (True),
  `constr_error_msg` ("Diese Frage muss beantwortet werden"), `display_mode`
  ("columns"), `column_nb` (12), `matrix_subtype`, `validation_*` (Standardwerte).
- Antwortvorgabe: `value`, `sequence` (10), `quizz_mark` (0,0).
- Teilnahme: `survey_id`, `state`, `token` (36 Zeichen, eindeutig), `date_create`,
  `last_displayed_page_id`, `test_entry`.
- Antwort: `user_input_id`, `question_id`, `page_id`, `answer_type`, `value_text`,
  `skipped` (False), `quizz_mark` (0,0), `date_create`.

### 1.4 Menues, Ansichten, Rechte (Odoo 11)

| Menue | Aktion | Inhalt |
|---|---|---|
| Surveys | `survey.survey` | Umfrageliste/Kanban (Kanban gruppiert nach `stage_id`) |
| Surveys / Answers | `survey.user_input` | Teilnahmen |
| Surveys / Configuration / Pages | `survey.page` | Seiten |
| Surveys / Configuration / Questions | `survey.question` | Fragen |
| Surveys / Configuration / Labels | `survey.label` | Antwortvorgaben |
| Surveys / Configuration / User Input Lines | `survey.user_input_line` | Einzelantworten |

Das Wurzelmenue ist auf die Gruppe `survey.group_survey_user` eingeschraenkt.
Ansichten: je Modell Formular, Liste, Suche; zusaetzlich Kanban fuer Umfragen und
Teilnahmen. Keine eigenen Filter (`ir.filters` = 0), keine eigenen Berichte, keine
Cronjobs. Eine Server-Aktion "Umfrage: Testantworten entfernen" und eine
E-Mail-Vorlage "Survey - Send by Email".

Rechte Odoo 11:

| Gruppe | Mitglieder | Wirkung |
|---|---|---|
| `survey.group_survey_user` ("Survey / User") | 45 (43 aktiv) | Umfrage lesen, **nur offene** (Record Rule: `stage_id.closed = False`); Teilnahmen **nur eigene** (`create_uid = user` oder `partner_id = user.partner_id`) |
| `survey.group_survey_manager` ("Survey / Manager") | 42 | alles lesen/schreiben/loeschen, alle Teilnahmen |
| oeffentlich (keine Gruppe) | - | Umfrage/Seite/Frage/Vorgabe lesen, Teilnahme anlegen und aendern (anonymes Ausfuellen) |

## 2 Bestand Odoo 18 (gemessen 18.11.2026)

| Punkt | Wert |
|---|---|
| Modul | `survey` **18.0.3.7**, auf lokal und VM installiert |
| Datenbestand | `survey.survey` 0, `survey.question` 0, `survey.question.answer` 0, `survey.user_input` 0, `survey.user_input.line` 0 |
| Nicht installiert | `hr_recruitment_survey`, `website_slides_survey` (beide nicht benoetigt) |
| Modelle | `survey.survey`, `survey.question` (Seiten **und** Fragen), `survey.question.answer`, `survey.user_input`, `survey.user_input.line`; **kein** `survey.stage` |
| Menues | Umfragen, Teilnahmen, Fragen & Antworten (Fragen, Vorgeschlagene Werte, Detaillierte Antworten) - deutsche Standardbezeichnungen vorhanden |
| Ansichten | Umfragen: Kanban, Liste, Formular, Suche, Graph, Pivot, Aktivitaeten; Teilnahmen: Liste, Kanban, Formular, Suche; Fragen/Vorgaben/Antwortzeilen: Formular, Liste, Suche |
| Rechte | Gruppen "Umfragen / Benutzer" (599) und "Umfragen / Administrator" (600); zusaetzlich je Umfrage das Feld "eingeschraenkte Benutzer" |
| Zusatzfunktionen | Zertifizierungen, Live-Session, Bewertung, Zeitlimit, Abschnitte mit bedingten Fragen, Einladungen per E-Mail, Auswertung Graph/Pivot, Zertifikats-PDF |

## 3 Mapping: Odoo 11 | verwendet? | Odoo 18 | Status | Entscheidung

### 3.1 Modelle

| Odoo 11 | verwendet? | Odoo 18 Entsprechung | Status | Entscheidung |
|---|---|---|---|---|
| `survey.survey` | ja (2) | `survey.survey` | 1:1 vorhanden | uebernehmen, `itk_o11_id` als Anker |
| `survey.page` | ja (2) | `survey.question` mit `is_page=True` | anders modelliert | Seite wird als Abschnitt angelegt, Fragen haengen per `page_id` daran |
| `survey.question` | ja (2) | `survey.question` (`is_page=False`) | 1:1 vorhanden | uebernehmen, `question` -> `title` |
| `survey.label` | ja (2) | `survey.question.answer` | anders benannt | `value` -> `value`; `question_id_2` (Matrixzeile) -> `matrix_question_id` |
| `survey.user_input` | ja (72) | `survey.user_input` | 1:1 vorhanden | uebernehmen |
| `survey.user_input_line` | ja (71) | `survey.user_input.line` | 1:1 vorhanden | uebernehmen |
| `survey.stage` | ja (4) | **fehlt** (Modell in Odoo 18 entfernt) | fehlt | nicht nachbauen; Regel: "Geschlossen" -> archiviert, alle anderen Stufen aktiv (siehe 5.1) |
| `survey.mail.compose.message` | nein (0 Datensaetze) | entfallen | obsolet | nicht migrieren |
| `survey.mail.template` | 1 Standardvorlage | `mail.template` (Standard) | anders modelliert | nicht migrieren (keine eigenen Vorlagen vorhanden) |

### 3.2 Felder

| Odoo 11 Feld | verwendet? | Odoo 18 Feld | Status | Entscheidung |
|---|---|---|---|---|
| `survey.survey.title` | ja | `title` | 1:1 | uebernehmen |
| `description` | ja (leer) | `description` | 1:1 | uebernehmen |
| `stage_id` | ja | - | fehlt | Regel siehe 5.1 |
| `is_closed` (berechnet) | ja | - | fehlt | aus Stufe abgeleitet, siehe 5.1 |
| `active` | ja | `active` | 1:1 | uebernehmen |
| `auth_required` | ja (False) | `users_login_required` | anders benannt | uebernehmen; zusaetzlich `access_mode` = `public`/`token` |
| `users_can_go_back` | ja (False) | `users_can_go_back` | 1:1 | uebernehmen |
| `quizz_mode` | ja (False) | `scoring_type` / `certification` | anders modelliert | `False` -> `no_scoring`; `True` -> `scoring_with_answers` (in diesem Bestand nicht vorkommend) |
| `color` | ja (0) | `color` | 1:1 | uebernehmen |
| `tot_sent_survey` / `tot_start_survey` / `tot_comp_survey` | berechnet | `answer_count` / `answer_done_count` | anders modelliert | nicht schreiben, Odoo 18 rechnet selbst |
| `public_url` / `print_url` | berechnet | `access_token` + URL | anders modelliert | nicht schreiben |
| `thank_you_message` | ja (leer) | `description_done` | anders benannt | uebernehmen (leer) |
| `email_template_id` | nein (False) | - | entfallen | nicht migrieren |
| `designed` | ja (True) | - | entfallen | Odoo 18 hat keinen Editor-Zustand mehr |
| `survey.page.title` | ja | `survey.question.title` | anders modelliert | uebernehmen |
| `survey.page.sequence` / `description` | ja | `sequence` / `description` | 1:1 | uebernehmen |
| `survey.question.question` | ja | `title` | anders benannt | uebernehmen |
| `survey.question.type` | ja | `question_type` | anders benannt | `textbox` -> `text_box`, `simple_choice` -> `simple_choice` (Tabelle 3.3) |
| `sequence` | ja | `sequence` | 1:1 | uebernehmen |
| `constr_mandatory` | ja (True) | `constr_mandatory` | 1:1 | uebernehmen |
| `constr_error_msg` | ja | `constr_error_msg` | 1:1 | uebernehmen |
| `comments_allowed` / `comments_message` / `comment_count_as_answer` | ja (False) | gleichnamig | 1:1 | uebernehmen |
| `validation_required`, `validation_error_msg`, `validation_email`, `validation_length_min/max`, `validation_min/max_float_value`, `validation_min/max_date` | Standardwerte | gleichnamig | 1:1 | uebernehmen |
| `matrix_subtype` | ja (simple) | `matrix_subtype` | 1:1 | uebernehmen |
| `display_mode` / `column_nb` | ja (columns / 12) | - | entfallen | Odoo 18 stellt Auswahlfragen immer als Spalten dar |
| `survey.label.value` | ja | `survey.question.answer.value` | 1:1 | uebernehmen |
| `sequence` | ja (10) | `sequence` | 1:1 | uebernehmen |
| `quizz_mark` | ja (0,0) | `answer_score` | anders benannt | uebernehmen |
| `survey.user_input.state` | ja | `state` | 1:1, Werte anders | `new`/`done` bleiben, Odoo 18 kennt zusaetzlich `in_progress` |
| `token` | ja | `access_token` | anders benannt | uebernehmen (Antwortlinks bleiben damit gueltig) |
| `date_create` | ja | `start_datetime` | anders benannt | uebernehmen |
| `deadline` | ja (leer) | `deadline` | 1:1 | uebernehmen |
| `last_displayed_page_id` | ja | `last_displayed_page_id` (auf Frage) | 1:1, Zielmodell anders | auf die Abschnitts-Frage abbilden |
| `test_entry` | ja (False) | `test_entry` | 1:1 | uebernehmen |
| `email` / `partner_id` | ja (beide leer) | `email` / `partner_id` | 1:1 | uebernehmen (0 Faelle) |
| `quizz_score` | ja (0,0) | `scoring_total` / `scoring_percentage` (berechnet) | anders modelliert | nicht schreiben |
| `type` (`manually`) | ja | - | entfallen | nicht migrieren |
| `survey.user_input_line.value_text` | ja | `value_text_box` | anders benannt | uebernehmen (`answer_type='text'` -> `text_box`) |
| `value_free_text` | ja (leer) | `value_text_box` | anders modelliert | nur falls gefuellt (0 Faelle) |
| `value_suggested` | ja (leer) | `suggested_answer_id` | anders benannt | uebernehmen |
| `value_suggested_row` | ja (leer) | `matrix_row_id` | anders benannt | uebernehmen |
| `value_number` / `value_date` | ja (0 / leer) | `value_numerical_box` / `value_date` | 1:1 bzw. anders benannt | uebernehmen |
| `skipped` | ja (False) | `skipped` | 1:1 | uebernehmen |
| `quizz_mark` | ja (0,0) | `answer_score` | anders benannt | uebernehmen |
| `user_input_id`, `survey_id`, `question_id`, `page_id` | ja | gleichnamig (`page_id` = Abschnitt) | 1:1 | uebernehmen |

### 3.3 Fragetypen und Antworttypen

| Odoo 11 (`survey.question.type`) | Odoo 18 (`question_type`) | Status |
|---|---|---|
| `simple_choice` | `simple_choice` | 1:1 |
| `textbox` | `text_box` | anders benannt |
| `multiple_choice` | `multiple_choice` | 1:1 |
| `numerical_box` | `numerical_box` | 1:1 |
| `date` / `datetime` | `date` / `datetime` | 1:1 |
| `matrix` | `matrix` | 1:1 |

| Odoo 11 (`answer_type`) | Odoo 18 | Status |
|---|---|---|
| `text` | `text_box` | anders benannt (im Bestand: 71 Zeilen) |
| `suggestion` | `suggestion` | 1:1 |
| `number` | `numerical_box` | anders benannt |
| `date` | `date` | 1:1 |

### 3.4 Statuswerte

| Odoo 11 | Odoo 18 | Status | Entscheidung |
|---|---|---|---|
| Umfrage-Stufe `Draft` | - | fehlt | aktiv, siehe 5.1 |
| Umfrage-Stufe `In progress` | - | fehlt | aktiv, siehe 5.1 |
| Umfrage-Stufe `Closed` (`closed=True`, `fold=True`) | `active=False` (archiviert) | Mapping noetig | geschlossene Umfrage wird archiviert |
| Umfrage-Stufe `Permanent` | - | fehlt | aktiv, siehe 5.1 |
| Teilnahme `new` | `new` | 1:1 | unveraendert |
| Teilnahme `done` | `done` | 1:1 | unveraendert |
| (kein Gegenstueck) | `in_progress` | Zusatz | Odoo-18-Zusatz, bleibt erhalten |

### 3.5 Beziehungen

| Beziehung Odoo 11 | Odoo 18 | Status |
|---|---|---|
| Umfrage -> Seiten (`page_ids`) | Umfrage -> Fragen/Seiten (`question_and_page_ids`) | anders modelliert, Beziehung erhalten |
| Seite -> Fragen (`question_ids`) | Frage -> Seite (`page_id`) | Richtung gedreht, Beziehung erhalten |
| Frage -> Antwortvorgaben (`labels_ids`) | `suggested_answer_ids` | anders benannt, erhalten |
| Frage -> Matrixzeilen (`labels_ids_2`) | `matrix_row_ids` | anders benannt, im Bestand nicht verwendet |
| Teilnahme -> Antworten (`user_input_line_ids`) | `user_input_line_ids` | 1:1 |
| Antwort -> Vorgabe / Matrixzeile | `suggested_answer_id` / `matrix_row_id` | anders benannt, im Bestand nicht verwendet |
| Teilnahme -> Partner (`partner_id`) | `partner_id` | 1:1, im Bestand 0 Faelle |
| Umfrage -> CRM (survey_crm) | `survey_crm` in Odoo 18 nicht installiert | bewusst nicht uebernommen |

### 3.6 Menues, Ansichten, Filter

| Odoo 11 | Odoo 18 | Status | Entscheidung |
|---|---|---|---|
| Menue "Surveys" | "Umfragen" | 1:1 vorhanden | keine Aenderung |
| Menue "Answers" | "Teilnahmen" | 1:1 vorhanden | keine Aenderung |
| Menue "Configuration / Pages" | entfaellt (Seiten sind Fragen) | anders modelliert | Seiten ueber "Fragen" mit Spalte/Filter "Seite" erreichbar |
| Menue "Configuration / Questions" | "Fragen & Antworten / Fragen" | 1:1 vorhanden | keine Aenderung |
| Menue "Configuration / Labels" | "Fragen & Antworten / Vorgeschlagene Werte" | 1:1 vorhanden | keine Aenderung |
| Menue "Configuration / User Input Lines" | "Fragen & Antworten / Detaillierte Antworten" | 1:1 vorhanden | keine Aenderung |
| Kanban Umfragen gruppiert nach `stage_id` | Kanban ohne diese Gruppierung | fehlt | siehe 5.1 |
| Suchfilter "Archiviert" | "Archiviert" | 1:1 vorhanden | keine Aenderung |
| Suchfilter Aktivitaeten (4) | 3 Filter, in Odoo 18 eingeklappt (`invisible="1"`) | 1:1 vorhanden, Bedienung anders | Odoo-18-Standard |
| Weitere Filter/Gruppierungen | Zertifizierung, Verantwortlich, Eingeschraenkte Benutzer | Zusatz | bleibt erhalten |
| Auswertung (O11 nur Zahlen im Formular) | Graph + Pivot + "Ergebnisse ansehen" | Zusatz | bleibt erhalten |
| Server-Aktion "Testantworten entfernen" | - | entfallen | Odoo 18 filtert Testteilnahmen und loescht per Auswahl |
| Bericht | - | Zertifikats-PDF | Zusatz | bleibt erhalten (nicht benoetigt) |

### 3.7 Rechte und Gruppen

| Odoo 11 | Odoo 18 | Status | Entscheidung |
|---|---|---|---|
| `group_survey_user` (45 Benutzer) | "Umfragen / Benutzer" (599, 5 Benutzer inkl. technischer Konten) | anders modelliert | Rechte wie Odoo 11 über `itk_survey_security` (5.2) |
| `group_survey_manager` (42 Benutzer) | "Umfragen / Administrator" (600, 2 Benutzer) | anders modelliert | unverändert, sieht alle Antworten |
| Umfrage lesen nur wenn `stage_id.closed = False` | keine Einschraenkung (nur aktiv/archiviert) | anders | akzeptierte Abweichung (keine geschlossene Umfrage im Bestand) |
| Teilnahmen nur eigene (Record Rule) | alle Teilnahmen der Umfrage, ausser "eingeschraenkte Benutzer" | **weiter gefasst** | durch `itk_survey_security` auf Odoo-11-Verhalten zurückgeführt (5.2) |
| Anonymes Ausfuellen (public) | `access_mode = public` | 1:1 vorhanden | keine Aenderung |

## 4 Datenmigration

Skript: `scripts/migration/survey_migration.py`, Dokumentation
`docs/migration/survey_migration.md`.

Reihenfolge: Umfragen -> Seiten -> Fragen -> Antwortvorgaben -> Teilnahmen ->
Antworten -> Zeitstempel. Idempotenz ueber `itk_o11_id` auf allen fuenf Modellen
(Modul `itk_migration_keys` 18.0.1.2.0). Der Zielbestand wird immer mit
`active_test=False` gelesen.

| Objekt | Soll aus Odoo 11 | Zielmodell Odoo 18 |
|---|---|---|
| Umfragen | 2 | `survey.survey` |
| Seiten | 2 | `survey.question` (`is_page=True`) |
| Fragen | 2 | `survey.question` (`is_page=False`) |
| Antwortvorgaben | 2 | `survey.question.answer` |
| Teilnahmen | 72 | `survey.user_input` |
| Antworten | 71 | `survey.user_input.line` |

Besonderheiten:

- Die Odoo-11-IDs von Seiten und Fragen ueberlappen (Seite 1 und Frage 1). Die
  Zuordnung fuehrt beide Namensraeume getrennt und unterscheidet ueber `is_page`.
- `end_datetime` einer abgeschlossenen Teilnahme wird aus dem Zeitpunkt der letzten
  Antwort gesetzt (Odoo 11 fuehrt kein Abschlussdatum). Bei der Teilnahme ohne
  Antwortzeile bleibt es leer.
- `start_datetime` entspricht dem Odoo-11-`date_create`; in diesem Bestand ist es
  mit `create_date` identisch.
- Der Antworttext wird unveraendert uebernommen (kein Kuerzen, keine Normalisierung).
- Erstellungs-/Bearbeitungsdatum und Ersteller werden ueber
  `itk.migration.zeitstempel` nachgezogen, weil Odoo 18 Log-Access-Felder im ORM
  verwirft.

## 5 Bewusst akzeptierte Abweichungen und offene Entscheidungen

### 5.1 Umfrage-Stufen (akzeptierte Abweichung, Entscheidung bestaetigen)

Odoo 18 hat das Stufenmodell abgeschafft. Eine Umfrage ist entweder aktiv oder
archiviert. **Regel:** Odoo-11-Stufe "Geschlossen" entspricht "archiviert", alle
anderen Stufen bleiben aktiv. Es wird **kein** Statusfeld nachgebaut (kein
Rueckbau des Odoo-18-Standards).

Was dadurch entfaellt: die Statusspalte in der Umfrageliste, die Kanban-Gruppierung
nach Stufe und die Sichtbarkeitsregel "geschlossene Umfrage fuer normale Benutzer
ausblenden". Im vorhandenen Bestand sind beide Umfragen offen (Entwurf, In
Bearbeitung), es geht kein Datensatz und keine Sichtbarkeit verloren.

Falls die Stufe sichtbar bleiben soll, waere ein ITK-Zusatzfeld (nur Anzeige und
Gruppierung) moeglich - dafuer ist eine ausdrueckliche Entscheidung notwendig.

### 5.2 Sichtbarkeit fremder Antworten (geloest am 19.11.2026, Session 147)

- Odoo 11: normale Umfrage-Benutzer sehen **nur ihre eigenen** Antworten
  (Record Rule `create_uid = user` bzw. `partner_id = user.partner_id`).
- Odoo 18 (Standard): Benutzer der Gruppe "Umfragen / Benutzer" sehen **alle**
  Antworten; eingeschraenkt wird nur ueber das Feld "eingeschraenkte Benutzer"
  je Umfrage.

**Entscheidung (Anna Maierhofer, 19.11.2026):** Das Odoo-11-Prinzip bleibt erhalten.
Normale Umfrage-Benutzer sehen nur ihre eigenen Teilnahmen und Antworten, Manager und
Administratoren weiterhin alle.

**Umsetzung:** Modul `itk_survey_security` 18.0.1.0.0 (nur Rechtekonfiguration, keine
Felder, keine Daten). Es ueberschreibt die beiden Gruppenregeln des Moduls `survey` fuer
`survey.user_input` und `survey.user_input.line` mit derselben XML-ID:

| Regel | neue Domain |
|---|---|
| `survey.survey_user_input_rule_survey_user` | Umfragetyp wie bisher UND (`create_uid = user` ODER `partner_id = user.partner_id`) |
| `survey.survey_user_input_line_rule_survey_user` | Umfragetyp wie bisher UND (`user_input_id.create_uid = user` ODER `user_input_id.partner_id = user.partner_id`) |

Warum dieser Weg:

- Die Regeln stehen im Modul `survey` in einem Block `noupdate="1"`; ein Upgrade von
  `survey` setzt sie nicht zurueck, ein Upgrade von `itk_survey_security` schreibt sie
  erneut. Die Konfiguration liegt damit im Repository, nicht in einem einmaligen Eingriff.
- Eine **zusaetzliche** Gruppenregel wuerde nicht wirken, weil Odoo Gruppenregeln mit
  ODER kombiniert - die bestehende Officer-Regel wuerde die Einschraenkung aushebeln.
- Eine **globale** Regel wuerde auch Manager und Administrator einschraenken; das ist
  ausgeschlossen.
- Die Manager-Regeln (`survey_user_input_rule_survey_manager`,
  `survey_user_input_line_rule_survey_manager`) bleiben unveraendert. Wer zusaetzlich in
  "Umfragen / Administrator" ist, sieht ueber die ODER-Verknuepfung weiterhin alles. Das
  Administratorkonto ist unberuehrt.
- Oeffentliche Umfragen (Ausfuellen ohne Anmeldung) laufen ueber den Controller mit
  erhoehten Rechten und sind nicht betroffen.

Geprueft mit `scripts/migration/survey_rechte_pruefung.py` (28 Pruefungen je Instanz) und
`scripts/browser_survey_rechte.py` (echter Chrome, eigene und fremde Teilnahme,
direkte URL auf eine fremde Antwort).

### 5.3 Weitere nicht uebernommene Punkte

| Punkt | Grund |
|---|---|
| `survey_crm` ("Umfrage senden" aus Interessent/Kontakt) | 0 Datensaetze, Funktion wird nicht mehr benoetigt (Projektentscheidung); haette ausserdem das gesperrte CRM beruehrt |
| Server-Aktion "Testantworten entfernen" | in Odoo 18 ueber Filter und Loeschen abgedeckt |
| `display_mode` / `column_nb` | Odoo 18 stellt Auswahlfragen immer als Spalten dar |
| `designed`, `public_url`, `print_url`, Kennzahlen | in Odoo 18 berechnet |
| `user_input.type` | in Odoo 18 entfallen |
| `quizz_score` | in Odoo 18 aus den Antworten berechnet; beide Umfragen ohne Bewertung |

## 6 Odoo-18-Zusatzfunktionen, die erhalten bleiben

Zertifizierungen, Live-Session, Bewertung mit Punkten, Zeitlimit, Abschnitte mit
bedingten Fragen, Einladung per E-Mail, Auswertung als Graph und Pivot,
"Ergebnisse ansehen", Zertifikats-PDF, Feld "eingeschraenkte Benutzer",
Verantwortlicher je Umfrage, Aktivitaeten. Nichts davon beruehrt die
Odoo-11-Funktionalitaet; es wird nichts davon entfernt.

## 7 Ergebnisse der Migration (Stand 18.11.2026)

### 7.1 Datenmigration lokal

| Objekt | Odoo 11 | Odoo 18 lokal | angelegt | Idempotenzlauf |
|---|---|---|---|---|
| Umfragen | 2 | 2 | 2 | 0 neu |
| Seiten (Abschnitte) | 2 | 2 | 2 | 0 neu |
| Fragen | 2 | 2 | 2 | 0 neu |
| Antwortvorgaben | 2 | 2 | 2 | 0 neu |
| Teilnahmen | 72 | 72 | 72 | 0 neu |
| Antworten | 71 | 71 | 71 | 0 neu |

Zweiter Lauf: **0 angelegt, 0 aktualisiert, 151 übersprungen, 0 Fehler, 0 Dubletten.**
Erstellungs- und Bearbeitungsdatum sowie Ersteller sind je Datensatz auf dem
Odoo-11-Stand (Zeitstempel-Importweg, weil Odoo 18 Log-Access-Felder im ORM verwirft).

### 7.2 Abgleich Odoo 11 gegen Odoo 18 lokal

`scripts/migration/survey_abgleich.py --instanz lokal`: **409 Prüfungen OK, 0 Abweichungen.**
Geprüft wurden Mengen, Statuswerte je Teilnahme, Testteilnahmen, aktive Umfragen,
Partner-/E-Mail-/Fristbezüge, übersprungene Antworten, Punktesummen, Titel, Fragetypen,
Pflichtfelder, Fehlertexte, Abschnittszuordnung, Token, Start- und Erstellungsdatum,
Beziehungen Umfrage → Seite/Frage/Teilnahme → Antwort sowie die Antworttexte über
Länge und SHA-1-Prüfsumme (Inhalte werden nicht ausgegeben).

Bekannte, dokumentierte Abweichung: drei Beziehungsprüfungen im Abgleich vergleichen
IDs über den Anker; die Punktesumme ist in beiden Systemen 0,00 (beide Umfragen ohne
Bewertung).

### 7.3 Browserabnahme lokal

`scripts/browser_survey_abnahme.py --instanz lokal`: **44 OK / 0 FEHL**, echter Chrome.

Belegt: Menüband mit Umfragen/Teilnahmen/Fragen & Antworten, Umfrageliste (2 Umfragen),
Kanban (2 Karten), Umfrageformular mit Abschnitt und Frage, Fragenliste (2), Vorgaben (2),
Teilnahmenliste (72, standardmäßig nach Umfrage gruppiert), Filter "Abgeschlossen" (71),
Gruppierung entfernen und erneut setzen, Suche nach Umfragetitel, Einzelteilnahme mit
Antwortzeile, Ergebnisseite, Ausfüllen der öffentlichen Umfrage über die Oberfläche
(Startseite → Antwort → Absenden → Danke-Seite, Teilnahme mit Status "Abgeschlossen" und
einer Antwortzeile), Anlegen einer Umfrage samt Frage über den Dialog "Abschnitte und
Fragen erstellen" und Löschen der Testdaten.

Befunde (keine Fehlschläge):

- Die Ansichtsumschalter der Umfrage-Aktion führen nur Kanban/Liste/Formular/Aktivität;
  Graph und Pivot sind im Modul vorhanden, aber nicht in der Aktion verknüpft
  (Odoo-18-Standard). Auswertung läuft über "Ergebnisse ansehen".
- Die Teilnahmen-Suche sucht nach Teilnehmer/E-Mail; der Umfragetitel wird über
  Filter/Gruppierung "Umfrage" gesetzt (wie in Odoo 11).
- Die Spalte "Fragen" ist in der Umfrageliste über die Spaltenauswahl zuschaltbar.
- Fragen werden im Formular über den Dialog "Abschnitte und Fragen erstellen" angelegt.

### 7.4 Rechteprüfung (nach der Rechteanpassung)

`scripts/migration/survey_rechte_pruefung.py`: **28 OK / 0 FEHL** je Instanz.

| Rolle | Umfragen lesen | eigene Teilnahme | fremde Teilnahmen | Verwalten |
|---|---|---|---|---|
| Interner Benutzer ohne Umfragegruppe | nein | nein | nein | nein |
| Umfragen / Benutzer | ja (2) | ja (genau 1 sichtbar) | nein (Suche, direkter Zugriff und Schreiben verweigert) | ja |
| Umfragen / Administrator | ja (2) | ja | ja (72 migrierte plus Testteilnahmen) | ja |

`scripts/browser_survey_rechte.py`: **6 OK / 0 FEHL** je Instanz. Ein normaler
Umfrage-Benutzer sieht in der Teilnahmenliste genau die eigene Teilnahme; die direkte URL
auf eine fremde Teilnahme endet im Odoo-Zugriffsfehler ("Es sieht so aus, als wären Sie
über einige streng geheime Datensätze gestolpert"). Der Administrator sieht alle
Teilnahmen und öffnet die fremde Antwort.

### 7.5 Datenmigration VM

Derselbe Skriptstand, dieselbe Quelle. Auf der VM traten zwei Effekte auf, die auf
lokal nicht sichtbar waren und im Skript behoben wurden:

1. **Abschnittszuordnung beim Anlegen über die O2M.** Odoo verwarf beim Create über
   `question_and_page_ids` das Feld `page_id` und setzte für Abschnitte eine eigene
   Sequenz. Folge: Die Frage hing ohne Abschnitt, und die öffentliche Umfrageseite zeigte
   den Abschnitt ohne Frage. Das Skript setzt `page_id` und `sequence` nach dem Anlegen
   ausdrücklich nach.
2. **Zeitstempel über die Ziel-ID.** Der Nachzug schreibt über `id` (nicht über
   `itk_o11_id`), weil Odoo-11-Seite 1 und -Frage 1 dieselbe ID tragen. Mit dem falschen
   Schlüssel trafen nur Zufallstreffer; auf der VM blieben 71 Teilnahmen auf dem
   Einspieldatum. Nach dem Fix wurden 72 Teilnahmen, 71 Antworten und 2 Fragen
   nachgezogen.

Nach dem Fix, auf beiden Instanzen:

| Objekt | Odoo 11 | Odoo 18 VM | angelegt | Idempotenzlauf |
|---|---|---|---|---|
| Umfragen | 2 | 2 | 2 | 0 neu |
| Seiten (Abschnitte) | 2 | 2 | 2 | 0 neu |
| Fragen | 2 | 2 | 2 | 0 neu |
| Antwortvorgaben | 2 | 2 | 2 | 0 neu |
| Teilnahmen | 72 | 72 | 72 | 0 neu |
| Antworten | 71 | 71 | 71 | 0 neu |

Zweiter Lauf VM: 0 angelegt, 0 aktualisiert, 151 übersprungen, 0 Fehler, 0 Dubletten.
Abgleich VM: 409 Prüfungen OK, 0 Abweichungen. Browser VM: 44 OK / 0 FEHL.
Rechte VM: 17 OK / 0 FEHL.

### 7.6 Live-Drift in Odoo 11 nach der Migration (19.11.2026)

Odoo 11 ist produktiv. Zwischen Migration (18.11.) und Abschlusspruefung (19.11.) wurde
dort die Teilnahme **ID 1624** geloescht: eine angefangene Teilnahme ohne Antwortzeile an
der Testumfrage "Wird Odoo noch was?" (`state = new`, angelegt am 18.11.2026 um 13:16).
Odoo 11 fuehrt jetzt 71 Teilnahmen, Umfrage 1 hat dort keine Teilnahme mehr.

Odoo 18 (lokal und VM) behaelt den Datensatz als Historie: 72 Teilnahmen, davon eine
`new` ohne Antwortzeile. Er wurde bewusst **nicht** geloescht - Daten werden in diesem
Projekt nur auf ausdrueckliche Freigabe entfernt.

Folge fuer den Abgleich: Er meldet genau diese vier Punkte als Abweichung (Anzahl,
Statusverteilung, Teilnahmen je Umfrage 1, Zeitspanne). Alles andere bleibt deckungsgleich.
Die Migration selbst ist davon nicht betroffen - der Datensatz war zum Migrationszeitpunkt
in Odoo 11 vorhanden.

