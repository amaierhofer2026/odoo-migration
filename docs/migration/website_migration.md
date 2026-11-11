# Migrationsskript Website/Webinhalte (Odoo 11 -> Odoo 18)

Skript: `scripts/migration/website_migration.py`
Einstieg fuer die Logik: `scripts/migrate_website.py` (Markup: `scripts/website_markup.py`)
Modulbezogene Anpassungen (Wortlaute, Cookie-Hinweis, Fusszeile): `addons/itk_website`

Dieses Skript ist Teil des ITK-Migrationsprojekts. Es wurde unter Freigabe von
Anna Maierhofer ausgefuehrt; die Entscheidungen E1-E14 stammen von ihr
(`docs/o11-o18-website-abnahme.md`).

## Quelle

Odoo 11 Produktion `ITK_V1_a` (portal.it-kommunal.at) - **ausschliesslich lesend**
(`search_read`, `read`, `fields_get`). Es findet kein Schreibzugriff auf Odoo 11 statt.

## Ziel

Odoo 18, waehlbar per `--instanz lokal` (Docker `odoo18_test`, localhost:8069) oder
`--instanz vm` (https://k001959vsx.ipax.at).

## Voraussetzungen

- `.env` im Repo-Wurzelverzeichnis mit `ODOO11_URL/DB/USER/PWD` und `ODOO18_URL/DB/USER/PWD`
  (nicht versioniert; Vorlage `.env.example`).
- Modul `itk_website` installiert (Cookie-Hinweis, Fusszeile, Wortlaute) - auf der VM
  einmalig mit `-i itk_website` installiert.
- Schreibrechte des technischen Benutzers auf `website.page`, `website.menu`,
  `link.tracker`, `utm.*`, `ir.attachment`.
- Python 3 mit Standardbibliothek (kein Zusatzpaket; `lxml` wird bewusst nicht benutzt).

## Trockenlauf (Standard)

```
python scripts/migration/website_migration.py --instanz lokal
python scripts/migration/website_migration.py --instanz vm
```

Der Trockenlauf schreibt nichts. Technisch abgesichert durch die Klasse `Schreibschutz`:
jeder `create`/`write`/`unlink`-Aufruf im Trockenlauf bricht mit Fehler ab, statt still zu
schreiben. Zusaetzlich wird der Bestand vor und nach dem Lauf verglichen.

## Produktiver Lauf

```
python scripts/migration/website_migration.py --instanz lokal --ausfuehren --ich-habe-freigabe
```

Ohne `--ich-habe-freigabe` bricht das Skript mit Exit-Code 2 ab. Weitere Optionen:
`--nur anhang,demo,seiten,menues,einstellungen,tracker`, `--mapping datei.json`,
`--abnahme` (nur Bestandszahlen).

Reihenfolge der Schritte: Anhang -> Demo-Bereinigung -> Seiten -> Menues -> Einstellungen ->
Link-Tracker. Der Anhang muss vor Seite 17 laufen (die Bild-URL enthaelt die Anhangs-id),
die Demo-Bereinigung vor der Startseite (gibt den Pfad `/` frei).

## Sicherheitsmechanismen

- Trockenlauf als Standard, Schreibschutz-Klasse gegen versehentliche Schreibaufrufe.
- Schreiblauf nur mit zwei Schaltern (`--ausfuehren` **und** `--ich-habe-freigabe`).
- Odoo 11 wird nur gelesen; das Skript kennt keinen Schreibpfad dorthin.
- Keine Zugangsdaten im Skript; alles aus `.env`.
- Demo-Schutz: Besucher/Seitenansichten werden nur bis 50 Datensaetze geloescht, damit die
  echte Zugriffsstatistik der VM erhalten bleibt.
- Klick-Ueberschuss ueber dem Odoo-11-Sollwert wird entfernt (Abnahmeklicks verfaelschen
  die Zahlen nicht).

## Mapping (fachliche Schluessel, keine Odoo-11-IDs als Bruecke)

| Objekt | Erkennung im Ziel | Datei/Key |
|---|---|---|
| Seite | View-Key `website.<slug>` (Startseite: `website.webseite`), sonst URL | Odoo-11-Key wird uebernommen |
| Menue | URL unter der Wurzel `Top Menü` | `website.menu` der Website |
| Anhang | Name + Dateigroesse | `ir.attachment` |
| Link-Tracker | Kurz-URL-Code (`code`) | `link.tracker.code` |
| Klicks | Sollzahl je Tracker (`count` aus Odoo 11) | `link.tracker.click` |
| Kampagne | Name | `utm.campaign` |
| Medium | Name, mit Odoo-18-Umbenennung Banner Ads->Banner, Twitter Ads->X, Facebook Ads->Facebook | `utm.medium` |
| Quelle | Name | `utm.source` |

`--mapping datei.json` schreibt die Zuordnung Odoo-11-id -> Odoo-18-id/Key. Die Datei enthaelt
nur fachliche Schluessel (Seitenname, URL, Key, Kurz-URL-Code, Klickzahl) - keine
personenbezogenen Daten.

## Bekannte Sonderfaelle

1. **Eindeutigkeit der Link-Tracker:** Odoo 18 verlangt (URL, Kampagne, Medium, Quelle,
   Bezeichnung) eindeutig; Odoo 11 erlaubte Dubletten (ein Kurzlink je Mailing). 633 der
   837 Tracker tragen daher die technische Kennung `Odoo-11-Link <id>` im Feld Bezeichnung.
   Das Feld ist rein intern (Backend-Spalte) und erscheint nicht auf der Website.
2. **Quellen/Kampagnen mit gleichem Namen:** Odoo 11 hat 220 Quellen, aber nur 133 eindeutige
   Namen (z. B. 21 x "Newsletter"). Sie werden auf je eine Odoo-18-Quelle abgebildet; die
   Tracker-Zuordnung bleibt vollstaendig (alle 837 Tracker haben ihre Quelle).
   Gleiches Prinzip bei Kampagnen: 16 Odoo-11-Kampagnen -> 14 eindeutige Odoo-18-Kampagnen.
3. **Klick-Einzelsaetze:** 563 Klick-Datensaetze werden ohne IP-Adresse und ohne
   Mail-/Kontaktbezug angelegt (nur Link + Zeitpunkt), damit die historischen Klickzahlen
   in Odoo 18 dauerhaft stimmen (`link.tracker.count` ist ein berechnetes Feld).
4. **Doppelte Startseite:** Die vom Konfigurator kopierte, websitegebundene Startseite wird
   entfernt. Die Odoo-Standard-Startseite (`website.homepage_page`, Moduldaten) wird auf
   `/homepage-vorlage` gelegt und unveroeffentlicht - Loeschen waere nach einem
   `website`-Upgrade nicht dauerhaft.
5. **Geschuetztes Wurzelmenue:** `website.main_menu` ("Default Main Menu") ist
   Odoo-Standarddatum und wird nicht geloescht oder veraendert.
6. **Startseite:** gestalterisch neu im Odoo-18-Layout (`scripts/website_homepage_o18.html`),
   Inhalt und Links aus Odoo 11 (Entscheidung E1).
7. **Nicht uebernommen:** Seiten 5, 7, 9, 12, 13 (Test/Kopie/Sicherung) und die
   Odoo-Standardseiten 2, 3, 4; Formularuebermittlungen, Kontakte, Leads, Auftraege.

## Validierung nach der Migration

1. Zweiter Lauf muss `angelegt = 0` und `aktualisiert = 0` melden (Idempotenz).
2. `--abnahme` bzw. Bestandsvergleich: Tracker 837, Klicks 563, Seiten 12, Menues 15.
3. HTTP: 7 uebernommene Seiten 200, die zwei unveroeffentlichten 404.
4. Browser lokal und VM: Startseite, `/kurse` (Akkordeons bedienbar), FAQ-Partner mobil,
   Cookie-OK, Kopfzeile mit 8 Punkten (Punkt 7 und 10 unsichtbar).
5. Kurz-URL: `/r/wFy` -> 301 auf das historische Ziel mit UTM-Parametern.
6. Rechte: `scripts/pruefe_website_rechte.py --instanz lokal|vm` (17 Pruefungen).
7. Regression der gesperrten Bereiche.

## Laufprotokoll (Mengenwerte, ohne personenbezogene Inhalte)

| Datum/Zeit | Commit | Quelle | Ziel | Modus | Ergebnis |
|---|---|---|---|---|---|
| 11.11.2026, Session 142 | 5f2a4c7 | Odoo 11 `ITK_V1_a` (lesend) | lokal `odoo18_test` | Trockenlauf | 0 geschrieben (Snapshot 10 Modelle identisch) |
| 11.11.2026, Session 142 | 5f2a4c7 | Odoo 11 `ITK_V1_a` (lesend) | lokal `odoo18_test` | Schreiblauf (Freigabe Anna) | 9 Seiten, 10 Menues, 837 Tracker, 563 Klicks, 1 Anhang angelegt |
| 11.11.2026, Session 142 | 5f2a4c7 | Odoo 11 `ITK_V1_a` (lesend) | lokal `odoo18_test` | Schreiblauf (Wiederholung) | 0 Neuanlagen, 0 neue Klicks |
| 11.11.2026, Session 142 | 506afb4 | Odoo 11 `ITK_V1_a` (lesend) | VM `odoo18_test` | Schreiblauf (Freigabe Anna) | 9 Seiten, 9 Menues + 1 vorhanden, 837 Tracker, 563 Klicks, 1 Anhang |
| 11.11.2026, Session 142 | 506afb4 | Odoo 11 `ITK_V1_a` (lesend) | VM `odoo18_test` | Schreiblauf (Wiederholung) | 0 Neuanlagen, 0 neue Klicks |
| 12.11.2026 14:53 | 845237c | Odoo 11 `ITK_V1_a` (lesend) | lokal `odoo18_test` | Trockenlauf (Nachweis) | gelesen 9/10/837, angelegt 0, aktualisiert 0, uebersprungen 857, Fehler 0 |
| 12.11.2026 14:55 | 845237c | Odoo 11 `ITK_V1_a` (lesend) | VM `odoo18_test` | Trockenlauf (Nachweis) | gelesen 9/10/837, angelegt 0, aktualisiert 0, uebersprungen 857, Fehler 0 |

Bestand nach der Migration (lokal und VM identisch): 12 Seiten (9 veroeffentlicht),
15 Menues, 837 Link-Tracker, 563 Klicks, 14 Kampagnen, 10 Medien, 141 (lokal) / 140 (VM)
Quellen, 1 migrierter Anhang.
