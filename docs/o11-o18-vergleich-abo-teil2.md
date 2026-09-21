# Abonnements / Subscriptions: Teil 2 - Vollstaendiges Feldinventar

## Teil 2: Vollstaendiges Feldinventar (18.09.2026, Session 118)

Grundlage: `fields_get` in Odoo 11 Prod (read-only) und Odoo 18 (lokal), Nutzung je Feld per `search_count`.
Die Feldnamen sind in beiden Systemen **identisch** - das Abo-Modul stammt in beiden Systemen aus derselben
ITK-Codebasis (`itk_subscription`).

### 1. Modell sale.subscription (31 Felder mit Datenbezug + berechnete Felder)

| Feld | Beschriftung (Odoo 11) | Typ/Relation | req | readonly | store/compute | Nutzung O11 (von 1.764) | Ziel in Odoo 18 | Einstufung |
|---|---|---|---|---|---|---|---|---|
| `analytic_account_id` | Kostenstelle | many2one/account.analytic.account | - | - | store | 0 | analytic_account_id (many2one) | 1:1 (Datenbestand 0) |
| `close_reason_id` | Grund für die Beendigung | many2one/sale.subscription.close.reason | - | - | store | 291 | close_reason_id (many2one) | 1:1 |
| `code` | Referenz | char | ja | - | store | 1764 | code (char) | 1:1 |
| `company_id` | Unternehmen | many2one/res.company | ja | - | store | 1764 | company_id (many2one) | 1:1 |
| `contract_termination_period_number` | Kündigungsfrist | integer | - | ja | store | 1764 | contract_termination_period_number (integer) | 1:1 |
| `contract_termination_period_unit` | Vertragsende | selection | - | ja | store | 1764 | contract_termination_period_unit (selection) | 1:1 |
| `country_id` | Land | many2one/res.country | - | - | store | 1763 | country_id (many2one) | 1:1 |
| `date` | Enddatum | date | - | - | store | 52 | date (date) | 1:1 |
| `date_start` | Startdatum | date | - | - | store | 1764 | date_start (date) | 1:1 |
| `description` | Beschreibung | text | - | - | store | 35 | description (text) | 1:1 |
| `industry_id` | Branche | many2one/res.partner.industry | - | - | store | 0 | industry_id (many2one) | 1:1 (Datenbestand 0) |
| `minimum_contract_period` | Mindestvertragsdauer | boolean | - | - | store | 0 | minimum_contract_period (boolean) | 1:1 (Datenbestand 0) |
| `minimum_contract_period_number` | Mindestvertragsdauer | integer | - | ja | store | 1764 | minimum_contract_period_number (integer) | 1:1 |
| `minimum_contract_period_unit` | Mindestvertragsdauer | selection | - | ja | store | 1764 | minimum_contract_period_unit (selection) | 1:1 |
| `name` | Name | char | ja | - | store | 1764 | name (char) | 1:1 |
| `noticeperiod` | Kündigungsfrist | many2one/itk_subscription.noticeperiod | - | ja | store | 0 | noticeperiod (many2one) | 1:1 (Datenbestand 0) |
| `partner_id` | Kunde | many2one/res.partner | ja | - | store | 1764 | partner_id (many2one) | 1:1 |
| `payment_mandatory` | Automatische Bezahlung | boolean | - | - | store | 0 | payment_mandatory (boolean) | 1:1 (Datenbestand 0) |
| `payment_token_id` | Zahlungs-Token | many2one/payment.token | - | - | store | 0 | payment_token_id (many2one) | 1:1 (Datenbestand 0) |
| `pricelist_id` | Preisliste | many2one/product.pricelist | ja | - | store | 1764 | pricelist_id (many2one) | 1:1 |
| `recurring_invoice_line_ids` | Rechnungszeilen | one2many/sale.subscription.line | - | - | store | 1763 | recurring_invoice_line_ids (one2many) | 1:1 |
| `recurring_monthly` | Monatlich Wiederkehrende Einnahmen | float | - | ja | store | 1764 | recurring_monthly (float) | 1:1 |
| `recurring_next_date` | Start-Datum des nächsten Leistungs | date | - | - | store | 1764 | recurring_next_date (date) | 1:1 |
| `recurring_total` | Wiederkehrender Preis | float | - | ja | store | 1764 | recurring_total (float) | 1:1 |
| `sale_order_confirmation_date` | Nutzungsvereinbarung vom | date | - | - | store | 1756 | sale_order_confirmation_date (date) | 1:1 |
| `sale_order_id` | Verkaufsauftrag | many2one/sale.order | - | - | store | 1722 | sale_order_id (many2one) | 1:1 |
| `state` | Status | selection | ja | - | store | 1764 | state (selection) | 1:1 |
| `tag_ids` | Stichwörter | many2many/account.analytic.tag | - | - | store | 0 | tag_ids (many2many) | 1:1 (Datenbestand 0) |
| `template_id` | Vorlage für Abonnements | many2one/sale.subscription.template | ja | - | store | 1764 | template_id (many2one) | 1:1 |
| `user_id` | Verkäufer | many2one/res.users | - | - | store | 1763 | user_id (many2one) | 1:1 |
| `uuid` | Konto-UUID | char | ja | - | store | 1764 | uuid (char) | 1:1 |
| `currency_id` | Währung | many2one/res.currency | - | ja | store | n/a | currency_id (many2one) | 1:1 |
| `end_of_contract_date` | Vertragsende-Datum | date | - | ja | store | n/a | end_of_contract_date (date) | 1:1 |
| `invoice_count` | Rechnungsanzahl | integer | - | ja | store | n/a | invoice_count (integer) | 1:1 |
| `recurring_amount_tax` | Steuern | float | - | ja | store | n/a | recurring_amount_tax (float) | 1:1 |
| `recurring_amount_total` | Gesamtbetrag | float | - | ja | store | n/a | recurring_amount_total (float) | 1:1 |
| `recurring_interval` | Wiederhole alle | integer | - | ja | store | n/a | recurring_interval (integer) | 1:1 |
| `recurring_rule_type` | Wiederholung | selection | - | ja | store | n/a | recurring_rule_type (selection) | 1:1 |
| `sale_order_count` | Verkaufsauftragsanzahl | integer | - | ja | store | n/a | sale_order_count (integer) | 1:1 |

### 2. Modell sale.subscription.line (11 Felder)

| Feld | Beschriftung (Odoo 11) | Typ/Relation | req | readonly | store/compute | Nutzung O11 (von 2.434) | Ziel in Odoo 18 | Einstufung |
|---|---|---|---|---|---|---|---|---|
| `analytic_account_id` | Aboauftrag | many2one/sale.subscription | - | - | store | 2434 | analytic_account_id (many2one) | 1:1 |
| `discount` | Rabatt (%) | float | - | - | store | 1395 | discount (float) | 1:1 |
| `name` | Beschreibung | text | ja | - | store | 2434 | name (text) | 1:1 |
| `partner_id` | Partner | many2one/res.partner | - | - | store | 2345 | partner_id (many2one) | 1:1 |
| `price_subtotal` | Zwischensumme | float | - | ja | store | 2434 | price_subtotal (float) | 1:1 |
| `price_unit` | Preis pro ME | float | ja | - | store | 2434 | price_unit (float) | 1:1 |
| `product_id` | Produkt | many2one/product.product | ja | - | store | 2434 | product_id (many2one) | 1:1 |
| `qty_multiplication_factor` | Multiplication Factor/Thsd | integer | - | - | store | 2434 | qty_multiplication_factor (integer) | 1:1 |
| `quantity` | Menge | float | - | - | store | 2434 | quantity (float) | 1:1 |
| `salesperson_id` | Verkäufer | many2one/res.users | - | - | store | 2343 | salesperson_id (many2one) | 1:1 |
| `uom_id` | Mengeneinheit | many2one/product.uom | ja | - | store | 2434 | uom_id (many2one) | Transformation |

### 3. Status- und Intervalle (Selections) - identisch

```
state           draft=Neu | open=Laufend | pending=Zu erneuern | close=Abgeschlossen | cancel=Abgebrochen
                in beiden Systemen wortgleich; Odoo 11 nutzt pending nicht (0 Datensaetze)
recurring_rule_type  daily=Tag(e) | weekly=Woche(n) | monthly=Monat(e) | yearly=Jahr(e)   (identisch)
Odoo 11 Verteilung: yearly 1.736 | monthly 28 | weekly 0 | daily 0
Odoo 11 Intervalle (recurring_interval): 1 (1.740x), 3 (24x)
```

### 4. Die 42 Abonnements ohne Verkaufsauftrag

```
Anzahl 42 von 1.764 (2,4 %)
Zustaende:  open 24 | cancel 16 | close 2
Vorlagen:   J - Jahresabrechnung-Abonnement 39 | j - Quartalsabrechnung-Abonnement 2 |
            J- Jahresabrechnungsabo-Mindestvertragsdauer 12 Monate 1
Intervalle: yearly 39 | monthly 3
Namenskreis: NV-0xxxx mit Startdaten 2013/2014 (Altbestand aus der Vorgaengerloesung)
```
Bewertung: reiner Altbestand ohne Auftragsbezug, ueberwiegend beendet oder abgebrochen. Fuer die spaetere
Migration ist eine Auswahlregel noetig (Vorschlag: uebernehmen wie der jeweilige Status es vorgibt, oder
diese 42 als Altbestand getrennt entscheiden). Die Auswahlregel selbst ist Datenschritt - jetzt nicht
festgelegt. In Odoo 18 existiert dazu bereits ein Testdatensatz (185, NV-00962, Start 2013).

### 5. Zeilenmodell (Produkte, Mengen, Preise, Multiplikationsfaktor)

```
2.434 Zeilen, alle mit Produkt, Menge, Preis, Mengeneinheit, Beschreibung und Multiplikationsfaktor
  product_id 2434 | quantity 2434 | price_unit 2434 | price_subtotal 2434 | uom_id 2434
  qty_multiplication_factor 2434 (Multiplikationsfaktor pro 1.000, integer - in O11 UND O18 vorhanden,
      kommt aus itk_multifactor; alle 2.434 Zeilen haben einen Wert ungleich 0)
  discount 1395 (57 %) | partner_id 2345 | salesperson_id 2343
Verknuepfung Zeile -> Abo: analytic_account_id (Beschriftung "Aboauftrag", many2one sale.subscription)
   - in Odoo 11 UND Odoo 18 derselbe Feldname (OCA-Erbe). Ein Feld subscription_id gibt es nicht.
```

### 6. Einordnung der Felder

```
1:1                          alle Felder mit Datenbezug, gleicher Name, gleicher Typ/Relation
1:1 (Datenbestand 0)         analytic_account_id, industry_id, minimum_contract_period, noticeperiod,
                             payment_mandatory, payment_token_id, tag_ids
berechnet                    contract_termination_period_unit u. a. berechnete Felder (nicht gespeichert)
nur Odoo 18                  has_message (technisch)
obsolet                      __last_update (Odoo-11-Infrastruktur)
kein Ziel vorhanden          keines
Transformation               keines
Klaerung noetig              1) recurring_next_date: Beschriftung unterscheidet sich
                                (Odoo 11 "Start-Datum des nächsten Leistungszeitraums",
                                 Odoo 18 "Datum der nächsten Rechnung") - Funktion identisch,
                                Wortlaut entscheiden. 2) Auswahlregel fuer die 42 Abos ohne Auftrag.
```

### 7. Labelunterschiede (vollstaendig)

```
recurring_next_date   O11: Start-Datum des nächsten Leistungszeitraums
                      O18: Datum der nächsten Rechnung
Alle uebrigen Beschriftungen stimmen zwischen Odoo 11 und Odoo 18 ueberein.
```

### 8. Ergebnis

Das Abo-Modell ist zwischen Odoo 11 Prod und Odoo 18 **strukturell identisch**: gleiche Feldnamen, gleiche
Typen, gleiche Relationen, gleiche Selection-Werte, gleiche Nutzung. Es gibt kein Feld in Odoo 11 ohne Ziel
und keine notwendige Transformation. Fuer die spaetere Migration sind daher reine 1:1-Zuordnungen moeglich.
Offen bleiben nur die Auswahlregel (42 Abos ohne Auftrag) und die Wortlaut-Entscheidung bei
`recurring_next_date`.
