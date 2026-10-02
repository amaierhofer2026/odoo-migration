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
