# Migrationsskript Verkauf (Odoo 11 -> Odoo 18)

Skript: `scripts/migration/verkauf_migration.py`
Teil des ITK-Migrationsprojekts, erstellt unter Freigabe von Anna Maierhofer (11.11.2026).
Rekonstruiert aus `scripts/analyse_verkauf_*.py`, `scripts/abschluss_verkauf_*.py`,
`scripts/pruefe_verkauf_migrationscheck_*.py`, `scripts/apply_verkauf_stammdaten.py`,
`scripts/baue_verkauf_migrationsregeln.py` und `docs/o11-o18-verkauf-migrationscheck*.md`.

## Quelle

Odoo 11 Produktion `ITK_V1_a` - ausschliesslich lesend (`sale.order`, `sale.order.line`).

## Ziel

Odoo 18, `--instanz lokal` oder `--instanz vm`.

## Voraussetzungen

- `.env` mit `ODOO11_*` und `ODOO18_*` (nicht versioniert).
- Fuer einen spaeteren Datenlauf zusaetzlich: Kunden- und Produktzuordnung
  (`res.partner`, `product.product.default_code`) sowie Preislisten.

## Trockenlauf (Standard)

```
python scripts/migration/verkauf_migration.py --instanz lokal
python scripts/migration/verkauf_migration.py --instanz vm
```

Schreibt nichts (Schreibschutz-Klasse bricht jeden Schreibaufruf ab).

## Produktiver Lauf

```
python scripts/migration/verkauf_migration.py --instanz lokal --ausfuehren --ich-habe-freigabe --grenze 50
```

Der Schreibpfad ist **bewusst gesperrt**: er bricht mit Klartext ab, solange die
Stammdatenzuordnung nicht geprueft und freigegeben ist. Ein Teilimport ohne Kunden und
Produkte wuerde Auftraege ohne belastbare Zeilen erzeugen und waere fachlich falsch.

## Sicherheitsmechanismen

- Trockenlauf als Standard, Schreibschutz-Klasse, Freigabeschalter (`--ich-habe-freigabe`).
- Odoo 11 nur lesend.
- Keine Zugangsdaten im Skript.
- Keine Kunden- oder Personendaten im Mapping-Export (nur Auftragsname, Status, Zeilenzahl).

## Mapping

| Objekt | Erkennung | Anmerkung |
|---|---|---|
| Auftrag | `name` (z. B. `A-1900011`) | Odoo-11-IDs werden nicht als Bruecke benutzt |
| Zeile | Produkt ueber `default_code`, sonst Name; Menge und Preis aus Odoo 11 | Preis wird nicht neu berechnet |
| Kunde | Name in `res.partner` | bei Mehrdeutigkeit nicht zuordenbar |
| Produkt | `default_code` | fehlender Code = nicht zuordenbar |

`--mapping datei.json` schreibt die erkannten Zuordnungen.

## Bekannte Sonderfaelle

- Odoo 18 enthaelt derzeit nur Abnahme- und Testauftraege (`S00001`, `A-1900011` usw.).
- Nummernkreise: 2 der 18 Odoo-18-Auftragsnamen existieren auch in Odoo 11; die Erkennung
  ueber `name` ist deshalb nur zusammen mit Status und Datum belastbar.
- Ein Auftrag ohne zuordenbaren Kunden oder ohne zuordenbares Produkt wird nicht
  geschrieben, sondern als "nicht zuordenbar" gezaehlt.

## Validierung nach der Migration

1. Trockenlauf: `fehlend = 0`, `nicht zuordenbar = 0`.
2. Zweiter Lauf: `angelegt = 0`.
3. Stichproben: Auftragssummen und Zeilenanzahl gegen Odoo 11.
4. Regression Verkauf/Abrechnung (`scripts/abschluss_verkauf_regression.py`).
5. Browser lokal und VM.

## Laufprotokoll (nur Mengenwerte)

| Datum/Zeit | Commit | Quelle | Ziel | Modus | Ergebnis |
|---|---|---|---|---|---|
| 12.11.2026 15:33 | f24214a | Odoo 11 `ITK_V1_a` (lesend) | lokal `odoo18_test` | Trockenlauf | gelesen 2.514, erkannt 2, fehlend 2.512, Kunde fehlt 2.509, Produkt fehlt 2.501, Fehler 0 |
| 12.11.2026 15:40 | f24214a | Odoo 11 `ITK_V1_a` (lesend) | VM `odoo18_test` | Trockenlauf | gelesen 2.514, erkannt 2, fehlend 2.512, Fehler 0 |

**Befund:** Die Auftragsdaten sind nicht migriert. Ein produktiver Lauf wurde **nicht**
ausgefuehrt (er waere nur durch Schreiben testbar und braucht zuerst die Stammdaten).
