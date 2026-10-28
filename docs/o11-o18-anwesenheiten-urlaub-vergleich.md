# Bereich ANWESENHEITEN und URLAUBSANTRÄGE / ABWESENHEITEN — Odoo 11 -> Odoo 18

Stand: 28.10.2026 (Session 137). Referenz: produktives Odoo 11 (`portal.it-kommunal.at`, DB `ITK_V1_a`),
**ausschliesslich lesend** verwendet. Ziel: `C:\Odoo-Test` (lokal) und `https://k001959vsx.ipax.at` (VM).

Ergebnis: **migrationsbereit, abgenommen**. Modul `itk_hr_leave_compat` 18.0.1.0.0.

---

## 1. Ausgangslage

| Punkt | Wert |
|---|---|
| Odoo-11-Module | `hr`, `hr_holidays` 11.0.1.5, `hr_attendance` 11.0.2.0, `hr_timesheet_attendance`; **kein** `hr_holidays_public` (nicht installiert) |
| Odoo-18-Module | `hr_holidays` 18.0.1.6, `hr_attendance` 18.0.2.0, `hr_holidays_public` 18.0.1.0.0, `itk_hr` 18.0.1.0.1 |
| Odoo-11-Bestand 28.10.2026 | 483 Anträge, 69 Ansprüche, 196 Anwesenheiten, 25 Mitarbeiter (13 aktiv, 12 archiviert) |
| Odoo-18-Bestand vor dieser Sitzung | 483 Anträge, 65 Ansprüche, 192 Anwesenheiten |

Der Bestand in Odoo 11 wächst weiter (zwischen 21.10. und 28.10.: +1 Antrag, +4 Anwesenheiten).
Vor jeder Migration wird er deshalb neu erhoben; die Migration ist idempotent.

---

## 2. Bestandsaufnahme Odoo 11

### 2.1 Menüs (vollständig)

App **Urlaubsanträge** (Gruppe "Mitarbeiter"):

| Menü | Aktion | Inhalt |
|---|---|---|
| Mein Urlaubskonto > Urlaubsantrag | 554 | eigene Anträge (`type=remove`), Filter "Meine Anträge" |
| Mein Urlaubskonto > Auswertung Urlaubskonto | 558 | Berichtsliste Anträge + Ansprüche |
| Mein Urlaubskonto > Urlaubsanspruch anfragen | 556 | eigene Ansprüche (`type=add`) |
| Zu bestätigender Urlaub > Urlaubsanträge | 560 | zu genehmigende Anträge (Gruppe Personalsachbearbeiter/Manager) |
| Zu bestätigender Urlaub > Urlaubsanspruch | 561 | zu genehmigende Ansprüche |
| Berichtswesen > Urlaubdetails | 559 | Anträge (Berichtsliste) |
| Berichtswesen > Urlaubsanträge | 574 | Anträge mit Filter Jahr/Typ |
| Berichtswesen > Urlaub nach Abteilung | 571 | Grafik/Pivot je Abteilung |

App **Anwesenheiten** (Gruppe "Anwesenheit manuell"):
- Check In / Check Out (Client-Aktion 318)
- Anwesenheitszeiten verwalten > Anwesenheiten (Aktion 313, Liste/Kanban/Formular)

App **Personal**: Personal (Aktion 126), Abteilungen (Aktion 131) — bereits abgenommen (Session 134).

### 2.2 Modelle und Felder

`hr.holidays` (43 Felder) — belegt in Klammern (von 552 Datensätzen):

`name` = "Beschreibung" (360), `holiday_status_id` = "Abwesenheitstyp" (552), `type` (552, `remove`/`add`),
`holiday_type` (552, `employee`/`category`), `employee_id` (551), `category_id` (1),
`department_id` (468), `state` (552), `date_from`/`date_to` (483), `number_of_days` ("Anzahl der Tage", 535),
`number_of_days_temp` (535), `notes` (1), `report_note` (0), `payslip_status` (0), `double_validation` (0),
`manager_id` (390), `user_id` (551), `first_approver_id` (548), `second_approver_id` (21),
`create_*`/`write_*` (552), `parent_id` (0), `meeting_id` (467).

`hr.holidays.status` (28 Datensätze): `name`, `limit` (5x wahr), `color_name`, `active`.

`hr.attendance` (13 Felder): `employee_id`, `check_in` = "Check In", `check_out` = "Check Out",
`worked_hours` = "Arbeitsstunden", `department_id` und das **Studio-Feld `x_homeoffice`** ("Home-Office",
116x wahr, 80x falsch).

### 2.3 Ansichten und Suche

- Formular `hr.holidays.form` (1419): Kopf mit Aktionen Bestätigen/Genehmigen/Zurücksetzen, Statusleiste
  draft/confirm/validate, Felder Beschreibung, Abwesenheitstyp, Dauer, Von/Bis, Modus, Mitarbeiter,
  Kategorie, Abteilung, Notizen (nur Ansprüche), Chatter.
- Liste `hr.holidays.tree` (1425): Mitarbeiter, Modus, Abwesenheitstyp, Beschreibung, Von, Bis,
  **Anzahl der Tage (Summe "Resturlaub")**, Status, Payslip-Spalte; Zeilenfarbe rot bei `refuse`.
- Kanban (1423) mit Mitarbeiterbild, Statuslabel, Zeitraum, Tages-Badge; Kalender (1418).
- Ansprüche: `hr.holidays.allocation.tree` (1420/1421), Berichtslisten (1422/1424), Pivot/Graph (1442/1443).
- Suche (1417): Filter "Zur Genehmigung" (`confirm`,`validate1`), "Genehmigter Urlaub", "Aktive Typen",
  "Ungelesene Nachrichten", "Urlaube meiner Abteilung", "Mein Teamurlaub", "In Personalabrechnung
  anzuzeigen", "Zu erledigen", "Aktuelles Jahr", "Meine Anträge", "Urlaubsanträge", "Urlaubsansprüche";
  Gruppierung nach Beschreibung, Mitarbeiter, Kategorie, Manager, Prüfer, Typ, Startmonat.
- Anwesenheiten: Liste/Formular/Kanban (703-705) mit `x_homeoffice`; Suche (706) mit Heute,
  Aktueller Monat, Kein Check Out, Meine Anwesenheiten, Gruppierung Mitarbeiter/Monat; Pivot/Graph (707/708).

### 2.4 Rechte und Datensatzregeln

| Gruppe | Mitglieder | Wirkung |
|---|---|---|
| 34 "Anwesenheit manuell" | 24 | Anwesenheiten lesen/schreiben/anlegen (nur eigene Zeiten laut Regel 69/141), kein Löschen |
| 32 "Aufsicht" | 5 | Vollzugriff Anwesenheiten (Regel 68) |
| 79 "Personalsachbearbeiter" | 29 | `hr.holidays` Vollzugriff (Zugriff 738), alle Anträge (Regel 138) |
| 80 "Manager" | 5 | zusätzlich `hr.holidays.status` Vollzugriff (Zugriff 741) |
| 1 "Mitarbeiter" | 44 | eigene Anträge anlegen/ändern (Zugriff 739, Regeln 136/137), Urlaubsarten nur lesen |

### 2.5 Daten

- 483 Anträge: 529 `validate`, 21 `refuse`, 2 `confirm` (davon 1 Anspruch).
- 69 Ansprüche: 1 Kategorie-Anspruch (ID 7, 25 Tage, kein Mitarbeiter), 2 mit 0 Tagen (IDs 65, 582),
  1 doppelter 25-Tage-Anspruch (Würrer Florian, IDs 67 und 142).
- 17 Anträge mit 0 Tagen (Krankmeldungen, Zeiträume ohne verrechenbare Arbeitszeit).
- 141 Anträge von ausgeschiedenen Mitarbeitern (121 davon auf die 9 archivierten Mitarbeiter mit Anträgen).
- Anwesenheiten: 196 Zeilen, alle von Maierhofer Anna, 2026, 116 mit Home-Office, 1 offene Zeile (28.10.).
- Odoo 11 kennt **keinen** Feiertagskalender (Modul `hr_holidays_public` nicht installiert).

---

## 3. Bestandsaufnahme Odoo 18 vor der Arbeit und gefundene Lücken

| Befund | Detail | Kategorie |
|---|---|---|
| L1 | Home-Office fehlte vollständig (kein Feld, keine Spalte) | muss nachgebaut werden |
| L2 | Beschreibung aus Odoo 11 war verloren (Odoo 18 `name` ist berechnet) | muss nachgebaut werden |
| L3 | Tagesanzahl aus Odoo 11 nicht gespeichert (Odoo 18 rechnet neu) | muss nachgebaut werden (Belegfeld) |
| L4 | App heisst "Abwesenheiten", Menüs "Meine Zeit/Verwaltung" statt Odoo-11-Namen | muss angepasst werden |
| L5 | Anwesenheiten: "Anmeldung/Abmeldung" statt "Check In/Check Out" | muss angepasst werden |
| L6 | Filter "Zur Genehmigung", "Aktive Typen", "Urlaube meiner Abteilung", "Mein Teamurlaub", Gruppen Manager/Prüfer fehlten | muss nachgebaut werden |
| L7 | Interne Benutzer durften Anwesenheiten nur lesen (Odoo 11: eigene Zeilen pflegen) | muss nachgebaut werden |
| L8 | Würrer-Anspruch 25,0 Tage fehlte (als "Dublette" übersprungen) | Datenfehler, korrigiert |
| L9 | 23 (lokal) bzw. 34 (VM) Zeiterfassungszeilen ohne Abwesenheitsbezug | Schnittstelle, korrigiert |
| L10 | fremder Odoo-18-Testantrag (Administrator / Bezahlte Abwesenheit) | Testdaten, entfernt |
| L11 | Arbeitsstunden lokal um 1 Stunde zu niedrig (183 Zeilen, Zeitzone des Arbeitsplans) | Datenfehler, korrigiert |
| L12 | offene Anmeldung 21.10. blockierte neue Zeilen | Datenfehler, korrigiert |

---

## 4. Mapping Odoo 11 -> Odoo 18

### 4.1 Muss nachgebaut / angepasst werden (umgesetzt)

| Odoo 11 | Odoo 18 | Umsetzung |
|---|---|---|
| `x_homeoffice` (Boolean, "Home-Office") | Feld `x_homeoffice` an `hr.attendance` | Modul: Feld, Listenspalte, Formularfeld, Suchfilter |
| `name` ("Beschreibung") | `private_name` (gespeichert, "Beschreibung") | Migration schreibt den Odoo-11-Text |
| `number_of_days_temp` ("Anzahl der Tage") | Feld `x_o11_number_of_days` (schreibgeschützt) | Belegfeld, Spalte und Formularfeld |
| App "Urlaubsanträge" | App-Menü umbenannt | `hr_holidays.menu_hr_holidays_root` |
| "Mein Urlaubskonto", "Urlaubsantrag", "Urlaubsanspruch anfragen", "Zu bestätigender Urlaub", "Urlaubsanträge", "Urlaubsanspruch", "Urlaubdetails" | Menüs umbenannt | Modul + de_DE-Slots |
| "Auswertung Urlaubskonto", "Urlaubsanträge" (Bericht), "Urlaub nach Abteilung" | neue Aktionen/Menüs | Modul |
| Spalten "Check In"/"Check Out", "Abwesenheitstyp" | Spaltenbeschriftung | Modul |
| Filter "Zur Genehmigung", "Aktive Typen", "Ungelesene Nachrichten", "Urlaube meiner Abteilung", "Mein Teamurlaub" | neue Suchfilter | Modul |
| Gruppierung "Abteilung", "Manager", "Prüfer" | neue Gruppierungen | Modul |
| Gruppe 34 "Anwesenheit manuell" | neue Gruppe + Zugriffsrecht + Datensatzregel "nur eigene" | Modul, Mitglieder per Skript |
| Gruppe 79/80 | `hr_holidays.group_hr_holidays_user` / `_manager` | Mitglieder per Skript |

### 4.2 Odoo-18-Zusatzfunktionen, die erhalten bleiben

Dashboard/Übersicht, Verwaltung (Sammelliste), Konfiguration (Abwesenheitsarten, Rückstellungspläne,
gesetzliche Feiertage, Tage mit Anwesenheitspflicht), Saldo-Bericht, Feiertags-App, Kioskmodus,
Überstunden-Genehmigung, Aktivitäten, Chatter, Halbtage/Stunden als Antragseinheit, mehrstufige
Genehmigung (`validate1`), Abwesenheitsarten mit Anspruchspflicht, Arbeitsorte.

### 4.3 Technisch anders, fachlich gleichwertig

| Odoo 11 | Odoo 18 | Anmerkung |
|---|---|---|
| ein Modell `hr.holidays` mit `type=remove/add` | `hr.leave` und `hr.leave.allocation` | Menüs und Filter ersetzen die Typ-Trennung |
| `holiday_type` (`employee`/`category`) | nur persönliche Ansprüche | Kategorie-Anspruch nicht übertragbar (4.4) |
| `number_of_days` (gespeichert, ohne Neuberechnung) | `number_of_days` berechnet, `duration_display` | Dauer nach Odoo-18-Logik (Abschnitt 7) |
| `state` draft/confirm/validate1/validate/refuse/cancel | confirm/validate1/validate/refuse/cancel (kein `draft`) | Odoo 11 hatte 0 Datensätze in `draft` |
| "Mein Teamurlaub" über `employee_id.parent_id.user_id` | Odoo-18-Filter "Mein Team" über `leave_manager_id` | beide Filter vorhanden |
| Check In/Check Out als Menüpunkt | Uhr in der Kopfleiste + Kioskmodus | kein Menüeintrag nötig |
| `worked_hours` = reine Zeitdifferenz | `worked_hours` aus Arbeitsplan berechnet | Werte identisch (Summe 1.221,72 h) |
| Gruppierung "Beschreibung" | nicht möglich (`name` ist berechnet) | Suche über Beschreibung funktioniert |

### 4.4 Nicht übertragbar (begründet, dokumentiert)

| Odoo-11-Objekt | Grund | Behandlung |
|---|---|---|
| Kategorie-Anspruch ID 7 (25 Tage, `holiday_type=category`, Mitarbeiter-Tag "IT-Kommunal GmbH") | Odoo 18 kennt keine Kategorie-Ansprüche | nicht angelegt, in Odoo 11 unverändert; Nachweis in `docs/o11-o18-personal-migration.md` Abschnitt 4 |
| Ansprüche ID 65 (Breiteneder, 0 Tage) und ID 582 (Mohammad, 0 Tage) | Odoo 18 verlangt Dauer > 0 (SQL-Constraint) | nicht angelegt, dokumentiert |
| `payslip_status`, `report_note`, `double_validation`, `parent_id` | in Odoo 11 zu 0 % belegt | nicht nachgebaut |
| `category_id`-Gruppierung | Feld existiert in Odoo 18 nicht | entfällt |
| `meeting_id` (467 Kalendereinträge) | Odoo 18 legt bei gebuchten Abwesenheiten eigene Kalendereinträge an | keine 1:1-Übernahme der Odoo-11-Event-IDs |
| Listentitel "Mitarebeiter-Anwesenheiten" (Tippfehler in Odoo 11) | Tippfehler | Odoo 18: "Mitarbeiteranwesenheiten" |

---

## 5. Umsetzung

### 5.1 Modul `addons/itk_hr_leave_compat` (18.0.1.0.0)

- `hr.attendance.x_homeoffice` (Boolean, "Home-Office"), Listenspalte (abwählbar), Formularfeld,
  Suchfilter "Home-Office" (Odoo-18-Zusatz).
- `hr.leave.x_o11_number_of_days` (Float, "Anzahl der Tage (Odoo 11)", schreibgeschützt):
  Liste (abwählbar, Summe), Formular (nur wenn > 0), Berichtsliste "Urlaubdetails".
- Menüs: App "Urlaubsanträge", Gruppen "Mein Urlaubskonto", "Zu bestätigender Urlaub", "Berichtswesen"
  mit den Odoo-11-Einträgen; Anwesenheiten: "Anwesenheiten", "Anwesenheits-Analyse".
- Suche: Odoo-11-Filter und -Gruppierungen zusätzlich zu den Odoo-18-Filtern.
- Gruppe "Anwesenheit manuell" mit `ir.model.access` (lesen/schreiben/anlegen, kein Löschen) und
  Datensatzregel `employee_id.user_id = user.id`.
- de_DE-Slots der Menüs/Aktionen über `scripts/anwesenheiten_labels_de.py` (der Modul-Record setzt nur
  den Basistext, die Oberfläche liest de_DE).

### 5.2 Rechte (Skript `scripts/anwesenheiten_rechte.py`)

Zuordnung ausschliesslich über den Login (keine Benutzer-IDs):

| Odoo-11-Gruppe | Odoo-18-Gruppe | gesetzt |
|---|---|---|
| 34 "Anwesenheit manuell" (24) | `itk_hr_leave_compat.group_itk_anwesenheit_manuell` | 22 Benutzer (2 ohne Odoo-18-Konto: `admin`, `lorenz.galler@`) |
| 32 "Aufsicht" (5) | `hr_attendance.group_hr_attendance_manager` | 3 Benutzer (1 ohne Konto, 1 schon vorhanden) |
| 79 "Personalsachbearbeiter" (29) | `hr_holidays.group_hr_holidays_user` | 8 Benutzer (19 Odoo-11-Konten sind Kunden-/Sammel-Logins ohne Odoo-18-Benutzer) |
| 80 "Manager" (5) | `hr_holidays.group_hr_holidays_manager` | 4 Benutzer |

Nach der Zuordnung: Gruppe "Anwesenheit manuell" 12 aktive Benutzer (22 inkl. der 10 archivierten).

---

## 6. Datenmigration

Aufruf: `python scripts/anwesenheiten_migration.py --instanz lokal|vm [--ausfuehren --ich-habe-freigabe]`
(Trockenlauf ist Standard; Protokoll unter `%LOCALAPPDATA%\Temp\anwesenheiten_migration`).

| Objekt | Odoo 11 | Odoo 18 | Ergebnis |
|---|---|---|---|
| Urlaubsanträge | 483 | **483** | 0 fehlend, 0 doppelt |
| Urlaubsansprüche | 69 | **66** | 3 nicht übertragbar (Abschnitt 4.4) |
| Anwesenheiten | 196 | **196** | 0 fehlend, 0 doppelt |
| Home-Office | 116 | **116** | Feld neu gefüllt |
| Summe Anspruchstage (übertragbar) | 1.231,16 | **1.231,16** | identisch |
| Summe Antragstage | 1.092,42 | 1.156,00 | +63,58 (Abschnitt 7) |
| Summe Arbeitsstunden | 1.221,72 | **1.221,72** | identisch |

Zugeordnet wird über fachliche Schlüssel: Mitarbeiter über Arbeits-E-Mail (Fallback Name),
Abwesenheitsart über den Namen, Anträge über Mitarbeiter + Art + Zeitraum (Multimenge, damit
gleichlautende Datensätze erhalten bleiben), Anwesenheiten über Mitarbeiter + Check-in.
Keine Zuordnung über Datenbank-IDs.

### 6.1 Sonderfälle

| Fall | Umfang | Lösung |
|---|---|---|
| Abwesenheit #87 (VM) / #1090 (lokal), Koch Katharina, 01.-15.06.2021 | 1 Datensatz + 11 Zeiterfassungszeilen | Odoo 11: `validate`. VM stand auf `confirm`, weil der Status beim ersten Lauf nicht geschrieben wurde (die Migration überspringt vorhandene Datensätze vor dem Statusschreiben). Status jetzt `validate`; die 11 Zeiterfassungszeilen haben ihren Bezug erhalten. |
| Neuer Antrag 711 (Blagojevic, 26.-30.10.2026) | 1 | nachgezogen, Status `confirm` ("Zu genehmigen") wie in Odoo 11 |
| Gleichnamige Ansprüche (Würrer 25,0 Tage zweimal) | 1 | beide angelegt (Odoo 18 erlaubt Mehrfachansprüche); vorher fehlte einer |
| 0-Tage-Ansprüche | 2 | nicht übertragbar (Odoo-18-Constraint) |
| 0-Tage-Anträge | 17 | unverändert übernommen |
| Überschneidende Anträge (Waiss 16.-22.07.2023, Tiefling 12.02.2025) | 2 | mit `leave_skip_date_check` nur im Anlage-Aufruf übernommen |
| Archivierte Mitarbeiter | 121 Anträge | vollständig übernommen, Mitarbeiter bleiben archiviert |
| Offene Anwesenheit (28.10., kein Check Out) | 1 | als offene Zeile übernommen |
| Arbeitsstunden lokal 1 Stunde zu niedrig | 183 Zeilen | Neuschreiben von `check_in` rechnet mit dem gesetzten Zeitzonenfeld neu (5,0836 -> 6,0836) |
| Fremder Testantrag Odoo 18 | 1 | entfernt (Art "Bezahlte Abwesenheit" existiert in Odoo 11 nicht) |

---

## 7. Tagesanzahl und Resturlaub (fachliche Entscheidung 28.10.2026)

**Entscheidung (Anna):** Die Odoo-18-Berechnungslogik bleibt bestehen. Es werden **keine** künstlichen
Ausgleichsansprüche und keine erfundenen Werte erzeugt. Die Odoo-11-Werte bleiben nachvollziehbar.

Umsetzung:
- Odoo 18 rechnet die Dauer aus Zeitraum, Arbeitsplan und Abwesenheitsart (`number_of_days`, `duration_display`).
- Der in Odoo 11 gespeicherte Wert steht schreibgeschützt in **`x_o11_number_of_days`** und ist im
  Formular ("Anzahl der Tage (Odoo 11)") und in der Liste abrufbar.
- Resturlaube in Odoo 18 rechnen mit dem Odoo-18-Wert. Die Odoo-11-Salden sind über das Belegfeld
  nachrechenbar, werden aber nicht numerisch nachgebaut.

**Umfang:** 141 von 483 Anträgen weichen ab; Summe Odoo 11 400,42 Tage gegen Odoo 18 464,00 Tage
(Differenz +63,58 Tage). Vollständige Liste mit Odoo-11- und Odoo-18-Wert, Mitarbeiter, Art, Zeitraum,
Status und Beschreibung: **`docs/o11-o18-anwesenheiten-tagesabweichungen.csv`** (141 Zeilen,
Trennzeichen `;`).

Ursachen (belegt, nicht geraten):
1. Odoo 11 rechnete die Dauer über Arbeitsstunden und zog dabei bereits gebuchte Abwesenheiten im
   Zeitraum ab (`get_work_days_data(compute_leaves=True)`), Odoo 18 zählt Arbeitstage des Zeitraums.
   Folge: krumme Odoo-11-Werte wie 0,67 oder 2,5 Tage.
2. Ein Teil der Odoo-11-Werte ist veraltet: sie wurden beim Anlegen mit dem damaligen Arbeitsplan
   berechnet und danach nicht neu erzeugt (z. B. Koch 01.-15.06.2021: 10 statt 11 Arbeitstage).
3. Odoo 11 führt keinen Feiertagskalender; Odoo 18 kann Feiertage je Art berücksichtigen
   (`include_public_holidays_in_duration`), der Bestand ist aber leer.
4. Halbtage: Odoo 11 speicherte 0,5 für einzelne Tage, Odoo 18 zählt den ganzen Arbeitstag, wenn kein
   Halbtagsantrag vorliegt.

Verteilung: 14 Mitarbeiter, 18 Abwesenheitsarten; grösste Abweichungen Waiss Martina (29 Fälle,
-9,25 Tage), Steinecker Julia (23 Fälle, +22,00), Pellkvist Tobias (12 Fälle, +25,00).

---

## 8. Prüfungen (28.10.2026)

| Prüfung | lokal | VM |
|---|---|---|
| `verify_s137_anwesenheiten.py` (Struktur, Daten, Rechte, Sonderfälle) | **65 OK / 0 FEHLER** | **65 OK / 0 FEHLER** |
| `browser_anwesenheiten_abnahme.py` (echter Chrome) | **28 OK / 0 FEHLER** | **28 OK / 0 FEHLER** |
| `verify_personal.py` (Referenz 196/66 angepasst) | 54 OK / 0 FEHL | 54 OK / 0 FEHL |
| `verify_s135_projekt.py` | 20 OK / 0 FEHLER | 20 OK / 0 FEHLER |
| `verify_s136_zeiterfassung.py` | 81 OK / 0 FEHLER | 81 OK / 0 FEHLER |
| `abschluss_verkauf_regression.py` (11 Prüfläufe, lokal und VM) | 881 OK / 0 FEHL | enthalten |
| `anwesenheiten_labels_de.py` | 0 offen | 0 offen |
| `anwesenheiten_rechte.py` | 0 offen | 0 offen |

Browserabnahme im Detail (je Instanz): App-Name "Urlaubsanträge", Menüleiste mit Mein Urlaubskonto /
Übersicht / Zu bestätigender Urlaub / Berichtswesen / Konfiguration / Feiertage, Urlaubdetails 483 Zeilen
mit Spalte "Abwesenheitstyp", Filter "Zur Genehmigung" = 1, Suche "Sommerurlaub" = 6 (migrierte
Beschreibung), Gruppierung nach Abwesenheitstyp = 11 Gruppen, Formular Koch mit Status "Genehmigt",
Dauer 11 Tage und "Anzahl der Tage (Odoo 11)" = 10, Anwesenheiten 196 Zeilen mit Spalten Check In /
Check Out / Home-Office, Filter Home-Office = 116, Rechteprüfung mit Testbenutzer (sieht nur eigene
Zeile, darf eigene anlegen, fremde nicht ändern, danach gelöscht).

Testdaten: keine Reste (0 Benutzer `hermes*`, 0 Mitarbeiter `Hermes*`, 0 Anträge auf "Administrator",
0 Anträge der Art "Bezahlte Abwesenheit"), lokal und VM.

---

## 9. Werkzeuge

| Datei | Zweck |
|---|---|
| `scripts/anwesenheiten_migration.py` | Datenmigration/Nachzug (Trockenlauf Standard) |
| `scripts/anwesenheiten_rechte.py` | Odoo-11-Gruppen auf Odoo-18-Gruppen abbilden |
| `scripts/anwesenheiten_labels_de.py` | de_DE-Slots der Menüs/Aktionen setzen und prüfen |
| `scripts/anwesenheiten_zeiterfassung_bezug.py` | Abwesenheitsbezug der Zeiterfassung nachziehen (Schnittstelle) |
| `scripts/verify_s137_anwesenheiten.py` | Abnahme Struktur und Daten |
| `scripts/browser_anwesenheiten_abnahme.py` | Browserabnahme (Chrome) |
| `docs/o11-o18-anwesenheiten-tagesabweichungen.csv` | Liste der 141 Tagesabweichungen |

---

## 10. Abnahmestatus

**Bereich Anwesenheiten und Urlaubsanträge: ABGENOMMEN und GESPERRT (28.10.2026).**

Ab jetzt keine Änderungen mehr an diesem Bereich ohne neuen Auftrag. Offene Punkte ausserhalb des
Bereichs: siehe `docs/uebergabe-session-137.md`.
