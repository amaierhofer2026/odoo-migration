# Uebergabe Session 142 (Nachtrag 2): Stammdaten fuer Verkauf und Abonnements

Stand 12.11.2026. Einstieg fuer die naechste Sitzung.

## Auftrag

Anna hat Option A freigegeben: Kontakte, Produkte und Preislisten als eigenes Teilprojekt
vollstaendig bearbeiten, danach Verkauf (2.514 Auftraege) und Abonnements (1.788)
migrieren. Bereits abgenommene Bereiche duerfen nicht fachlich veraendert werden.

## Erledigt

1. **Modul `itk_migration_keys` 18.0.1.0.0** (lokal und VM installiert): technisches Feld
   `itk_o11_id` auf `res.partner`, `res.partner.category`, `product.template`,
   `product.product`, `product.category`, `product.pricelist`, `product.pricelist.item`,
   `sale.order`, `sale.subscription`. Nicht in Ansichten sichtbar, enthaelt nur Zahlen.
2. **`scripts/migration/kontakte_migration.py`** - 123 Kontakt-Tags, 169 Anreden,
   6.020 Kontakte (5.851 aktiv + 201 archiviert), 32 ohne Namen nicht uebernommen.
3. **`scripts/migration/produkte_migration.py`** - 31 Kategorien, 658 Vorlagen,
   657 Varianten (Zuordnung ueber `itk_o11_id` auf der automatisch erzeugten Variante).
4. **`scripts/migration/preislisten_migration.py`** - 50 Listen, 1.875 Regeln,
   1 Regel ohne Produktbezug.
5. **`scripts/migration/verkauf_abo_stammdaten_abgleich.py`** - read-only Zuordnungsbericht.
6. Doku: `docs/migration/stammdaten-kontakte-produkte-preislisten.md`,
   `docs/migration/verkauf_abo_stammdaten-abgleich.md`.

## Ergebnis lokal

| Lauf | Ergebnis |
|---|---|
| Kontakte 1. Lauf | 123 Tags, 169 Anreden, 6.020 Kontakte, 32 nicht zuordenbar, 0 Fehler |
| Kontakte 2. Lauf | 0 Neuanlagen, 6.020 erkannt |
| Produkte 1. Lauf | 31 Kategorien, 658 Vorlagen, 657 Varianten, 0 Fehler |
| Produkte 2. Lauf | 0 Neuanlagen |
| Preislisten 1. Lauf | 50 Listen, 1.875 Regeln, 1 nicht zuordenbar, 0 Fehler |
| Preislisten 2. Lauf | 0 Neuanlagen |

## Erkenntnisse, die Zeit gekostet haben (Wiederholung vermeiden)

- `itk_crm` erzwingt `UNIQUE(ref)`. Odoo-18-Demopartner belegten 8 benoetigte Referenzen;
  deren `ref` wird geleert (Datensaetze bleiben). Loesung im Skript, Abschnitt 1c.
- `base_vat` blockierte historische USt-IDs: `context={"no_vat_validation": True}`.
- Bestandsmessung **muss** `context={"active_test": False}` nutzen, sonst werden
  archivierte Kontakte bei jedem Lauf neu angelegt (UNIQUE-Konflikt).
- `partner_firstname` (Odoo 18) verlangt Vor-/Nachnamen; 32 namenlose Odoo-11-Kontakte
  koennen deshalb nicht angelegt werden.
- `product.template.description` ist in Odoo 18 HTML (Odoo 11: Text) - Konvertierung
  ueber `text_nach_html()`.
- Preislistenregeln mit `base = pricelist` brauchen `base_pricelist_id`.
- Steuern: Odoo 11 "20% Umsatzsteuer" vs Odoo 18 "20% Ust" - Zuordnung ueber Betrag und
  Typ, bei Mehrdeutigkeit Namensaehnlichkeit. Vorlaeufig, siehe offene Punkte.

## Offen (Reihenfolge fuer die naechste Sitzung)

1. **Verkauf migrieren** (2.514 Auftraege, 4.076 Zeilen) mit `sale.order`/`sale.order.line`,
   Erkennung ueber `itk_o11_id`, danach Idempotenzlauf.
2. **Abonnements migrieren** (1.788 Abos, 2.459 Zeilen).
3. Browserabnahme lokal und VM, Regression, Testdaten entfernen, Dreistand.
4. Entscheidungen von Anna einholen:
   - 32 Kontakte ohne Namen (Datei `kontakte_ohne_namen.json` ausserhalb Git),
   - Steuerzuordnung 20% USt/Vorsteuer bestaetigen,
   - Odoo-11-Abrechnungseinheiten ("13 Gemeinden") ueber `to_multiply_by_factor` abbilden?
   - 1 Preislistenregel ohne Produktbezug.
