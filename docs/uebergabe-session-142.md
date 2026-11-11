# Uebergabe Session 142 -> 143

Stand: 12.11.2026. Diese Datei ist der Einstieg fuer die naechste Session.

## 1 Gesperrter Stand (nicht ohne ausdruecklichen Auftrag aendern)

| Bereich | Status |
|---|---|
| Projekt | ABGENOMMEN und GESPERRT |
| Personal | ABGENOMMEN und GESPERRT |
| Zeiterfassung | ABGENOMMEN und GESPERRT |
| Anwesenheiten / Urlaubsantraege | ABGENOMMEN und GESPERRT |
| Verkauf | ABGENOMMEN und GESPERRT |
| Abonnements | ABGENOMMEN und GESPERRT |
| Abrechnung | MIGRATIONSBEREIT (Struktur), Datenmigration offen (Kontenstammdaten 8400/3400) |
| Helpdesk | ABGENOMMEN und GESPERRT |
| Events | ABGENOMMEN und GESPERRT |
| E-Mail-Marketing | ABGENOMMEN und GESPERRT |
| Massenbearbeitung | ABGENOMMEN und GESPERRT (Session 140) |
| **Website / Webinhalte** | **ABGENOMMEN UND GESPERRT (12.11.2026, Session 142)** |

## 2 Was Session 142 gemacht hat

Auftrag: Entscheidungen E1-E14 umsetzen, Website-Daten aus Odoo 11 migrieren, lokal und VM
abnehmen, Bereich sperren. Dokument: `docs/o11-o18-website-abnahme.md`.

Neu im Repo:
- `addons/itk_website` 18.0.1.0.0: Cookie-Hinweis deutsch, ITK-Fusszeile, Demo-Kontaktblock
  im Kopf deaktiviert, Backend-Wortlaute "Site" -> "Webseite", "Analytics" -> "Analysen"
  (Quelle + de_DE + en_US, bei jedem Setup erneut gesetzt).
- `scripts/website_markup.py`: Markup-Konverter Odoo 11 (BS3) -> Odoo 18 (BS5), nur
  Standardbibliothek (ElementTree; lxml im aktiven Python ohne `etree`).
- `scripts/migrate_website.py`: Trockenlauf/Schreiblauf mit Schreibschutz-Klasse, `--nur`,
  `--abnahme`. Schritte: Anhang, Demo, Seiten, Menues, Einstellungen, Link-Tracker.
- `scripts/website_homepage_o18.html`: Startseite im Odoo-18-Layout.
- `scripts/pruefe_website_rechte.py`: Rechtepruefung mit zwei temporaeren Benutzern,
  entfernt Benutzer UND die dabei erzeugten Partner.

Zahlen:
- Odoo 11: 17 Seiten (10 veroeffentlicht), 11 Menues, 837 Link-Tracker, 563 Klicks.
- Uebernommen: 9 Seiten (7 veroeffentlicht, 2 unveroeffentlicht), 10 Menuepunkte,
  837 Tracker mit 563 Klicks, 16 Kampagnen, 9 Medien, 220 Quellen, 1 Bild-Anhang.
- Odoo 18 danach: 12 Seiten (9 + Contact Us + Thanks + unveroeffentlichte
  Standard-Startseite `/homepage-vorlage`), 15 Menues (10 Odoo-11-Punkte, 3 Kinder des
  geschuetzten `website.main_menu`, 2 Wurzeln).

## 3 Abnahme (lokal und VM)

- Alle veroeffentlichten Seiten HTTP 200, die zwei unveroeffentlichten HTTP 404.
- 0 sichtbare `&nbsp;`/`&amp;`-Artefakte; Akkordeons 54/4/6/33/14.
- Browser (echtes Chrome): Startseite (Logo, Karten, Cookie-Banner deutsch, Support- und
  Kontaktblock), `/kurse` (49 bzw. 54 Aufklapperknoepfe, Klick oeffnet), FAQ-Partner mobil.
- Kopfzeile: 8 Menuepunkte sichtbar, Punkt 7 und 10 unsichtbar (Zielseite unveroeffentlicht).
- Kurz-URL `/r/wFy` -> 301 auf das historische Ziel mit UTM-Parametern.
- Rechte: 17 OK / 0 Fehler lokal und VM; Testbenutzer und Testpartner vollstaendig entfernt
  (14 Benutzer, 96 Partner vorher = nachher).
- Idempotenz: Wiederholungslaeufe 0 Neuanlagen, 0 Aktualisierungen, 0 neue Klicks.
- Regression lokal und VM: Events 61/0, Marketing 37/0, Personal 54/0, Projekt 20/0,
  Verkauf ohne Abweichung, Massenbearbeitung 7/0.

## 4 Bewusste Entscheidungen und Nebeneffekte

- **Klick-Einzelsaetze ohne IP und ohne Mailbezug** (Anna, 11.11.2026): Klickzahlen sind
  uebernommen, personenbezogene Bestandteile nicht.
- **633 technische Labels** `Odoo-11-Link <id>` im Backend-Feld "Bezeichnung", weil Odoo 18
  (URL, Kampagne, Medium, Quelle, Bezeichnung) eindeutig verlangt. Nur intern sichtbar.
- **VM-Zugriffsstatistik geschuetzt**: 7.205 Besucher / 7.271 Seitenansichten sind echte
  Zugriffe, keine Demodaten. Geloescht wird nur bis 50 Datensaetze (`DEMO_GRENZE` im Skript).
  Durch das Entfernen der doppelten Konfigurator-Startseite sanken die an ihr haengenden
  Seitenansichten von 7.271 auf 204 (Odoo-Standard-Kaskade).
- **Abnahmeklicks**: Testaufrufe von `/r/wFy` erzeugen echte Klicks; das Skript entfernt
  jetzt Ueberschuss-Klicks ueber dem Odoo-11-Sollwert (beide Instanzen stehen auf 563).
- **`website.main_menu`** bleibt unveraendert (Odoo-Standarddatum, nicht loeschbar).
- **`/homepage-vorlage`** bleibt als unveroeffentlichte Vorlage, weil ein Loeschen von
  Moduldaten beim naechsten `website`-Upgrade rueckgaengig gemacht wuerde.

## 5 Offene Punkte (nicht Website)

- Abrechnung: Kontenstammdaten 8400/3400 fehlen im Odoo-18-Kontenrahmen (BLOCKER).
- Umfragen/Survey (Odoo 11: 2 Umfragen, 73 Teilnahmen) noch nicht bearbeitet.
- Valorisierung, Lager/Bestand offen.
- Externe Konfigurationspunkte fuer Website: Produktivdomain (derzeit
  `https://www.it-kommunal.at`), `mail.catchall.domain`, reCAPTCHA-Schluessel.

## 6 Werkzeuge

| Datei | Zweck |
|---|---|
| `scripts/migrate_website.py` | Website-Migration, `--instanz lokal\|vm`, `--schreiben`, `--nur`, `--abnahme` |
| `scripts/website_markup.py` | Konverter mit Restpruefung, `--verzeichnis`/`--ziel` |
| `scripts/pruefe_website_rechte.py` | Rechtepruefung mit temporaeren Benutzern |
| `scripts/analyse_o11_website.py` | read-only Bestandsaufnahme |
| `addons/itk_website` | Cookie-Hinweis, Fusszeile, Wortlaute |

## 7 Start der naechsten Session

```
cd C:\Odoo-Test
git status --short --branch && git log --oneline -3
python scripts/migrate_website.py --instanz lokal            # muss 0 Neuanlagen melden
python scripts/pruefe_website_rechte.py --instanz lokal
```

Website ist gesperrt: keine Aenderungen an Seiten, Menues, Trackern, Einstellungen oder
`itk_website` ohne neuen Auftrag von Anna.
