# Stammdaten Kontakte, Produkte, Preislisten: Strukturvergleich und Migration

Stand 12.11.2026, Session 142. Freigabe Anna Maierhofer (Option A).
Quelle: Odoo 11 Produktion `ITK_V1_a`, ausschliesslich lesend.
Ziel: Odoo 18 (`odoo18_test`), lokal und VM.

**Datenschutz:** Dieses Dokument enthaelt ausschliesslich Zaehlwerte, Odoo-IDs, Feldnamen
und technische Schluessel. Keine Namen, E-Mail-Adressen, Telefonnummern oder Adressen.
Zuordnungsdateien (JSON) liegen ausserhalb des Repositories unter
`%LOCALAPPDATA%\Temp\s142_web\`.

## 1 Umfang

| Bereich | Odoo 11 | migriert nach Odoo 18 |
|---|---|---|
| Kontakt-Tags (`res.partner.category`) | 123 | 123 |
| Anreden (`res.partner.title`) | 169 | 169 |
| Kontakte (`res.partner`) | 5.851 aktiv + 201 archiviert = 6.052 gelesen | 6.020; 32 nicht zuordenbar |
| Produktkategorien (`product.category`) | 31 | 31 |
| Produktvorlagen (`product.template`) | 658 | 658 |
| Produktvarianten (`product.product`) | 657 | 657 (Zuordnung auf die automatisch erzeugte Variante) |
| Preislisten (`product.pricelist`) | 50 | 50 |
| Preislistenregeln (`product.pricelist.item`) | 1.876 | 1.875; 1 nicht zuordenbar |

## 2 Strukturvergleich

### 2.1 Kontakte (`res.partner`)

Odoo 11 fuehrt 169 Felder, Odoo 18 246. Uebernommen werden die fachlich benoetigten
Identitaets-, Adress- und Klassifikationsfelder:

`name`, `is_company`, `active`, `ref`, `vat`, `street`, `street2`, `zip`, `city`,
`country_id` (ueber Laendercode), `email`, `phone`, `mobile`, `website`, `function`,
`title` (ueber `res.partner.title`, 169 Anreden neu angelegt), `comment` (Text zu HTML),
`category_id` (ueber `res.partner.category`), `parent_id` (Firmenhierarchie).

**Bewusst nicht uebernommen** (Odoo 18 fuehrt diese Felder nicht mehr):

| Odoo-11-Feld | Grund |
|---|---|
| `customer`, `supplier` | In Odoo 18 ersatzlos entfallen; die Eigenschaft ergibt sich aus Verkaufs-/Einkaufsbelegen |
| `team_id` | Nur 45 Kontakte betroffen; in Odoo 18 gehoert das CRM-Team zum Lead, nicht zum Kontakt |
| `sla_id`, `support_ticket_*` | Helpdesk-Felder; Helpdesk wurde ohne Ticketdaten abgenommen |
| `opt_out`, `signup_*` | Massenmail-/Portal-Felder ohne fachliche Entsprechung |
| `image`, `image_medium`, `image_small` | Odoo 18 fuehrt Bilder als `image_1920`; keine Bilddaten in Odoo 11 vorhanden |

**Strukturelle Anpassung in Odoo 18:** neues Modul `itk_migration_keys` mit dem technischen
Feld `itk_o11_id` (Integer, indexiert, nicht in Ansichten sichtbar) auf `res.partner`,
`res.partner.category`, `product.template`, `product.product`, `product.category`,
`product.pricelist`, `product.pricelist.item`, `sale.order`, `sale.subscription`.
Damit erkennt jeder Lauf bereits uebernommene Datensaetze, ohne Namen zu vergleichen.

**Sonderfaelle, die beim Schreiben aufgetreten sind (und wie sie geloest wurden):**

| Fall | Anzahl | Loesung |
|---|---|---|
| `itk_crm` erzwingt `UNIQUE(ref)`; 8 Odoo-18-Demopartner belegten benoetigte Referenzen | 8 (4 + 2 + 2 in mehreren Laeufen) | `ref` der Demopartner geleert, Datensaetze bleiben erhalten (Freigabe: Demodaten duerfen bereinigt werden) |
| Kontakte ohne Namen (Odoo-18-Pflichtfeld) | 32 | **nicht angelegt**, als "nicht zuordenbar" gezaehlt, Anna zur Entscheidung vorgelegt |
| Archivierte Kontakte wurden bei jedem Lauf neu angelegt (Bestandsmessung ohne `active_test=False`) | 201 | Bestand wird inklusive archivierter Datensaetze gelesen |
| USt-IDs historischer Formate blockierten `base_vat` | 216 Kontakte in 4 Bloecken | `no_vat_validation` beim Anlegen, Werte unveraendert uebernommen |
| `partner_firstname` verlangt Vor-/Nachname | betraf die 32 namenlosen Kontakte | siehe oben |
| Modul `partner_firstname` (Odoo 18) vs. freies Namensfeld (Odoo 11) | alle Personen | `name` bleibt massgeblich, Odoo 18 splittet automatisch |

### 2.2 Produkte (`product.template`)

Odoo 11 fuehrt 134 Felder, Odoo 18 141. Die ITK-Produkttypen existieren in Odoo 18
bereits 1:1 ueber das Modul `itk_product` (`type`-Auswahl mit `consu`, `service`,
`general`, `onlineservice`, `sw`, `consulting`, `platform`, `hw`, `project`) sowie das
Modell `itk_product.product_type` (6 Datensaetze, identische Codes OS/SW/C/P/HW/FP).
Ein Typ-Mapping ist deshalb **nicht** noetig — die Odoo-11-Werte werden unveraendert
geschrieben.

Uebernommen: `name`, `type`, `categ_id`, `list_price` (aus Odoo-11-`lst_price`),
`standard_price`, `default_code`, `barcode`, `description` (Text zu HTML),
`description_sale`, `description_purchase`, `sale_ok`, `purchase_ok`, `invoice_policy`,
`taxes_id`, `supplier_taxes_id`, `product_type_id`, `active`, `uom_id`/`uom_po_id`.

Nicht uebernommen (Felder existieren in Odoo 18 nicht oder gehoeren zu nicht migrierten
Modulen): `website_*`, `public_categ_ids`, `rating_*`, `rental`, `accessory_product_ids`,
`alternative_product_ids`, `property_stock_account_*`, `property_valuation`,
`product_image_ids`, `pricelist_id`.

**UoM:** Odoo 11 fuehrt 33 "Mengeneinheiten", die fachlich Abrechnungseinheiten sind
("13 Gemeinden", "15 Gemeinden"). Odoo 18 hat Standardeinheiten (`uom.uom`). Die Produkte
werden mit der Standardeinheit angelegt; die abweichenden Odoo-11-Einheiten werden
**nicht** als neue Einheiten erfunden. **Offener Punkt fuer Anna** (siehe Abschnitt 5).

**Steuern:** Odoo 11 und Odoo 18 benennen Steuern unterschiedlich ("20% Umsatzsteuer" vs
"20% Ust"). Zuordnung ueber Betrag und Verwendungsart, bei mehreren Kandidaten ueber
Namensaehnlichkeit:

| Odoo-11-Steuer | Betrag | Odoo-18-Steuer-ID | Kandidaten | Status |
|---|---|---|---|---|
| 20% Umsatzsteuer | 20,0 | 15 | 3 | mehrdeutig, vorlaeufig zugeordnet |
| 20% Vorsteuer | 20,0 | 57 | 14 | mehrdeutig, vorlaeufig zugeordnet |

**Offener Punkt fuer Anna** (siehe Abschnitt 5).

### 2.3 Preislisten (`product.pricelist`)

Odoo 11 fuehrt 18 Felder, Odoo 18 37. Uebernommen: `name`, `currency_id`, `active`
sowie je Regel `applied_on`, `product_tmpl_id`, `product_id`, `categ_id`, `min_quantity`,
`compute_price`, `fixed_price`, `percent_price`, `base`, `base_pricelist_id`,
`price_discount`, `price_round`, `price_surcharge`, `date_start`, `date_end`.

Nicht uebernommen, weil in Odoo 18 nicht vorhanden:
`code` (0 belegt), `selectable` (0 belegt), `discount_policy` (in Odoo 18 am Auftrag),
`website_id` (website_sale wird nicht migriert).

Regelverteilung Odoo 11: 1.473 Produktvorlage, 268 Variante, 107 Kategorie, 28 global;
473 Festpreis, 1.397 Formel, 6 Prozent.

## 3 Migrationsergebnis (lokal, Stand 12.11.2026)

| Lauf | Ergebnis |
|---|---|
| Kontakte, 1. Lauf (Schreiben) | 123 Tags, 169 Anreden, 6.020 Kontakte angelegt; 32 ohne Namen; 0 Fehler |
| Kontakte, 2. Lauf (Idempotenz) | **0 Neuanlagen**, 6.020 erkannt, 0 Fehler |
| Produkte, 1. Lauf | 31 Kategorien, 658 Vorlagen, 657 Varianten; 0 Fehler |
| Produkte, 2. Lauf (Idempotenz) | **0 Neuanlagen**, 658/31 erkannt, 0 Fehler |
| Preislisten, 1. Lauf | 50 Listen, 1.875 Regeln; 1 Regel ohne Produktbezug; 0 Fehler |
| Preislisten, 2. Lauf (Idempotenz) | **0 Neuanlagen**, 50/1.875 erkannt, 0 Fehler |

Wiederholte Laeufe sind idempotent, weil jeder Datensatz ueber `itk_o11_id` erkannt wird.

## 4 Reproduzierbare Skripte

| Bereich | Skript | Trockenlauf | Schreiben |
|---|---|---|---|
| Kontakte | `scripts/migration/kontakte_migration.py` | Standard | `--ausfuehren --ich-habe-freigabe` |
| Produkte | `scripts/migration/produkte_migration.py` | Standard | `--ausfuehren --ich-habe-freigabe` |
| Preislisten | `scripts/migration/preislisten_migration.py` | Standard | `--ausfuehren --ich-habe-freigabe` |
| Abhaengigkeiten | `scripts/migration/verkauf_abo_stammdaten_abgleich.py` | read-only | - |

Mapping-Export: `--mapping <datei.json>` (nur IDs, ausserhalb des Repositories ablegen).

## 5 Offene Punkte zur Entscheidung

1. **32 Kontakte ohne Namen** (IDs in `%LOCALAPPDATA%\Temp\s142_web\kontakte_ohne_namen.json`).
   Odoo 18 verlangt einen Namen. Optionen: (a) nicht uebernehmen lassen, (b) mit einem
   sachlichen Platzhalter anlegen, (c) vorher in Odoo 11 bereinigen lassen.
2. **Steuerzuordnung 20% USt / 20% Vorsteuer** ist betragsbasiert und vorlaeufig
   (Odoo-18-Steuer 15 bzw. 57 bei 3 bzw. 14 Kandidaten). Fachliche Bestaetigung noetig,
   weil die Abrechnung bereits abgenommen ist.
3. **Odoo-11-Mengeneinheiten** ("13 Gemeinden" usw.) sind Abrechnungseinheiten ohne
   Odoo-18-Entsprechung. Vorschlag: ueber `to_multiply_by_factor` im Modul `itk_product`
   abbilden; ohne Entscheidung bleiben die Produkte auf der Standardeinheit.
4. **1 Preislistenregel ohne Produktbezug** (o11_id im Mapping-Export) - Zielprodukt
   existiert nicht in Odoo 18.

## 6 Noch nicht durchgefuehrt

Verkauf (2.514 Auftraege) und Abonnements (1.788) sind **noch nicht** migriert. Nach dem
Stammdatenlauf stehen die Voraussetzungen bereit; der Beleglauf, die Browserabnahme, die
Regression und der Dreistand folgen im naechsten Schritt.
