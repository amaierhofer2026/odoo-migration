# Odoo 11 -> Odoo 18: Bereich Verkauf, Teil 2 (Feldinventar sale.order und sale.order.line)

Stand: 24.09.2026, Session 121. Odoo 11 Prod (`portal.it-kommunal.at`, DB `ITK_V1_a`) wurde
ausschliesslich lesend gelesen. Keine Datenmigration, keine Aenderung an Produktivdaten,
keine Aenderung an Odoo 18 in diesem Teil.

Werkzeuge: `scripts/analyse_verkauf_teil2_felder.py` (Feldinventar, Nutzung, Auswahlwerte;
schreibt `docs/_verkauf_teil2_felder.json`), `scripts/baue_verkauf_teil2_doku.py` (dieses Dokument).

## 1. Uebersicht

```
                                  sale.order                     sale.order.line
Odoo 11 Felder                    89                             53
Odoo 18 Felder (lokal = VM)       110                            80
gemeinsame Feldnamen              58                             39
nur Odoo 11                       31                             14
nur Odoo 18                       52                             41
Typ-/Relationsabweichungen        3                              2
Datensaetze Odoo 11               2.461                          4.007
Datensaetze Odoo 18 (Teststand)   18 lokal / 20 VM               28 lokal / 29 VM
```

Zaehlweise: die Feldlisten stammen aus `ir.model.fields` und wurden gegen `fields_get`
gegengeprueft (beide Quellen liefern dieselben Feldmengen, je Modell und Instanz).
Belegte Datensaetze = `search_count([(feld, '!=', False)])` in Odoo 11, nur bei gespeicherten,
nicht abgeleiteten Feldern.

Einstufung je Feld (Vorgabe): `1:1` | `Transformation` | `berechnet` | `kein Ziel vorhanden` |
`obsolet`. Felder, die es nur in Odoo 18 gibt, sind in Abschnitt 9 als Zusatzfunktion gefuehrt.

## 2. sale.order - Feldinventar Odoo 11 gegen Odoo 18


| Odoo-11-Feld | Beschriftung | Typ / Relation | Pflicht | readonly | gespeichert | belegte Datensaetze | Odoo-18-Ziel | Einstufung |
|---|---|---|---|---|---|---|---|---|
| `__last_update` | Zuletzt geändert am | datetime | nein | ja | nein (berechnet) | berechnet (nicht gespeichert) | technisches Feld, in Odoo 18 entfernt (ersetzt `write_date`). | obsolet |
| `access_token` | Security Token | char | nein | nein | ja | 2461 von 2461 | Odoo 18 `access_token` (char) | 1:1 |
| `activity_date_deadline` | Nächste Aktivitätsfrist | date | nein | ja | ja | abgeleitet (related) | Odoo 18 `activity_date_deadline` (date) | 1:1 |
| `activity_ids` | Aktivitäten | one2many -> mail.activity | nein | nein | ja | 0 von 2461 | Odoo 18 `activity_ids` (one2many -> mail.activity) | 1:1 |
| `activity_state` | Bundesland | selection | nein | ja | nein (berechnet) | berechnet (nicht gespeichert) | Odoo 18 `activity_state` (selection) | berechnet |
| `activity_summary` | Zusammenfassung nächste Aktion | char | nein | nein | nein (berechnet) | abgeleitet (related) | Odoo 18 `activity_summary` (char) | berechnet |
| `activity_type_id` | Nächster Aktivitätstyp | many2one -> mail.activity.type | nein | nein | nein (berechnet) | abgeleitet (related) | Odoo 18 `activity_type_id` (many2one -> mail.activity.type) | berechnet |
| `activity_user_id` | Verantwortlich | many2one -> res.users | nein | nein | nein (berechnet) | abgeleitet (related) | Odoo 18 `activity_user_id` (many2one -> res.users) | berechnet |
| `administrative_contact_id` | Administrativer Kontakt | many2one -> res.partner | nein | nein | ja | 2 von 2461 | Odoo 18 `administrative_contact_id` (many2one -> res.partner) | 1:1 |
| `amount_tax` | Steuern | monetary | nein | ja | ja | 2461 von 2461 | Odoo 18 `amount_tax` (monetary) | 1:1 |
| `amount_total` | Total | monetary | nein | ja | ja | 2461 von 2461 | Odoo 18 `amount_total` (monetary) | 1:1 |
| `amount_untaxed` | Nettobetrag | monetary | nein | ja | ja | 2461 von 2461 | Odoo 18 `amount_untaxed` (monetary) | 1:1 |
| `analytic_account_id` | Kostenstelle | many2one -> account.analytic.account | nein | ja | ja | 0 von 2461 | 0 Verwendungen in Odoo 11. Kostenstellen laufen in Odoo 18 zeilenweise ueber `sale.order.line.analytic_distribution`. | obsolet |
| `campaign_id` | Kampagne | many2one -> utm.campaign | nein | nein | ja | 0 von 2461 | Odoo 18 `campaign_id` (many2one -> utm.campaign) | 1:1 |
| `can_directly_mark_as_paid` | Kann direkt als bezahlt markiert werden | boolean | nein | ja | ja | 0 von 2461 | Website-Kaufvorgang (`website_sale`), 0 Verwendungen. | obsolet |
| `cart_quantity` | Anzahl der Artikel im Warenkorb | integer | nein | ja | nein (berechnet) | berechnet (nicht gespeichert) | berechnet, Website-Kaufvorgang, 0 Verwendungen. | obsolet |
| `cart_recovery_email_sent` | E-Mail zur Warenkorbwiederherstellung bereits gesendet. | boolean | nein | nein | ja | 0 von 2461 | Website-Kaufvorgang (`website_sale`), 0 Verwendungen. | obsolet |
| `client_order_ref` | Kundenreferenz | char | nein | nein | ja | 0 von 2461 | Odoo 18 `client_order_ref` (char) | 1:1 |
| `company_id` | Unternehmen | many2one -> res.company | nein | nein | ja | 2461 von 2461 | Odoo 18 `company_id` (many2one -> res.company) | 1:1 |
| `confirmation_date` | Bestätigung am | datetime | nein | ja | ja | 2437 von 2461 | Odoo 18 `confirmation_date` (datetime) In Odoo 18 eigenes Feld des Moduls `itk_sale_management` (18.0.1.1.0), Beschriftung "Bestätigung am". | 1:1 |
| `create_date` | Erzeugt am | datetime | nein | ja | ja | 2461 von 2461 | Odoo 18 `create_date` (datetime) | 1:1 |
| `create_uid` | Erstellt von | many2one -> res.users | nein | nein | ja | 2461 von 2461 | Odoo 18 `create_uid` (many2one -> res.users) | 1:1 |
| `currency_id` | Währung | many2one -> res.currency | ja | ja | nein (berechnet) | abgeleitet (related) | Odoo 18 `currency_id` (many2one -> res.currency) | berechnet |
| `date_order` | Bestelldatum | datetime | ja | ja | ja | 2461 von 2461 | Odoo 18 `date_order` (datetime) Odoo 18 setzt `date_order` beim Bestaetigen neu; das Odoo-11-Bestaetigungsdatum liegt in `confirmation_date`. | 1:1 |
| `delivery_count` | Warenauslieferung | integer | nein | ja | nein (berechnet) | berechnet (nicht gespeichert) | Zaehler aus `picking_ids` (`sale_stock`), entfaellt mit dem Modul. | berechnet |
| `display_name` | Anzeigename | char | nein | ja | nein (berechnet) | berechnet (nicht gespeichert) | Odoo 18 `display_name` (char) | berechnet |
| `final_customer_id` | Endkunde | many2one -> res.partner | nein | nein | ja | 0 von 2461 | Odoo 18 `final_customer_id` (many2one -> res.partner) | 1:1 |
| `fiscal_position_id` | Steuerzuordnung | many2one -> account.fiscal.position | nein | nein | ja | 0 von 2461 | Odoo 18 `fiscal_position_id` (many2one -> account.fiscal.position) | 1:1 |
| `id` | ID | integer | nein | ja | ja | 2461 von 2461 | Odoo 18 `id` (integer) | 1:1 |
| `incoterm` | Lieferbedingungen | many2one -> stock.incoterms | nein | nein | ja | 0 von 2461 | 0 Verwendungen in Odoo 11. Odoo 18 fuehrt Incoterms im Modul `sale_stock` (nicht installiert). | obsolet |
| `invoice_count` | # Rechnungen | integer | nein | ja | nein (berechnet) | berechnet (nicht gespeichert) | Odoo 18 `invoice_count` (integer) | berechnet |
| `invoice_ids` | Rechnungen | many2many -> account.invoice | nein | ja | nein (berechnet) | berechnet (nicht gespeichert) | Odoo 11 `account.invoice` -> Odoo 18 `account.move` (Rechnungsmodell umbenannt). | Transformation |
| `invoice_status` | Status Rechnung | selection | nein | ja | ja | 2461 von 2461 | Odoo 18 `invoice_status` (selection) | 1:1 |
| `is_abandoned_cart` | Verworfener Warenkorb | boolean | nein | ja | nein (berechnet) | berechnet (nicht gespeichert) | berechnet, Website-Kaufvorgang, 0 Verwendungen. | obsolet |
| `is_expired` | Ist abgelaufen | boolean | nein | ja | nein (berechnet) | berechnet (nicht gespeichert) | Odoo 18 `is_expired` (boolean) | berechnet |
| `medium_id` | Medium | many2one -> utm.medium | nein | nein | ja | 0 von 2461 | Odoo 18 `medium_id` (many2one -> utm.medium) | 1:1 |
| `message_channel_ids` | Abonnenten (Kanäle) | many2many -> mail.channel | nein | ja | nein (berechnet) | berechnet (nicht gespeichert) | technischer mail-Rest, in Odoo 18 entfernt. | obsolet |
| `message_follower_ids` | Abonnenten | one2many -> mail.followers | nein | nein | ja | 2461 von 2461 | Odoo 18 `message_follower_ids` (one2many -> mail.followers) | 1:1 |
| `message_ids` | Nachrichten | one2many -> mail.message | nein | nein | ja | 2461 von 2461 | Odoo 18 `message_ids` (one2many -> mail.message) | 1:1 |
| `message_is_follower` | Ist ein Abonnent | boolean | nein | ja | nein (berechnet) | berechnet (nicht gespeichert) | Odoo 18 `message_is_follower` (boolean) | berechnet |
| `message_last_post` | Datum der letzten Nachricht | datetime | nein | nein | ja | 0 von 2461 | technischer mail-Rest, 0 Verwendungen, in Odoo 18 entfernt. | obsolet |
| `message_needaction` | Aktion notwendig | boolean | nein | ja | nein (berechnet) | berechnet (nicht gespeichert) | Odoo 18 `message_needaction` (boolean) | berechnet |
| `message_needaction_counter` | Anzahl der Aktionen | integer | nein | ja | nein (berechnet) | berechnet (nicht gespeichert) | Odoo 18 `message_needaction_counter` (integer) | berechnet |
| `message_partner_ids` | Abonnenten (Partner) | many2many -> res.partner | nein | ja | nein (berechnet) | berechnet (nicht gespeichert) | Odoo 18 `message_partner_ids` (many2many -> res.partner) | berechnet |
| `message_unread` | Ungelesene Nachrichten | boolean | nein | ja | nein (berechnet) | berechnet (nicht gespeichert) | technischer mail-Rest, in Odoo 18 entfernt. | obsolet |
| `message_unread_counter` | Zähler der ungelesenen Nachrichten | integer | nein | ja | nein (berechnet) | berechnet (nicht gespeichert) | technischer mail-Rest, in Odoo 18 entfernt. | obsolet |
| `name` | Auftragsreferenz | char | ja | ja | ja | 2461 von 2461 | Odoo 18 `name` (char) | 1:1 |
| `note` | Geschäftsbedingungen | text | nein | nein | ja | 2439 von 2461 | Odoo 11 `text` -> Odoo 18 `html` (Odoo-18-Textfeld, Inhalt 1:1 uebernehmbar). | Transformation |
| `only_services` | Nur Dienstleistungen | boolean | nein | ja | nein (berechnet) | berechnet (nicht gespeichert) | berechnet, Website-Warenkorb, 0 Verwendungen. | obsolet |
| `opportunity_id` | Chance | many2one -> crm.lead | nein | nein | ja | 128 von 2461 | Odoo 18 `opportunity_id` (many2one -> crm.lead) | 1:1 |
| `order_line` | Auftragszeilen | one2many -> sale.order.line | nein | nein | ja | 2449 von 2461 | Odoo 18 `order_line` (one2many -> sale.order.line) | 1:1 |
| `origin` | Referenzbeleg | char | nein | nein | ja | 22 von 2461 | Odoo 18 `origin` (char) | 1:1 |
| `partner_id` | Kunde | many2one -> res.partner | ja | ja | ja | 2461 von 2461 | Odoo 18 `partner_id` (many2one -> res.partner) | 1:1 |
| `partner_invoice_id` | Rechnungsadresse | many2one -> res.partner | ja | ja | ja | 2461 von 2461 | Odoo 18 `partner_invoice_id` (many2one -> res.partner) | 1:1 |
| `partner_shipping_id` | Lieferadresse | many2one -> res.partner | ja | ja | ja | 2461 von 2461 | Odoo 18 `partner_shipping_id` (many2one -> res.partner) | 1:1 |
| `payment_acquirer_id` | Zahlungsanbieter | many2one -> payment.acquirer | nein | nein | ja | abgeleitet (related) | berechnetes Feld aus `sale_payment`, 0 Verwendungen; Ziel ist `transaction_ids`. | berechnet |
| `payment_term_id` | Zahlungsbedingungen | many2one -> account.payment.term | nein | nein | ja | 613 von 2461 | Odoo 18 `payment_term_id` (many2one -> account.payment.term) | 1:1 |
| `payment_transaction_count` | Anzahl der Zahlungstransaktionen | integer | nein | ja | nein (berechnet) | berechnet (nicht gespeichert) | Zaehler aus `payment_tx_ids`, 0 Verwendungen; Odoo 18 zaehlt ueber `transaction_ids`. | berechnet |
| `payment_tx_id` | Letzte Transaktion | many2one -> payment.transaction | nein | nein | ja | 0 von 2461 | 0 Verwendungen. Ziel in Odoo 18 ist `transaction_ids` (many2many payment.transaction). | obsolet |
| `payment_tx_ids` | Transaktionen | one2many -> payment.transaction | nein | nein | ja | 0 von 2461 | Ziel in Odoo 18: `transaction_ids` (many2many payment.transaction). | Transformation |
| `picking_ids` | Pickaufträge | one2many -> stock.picking | nein | nein | ja | 235 von 2461 | Feld aus `sale_stock`; 235 Auftraege hatten Lieferauftraege, davon 0 erledigt. | kein Ziel vorhanden |
| `picking_policy` | Auslieferungsbedingungen | selection | ja | ja | ja | 2461 von 2461 | Feld aus `sale_stock`; stock wird nicht installiert (Entscheidung Session 119). In Odoo 11 bei allen 2.461 Auftraegen der Standardwert `direct`. | kein Ziel vorhanden |
| `portal_url` | Portalzugriffs-URL | char | nein | ja | nein (berechnet) | berechnet (nicht gespeichert) | berechneter Portal-Link; Odoo 18 fuehrt `access_url` (berechnet). | berechnet |
| `pricelist_id` | Preisliste | many2one -> product.pricelist | ja | ja | ja | 2461 von 2461 | Odoo 18 `pricelist_id` (many2one -> product.pricelist) | 1:1 |
| `procurement_group_id` | Beschaffungsgruppe | many2one -> procurement.group | nein | nein | ja | 240 von 2461 | Feld aus `sale_stock` (Beschaffungsgruppe, 240 Auftraege). | kein Ziel vorhanden |
| `product_category_id` | Produktkategorie | many2one -> product.category | nein | nein | ja | 47 von 2461 | Odoo 18 `product_category_id` (many2one -> product.category) | 1:1 |
| `product_id` | Produkt | many2one -> product.product | nein | nein | nein (berechnet) | abgeleitet (related) | related auf die erste Auftragszeile, nicht gespeichert. Funktion in Odoo 18 ueber `order_line.product_id`. | berechnet |
| `project_ids` | Projekte | many2many -> project.project | nein | ja | nein (berechnet) | berechnet (nicht gespeichert) | Feld aus `sale_timesheet` (nicht installiert, 0 Stundenzettelzeilen). | kein Ziel vorhanden |
| `project_project_id` | Projekt für diesen Verkauf | many2one -> project.project | nein | ja | nein (berechnet) | berechnet (nicht gespeichert) | Feld aus `sale_timesheet` (nicht installiert). | kein Ziel vorhanden |
| `sale_contact_id` | Verkaufskontakt | many2one -> res.partner | nein | nein | ja | 3 von 2461 | Odoo 18 `sale_contact_id` (many2one -> res.partner) | 1:1 |
| `source_id` | Referenz | many2one -> utm.source | nein | nein | ja | 0 von 2461 | Odoo 18 `source_id` (many2one -> utm.source) | 1:1 |
| `state` | Status | selection | nein | ja | ja | 2461 von 2461 | Odoo 18 `state` (selection) Odoo 11 kennt zusaetzlich `done` (0 Datensaetze); Odoo 18 fuehrt `sale` + `locked`. | 1:1 |
| `subscription_count` | Abonnementanzahl | integer | nein | ja | nein (berechnet) | berechnet (nicht gespeichert) | Odoo 18 `subscription_count` (integer) ITK-Feld (`itk_subscription`), berechneter Zaehler fuer den Smart Button. | berechnet |
| `subscription_management` | Aboauftragsmanagement | selection | nein | nein | ja | 2461 von 2461 | Odoo 18 `subscription_management` (selection) ITK-Feld (`itk_subscription`): steuert, ob der Auftrag ein Abo erzeugt/erneuert. | 1:1 |
| `tag_ids` | Stichwörter | many2many -> crm.lead.tag | nein | nein | ja | 1 von 2461 | Odoo 11 `crm.lead.tag` -> Odoo 18 `crm.tag` (in Odoo 11 traegt genau 1 von 2.461 Auftraegen ein Stichwort: A-1900710). | Transformation |
| `tasks_count` | Aufgaben | integer | nein | ja | nein (berechnet) | berechnet (nicht gespeichert) | Zaehler aus `sale_timesheet`, Modul nicht installiert. | berechnet |
| `tasks_ids` | Aufgaben für diesen Auftrag | many2many -> project.task | nein | ja | nein (berechnet) | berechnet (nicht gespeichert) | Feld aus `sale_timesheet` (nicht installiert). | kein Ziel vorhanden |
| `team_id` | Vertriebskanal | many2one -> crm.team | nein | nein | ja | 2461 von 2461 | Odoo 18 `team_id` (many2one -> crm.team) Beschriftung in Odoo 18 "Vertriebskanal" (Angleichung an Odoo 11). | 1:1 |
| `technical_contact_id` | Technischer Kontakt | many2one -> res.partner | nein | nein | ja | 1 von 2461 | Odoo 18 `technical_contact_id` (many2one -> res.partner) | 1:1 |
| `timesheet_count` | Zeiterfassungsaktivitäten | float | nein | ja | nein (berechnet) | berechnet (nicht gespeichert) | Zaehler aus `sale_timesheet`, Modul nicht installiert. | berechnet |
| `timesheet_ids` | Zeiterfassungsaktivitäten verbunden mit diesen Verkauf | many2many -> account.analytic.line | nein | ja | nein (berechnet) | berechnet (nicht gespeichert) | Feld aus `sale_timesheet` (nicht installiert). | kein Ziel vorhanden |
| `user_id` | Verkäufer | many2one -> res.users | nein | nein | ja | 2461 von 2461 | Odoo 18 `user_id` (many2one -> res.users) | 1:1 |
| `validity_date` | Ablaufdatum | date | nein | ja | ja | 1 von 2461 | Odoo 18 `validity_date` (date) | 1:1 |
| `warehouse_id` | Lager | many2one -> stock.warehouse | ja | ja | ja | 2461 von 2461 | Feld aus `sale_stock`; in Odoo 11 bei allen Auftraegen das eine Standardlager. | kein Ziel vorhanden |
| `warning_stock` | Warnung | char | nein | nein | ja | 0 von 2461 | Website-Bestandshinweis (`website_sale_stock`), 0 Verwendungen. | obsolet |
| `website_message_ids` | Website-Nachrichten | one2many -> mail.message | nein | nein | ja | 0 von 2461 | Odoo 18 `website_message_ids` (one2many -> mail.message) | 1:1 |
| `website_order_line` | In der Website angezeigte Auftragszeilen | one2many -> sale.order.line | nein | ja | nein (berechnet) | berechnet (nicht gespeichert) | Website-Warenkorb (`website_sale`), 0 Verwendungen. | obsolet |
| `write_date` | Zuletzt aktualisiert am | datetime | nein | nein | ja | 2461 von 2461 | Odoo 18 `write_date` (datetime) | 1:1 |
| `write_uid` | Zuletzt aktualisiert durch | many2one -> res.users | nein | nein | ja | 2461 von 2461 | Odoo 18 `write_uid` (many2one -> res.users) | 1:1 |

## 3. sale.order.line - Feldinventar Odoo 11 gegen Odoo 18

| Odoo-11-Feld | Beschriftung | Typ / Relation | Pflicht | readonly | gespeichert | belegte Datensaetze | Odoo-18-Ziel | Einstufung |
|---|---|---|---|---|---|---|---|---|
| `__last_update` | Zuletzt geändert am | datetime | nein | ja | nein (berechnet) | berechnet (nicht gespeichert) | technisches Feld, in Odoo 18 entfernt. | obsolet |
| `amt_invoiced` | Abgerechneter Betrag | monetary | nein | ja | ja | 4007 von 4007 | Ziel in Odoo 18: `amount_invoiced` (monetary, berechnet). | Transformation |
| `amt_to_invoice` | Abzurechnender Betrag | monetary | nein | ja | ja | 4007 von 4007 | Ziel in Odoo 18: `amount_to_invoice` (monetary, berechnet). | Transformation |
| `analytic_tag_ids` | Kostenstellen Tags | many2many -> account.analytic.tag | nein | nein | ja | 0 von 4007 | 0 Verwendungen; Ziel ist `analytic_distribution`. | obsolet |
| `company_id` | Unternehmen | many2one -> res.company | nein | ja | ja | abgeleitet (related) | Odoo 18 `company_id` (many2one -> res.company) | 1:1 |
| `create_date` | Erstellt am | datetime | nein | nein | ja | 4007 von 4007 | Odoo 18 `create_date` (datetime) | 1:1 |
| `create_uid` | Erstellt von | many2one -> res.users | nein | nein | ja | 4007 von 4007 | Odoo 18 `create_uid` (many2one -> res.users) | 1:1 |
| `currency_id` | Währung | many2one -> res.currency | nein | ja | ja | abgeleitet (related) | Odoo 18 `currency_id` (many2one -> res.currency) | 1:1 |
| `customer_lead` | Tage bis Auslieferung | float | ja | nein | ja | 4007 von 4007 | Odoo 18 `customer_lead` (float) | 1:1 |
| `discount` | Rabatt (%) | float | nein | nein | ja | 4007 von 4007 | Odoo 18 `discount` (float) | 1:1 |
| `display_name` | Anzeigename | char | nein | ja | nein (berechnet) | berechnet (nicht gespeichert) | Odoo 18 `display_name` (char) | berechnet |
| `id` | ID | integer | nein | ja | ja | 4007 von 4007 | Odoo 18 `id` (integer) | 1:1 |
| `invoice_lines` | Rechnungszeilen | many2many -> account.invoice.line | nein | nein | ja | 1852 von 4007 | Odoo 11 `account.invoice.line` -> Odoo 18 `account.move.line`. | Transformation |
| `invoice_status` | Status Rechnung | selection | nein | ja | ja | 4007 von 4007 | Odoo 18 `invoice_status` (selection) | 1:1 |
| `is_downpayment` | Ist eine Anzahlung | boolean | nein | nein | ja | 2 von 4007 | Odoo 18 `is_downpayment` (boolean) | 1:1 |
| `is_service` | Ist eine Dienstleistung | boolean | nein | ja | ja | 363 von 4007 | Odoo 18 `is_service` (boolean) | 1:1 |
| `layout_category_id` | Sektion | many2one -> sale.layout_category | nein | nein | ja | 2 von 4007 | Modell `sale.layout.category` ist in Odoo 11 nicht registriert (toter Menuepunkt); Feld auf 2 von 4.007 Zeilen gesetzt. | obsolet |
| `layout_category_sequence` | Reihenfolge Auftragszeilen | integer | nein | nein | ja | 1366 von 4007 | Rest des Odoo-11-Reportlayouts; 1.366 Zeilen tragen nur den Standardwert 1, Odoo 18 kennt kein `sale.layout.category`. | obsolet |
| `move_ids` | Lagerbuchungen | one2many -> stock.move | nein | nein | ja | 296 von 4007 | Feld aus `sale_stock` (Lagerbewegungen, 296 Zeilen). | kein Ziel vorhanden |
| `name` | Beschreibung | text | ja | nein | ja | 4007 von 4007 | Odoo 18 `name` (text) | 1:1 |
| `number` | Nummer | integer | nein | ja | ja | 4007 von 4007 | Odoo 18 `number` (integer) | 1:1 |
| `order_id` | Auftragsreferenz | many2one -> sale.order | ja | nein | ja | 4007 von 4007 | Odoo 18 `order_id` (many2one -> sale.order) | 1:1 |
| `order_partner_id` | Kunde | many2one -> res.partner | nein | ja | ja | abgeleitet (related) | Odoo 18 `order_partner_id` (many2one -> res.partner) | 1:1 |
| `partner_id` | Partner | many2one -> res.partner | nein | nein | ja | 0 von 4007 | Odoo 18 `partner_id` (many2one -> res.partner) ITK-Feld (`itk_saleorder_lines`), in Odoo 11 mit 0 Verwendungen. | 1:1 |
| `price_reduce` | Reduzierter Preis | float | nein | ja | ja | 4007 von 4007 | Odoo 18 fuehrt keinen reduzierten Stueckpreis mehr; Anzeige und Berechnung nutzen `price_unit` mit Rabatt und `price_subtotal`. | obsolet |
| `price_reduce_taxexcl` | Reduzierter Preis zzgl. USt. | monetary | nein | ja | ja | 4007 von 4007 | Odoo 18 `price_reduce_taxexcl` (monetary) | 1:1 |
| `price_reduce_taxinc` | Reduzierter Preis inkl. USt. | monetary | nein | ja | ja | 4007 von 4007 | Odoo 18 `price_reduce_taxinc` (monetary) | 1:1 |
| `price_subtotal` | Zwischensumme | monetary | nein | ja | ja | 4007 von 4007 | Odoo 18 `price_subtotal` (monetary) | 1:1 |
| `price_tax` | Steuern | float | nein | ja | ja | 4007 von 4007 | Odoo 18 `price_tax` (float) | 1:1 |
| `price_total` | Total | monetary | nein | ja | ja | 4007 von 4007 | Odoo 18 `price_total` (monetary) | 1:1 |
| `price_unit` | Preis pro ME | float | ja | nein | ja | 4007 von 4007 | Odoo 18 `price_unit` (float) | 1:1 |
| `product_id` | Produkt | many2one -> product.product | ja | nein | ja | 4007 von 4007 | Odoo 18 `product_id` (many2one -> product.product) | 1:1 |
| `product_image` | Produktbild | binary | nein | nein | nein (berechnet) | abgeleitet (related) | berechnetes Bild der Produktvariante. | berechnet |
| `product_packaging` | Verpackung | many2one -> product.packaging | nein | nein | ja | 0 von 4007 | Feld aus `sale_stock`, 0 Verwendungen; Odoo 18 hat `product_packaging_id` (ebenfalls sale_stock). | kein Ziel vorhanden |
| `product_uom` | Mengeneinheit | many2one -> product.uom | ja | nein | ja | 4007 von 4007 | Odoo 11 `product.uom` -> Odoo 18 `uom.uom` (Modell umbenannt). | Transformation |
| `product_uom_qty` | Menge | float | ja | nein | ja | 4007 von 4007 | Odoo 18 `product_uom_qty` (float) | 1:1 |
| `product_updatable` | Kann Produkt bearbeiten | boolean | nein | ja | nein (berechnet) | berechnet (nicht gespeichert) | Odoo 18 `product_updatable` (boolean) | berechnet |
| `qty_delivered` | Ausgeliefert | float | nein | nein | ja | 4007 von 4007 | Odoo 18 `qty_delivered` (float) | 1:1 |
| `qty_delivered_updateable` | Kann gelieferte Auftragszeilen anpassen | boolean | nein | ja | nein (berechnet) | berechnet (nicht gespeichert) | berechnetes Steuerfeld; Odoo 18 regelt das ueber `qty_delivered_method`. | berechnet |
| `qty_invoiced` | Abgerechnet | float | nein | ja | ja | 4007 von 4007 | Odoo 18 `qty_invoiced` (float) | 1:1 |
| `qty_multiplication_factor` | Multiplication Factor/Thsd | integer | nein | nein | ja | 1366 von 4007 | Odoo 18 `qty_multiplication_factor` (integer) ITK-Feld (`itk_multifactor`): Multiplikationsfaktor je Zeile (1.366 Zeilen != 1). | 1:1 |
| `qty_to_invoice` | Abzurechnen | float | nein | ja | ja | 4007 von 4007 | Odoo 18 `qty_to_invoice` (float) | 1:1 |
| `route_id` | Route | many2one -> stock.location.route | nein | nein | ja | 0 von 4007 | Feld aus `sale_stock`, 0 Verwendungen. | kein Ziel vorhanden |
| `salesman_id` | Verkäufer | many2one -> res.users | nein | ja | ja | abgeleitet (related) | Odoo 18 `salesman_id` (many2one -> res.users) | 1:1 |
| `salesperson_id` | Verkäufer | many2one -> res.users | nein | nein | ja | 0 von 4007 | Odoo 18 `salesperson_id` (many2one -> res.users) ITK-Feld (`itk_saleorder_lines`): Verkaeufer je Zeile, in Odoo 11 mit 0 Verwendungen. | 1:1 |
| `sequence` | Nummernfolge | integer | nein | nein | ja | 4007 von 4007 | Odoo 18 `sequence` (integer) | 1:1 |
| `state` | Auftragsstatus | selection | nein | ja | ja | abgeleitet (related) | Odoo 18 `state` (selection) | 1:1 |
| `subscription_id` | Aboauftrag | many2one -> sale.subscription | nein | nein | ja | 2307 von 4007 | Odoo 18 `subscription_id` (many2one -> sale.subscription) ITK-Feld (`itk_subscription`): Verknuepfung der Zeile zum Abo (2.307 Zeilen). | 1:1 |
| `task_id` | Aufgabe | many2one -> project.task | nein | nein | ja | 0 von 4007 | Feld aus `sale_timesheet`, 0 Verwendungen. | kein Ziel vorhanden |
| `tax_id` | Steuern | many2many -> account.tax | nein | nein | ja | 4004 von 4007 | Odoo 18 `tax_id` (many2many -> account.tax) | 1:1 |
| `warning_stock` | Warnung | char | nein | nein | ja | 0 von 4007 | Website-Bestandshinweis (`website_sale_stock`), 0 Verwendungen. | obsolet |
| `write_date` | Zuletzt aktualisiert am | datetime | nein | nein | ja | 4007 von 4007 | Odoo 18 `write_date` (datetime) | 1:1 |
| `write_uid` | Zuletzt aktualisiert durch | many2one -> res.users | nein | nein | ja | 4007 von 4007 | Odoo 18 `write_uid` (many2one -> res.users) | 1:1 |

## 4. Selection-Werte

**sale.order**

| Feld | Odoo 11 | Odoo 18 | Bewertung |
|---|---|---|---|
| `activity_exception_decoration` | - | warning, danger | nur Odoo 18 |
| `activity_state` | overdue, today, planned | overdue, today, planned | identisch |
| `company_price_include` | - | tax_included, tax_excluded | nur Odoo 18 |
| `invoice_status` | upselling, invoiced, to invoice, no | upselling, invoiced, to invoice, no | identisch |
| `picking_policy` | direct, one | - | Feld entfaellt (siehe Abschnitt 7/8) |
| `state` | draft, sent, sale, done, cancel | draft, sent, sale, cancel | Odoo 18 ohne done (nicht verwendet) |
| `subscription_management` | create, renew, upsell | create, renew, upsell | identisch |
| `tax_calculation_rounding_method` | - | round_per_line, round_globally | nur Odoo 18 |
| `terms_type` | - | plain, html | nur Odoo 18 |

**sale.order.line**

| Feld | Odoo 11 | Odoo 18 | Bewertung |
|---|---|---|---|
| `company_price_include` | - | tax_included, tax_excluded | nur Odoo 18 |
| `display_type` | - | line_section, line_note | nur Odoo 18 |
| `invoice_status` | upselling, invoiced, to invoice, no | upselling, invoiced, to invoice, no | identisch |
| `product_type` | - | consu, service, combo, general, onlineservice, sw, consulting, platform, hw, project | nur Odoo 18 |
| `qty_delivered_method` | - | manual, analytic | nur Odoo 18 |
| `service_tracking` | - | no | nur Odoo 18 |
| `state` | draft, sent, sale, done, cancel | draft, sent, sale, cancel | Odoo 18 ohne done (nicht verwendet) |
| `tax_calculation_rounding_method` | - | round_per_line, round_globally | nur Odoo 18 |

## 5. Pflichtfelder und readonly-Felder

**sale.order**

```
Pflichtfelder Odoo 11 : currency_id, date_order, name, partner_id, partner_invoice_id, partner_shipping_id, picking_policy, pricelist_id, warehouse_id
Pflichtfelder Odoo 18 : company_id, date_order, name, partner_id, partner_invoice_id, partner_shipping_id
in Odoo 18 zusaetzlich pflichtig : company_id
nicht mehr pflichtig in Odoo 18    : currency_id, picking_policy, pricelist_id, warehouse_id
readonly Odoo 11       : __last_update, activity_date_deadline, activity_state, amount_tax, amount_total, amount_untaxed, analytic_account_id, can_directly_mark_as_paid, cart_quantity, confirmation_date, create_date, currency_id, date_order, delivery_count, display_name, id, invoice_count, invoice_ids, invoice_status, is_abandoned_cart, is_expired, message_channel_ids, message_is_follower, message_needaction, message_needaction_counter, message_partner_ids, message_unread, message_unread_counter, name, only_services, partner_id, partner_invoice_id, partner_shipping_id, payment_transaction_count, picking_policy, portal_url, pricelist_id, project_ids, project_project_id, state, subscription_count, tasks_count, tasks_ids, timesheet_count, timesheet_ids, validity_date, warehouse_id, website_order_line
readonly Odoo 18       : access_url, access_warning, activity_calendar_event_id, activity_date_deadline, activity_exception_decoration, activity_exception_icon, activity_state, activity_type_icon, activity_user_id, amount_invoiced, amount_paid, amount_tax, amount_to_invoice, amount_total, amount_undiscounted, amount_untaxed, authorized_transaction_ids, available_product_document_ids, company_price_include, confirmation_date, country_code, create_date, create_uid, currency_id, currency_rate, display_name, duplicated_order_ids, expected_date, has_active_pricelist, has_archived_products, has_message, id, invoice_count, invoice_ids, invoice_status, is_expired, is_pdf_quote_builder_available, message_attachment_count, message_has_error, message_has_error_counter, message_has_sms_error, message_is_follower, message_needaction, message_needaction_counter, my_activity_date_deadline, partner_credit_warning, pending_email_template_id, purchase_order_count, state, subscription_count, tax_calculation_rounding_method, tax_country_id, tax_totals, terms_type, transaction_ids, type_name, write_date, write_uid
```

Hinweis: die zusaetzlichen Pflichtfelder in Odoo 11 (`picking_policy`, `warehouse_id`,
`currency_id`) stammen aus `sale_stock` beziehungsweise aus berechneten Feldern; in Odoo 18
ist `company_id` neu pflichtig. Kein Feld verliert dadurch Daten.

**sale.order.line**

```
Pflichtfelder Odoo 11 : customer_lead, name, order_id, price_unit, product_id, product_uom, product_uom_qty
Pflichtfelder Odoo 18 : customer_lead, name, order_id, price_unit, product_uom_qty
in Odoo 18 zusaetzlich pflichtig : keiner
nicht mehr pflichtig in Odoo 18    : product_id, product_uom
readonly Odoo 11       : __last_update, amt_invoiced, amt_to_invoice, company_id, currency_id, display_name, id, invoice_status, is_service, number, order_partner_id, price_reduce, price_reduce_taxexcl, price_reduce_taxinc, price_subtotal, price_tax, price_total, product_updatable, qty_delivered_updateable, qty_invoiced, qty_to_invoice, salesman_id, state
readonly Odoo 18       : amount_invoiced, amount_to_invoice, available_product_document_ids, company_id, company_price_include, create_date, create_uid, currency_id, display_name, distribution_analytic_account_ids, id, invoice_status, is_configurable_product, is_product_archived, is_service, number, order_partner_id, price_reduce_taxexcl, price_reduce_taxinc, price_subtotal, price_tax, price_total, pricelist_item_id, product_template_attribute_value_ids, product_type, product_uom_category_id, product_uom_readonly, product_updatable, purchase_line_count, purchase_line_ids, qty_delivered_method, qty_invoiced, qty_invoiced_posted, qty_to_invoice, salesman_id, service_tracking, state, tax_calculation_rounding_method, tax_country_id, translated_product_name, untaxed_amount_invoiced, untaxed_amount_to_invoice, write_date, write_uid
```

Hinweis: die zusaetzlichen Pflichtfelder in Odoo 11 (`picking_policy`, `warehouse_id`,
`currency_id`) stammen aus `sale_stock` beziehungsweise aus berechneten Feldern; in Odoo 18
ist `company_id` neu pflichtig. Kein Feld verliert dadurch Daten.

## 6. ITK-eigene Felder und Sonderlogik

```
sale.order
  sale_contact_id            res.partner       itk_sale_management   Odoo 11 belegt: 3 von 2.461
  administrative_contact_id  res.partner       itk_sale_management   Odoo 11 belegt: 2
  technical_contact_id       res.partner       itk_sale_management   Odoo 11 belegt: 1
  final_customer_id          res.partner       itk_sale_management   Odoo 11 belegt: 0
  product_category_id        product.category  itk_sale_management   Odoo 11 belegt: 47
  confirmation_date          datetime          itk_sale_management   Odoo 11 belegt: 2.437 (in Odoo 18 eigenes Feld)
  subscription_management    selection         itk_subscription      Odoo 11 belegt: 2.461
  subscription_count         integer           itk_subscription      berechnet (Smart Button)

sale.order.line
  qty_multiplication_factor  integer           itk_multifactor       Odoo 11 belegt: 1.366 von 4.007
  subscription_id            many2one          itk_subscription      Odoo 11 belegt: 2.307
  partner_id                 many2one          itk_saleorder_lines   Odoo 11 belegt: 0
  salesperson_id             many2one          itk_saleorder_lines   Odoo 11 belegt: 0
```

Alle ITK-Felder sind in Odoo 18 mit gleichem Namen, gleichem Typ und gleicher Relation vorhanden
(Ausnahme: `confirmation_date` stammt in Odoo 18 aus `itk_sale_management` statt aus `sale`).
Sonderlogik: `subscription_management` steuert die Abo-Erzeugung, `qty_multiplication_factor`
geht in die Abrechnung ein (Faktor 1.000er-Regel), `subscription_id` verbindet Zeile und Abo.

## 7. Felder ohne Ziel in Odoo 18 (Modul in Odoo 18 nicht installiert bzw. Funktion entfaellt)


- `sale.order.picking_ids` (one2many -> stock.picking, 235 von 2461): Feld aus `sale_stock`; 235 Auftraege hatten Lieferauftraege, davon 0 erledigt.
- `sale.order.picking_policy` (selection, 2461 von 2461): Feld aus `sale_stock`; stock wird nicht installiert (Entscheidung Session 119). In Odoo 11 bei allen 2.461 Auftraegen der Standardwert `direct`.
- `sale.order.procurement_group_id` (many2one -> procurement.group, 240 von 2461): Feld aus `sale_stock` (Beschaffungsgruppe, 240 Auftraege).
- `sale.order.project_ids` (many2many -> project.project, berechnet (nicht gespeichert)): Feld aus `sale_timesheet` (nicht installiert, 0 Stundenzettelzeilen).
- `sale.order.project_project_id` (many2one -> project.project, berechnet (nicht gespeichert)): Feld aus `sale_timesheet` (nicht installiert).
- `sale.order.tasks_ids` (many2many -> project.task, berechnet (nicht gespeichert)): Feld aus `sale_timesheet` (nicht installiert).
- `sale.order.timesheet_ids` (many2many -> account.analytic.line, berechnet (nicht gespeichert)): Feld aus `sale_timesheet` (nicht installiert).
- `sale.order.warehouse_id` (many2one -> stock.warehouse, 2461 von 2461): Feld aus `sale_stock`; in Odoo 11 bei allen Auftraegen das eine Standardlager.
- `sale.order.line.move_ids` (one2many -> stock.move, 296 von 4007): Feld aus `sale_stock` (Lagerbewegungen, 296 Zeilen).
- `sale.order.line.product_packaging` (many2one -> product.packaging, 0 von 4007): Feld aus `sale_stock`, 0 Verwendungen; Odoo 18 hat `product_packaging_id` (ebenfalls sale_stock).
- `sale.order.line.route_id` (many2one -> stock.location.route, 0 von 4007): Feld aus `sale_stock`, 0 Verwendungen.
- `sale.order.line.task_id` (many2one -> project.task, 0 von 4007): Feld aus `sale_timesheet`, 0 Verwendungen.
- `sale.order.payment_tx_ids` (one2many -> payment.transaction, 0 von 2461): Ziel in Odoo 18: `transaction_ids` (many2many payment.transaction).
- `sale.order.line.amt_invoiced` (monetary, 4007 von 4007): Ziel in Odoo 18: `amount_invoiced` (monetary, berechnet).
- `sale.order.line.amt_to_invoice` (monetary, 4007 von 4007): Ziel in Odoo 18: `amount_to_invoice` (monetary, berechnet).

## 8. Fachlich nicht mehr benoetigte Felder (obsolet)

- `sale.order.__last_update` (datetime, berechnet (nicht gespeichert)): technisches Feld, in Odoo 18 entfernt (ersetzt `write_date`).
- `sale.order.analytic_account_id` (many2one -> account.analytic.account, 0 von 2461): 0 Verwendungen in Odoo 11. Kostenstellen laufen in Odoo 18 zeilenweise ueber `sale.order.line.analytic_distribution`.
- `sale.order.can_directly_mark_as_paid` (boolean, 0 von 2461): Website-Kaufvorgang (`website_sale`), 0 Verwendungen.
- `sale.order.cart_quantity` (integer, berechnet (nicht gespeichert)): berechnet, Website-Kaufvorgang, 0 Verwendungen.
- `sale.order.cart_recovery_email_sent` (boolean, 0 von 2461): Website-Kaufvorgang (`website_sale`), 0 Verwendungen.
- `sale.order.incoterm` (many2one -> stock.incoterms, 0 von 2461): 0 Verwendungen in Odoo 11. Odoo 18 fuehrt Incoterms im Modul `sale_stock` (nicht installiert).
- `sale.order.is_abandoned_cart` (boolean, berechnet (nicht gespeichert)): berechnet, Website-Kaufvorgang, 0 Verwendungen.
- `sale.order.message_channel_ids` (many2many -> mail.channel, berechnet (nicht gespeichert)): technischer mail-Rest, in Odoo 18 entfernt.
- `sale.order.message_last_post` (datetime, 0 von 2461): technischer mail-Rest, 0 Verwendungen, in Odoo 18 entfernt.
- `sale.order.message_unread` (boolean, berechnet (nicht gespeichert)): technischer mail-Rest, in Odoo 18 entfernt.
- `sale.order.message_unread_counter` (integer, berechnet (nicht gespeichert)): technischer mail-Rest, in Odoo 18 entfernt.
- `sale.order.only_services` (boolean, berechnet (nicht gespeichert)): berechnet, Website-Warenkorb, 0 Verwendungen.
- `sale.order.payment_tx_id` (many2one -> payment.transaction, 0 von 2461): 0 Verwendungen. Ziel in Odoo 18 ist `transaction_ids` (many2many payment.transaction).
- `sale.order.warning_stock` (char, 0 von 2461): Website-Bestandshinweis (`website_sale_stock`), 0 Verwendungen.
- `sale.order.website_order_line` (one2many -> sale.order.line, berechnet (nicht gespeichert)): Website-Warenkorb (`website_sale`), 0 Verwendungen.
- `sale.order.line.__last_update` (datetime, berechnet (nicht gespeichert)): technisches Feld, in Odoo 18 entfernt.
- `sale.order.line.analytic_tag_ids` (many2many -> account.analytic.tag, 0 von 4007): 0 Verwendungen; Ziel ist `analytic_distribution`.
- `sale.order.line.layout_category_id` (many2one -> sale.layout_category, 2 von 4007): Modell `sale.layout.category` ist in Odoo 11 nicht registriert (toter Menuepunkt); Feld auf 2 von 4.007 Zeilen gesetzt.
- `sale.order.line.layout_category_sequence` (integer, 1366 von 4007): Rest des Odoo-11-Reportlayouts; 1.366 Zeilen tragen nur den Standardwert 1, Odoo 18 kennt kein `sale.layout.category`.
- `sale.order.line.price_reduce` (float, 4007 von 4007): Odoo 18 fuehrt keinen reduzierten Stueckpreis mehr; Anzeige und Berechnung nutzen `price_unit` mit Rabatt und `price_subtotal`.
- `sale.order.line.warning_stock` (char, 0 von 4007): Website-Bestandshinweis (`website_sale_stock`), 0 Verwendungen.

## 9. Felder, die es nur in Odoo 18 gibt (Zusatzfunktionen, bleiben)


**sale.order** (52 Felder)

| Feld | Typ / Relation | Bedeutung |
|---|---|---|
| `access_url` | char | Odoo-18-Entsprechung zu `portal_url` |
| `access_warning` | text | Odoo-18-Zusatzfunktion |
| `activity_calendar_event_id` | many2one -> calendar.event | Odoo-18-Zusatzfunktion |
| `activity_exception_decoration` | selection | Odoo-18-Zusatzfunktion |
| `activity_exception_icon` | char | Odoo-18-Zusatzfunktion |
| `activity_type_icon` | char | Odoo-18-Zusatzfunktion |
| `amount_invoiced` | monetary | Ziel von `amt_invoiced` |
| `amount_paid` | float | Odoo-18-Zusatzfunktion |
| `amount_to_invoice` | monetary | Ziel von `amt_to_invoice` |
| `amount_undiscounted` | float | Odoo-18-Zusatzfunktion |
| `authorized_transaction_ids` | many2many -> payment.transaction | Odoo-18-Zusatzfunktion |
| `available_product_document_ids` | many2many -> quotation.document | Odoo-18-Zusatzfunktion |
| `commitment_date` | datetime | Odoo-18-Zusatzfunktion |
| `company_price_include` | selection | Odoo-18-Zusatzfunktion |
| `country_code` | char | Odoo-18-Zusatzfunktion |
| `currency_rate` | float | Odoo-18-Zusatzfunktion |
| `customizable_pdf_form_fields` | json | Odoo-18-Zusatzfunktion |
| `duplicated_order_ids` | many2many -> sale.order | Odoo-18-Zusatzfunktion |
| `expected_date` | datetime | Odoo-18-Zusatzfunktion |
| `has_active_pricelist` | boolean | Odoo-18-Zusatzfunktion |
| `has_archived_products` | boolean | Odoo-18-Zusatzfunktion |
| `has_message` | boolean | Odoo-18-Zusatzfunktion |
| `is_pdf_quote_builder_available` | boolean | Odoo-18-Zusatzfunktion |
| `journal_id` | many2one -> account.journal | Odoo-18-Zusatzfunktion |
| `locked` | boolean | Odoo-18-Ersatz fuer den Odoo-11-Status `done` |
| `message_attachment_count` | integer | Odoo-18-Zusatzfunktion |
| `message_has_error` | boolean | Odoo-18-Zusatzfunktion |
| `message_has_error_counter` | integer | Odoo-18-Zusatzfunktion |
| `message_has_sms_error` | boolean | Odoo-18-Zusatzfunktion |
| `my_activity_date_deadline` | date | Odoo-18-Zusatzfunktion |
| `partner_credit_warning` | text | Odoo-18-Zusatzfunktion |
| `pending_email_template_id` | many2one -> mail.template | Odoo-18-Zusatzfunktion |
| `prepayment_percent` | float | Odoo-18-Zusatzfunktion |
| `purchase_order_count` | integer | Odoo-18-Zusatzfunktion |
| `quotation_document_ids` | many2many -> quotation.document | Odoo-18-Zusatzfunktion |
| `rating_ids` | one2many -> rating.rating | Odoo-18-Zusatzfunktion |
| `reference` | char | Odoo-18-Zusatzfunktion |
| `require_payment` | boolean | Odoo-18-Zusatzfunktion |
| `require_signature` | boolean | Odoo-18-Zusatzfunktion |
| `sale_order_option_ids` | one2many -> sale.order.option | Odoo-18-Zusatzfunktion |
| `sale_order_template_id` | many2one -> sale.order.template | Odoo-18-Zusatzfunktion |
| `show_update_fpos` | boolean | Odoo-18-Zusatzfunktion |
| `show_update_pricelist` | boolean | Odoo-18-Zusatzfunktion |
| `signature` | binary | Odoo-18-Zusatzfunktion |
| `signed_by` | char | Odoo-18-Zusatzfunktion |
| `signed_on` | datetime | Odoo-18-Zusatzfunktion |
| `tax_calculation_rounding_method` | selection | Odoo-18-Zusatzfunktion |
| `tax_country_id` | many2one -> res.country | Odoo-18-Zusatzfunktion |
| `tax_totals` | binary | Odoo-18-Zusatzfunktion |
| `terms_type` | selection | Odoo-18-Zusatzfunktion |
| `transaction_ids` | many2many -> payment.transaction | Ziel von `payment_tx_ids` |
| `type_name` | char | Odoo-18-Zusatzfunktion |

**sale.order.line** (41 Felder)

| Feld | Typ / Relation | Bedeutung |
|---|---|---|
| `amount_invoiced` | monetary | Ziel von `amt_invoiced` |
| `amount_to_invoice` | monetary | Ziel von `amt_to_invoice` |
| `analytic_distribution` | json | Ziel von `analytic_account_id` |
| `analytic_line_ids` | one2many -> account.analytic.line | Odoo-18-Zusatzfunktion |
| `analytic_precision` | integer | Odoo-18-Zusatzfunktion |
| `available_product_document_ids` | many2many -> product.document | Odoo-18-Zusatzfunktion |
| `combo_item_id` | many2one -> product.combo.item | Odoo-18-Zusatzfunktion |
| `company_price_include` | selection | Odoo-18-Zusatzfunktion |
| `display_type` | selection | Odoo-18-Zusatzfunktion |
| `distribution_analytic_account_ids` | many2many -> account.analytic.account | Odoo-18-Zusatzfunktion |
| `is_configurable_product` | boolean | Odoo-18-Zusatzfunktion |
| `is_expense` | boolean | Odoo-18-Zusatzfunktion |
| `is_product_archived` | boolean | Odoo-18-Zusatzfunktion |
| `linked_line_id` | many2one -> sale.order.line | Odoo-18-Zusatzfunktion |
| `linked_line_ids` | one2many -> sale.order.line | Odoo-18-Zusatzfunktion |
| `linked_virtual_id` | char | Odoo-18-Zusatzfunktion |
| `pricelist_item_id` | many2one -> product.pricelist.item | Odoo-18-Zusatzfunktion |
| `product_custom_attribute_value_ids` | one2many -> product.attribute.custom.value | Odoo-18-Zusatzfunktion |
| `product_document_ids` | many2many -> product.document | Odoo-18-Zusatzfunktion |
| `product_no_variant_attribute_value_ids` | many2many -> product.template.attribute.value | Odoo-18-Zusatzfunktion |
| `product_packaging_id` | many2one -> product.packaging | Odoo-18-Entsprechung zu `product_packaging` (beide sale_stock) |
| `product_packaging_qty` | float | Odoo-18-Zusatzfunktion |
| `product_template_attribute_value_ids` | many2many -> product.template.attribute.value | Odoo-18-Zusatzfunktion |
| `product_template_id` | many2one -> product.template | Odoo-18-Zusatzfunktion |
| `product_type` | selection | Odoo-18-Zusatzfunktion |
| `product_uom_category_id` | many2one -> uom.category | Odoo-18-Zusatzfunktion |
| `product_uom_readonly` | boolean | Odoo-18-Zusatzfunktion |
| `purchase_line_count` | integer | Odoo-18-Zusatzfunktion |
| `purchase_line_ids` | one2many -> purchase.order.line | Odoo-18-Zusatzfunktion |
| `qty_delivered_method` | selection | Odoo-18-Zusatzfunktion |
| `qty_invoiced_posted` | float | Odoo-18-Zusatzfunktion |
| `sale_order_option_ids` | one2many -> sale.order.option | Odoo-18-Zusatzfunktion |
| `selected_combo_items` | char | Odoo-18-Zusatzfunktion |
| `service_tracking` | selection | Odoo-18-Zusatzfunktion |
| `tax_calculation_rounding_method` | selection | Odoo-18-Zusatzfunktion |
| `tax_country_id` | many2one -> res.country | Odoo-18-Zusatzfunktion |
| `technical_price_unit` | float | Odoo-18-Zusatzfunktion |
| `translated_product_name` | text | Odoo-18-Zusatzfunktion |
| `untaxed_amount_invoiced` | monetary | Odoo-18-Zusatzfunktion |
| `untaxed_amount_to_invoice` | monetary | Odoo-18-Zusatzfunktion |
| `virtual_id` | char | Odoo-18-Zusatzfunktion |

## 10. Beschriftungsunterschiede in der Anzeigesprache (de_DE)

Vergleich der Feldbeschriftungen gemeinsamer Felder, gelesen mit `lang=de_DE`.

| Modell | Feld | Odoo 11 (de_DE) | Odoo 18 (de_DE) | Bewertung |
|---|---|---|---|---|
| sale.order | `access_token` | Security Token | Security-Token | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order | `activity_state` | Bundesland | Status der Aktivität | Befund: die Odoo-11-de_DE-Uebersetzung ist falsch ("Bundesland"), englisch "State"; Odoo 18 ist korrekt |
| sale.order | `activity_summary` | Zusammenfassung nächste Aktion | Zusammenfassung der nächsten Aktivität | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order | `activity_user_id` | Verantwortlich | Verantwortlicher Benutzer | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order | `administrative_contact_id` | Administrativer Kontakt | Verwaltungskontakt | bewusst angeglichen (Session 117): Verwaltungskontakt |
| sale.order | `amount_total` | Total | Gesamt | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order | `create_date` | Erzeugt am | Erstellungsdatum | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order | `date_order` | Bestelldatum | Auftragsdatum | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order | `fiscal_position_id` | Steuerzuordnung | Steuerposition | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order | `invoice_count` | # Rechnungen | Rechnungsanzahl | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order | `invoice_status` | Status Rechnung | Rechnungsstatus | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order | `message_follower_ids` | Abonnenten | Follower | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order | `message_is_follower` | Ist ein Abonnent | Ist Follower | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order | `message_partner_ids` | Abonnenten (Partner) | Follower (Partner) | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order | `note` | Geschäftsbedingungen | Allgemeine Geschäftsbedingungen | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order | `order_line` | Auftragszeilen | Auftragspositionen | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order | `user_id` | Verkäufer | Vertriebsmitarbeiter | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order | `validity_date` | Ablaufdatum | Gültigkeit | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order | `write_uid` | Zuletzt aktualisiert durch | Zuletzt aktualisiert von | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order.line | `customer_lead` | Tage bis Auslieferung | Vorlaufzeit | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order.line | `invoice_status` | Status Rechnung | Rechnungsstatus | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order.line | `is_service` | Ist eine Dienstleistung | Is a Service | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order.line | `price_reduce_taxexcl` | Reduzierter Preis zzgl. USt. | Preisminderung exkl. Steuern | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order.line | `price_reduce_taxinc` | Reduzierter Preis inkl. USt. | Preisminderung inkl. Steuern | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order.line | `price_tax` | Steuern | Gesamtsteuer | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order.line | `price_total` | Total | Gesamt | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order.line | `price_unit` | Preis pro ME | Einzelpreis | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order.line | `product_uom` | Mengeneinheit | Maßeinheit | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order.line | `qty_delivered` | Ausgeliefert | Liefermenge | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order.line | `qty_invoiced` | Abgerechnet | Abgerechnete Menge | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order.line | `qty_multiplication_factor` | Multiplication Factor/Thsd | Multiplikationsfaktor (pro 1.000) | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order.line | `qty_to_invoice` | Abzurechnen | Abzurechnende Menge | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order.line | `salesman_id` | Verkäufer | Vertriebsmitarbeiter | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order.line | `salesperson_id` | Verkäufer | Salesperson | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order.line | `sequence` | Nummernfolge | Sequenz | Odoo-18-Wortlaut (bleibt, dokumentiert) |
| sale.order.line | `write_uid` | Zuletzt aktualisiert durch | Zuletzt aktualisiert von | Odoo-18-Wortlaut (bleibt, dokumentiert) |

Anzahl der abweichenden Beschriftungen: 36.

## 11. Stammdaten, die vor der Datenmigration zuzuordnen sind

Read-only in Odoo 11 gemessen, mit Odoo 18 abgeglichen (Stand 24.09.2026):

```
Zahlungsbedingungen (Feld sale.order.payment_term_id, 613 von 2.461 Auftraegen belegt)
  Odoo 11 "Sofortige Zahlung"   96 Auftraege   -> Odoo 18 vorhanden (id 1, 0 Tage ab Rechnungsdatum)
  Odoo 11 "14 Tage"            515 Auftraege   -> Odoo 18 hat "14 Tage" (id 12), aber mit
                                                  nb_days = 0 (sofort) statt 14 Tagen -> KLAERUNG
  Odoo 11 "30 Tage netto"        2 Auftraege   -> Odoo 18 "30 Tage" (id 4), 100 % nach 30 Tagen:
                                                  fachlich identisch -> kein neuer Eintrag
  Odoo 11 "15 Tage"              0 Auftraege   -> Odoo 18 vorhanden (id 2), nicht noetig

Preisliste (sale.order.pricelist_id, 2.461 von 2.461 belegt)
  Odoo 11 verwendet 25 Preislisten mit Auftraegen (Summe 2.461 Auftraege), darunter
  "Allgemeine Preisliste" (1.120), "Preisliste 2025 Preiserhoehung und Valorisierung" (345),
  "Preisliste 2026 + Valorisierung" (256), "Preisliste amtsweg-Basis 2020 Neukunden" (155),
  "GSZ Kaernten 2019 + 2020 Valorisierung" (117), viele mit dem Zusatz "nicht mehr verwenden".
  Odoo 18 hat genau eine Preisliste: "Preisliste 2026 + Valorisierung" (id 34, EUR, aktiv).
  Verbindliche Regel: alle Odoo-11-Preislisten werden auf id 34 (EUR) abgebildet, keine neuen
  Preislisten in Odoo 18.

Verkaeufer (sale.order.user_id, 2.461 belegt, 31 verschiedene Verkaeufer)
  Groesste Gruppen: IT-Kommunal 1.644, Oberoesterreich GemDAT 205, Waiss Martina 115,
  Sales GSZ Kaernten 113, Niederoesterreich GemDAT 96, Kufgem 71.
  Odoo 11 hat 57 aktive Benutzer, Odoo 18 deutlich weniger -> Benutzerzuordnung vor der Migration
  (offen seit Session 105; ausgeschiedene Benutzer deaktiviert anlegen).

Vertriebskanal (sale.order.team_id, 2.461 belegt)
  Odoo 11 nutzt 4 Kanaele: Vertriebskanaele (Intern) 2.443, Interne Weitergabe 13,
  Persoenlicher Kontakt 4, Newsletter 1. Odoo 18 hat 8 Teams -> Zuordnung entscheiden.

Stichwoerter (sale.order.tag_ids)
  Odoo 11 hat 44 crm.lead.tag-Datensaetze; im Verkauf nutzt genau 1 Auftrag (A-1900710) das
  Stichwort "Up-Sell". Odoo 18 hat derzeit 0 crm.tag-Datensaetze. Tag-Stammdaten sind im
  CRM-Bereich als Migrationspunkt dokumentiert (Session 114).

Weitere Felder ohne Pflege in Odoo 11
  source_id, campaign_id, medium_id (utm): 0 von 2.461 Auftraegen belegt -> keine Zuordnung noetig.
  fiscal_position_id: 0 von 2.461 belegt -> keine Zuordnung noetig.
```

## 12. Befunde dieser Analyse

```
1. Irrefuehrende Odoo-11-Uebersetzung: das Feld activity_state heisst in Odoo 11 auf Deutsch
   "Bundesland" (englisch "State"), in Odoo 18 "Status der Aktivität". Kein Fehler in Odoo 18,
   kein Handlungsbedarf - dokumentiert, damit der Unterschied nicht als Luecke gewertet wird.
2. tag_ids: die Angabe "0 Verwendungen" aus Session 117 ist zu korrigieren - genau 1 von 2.461
   Auftraegen traegt ein Stichwort ("Up-Sell", Auftrag A-1900710).
3. Beschriftung von note: Odoo 11 "Geschäftsbedingungen", Odoo 18 "Allgemeine
   Geschäftsbedingungen"; 2.439 von 2.461 Auftraegen sind befuellt.
4. Odoo 11 fuehrt amount_total/amount_tax/amount_untaxed als gespeicherte Felder, Odoo 18
   berechnet sie. Kein Datenverlust: die Werte entstehen bei der Migration aus den Auftragszeilen.
```

## 13. Entscheidungen von Anna (24.09.2026) und verbindliche Vorgaben

```
1. note (Geschaeftsbedingungen, 2.439 Auftraege): Inhalt aus Odoo 11 vollstaendig uebernehmen.
   Zeilenumbrueche fuer das Odoo-18-HTML-Feld korrekt in HTML umsetzen (keine weitere
   Formatierung erfinden, Sonderzeichen escapen).
2. Zahlungsbedingung "30 Tage netto" (2 Auftraege): keine Dublette anlegen. Zuordnung auf die
   vorhandene Odoo-18-Zahlungsbedingung "30 Tage" (id 4) - fachlich identisch (100 % nach
   30 Tagen ab Rechnungsdatum).
3. Stichwort "Up-Sell" (1 Auftrag A-1900710): nicht verlieren. Als spaeterer Stammdaten-/
   Migrationsschritt vorbereitet: Odoo 18 hat derzeit 0 crm.tag, anzulegen ist "Up-Sell".
4. Felder aus sale_stock und sale_timesheet duerfen entfallen (Module in Odoo 18 bewusst nicht
   installiert). Kein Nachbau, weiterhin dokumentiert (Abschnitt 7).
5. Preislisten: Zuordnung als spaeterer Datenmigrationsschritt vollstaendig vorbereitet - alle
   25 in Odoo 11 verwendeten Preislisten auf die Odoo-18-Preisliste id 34
   ("Preisliste 2026 + Valorisierung", EUR, aktiv). EUR bleibt verbindlich.

Verbindliche Regeln als Datei: migration/verkauf_migrationsregeln.json
(erzeugt mit scripts/baue_verkauf_migrationsregeln.py, Zahlen read-only gemessen).
```

**Umsetzung dieser Entscheidungen (24.09.2026, lokal; VM folgt):**

```
1. Zahlungsbedingung "14 Tage" korrigiert: nb_days war 0 (Zahlung sofort), ist jetzt 14
   (14 Tage nach Rechnungsdatum). "Sofortige Zahlung" (0) und "30 Tage" (30) unveraendert.
   Werkzeug: scripts/apply_verkauf_stammdaten.py --instanz lokal|vm [--pruefen], idempotent,
   jeweils 3 OK / 0 FEHL nach dem Schreiben.
   Vorher/nachher belegt: nb_days 0 -> 14 (account.payment.term.line id 12).
2. Reiterbeschriftung: "Auftragspositionen" -> "Auftragszeilen" (Odoo-11-Wortlaut), umgesetzt in
   itk_sale_management 18.0.1.2.0 mit einer eigenen Ansicht an der Wurzel-View
   (sale.view_order_form, priority 99, xpath //page[@name='order_lines'], position="attributes").
   Nach dem Modul-Upgrade zeigt der Reiter in de_DE "Auftragszeilen".
3. Die Gruppe "Lieferadresse" wird nicht nachgebaut (Felder aus sale_stock).
```

**Befund zur Zahlungsbedingung "14 Tage" (entschieden und umgesetzt am 24.09.2026):** In Odoo 18
trug der Eintrag "14 Tage" (id 12) den Wert `nb_days = 0`, also Zahlung sofort; Odoo 11 fuehrt
"14 Tage" mit 14 Tagen ab Rechnungsdatum. Betroffen sind 515 Auftraege. Auf Entscheidung von Anna
wurde der Odoo-18-Eintrag auf 14 Tage korrigiert (nb_days 0 -> 14); die Eintraege "Sofortige
Zahlung" und "30 Tage" blieben unveraendert.

## 14. Nachweise

```
scripts/verify_s121_verkauf_teil2.py       111 OK / 0 FEHL
                                           (prueft Odoo 11 read-only, Odoo 18 lokal und VM in einem Lauf)
scripts/baue_verkauf_migrationsregeln.py   erzeugt migration/verkauf_migrationsregeln.json
                                           (Preislisten, Zahlungsbedingungen, Stichworte, Verkaeufer,
                                            Kanaele, entfallende Felder - Zahlen read-only gemessen)
Datenlage                                   Odoo 11: sale.order 2.461, sale.order.line 4.007
                                            Odoo 18: 18 Auftraege / 28 Zeilen (lokal),
                                            20 Auftraege / 29 Zeilen (VM)
Vergleichsgrundlage                         ir.model.fields gegen fields_get geprueft (identische Feldmengen)
Testdaten                                   keine angelegt, keine geaendert
Odoo 11 Prod                                ausschliesslich lesend
```

