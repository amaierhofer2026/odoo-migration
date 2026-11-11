# Migrationsskript Abonnements (Odoo 11 -> Odoo 18)

Skript: `scripts/migration/abonnement_migration.py`
Teil des ITK-Migrationsprojekts, erstellt unter Freigabe von Anna Maierhofer (11.11.2026).
Rekonstruiert aus `scripts/apply_abo_stammdaten.py`, `scripts/check_abo_migration_rules.py`,
`scripts/abgleich_abonnements_1..5.py`, `docs/o11-o18-abonnement-abgleich.md` und der
Abo-Historie in `PROJECT_KNOWLEDGE.md`.

## Quelle

Odoo 11 Produktion `ITK_V1_a` - ausschliesslich lesend (`sale.subscription`, Vorlagen,
Beendigungsgruende, Preislisten).

## Ziel

Odoo 18, `--instanz lokal` oder `--instanz vm`.

## Voraussetzungen

- `.env` mit `ODOO11_*` und `ODOO18_*` (nicht versioniert).
- Abo-Stammdaten in Odoo 18: `scripts/apply_abo_stammdaten.py` (von Anna am 18.09.2026
  freigegeben) - Vorlagen und Beendigungsgruende sind vorhanden (4 bzw. 31 in lokal,
  5 Vorlagen auf der VM).
- Fuer einen Datenlauf: Zuordnung der Abo-Vorlagen, Preislisten und Partner.

## Trockenlauf (Standard)

```
python scripts/migration/abonnement_migration.py --instanz lokal
python scripts/migration/abonnement_migration.py --instanz vm
```

Schreibt nichts (Schreibschutz-Klasse).

## Produktiver Lauf

```
python scripts/migration/abonnement_migration.py --instanz lokal --ausfuehren --ich-habe-freigabe --grenze 20
```

Der Schreibpfad ist **bewusst gesperrt** und bricht mit Klartext ab, solange Partner,
Preislisten und Vorlagen nicht vollstaendig zugeordnet und freigegeben sind.

## Sicherheitsmechanismen

- Trockenlauf als Standard, Schreibschutz-Klasse, Freigabeschalter.
- Odoo 11 nur lesend.
- Keine Zugangsdaten im Skript, keine Kunden- oder Personendaten im Mapping
  (nur Abo-Name, Code, Status, Ziel-id).
- Stammdatensaetze (Vorlagen, Beendigungsgruende) werden nur gezaehlt, nicht angelegt.

## Mapping

| Objekt | Erkennung |
|---|---|
| Abonnement | `name`, zusaetzlich `code` |
| Vorlage | Odoo-11-`template_id` -> Odoo-18-Vorlage ueber Namen |
| Preisliste | Odoo-11-`pricelist_id` -> Odoo-18-Preisliste ueber Namen |
| Partner | Name in `res.partner` |
| Beendigungsgrund | Name (Stammdaten bereits vorhanden) |

## Bekannte Sonderfaelle

- Odoo 11 hat 1.788 Abos; Odoo 18 enthaelt derzeit nur Abnahme-/Testabos
  (`TEST Abnahme cancel`, `TEST Abnahme open`, `NV-00962`).
- Das Abo `NV-00962` wurde laut Projektwissen manuell mit expliziter Preisliste (PL 34, EUR)
  angelegt - die Historie ist dokumentiert, das Skript erkennt es ueber den Namen.
- Abos ohne zuordenbaren Partner/Preisliste/Vorlage werden als "nicht zuordenbar" gezaehlt
  und nicht geschrieben.

## Validierung nach der Migration

1. Trockenlauf: `fehlend = 0`, `nicht zuordenbar = 0`.
2. Zweiter Lauf: `angelegt = 0`.
3. Summenvergleich `recurring_total` je Abo gegen Odoo 11.
4. Regression Abonnements/Abrechnung.
5. Browser lokal und VM.

## Laufprotokoll (nur Mengenwerte)

| Datum/Zeit | Commit | Quelle | Ziel | Modus | Ergebnis |
|---|---|---|---|---|---|
| 12.11.2026 15:36 | f24214a | Odoo 11 `ITK_V1_a` (lesend) | lokal `odoo18_test` | Trockenlauf | gelesen 1.788, erkannt 11, fehlend 1.777, Partner fehlt 1.775, Preisliste fehlt 1.777, Fehler 0 |
| 12.11.2026 15:41 | f24214a | Odoo 11 `ITK_V1_a` (lesend) | VM `odoo18_test` | Trockenlauf | gelesen 1.788, erkannt 11, fehlend 1.777, Fehler 0 |

**Befund:** Die Abodaten sind nicht migriert. Ein produktiver Lauf wurde **nicht**
ausgefuehrt (nur durch Schreiben testbar, Voraussetzungen fehlen).
