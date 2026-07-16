# Datenmigrations-Checkliste: Odoo 11 → Odoo 18

> Diese Checkliste ersetzt die historischen `itk_initial_*`-Module und `itk_data_setup`.
> Keines dieser Module wird als Odoo-18-Modul migriert — die Daten werden über
> CSV-Export/Import bzw. Migrationsskripte übernommen.

## Bereits in Odoo 18 vorhanden (NICHT importieren)

| Datenbereich | In Odoo 18 | Quelle |
|---|---|---|
| Österreichische Bundesländer (9) | ✅ Vorhanden | Odoo-18-Standard |
| Product Types (6) | ✅ Vorhanden | Session 6 (manuell erstellt) |
| Status-of-Community (6) | ❌ Fehlt | War in `itk_initial_data_import`, muss aus Odoo 11 exportiert werden |
| Community-Magnitude-Klassen (14) | ✅ Vorhanden | itk_crm (Session 16) |

## Odoo 18 Testdaten (vor Import bereinigen)

| Modell | Anzahl | Aktion |
|---|---|---|
| res.partner | 11 | Löschen (Testdaten) |
| product.template | 11 | Löschen (Testdaten) |
| product.product | ~11 | Löschen (Testdaten) |
| sale.order | 14 | Löschen (Testdaten) |
| sale.order.line | 24 | Löschen (Testdaten) |
| sale.subscription | 4 | Löschen (Testdaten) |
| sale.subscription.line | ? | Löschen (Testdaten) |

---

## Datenmigrationsplan (nach Importreihenfolge)

### Phase 1: Stammdaten ohne Abhängigkeiten

#### 1.1 Bundesländer
- **Odoo-11-Quellmodell:** `res.country.state` (aus `itk_data_setup`)
- **Relevante Felder:** name, code, country_id
- **Anzahl:** 9
- **Odoo-18-Zielmodell:** `res.country.state`
- **Status:** ✅ BEREITS IN ODOO 18 VORHANDEN — **nicht importieren**
- **Validierung:** `search_count([('country_id.code','=','AT')])` muss 9 sein

#### 1.2 Zahlungsbedingungen
- **Odoo-11-Quellmodell:** `account.payment.term` (aus `itk_data_setup`)
- **Relevante Felder:** name, note, line_ids
- **Anzahl:** ~5 ITK-spezifische (plus ~5 Standard)
- **Odoo-18-Zielmodell:** `account.payment.term`
- **Abgleichsschlüssel:** name
- **Importreihenfolge:** Phase 1
- **Importweg:** CSV-Export aus Odoo 11 → Import Odoo 18
- **ACHTUNG:** Standard-Zahlungsbedingungen (Sofort, 15 Tage, 30 Tage etc.) bereits in Odoo 18 vorhanden — nur ITK-spezifische importieren, Duplikate vermeiden
- **Validierung:** Count vergleichen, manuelle Sichtprüfung der Namen

#### 1.3 Sale-Layout-Kategorien
- **Odoo-11-Quellmodell:** `sale.layout.category` (aus `itk_data_setup`)
- **Relevante Felder:** name, sequence
- **Anzahl:** ~3-5
- **Odoo-18-Zielmodell:** `sale.layout_category` (Odoo 18 hat `sale.layout_category`)
- **Abgleichsschlüssel:** name
- **Importreihenfolge:** Phase 1
- **Importweg:** CSV-Export aus Odoo 11 → Import Odoo 18
- **Validierung:** Count, Namen prüfen

#### 1.4 Produktkategorien
- **Odoo-11-Quellmodell:** `product.category` (aus `itk_initial_product_import`)
- **Relevante Felder:** name, parent_id, sequence
- **Anzahl:** 30 (Odoo 11) — davon ~8 ITK-spezifische
- **Odoo-18-Zielmodell:** `product.category`
- **Abgleichsschlüssel:** name (oder external ID falls migrierbar)
- **Importreihenfolge:** Phase 1 (vor Produkten)
- **Abhängigkeiten:** parent_id → zuerst Eltern, dann Kinder
- **Importweg:** CSV-Export → Import (händisch Parent-ID-Mapping)
- **ACHTUNG:** Odoo-18-Standardkategorien (All, Sales) nicht überschreiben
- **Validierung:** `search_count([])` muss 3 + ITK-Kategorien ergeben

#### 1.5 Produkte (Templates + Varianten)
- **Odoo-11-Quellmodell:** `product.template` + `product.product` (aus `itk_initial_product_import`)
- **Relevante Felder:** name, type, list_price, recurring_invoice, subscription_template_id, product_type_id, categ_id, uom_id, description
- **Anzahl:** 645 Templates / 644 Varianten (Odoo 11)
- **Odoo-18-Zielmodell:** `product.template` / `product.product`
- **Abgleichsschlüssel:** name + internal_ref (default_code)
- **Importreihenfolge:** Phase 1 (vor Aufträgen/Abos)
- **Abhängigkeiten:** product_type_id (itk_product), subscription_template_id (itk_subscription), categ_id, uom_id
- **Importweg:** CSV-Export → Import. `product_type_id` über external ID mappen. `subscription_template_id` über Abo-Template-Name referenzieren.
- **ACHTUNG:** Felder `recurring_invoice` und `subscription_template_id` sind in Odoo 18 durch `itk_subscription` vorhanden
- **Validierung:** `search_count([])` muss ~645 sein, Felder `product_type_id`, `recurring_invoice` befüllt

#### 1.6 Preislisten
- **Odoo-11-Quellmodell:** `product.pricelist` (aus `itk_initial_data_habasis_gszk_import` + Odoo Standard)
- **Relevante Felder:** name, currency_id, item_ids
- **Anzahl:** ~3 (inkl. GSZK-Preisliste)
- **Odoo-18-Zielmodell:** `product.pricelist`
- **Abgleichsschlüssel:** name
- **Importreihenfolge:** Phase 1
- **Importweg:** CSV oder manuell anlegen (wenige Datensätze)
- **Validierung:** Namen prüfen, Währung muss EUR sein

---

### Phase 2: Partner/Kontakte (das Kernstück)

#### 2.1 Gemeinden/Kontakte (mit GKZ)
- **Odoo-11-Quellmodell:** `res.partner` (aus `itk_initial_data_import`)
- **Relevante Felder:** ref (GKZ), name, street, city, zip, website, population, population_update, is_company, country_id, state_id, status_of_community, community_magnitude, email, phone, latitude, longitude, austria_wiki_url, vat
- **Anzahl:** 2.275 (mit ref/GKZ) von insgesamt 5.786 Partnern
- **Odoo-18-Zielmodell:** `res.partner`
- **Abgleichsschlüssel:** ref (GKZ-Nummer) oder name
- **Importreihenfolge:** Phase 2 (nach States, vor Aufträgen)
- **Abhängigkeiten:** state_id (res.country.state), status_of_community (itk_crm.statusofcommunity), country_id (base.at)
- **Importweg:** CSV-Export aus Odoo 11 → Import in Odoo 18. `state_id` über Code mappen. `status_of_community` über external ID.
- **PITFALL:** `status_of_community` ist ein Feld aus `itk_crm` — das Modul muss in Odoo 18 installiert sein!
- **PITFALL:** `community_magnitude` wird in Odoo 18 durch itk_crm automatisch berechnet (abhängig von `population`) — nicht mitimportieren!
- **Validierung:** `search_count([('ref','!=',False)])` sollte ~2.275 sein

#### 2.2 Straßen, Websites, Koordinaten, Bürgermeister
- **Odoo-11-Quellmodell:** `res.partner` (Felder aus `itk_initial_partner_data_import` + `itk_initial_data_habasis_gkz_strasse_import`)
- **Relevante Felder:** street, website, latitude, longitude, austria_wiki_url, mayor_name
- **Anzahl:** In den 2.275 Gemeinde-Partnern enthalten
- **Odoo-18-Zielmodell:** `res.partner`
- **Importreihenfolge:** Phase 2 (zusammen mit Gemeinde-Import, dieselben Records)
- **Abhängigkeiten:** Keine (Felder auf bestehenden Partner-Records)
- **Importweg:** Im gleichen CSV-Export wie 2.1 enthalten — kein separater Import nötig
- **Validierung:** `search_count([('website','!=',False)])` prüfen

#### 2.3 Nicht-GKZ-Kontakte
- **Odoo-11-Quellmodell:** `res.partner` (aus `itk_initial_partner_nogkz_data_import`)
- **Relevante Felder:** name, is_company, street, city, zip, country_id, state_id, vat
- **Anzahl:** ~50 (GEMDAT, Land NÖ, etc.)
- **Odoo-18-Zielmodell:** `res.partner`
- **Abgleichsschlüssel:** name + vat
- **Importreihenfolge:** Phase 2
- **Importweg:** Im Gemeinde-CSV enthalten (alle 5.786 Partner exportieren, Filtern nicht nötig)
- **Validierung:** Manuelle Prüfung einiger Nicht-GKZ-Partner

#### 2.4 Gemeindewappen/Bilder
- **Odoo-11-Quellmodell:** `res.partner` Feld `image_1920` (aus `itk_initial_partner_emblem_import`)
- **Relevante Felder:** image_1920 (base64)
- **Anzahl:** 3.102 Partner mit Bild
- **Odoo-18-Zielmodell:** `res.partner` → `image_1920`
- **Abgleichsschlüssel:** ref (GKZ) → id
- **Importreihenfolge:** Phase 2 (nach Partner-Import)
- **Importweg:** **Separates Migrationsskript** — CSV-Export mit base64-Bildern ist extrem groß (mehrere GB). Besser: Python-Skript das Bilder aus Odoo 11 exportiert und über JSON-RPC in Odoo 18 importiert.
- **PITFALL:** `image_1920` ist das Odoo-18-Feld; Odoo 11 verwendet `image` (wird automatisch in image_1920 konvertiert beim Export)
- **Validierung:** `search_count([('image_1920','!=',False)])` ≈ 3.102

---

### Phase 3: Geschäftsdaten

#### 3.1 Historische Verkaufsaufträge
- **Odoo-11-Quellmodell:** `sale.order` + `sale.order.line`
- **Relevante Felder:** name, partner_id, date_order, confirmation_date, state, pricelist_id, team_id, order_line (product_id, quantity, price_unit)
- **Anzahl:** 2.258 Aufträge (Odoo 11)
- **Odoo-18-Zielmodell:** `sale.order` / `sale.order.line`
- **Abgleichsschlüssel:** name (Auftragsnummer)
- **Importreihenfolge:** Phase 3 (nach Partner + Produkte)
- **Abhängigkeiten:** partner_id, product_id, pricelist_id, team_id
- **Importweg:** CSV-Export → Import. partner_id über ref mappen. product_id über default_code oder name.
- **PITFALL:** `state`-Feld — historische Aufträge sollten mit state='sale' oder 'done' importiert werden. Keine draft-Aufträge.
- **PITFALL:** Odoo 18 hat `sale.order.line` ohne `subscription_id` (kommt separat)
- **Validierung:** `search_count([])` ≈ 2.258, alle states='sale' oder 'done'

#### 3.2 Abonnements und Abo-Positionen
- **Odoo-11-Quellmodell:** `sale.subscription` + `sale.subscription.line`
- **Relevante Felder:** name, partner_id, template_id, recurring_next_date, date_start, date_end, recurring_total, state, lines (product_id, quantity, price_unit)
- **Anzahl:** 1.682 Abos / 2.352 Positionen (Odoo 11)
- **Odoo-18-Zielmodell:** `sale.subscription` / `sale.subscription.line`
- **Abgleichsschlüssel:** name (Abo-Code) oder partner_id + template_id
- **Importreihenfolge:** Phase 3 (nach Aufträgen)
- **Abhängigkeiten:** partner_id, template_id (sale.subscription.template), product_id
- **Importweg:** CSV-Export → Import. Templates über external ID aus itk_subscription mappen.
- **PITFALL:** `recurring_next_date` und `date_start` als date-Objekte, nicht Strings
- **Validierung:** `search_count([])` ≈ 1.682, Template-Referenzen valide

#### 3.3 Auftrags-Abo-Verknüpfungen
- **Odoo-11-Quellmodell:** `sale.order.line` → Feld `subscription_id`
- **Relevante Felder:** subscription_id (Many2one zu sale.subscription)
- **Anzahl:** ~2.054 Verknüpfungen (aus `connect_contracts_orders_*.xml`)
- **Odoo-18-Zielmodell:** `sale.order.line` → `subscription_id`
- **Abgleichsschlüssel:** order_line name + subscription name
- **Importreihenfolge:** Phase 3 (nach Aufträgen + Abos)
- **Importweg:** **Migrationsskript** — Aufträge und Abos müssen bereits importiert sein, dann über JSON-RPC die `subscription_id` nachsetzen
- **Validierung:** `search_count([('subscription_id','!=',False)])`

---

### Phase 4: GSZK-spezifische Daten

#### 4.1 GSZK-Kunden, Produkte, Preislisten, Aufträge
- **Odoo-11-Quellmodell:** `res.partner`, `product.pricelist`, `sale.order`, `sale.subscription` (aus `itk_initial_data_habasis_gszk_import`)
- **Relevante Felder:** Siehe Phasen 1-3, gefiltert auf GSZK-spezifische Datensätze
- **Anzahl:** Unbekannt (~150 GSZK-Kunden + deren Aufträge/Abos)
- **Odoo-18-Zielmodell:** Siehe Phasen 1-3
- **Abgleichsschlüssel:** GSZK-spezifisches Flag oder Benutzer-Zuordnung
- **Importreihenfolge:** Phase 4 (nach allen anderen Daten)
- **Importweg:** Diese Daten sind im Gesamtexport der Phasen 1-3 enthalten — separater Export nur nötig, wenn GSZK-spezifische Felder (z.B. GSZK-Preisliste, GSZK-Benutzer) in Odoo 18 manuell neu konfiguriert werden müssen
- **PITFALL:** `__export__` external IDs aus dem XML sind in Odoo 18 ungültig. GSZK-Preisliste und GSZK-Benutzer müssen in Odoo 18 neu erstellt werden, dann die Zuordnung manuell oder per Skript setzen.
- **Validierung:** Manuelle Prüfung der GSZK-Kunden

---

## Zusammenfassung: Importreihenfolge

```
Phase 1 — Stammdaten (keine Abhängigkeiten)
  1.1  Bundesländer ................... ✅ BEREITS DA
  1.2  Zahlungsbedingungen ............ CSV-Import (nur ITK-spezifische)
  1.3  Sale-Layout-Kategorien ......... CSV-Import
  1.4  Produktkategorien .............. CSV-Import
  1.5  Produkte (Templates+Varianten) . CSV-Import
  1.6  Preislisten .................... CSV oder manuell

Phase 2 — Partner (abhängig von States, Produkten)
  2.1  Gemeinden/Kontakte mit GKZ ..... CSV-Import (5.786 Partner)
  2.2  Straßen/Websites/Koordinaten ... im 2.1-CSV enthalten
  2.3  Nicht-GKZ-Kontakte ............. im 2.1-CSV enthalten
  2.4  Gemeindewappen ................. SEPARATES BILD-SKRIPT (nach 2.1)

Phase 3 — Geschäftsdaten (abhängig von Partnern + Produkten)
  3.1  Verkaufsaufträge ............... CSV-Import
  3.2  Abonnements + Positionen ....... CSV-Import
  3.3  Auftrags-Abo-Verknüpfungen ..... Migrationsskript (JSON-RPC)

Phase 4 — GSZK-Daten
  4.1  GSZK-Konfiguration ............. Manuell + Prüfung
```

## Kontrollzahlen (Soll nach Import)

| Modell | Odoo 11 (IST) | Odoo 18 (SOLL) |
|---|---|---|
| res.country.state (AT) | 9 | 9 ✅ |
| itk_product.product_type | 6 | 6 ✅ |
| account.payment.term | ~10 | ~10 + ITK |
| product.category | 30 | ~33 (3 Standard + 30) |
| product.template | 645 | ~645 |
| product.product | 644 | ~644 |
| res.partner | 5.786 | ~5.775 (5.786 minus gelöschte Testdaten) |
| res.partner mit image | 3.102 | ~3.102 |
| sale.order | 2.258 | ~2.258 |
| sale.order.line | ? | ? |
| sale.subscription | 1.682 | ~1.682 |
| sale.subscription.line | 2.352 | ~2.352 |
