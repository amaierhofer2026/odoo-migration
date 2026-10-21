# Bereich PERSONAL: Struktur- und Bestandsvergleich Odoo 11 gegen Odoo 18

Stand: 21.10.2026. Read-only-Erhebung; Odoo 11 (Produktiv, DB ITK_V1_a) wurde ausschliesslich
gelesen. In Odoo 18 wurde zu diesem Zeitpunkt nichts geaendert.

Werkzeuge: `scripts/hr_sofortbefund.py`, `scripts/hr_menuebaum.py`, `scripts/hr_erhebe_o11.py`,
`scripts/hr_erhebe_o18.py`, `scripts/hr_feldbelegung_o11.py`, `scripts/hr_detail_o11.py`,
`scripts/hr_detail_o18.py`, `scripts/hr_gerenderte_ansicht.py`, `scripts/hr_rechte.py`,
`scripts/hr_aktionen.py`, `scripts/hr_vergleichsbericht.py`.
Rohdaten (JSON) liegen ausserhalb des Repos in `%LOCALAPPDATA%\Temp\hr_erhebung\`.

## 1. Bestand Odoo 11 (Produktiv, read-only)

Module: `hr` 11.0.1.1, `hr_attendance` 11.0.2.0, `hr_holidays` 11.0.1.5,
`hr_org_chart` 11.0.1.0, `hr_timesheet` 11.0.1.0, `hr_timesheet_attendance` 11.0.1.0,
`hr_employee_firstname` 11.0.1.0.1.
**Kein** Vertragsmodell (`hr_contract` nicht installiert), **keine** Personalbeschaffung,
**keine** Lohnverrechnung.

Datensaetze:

- Mitarbeiter: 25 gesamt, davon 13 aktiv und 12 archiviert
- Abteilungen: 4, Stellen: 5, Stichwoerter (Tags): 2 (Namen identisch mit Odoo 18)
- Arbeitszeitmodelle: 9 (davon von Mitarbeitern genutzt: 6)
- Anwesenheiten: 192 (alle im Jahr 2026, alle fuer einen Mitarbeiter)
- Urlaubsantraege: 551 in 21 verwendeten Urlaubsarten, Jahre 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026,
  Zustaende confirm 1, refuse 21, validate 529, betroffene Mitarbeiter 21
- Urlaubsarten gesamt: 28
- Zeiterfassungszeilen mit Mitarbeiterbezug: 12.854 (Projekt-/Leistungszeiten)
- Benutzer: 62 (davon aktiv 58)

Menue (App "Personal", Menue-ID 110):

- `Personal/Personal` -> Aktion 126 (Mitarbeiterliste, Modus kanban,tree,form)
- `Personal/Abteilungen` -> Aktion 131 (Modus kanban,tree,form)
- `Einstellungen` (Menue 117) haengt an Menue 113, das **nicht mehr existiert** -> nicht sichtbar.
- Die Aktionen 124 (Mitarbeiterstruktur), 125 (Personal), 129 (Arbeitsstellen) sind in **keinem
  Menue** verlinkt, also fuer Benutzer nicht erreichbar.
- Eigene Apps daneben: "Anwesenheiten" (Check In/Check Out, Anwesenheitszeiten verwalten) und
  "Urlaubsanträge" (Mein Urlaubskonto, Zu bestaetigender Urlaub, Berichtswesen).

Ansichten hr.employee: 1 Formular (3 Reiter), 1 Liste (7 Spalten), 1 Kanban, 1 Suche
(4 Suchfelder, 3 Filter, 5 Gruppierungen). Formularaufbau siehe Abschnitt 4.

Rechte:

- Gruppe `Personal / Personalsachbearbeiter` (ID 13): Lesen/Schreiben/Anlegen/Loeschen auf
  Mitarbeiter, Abteilungen, Stellen, Tags.
- Gruppe `Personal / Mitarbeiter` (ID 1 = interner Benutzer): **nur Lesen** auf denselben Modellen.
- **Keine Datensatzregel** auf `hr.employee` -> jeder interne Benutzer sieht alle Mitarbeiter
  einschliesslich der Felder im Reiter "Private Informationen".
- Menue "Abteilungen" nur fuer Gruppe 13; Menue "Personal" fuer alle.

## 2. Ausgangszustand Odoo 18 (lokal, vor jeder Aenderung)

Module: 17 hr-Module installiert, u. a. `hr` 18.0.1.1, `hr_holidays` 18.0.1.6,
`hr_attendance` 18.0.2.0, `hr_org_chart`, `hr_timesheet`, `hr_employee_firstname` 18.0.1.0.0,
dazu Odoo-18-Zusaetze `hr_skills`, `hr_gamification`, `hr_hourly_cost`, `hr_holidays_public`.
**Kein** Vertragsmodell installiert (`hr_contract`/`hr.version` fehlen) - in Odoo 11 gibt es
ebenfalls keines, also kein Verlust.

Datensaetze:

- Mitarbeiter: 24 gesamt, davon 13 aktiv
- Abteilungen: 4, Stellen: 5, Tags: 2
- Arbeitszeitmodelle: 1 ("Standard 40 hours/week")
- Arbeitsorte: 3 (Home/Office/Other, Odoo-18-Standard)
- Anwesenheiten: 0, Abwesenheiten: 1, Zeiterfassungszeilen: 19
- Benutzer: 18

Der vorhandene Odoo-18-Mitarbeiterbestand ist eine **frueher angelegte Kopie des Odoo-11-Bestands**
(gleiche Namen, gleiche Arbeits-E-Mails), aber unvollstaendig und teilweise falsch:
uebernommen wurden Name, E-Mail, Barcode, PIN, Notiz eines Mitarbeiters; **verloren** gingen
Arbeitsadresse, Mobilnummern, Arbeitstelefonie (alle haben denselben Wert), Arbeitsorte,
Arbeitszeitmodelle (alle "Standard 40"), Manager-/Coach-Zuordnung (alle Coaches auf eine Person
gesetzt), Tag-Zuordnungen sowie einzelne Werte (Geschlecht, Abteilung, Barcode, PIN bei
Maierhofer Anna; Schreibfehler "Breitenender" statt "Breiteneder"; vertauschte Namensreihenfolge
"Miglar Daniel"; Osagie Jonathan aktiv statt archiviert). Ausserdem fehlt ein Mitarbeiter
(Meraner Daniel) und einer wurde nie angelegt (Buchinger Hannah existiert, aber ohne E-Mail).

Damit ist klar: der Odoo-18-Bestand ist Altbestand, der durch die Odoo-11-Daten ersetzt wird.

Menue (App "Mitarbeiter", Menue-ID 297): Mitarbeiter (Liste, Organigramm), Verzeichnis,
Abteilungen, Berichtswesen (Kompetenzen, Zertifizierungen), Konfiguration (Einstellungen,
Aktivitaetsplan, Arbeitsorte, Arbeitsplaene, Austrittsgruende, Kompetenzarten, Stellen,
Anstellungsarten, Abzeichen, Herausforderungen). Zusaetzlich eigene Apps "Anwesenheiten" und
"Abwesenheiten".

Formular hr.employee: 5 Reiter (Lebenslauf, Arbeitsinformationen, Erhaltene Abzeichen,
Private Informationen, Einstellungen). Kontakt und Position stehen im Kopfbereich **ohne**
Gruppenueberschriften. Das Feld `notes` ist vorhanden, aber **in keiner Ansicht** eingebaut.

Rechte (Odoo 18 Standard): `hr.employee` Lesen nur fuer `Mitarbeiter / Sachbearbeiter` (ID 52) und
Administration; der interne Benutzer (ID 1) hat nur Lesen auf `hr.employee.public`. Menue
"Abteilungen" ist fuer alle internen Benutzer sichtbar (Odoo 11: nur Personalsachbearbeiter).

## 3. Menuevergleich

| Odoo 11 | Odoo 18 | Bewertung |
|---|---|---|
| App "Personal" | App "Mitarbeiter" | anders benannt; Funktion gleich (Mitarbeiterliste) |
| Personal/Personal (Liste) | Mitarbeiter/Mitarbeiter/Mitarbeiter | 1:1 vorhanden |
| Personal/Abteilungen | Mitarbeiter/Abteilungen | 1:1 vorhanden |
| (nicht erreichbar) Arbeitsstellen | Mitarbeiter/Konfiguration/Personalbeschaffung/Stellen | O18-Zusatz, bleibt |
| (nicht erreichbar) Einstellungen | Mitarbeiter/Konfiguration/Einstellungen + Untermenues | O18-Zusatz, bleibt |
| - | Mitarbeiter/Verzeichnis | O18-Zusatz (oeffentliche Sicht), bleibt |
| - | Mitarbeiter/Organigramm | O11 hatte Organigramm im Formular; O18 zusaetzlich als Menue |
| - | Mitarbeiter/Berichtswesen (Kompetenzen, Zertifizierungen) | O18-Zusatz (hr_skills), bleibt |
| App "Anwesenheiten" (Check In/Out, Verwaltung) | App "Anwesenheiten" (Uebersicht, Verwaltung, Kioskmodus, Berichtswesen, Konfiguration) | funktional gleichwertig, O18 breiter |
| App "Urlaubsantraege" (Mein Urlaubskonto, Zu bestaetigender Urlaub, Berichtswesen) | App "Abwesenheiten" (Meine Zeit, Uebersicht, Verwaltung, Berichtswesen, Konfiguration) | funktional gleichwertig, O18 breiter |

## 4. Formularvergleich (Reiter)

| Odoo 11 | Inhalt | Odoo 18 | Bewertung |
|---|---|---|---|
| Reiter 1 "Arbeitsinformation" | Gruppe "Kontaktinformationen" (Arbeitsadresse, Arbeitsort, Arbeits-E-Mail, Handy, Telefon), Gruppe "Position" (Abteilung, Position, Manager, Ausbilder, Arbeitsstunden), danach Notizen "Weitere Informationen" | Kopfbereich ohne Ueberschriften (E-Mail, Telefon, Handy, Stichwoerter / Abteilung, Stelle, Manager, Coach) + Reiter "Arbeitsinformationen" (Standort, Genehmiger, Austritt, Arbeitsplan, Unterstellte) | **Abweichung**: Gruppenueberschriften fehlen, Notizenfeld fehlt, Arbeitsort als Auswahl statt Text |
| Reiter 2 "Private Informationen" | Wohnort & weitere Informationen (Nationalitaet, Identifikationsnummer, Ausweis, Bankverbindung), Kontaktinformationen (Privatadresse + Warnhinweis), Status (Geschlecht, Familienstand), Geburt (Geburtsdatum), Arbeitsbeitrag (Visa, Arbeitserlaubnis) | Reiter "Private Informationen" (Privater Kontakt, Staatsangehoerigkeit, Notfall, Ausbildung) | funktional gleichwertig, O18 breiter (Notfallkontakt, Ehepartner, Kinder, Ausbildung) |
| Reiter 3 "HR Einstellungen" | Status (Unternehmen ausgeblendet, Verknuepfter Benutzer), Zeiterfassung (Stundenlohn, ausgeblendet), Urlaubsantraege (Resturlaub, ausgeblendet) | Reiter "Einstellungen" (Status: Mitarbeitertyp, Verknuepfter Benutzer + Benutzer erstellen; Anwesenheit/Kassensystem: PIN, Ausweis; Anwendungseinstellungen: Stundenkosten) | funktional gleichwertig, O18 breiter |
| - | - | Reiter "Lebenslauf" (Kompetenzen, Lebenslauf) | O18-Zusatz aus hr_skills |
| - | - | Reiter "Erhaltene Abzeichen" | O18-Zusatz aus hr_gamification |
| Organigramm rechts im Formular | Unterstellte Mitarbeiter (Widget) | Reiter "Arbeitsinformationen", Gruppe rechts: Unterstellte (nur lesbar) + Menue Organigramm | funktional gleichwertig, Position anders |

Smart Buttons Odoo 11: "Zeiterfassungen" (Aktion 415), "Resturlaub" (Aktion 563, nur wenn
`show_leaves`), Archivieren-Knopf.
Smart Buttons Odoo 18: Resturlaub, Abwesenheit, Abwesenheits-Dashboard, Zeiterfassung,
Anwesenheitsstatus, Stunden letzter Monat, verknuepfte Kontakte, Organigramm, "Ueberstunden
abziehen", "Plan ausfuehren". Funktional eine Obermenge von Odoo 11.

## 5. Feldmapping Odoo 11 -> Odoo 18

| Odoo 11 Feld | verwendet | Odoo 18 Entsprechung | Status | empfohlene Aktion |
|---|---|---|---|---|
| firstname / lastname | 24 / 25 | firstname / lastname (hr_employee_firstname 18.0.1.0.0) | 1:1 vorhanden | uebernehmen, Reihenfolge im Titel bleibt wie O11 |
| name | 25 (berechnet) | name (berechnet aus Vor-/Nachname) | 1:1 vorhanden | nicht schreiben, O18 berechnet ihn |
| active | 13 aktiv / 12 archiviert | active | 1:1 vorhanden | Archivstand aus O11 uebernehmen |
| gender | 25 | gender (male/female/other) | 1:1 vorhanden | uebernehmen |
| marital | 24 | marital (single/married/cohabitant/widower/divorced) | 1:1 vorhanden | uebernehmen; O18 verlangt Pflichtwert, O11-Leerfall auf 'single' |
| birthday | 0 | birthday | 1:1 vorhanden | nichts zu uebernehmen |
| country_id (Nationalitaet) | 1 | country_id | 1:1 vorhanden | uebernehmen |
| identification_id | 0 | identification_id | 1:1 vorhanden | nichts zu uebernehmen |
| passport_id | 0 | passport_id | 1:1 vorhanden | nichts zu uebernehmen |
| visa_no / visa_expire / permit_no | 0 | visa_no / visa_expire / permit_no | 1:1 vorhanden | nichts zu uebernehmen |
| sinid (KV-Nummer) | 0 | sinid (AHV-Nummer) | 1:1 vorhanden | nichts zu uebernehmen (Feld leer) |
| ssnid (RV-Nummer) | 0 | ssnid (SV-Nummer) | 1:1 vorhanden | nichts zu uebernehmen (Feld leer) |
| bank_account_id | 0 | bank_account_id | 1:1 vorhanden | nichts zu uebernehmen (Feld leer) |
| address_id (Arbeitsadresse) | 25 | address_id (Arbeitsadresse) | 1:1 vorhanden | uebernehmen, Partner ueber Namen zuordnen |
| address_home_id (Privatadresse) | 1 | private_street/street2/zip/city/country_id + work_contact_id | Mapping noetig | O11-Adresse des Partners in die O18-Privatfelder schreiben |
| work_email | 24 | work_email | 1:1 vorhanden | uebernehmen (Schreibweise aus O11 gilt) |
| work_phone | 4 | work_phone | 1:1 vorhanden | uebernehmen (O18 hat derzeit bei allen denselben Wert) |
| mobile_phone | 5 | mobile_phone | 1:1 vorhanden | uebernehmen |
| work_location (Text) | 3 | work_location_id (hr.work.location) | Mapping noetig | Arbeitsorte aus den O11-Texten anlegen und zuordnen |
| notes (Weitere Informationen) | 1 | notes | 1:1 vorhanden, in O18 nicht im Formular | Feld in den Reiter Arbeitsinformationen aufnehmen |
| barcode (Signatur-ID) | 25 | barcode (Ausweis-ID) | 1:1 vorhanden | uebernehmen |
| pin | 25 | pin | 1:1 vorhanden | uebernehmen |
| department_id | 16 | department_id | 1:1 vorhanden | ueber Namen zuordnen |
| job_id (Position) | 15 | job_id (Stelle) | 1:1 vorhanden | ueber Namen zuordnen |
| parent_id (Manager) | 12 | parent_id (Manager) | 1:1 vorhanden | ueber zugeordneten Mitarbeiter setzen |
| coach_id (Ausbilder) | 0 | coach_id (Coach) | 1:1 vorhanden | nichts zu uebernehmen; O18-Daten enthalten falsche Werte, werden ersetzt |
| user_id (Verknuepfter Benutzer) | 24 | user_id (Verknuepfter Benutzer) | 1:1 vorhanden | nur verknuepfen, wo O18-Benutzer existiert (siehe Blocker B3) |
| company_id | 25 | company_id (Pflichtfeld) | 1:1 vorhanden | setzen |
| resource_calendar_id (Arbeitsstunden) | 25 (6 Modelle) | resource_calendar_id (Arbeitsstunden) | Mapping noetig | O11-Arbeitszeitmodelle anlegen und zuordnen (B4) |
| category_ids (Stichwoerter) | 10 | category_ids (Stichwoerter) | 1:1 vorhanden | ueber Tag-Namen zuordnen (2 Tags, Namen identisch) |
| timesheet_cost (Stundenlohn) | 0 | hourly_cost (Stuendliche Kosten) | anders benannt | nichts zu uebernehmen (Feld leer) |
| image / image_medium / image_small | technisch | image_1920 / image_128 / avatar_128 | anders benannt | Bild uebernehmen, falls vorhanden |
| attendance_ids | 1 Mitarbeiter | attendance_ids | 1:1 vorhanden | siehe Anwesenheiten (B2) |
| leaves_count / remaining_leaves | 17 | leaves_count / allocation_remaining_display | 1:1 vorhanden (berechnet) | nicht schreiben, O18 berechnet aus Abwesenheiten |
| current_leave_id / current_leave_state | 0 | current_leave_id (hr.leave.type) / current_leave_state | 1:1 vorhanden (berechnet) | nichts zu schreiben |
| is_absent_totay | berechnet | is_absent | anders benannt | kein Nachbau; O18-Filter 'In Abwesenheit' entspricht O11 'Heute abwesend' |
| is_address_home_a_company | 1 | entfallen (O18 fuehrt Privatadresse direkt) | obsolet | nicht nachbauen |
| manual_attendance | 24 | entfallen | obsolet | nicht nachbauen |
| child_all_count / child_ids | 2 | child_count / child_ids | 1:1 vorhanden | berechnet, nichts schreiben |
| message_* / __last_update | technisch | Chatter (chatter-Widget) | anders benannt | kein Nachbau |
| - | - | employee_type, job_title, departure_*, private_*, spouse_*, children, emergency_*, distance_home_work, certificate/study_*, work_permit_*, lang, tz, employee_properties, badges, skills | O18-Zusatz | behalten, nicht fuellen (fachlich sinnvolle Odoo-18-Funktionen) |

## 6. Suche, Filter, Gruppierung

| Odoo 11 | Odoo 18 | Bewertung |
|---|---|---|
| Suchfeld "Personal" (Name ODER Arbeits-E-Mail) | Suchfeld "Mitarbeiter" (Name ODER Arbeits-E-Mail) | 1:1, nur Beschriftung anders |
| Suchfeld Abteilung | Suchfeld Abteilung (+ Suchleiste links) | 1:1 vorhanden, O18 zusaetzlich Suchpanel |
| Suchfeld Stichwoerter | Suchfeld Stichwoerter | 1:1 vorhanden |
| Suchfeld Position | Suchfeld Stelle | 1:1, Wortlaut "Stelle" statt "Position" |
| Filter "Heute abwesend" | Filter "In Abwesenheit" / "Auf der Arbeit" | funktional gleich (Feld `is_absent_totay` -> `is_absent`) |
| Filter "Ungelesene Nachrichten" | Filter "Ungelesene Nachrichten" | 1:1 vorhanden |
| Filter "Archiviert" | Filter "Archiviert" | 1:1 vorhanden |
| Gruppierung Manager / Ausbilder / Abteilung / Arbeitsstelle | Gruppierung Manager / Abteilung / Stelle (+Startdatum, Stichwoerter) | **Ausbilder-Gruppierung fehlt in O18**, O18 hat zwei zusaetzliche Gruppierungen |
| Liste: Name, Telefon, E-Mail, Abteilung, Position, Manager | Liste: Name, Telefon, E-Mail, Abteilung, Stelle, Manager (+ Aktivitaetsdatum sichtbar) | funktional gleich; O18 zeigt zusaetzlich eine Aktivitaetsspalte |
| Kanban: Name, Position, Anwesenheitsstatus, Nachrichten | Kanban: Name, Stellenbezeichnung, E-Mail, Telefon, Stichwoerter, Benutzer, Aktivitaeten | funktional gleichwertig, O18 breiter |

## 7. Rechte und Rollen

| Punkt | Odoo 11 | Odoo 18 (Standard) | Bewertung |
|---|---|---|---|
| Mitarbeiter lesen | alle internen Benutzer (Gruppe 1) | nur HR-Sachbearbeiter (52); interne Benutzer nur `hr.employee.public` | **Abweichung (Datenschutz)** - Entscheidung noetig (B5) |
| Mitarbeiter bearbeiten | Personalsachbearbeiter (13) | HR-Sachbearbeiter (52) | 1:1 vorhanden |
| Abteilungen sehen | nur Personalsachbearbeiter (13) | alle internen Benutzer | **Abweichung** |
| Stellen sehen/bearbeiten | Gruppe 13 / Lesen fuer 1 | Gruppe 52 / kein Lesen fuer 1 | **Abweichung** |
| Private Felder | fuer alle internen Benutzer sichtbar | nur fuer HR-Gruppen | O18 datenschutzfreundlicher |
| Datensatzregeln Mitarbeiter | keine (nur Mehrfirmen-Regel) | nur Mehrfirmen-Regel | gleich |

## 8. Beziehungen zu anderen Modulen

| Beziehung | Odoo 11 | Odoo 18 | Status |
|---|---|---|---|
| Mitarbeiter -> Benutzer | 24 von 25 verknuepft, 62 Benutzer | 14 Mitarbeiter mit Benutzer, 18 Benutzer | **10 Mitarbeiter ohne Odoo-18-Benutzer** (B3) |
| Mitarbeiter -> Abteilung | 16 Mitarbeiter, 4 Abteilungen | 12 Mitarbeiter, 4 Abteilungen (Namen identisch) | ueber Namen zuordenbar |
| Mitarbeiter -> Stelle | 15 Mitarbeiter, 5 Stellen | 12 Mitarbeiter, 5 Stellen (Namen identisch) | ueber Namen zuordenbar |
| Mitarbeiter -> Manager | 12 Verknuepfungen | 12 Verknuepfungen (andere Personen) | ueber Mitarbeiterzuordnung neu setzen |
| Mitarbeiter -> Coach | 0 | 12 Verknuepfungen (falsch) | wird geleert/ersetzt |
| Mitarbeiter -> Arbeitszeitmodell | 6 Modelle genutzt (von 9) | 1 Modell | **Modelle muessen angelegt werden** (B4) |
| Mitarbeiter -> Arbeitsort | Textfeld, 3 Werte | 3 Odoo-18-Standardorte, keiner zugewiesen | Mapping noetig |
| Mitarbeiter -> Tags | 10 Mitarbeiter, Tag "IT-Kommunal GmbH" | 1 Mitarbeiter, gleiche 2 Tags | ueber Namen zuordenbar |
| Mitarbeiter -> Anwesenheiten | 192 (1 Mitarbeiter, 2026) | 0 | Migrationsentscheidung (B2) |
| Mitarbeiter -> Urlaubsantraege | 551 (21 Mitarbeiter, 2019-2026) | 1 | Migrationsentscheidung (B1/B2) |
| Mitarbeiter -> Zeiterfassung | 12.854 Zeilen mit Mitarbeiterbezug | 19 Zeilen | **ausserhalb dieses Bereichs** (Projekt/Zeiterfassung) (B6) |
| Mitarbeiter -> Kontakte | Arbeitsadresse = Partner | Arbeitsadresse = Partner, Arbeitskontakt automatisch | 1:1 vorhanden |
| Mitarbeiter -> Abrechnung | keine Verknuepfung | keine Verknuepfung | nicht betroffen |

## 9. Zuordnung der Mitarbeiter (Schluessel und Ergebnis)

Zuordnungsregel (in dieser Reihenfolge, Abbruch bei Mehrdeutigkeit):

1. **Arbeits-E-Mail** normalisiert (Kleinschreibung, Leerzeichen entfernt) - eindeutig bei 23 Mitarbeitern.
2. **Name** (Vor- und Nachname normalisiert) - fuer Mitarbeiter ohne E-Mail (1 Fall:
   Buchinger Hannah, in beiden Systemen ohne E-Mail und ohne Benutzer).
3. **Benutzer-Login** nur als Gegenprobe, nicht als Schluessel: Odoo 11 fuehrt bei
   Breiteneder Lorenz den Login `lorenz.galler@...`, Odoo 18 `lorenz.breiteneder@...` -
   der Login ist also **nicht** stabil.
4. Kein Schluessel: Datenbank-ID (Odoo 11 IDs 1..29, Odoo 18 IDs 1..27, keine gemeinsame Basis).

Ergebnis: **24 von 25** Odoo-11-Mitarbeitern haben einen eindeutigen Odoo-18-Partner
(23 ueber Arbeits-E-Mail, 1 ueber Name). **1 Mitarbeiter fehlt in Odoo 18** (Meraner Daniel) und
wird neu angelegt. **Kein** Odoo-18-Mitarbeiter bleibt ohne Odoo-11-Partner -> keine Loeschung
noetig, der Bestand wird feldweise ueberschrieben.

Namensabweichungen (mit Entscheidung, ohne Aenderung in Odoo 11):
Breiteneder Lorenz (O11) gegen Breitenender Lorenz (O18, Schreibfehler) - gleiche E-Mail;
Daniel Miglar (O11) gegen Miglar Daniel (O18) - gleiche E-Mail, Reihenfolge vertauscht.

## 10. Blocker und offene Entscheidungen

**B1 Urlaubsarten (28 in Odoo 11, 6 in Odoo 18).** Odoo 11 fuehrt 28 Urlaubsarten, davon 21
verwendet, mit Jahresnamen ("gesetzlicher Jahresurlaub 2020" bis 2026, doppelt vorhanden),
Tippfehlern ("Augleichstage", "Krankheitsstaende", "Arbeitssuchtag" zweimal) und Sonderfaellen
("Ausgleich der restlichen 9 Urlaubstage, die ausbezahlt wurden ..."). Odoo 18 hat 6 Standardarten.
Ohne Entscheidung kein verlustfreies Mapping der 551 Urlaubsantraege.

**B2 Umfang der Personaldaten.** 551 Urlaubsantraege (2019-2026, 529 genehmigt) und 192
Anwesenheiten (2026, ein Mitarbeiter) sind vorhanden. Ob diese Historie mitmigriert wird, ist eine
fachliche Entscheidung (Datenschutz, Aufwand, Aussagekraft).

**B3 Fehlende Odoo-18-Benutzer.** 24 Odoo-11-Mitarbeiter haben einen Benutzer. In Odoo 18 sind nur
14 davon verknuepft; fuer 10 Mitarbeiter existiert kein Benutzer: Koch Katharina, Steinecker Julia,
Vercimak Daniel, Horniak Guenter, Czarnecki Clemens, Buchinger Lorenz, Al Janabi Noor,
Miglar Daniel, Mohammad Fahad, Meraner Daniel. Bei Breiteneder Lorenz ist der Benutzer vorhanden,
hat aber einen anderen Login (`lorenz.breiteneder@` statt `lorenz.galler@`) - die Verknuepfung
bleibt ueber die Person erhalten. Benutzeranlage ist Stammdatenanlage und wird ohne Freigabe nicht
durchgefuehrt.

**B4 Arbeitszeitmodelle.** Odoo 11 hat 9 Modelle mit eigenen Arbeitszeiten, Odoo 18 nur eines.
6 Modelle werden von Mitarbeitern genutzt. Anlegen der fehlenden Modelle ist Stammdatenanlage.

**B5 Datenschutz/Sichtbarkeit.** Odoo 11 laesst jeden internen Benutzer alle Mitarbeiter samt
privaten Feldern sehen; Odoo 18 beschraenkt `hr.employee` auf HR-Gruppen. Beibehalten (O18-Stand)
oder angleichen (O11-Stand)?

**B6 Zeiterfassung.** 12.854 Zeiterfassungszeilen mit Mitarbeiterbezug haengen an Projekten,
Aufgaben und Leistungsarten, die im Bereich Projekt/Zeiterfassung noch nicht migriert sind.
Sie werden hier nicht mitgenommen.

**B7 Menue- und Wortlautfragen.** App-Name "Mitarbeiter" (O18) gegen "Personal" (O11);
Feldwortlaut "Stelle" (O18) gegen "Position" (O11); "Coach" (O18) gegen "Ausbilder" (O11).

## 11. Vorschlag fuer die Umsetzung (nach Freigabe)

1. Modul `itk_hr` (nur Ansichten, keine Daten): Gruppenueberschriften "Kontaktinformationen" und
   "Position" im Kopfbereich, Feld `notes` ("Weitere Informationen") im Reiter
   Arbeitsinformationen, Gruppierung "Ausbilder" in der Suche, Spalte Aktivitaetsdatum ausblenden.
2. Stammdaten: fehlende Arbeitszeitmodelle und Arbeitsorte anlegen (B4), Tags unveraendert.
3. Datenmigration Mitarbeiter: 24 Datensaetze feldweise aus Odoo 11 ueberschreiben, 1 neu anlegen;
   Beziehungen (Abteilung, Stelle, Manager, Arbeitszeitmodell, Tags, Arbeitsadresse) ueber
   fachliche Schluessel aufloesen; Benutzer nur verknuepfen, wo vorhanden (B3).
4. Urlaubsarten/Urlaubsantraege/Anwesenheiten erst nach Entscheidung B1/B2.
5. Pruefung: Anzahlvergleich, Stichproben, echter Browser lokal und VM, Regression.
 