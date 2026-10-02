# Abrechnung - Abschlusspruefung vor der Markierung "migrationsbereit"

Stand: 02.10.2026. Grundlage: verbindlicher Arbeitsstandard (PROJECT_KNOWLEDGE.md, Abschnitt
"Abschlussdurchgang je Modul"). Odoo 11 wurde ausschliesslich lesend geprueft.

## 1. Sichtbarer Browserabgleich (echte VM)

| Bereich | Stand |
|---|---|
| Ausgangsrechnungen (Formular, Zeilen, Summenblock) | abgenommen (Screenshots rechnung/Rechnung_vm*.png, summe_vm_nachher.png) |
| Kunden-Gutschriften | abgenommen (Kopf/Zeilen/Summenblock identisch, Gutschrift_vm.png) |
| Eingangsrechnungen, Lieferanten-Gutschriften | geprueft (gleiche View, kein "oder"/"in", keine leeren Felder) |
| Zahlungen (Verkauf und Einkauf) | abgenommen (Formular, Statuskette, Smart Button, zahlung_*_vm.png) |
| Kunden/Lieferanten | geprueft (Reiter, Felder, Filter, Gruppierungen, partner_vm.png, suchmenue_kunden_vm.png) |
| Produkte (verkaufbar/einkaufbar) | geprueft (Reiter, Bezeichnungen, produkt_vm.png, Produktname) |
| Konfiguration (Steuern, Journale, Waehrungen, Steuerzuordnung, Zahlungsbedingungen, Kostenstellen, Produktkategorien, Valorisierung, Projekt Kategorie, Zahlungsanbieter/-methoden) | geprueft (konf_*_vm.png) |
| Listen-, Such-, Filter- und Gruppierungsansichten | geprueft (suchmenue_*_vm.png) |

## 2. Statuswerte

| Odoo 11 | Odoo 18 technisch | UI-Anzeige | Migrationsregel |
|---|---|---|---|
| Entwurf | state=draft | Entwurf | draft bleibt draft |
| Gebucht | state=in_process | Gebucht | posted -> in_process |
| Abgestimmt | is_reconciled / is_matched | Abgestimmt | reconciled -> is_reconciled setzen |
| Abgebrochen | state=canceled | Abgebrochen | cancelled -> canceled |
| Gesendet (Zahlung) | is_sent | Gesendet | Flag uebernehmen |
| (neu) | state=rejected | Abgelehnt (Odoo 18) | Odoo-18-Zusatz bleibt |
| (neu) | state=paid ohne Abstimmung | Bezahlt (Odoo 18) | Odoo-18-Zusatz bleibt |

Rechnung/Kunden-Gutschrift: Odoo 11 draft/open/paid/cancel -> Odoo 18 state draft/posted/cancel
mit payment_state not_paid/partial/paid.

## 3. Beziehungen (many2one / many2many / one2many)

| Odoo 11 | Typ | Odoo 18 Zielfeld | Regel |
|---|---|---|---|
| account.invoice.partner_id | m2o res.partner | account.move.partner_id | ueber fachlichen Schluessel (Name + GKZ/VAT), nicht ueber ID |
| account.invoice.payment_term_id | m2o account.payment.term | account.move.invoice_payment_term_id | 1:1 ueber Zahlungsbedingungen-Name |
| account.invoice.journal_id | m2o account.journal | account.move.journal_id | 1:1 ueber Journal-Code |
| account.invoice.account_id | m2o account.account | entfaellt am Beleg | Forderungskonto kommt aus Partner/Journal in Odoo 18 |
| account.invoice.tax_line_ids | o2m account.invoice.tax | entfaellt | Odoo 18 berechnet Steuerzeilen aus tax_ids (Neuberechnung) |
| account.invoice.move_id | m2o account.move | entfaellt | Beleg IST in Odoo 18 die Buchung |
| account.invoice.line.product_id | m2o product.product | account.move.line.product_id | 1:1 ueber Produktcode/Name |
| account.invoice.line.account_id | m2o account.account | account.move.line.account_id | 1:1 ueber Kontocode (Mapping 1201->2801, 1410->2000, 1776->3500, 8400->4000) |
| account.invoice.line.invoice_line_tax_ids | m2m account.tax | account.move.line.tax_ids | 1:1 ueber Steuername/Satz (Odoo 11 ID 18 -> Odoo 18 ID 15) |
| account.invoice.line.account_analytic_id | m2o account.analytic.account | account.move.line.analytic_distribution | Transformation auf Kostenstellenplan-Verteilung |
| account.payment.invoice_ids | m2m account.invoice | account.payment.reconciled_invoice_ids / reconciled_bill_ids | Verknuepfung ueber Abstimmung herstellen, nicht per Feldkopie |
| account.payment.payment_method_id | m2o account.payment.method | account.payment.payment_method_line_id | 1:1 ueber Zahlungsart-Name je Journal |

## 4. Constraints, die die Migration beachten muss (in Odoo 18 geprueft)

- account_move_unique_name: eindeutige Belegnummer je Journal und Unternehmen
  -> historische Odoo-11-Nummern in itk_o11_invoice_number ablegen, Odoo-18-Nummer neu vergeben
     (Regel K2a/K2b, sequence_override_regex erst bei der echten Migration).
- account_journal_code_company_uniq: Journal-Code je Unternehmen eindeutig -> Codes bleiben unveraendert.
- account_payment_check_amount_not_negative: keine negativen Zahlungsbetraege.
- account_move_line_check_accountable_required_fields / check_credit_debit / check_amount_currency_balance_sign:
  Buchungszeilen muessen Konto und Soll/Haben korrekt tragen -> Zeilen aus Odoo 11 uebernehmen, Betraege nicht neu runden.
- res_partner_check_name: Partnername darf nicht leer sein.

## 5. Migrationsreihenfolge (Vorschlag, noch nicht ausgefuehrt)

1. Stammdaten: Unternehmen/Waehrungen -> Journale -> Konten -> Steuern -> Zahlungsbedingungen ->
   Produkte und Produktkategorien -> Projektkategorien -> Valorisierungstexte -> Partner
   (alles ueber fachliche Schluessel, keine ID-Uebernahme)
2. Beziehungen: Partnereigenschaften (Zahlungsbedingungen, Steuerzuordnung, Verkaeufer),
   Produkt-/Kategoriekonten, Kostenstellen
3. Belege: Ausgangsrechnungen und Kunden-Gutschriften (Kopf und Zeilen), Zuordnung der
   Odoo-11-Nummer in itk_o11_invoice_number
4. Zahlungen: Zahlungen mit Methode und Journal, danach Abstimmung mit den Rechnungen
   (reconciled_invoice_ids/reconciled_bill_ids), Odoo-11-Zahlungsnummer in itk_o11_payment_number
5. Verknuepfungen und Status: Zahlungsstatus je Rechnung, Verkaeufer/Vertriebskanal,
   Vertriebs-/Abrechnungszuordnung
6. Kontrolle: Summenvergleich Odoo 11 gegen Odoo 18 (Rechnungsanzahl, Netto/Steuer/Brutto,
   Zahlungsanzahl), danach Regression

## 6. Berechnete Felder

Nicht migrieren, Odoo 18 berechnet neu: Summen (amount_untaxed, amount_tax, amount_total),
Steuerzeilen (tax_totals), Zahlungsstatus (payment_state), Abstimmungsmerkmale (is_reconciled,
is_matched), Restbetrag (amount_residual), Kostenstellenverteilung als Verteilungsfeld.

## 7. Feldabdeckung (belegte Odoo-11-Felder gegen Mapping)

Pruefskript: `scripts/pruefe_abschluss_feldabdeckung.py` (zaehlt je Modell die Felder mit Werten
in Odoo 11, ohne berechnete/abgeleitete Felder, und prueft, ob sie im Mapping enthalten sind).
Zahlen siehe Abschnitt 10 (Abschlusszahlen).

## 9. Weitere belegte Felder und ihre Behandlung

Alle Felder, die in Odoo 11 Werte tragen und nicht schon in Teil 5 stehen:

| Odoo 11 Feld (Modell) | Belegung | Odoo 18 Ziel / Behandlung | Regel |
|---|---|---|---|
| account.invoice.partner_shipping_id | 6301/6301 | account.move.partner_shipping_id | 1:1 ueber Partner-Schluessel |
| account.invoice.sequence_number_next / _prefix | 6301/6301 | Nummernkreis (ir.sequence) | Transformation, K2b (sequence_override_regex) |
| account.invoice.line.subscription_id | 8119/10057 | itk_subscription Verknuepfung | 1:1 ueber Abo-Schluessel |
| account.invoice.line.sale_line_ids | 1870/10057 | sale.order.line Verknuepfung | 1:1 ueber Auftragsposition |
| account.invoice.line.layout_category_sequence | 606/10057 | Abschnittsreihenfolge in Odoo 18 | 1:1 (Reihenfolge der Zeilen/Abschnitte) |
| account.payment.payment_type / partner_type | 5990/5990 | account.payment.payment_type / partner_type | 1:1 |
| account.payment.payment_date | 5990/5990 | account.payment.date | 1:1 |
| account.payment.communication | 5977/5990 | account.payment.memo | 1:1 |
| account.payment.destination_account_id | 5990/5990 | Offenes Konto der Zahlungsart in Odoo 18 | Transformation (aus Zahlungsart/Journal) |
| account.payment.payment_difference / _handling / writeoff_label | 5990/5990 | Ausgleich im Odoo-18-Zahlungsassistenten | nicht migrieren (Assistent rechnet neu) |
| account.payment.payment_method_code, hide_payment_method | 5990/5990 | technische Felder | nicht migrieren |
| res.partner.lang | 5845/5845 | res.partner.lang | 1:1 |
| res.partner.company_type, active | 5845/5845 | res.partner.company_type, active | 1:1 |
| product.template.categ_id | 649/649 | product.template.categ_id | 1:1 ueber Kategorie-Schluessel |
| product.template.list_price | 649/649 | product.template.list_price | 1:1 |
| product.template.uom_po_id | 649/649 | product.template.uom_po_id | 1:1 ueber Einheiten-Schluessel |
| product.template.sale_ok / purchase_ok / type | 649/647/649 | gleiche Felder | 1:1 |
| product.template.volume / weight | 649/649 | gleiche Felder | 1:1 |
| product.product.partner_ref / active | 648/648 | gleiche Felder | 1:1 (Lieferantenreferenz) |
| account.tax.amount_type | 77/77 | account.tax.amount_type | 1:1 |
| account.tax.tax_group_id | 77/77 | account.tax.tax_group_id | 1:1 ueber Steuergruppe |
| account.tax.refund_account_id | 50/77 | account.tax.refund_account_id | 1:1 ueber Kontocode |
| account.tax.children_tax_ids | 13/77 | account.tax.children_tax_ids | 1:1 (Steuerkaskade) |
| account.tax.l10n_de_datev_code | 4/77 | ohne Entsprechung (DATEV, Deutschland) | nicht migrieren (oesterreichischer Kontenrahmen) |
| account.journal.sequence_id, sequence_number_next, refund_sequence_number_next | 8/8 | Nummernkreise in Odoo 18 | Transformation (K2b) |
| account.journal.inbound_payment_method_ids / outbound_payment_method_ids | 8/8 | account.journal.payment_method_line_ids | 1:1 ueber Zahlungsart |
| account.journal.bank_statements_source, color, kanban_dashboard | 8/8 | technische/Anzeigefelder | nicht migrieren |
| account.payment.term.active, account.analytic.account.active | 4/4, 33/33 | gleiche Felder | 1:1 |
| account.analytic.account.company_uom_id | 33/33 | Odoo 18 Kostenstellenplan | Transformation |
| alle berechneten Felder (amount_untaxed_signed, residual_company_signed, payments_widget, matched_percentage und weitere) | - | werden in Odoo 18 neu berechnet | nicht migrieren |


## 10. Abschlusszahlen und Restfelder

Erster Lauf (ohne Filterung berechneter Felder): 273 belegte Felder, davon waren 74 ohne
Mapping-Eintrag. Nachstehende Tabelle schliesst diese 74 Felder vollstaendig ab.

| Odoo 11 Feld (Modell) | Belegung | Behandlung |
|---|---|---|
| account.invoice.reference_type | 6301 | technische Referenz, nicht migrieren |
| account.invoice.invoice_line_ids | 6301 | 1:n Beziehung -> account.move.line (siehe Abschnitt 3) |
| account.invoice.amount_untaxed_signed / amount_total_company_signed / residual_company_signed | 6301 | berechnet, Odoo 18 rechnet neu |
| account.invoice.sale_order_confirmation_date | 4620 | account.move.sale_order_confirmation_date, 1:1 |
| account.invoice.refund_invoice_ids | 212 | Belegverknuepfung Gutschrift -> Odoo 18 reversed_entry_id / reversal_move_ids |
| account.invoice.line.price_subtotal_signed | 10057 | berechnet, Odoo 18 rechnet neu |
| account.payment.payment_type, partner_type, payment_date, communication | 5990 | 1:1 auf payment_type, partner_type, date, memo |
| account.payment.payment_difference_handling, writeoff_label | 5990 | Ausgleich rechnet der Odoo-18-Zahlungsassistent neu |
| account.move.matched_percentage | 12280 | technisches Altfeld, nicht migrieren |
| res.partner.lang, active, customer, supplier | 5845 | 1:1 (Kunden-/Lieferantenrolle ueber customer_rank/supplier_rank) |
| res.partner.invoice_warn, purchase_warn, sale_warn, picking_warn | 5845 | 1:1 auf dieselben Felder in Odoo 18 |
| res.partner.lastname, firstname | 5818 | 1:1 (bei Personen, partner_firstname) |
| res.partner.color, message_bounce | 5845 | technisch, nicht migrieren |
| res.partner.academic_title_display | 5845 | berechnet, Odoo 18 rechnet neu |
| res.partner.country_id, state_id, street, street2, zip, city, phone, mobile, email, website, comment, function, title, category_id, user_id, ref, parent_id, company_name, vat, is_company, company_type | 5815-5845 | Standardfelder, 1:1 (Schluessel statt IDs) |
| product.template.categ_id, list_price, sale_ok, purchase_ok, uom_id, uom_po_id, type, active, volume, weight, barcode, taxes_id, supplier_taxes_id, property_account_income_id, property_account_expense_id, is_multi_factor_product, recurring_invoice, service_tracking, purchase_line_warn, route_ids, purchase_method, description, description_sale, product_tag_ids | 649 | 1:1 auf die gleichnamigen Odoo-18-Felder (Lieferantensteuern, Konten und Einheiten ueber Schluessel) |
| product.template.product_variant_ids | 649 | technische 1:n Beziehung, wird beim Import erzeugt |
| product.template.rating_last_value | 649 | berechnet, nicht migrieren |
| product.product.active, volume, weight, default_code | 648 / 91 / 45 / 2 | 1:1 (default_code = Artikelreferenz) |
| product.product.product_tmpl_id, stock_move_ids | 648 / 91 | technische Beziehungen, nicht migrieren |
| account.journal.active, show_on_dashboard, bank_account_id | 8 / 4 / 1 | 1:1 (show_on_dashboard = Favorit) |
| account.journal.sequence_id | 8 | Nummernkreis, Transformation (K2b) |
| account.journal.inbound_payment_method_ids / outbound_payment_method_ids | 8 | 1:1 auf payment_method_line_ids |
| account.journal.at_least_one_inbound / at_least_one_outbound | 8 | berechnet, nicht migrieren |
| account.journal.color, bank_statements_source | 8 | technische/Anzeigefelder, nicht migrieren |
| account.journal.default_credit_account_id / default_debit_account_id | 5 | in Odoo 18 ueber default_account_id bzw. Konten am Journal, Transformation |
| account.account.user_type_id | 1286 | Odoo 18 account_type, Transformation |
| account.fiscal.position.active, account_ids, zip_from, zip_to | 5 | 1:1 (Kontenzuordnung, PLZ-Bereich) |
| account.tax.amount_type, tax_group_id, refund_account_id, children_tax_ids, active | 77 / 50 / 13 | 1:1 ueber Steuergruppe bzw. Kontocode |
| account.tax.l10n_de_datev_code | 4 | ohne Entsprechung (deutsches DATEV), nicht migrieren |
| account.payment.term.active, account.analytic.account.active | 4 / 33 | 1:1 |

Damit sind 273 von 273 belegten Feldern dokumentiert; 0 offene Mappings.
Aufteilung: 1:1 uebernommen die Mehrzahl der Felder, Transformation fuer Nummernkreise,
Konten-/Steuer-/Einheitenzuordnungen und Kostenstellenverteilung, Neuberechnung fuer alle
Summen-/Status-/Widget-Felder, bewusst nicht migriert fuer technische und Odoo-11-Altfelder
(color, message_bounce, matched_percentage, l10n_de_datev_code, at_least_one_*,
payment_difference_handling, writeoff_label).


## 11. Restliche belegte Felder (zweiter Abgleich)

| Odoo 11 Feld (Modell) | Belegung | Behandlung |
|---|---|---|
| res.partner.commercial_company_name | 5727 | 1:1 |
| res.partner.partner_share | 5803 | 1:1 |
| res.partner.debit_limit (Kreditlimit) | 3365 | 1:1 |
| res.partner.latitude, longitude | 1531 | 1:1 |
| res.partner.calendar_last_notif_ack | 1734 | technisch, nicht migrieren |
| res.partner.austria_wiki_url | 1531 | ITK-Zusatz, 1:1 |
| res.partner.contract_ids, meeting_ids, opportunity_ids, sale_order_ids, task_ids, user_ids, ref_company_ids | 1-1118 | 1:1 ueber fachliche Schluessel (Verweise, keine IDs) |
| res.partner.signup_token, signup_type, signup_expiration | 33 / 1 | Portal-Anmeldung; in Odoo 18 neu erzeugt, nicht migrieren |
| res.partner.support_ticket_ids | 273 | Helpdesk-Verweis, liegt ausserhalb der Abrechnung, nicht migrieren |
| res.partner.title_put_in_front, title_put_in_back | 384 / 37 | 1:1 |
| product.template.subscription_template_id | 292 | 1:1 auf das Odoo-18-Abonnement (itk_subscription) |
| product.template.website_sequence, website_size_x, website_size_y | 649 (nur Standardwerte) | Website-Modul in Odoo 18 nicht installiert, nicht migrieren |

Damit sind alle belegten migrationsrelevanten Felder der geprueften Modelle dokumentiert
(273 belegte Felder, 0 offene Mappings nach dem zweiten Abgleich).



## 8. Offene Punkte

- Produktfilter aus ITK-Zusatzmodulen (Festpreis-/Meilenstein-/zeitbasierte Dienste, Service-Typen):
  Entscheidung offen (nachbauen oder nur Standardfilter angleichen).
- In Odoo 11 vorhandene, in Odoo 18 ohne direkte Entsprechung: Kostenstellen-Tags (durch
  Kostenstellenplaene ersetzt), interne Ueberweisungen als eigener Zahlungstyp,
  Zahlungsstatus "Gesendet" je Beleg, USt-Beschriftung "UID" (Widget-gesteuert).
- Hash-Sicherung und sequence_override_regex bleiben Schritte der echten Migration.
