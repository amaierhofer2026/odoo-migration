# Gezielter Migrations-Check Bereich Verkauf: Feldzuordnung Odoo 11 -> Odoo 18

Stand: 29.09.2026, Session 121. **Nur Analyse.** Odoo 11 Prod ausschliesslich read-only,
Odoo 18 wurde nicht veraendert. Keine Datenmigration.

Statuswerte: 1:1 vorhanden / umbenannt / an anderer Stelle dargestellt /
durch Odoo-18-Funktion ersetzt / Transformationsregel erforderlich /
bewusst nicht zu uebernehmen / fehlende Zuordnung.

## 1. Zusammenfassung

```
sale.order       : 89 Felder, 39 belegt, 50 ohne Wert
sale.order.line  : 53 Felder, 33 belegt, 20 ohne Wert
Auswertung der belegten Felder: siehe Tabellen unten; Risiken/fehlende Zuordnungen am Ende.
```

## 2. Wertpruefungen in Odoo 11 (Auswahlwerte)

```
sale.order.state: {'sale': 2312, 'cancel': 147, 'draft': 5}
sale.order.invoice_status: {'invoiced': 1185, 'to invoice': 1127, 'no': 152}
sale.order.picking_policy: {'direct': 2464}
sale.order.line.state: {'sale': 3770, 'cancel': 235, 'draft': 6}
```

## 3. Feldzuordnung (nur belegte Felder)


### sale.order

| Odoo-11-Feld | Odoo-11-Bezeichnung | technisch | Odoo-18-Zielfeld | Odoo-18-technisch | Typ O11 -> O18 | Transformation | Status | belegt |
|---|---|---|---|---|---|---|---|---|
| access_token | Security Token | access_token | access_token | access_token | char -> char | - | **1:1 vorhanden** | 2464/2464 |
| administrative_contact_id | Administrativer Kontakt | administrative_contact_id | administrative_contact_id | administrative_contact_id | many2one -> many2one | - | **1:1 vorhanden** | 2/2464 |
| amount_tax | Steuern | amount_tax | amount_tax | amount_tax | monetary -> monetary | - | **1:1 vorhanden** | 2445/2464 |
| amount_total | Total | amount_total | amount_total | amount_total | monetary -> monetary | - | **1:1 vorhanden** | 2446/2464 |
| amount_untaxed | Nettobetrag | amount_untaxed | amount_untaxed | amount_untaxed | monetary -> monetary | - | **1:1 vorhanden** | 2446/2464 |
| company_id | Unternehmen | company_id | company_id | company_id | many2one -> many2one | - | **1:1 vorhanden** | 2464/2464 |
| confirmation_date | Bestätigung am | confirmation_date | confirmation_date | confirmation_date | datetime -> datetime | - | **1:1 vorhanden** | 2440/2464 |
| create_date | Erzeugt am | create_date | create_date | create_date | datetime -> datetime | - | **1:1 vorhanden** | 2464/2464 |
| create_uid | Erstellt von | create_uid | create_uid | create_uid | many2one -> many2one | - | **1:1 vorhanden** | 2464/2464 |
| date_order | Bestelldatum | date_order | date_order | date_order | datetime -> datetime | - | **1:1 vorhanden** | 2464/2464 |
| id | ID | id | id | id | integer -> integer | - | **1:1 vorhanden** | 2464/2464 |
| invoice_status | Status Rechnung | invoice_status | invoice_status | invoice_status | selection -> selection | - | **1:1 vorhanden** | 2464/2464 |
| message_follower_ids | Abonnenten | message_follower_ids | message_follower_ids | message_follower_ids | one2many -> one2many | - | **1:1 vorhanden** | 2464/2464 |
| message_ids | Nachrichten | message_ids | message_ids | message_ids | one2many -> one2many | - | **1:1 vorhanden** | 2464/2464 |
| name | Auftragsreferenz | name | name | name | char -> char | - | **1:1 vorhanden** | 2464/2464 |
| note | Geschäftsbedingungen | note | note (html) | note (html) | text -> html | text -> html | **Transformationsregel erforderlich** | 2442/2464 |
| opportunity_id | Chance | opportunity_id | opportunity_id | opportunity_id | many2one -> many2one | - | **1:1 vorhanden** | 128/2464 |
| order_line | Auftragszeilen | order_line | order_line | order_line | one2many -> one2many | - | **1:1 vorhanden** | 2452/2464 |
| origin | Referenzbeleg | origin | origin | origin | char -> char | - | **1:1 vorhanden** | 22/2464 |
| partner_id | Kunde | partner_id | partner_id | partner_id | many2one -> many2one | - | **1:1 vorhanden** | 2464/2464 |
| partner_invoice_id | Rechnungsadresse | partner_invoice_id | partner_invoice_id | partner_invoice_id | many2one -> many2one | - | **1:1 vorhanden** | 2464/2464 |
| partner_shipping_id | Lieferadresse | partner_shipping_id | partner_shipping_id | partner_shipping_id | many2one -> many2one | - | **1:1 vorhanden** | 2464/2464 |
| payment_term_id | Zahlungsbedingungen | payment_term_id | payment_term_id | payment_term_id | many2one -> many2one | - | **1:1 vorhanden** | 613/2464 |
| picking_ids | Pickaufträge | picking_ids | picking_ids | picking_ids | one2many -> one2many | - | **1:1 vorhanden** | 235/2464 |
| picking_policy | Auslieferungsbedingungen | picking_policy | picking_policy | picking_policy | selection -> selection | - | **1:1 vorhanden** | 2464/2464 |
| pricelist_id | Preisliste | pricelist_id | pricelist_id | pricelist_id | many2one -> many2one | - | **1:1 vorhanden** | 2464/2464 |
| procurement_group_id | Beschaffungsgruppe | procurement_group_id | procurement_group_id | procurement_group_id | many2one -> many2one | - | **1:1 vorhanden** | 240/2464 |
| product_category_id | Produktkategorie | product_category_id | product_category_id | product_category_id | many2one -> many2one | - | **1:1 vorhanden** | 47/2464 |
| sale_contact_id | Verkaufskontakt | sale_contact_id | sale_contact_id | sale_contact_id | many2one -> many2one | - | **1:1 vorhanden** | 3/2464 |
| state | Status | state | state (ohne 'done') + locked | state (ohne 'done') + locked | selection -> selection | Auswahlwerte ohne Entsprechung: ['done']; 'done' entfaellt -> state='sale' + locked=True | **Transformationsregel erforderlich** | 2464/2464 |
| subscription_management | Aboauftragsmanagement | subscription_management | subscription_management | subscription_management | selection -> selection | - | **1:1 vorhanden** | 2464/2464 |
| tag_ids | Stichwörter | tag_ids | tag_ids | tag_ids | many2many -> many2many | Relation crm.lead.tag -> crm.tag | **Transformationsregel erforderlich** | 1/2464 |
| team_id | Vertriebskanal | team_id | team_id | team_id | many2one -> many2one | - | **1:1 vorhanden** | 2464/2464 |
| technical_contact_id | Technischer Kontakt | technical_contact_id | technical_contact_id | technical_contact_id | many2one -> many2one | - | **1:1 vorhanden** | 1/2464 |
| user_id | Verkäufer | user_id | user_id | user_id | many2one -> many2one | - | **1:1 vorhanden** | 2464/2464 |
| validity_date | Ablaufdatum | validity_date | validity_date | validity_date | date -> date | - | **1:1 vorhanden** | 1/2464 |
| warehouse_id | Lager | warehouse_id | warehouse_id | warehouse_id | many2one -> many2one | - | **1:1 vorhanden** | 2464/2464 |
| write_date | Zuletzt aktualisiert am | write_date | write_date | write_date | datetime -> datetime | - | **1:1 vorhanden** | 2464/2464 |
| write_uid | Zuletzt aktualisiert durch | write_uid | write_uid | write_uid | many2one -> many2one | - | **1:1 vorhanden** | 2464/2464 |

### sale.order.line

| Odoo-11-Feld | Odoo-11-Bezeichnung | technisch | Odoo-18-Zielfeld | Odoo-18-technisch | Typ O11 -> O18 | Transformation | Status | belegt |
|---|---|---|---|---|---|---|---|---|
| amt_invoiced | Abgerechneter Betrag | amt_invoiced | amount_invoiced | amount_invoiced | monetary -> monetary | - | **umbenannt** | 1669/4011 |
| amt_to_invoice | Abzurechnender Betrag | amt_to_invoice | amount_to_invoice | amount_to_invoice | monetary -> monetary | - | **umbenannt** | 1950/4011 |
| create_date | Erstellt am | create_date | create_date | create_date | datetime -> datetime | - | **1:1 vorhanden** | 4011/4011 |
| create_uid | Erstellt von | create_uid | create_uid | create_uid | many2one -> many2one | - | **1:1 vorhanden** | 4011/4011 |
| discount | Rabatt (%) | discount | discount | discount | float -> float | - | **1:1 vorhanden** | 483/4011 |
| id | ID | id | id | id | integer -> integer | - | **1:1 vorhanden** | 4011/4011 |
| invoice_lines | Rechnungszeilen | invoice_lines | invoice_lines | invoice_lines | many2many -> many2many | Relation account.invoice.line -> account.move.line | **Transformationsregel erforderlich** | 1863/4011 |
| invoice_status | Status Rechnung | invoice_status | invoice_status | invoice_status | selection -> selection | - | **1:1 vorhanden** | 4011/4011 |
| is_downpayment | Ist eine Anzahlung | is_downpayment | is_downpayment | is_downpayment | boolean -> boolean | - | **1:1 vorhanden** | 2/4011 |
| is_service | Ist eine Dienstleistung | is_service | is_service | is_service | boolean -> boolean | - | **1:1 vorhanden** | 363/4011 |
| layout_category_id | Sektion | layout_category_id | - | - | many2one -> None | - | **bewusst nicht zu uebernehmen** | 2/4011 |
| move_ids | Lagerbuchungen | move_ids | move_ids | move_ids | one2many -> one2many | - | **1:1 vorhanden** | 296/4011 |
| name | Beschreibung | name | name | name | text -> text | - | **1:1 vorhanden** | 4011/4011 |
| number | Nummer | number | number | number | integer -> integer | - | **1:1 vorhanden** | 4011/4011 |
| order_id | Auftragsreferenz | order_id | order_id | order_id | many2one -> many2one | - | **1:1 vorhanden** | 4011/4011 |
| price_reduce | Reduzierter Preis | price_reduce | price_reduce_taxexcl / price_reduce_taxinc | - | float -> None | offen | **fehlende Zuordnung** | 3980/4011 |
| price_reduce_taxexcl | Reduzierter Preis zzgl. USt. | price_reduce_taxexcl | price_reduce_taxexcl | price_reduce_taxexcl | monetary -> monetary | - | **1:1 vorhanden** | 3932/4011 |
| price_reduce_taxinc | Reduzierter Preis inkl. USt. | price_reduce_taxinc | price_reduce_taxinc | price_reduce_taxinc | monetary -> monetary | - | **1:1 vorhanden** | 3932/4011 |
| price_subtotal | Zwischensumme | price_subtotal | price_subtotal | price_subtotal | monetary -> monetary | - | **1:1 vorhanden** | 3932/4011 |
| price_tax | Steuern | price_tax | price_tax | price_tax | float -> float | - | **1:1 vorhanden** | 3931/4011 |
| price_total | Total | price_total | price_total | price_total | monetary -> monetary | - | **1:1 vorhanden** | 3932/4011 |
| price_unit | Preis pro ME | price_unit | price_unit | price_unit | float -> float | - | **1:1 vorhanden** | 3981/4011 |
| product_id | Produkt | product_id | product_id | product_id | many2one -> many2one | - | **1:1 vorhanden** | 4011/4011 |
| product_uom | Mengeneinheit | product_uom | product_uom | product_uom | many2one -> many2one | Relation product.uom -> uom.uom | **Transformationsregel erforderlich** | 4011/4011 |
| product_uom_qty | Menge | product_uom_qty | product_uom_qty | product_uom_qty | float -> float | - | **1:1 vorhanden** | 3960/4011 |
| qty_delivered | Ausgeliefert | qty_delivered | qty_delivered | qty_delivered | float -> float | - | **1:1 vorhanden** | 1/4011 |
| qty_invoiced | Abgerechnet | qty_invoiced | qty_invoiced | qty_invoiced | float -> float | - | **1:1 vorhanden** | 1863/4011 |
| qty_to_invoice | Abzurechnen | qty_to_invoice | qty_to_invoice | qty_to_invoice | float -> float | - | **1:1 vorhanden** | 1875/4011 |
| sequence | Nummernfolge | sequence | sequence | sequence | integer -> integer | - | **1:1 vorhanden** | 1101/4011 |
| subscription_id | Aboauftrag | subscription_id | subscription_id | subscription_id | many2one -> many2one | - | **1:1 vorhanden** | 2310/4011 |
| tax_id | Steuern | tax_id | tax_id | tax_id | many2many -> many2many | - | **1:1 vorhanden** | 4008/4011 |
| write_date | Zuletzt aktualisiert am | write_date | write_date | write_date | datetime -> datetime | - | **1:1 vorhanden** | 4011/4011 |
| write_uid | Zuletzt aktualisiert durch | write_uid | write_uid | write_uid | many2one -> many2one | - | **1:1 vorhanden** | 4011/4011 |

## 4. Risiken und fehlende Zuordnungen

```
[sale.order] note (belegt 2442/2464): Transformationsregel erforderlich | text -> html
[sale.order] state (belegt 2464/2464): Transformationsregel erforderlich | Auswahlwerte ohne Entsprechung: ['done']; 'done' entfaellt -> state='sale' + locked=True
[sale.order] tag_ids (belegt 1/2464): Transformationsregel erforderlich | Relation crm.lead.tag -> crm.tag
[sale.order.line] invoice_lines (belegt 1863/4011): Transformationsregel erforderlich | Relation account.invoice.line -> account.move.line
[sale.order.line] price_reduce (belegt 3980/4011): fehlende Zuordnung | offen
[sale.order.line] product_uom (belegt 4011/4011): Transformationsregel erforderlich | Relation product.uom -> uom.uom
```

## 5. Abweichende Feldbezeichnungen (Anzeige)

```
- sale.order.access_token: Odoo 11: "Security Token" | Odoo 18: "Security-Token"
- sale.order.administrative_contact_id: Odoo 11: "Administrativer Kontakt" | Odoo 18: "Verwaltungskontakt"
- sale.order.amount_total: Odoo 11: "Total" | Odoo 18: "Gesamt"
- sale.order.create_date: Odoo 11: "Erzeugt am" | Odoo 18: "Erstellungsdatum"
- sale.order.date_order: Odoo 11: "Bestelldatum" | Odoo 18: "Auftragsdatum"
- sale.order.invoice_status: Odoo 11: "Status Rechnung" | Odoo 18: "Rechnungsstatus"
- sale.order.message_follower_ids: Odoo 11: "Abonnenten" | Odoo 18: "Follower"
- sale.order.note: Odoo 11: "Geschäftsbedingungen" | Odoo 18: "Allgemeine Geschäftsbedingungen"
- sale.order.order_line: Odoo 11: "Auftragszeilen" | Odoo 18: "Auftragspositionen"
- sale.order.picking_ids: Odoo 11: "Pickaufträge" | Odoo 18: "Transfers"
- sale.order.picking_policy: Odoo 11: "Auslieferungsbedingungen" | Odoo 18: "Versandbedingungen"
- sale.order.user_id: Odoo 11: "Verkäufer" | Odoo 18: "Vertriebsmitarbeiter"
- sale.order.validity_date: Odoo 11: "Ablaufdatum" | Odoo 18: "Gültigkeit"
- sale.order.warehouse_id: Odoo 11: "Lager" | Odoo 18: "Lagerhaus"
- sale.order.write_uid: Odoo 11: "Zuletzt aktualisiert durch" | Odoo 18: "Zuletzt aktualisiert von"
- sale.order.line.amt_to_invoice: Odoo 11: "Abzurechnender Betrag" | Odoo 18: "Nicht abgerechnetes Saldo"
- sale.order.line.invoice_status: Odoo 11: "Status Rechnung" | Odoo 18: "Rechnungsstatus"
- sale.order.line.is_service: Odoo 11: "Ist eine Dienstleistung" | Odoo 18: "Is a Service"
- sale.order.line.layout_category_id: In Odoo 11 belegte/tote Funktion ohne fachliche Notwendigkeit
- sale.order.line.price_reduce: Kein gleichnamiges Feld in Odoo 18 - Zuordnung klaeren
- sale.order.line.price_reduce_taxexcl: Odoo 11: "Reduzierter Preis zzgl. USt." | Odoo 18: "Preisminderung exkl. Steuern"
- sale.order.line.price_reduce_taxinc: Odoo 11: "Reduzierter Preis inkl. USt." | Odoo 18: "Preisminderung inkl. Steuern"
- sale.order.line.price_tax: Odoo 11: "Steuern" | Odoo 18: "Gesamtsteuer"
- sale.order.line.price_total: Odoo 11: "Total" | Odoo 18: "Gesamt"
- sale.order.line.price_unit: Odoo 11: "Preis pro ME" | Odoo 18: "Einzelpreis"
- sale.order.line.product_uom: Odoo 11: "Mengeneinheit" | Odoo 18: "Maßeinheit"
- sale.order.line.qty_delivered: Odoo 11: "Ausgeliefert" | Odoo 18: "Liefermenge"
- sale.order.line.qty_invoiced: Odoo 11: "Abgerechnet" | Odoo 18: "Abgerechnete Menge"
- sale.order.line.qty_to_invoice: Odoo 11: "Abzurechnen" | Odoo 18: "Abzurechnende Menge"
- sale.order.line.sequence: Odoo 11: "Nummernfolge" | Odoo 18: "Sequenz"
- sale.order.line.write_uid: Odoo 11: "Zuletzt aktualisiert durch" | Odoo 18: "Zuletzt aktualisiert von"
```
