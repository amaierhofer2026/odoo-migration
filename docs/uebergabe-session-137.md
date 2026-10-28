# Uebergabe Session 137 -> 138

Stand: 28.10.2026. Diese Datei ist der Einstieg fuer die naechste Session.

## 1. Ergebnis dieser Session

**Bereich ANWESENHEITEN und URLAUBSANTRAEGE: ABGENOMMEN und GESPERRT.**

- Odoo-11-Bestand live neu erhoben (read-only): **483 Antraege, 69 Ansprueche,
  196 Anwesenheiten**, 25 Mitarbeiter (13 aktiv, 12 archiviert), Home-Office 116.
- Nach Odoo 18 migriert: **483 Antraege, 66 Ansprueche** (3 nicht uebertragbar),
  **196 Anwesenheiten**, **Home-Office 116**.
- Summe Anspruchstage 1.231,16 = 1.231,16; Summe Arbeitsstunden 1.221,72 = 1.221,72.
- Tagesanzahl folgt der Odoo-18-Logik; der Odoo-11-Wert steht in
  `x_o11_number_of_days`. 141 Abweichungen dokumentiert (CSV).
- Neues Modul `itk_hr_leave_compat` 18.0.1.0.0: Odoo-11-Menues, Home-Office,
  Tage (Odoo 11), Odoo-11-Suchfilter, Gruppe "Anwesenheit manuell".

Pruefzahlen (alle lokal **und** VM):

| Pruefung | Ergebnis |
|---|---|
| `verify_s137_anwesenheiten.py` | 65 OK / 0 FEHLER |
| `browser_anwesenheiten_abnahme.py` | 28 OK / 0 FEHLER |
| `verify_personal.py` | 54 OK / 0 FEHL |
| `verify_s135_projekt.py` | 20 OK / 0 FEHLER |
| `verify_s136_zeiterfassung.py` | 81 OK / 0 FEHLER |
| `abschluss_verkauf_regression.py` | 881 OK / 0 FEHL (11 Prueflaeufe, lokal und VM) |

## 2. Nachtrag Zeiterfassung (Schnittstelle, keine Struktur-Aenderung)

Odoo 11 ist weiter produktiv; die Zeiterfassung ist mit dem idempotenten Werkzeug
nachgezogen: **12.936 Zeilen, 16.851,14 h** (Session 136: 12.917 / 16.832,47).
Zusaetzlich wurde der **Abwesenheitsbezug** nachgezogen (neues Werkzeug
`scripts/anwesenheiten_zeiterfassung_bezug.py`, lokal 23 Zeilen, VM 33 Zeilen).
Damit ist der Punkt "Abwesenheit #87 / Zeilen ohne Bezug" geschlossen.

## 3. Fall Abwesenheit #87 (geloest)

Odoo 11 Datensatz 168 (Koch Katharina, 01.-15.06.2021, `validate`, 10 Tage nach
Odoo-11-Rechnung). Odoo 18: lokal #1090 `validate`, VM #87 war `confirm`.
Ursache: die Migration prueft "vorhanden" vor dem Statusschreiben und ueberspringt den
Datensatz danach dauerhaft. Status jetzt auf der VM `validate`; die 11 zugehoerigen
Zeiterfassungszeilen haben ihren Bezug.

## 4. Fachliche Entscheidung zur Tagesanzahl (Anna, 28.10.2026)

- Odoo-18-Berechnungslogik bleibt bestehen.
- Keine kuenstlichen Ausgleichsansprueche, keine erfundenen Werte.
- Odoo-11-Werte bleiben im Feld `x_o11_number_of_days` nachvollziehbar.
- 141 Abweichungen (Summe +63,58 Tage) dokumentiert:
  `docs/o11-o18-anwesenheiten-tagesabweichungen.csv`.

Ursachen der Abweichungen: Odoo 11 rechnete die Dauer ueber Arbeitsstunden und zog
bereits gebuchte Abwesenheiten ab (krumme Werte), ein Teil der Odoo-11-Werte ist
veraltet (Arbeitsplan wurde spaeter geaendert), Odoo 11 fuehrt keinen
Feiertagskalender, Halbtage wurden in Odoo 11 als 0,5 gespeichert.

## 5. Rechte

Odoo-11-Gruppen ueber den Login abgebildet (Skript `scripts/anwesenheiten_rechte.py`):

| Odoo 11 | Odoo 18 | Benutzer |
|---|---|---|
| 34 Anwesenheit manuell (24) | `group_itk_anwesenheit_manuell` (neu) | 22 (2 ohne Odoo-18-Konto) |
| 32 Aufsicht (5) | `hr_attendance.group_hr_attendance_manager` | 3 neu, 1 vorhanden |
| 79 Personalsachbearbeiter (29) | `hr_holidays.group_hr_holidays_user` | 8 (19 Odoo-11-Logins sind keine Odoo-18-Benutzer) |
| 80 Manager (5) | `hr_holidays.group_hr_holidays_manager` | 4 |

Hinweis: `res.groups.users` zaehlt nur aktive Benutzer (12 von 22).

## 6. Werkzeuge

| Datei | Zweck |
|---|---|
| `scripts/anwesenheiten_migration.py` | Datenmigration (Trockenlauf Standard, `--ausfuehren --ich-habe-freigabe`) |
| `scripts/anwesenheiten_rechte.py` | Gruppen abbilden (`--setzen`) |
| `scripts/anwesenheiten_labels_de.py` | de_DE-Slots der Menues/Aktionen (`--setzen`) |
| `scripts/anwesenheiten_zeiterfassung_bezug.py` | Abwesenheitsbezug der Zeiterfassung (`--setzen`) |
| `scripts/verify_s137_anwesenheiten.py` | Abnahme Struktur/Daten |
| `scripts/browser_anwesenheiten_abnahme.py` | Browserabnahme (Chrome) |

Protokolle: `%LOCALAPPDATA%\Temp\anwesenheiten_migration\`, Screenshots
`%LOCALAPPDATA%\Temp\anw_abnahme_*.png`.

## 7. Offene Punkte ausserhalb dieses Bereichs

| Punkt | Zustaendiger Bereich |
|---|---|
| Zwei Projektkunden fehlen in Odoo 18: "[70101] Statutarstadt Innsbruck", "[WLV-Voeslau] Wasserleitungsverband ..." | Kunden-/Partnerzuordnung |
| Startzeit historischer Zeiterfassungszeilen als 00:00 UTC gespeichert (Anzeige 01:00/02:00 Wiener Zeit) | bekannte Zeitzonen-Darstellung |
| Odoo 11 waechst weiter (Antraege, Anwesenheiten, Zeiterfassung): vor einem Produktivstart Nachzug mit den idempotenten Werkzeugen einplanen | alle Bereiche |
| Bereiche, die noch nicht abgenommen sind: Helpdesk (abgeschlossen), Kontakte/Kundenverwaltung, CRM, Abrechnung (migrationsbereit) | naechste Sessions |

## 8. Git-Stand

Arbeitsbranch `s137-anwesenheiten-urlaub`, Commits siehe `git log`. Nach dem Merge
wird dieser Abschnitt um Merge-Commit, Baum-Hash und den Dreistand-Nachweis ergaenzt.
