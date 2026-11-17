# Uebergabe Session 144

Stand: 12.11.2026, Ende Session 144. Einstiegspunkt fuer Session 145.
Verbindliche Regel: `docs/MIGRATIONSREGEL.md` (Freigabe Anna Maierhofer, 11.11.2026).

## 1 Gemeinsamer Stand

| Ort | Stand |
|---|---|
| lokal `C:\Odoo-Test` | `d067242b604ec73c784d98c367454ca7eeef3b5f`, Arbeitsbaum sauber |
| GitHub `main` | derselbe Commit |
| VM `k001959vsx.ipax.at` | derselbe Commit, Arbeitsbaum sauber |

Dreistand geprueft. Letzte PRs: #268 bis #272.

Instanzen: lokal `http://localhost:8069` (Docker `odoo18` / `odoo18-db`), VM
`https://k001959vsx.ipax.at`. Beide DB `odoo18_test`, HTTP 200.
Odoo 11 Produktion `https://portal.it-kommunal.at`, DB `ITK_V1_a` - **ausschliesslich lesend**.

## 2 Abgeschlossen und gesperrt

| Bereich | Beleg |
|---|---|
| Personal | 25 Mitarbeiter, 8 Arbeitszeitmodelle, 25 Urlaubsarten, 482 Antraege, 192 Anwesenheiten |
| Zeiterfassung | migriert, Regression 54/0 |
| Anwesenheiten | migriert |
| Projekt | migriert, Regression 20/0 |
| Events | 121 Events, Regression 61/0 |
| E-Mail-Marketing | 147 Mailings, 8 Listen ohne Empfaenger, Regression 37/0 |
| Massenbearbeitung | 20 Massenaktionen, Struktur ohne Datenbestand |
| Helpdesk | bewusst ohne Ticket-Transfer, `itk_helpdesk_compat` 18.0.1.1.3 |
| Website / Webinhalte | 17 Seiten analysiert, 9 migriert, 10 Menues, 837 Tracker, 563 Klicks |
| **Kontakte/Kundenverwaltung** | **6.022 Kontakte, 0 Dubletten, 0 Elternverluste, Filter/Gruppierung im UI belegt** |
| **Verkauf** | 2.519 Auftraege / 4.079 Zeilen, 0 Abweichungen Menge/Preis/Rabatt/Steuer |
| **Abonnements** | 1.786 Abos / 2.456 Zeilen |

Dokumente: `docs/migration/kontakte-abnahme.md`,
`docs/migration/verkauf-abonnement-migration.md`, `docs/o11-o18-website-abnahme.md`.

## 3 Kontakte - was in Session 144 passiert ist

**Kerndaten:** Odoo 11 fuehrt 6.054 Kontakte, Odoo 18 hat 6.022. Die 32 fehlenden sind
Kontakte ohne Namen (Rechnungsadressen mit leerem `name`); sie wurden bewusst nicht
migriert und nicht mit Platzhaltern ergaenzt. An 4 davon haengen 7 gebuchte Rechnungen -
vor dem Abrechnungslauf gesondert behandeln.

**Dubletten (wichtigster Befund):** 86 Odoo-11-IDs lagen mit 2 bis 7 Kopien vor, 501
Datensaetze, alle archiviert. Ursache: fruehe Migrationslaeufe lasen den Bestand ohne
`active_test=False` und legten archivierte Kontakte bei jedem Lauf neu an. Bereinigt
durch den Block "6) Dubletten bereinigen" in `kontakte_migration.py`: pro ID bleibt eine
Kopie, 415 entfernt, Beziehungen vorher umgehaengt. Ergebnis lokal und VM: 0 Dubletten.

**Elternbezuege:** Der zuvor gemeldete lokale Einzelfall war eine dieser Dubletten.
Endstand lokal und VM: 0 verlorene Elternbeziehungen. Odoo 11 hat 3.544 Kontakte mit
Elternkontakt, Odoo 18 3.513 - Differenz 31 = die namenlosen Kontakte.

**Idempotenz-Falle `vat`:** Odoo 18 normalisiert USt-ID-Formate. Solange `vat` im
Adresskorrektur-Block stand, meldete jeder Lauf dieselben 24 Formatabweichungen und
schrieb sie erneut. `vat` ist entfernt; der Wiederholungslauf zeigt 0 Korrekturen,
lokal und VM (VM doppelt belegt).

**Odoo 11 lebt weiter:** Am 17.11.2026 wurden zwei Kontakte (o11 13929, 13930) in Odoo 11
angelegt, die auf der VM fehlten. Nachgezogen. Bei jedem weiteren Modulabschluss ist der
Kontakte-Stand erneut zu ziehen - kein Migrationsfehler, sondern Produktivbetrieb.
Das Datum des jeweiligen Laufs gehoert in den Abschlussbericht.

**UI-Bedienung (Lehre fuer alle kuenftigen Browserabnahmen):** Der Filter-/Gruppierungs-
Dialog haengt an `.o_searchview_dropdown_toggler` (mit "r" am Ende), nicht an
`.o_searchview_dropdown_toggle`. Ein Klick auf den Such-Button `.o_searchview button.btn`
fokussiert nur das Suchfeld. Nach dem Entfernen eines Filter-Chips braucht der Toggle
5-6 Sekunden, bevor er wieder klickt. Echte Werte: Filter "Unternehmen" lokal 2.390 /
VM 2.393, Filter "Archiviert" lokal 204 / VM 203.

## 4 Offene Bereiche - Vorschlag fuer Session 145

1. **Produkte und Preislisten abnehmen.** Daten sind migriert (662 Vorlagen inkl.
   4 archivierter, 657 Varianten, 31 Kategorien, 50 Preislisten, 1.876 Regeln) und
   idempotent. Es fehlen nur Browserabnahme, Rechtepruefung und Sperrvermerk.
2. **CRM (Leads, Teams).** Noch kein Skript. Personenbezogene Daten, daher
   ausdrueckliche Freigabe vor dem Schreiblauf.
3. **Abrechnung.** Kontenstammdaten sind entschieden (8400 -> 4000, 3400 -> 5010,
   Steuern 77/2 geprueft, Sonderfall R-24832 nach gebuchtem Ist-Zustand).
   `scripts/testmigration_abrechnung.py` zum produktiven Skript ausbauen.
   Die 7 gebuchten Testrechnungen und 4 namenlosen Rechnungsadressen dabei beachten.
4. **Umfragen** (Odoo 11: 2 Umfragen, 73 Teilnahmen), **Valorisierung**, **Lager**.

## 5 Testdaten - bewusst stehen gelassen

12 Testauftraege, 25 Testprodukte, 32 Rechnungen (7 gebucht, 25 Entwurf).
Dokumentiert in `docs/migration/testdaten-analyse.md`. Kein Odoo-11-Bezug.
Die Bereinigungskette lautet: 25 Entwurfsrechnungen -> 12 Testauftraege -> 7 gebuchte
Rechnungen (Buchhaltung) -> 25 Testprodukte. Die 7 gebuchten Rechnungen werden
**nicht** storniert oder geloescht ohne ausdrueckliche Freigabe von Anna.

## 6 Arbeitsweise (bewaehrt, bitte beibehalten)

- Vor jedem Schreiblauf: Trockenlauf und Bericht an Anna, dann Freigabe abwarten.
- Migrationen laufen als Hintergrundprozess mit Logdatei unter
  `%LOCALAPPDATA%\Temp\s142_web\`; VM-Laeufe brauchen 10-20 Minuten.
- VM-Shell ueber `%LOCALAPPDATA%\Temp\vm_exec.py`; die VM hat **keine**
  Odoo-Zugangsdaten in der `.env`, Skripte laufen immer vom lokalen Client mit
  `--instanz vm`.
- Vor dem Sperrvermerk: Datenmengen, Idempotenz, Browser lokal und VM, Rechte,
  Regression, Dreistand - in dieser Reihenfolge, mit konkreten Werten.
- Nach jedem Bereich: Branch, PR ueber die REST-API (kein `gh`), Merge, VM `reset --hard`,
  Dreistand nachweisen.
- Keine personenbezogenen Daten in Git: nur IDs, Zaehlwerte, anonymisierte Nachweise.
