# Label- und Feldmapping Abrechnung (Odoo 11 -> Odoo 18)

Erzeugt von `scripts/check_abrechnung_labels.py` (Stand 30.09.2026, Session 122).
Regel: sichtbare Bezeichnung wie Odoo 11, technischer Feldname bleibt Odoo 18.

| Odoo-11-Feld | Odoo-11-Bezeichnung | Odoo-18-Zielfeld | Odoo-18-Bezeichnung | Zustand | Anmerkung |
| --- | --- | --- | --- | --- | --- |
| `account.invoice.partner_id` | Partner | `account.move.partner_id` | Partner | gleich | Kunde |
| `account.invoice.commercial_partner_id` | Gewerbliche Einheit | `account.move.commercial_partner_id` | Gewerbliche Einheit | gleich | gewerbliche Einheit |
| `account.invoice.date_invoice` | Rechnungsdatum | `account.move.invoice_date` | Rechnungsdatum | gleich | umbenannt |
| `account.invoice.date_due` | Fälligkeit | `account.move.invoice_date_due` | Fälligkeit | gleich | umbenannt |
| `account.invoice.date` | Buchungsdatum | `account.move.date` | Buchungsdatum | gleich | Buchungsdatum |
| `account.invoice.number` | Nummer | `account.move.name` | Nummer | gleich | umbenannt (Belegnummer) |
| `account.invoice.reference` | Lieferantenreferenz | `account.move.ref` | Referenz | begruendet abweichend | umbenannt, in Odoo 11 ungenutzt |
| `account.invoice.origin` | Referenzbeleg | `account.move.invoice_origin` | Referenzbeleg | gleich | umbenannt |
| `account.invoice.comment` | Weitere Informationen | `account.move.narration` | Weitere Informationen | gleich | umbenannt |
| `account.invoice.state` | Status | `account.move.state` | Status | gleich | Zustand |
| `account.invoice.type` | Typ | `account.move.move_type` | Typ | gleich | umbenannt |
| `account.invoice.company_id` | Unternehmen | `account.move.company_id` | Unternehmen | gleich |  |
| `account.invoice.currency_id` | Währung | `account.move.currency_id` | Währung | gleich |  |
| `account.invoice.journal_id` | Journal | `account.move.journal_id` | Journal | gleich |  |
| `account.invoice.user_id` | Verkäufer | `account.move.invoice_user_id` | Verkäufer | gleich | Verkaeufer |
| `account.invoice.team_id` | Vertriebskanal | `account.move.team_id` | Vertriebskanal | gleich | Vertriebskanal |
| `account.invoice.payment_term_id` | Zahlungsbedingungen | `account.move.invoice_payment_term_id` | Zahlungsbedingungen | gleich | umbenannt |
| `account.invoice.fiscal_position_id` | Steuerzuordnung | `account.move.fiscal_position_id` | Steuerzuordnung | gleich | Steuerzuordnung |
| `account.invoice.partner_bank_id` | Bankkonto | `account.move.partner_bank_id` | Bankkonto | gleich |  |
| `account.invoice.amount_untaxed` | Nettobetrag | `account.move.amount_untaxed` | Nettobetrag | gleich |  |
| `account.invoice.amount_tax` | Steuer | `account.move.amount_tax` | Steuer | gleich |  |
| `account.invoice.amount_total` | Total | `account.move.amount_total` | Total | gleich |  |
| `account.invoice.amount_untaxed_signed` | Nettobetrag in Unternehmenswährung | `account.move.amount_untaxed_signed` | Nettobetrag in Unternehmenswährung | gleich |  |
| `account.invoice.amount_total_signed` | Gesamtbetrag in Rechnungswährung | `account.move.amount_total_signed` | Gesamtbetrag in Rechnungswährung | gleich |  |
| `account.invoice.amount_total_company_signed` | Gesamt (in eigener Währung) | `account.move.amount_total_in_currency_signed` | Gesamt (in eigener Währung) | gleich | umbenannt |
| `account.invoice.residual` | Fälliger Betrag | `account.move.amount_residual` | Fälliger Betrag | gleich | umbenannt |
| `account.invoice.payment_reference` | - | `account.move.payment_reference` | Zahlungsreferenz | begruendet abweichend |  |
| `account.invoice.notice` | Rechnungsnotiz | `account.move.notice` | Rechnungsnotiz | gleich | ITK-Feld |
| `account.invoice.projectcategory_id` | Project Category | `account.move.projectcategory_id` | Project Category | gleich | ITK-Feld |
| `account.invoice.valorisierung_id` | Valorisation Text | `account.move.valorisierung_id` | Valorisation Text | gleich | ITK-Feld |
| `account.invoice.sent` | Gesendet | `account.move.is_move_sent` | Gesendet | gleich | umbenannt |
| `account.invoice.reconciled` | Bezahlt/Abgestimmt | `account.move.has_reconciled_entries` | Bezahlt/Abgestimmt | gleich | umbenannt |
| `account.invoice.payment_move_line_ids` | Zahlungsbuchungszeilen | `account.move.matched_payment_ids` | Zahlungsbuchungszeilen | gleich | anderes Modell |
| `account.invoice.incoterms_id` | Lieferbedingungen | `account.move.invoice_incoterm_id` | Lieferbedingungen | gleich | umbenannt |
| `account.invoice.cash_rounding_id` | Methode zur Bargeldrundung | `account.move.invoice_cash_rounding_id` | Methode zur Bargeldrundung | gleich | umbenannt |
| `account.invoice.invoice_line_ids` | Rechnungszeilen | `account.move.invoice_line_ids` | Rechnungszeilen | gleich |  |
| `account.invoice.move_name` | Buchungssatzname | `account.move.name` | Nummer | begruendet abweichend | aufgegangen in name |
| `account.invoice.line.invoice_id` | Rechnungsreferenz | `account.move.line.move_id` | Rechnungsreferenz | gleich | umbenannt |
| `account.invoice.line.name` | Beschreibung | `account.move.line.name` | Beschreibung | gleich | Beschreibung |
| `account.invoice.line.quantity` | Menge | `account.move.line.quantity` | Menge | gleich |  |
| `account.invoice.line.price_unit` | Preis pro ME | `account.move.line.price_unit` | Preis pro ME | gleich |  |
| `account.invoice.line.discount` | Rabatt (%) | `account.move.line.discount` | Rabatt (%) | gleich |  |
| `account.invoice.line.price_subtotal` | Betrag | `account.move.line.price_subtotal` | Betrag | gleich |  |
| `account.invoice.line.price_total` | Betrag | `account.move.line.price_total` | Betrag | gleich |  |
| `account.invoice.line.product_id` | Produkt | `account.move.line.product_id` | Produkt | gleich |  |
| `account.invoice.line.uom_id` | Mengeneinheit | `account.move.line.product_uom_id` | Mengeneinheit | gleich | umbenannt |
| `account.invoice.line.account_id` | Konto | `account.move.line.account_id` | Konto | gleich |  |
| `account.invoice.line.invoice_line_tax_ids` | Steuern | `account.move.line.tax_ids` | Steuern | gleich | umbenannt |
| `account.invoice.line.purchase_line_id` | Bestellposition | `account.move.line.purchase_line_id` | Bestellposition | gleich |  |
| `account.invoice.line.sequence` | Nummernfolge | `account.move.line.sequence` | Nummernfolge | gleich |  |
| `account.invoice.line.company_currency_id` | Betriebl. Währung | `account.move.line.company_currency_id` | Betriebl. Währung | gleich |  |
| `account.invoice.line.currency_id` | Währung | `account.move.line.currency_id` | Währung | gleich |  |
| `account.invoice.line.partner_id` | Partner | `account.move.line.partner_id` | Partner | gleich |  |
| `account.invoice.line.company_id` | Unternehmen | `account.move.line.company_id` | Unternehmen | gleich |  |
| `account.invoice.line.projectcategory_id` | - | `account.move.line.projectcategory_id` | - | FELD FEHLT | ITK-Feld |
| `account.invoice.line.valorisierung_id` | - | `account.move.line.valorisierung_id` | - | FELD FEHLT | ITK-Feld |
| `account.invoice.line.account_analytic_id` | Kostenstelle | `account.move.line.analytic_distribution` | Kostenstelle | gleich | anderes Modell |
| `product.template.barcode` | Strichcode | `product.template.barcode` | Strichcode | gleich |  |
| `product.product.barcode` | Strichcode | `product.product.barcode` | Strichcode | gleich |  |
| `product.template.categ_id` | Interne Kategorie | `product.template.categ_id` | Interne Kategorie | gleich |  |
| `product.product.categ_id` | Interne Kategorie | `product.product.categ_id` | Interne Kategorie | gleich |  |
| `product.template.cost_method` | Kostenmethode | `product.template.cost_method` | Kostenmethode | gleich |  |
| `product.product.cost_method` | Kostenmethode | `product.product.cost_method` | Kostenmethode | gleich |  |
| `product.template.description_picking` | Beschreibung der Kommisionierung | `product.template.description_picking` | Beschreibung der Kommisionierung | gleich |  |
| `product.product.description_picking` | Beschreibung der Kommisionierung | `product.product.description_picking` | Beschreibung der Kommisionierung | gleich |  |
| `product.template.expense_policy` | Spesen weiter verrechnen | `product.template.expense_policy` | Spesen weiter verrechnen | gleich |  |
| `product.product.expense_policy` | Spesen weiter verrechnen | `product.product.expense_policy` | Spesen weiter verrechnen | gleich |  |
| `product.template.invoice_policy` | Fakturierungsregel | `product.template.invoice_policy` | Fakturierungsregel | gleich |  |
| `product.product.invoice_policy` | Fakturierungsregel | `product.product.invoice_policy` | Fakturierungsregel | gleich |  |
| `product.template.is_multi_factor_product` | To multiply by Factor(per 1000) | `product.template.is_multi_factor_product` | To multiply by Factor(per 1000) | gleich |  |
| `product.product.is_multi_factor_product` | To multiply by Factor(per 1000) | `product.product.is_multi_factor_product` | To multiply by Factor(per 1000) | gleich |  |
| `product.template.nbr_reordering_rules` | Meldebestände | `product.template.nbr_reordering_rules` | Meldebestände | gleich |  |
| `product.product.nbr_reordering_rules` | Meldebestände | `product.product.nbr_reordering_rules` | Meldebestände | gleich |  |
| `product.template.orderpoint_ids` | - | `product.template.orderpoint_ids` | - | FELD FEHLT |  |
| `product.product.orderpoint_ids` | Meldebestandsregeln | `product.product.orderpoint_ids` | Meldebestandsregeln | gleich |  |
| `product.template.outgoing_qty` | Ausgehend | `product.template.outgoing_qty` | Ausgehend | gleich |  |
| `product.product.outgoing_qty` | Ausgehend | `product.product.outgoing_qty` | Ausgehend | gleich |  |
| `product.template.packaging_ids` | Produktverpackungen | `product.template.packaging_ids` | Produktverpackungen | gleich |  |
| `product.product.packaging_ids` | Produktverpackungen | `product.product.packaging_ids` | Produktverpackungen | gleich |  |
| `product.template.partner_ref` | - | `product.template.partner_ref` | - | FELD FEHLT |  |
| `product.product.partner_ref` | Kunden Ref | `product.product.partner_ref` | Kunden Ref | gleich |  |
| `product.template.product_type_id` | Product-Type | `product.template.product_type_id` | Produktart | begruendet abweichend | bewusst abweichend |
| `product.product.product_type_id` | Product-Type | `product.product.product_type_id` | Produktart | begruendet abweichend | bewusst abweichend |
| `product.template.product_variant_count` | # Produkt Varianten | `product.template.product_variant_count` | # Produkt Varianten | gleich |  |
| `product.product.product_variant_count` | # Produkt Varianten | `product.product.product_variant_count` | # Produkt Varianten | gleich |  |
| `product.template.property_account_income_id` | Erlöskonto | `product.template.property_account_income_id` | Erlöskonto | gleich |  |
| `product.product.property_account_income_id` | Erlöskonto | `product.product.property_account_income_id` | Erlöskonto | gleich |  |
| `product.template.property_stock_inventory` | Lagerort Bestandsaufnahme | `product.template.property_stock_inventory` | Lagerort Bestandsaufnahme | gleich |  |
| `product.product.property_stock_inventory` | Lagerort Bestandsaufnahme | `product.product.property_stock_inventory` | Lagerort Bestandsaufnahme | gleich |  |
| `product.template.property_stock_production` | Fertigungort (virtuelles Lager) | `product.template.property_stock_production` | Fertigungort (virtuelles Lager) | gleich |  |
| `product.product.property_stock_production` | Fertigungort (virtuelles Lager) | `product.product.property_stock_production` | Fertigungort (virtuelles Lager) | gleich |  |
| `product.template.purchase_line_warn` | Bestellposition | `product.template.purchase_line_warn` | Bestellposition | gleich |  |
| `product.product.purchase_line_warn` | Bestellposition | `product.product.purchase_line_warn` | Bestellposition | gleich |  |
| `product.template.purchase_ok` | Kann eingekauft werden | `product.template.purchase_ok` | Kann eingekauft werden | gleich |  |
| `product.product.purchase_ok` | Kann eingekauft werden | `product.product.purchase_ok` | Kann eingekauft werden | gleich |  |
| `product.template.qty_available` | Bestandsmenge | `product.template.qty_available` | Bestandsmenge | gleich |  |
| `product.product.qty_available` | Bestandsmenge | `product.product.qty_available` | Bestandsmenge | gleich |  |
| `product.template.sale_delay` | Auslieferungszeit | `product.template.sale_delay` | Auslieferungszeit | gleich |  |
| `product.product.sale_delay` | Auslieferungszeit | `product.product.sale_delay` | Auslieferungszeit | gleich |  |
| `product.template.sale_line_warn` | Auftragsposition | `product.template.sale_line_warn` | Auftragsposition | gleich |  |
| `product.product.sale_line_warn` | Auftragsposition | `product.product.sale_line_warn` | Auftragsposition | gleich |  |
| `product.template.sale_line_warn_msg` | Mitteilung für Auftragszeile | `product.template.sale_line_warn_msg` | Mitteilung für Auftragszeile | gleich |  |
| `product.product.sale_line_warn_msg` | Mitteilung für Auftragszeile | `product.product.sale_line_warn_msg` | Mitteilung für Auftragszeile | gleich |  |
| `product.template.sale_ok` | Kann verkauft werden | `product.template.sale_ok` | Kann verkauft werden | gleich |  |
| `product.product.sale_ok` | Kann verkauft werden | `product.product.sale_ok` | Kann verkauft werden | gleich |  |
| `product.template.sales_count` | # Verkäufe | `product.template.sales_count` | # Verkäufe | gleich |  |
| `product.product.sales_count` | # Verkäufe | `product.product.sales_count` | # Verkäufe | gleich |  |
| `product.template.sequence` | Nummernfolge | `product.template.sequence` | Nummernfolge | gleich |  |
| `product.product.sequence` | Nummernfolge | `product.product.sequence` | Nummernfolge | gleich |  |
| `product.template.service_type` | Dienstleistungsverfolgung | `product.template.service_type` | Dienstleistungsverfolgung | gleich |  |
| `product.product.service_type` | Dienstleistungsverfolgung | `product.product.service_type` | Dienstleistungsverfolgung | gleich |  |
| `product.template.supplier_taxes_id` | Steuern (Einkauf) | `product.template.supplier_taxes_id` | Steuern (Einkauf) | gleich |  |
| `product.product.supplier_taxes_id` | Steuern (Einkauf) | `product.product.supplier_taxes_id` | Steuern (Einkauf) | gleich |  |
| `product.template.taxes_id` | Steuern (Verkauf) | `product.template.taxes_id` | Steuern (Verkauf) | gleich |  |
| `product.product.taxes_id` | Steuern (Verkauf) | `product.product.taxes_id` | Steuern (Verkauf) | gleich |  |
| `product.template.uom_id` | Mengeneinheit | `product.template.uom_id` | Mengeneinheit | gleich |  |
| `product.product.uom_id` | Mengeneinheit | `product.product.uom_id` | Mengeneinheit | gleich |  |
| `product.template.uom_po_id` | Einkauf ME | `product.template.uom_po_id` | Einkauf ME | gleich |  |
| `product.product.uom_po_id` | Einkauf ME | `product.product.uom_po_id` | Einkauf ME | gleich |  |
| `product.template.valuation` | Bewertung | `product.template.valuation` | Bewertung | gleich |  |
| `product.product.valuation` | Bewertung | `product.product.valuation` | Bewertung | gleich |  |
| `product.template.warehouse_id` | Lager | `product.template.warehouse_id` | Lager | gleich |  |
| `product.product.warehouse_id` | Lager | `product.product.warehouse_id` | Lager | gleich |  |
| `product.template.lst_price` | Allgemeiner Preis | `product.template.lst_price` | - | FELD FEHLT |  |
| `product.product.lst_price` | Verkaufspreis | `product.product.lst_price` | Verkaufspreis | gleich |  |
| `product.template.is_product_variant` | Ist eine Produktvariante | `product.template.is_product_variant` | Ist eine Produktvariante | gleich |  |
| `product.product.is_product_variant` | Ist eine Produktvariante | `product.product.is_product_variant` | Ist eine Produktvariante | gleich |  |
| `product.template.virtual_available` | Geplante Bestandsmenge | `product.template.virtual_available` | Geplante Bestandsmenge | gleich |  |
| `product.product.virtual_available` | Prognostizierter Bestand | `product.product.virtual_available` | Prognostizierter Bestand | gleich |  |
| `product.template.website_message_ids` | Website-Nachrichten | `product.template.website_message_ids` | Website Messages | begruendet abweichend |  |
| `product.product.website_message_ids` | Website-Nachrichten | `product.product.website_message_ids` | Website Messages | begruendet abweichend |  |
| `product.template.activity_state` | Bundesland | `product.template.activity_state` | Status der Aktivität | begruendet abweichend | bewusst abweichend |
| `product.product.activity_state` | Bundesland | `product.product.activity_state` | Status der Aktivität | begruendet abweichend | bewusst abweichend |
| `product.template.activity_summary` | Zusammenfassung nächste Aktion | `product.template.activity_summary` | Zusammenfassung der nächsten Aktivität | begruendet abweichend | bewusst abweichend |
| `product.product.activity_summary` | Zusammenfassung nächste Aktion | `product.product.activity_summary` | Zusammenfassung der nächsten Aktivität | begruendet abweichend | bewusst abweichend |
| `product.template.activity_user_id` | Verantwortlich | `product.template.activity_user_id` | Verantwortlicher Benutzer | begruendet abweichend | bewusst abweichend |
| `product.product.activity_user_id` | Verantwortlich | `product.product.activity_user_id` | Verantwortlicher Benutzer | begruendet abweichend | bewusst abweichend |
| `product.template.message_follower_ids` | Abonnenten | `product.template.message_follower_ids` | Follower | begruendet abweichend | bewusst abweichend |
| `product.product.message_follower_ids` | Abonnenten | `product.product.message_follower_ids` | Follower | begruendet abweichend | bewusst abweichend |
| `product.template.message_is_follower` | Ist ein Abonnent | `product.template.message_is_follower` | Ist Follower | begruendet abweichend | bewusst abweichend |
| `product.product.message_is_follower` | Ist ein Abonnent | `product.product.message_is_follower` | Ist Follower | begruendet abweichend | bewusst abweichend |
| `product.template.message_partner_ids` | Abonnenten (Partner) | `product.template.message_partner_ids` | Follower (Partner) | begruendet abweichend | bewusst abweichend |
| `product.product.message_partner_ids` | Abonnenten (Partner) | `product.product.message_partner_ids` | Follower (Partner) | begruendet abweichend | bewusst abweichend |
| `product.template.website_message_ids` | Website-Nachrichten | `product.template.website_message_ids` | Website Messages | begruendet abweichend | bewusst abweichend |
| `product.product.website_message_ids` | Website-Nachrichten | `product.product.website_message_ids` | Website Messages | begruendet abweichend | bewusst abweichend |
| `product.template.rating_ids` | Bewertung | `product.template.rating_ids` | Ratings | begruendet abweichend | bewusst abweichend |
| `product.product.rating_ids` | Bewertung | `product.product.rating_ids` | Ratings | begruendet abweichend | bewusst abweichend |
| `product.template.write_date` | Zuletzt aktualisiert am | `product.template.write_date` | Zuletzt aktualisiert am | gleich | bewusst abweichend |
| `product.product.write_date` | Zuletzt aktualisiert am | `product.product.write_date` | Änderungsdatum | begruendet abweichend | bewusst abweichend |
| `product.template.write_uid` | Zuletzt aktualisiert durch | `product.template.write_uid` | Zuletzt aktualisiert von | begruendet abweichend | bewusst abweichend |
| `product.product.write_uid` | Zuletzt aktualisiert durch | `product.product.write_uid` | Zuletzt aktualisiert von | begruendet abweichend | bewusst abweichend |
| `product.template.service_tracking` | Dienstverfolgung | `product.template.service_tracking` | Bei Auftrag erstellen | begruendet abweichend | bewusst abweichend |
| `product.product.service_tracking` | Dienstverfolgung | `product.product.service_tracking` | Bei Auftrag erstellen | begruendet abweichend | bewusst abweichend |
| `product.template.cost_currency_id` | Cost Currency | `product.template.cost_currency_id` | Kostenwährung | begruendet abweichend | bewusst abweichend |
| `product.product.cost_currency_id` | Cost Currency | `product.product.cost_currency_id` | Kostenwährung | begruendet abweichend | bewusst abweichend |
| `product.template.purchase_line_warn_msg` | Bachricht bei Beschaffungsauftragsposition | `product.template.purchase_line_warn_msg` | Nachricht für Bestellzeile | begruendet abweichend | bewusst abweichend |
| `product.product.purchase_line_warn_msg` | Bachricht bei Beschaffungsauftragsposition | `product.product.purchase_line_warn_msg` | Nachricht für Bestellzeile | begruendet abweichend | bewusst abweichend |
