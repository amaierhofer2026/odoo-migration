# Odoo 11 -> Odoo 18: Bereich EVENTS (Veranstaltungen) - Bestandsaufnahme und Vergleich

Stand: 28.10.2026, Session 138. Reine Lesefassung: In Odoo 11 wurde nichts geschrieben,
in Odoo 18 wurde nichts installiert, angelegt oder geaendert.

Quelle Odoo 11: Produktion `portal.it-kommunal.at`, DB `ITK_V1_a`, ausschliesslich
Leseabfragen (JSON-RPC). Quelle Odoo 18: lokal (`localhost:8069`, DB `odoo18_test`)
und VM (`https://k001959vsx.ipax.at`), Modulquelldateien des Containers gelesen.

---

## 1. Bestand Odoo 11 (live erhoben)

| Objekt | Modell | Datensaetze |
|---|---|---|
| Veranstaltungen | event.event | **122** (121 aktiv, 1 archiviert) |
| Teilnehmer / Anmeldungen | event.registration | **760** |
| Anlasskategorien | event.type | **2** |
| Mailplanung je Kategorie | event.type.mail | **5** |
| Mailplanung je Veranstaltung | event.mail | **170** |
| Teilnehmer-Mails (Versandprotokoll) | event.mail.registration | **758** |
| Fragen / Antworten | event.question / event.answer | **0 / 0** |
| Nachrichten (Chatter) | mail.message | 565 (Events) + 2.404 (Teilnehmer) = **2.969** |
| Abonnenten | mail.followers | 269 (Events) + 761 (Teilnehmer) = 1.030 |
| Anhaenge | ir.attachment | **6** (nur Teilnehmer, PDF-Teilnehmerausweise) |

Verteilung Veranstaltungen:

- Status: `confirm` 100, `cancel` 15, `done` 7 (kein `draft`).
- Zeitraum: 16.11.2020 bis 23.03.2026.
- Zeitzone: **alle 122** `Europe/Berlin`.
- Kategorie: 120 x "Online", 2 x keine Kategorie.
- Website veroeffentlicht: **101** von 122.
- Platzbegrenzung: 116 `limited`, 6 `unlimited`; `seats_max` bei 120 gesetzt
  (111 x 25, Rest 2 bis 40).
- `seats_min` bei 114 gesetzt (108 x 5, 3 x 1, 3 x 3).
- `is_online` = True bei 120/122; `auto_confirm` True bei 120/122.
- Ohne Daten: `twitter_hashtag`, `description`, `badge_front/innerleft/innerright/back`,
  `event_logo`, `menu_id` (Website-Menue) - jeweils 0 belegt.
- Veranstaltungsorte: 2 verschiedene (`IT-Kommunal GmbH`, `Hofstadler Helga - Kontakt - [Zentrum fuer Medienwissen]`).
- Veranstalter: dieselben 2 Partner.
- Verantwortliche Benutzer: 1 Veranstaltung ohne `user_id`.

Verteilung Teilnehmer:

- Status: `open` 629, `cancel` 95, `done` 26, `draft` 10.
- **Kontrollzahl:** Summe `seats_reserved` = **629** = Anzahl Teilnehmer mit Status `open`.
- Mit Kontakt verknuepft: 758, ohne Kontakt: 2. E-Mail bei allen 760 gesetzt, Telefon bei 464.
- `origin` (Referenzbeleg) und Antworten: 0 belegt.
- `date_open` weicht bei 23 Datensaetzen um genau 1 Sekunde von `create_date` ab.
- 38 Paare (Veranstaltung + Kontakt + E-Mail) sind **echte Mehrfachanmeldungen** derselben
  Person zum selben Termin (Odoo 11 zaehlt sie mit) - nicht bereinigen.
- 15 Veranstaltungen haben keine Anmeldung.

Installierte Odoo-11-Module des Bereichs:
`event` 11.0.1.0, `website_event` 11.0.1.0, `website_event_questions` 11.0.1.0,
`mass_mailing_event` 11.0.1.0. Nicht installiert: `event_sale`, `website_event_track`,
`website_event_sale`, `event_barcode`, `event_crm`.

## 2. Bestand Odoo 18 (lokal und VM identisch)

| Modul | lokal | VM |
|---|---|---|
| `event` | **nicht installiert** (verfuegbar 18.0.1.9) | **nicht installiert** |
| `website_event` | nicht installiert (18.0.1.4) | nicht installiert |
| `mass_mailing_event` | nicht installiert (18.0.1.0) | nicht installiert |
| `event_sale` / `website_event_sale` / `website_event_track` | nicht installiert | nicht installiert |
| `mass_mailing` | installiert 18.0.2.7 | installiert 18.0.2.7 |
| `website` | installiert | installiert |

**Kernbefund:** Der gesamte Bereich Events existiert in Odoo 18 derzeit nicht - kein Modul,
kein Menue, keine Ansicht, keine Datensaetze. `res.partner` enthaelt lokal 96 Kontakte.

## 3. Menuevergleich

| Odoo 11 (de_DE) | Odoo 18 (de_DE) | Status |
|---|---|---|
| Events (App) | Veranstaltungen (App) | anders benannt |
| Events > Events (Liste/Kanban/Kalender/Formular/Pivot) | Veranstaltungen > Veranstaltungen | anders benannt |
| Events > Berichtswesen > Events (Pivot/Graph) | Veranstaltungen > Berichtswesen > (kein Veranstaltungs-Pivot) | fehlt |
| Events > Berichtswesen > Fragestellungen | - (Odoo 18: Fragen sind Teil des Moduls event) | nicht verwendet (0 Fragen) |
| Events > Konfiguration > Anlasskategorien | Veranstaltungen > Konfiguration > Veranstaltungsvorlagen | anders benannt |
| (kein Gegenstueck) | Veranstaltungen > Konfiguration > Veranstaltungsphasen | Odoo-18-Zusatz |
| (kein Gegenstueck) | Veranstaltungen > Konfiguration > Stichwortkategorien | Odoo-18-Zusatz |
| (kein Gegenstueck) | Veranstaltungen > Konfiguration > Mailplaner (nur Entwicklermodus) | Odoo-18-Zusatz |
| Events > Konfiguration > Einstellungen | Veranstaltungen > Konfiguration > Einstellungen | 1:1 |
| Events > Berichtswesen (Gruppe Manager) | Berichtswesen (Gruppe Veranstaltungen/Benutzer) | Rechteunterschied |

Aktionen in Odoo 11: "Veranstaltungs-Statistik" (pivot,graph auf event.event),
"Teilnehmer" (tree,form,calendar,pivot,graph), "Abonnieren", "Anlassbestaetigung" (Assistent),
"Veranstaltungs-Mailplaner", "Anlasskategorien", "Analyse der Fragen".

## 4. Ansichtenvergleich

### 4.1 Veranstaltung (event.event)

| Ansicht | Odoo 11 | Odoo 18 | Befund |
|---|---|---|---|
| Liste | 10 Spalten (Name, Kategorie, Beginn, Ende, Reservierungen, min, max, Verantwortlich, Status, Aktion) | 17 Spalten (Name, Ort, Organisator, Verantwortlich, Firma, Beginn, Ende, Stichwoerter, Plaetze...) | Odoo 18 breiter, Status fehlt (kein `state`) |
| Kanban | ohne Phasen, Karte: Verantwortlich, Land, Beginn, Ende, Plaetze | **mit Phasen** (Neu/Gebucht/Angekuendigt/Beendet/Abgebrochen) | Strukturunterschied |
| Formular | Kopf: Status, erwartete Teilnehmer, aktiv, Name, Online-Event, Organisator, Ort, Firma, Verantwortlich, Kategorie, Hashtag, Auto-Bestaetigung, Beginn, Ende, Zeitzone, min, Platzbegrenzung, max; Reiter "Email Schedule"; Chatter | Kopf: Phase, Plaetze belegt, aktiv, Firma, Kanban-Status, Name, Beginn, Ende, Zeitzone, Sprache, Kategorie, Stichwoerter, Organisator, Verantwortlich, Ort; Reiter: Mailplanung, Fragen, Notiz, Ticket-Anleitung; Chatter | Felder teils anders, teils fehlend (siehe 5) |
| Kalender | Name, Kategorie | Verantwortlich, Plaetze, Kategorie | Odoo-18-Zusatz |
| Pivot | Name, Reservierungen | **kein Pivot fuer Veranstaltungen** | fehlt |
| Suche | Filter: Ungelesene Nachrichten, Unbestaetigt, Bestaetigt, Meine Events, Kommende, Archiviert; Gruppe: Verantwortlich, Kategorie, Status, Startmonat | Filter: Meine Veranstaltungen, Kommende, Startdatum, Inaktiv, Aktivitaeten, Online, Verantwortlich, Kategorie, Phase, Zeitraum, Ort; Gruppe u.a. Phase | weitgehend vorhanden, Status -> Phase |
| Aktionen/Buttons | Bestaetigen, Abschliessen, Auf Entwurf, Absagen, "Teilnehmer per E-Mail", Archivieren | nur "Statistik"; Phasenwechsel ueber Kanban, kein Bestaetigen/Absagen-Button | Funktionsunterschied |

### 4.2 Teilnehmer (event.registration)

| Ansicht | Odoo 11 | Odoo 18 | Befund |
|---|---|---|---|
| Liste | Erstellt am, Kontakt, Name, Telefon, E-Mail, Veranstaltung, Status | Strichcode, aktiv, Erstellt am, Name, Kontakt, E-Mail, Telefon, Firma, Veranstaltung, Ticket, Aktivitaeten, Status | Odoo 18 um Ticket/Barcode/Firma umfangreicher |
| Formular | Status, Kontakt, Name, Telefon, E-Mail, Veranstaltung, Anmeldedatum, Teilnahme-Datum; Buttons: Per E-Mail senden, Bestaetigen, Teilgenommen, Auf Unbestaetigt, Absagen | Status, Name, E-Mail, Telefon, Firma, Veranstaltung, Barcode, Ticket, Kontakt, Erstellt am, Teilnahme-Datum, UTM, Eigenschaften, Antworten; Buttons: Per E-Mail senden, Registriert, Teilgenommen, Absagen | `date_open` fehlt in Odoo 18, `origin` fehlt |
| Kanban | nicht vorhanden | vorhanden | Odoo-18-Zusatz |
| Kalender/Pivot/Graph | vorhanden | vorhanden | 1:1 |
| Suche | Filter: Ungelesen, Erwartet; Gruppe: Kontakt, Veranstaltung, Status, Anmeldetag/-monat | Filter: laufend, genommen, unbestaetigt, bestaetigt, teilgenommen, Erstell-/Start-/Teilnahmedatum, Aktivitaeten, letzter Monat, inaktiv; Gruppe: Kontakt, Veranstaltung, Ticket, Status, Woche/Tag, UTM | Odoo-18-Zusatz, Odoo-11-Filter abgedeckt |

### 4.3 Kategorie/Anlasskategorie (event.type), Mailplaner, Fragen

- `event.type`: Odoo 11 Formular hat 19 Felder (Zeitzone, Mailplanung, Hashtag, Platzlimit,
  Auto-Bestaetigung, Fragen). Odoo 18 Formular hat 12 Felder, davon **neu**: Stichwoerter,
  Tickets, Ticket-Anleitung; **fehlend**: `auto_confirm`, `use_timezone`, `use_hashtag`,
  `default_hashtag`, `is_online`, `use_mail_schedule`, `use_questions`,
  `default_registration_min/max`, `website_menu`.
- `event.mail`: Odoo 18 ersetzt `template_id` durch `template_ref` (Reference),
  `done` durch `mail_done` + `mail_state` + `mail_count_done`; `scheduled_date` ist in
  Odoo 18 **berechnet** (nicht schreibbar).
- `event.question`: nicht verwendet (0 Datensaetze), Odoo 18 hat ein reichhaltigeres Modell
  (Fragetypen, Pflichtfrage, Eigenschaften) - nicht migrieren.

## 5. Feldmapping Veranstaltung (event.event)

Format: Odoo-11-Feld | verwendet? | Odoo-18-Entsprechung | Status | empfohlene Aktion

| Odoo-11-Feld | verwendet? | Odoo-18-Entsprechung | Status | Aktion |
|---|---|---|---|---|
| name | ja (122) | name | 1:1 vorhanden | migrieren |
| active | ja | active | 1:1 vorhanden | migrieren (1 archiviert) |
| date_begin / date_end | ja | date_begin / date_end | 1:1 vorhanden | migrieren |
| date_tz | ja (alle Europe/Berlin) | date_tz | 1:1 vorhanden | migrieren |
| event_type_id | ja (120) | event_type_id | anders benannt (Label "Kategorie" vs "Veranstaltungsvorlage") | migrieren, Label angleichen |
| organizer_id | ja (2 Partner) | organizer_id | 1:1 vorhanden | migrieren |
| address_id | ja (2 Partner) | address_id | 1:1 vorhanden | migrieren |
| company_id | ja | company_id | 1:1 vorhanden | migrieren |
| user_id | ja (121) | user_id | 1:1 vorhanden | ueber Login zuordnen |
| state | ja | **stage_id** (event.stage) | Mapping noetig | draft->Neu, confirm->Gebucht, done->Beendet, cancel->Abgebrochen |
| seats_max | ja (120) | seats_max | 1:1 vorhanden | migrieren |
| seats_availability | ja | seats_limited (Boolean) | Mapping noetig | limited->True, unlimited->False |
| seats_min | ja (114) | **fehlt** | fehlt | Entscheidung E5 |
| seats_reserved / seats_used / seats_unconfirmed / seats_expected | berechnet | seats_reserved / seats_used / seats_taken | Neuberechnung | nicht schreiben, Odoo 18 rechnet |
| is_online | ja (120) | **fehlt** | fehlt | Entscheidung E5 |
| auto_confirm | ja (120 True, 2 False) | **fehlt** (Odoo 18 bestaetigt immer) | entfallen | dokumentieren, nicht nachbauen |
| twitter_hashtag | nein (0) | tag_ids (Stichwoerter) | obsolet | nicht migrieren |
| description / event_logo / badge_front/innerleft/innerright/back | nein (0) | description / badge_image / badge_format | entfallen | nicht migrieren |
| note | nein | note | 1:1 vorhanden | nicht migrieren |
| website_published | ja (101) | website_published (nur mit website_event) | 1:1 vorhanden, Modul fehlt | Entscheidung E1 |
| website_menu / menu_id | nein (0) | menu_id (website_event) | 1:1 vorhanden, unbenutzt | nicht migrieren |
| country_id | nein | country_id | 1:1 vorhanden | nicht migrieren |
| lang | nicht vorhanden | lang | Odoo-18-Zusatz | nicht setzen |
| event_mail_ids | ja (170) | event_mail_ids | 1:1 vorhanden | migrieren mit Sonderregel E6 |
| message_ids / message_follower_ids | ja | chatter | anders benannt | Entscheidung E7 |
| color | nein | (kein Gegenstueck) | entfallen | nicht migrieren |

## 6. Feldmapping Teilnehmer (event.registration)

| Odoo-11-Feld | verwendet? | Odoo-18-Entsprechung | Status | Aktion |
|---|---|---|---|---|
| event_id | ja | event_id | 1:1 vorhanden | migrieren |
| name | ja | name | 1:1 vorhanden | migrieren |
| email | ja | email | 1:1 vorhanden | migrieren |
| phone | ja (464) | phone | 1:1 vorhanden | migrieren |
| partner_id | ja (758) | partner_id | 1:1 vorhanden | ueber fachlichen Schluessel zuordnen |
| state | ja | state | 1:1 vorhanden, Beschriftung anders | migrieren (`open` = O11 "Bestaetigt", O18 "Registriert") |
| date_closed | ja (26) | date_closed | 1:1 vorhanden | migrieren |
| date_open | ja | **fehlt** | entfallen | `create_date` traegt den Wert (23 x 1 Sekunde Abweichung) |
| origin | nein (0) | **fehlt** | obsolet | nicht migrieren |
| answer_ids | nein (0) | registration_answer_ids | 1:1 vorhanden | nicht migrieren |
| company_id | ja | company_id (related) | 1:1 vorhanden | automatisch |
| message_ids / message_follower_ids | ja | chatter | anders benannt | Entscheidung E7 |
| active | nicht vorhanden | active | Odoo-18-Zusatz | nicht setzen |

## 7. Statuswerte und Workflow

Odoo 11 Veranstaltung: `draft` (Unbestaetigte Anmeldungen -> real "Nicht bestaetigt"),
`confirm` (Bestaetigt), `done` (Erledigt), `cancel` (Abgebrochen). Buttons: Bestaetigen,
Abschliessen, Auf Entwurf, Absagen. Kein `draft` in den Daten.

Odoo 18 Veranstaltung: **kein `state`**. Phasen (`event.stage`): Neu, Gebucht, Angekuendigt,
Beendet (gefaltet), Abgebrochen (gefaltet); zusaetzlich `kanban_state` (In Arbeit, Erledigt,
Blockiert). Phasenwechsel erfolgt ueber Kanban bzw. Phasenauswahl, nicht ueber
Bestaetigen/Absagen-Buttons.

Odoo 11 Teilnehmer: `draft`, `open`, `cancel`, `done` - identische technische Werte in Odoo 18,
nur die sichtbaren Beschriftungen weichen ab (`open`: O11 "Bestaetigt", O18 "Registriert";
`draft`: O11 "Nicht bestaetigte Anmeldungen", O18 "Unbestaetigt").

## 8. Beziehungen

- **Kontakte:** 29 verschiedene Partner werden referenziert (14 Firmen, 15 Personen, 2 archiviert,
  22 mit E-Mail, 3 mit Hauptkontakt). Davon 2 als Ort/Veranstalter, 27 als Teilnehmer.
  In Odoo 18 sind lokal **nur 6 von 29** vorhanden (Namensgleichheit); `res.partner` hat dort
  insgesamt 96 Datensaetze, die Kontaktmigration ist noch nicht gelaufen.
- **Benutzer:** 6 verschiedene Odoo-11-Benutzer referenziert (Verantwortlich/Erstellt von);
  5 davon existieren in Odoo 18 (ueber Login), nur `admin` fehlt (-> Odoo-18-Administrator).
  Die historische Benutzerin `ausgeschieden/Steinecker Julia` ist in Odoo 18 vorhanden (id 50),
  `Breit Christiane` ist in Odoo 11 inaktiv und in Odoo 18 vorhanden (id 14).
- **Orte:** eigener Datensatz (res.partner), kein separates Ortsmodell in Odoo 11 - Odoo 18
  identisch.
- **Kategorien:** Odoo 11 nur `event.type`; Odoo 18 zusaetzlich `event.tag` und
  `event.tag.category` (in Odoo 11 nicht vorhanden, 0 Stichwoerter belegt).

## 9. E-Mail-Kommunikation, Vorlagen, Mailplaner (Kernrisiko erneuter Versand)

Odoo 11: 4 Vorlagen auf `event.registration` ("Event: Registration", "Event: Registration Badge",
"Event: Reminder", "Reminder2"). Cron "Event: Mail-Planer" aktiv.

Mailplanung Odoo 11: 170 Zeilen, davon `after_sub` 121 (Ausloeser "Nach jeder Registrierung",
Einheit "Sofort"), `before_event` 49 (1 Tag bzw. 10 Tage vorher). **`done` = False bei 112,
`mail_sent` = False bei 130.**

Versandprotokoll `event.mail.registration`: 758 Zeilen, `mail_sent` True 750, **False 8**.

Odoo 18 (`event/models/event_mail.py`, gelesen):
- Cron "Event: Mail Scheduler" ruft stuendlich `schedule_communications()`.
- `after_sub`-Planer werden **immer** ausgefuehrt; gesendet wird jede Zeile
  `event.mail.registration` mit `mail_sent = False` und `scheduled_date <= jetzt`.
- `before_event`-Planer werden nur gesendet, wenn das Veranstaltungsende **in der Zukunft** liegt
  (historische Veranstaltungen sind dadurch geschuetzt).
- `after_event`-Planer (in Odoo 11 nicht verwendet) wuerden bei vergangenem Termin senden.

**Folge:** Werden die 170 Planer und 758 Protokollzeilen unveraendert uebernommen, wuerde der
Odoo-18-Cron die 8 offenen Teilnehmer-Mails sofort versenden - und die 121 `after_sub`-Planer
fuer kuenftige Anmeldungen aktiv halten. Die Migration muss daher alle uebernommenen
Protokollzeilen als "gesendet" uebernehmen und die historischen Planer stilllegen
(Entscheidung E6). Es darf kein einziger historischer Versand ausgeloest werden.

## 10. Rechte, Gruppen, Record Rules

| Odoo 11 | Benutzer | Odoo 18 |
|---|---|---|
| Gruppe 87 "Events / Benutzer" | 41 aktive | `event.group_event_user`, `event.group_event_registration_desk` |
| Gruppe 88 "Events / Manager" | 28 aktive | `event.group_event_manager` |

Odoo-11-Modellrechte: `event.event` lesen fuer Benutzer, schreiben nur Manager;
`event.registration` voll fuer Benutzer; `event.mail`, `event.mail.registration`,
`event.type.mail` lesen fuer Benutzer, schreiben nur Manager; oeffentlich/Portal nur lesen.

Record Rules Odoo 11 auf Veranstaltungen: "Event: multi-company" (Firmenfilter),
"event: Public" (`website_published = True` fuer Portal/oeffentlich).
Auf Teilnehmern: "Event/Registration: Portal" (eigene E-Mail/eigener Kontakt),
"Event/Registration: multi-company".

Odoo 18 bringt dieselben Mechanismen mit (`event.group_event_user`,
`event.group_event_registration_desk`, `event.group_event_manager`, Multi-Company-Regel,
Portal-Regel). Von den 23 Odoo-11-Logins der Manager-Gruppe existieren **8** als Odoo-18-Benutzer.

## 11. Automatische Aktionen und Cron

- `base.automation` in Odoo 11 installiert, aber **keine** automatisierte Aktion auf einem
  Event-Modell (die zwei vorhandenen betreffen Urlaub und Verkaufschance).
- Server Actions auf Event-Modellen: keine.
- Cron Odoo 11 "Event: Mail-Planer" (aktiv) -> Odoo 18 "Event: Mail Scheduler" (stuendlich).
- Odoo 18 zusaetzlich: automatischer Phasenwechsel nach Veranstaltungsende (`_cron_...`),
  Aktivitaeten (`mail.activity.mixin`).

## 12. Suche, Filter, Gruppierungen, Favoriten

Alle Odoo-11-Filter haben in Odoo 18 ein Gegenstueck ausser "Unbestaetigt/Bestaetigt"
(Status -> Phase) und dem Pivot "Veranstaltungs-Statistik".

Favoriten (gespeicherte Filter) in Odoo 11: 246 insgesamt, davon **genau einer** auf einem
Event-Modell: "Teilnehmer" (id 93, Modell `event.registration`, Benutzer Soritz Gerd,
Standardfilter, Domain `[['event_id','=',9],['state','in',['draft','open','done']]]`,
Kontext `{'default_event_id': 9}`). Das ist ein persoenlicher Filter auf genau eine
Veranstaltung (id 9); er wird nicht migriert, weil Odoo-18-Filter benutzergebunden sind und
die Veranstaltungs-ID neu vergeben wird. Alle uebrigen 245 Filter betreffen andere Bereiche.

## 13. Anhaenge und Chatter

- 6 PDF-Anhaenge auf Teilnehmern, alle vom Typ `badge_of_...pdf` (Teilnehmerausweis, erzeugt
  durch "Per E-Mail senden"). Regenerierbar, kein Geschaeftsdokument.
- 2.969 Nachrichten: 2.943 automatische Benachrichtigungen ("Notiz"),
  6 echte Kommentare, 20 E-Mails. Keine fachliche Korrespondenz mit Inhalt zu Veranstaltungen.

## 14. Datenmengen und Migrationsschluessel (Idempotenz)

Stabile fachliche Schluessel, keine alten Datenbank-IDs:

- Veranstaltung: `(name, date_begin, create_date)`. `(name, date_begin)` allein ist **nicht**
  eindeutig: 2 Paare kollidieren ("Webinar - Vorstellung Communex" 27.03.2024 13:00 und
  "Hinweisgeber-Portal Vorstellung" 31.01.2024 09:00). Namen allein kollidieren 23-fach
  ("Hinweisportal Vorstellung" 21 x).
- Teilnehmer: `(Veranstaltungsschluessel, E-Mail klein, create_date)`. Mehrfachanmeldungen
  derselben Person bleiben erhalten (38 Faelle).
- Kategorie: `name`.
- Kontakt: `(name, is_company)` mit Nachpruefung ueber E-Mail/UID; mehrdeutige Faelle werden
  vorgelegt, nicht geraten.
- Benutzer: `login`.

Erwartete Zielmengen: 122 Veranstaltungen, 760 Teilnehmer, 2 Kategorien, 5 Kategorie-Planer,
170 Planer, 758 Protokollzeilen.

## 15. Entscheidungspunkte

**E1 - Module in Odoo 18 (blockierend).** `event` ist nicht installiert. Fuer die 101
veroeffentlichten Veranstaltungen ist `website_event` erforderlich; fuer die Odoo-11-Funktion
"Teilnehmer per E-Mail" (mass_mailing_event) waere `mass_mailing_event` erforderlich.
Vorschlag: `event` + `website_event` + `mass_mailing_event` installieren
(`event_sale`, `website_event_track`, `website_event_sale` bleiben aussen vor - in Odoo 11
nicht installiert). `website_event_questions` gibt es in Odoo 18 nicht mehr als eigenes Modul
(Fragen sind Teil von `event`), 0 Fragen vorhanden.

**E2 - Kontakte (blockierend).** 23 der 29 referenzierten Kontakte fehlen in Odoo 18.
Optionen:
A) die 29 Kontakte im Zuge der Events-Migration vollstaendig nach den Kontaktregeln anlegen
   (Unternehmen/Person, Adresse, E-Mail, UID, Tags) - empfohlen, Vorarbeit fuer den Bereich
   Kontakte;
B) nur Minimal-Kontakte (Name, Typ, E-Mail) als Platzhalter anlegen;
C) Events erst nach der Kontaktmigration migrieren (Bereich bleibt dann offen).

**E3 - Status auf Phasen.** Odoo 18 kennt kein `state`. Vorschlag:
`draft` -> Neu, `confirm` -> Gebucht, `done` -> Beendet, `cancel` -> Abgebrochen.
Alternative: veroeffentlichte Veranstaltungen auf "Angekuendigt" (mischt zwei Dimensionen,
nicht empfohlen).

**E4 - Sichtbare Wortlaute.** Odoo 11 zeigt "Events", Odoo 18 "Veranstaltungen";
Odoo 11 "Anlasskategorie"/"Kategorie", Odoo 18 "Veranstaltungsvorlage";
Odoo 11 Teilnehmer-Status "Bestaetigt", Odoo 18 "Registriert".
Vorschlag: Menue "Events" (wie Odoo 11) und Feldlabel "Kategorie" beibehalten,
Statuswortlaut Odoo 11 ("Bestaetigt") sichtbar machen - Umsetzung per erbender View.

**E5 - Felder ohne Odoo-18-Gegenstueck.** `is_online` (120 Veranstaltungen),
`seats_min` (114), `auto_confirm` (2 x False). Vorschlag: `is_online` und `seats_min` als
technische Zusatzfelder im ITK-Modul nachbilden (sichtbar wie Odoo 11), `auto_confirm` nicht
nachbauen (Odoo 18 bestaetigt immer) und dokumentieren.

**E6 - Kein erneuter Versand (Sicherheitsauflage).** Alle 170 Planer mit `mail_done = True`
uebernehmen (stillgelegt), alle 758 Protokollzeilen mit `mail_sent = True` uebernehmen,
Cron "Event: Mail Scheduler" vor dem Import pausieren und nach der Pruefung wieder aktivieren.
Damit ist ein historischer Versand technisch ausgeschlossen.

**E7 - Chatter und Anhaenge.** Vorschlag: Chatter nicht migrieren (99 Prozent automatische
Systemnotizen), 6 Teilnehmerausweis-PDFs nicht migrieren (regenerierbar).
Alternative: die 6 echten Kommentare als Notiz uebernehmen.

**E8 - Berichtswesen.** Odoo 11 hat einen Pivot/Graph auf Veranstaltungen; Odoo 18 nur die
Teilnehmer-Analyse. Vorschlag: Pivot und Graph fuer Veranstaltungen im ITK-Modul als Ansicht
ergaenzen (keine Daten, nur Ansicht).

**E9 - Rechte.** Odoo-11-Gruppen ueber den Login abbilden: 41 Benutzer -> `group_event_user`,
28 -> `group_event_manager`; nur 8 der Manager-Logins existieren in Odoo 18, die uebrigen
werden als nicht zuordenbar dokumentiert (keine Benutzer werden angelegt).

**E10 - Menuezusatz.** Die Odoo-18-Menues "Veranstaltungsphasen" und "Stichwortkategorien"
haben in Odoo 11 kein Gegenstueck und bleiben als Odoo-18-Funktion erhalten (stoeren die
Odoo-11-Funktionalitaet nicht).

## 16. Bewusst nicht migrieren (Begruendung)

| Objekt | Menge | Begruendung |
|---|---|---|
| event.question / event.answer | 0 / 0 | keine Daten |
| twitter_hashtag | 0 belegt | in Odoo 18 durch Stichwoerter ersetzt |
| description, badges, event_logo | 0 belegt | keine Inhalte |
| origin | 0 belegt | Feld existiert in Odoo 18 nicht |
| date_open | 23 Abweichungen um 1 Sekunde | `create_date` traegt den Wert |
| Chatter (mail.message) | 2.969, davon 2.943 Systemnotizen | technische Versandprotokolle, keine Fachinhalte |
| Teilnehmerausweis-PDFs | 6 | regenerierbar |
| Menue "Fragestellungen" | Aktion ohne Daten | 0 Fragen |

---

## 17. Umsetzung (Session 138, 28.10.2026) - NUR Struktur und nicht personenbezogene Daten

**Auftragserweiterung von Anna (28.10.2026):** Keine Kontakte, Unternehmen, Personen,
Ansprechpartner, Teilnehmer und keine E-Mail-Adressen aus Odoo 11 uebernehmen. Keine
res.partner-Datensaetze anlegen, keine bestehenden Kontakte ueber Name/E-Mail
zusammenfuehren. Beziehungen, die auf noch nicht migrierte Kontakte zeigen, bleiben leer
und werden mit der Odoo-11-Kontakt-ID dokumentiert.

### 17.1 Umgesetzt

| Element | Umsetzung |
|---|---|
| Module | `event` 18.0.1.9 und `website_event` 18.0.1.4 installiert (lokal) |
| ITK-Modul | `itk_events_compat` 18.0.1.0.3 (Ansichten, Menues, Felder, Cron-Schutz) |
| Menues | App "Events" mit "Events", "Berichtswesen" (neu: "Events") und "Konfiguration > Anlasskategorien" |
| Status | Phasen tragen die Odoo-11-Bezeichnungen: Nicht bestätigt, Bestätigt, Angekündigt (Odoo-18-Zusatz), Erledigt, Abgebrochen |
| Felder | neu `x_is_online` (Online-Event), `x_seats_min` (Mindestzahl an Teilnehmern), technische Referenzen `x_o11_id`, `x_o11_state`, `x_o11_registrations`, `x_o11_organizer_id`, `x_o11_address_id` |
| Liste | Veranstaltungsname, Kategorie, Start-/Enddatum, Reservierungen, Max. Teilnehmeranzahl, Mindestzahl, Verantwortlich, Status |
| Suche | Filter Nicht bestätigt, Bestätigt, Erledigt, Abgebrochen; Gruppierung "Status" |
| Berichtswesen | Pivot und Graph auf Veranstaltungen (Kategorie x Status, Masse: Max. Teilnehmeranzahl, Mindestzahl) |
| Schutz | Cron "Event: Mail Scheduler" stillgelegt; alle uebernommenen Mailplaner `mail_done = True`; keine Odoo-18-Standardplaner an uebernommenen Veranstaltungen |

### 17.2 Datenmigration (nur nicht personenbezogene Daten)

| Objekt | Odoo 11 | Odoo 18 nach Migration |
|---|---|---|
| Anlasskategorien | 2 | 2 (Online, Physisches Event) |
| Veranstaltungen | 122 (121 aktiv, 1 archiviert) | 122 (121 aktiv, 1 archiviert) |
| Status | confirm 100, cancel 15, done 7 | Bestätigt 100, Abgebrochen 15, Erledigt 7 |
| Zeitzone | Europe/Berlin 122 | Europe/Berlin 122 |
| Veroeffentlichungsstatus | 101 veroeffentlicht | 101 veroeffentlicht |
| Online-Kennzeichen | 120 | 120 |
| Platzbegrenzung | 116 begrenzt | 116 begrenzt |
| Summe Mindestzahl | 552 | 552 |
| Anmeldungen (nur Zaehlwert) | 760 | 760 in `x_o11_registrations` |
| Mailplaner | 170 (130 ohne Versand) | 170, alle `mail_done = True` |
| **Kontakte** | 29 referenziert | **0 angelegt, 0 verknuepft** |
| **Teilnehmer** | 760 | **0 migriert** |

Zweiter Lauf: 0 Neuanlagen, 122 Aktualisierungen, 0 neue Mailplaner, 0 Standardplaner
(idempotent). Nachverknuepfungsliste: `docs/o11-o18-events-nachverknuepfung.csv`
(1.126 Zeilen: 122 Veranstaltungen, 122 Veranstalter, 122 Orte, 760 Teilnehmer - nur
Kennungen und Schluessel, keine Namen und keine E-Mail-Adressen).

### 17.3 Bewusste Abweichungen von Odoo 11 (dokumentiert)

1. **Veranstalter und Ort bleiben leer.** Odoo 18 setzt per Default den Firmenkontakt als
   Veranstalter und Ort ein; das wird bewusst ueberschrieben (`organizer_id = False`,
   `address_id = False`), weil die Odoo-11-Kontakte nicht migriert sind. Die Odoo-11-IDs
   stehen in `x_o11_organizer_id` / `x_o11_address_id`.
   Folge: der Odoo-18-Filter "Online" (Veranstaltungsort leer) trifft alle Veranstaltungen;
   das Odoo-11-Kennzeichen bleibt in `x_is_online` sichtbar.
2. **Status wird nicht automatisch auf "Erledigt" gesetzt.** Odoo 18 schiebt bei jedem
   Autovacuum-Lauf jede abgelaufene Veranstaltung in die Phase "Erledigt" und haette damit
   100 uebernommene Status ueberschrieben. Die Kernmethode `_gc_mark_events_done` ist im
   ITK-Modul so erweitert, dass Veranstaltungen mit Odoo-11-Referenz unangetastet bleiben;
   neue Odoo-18-Veranstaltungen werden weiterhin automatisch beendet. Nachweis: ein
   vollstaendiger Autovacuum-Lauf aendert die Verteilung 100/15/7 nicht.
3. **Kein Bestätigen-/Absagen-Button.** Odoo 18 fuehrt den Status ueber Phasen (Kanban,
   Statusleiste); die Odoo-11-Buttons entfallen funktionsbedingt.
4. **`auto_confirm` nicht nachgebaut.** Odoo 18 bestaetigt Anmeldungen immer; Odoo 11 hatte
   bei 2 Veranstaltungen `auto_confirm = False`.
5. **Kein Chatter, keine Anhaenge.** 99 Prozent der Odoo-11-Nachrichten sind automatische
   Systemnotizen; die 6 Teilnehmerausweis-PDFs sind regenerierbar.
6. **Rechte weichen ab (Odoo-18-Standard, nicht geaendert):** Odoo 11 erlaubte Benutzern
   nur Lesen von Veranstaltungen (`r1 w0 c0 u0`), Odoo 18 erlaubt Lesen, Schreiben und
   Anlegen (`r1 w1 c1 u0`), Loeschen nur Manager. Umgekehrt erlaubte Odoo 11 Benutzern
   volles Arbeiten an Teilnehmern und Mailplanern, Odoo 18 nicht. Eine Verengung haette
   Odoo-18-Standardablaeufe (Anmeldeschalter, Mailplanung) gebrochen; die Abweichung wird
   dokumentiert statt per Record Rule erzwungen. Entscheidung Anna offen.
7. **Mailversand ist aus.** Cron stillgelegt, bis der Bereich Kontakte/Teilnehmer migriert
   ist. Reaktivierung: `scripts/events_cron_schalten.py` (Folgeauftrag) bzw. Feld `active`.

### 17.4 Pruefungen (lokal, 28.10.2026)

| Pruefung | Ergebnis |
|---|---|
| `verify_s138_events.py --instanz lokal` | **61 OK / 0 FEHLER** |
| `browser_events_abnahme.py --instanz lokal` | **35 OK / 0 FEHLER** |
| `events_labels_de.py --instanz lokal` | 0 offen |
| Rechteprobe (`events_rechte.py --pruefen`) | Benutzer: lesen/schreiben/anlegen ja, loeschen nein; Manager: alles ja; Testdaten entfernt, Bestand 122 = 122 |
| Regression Personal (`verify_personal.py`) | 54 OK / 0 FEHL |
| Regression Projekt (`verify_s135_projekt.py`) | 20 OK / 0 FEHLER |
| Regression Urlaub/Anwesenheiten (`verify_s137_anwesenheiten.py`) | 3 Abweichungen, Ursache Odoo-11-Zuwachs (siehe 17.5) |
| Regression Zeiterfassung (`verify_s136_zeiterfassung.py`) | 2 Abweichungen, Ursache Odoo-11-Zuwachs (siehe 17.5) |

### 17.5 Regression: Ursache der Abweichungen

Die Pruefskripte vergleichen gegen den **Livebestand Odoo 11**, das weiter produktiv ist:

- Anwesenheiten: Odoo 11 fuehrt inzwischen **197** Zeilen, Odoo 18 hat **196**. Neu ist
  Odoo-11-Zeile 12691 (29.10.2026, 07:20 bis 14:40); Zeile 12686 ist in Odoo 11
  abgemeldet, in Odoo 18 noch offen (Stand der letzten Uebernahme). Summe Arbeitsstunden
  daher 1.221,72 gegen 1.228,23.
- Zeiterfassung: Stunden 2026 4.637,7 gegen 4.671,53 (Odoo-11-Zuwachs seit Session 137).
- Diese Differenzen entstehen ausschliesslich in hr.attendance/account.analytic.line; der
  Bereich Events schreibt nur in event.* und itk_events_compat. Nachzug mit den
  idempotenten Werkzeugen (`anwesenheiten_migration.py`, `zeiterfassung_migration.py`) vor
  einem Produktivstart, wie in der Uebergabe Session 137 festgehalten.
