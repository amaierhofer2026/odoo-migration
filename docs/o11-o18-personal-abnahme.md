# Bereich PERSONAL: Abnahme durchgefuehrt (Browser, lokal und VM)

Stand 21.10.2026. Diese Datei haelt die fachliche Browserabnahme des Moduls Personal
fest. Odoo 11 wurde ausschliesslich gelesen.

## 1. Pruefumfang und Ergebnis

| Pruefung | lokal | VM | Nachweis |
|---|---|---|---|
| Struktur, Labels, Filter, Rechte, Feldvergleich aller Mitarbeiter | 54 OK / 0 FEHL | 54 OK / 0 FEHL | `scripts/verify_personal.py` |
| Browserabnahme (Menue, Liste, Formular, Kalender, Orte, Arten, Ansprueche, Antraege, Anwesenheiten, Rechte) | 70 OK / 0 FEHL | 70 OK / 0 FEHL | `scripts/browser_personal_abnahme_voll.py` |
| Regression Verkauf/Abrechnung | siehe Abschnitt 5 | siehe Abschnitt 5 | `scripts/abschluss_verkauf_regression.py` |

Screenshots: `Desktop\Odoo18-Personal-Abnahme\lokal` und `...\vm`.

## 2. Was im Browser bedient und geprueft wurde

- App/Menue "Personal" mit den Untermenues Abteilungen, Berichtswesen, Konfiguration.
- Mitarbeiterliste: Spalten Name des Mitarbeiters, Telefon (geschaeftlich), Arbeits-E-Mail,
  Abteilung, Position, Manager; 13 aktive Datensaetze; Umschaltung Kanban/Liste;
  Gruppierung nach Abteilung im Suchmenue; archivierter Mitarbeiter
  "ausgeschieden/Koch Katharina" im Formular geoeffnet (aktiv = nein).
- Mitarbeiterformular (drei Stichproben: Waiss Martina, Soritz Gerd, Breiteneder Lorenz):
  Gruppen Kontaktinformationen und Position, Reiter Lebenslauf / Arbeitsinformationen /
  Erhaltene Abzeichen / Private Informationen / Einstellungen; Werte fuer Abteilung,
  Position, Arbeitszeitmodell (Reiter Arbeitsinformationen), Arbeitsort, Arbeits-E-Mail,
  Barcode und PIN (Reiter Einstellungen), Mobilnummer, Stichwort "IT-Kommunal GmbH".
- Arbeitszeitmodelle: 8 Datensaetze, Namen wie in Odoo 11, "20 Stunden" mit 10
  Arbeitszeitzeilen und Zeiten 08:00-12:00 / 13:00-17:00.
- Arbeitsorte: 5 Datensaetze inkl. "Home Office" und "Pius-Parsch-Platz 9/14, 1210 Wien".
- Urlaubsarten: 25 Datensaetze, keine doppelten Namen, "Krankheitsstände", "Augleichstage",
  "Unbezahlt", "gesetzlicher Jahresurlaub 2026" vorhanden.
- Urlaubsansprueche: 65 Datensaetze; Stichprobe Waiss Martina mit 23,75 Tagen,
  Urlaubsart "gesetzlicher Jahresurlaub"; keine 0-Tage-Ansprueche und kein Anspruch ohne
  Mitarbeiter (die beiden dokumentierten Sonderfaelle sind bewusst nicht angelegt).
- Urlaubsantraege: 483 Datensaetze (482 aus Odoo 11 + 1 Altbestand); der ueberschneidende
  Alt-Antrag Waiss Martina 16.-22.07.2023 ist mit Status "Genehmigt" vorhanden; ein
  Antrag mit 0 Tagen (Blagojevic Dejvid, Krankheitsstände, 09.08.2026) ist mit
  Originaldaten vorhanden.
- Anwesenheiten: 192 Datensaetze mit Ein-/Ausbuchungen (Pager und Schnittstelle gleich).
- Berechtigungen: als Administrator sind die HR-Felder vorhanden; die Zugriffsmatrix gibt
  internen Benutzern nur Lesen auf `hr.employee` und `hr.job`, kein Schreiben; Menue
  "Abteilungen" haengt an `hr.group_hr_user`.

## 3. Berechtigungsprobe mit echtem Benutzer (temporaer, wieder entfernt)

Ein temporaerer interner Benutzer (nur `base.group_user`) wurde angelegt, geprueft und im
selben Lauf geloescht (Benutzer 18 vorher = 18 nachher, keine Reste):

- Lesen `hr.employee`: erlaubt (13 aktive Datensaetze sichtbar) - Odoo-11-Stand.
- Sichtbare Felder: 81; **nicht** sichtbar: `private_street`, `private_phone`,
  `identification_id`, `sinid`, `ssnid`, `bank_account_id`.
- Direktes Lesen von `private_street`: `AccessError`.
- Schreiben auf `hr.employee`: `AccessError`.

Damit ist belegt: HR-sensitive Felder bleiben fuer nicht berechtigte Benutzer unsichtbar,
obwohl der Mitarbeiterstamm lesbar ist.

## 4. Befund: Odoo-11-Daten wurden waehrend des Projekts geaendert

In Odoo 11 (Produktion) wurden am 21.10.2026 um 12:30 und 12:31 drei Datensaetze durch
Benutzer "Maierhofer Anna" geaendert: `hr.employee` 27 (Maierhofer Anna) und 28
(Blagojevic Dejvid) sowie `hr.job` 1 (Projektconsultant, Folgeberechnung).

Die Pruefung zeigte danach drei Abweichungen in Odoo 18:
Blagojevic Dejvid Abteilung (Odoo 11: Sales), Maierhofer Anna Abteilung (Administration)
und Position (Projektconsultant). Diese Zugriffe stammen nicht aus den Migrationsskripten
(alle Odoo-11-Aufrufe sind lesend); sie sind Nutzeraktivitaet in der Produktion.

Behandlung: Odoo 18 wurde mit dem idempotenten Migrationslauf nachgezogen
(`hr_migration.py --ohne-belegdaten` fuer die VM), Odoo 11 blieb unveraendert.
Danach wieder 54 OK / 0 FEHL auf beiden Instanzen. Konsequenz fuer spaeter: die Migration
ist ein Schnappschuss; Aenderungen in Odoo 11 nach dem Lauf muessen nachgezogen werden.

## 5. Regression und Dreistand

- Regression Verkauf/Abrechnung: lokal und VM je 881 OK / 0 FEHL (elf Prueflaeufe).
- Testdaten: keine vorhanden. Die einzigen heute angelegten Datensaetze in Odoo 18 sind
  die Migrationsergebnisse selbst (1 Mitarbeiter Meraner Daniel, 482 Antraege,
  65 Ansprueche, 192 Anwesenheiten, 7 Arbeitszeitmodelle, 2 Arbeitsorte, 19 Urlaubsarten);
  Benutzer 18 (unveraendert), keine Testmitarbeiter, keine Test-Urlaubsarten.
- Odoo 11: Zaehlungen unveraendert (25 Mitarbeiter, 551 Urlaubssaetze, 192 Anwesenheiten,
  9 Arbeitszeitmodelle).
- Dreistand main = lokal = GitHub = VM: siehe Abschlussbericht.
