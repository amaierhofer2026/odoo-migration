# Odoo 11 -> Odoo 18: Bereich Abrechnung, Teil 2 (Feldinventar Rechnung)

Stand: 30.09.2026, Session 122
Status: **FELDINVENTAR ABGESCHLOSSEN - nur Analyse, an Odoo 18 wurde nichts geaendert**

Vergleichsbasis: Odoo 11 Prod (`https://portal.it-kommunal.at`, DB `ITK_V1_a`) - ausschliesslich lesend.
Zielsystem: Odoo 18 lokal (`localhost:8069`) und VM `k001959vsx.ipax.at`, DB `odo18_test`.

Auftrag (Anna, 30.09.2026): Teil 2 nur analysieren und dokumentieren - vollstaendiger Vergleich `account.invoice` / `account.invoice.line` (Odoo 11) gegen `account.move` / `account.move.line` (Odoo 18), inklusive belegter Felder, Typen, Relationen, Zustaende und Zielzuordnung.

## 1. Methodik und Nachweise

```
scripts/analyse_abrechnung_teil2_felder.py    Feldmengen, Typen, Relationen, Nutzung
scripts/analyse_abrechnung_teil2_details.py  Beschriftungen, Pflicht/readonly, Auswahlwerte
scripts/baue_abrechnung_teil2_doku.py        erzeugt dieses Dokument aus den Messdaten
```

Zwei Quellen je Modell und Instanz (Muster Session 121): `ir.model.fields` (autoritative Feldliste mit `modules`, `required`, `readonly`, `store`, `related`) und `fields_get` (Anzeigebeschriftung und Auswahlwerte in `de_DE`).

Vollstaendigkeitskontrolle (Feldmengen gegeneinander geprueft):
- `account.invoice` gegen `account.move`: `ir.model.fields` gegen `fields_get` ohne Abweichung (O11 87 / 87 und O18 189 / 189).
- `account.invoice.line` gegen `account.move.line`: `ir.model.fields` gegen `fields_get` ohne Abweichung (O11 37 / 37 und O18 93 / 93).

Zaehlregeln (Odoo-11-Besonderheiten):
```
- Odoo 11 kennt in ir.model.fields kein 'computed'. Berechnete Felder werden an
  store=False erkannt, abgeleitete an related != False.
- Nutzungszahlen nur fuer gespeicherte, nicht abgeleitete Felder (search_count mit
  Domain (feld != False)). Bei berechneten Feldern steht 'berechnet' statt einer Zahl.
- Infrastrukturfelder (message_*, activity_*, website_*, access_*, create_*, write_*,
  display_name, id, portal_url) sind je Modell zu einer Zeile zusammengefasst.
```

## 2. Feldmengen

```
account.invoice        Odoo 11:  87 Felder | account.move         Odoo 18: 189 Felder | gemeinsam 50 | nur O11 37 | nur O18 139
account.invoice.line   Odoo 11:  37 Felder | account.move.line    Odoo 18:  93 Felder | gemeinsam 23 | nur O11 14 | nur O18  70
```

Zum Vergleich die Odoo-11-Nutzung: `account.invoice` 6.277 Datensaetze, `account.invoice.line` 10.031 Datensaetze. Odoo-18-Testbestand (keine Produktivdaten): lokal 37 Belege / 100 Buchungszeilen, VM 57 Belege - die Zielzahlen sind Testdaten, keine Datenlage.

### 2.1 Felder, die es nur in Odoo 11 gibt (account.invoice): 37

| Odoo-11-Feld | Beschriftung | Typ | Relation | belegt (Odoo 11) | Ziel in Odoo 18 | Einstufung |
|---|---|---|---|---|---|---|
| `account_id` | Konto | many2one | account.account | 6277 | - | entfaellt (Konto kommt in Odoo 18 aus Journal/Position) |
| `amount_total_company_signed` | Gesamt (in eigener Währung) | monetary | - | 6277 | amount_total_in_currency_signed | Transformation (umbenannt) |
| `cash_rounding_id` | Methode zur Bargeldrundung | many2one | account.cash.rounding | 0 | invoice_cash_rounding_id | Transformation (umbenannt) |
| `comment` | Weitere Informationen | text | - | 5973 | narration | Transformation (umbenannt) |
| `date_due` | Fälligkeit | date | - | 6268 | invoice_date_due | Transformation (umbenannt) |
| `date_invoice` | Rechnungsdatum | date | - | 6263 | invoice_date | Transformation (umbenannt) |
| `has_outstanding` | Offene Posten vorhanden | boolean | - | berechnet | invoice_has_outstanding | Transformation (umbenannt) |
| `incoterms_id` | Lieferbedingungen | many2one | stock.incoterms | 0 | invoice_incoterm_id | Transformation (umbenannt, aus sale_stock) |
| `move_id` | Buchungssatz | many2one | account.move | 6263 | - | entfaellt (Odoo 11: Verknuepfung Rechnung <-> Buchungssatz) |
| `move_name` | Buchungssatzname | char | - | 6263 | name | Transformation (aufgegangen in name) |
| `number` | Nummer | char | - | 6263 | name | Transformation (umbenannt) |
| `origin` | Referenzbeleg | char | - | 6140 | invoice_origin | Transformation (umbenannt) |
| `outstanding_credits_debits_widget` | Widget für offene Posten | text | - | berechnet | invoice_outstanding_credits_debits_widget | Transformation (umbenannt, Widget) |
| `payment_move_line_ids` | Zahlungsbuchungszeilen | many2many | account.move.line | 6223 | matched_payment_ids | Transformation (anderes Modell) |
| `payment_term_id` | Zahlungsbedingungen | many2one | account.payment.term | 5737 | invoice_payment_term_id | Transformation (umbenannt) |
| `payments_widget` | Zahlungs-Widget | text | - | berechnet | invoice_payments_widget | Transformation (umbenannt, Widget) |
| `reconciled` | Bezahlt/Abgestimmt | boolean | - | 6234 | has_reconciled_entries | Transformation (umbenannt, boolean) |
| `reference` | Lieferantenreferenz | char | - | 0 | ref | Transformation (umbenannt); in Odoo 11 ungenutzt (0) |
| `reference_type` | Zahlungsreferenz | selection | - | 6277 | - | obsolet (in Odoo 11 immer 'none') |
| `refund_invoice_id` | Rechnung, für welche diese Gutschrift ausgestellt wurde | many2one | account.invoice | 215 | reversed_entry_id | Transformation (umbenannt) |
| `refund_invoice_ids` | Rechnungen erstatten | one2many | account.invoice | 212 | reversal_move_ids | Transformation (umbenannt) |
| `residual` | Fälliger Betrag | monetary | - | 6277 | amount_residual | Transformation (umbenannt) |
| `residual_company_signed` | fälliger Betrag in Unternehmenswährung | monetary | - | 6277 | amount_residual_signed | Transformation (aufgegangen) |
| `residual_signed` | Fälliger Betrag in Rechnungswährung | monetary | - | 6277 | amount_residual_signed | Transformation (umbenannt) |
| `sent` | Gesendet | boolean | - | 2549 | is_move_sent | Transformation (umbenannt) |
| `sequence_number_next` | Nächste Nummer zuweisen | char | - | berechnet | sequence_number + highest_name | Transformation (Nummernkreis) |
| `sequence_number_next_prefix` | Nächste Nummer zuweisen | char | - | berechnet | sequence_prefix | Transformation (Nummernkreis) |
| `tax_line_ids` | Steuerbuchungen | one2many | account.invoice.tax | 6255 | line_ids (display_type = tax) | Transformation (eigenes Modell entfaellt) |
| `timesheet_count` | Anzahl der Stundenzettel | integer | - | berechnet | - | entfaellt (sale_timesheet in Odoo 11 ungenutzt, 0 Datensaetze) |
| `timesheet_ids` | Zeiterfassung | one2many | account.analytic.line | 0 | - | entfaellt (sale_timesheet in Odoo 11 ungenutzt, 0 Datensaetze) |
| `type` | Typ | selection | - | 6277 | move_type | Transformation (Auswahlwerte umbenannt) |

Standard-Infrastruktur (in Odoo 18 durch die Standardfelder ersetzt): `__last_update`, `message_channel_ids`, `message_last_post`, `message_unread`, `message_unread_counter`, `portal_url`

### 2.2 Felder, die es nur in Odoo 11 gibt (account.invoice.line): 14

| Odoo-11-Feld | Beschriftung | Typ | Relation | belegt (Odoo 11) | Ziel in Odoo 18 | Einstufung |
|---|---|---|---|---|---|---|
| `account_analytic_id` | Kostenstelle | many2one | account.analytic.account | 0 | analytic_distribution | Transformation (umbenannt); Odoo 11 ungenutzt (0) |
| `analytic_tag_ids` | Kostenstellen Tags | many2many | account.analytic.tag | 0 | - | entfaellt (Odoo 11: 0 Datensaetze; Odoo 18: Verteilungsschluessel) |
| `invoice_id` | Rechnungsreferenz | many2one | account.invoice | 10031 | move_id | Transformation (umbenannt) |
| `invoice_line_tax_ids` | Steuern | many2many | account.tax | 10009 | tax_ids | Transformation (umbenannt) |
| `invoice_type` | Typ | selection | - | berechnet | move_id.move_type | Transformation (auf Kopf verschoben) |
| `is_rounding_line` | Rundungsposition | boolean | - | 0 | display_type = rounding | Transformation (Auswahlwert) |
| `layout_category_id` | Sektion | many2one | sale.layout_category | 2 | - | kein Ziel (Odoo 18: display_type line_section/line_note) |
| `layout_category_sequence` | Reihenfolge Auftragszeilen | integer | - | 606 | - | kein Ziel (Abschnittsreihenfolge, nicht migrieren) |
| `origin` | Referenzbeleg | char | - | 2181 | ref | Transformation (umbenannt) |
| `price_subtotal_signed` | Betrag unterzeichnet | monetary | - | 10031 | - | entfaellt (Vorzeichen ergibt sich aus debit/credit) |
| `product_image` | Produktbild | binary | - | berechnet | - | entfaellt (Anzeigefeld) |
| `purchase_id` | Beschaffungsauftrag | many2one | purchase.order | berechnet | purchase_order_id | Transformation (umbenannt); Odoo 11 ungenutzt (0) |
| `uom_id` | Mengeneinheit | many2one | product.uom | 10029 | product_uom_id | Transformation (umbenannt) |

Standard-Infrastruktur (in Odoo 18 durch die Standardfelder ersetzt): `__last_update`

### 2.3 Felder, die es nur in Odoo 18 gibt (Zusatzfunktionen und Infrastruktur)

`account.move` 139, `account.move.line` 70 Felder. Die wichtigsten Gruppen:

- **Nummernkreis/Sequenz:** `sequence_prefix`, `sequence_number`, `highest_name`, `name_placeholder`, `made_sequence_gap`, `secure_sequence_number`, `inalterable_hash`, `restrict_mode_hash_table`, `posted_before`
- **Zahlungsstatus/Abstimmung:** `payment_state`, `amount_residual`, `amount_residual_signed`, `amount_paid`, `matched_payment_ids`, `reconciled_payment_ids`, `payment_count`, `needed_terms`, `payment_term_details`, `next_payment_date`, `preferred_payment_method_line_id`, `statement_line_id`, `statement_id`, `has_reconciled_entries`
- **Betraege/Waehrung:** `amount_residual`, `amount_tax_signed`, `amount_total_in_currency_signed`, `amount_untaxed_in_currency_signed`, `amount_total_words`, `invoice_currency_rate`, `expected_currency_rate`, `display_inactive_currency_warning`, `tax_totals`, `quick_edit_total_amount`
- **E-Rechnung/EDI (Zusatzfunktion):** `peppol_move_state`, `peppol_message_uuid`, `peppol_can_send_response`, `peppol_response_ids`, `ubl_cii_xml_id`, `ubl_cii_xml_file`, `invoice_pdf_report_id`, `invoice_pdf_report_file`, `invoice_source_email`, `can_send_as_self_invoice`, `qr_code_method`, `display_qr_code`
- **Pruefpfad/Audit (Zusatzfunktion):** `audit_trail_message_ids`, `inalterable_hash`, `secure_sequence_number`, `checked`, `is_manually_modified`
- **Automatik/Pruefungen:** `auto_post`, `auto_post_origin_id`, `auto_post_until`, `abnormal_amount_warning`, `abnormal_date_warning`, `duplicated_ref_ids`, `partner_credit`, `partner_credit_warning`, `show_name_warning`, `show_reset_to_draft_button`, `show_update_fpos`, `tax_lock_date_message`, `hide_post_button`
- **Belegarten/Positionen:** `line_ids`, `invoice_line_ids`, `attachment_ids`, `reversal_move_ids`, `reversed_entry_id`, `move_type`, `type_name`, `narration`, `journal_group_id`, `direction_sign`, `is_storno`
- **Sonstige Odoo-18-Felder:** `delivery_date`, `show_delivery_date`, `sale_order_count`, `purchase_order_count`, `transaction_count`, `transaction_ids`, `invoice_vendor_bill_id`, `purchase_vendor_bill_id`, `is_purchase_matched`, `taxes_legal_notes`, `bank_partner_id`, `country_code`, `tax_country_id`, `tax_country_code`, `tax_calculation_rounding_method`, `always_tax_exigible`, `company_price_include`, `quick_edit_mode`, `is_being_sent`, `sending_data`, `move_sent_values`, `activity_calendar_event_id`, `my_activity_date_deadline`, `suitable_journal_ids`, `invoice_filter_type_domain`, `invoice_partner_display_name`, `invoice_outstanding_credits_debits_widget`, `invoice_payments_widget`, `origin_payment_id`, `tax_cash_basis_created_move_ids`, `tax_cash_basis_origin_move_id`, `tax_cash_basis_rec_id`, `stock_move_id`, `stock_valuation_layer_ids`, `status_in_payment`, `restrict_mode_hash_table`, `attachment_ids`

Die uebrigen Felder sind Odoo-18-Standardinfrastruktur (mail/activity/portal/Berechtigungen) oder berechnete Anzeigefelder. Sie werden nicht entfernt.

## 3. Gemeinsame Felder mit Abweichungen

### account.invoice

Typ-/Relationsabweichungen (2):

| Feld | Odoo 11 | Odoo 18 | Bewertung |
|---|---|---|---|
| `invoice_line_ids` | one2many -> account.invoice.line | one2many -> account.move.line | Beziehung angepasst, Feld bleibt |
| `payment_ids` | many2many -> account.payment | one2many -> account.payment | Beziehung angepasst, Feld bleibt |

Beschriftungsunterschiede in de_DE (24, Auswahl):

| Feld | Odoo 11 | Odoo 18 |
|---|---|---|
| `access_token` | Security Token | Security-Token |
| `activity_state` | Bundesland | Status der Aktivität |
| `activity_summary` | Zusammenfassung nächste Aktion | Zusammenfassung der nächsten Aktivität |
| `activity_user_id` | Verantwortlich | Verantwortlicher Benutzer |
| `amount_total` | Total | Gesamt |
| `amount_total_signed` | Gesamtbetrag in Rechnungswährung | Ingesamt unterzeichnet |
| `amount_untaxed_signed` | Nettobetrag in Unternehmenswährung | Nettobetrag unterzeichnet |
| `commercial_partner_id` | Gewerbliche Einheit | Handelsgesellschaft |
| `company_currency_id` | Betriebl. Währung | Unternehmenswährung |
| `date` | Buchungsdatum | Datum |
| `fiscal_position_id` | Steuerzuordnung | Steuerposition |
| `message_follower_ids` | Abonnenten | Follower |
| `message_is_follower` | Ist ein Abonnent | Ist Follower |
| `message_partner_ids` | Abonnenten (Partner) | Follower (Partner) |
| `name` | Referenz/Beschreibung | Nummer |
| `partner_bank_id` | Bankkonto | Empfängerbank |
| `partner_id` | Partner | Kunde |
| `projectcategory_id` | Project Category | Projektkategorie |
| `purchase_id` | Beschaffungsauftrag hinzufügen | Bestellung |
| `source_id` | Referenz | Quelle |
| `team_id` | Vertriebskanal | Verkaufsteam |
| `user_id` | Verkäufer | Benutzer |
| `valorisierung_id` | Valorisation Text | Valorisierungstext |
| `write_uid` | Zuletzt aktualisiert durch | Zuletzt aktualisiert von |

### account.invoice.line

Typ-/Relationsabweichungen (1):

| Feld | Odoo 11 | Odoo 18 | Bewertung |
|---|---|---|---|
| `name` | text  | char  | Beziehung angepasst, Feld bleibt |

Beschriftungsunterschiede in de_DE (10, Auswahl):

| Feld | Odoo 11 | Odoo 18 |
|---|---|---|
| `company_currency_id` | Betriebl. Währung | Unternehmenswährung |
| `name` | Beschreibung | Buchungstext |
| `partner_id` | Partner | Kunde |
| `price_subtotal` | Betrag | Zwischensumme |
| `price_total` | Betrag | Gesamt |
| `price_unit` | Preis pro ME | Einzelpreis |
| `purchase_line_id` | Bestellposition | Bestellzeile |
| `sale_line_ids` | Verkaufsauftragpositionen | Verkaufsauftragszeilen |
| `sequence` | Nummernfolge | Sequenz |
| `write_uid` | Zuletzt aktualisiert durch | Zuletzt aktualisiert von |

## 4. Pflichtfelder, readonly, berechnete Felder

```
account.invoice / account.move
  Pflicht Odoo 11:            ['account_id', 'company_id', 'currency_id', 'journal_id', 'partner_id', 'reference_type']
  Pflicht Odoo 18:            ['auto_post', 'currency_id', 'date', 'journal_id', 'move_type', 'state']
  in Odoo 18 zusaetzlich:     ['auto_post', 'date', 'move_type', 'state']
  nicht mehr pflichtig:       ['account_id', 'company_id', 'partner_id', 'reference_type']
  berechnet (store=False):    Odoo 11 21 | Odoo 18 90

account.invoice.line / account.move.line
  Pflicht Odoo 11:            ['account_id', 'name', 'price_unit', 'quantity']
  Pflicht Odoo 18:            ['currency_id', 'display_type', 'move_id']
  in Odoo 18 zusaetzlich:     ['currency_id', 'display_type', 'move_id']
  nicht mehr pflichtig:       ['account_id', 'name', 'price_unit', 'quantity']
  berechnet (store=False):    Odoo 11 6 | Odoo 18 29

```

Bewertung: Die Pflichtfelder verschieben sich von fachlichen Feldern (`partner_id`, `account_id`, `reference_type`) auf technische Felder (`move_type`, `state`, `date`, `auto_post`, `display_type`, `move_id`). Fuer die Migration heisst das: diese technischen Felder muessen beim Import gesetzt werden, die alten Pflichtfelder sind es nicht mehr.

## 5. Zustaende und Auswahlwerte

```
account.invoice.state        Odoo 11: draft Entwurf | open Offen | paid Bezahlt | cancel Abgebrochen
account.move.state           Odoo 18: draft Entwurf | posted Gebucht | cancel Abgebrochen
account.move.payment_state   Odoo 18: not_paid | in_payment | paid | partial | reversed | blocked | invoicing_legacy
account.invoice.type         Odoo 11: out_invoice | in_invoice | out_refund | in_refund
account.move.move_type       Odoo 18: entry | out_invoice | out_refund | in_invoice | in_refund | out_receipt | in_receipt
account.move.line.display_type Odoo 18: product | cogs | tax | discount | rounding | payment_term | line_section | line_note | epd
account.invoice.line.invoice_type  Odoo 11: wie type (auf der Zeile wiederholt)
account.invoice.reference_type     Odoo 11: nur 'none' belegt
```

Wichtig fuer die Migration: Odoo 11 fuehrt den Zahlungszustand im Feld `state` (`open`/`paid`), Odoo 18 trennt Buchungszustand (`state`) und Zahlungszustand (`payment_state`). Gemessene Verteilung in Odoo 11: draft 14, open 43, paid 6.220, cancel 0. Der Zustand `open` (43 Belege) ist der einzige Wert ohne direkte Entsprechung und wird in der Migrationsregel auf `posted` + `payment_state` abgebildet (Teil 5).

## 6. Belegte Datensaetze in Odoo 11 (vollstaendig)

### account.invoice (Grundgesamtheit 6.277)

| Feld | Beschriftung | Typ | Relation | Pflicht | readonly | belegt |
|---|---|---|---|---|---|---|
| `account_id` | Konto | many2one | account.account | ja | ja | 6277 |
| `amount_tax` | Steuer | monetary | - | - | ja | 6277 |
| `amount_total` | Total | monetary | - | - | ja | 6277 |
| `amount_total_company_signed` | Gesamt (in eigener Währung) | monetary | - | - | ja | 6277 |
| `amount_total_signed` | Gesamtbetrag in Rechnungswährung | monetary | - | - | ja | 6277 |
| `amount_untaxed` | Nettobetrag | monetary | - | - | ja | 6277 |
| `amount_untaxed_signed` | Nettobetrag in Unternehmenswährung | monetary | - | - | ja | 6277 |
| `campaign_id` | Kampagne | many2one | utm.campaign | - | - | 0 |
| `cash_rounding_id` | Methode zur Bargeldrundung | many2one | account.cash.rounding | - | ja | 0 |
| `comment` | Weitere Informationen | text | - | - | ja | 5973 |
| `commercial_partner_id` | Gewerbliche Einheit | many2one | res.partner | - | ja | 6277 (abgeleitet: partner_id.commercial_partner_id) |
| `company_id` | Unternehmen | many2one | res.company | ja | ja | 6277 |
| `currency_id` | Währung | many2one | res.currency | ja | ja | 6277 |
| `date` | Buchungsdatum | date | - | - | ja | 6263 |
| `date_due` | Fälligkeit | date | - | - | ja | 6268 |
| `date_invoice` | Rechnungsdatum | date | - | - | ja | 6263 |
| `fiscal_position_id` | Steuerzuordnung | many2one | account.fiscal.position | - | ja | 4 |
| `incoterms_id` | Lieferbedingungen | many2one | stock.incoterms | - | ja | 0 |
| `invoice_line_ids` | Rechnungszeilen | one2many | account.invoice.line | - | ja | 6277 |
| `journal_id` | Journal | many2one | account.journal | ja | ja | 6277 |
| `medium_id` | Medium | many2one | utm.medium | - | - | 0 |
| `move_id` | Buchungssatz | many2one | account.move | - | ja | 6263 |
| `move_name` | Buchungssatzname | char | - | - | - | 6263 |
| `name` | Referenz/Beschreibung | char | - | - | ja | 1418 |
| `notice` | Rechnungsnotiz | text | - | - | - | 519 |
| `number` | Nummer | char | - | - | ja | 6263 (abgeleitet: move_id.name) |
| `origin` | Referenzbeleg | char | - | - | ja | 6140 |
| `partner_bank_id` | Bankkonto | many2one | res.partner.bank | - | ja | 120 |
| `partner_id` | Partner | many2one | res.partner | ja | ja | 6277 |
| `partner_shipping_id` | Lieferadresse | many2one | res.partner | - | ja | 6277 |
| `payment_ids` | Zahlungen | many2many | account.payment | - | ja | 5996 |
| `payment_move_line_ids` | Zahlungsbuchungszeilen | many2many | account.move.line | - | ja | 6223 |
| `payment_term_id` | Zahlungsbedingungen | many2one | account.payment.term | - | ja | 5737 |
| `projectcategory_id` | Project Category | many2one | itk_projectcategory.projectcategory | - | - | 5254 |
| `purchase_id` | Beschaffungsauftrag hinzufügen | many2one | purchase.order | - | ja | 0 |
| `reconciled` | Bezahlt/Abgestimmt | boolean | - | - | ja | 6234 |
| `reference` | Lieferantenreferenz | char | - | - | ja | 0 |
| `reference_type` | Zahlungsreferenz | selection | - | ja | ja | 6277 |
| `refund_invoice_id` | Rechnung, für welche diese Gutschrift ausgestellt wurde | many2one | account.invoice | - | - | 215 |
| `refund_invoice_ids` | Rechnungen erstatten | one2many | account.invoice | - | ja | 212 |
| `residual` | Fälliger Betrag | monetary | - | - | ja | 6277 |
| `residual_company_signed` | fälliger Betrag in Unternehmenswährung | monetary | - | - | ja | 6277 |
| `residual_signed` | Fälliger Betrag in Rechnungswährung | monetary | - | - | ja | 6277 |
| `sale_order_benefit_period` | Leistungszeitraum | text | - | - | - | 5801 |
| `sale_order_confirmation_date` | Datum Auftragsbestätigung | date | - | - | - | 4602 |
| `sent` | Gesendet | boolean | - | - | ja | 2549 |
| `source_id` | Referenz | many2one | utm.source | - | - | 0 |
| `state` | Status | selection | - | - | ja | 6277 |
| `tax_line_ids` | Steuerbuchungen | one2many | account.invoice.tax | - | ja | 6255 |
| `team_id` | Vertriebskanal | many2one | crm.team | - | - | 6277 |
| `timesheet_ids` | Zeiterfassung | one2many | account.analytic.line | - | ja | 0 |
| `type` | Typ | selection | - | - | ja | 6277 |
| `user_id` | Verkäufer | many2one | res.users | - | ja | 6277 |
| `valorisierung_id` | Valorisation Text | many2one | itk_valorisierung.valorisierung | - | - | 4216 |

### account.invoice.line (Grundgesamtheit 10.031)

| Feld | Beschriftung | Typ | Relation | Pflicht | readonly | belegt |
|---|---|---|---|---|---|---|
| `account_analytic_id` | Kostenstelle | many2one | account.analytic.account | - | - | 0 |
| `account_id` | Konto | many2one | account.account | ja | - | 10031 |
| `analytic_tag_ids` | Kostenstellen Tags | many2many | account.analytic.tag | - | - | 0 |
| `company_id` | Unternehmen | many2one | res.company | - | ja | 10031 (abgeleitet: invoice_id.company_id) |
| `currency_id` | Währung | many2one | res.currency | - | ja | 10031 (abgeleitet: invoice_id.currency_id) |
| `discount` | Rabatt (%) | float | - | - | - | 10031 |
| `invoice_id` | Rechnungsreferenz | many2one | account.invoice | - | - | 10031 |
| `invoice_line_tax_ids` | Steuern | many2many | account.tax | - | - | 10009 |
| `is_rounding_line` | Rundungsposition | boolean | - | - | - | 0 |
| `layout_category_id` | Sektion | many2one | sale.layout_category | - | - | 2 |
| `layout_category_sequence` | Reihenfolge Auftragszeilen | integer | - | - | - | 606 |
| `name` | Beschreibung | text | - | ja | - | 10031 |
| `number` | Nummer | integer | - | - | ja | 10031 |
| `origin` | Referenzbeleg | char | - | - | - | 2181 |
| `partner_id` | Partner | many2one | res.partner | - | ja | 10031 (abgeleitet: invoice_id.partner_id) |
| `price_subtotal` | Betrag | monetary | - | - | ja | 10031 |
| `price_subtotal_signed` | Betrag unterzeichnet | monetary | - | - | ja | 10031 |
| `price_total` | Betrag | monetary | - | - | ja | 10031 |
| `price_unit` | Preis pro ME | float | - | ja | - | 10031 |
| `product_id` | Produkt | many2one | product.product | - | - | 10030 |
| `purchase_line_id` | Bestellposition | many2one | purchase.order.line | - | ja | 0 |
| `quantity` | Menge | float | - | ja | - | 10031 |
| `sale_line_ids` | Verkaufsauftragpositionen | many2many | sale.order.line | - | ja | 1863 |
| `sequence` | Nummernfolge | integer | - | - | - | 10031 |
| `subscription_id` | Aboauftrag | many2one | sale.subscription | - | - | 8099 |
| `uom_id` | Mengeneinheit | many2one | product.uom | - | - | 10029 |

## 7. ITK- und Drittmodul-Felder (Herkunft)

```
Odoo 11 account.invoice:
  campaign_id                    aus utm
  incoterms_id                   aus sale_stock
  medium_id                      aus utm
  notice                         aus itk_subscription
  portal_url                     aus portal
  projectcategory_id             aus itk_projectcategory
  sale_order_benefit_period      aus itk_subscription
  sale_order_confirmation_date   aus itk_subscription
  source_id                      aus utm
  timesheet_count                aus sale_timesheet
  timesheet_ids                  aus sale_timesheet
  valorisierung_id               aus itk_valorisierung
  website_message_ids            aus portal
Odoo 11 account.invoice.line:
  subscription_id                aus itk_subscription
Odoo 18 account.move:
  notice                         aus itk_subscription
  peppol_can_send_response       aus account_peppol_response
  peppol_move_state              aus account_peppol, account_peppol_response
  peppol_response_ids            aus account_peppol_response
  projectcategory_id             aus itk_projectcategory
  sale_order_benefit_period      aus itk_subscription
  sale_order_confirmation_date   aus itk_subscription
  valorisierung_id               aus itk_valorisierung
Odoo 18 account.move.line:
  is_downpayment                 aus purchase, sale
  subscription_id                aus itk_subscription
```

Ergebnis: Die ITK-Felder der Rechnung sind in Odoo 18 vorhanden - `valorisierung_id` (itk_valorisierung), `projectcategory_id` (itk_projectcategory), `notice`, `sale_order_benefit_period`, `sale_order_confirmation_date` (itk_subscription). Aus Odoo 11 entfallen die Felder des nie genutzten `sale_timesheet` (`timesheet_ids`, `timesheet_count`, je 0 Datensaetze) sowie die UTM-Felder des Rechnungskopfs (`campaign_id`, `medium_id`, `source_id`, alle 0 Datensaetze).

## 8. Auftrag K2: historische Rechnungsnummern in Odoo 18 (technisch geprueft)

Auftrag Anna (30.09.2026): pruefen, wie die historischen Rechnungsnummern in Odoo 18 korrekt und eindeutig erhalten bzw. nachvollziehbar zugeordnet werden koennen. Es wurde **nichts** umnummeriert und **nichts** geschrieben.

### 8.1 Messwerte Odoo 11

```
6.277 Rechnungen, davon 6.263 mit Nummer (14 Entwuerfe ohne Nummer)
alle Nummern im EINEN Journal "Ausgangsrechnungen (EUR)" (id 1), Praefix immer 'R-'
Formatwechsel: 2019 R-1900001 bis R-19578 (Jahr + 5 Stellen),
               2020-2026 R-20001 ... R-26989 (Jahr + 3 Stellen)
Eindeutigkeit in Odoo 11: SQL-Constraint account_invoice_number_uniq
  = unique(number, company_id, journal_id, type)
Befund: genau EINE Nummer doppelt im selben Journal, weil sie einmal fuer eine
  Rechnung und einmal fuer eine Gutschrift verwendet wurde:
  R-25001 = id 9703 (out_invoice, 02.01.2025, Magistrat der Stadt Wels, 27.593,52)
          = id 11531 (out_refund, 06.02.2025, Verein Gesundheitsland Kaernten,
            1.474,76, Ursprung R-25584)
  In Odoo 11 erlaubt, weil 'type' Teil des eindeutigen Schluessels war.
237 Kunden-Gutschriften liegen im selben Journal wie die Rechnungen.
```

### 8.2 Technische Lage in Odoo 18 (Quellcode und Datenbank geprueft, read-only)

```
1) Feld 'name' ist beschreibbar: account.move.name ist compute + inverse +
   readonly=False + store=True (account/models/account_move.py, Zeile 128).
   Eine Migration KANN die historische Nummer also direkt setzen.
2) Eindeutigkeit: UNIQUE INDEX account_move_unique_name
   ON account_move (name, journal_id) WHERE state = 'posted' AND name <> '/'
   Fehlermeldung: "Ein anderer Datensatz mit demselben Namen existiert bereits."
   => Nummern muessen je Journal eindeutig sein, ABER anders als in Odoo 11 zaehlt
      'type' nicht mit. Die eine Doppelnummer R-25001 wuerde den Import daher
      abbrechen (Klärung K2a).
3) Nummernvergabe setzt auf der hoechsten vorhandenen Nummer auf:
   _set_next_sequence() -> _get_next_sequence_format() -> _get_last_sequence()
   liest die letzte Nummer desselben Journals (name != '/') und leitet das Format
   ueber _get_sequence_format_param() ab. Sind die historischen Nummern einmal
   importiert, fuehrt Odoo 18 die Zaehlung im GLEICHEN Format fort (R-26990 ...),
   ohne dass eine Sequenz von Hand gepflegt werden muss.
4) Nur beim Posten wird automatisch nummeriert; ein bereits gesetzter Name bleibt
   erhalten (_get_last_sequence_domain schliesst Zeilen mit name = '/' aus).
5) Achtung beim Import: wird 'journal_id' geaendert und 'name' NICHT mitgeschrieben,
   setzt Odoo den Namen zurueck (account_move.py: draft_move.name = False).
   Journal und Nummer daher immer im selben Schreibvorgang setzen.
6) Journal-Felder fuer den Nummernkreis: sequence_override_regex, refund_sequence
   ("Gesonderter Nummerkreis fuer Gutschriften"), payment_sequence, code.
7) Pruefpfad/Audit (Buchungen festschreiben): secure_sequence_number,
   inalterable_hash, restrict_mode_hash_table, check_move_sequence_chain().
   Ist der Pruefpfad aktiv, sind Nummern gebuchter Belege nicht mehr aenderbar -
   die Entscheidung ueber die Nummernvergabe muss VOR der Migration fallen.
```

### 8.3 Empfehlung (Entscheidung offen, nichts umgesetzt)

```
a) Historische Nummern 1:1 als account.move.name importieren und posten ->
   Nummern bleiben erhalten, Odoo 18 zaehlt im Format R-xxxxx weiter.
   Voraussetzung: die eine Doppelnummer R-25001 wird vorher geregelt.
b) Fuer die Doppelnummer gibt es drei Moeglichkeiten (Entscheidung Anna):
   b1) Gutschrift behaelt R-25001, Rechnung bekommt eine dokumentierte Ersatznummer
       (Original in ref oder payment_reference) - Achtung: Nummernkreis- und
       Rechnungslegungslogik, daher nur nach fachlicher Freigabe.
   b2) Rechnung behaelt R-25001, Gutschrift bekommt eine Ersatznummer.
   b3) Beide behalten die Nummer; das geht nur mit getrennten Journalen (dann greift
       der UNIQUE INDEX je Journal) - wuerde aber die Journalstruktur veraendern.
c) Nicht empfohlen: Odoo-Nummern neu vergeben und die historische Nummer nur in 'ref'
   ablegen (Wunsch war: Nummern eindeutig erhalten).
d) Vor der Migration technisch pruefen (Testlauf in einer Kopie, kein Produktivsystem):
   6.263 Belege mit Nummer importieren, 0 Konflikte ausser R-25001 erwartet.
```

## 9. Bewertung und offene Punkte

```
Vollstaendigkeit: Jedes tatsaechlich belegte Odoo-11-Feld der Rechnung und der
  Rechnungszeile hat ein Ziel in Odoo 18 - entweder unter demselben Namen, als
  umbenanntes Standardfeld, als berechnetes Feld oder als bewusst entfallendes Feld
  mit Begruendung. Kein belegtes Feld bleibt ohne Zuordnung.
ITK-Felder: valorisierung_id, projectcategory_id, notice, sale_order_benefit_period,
  sale_order_confirmation_date und subscription_id sind in Odoo 18 vorhanden.
Entfallen (jeweils 0 belegte Datensaetze in Odoo 11): timesheet_ids/timesheet_count
  (sale_timesheet), campaign_id/medium_id/source_id (UTM), reference_type (immer
  'none'), analytic_tag_ids, account_analytic_id, purchase_id, incoterms_id und
  cash_rounding_id (beide 0).
Kein Ziel (bewusst, wie im Verkauf R7): layout_category_id und
  layout_category_sequence der Rechnungszeile. Gemessen: genau 2 von 10.031 Zeilen
  mit Abschnittskategorie, 606 Zeilen mit einer Abschnittsreihenfolge ungleich 0.
  Odoo 18 bildet Abschnitte ueber display_type = line_section/line_note ab; es
  werden keine kuenstlichen Abschnittszeilen angelegt.
Ungenutzt in Odoo 11, aber strukturell vorhanden: incoterms_id, cash_rounding_id,
  purchase_id, timesheet_*, layout_category_id.
```

Offene Punkte aus Teil 2 (Entscheidung Anna, nichts umgesetzt):

```
K2a Doppelnummer R-25001 (Rechnung und Gutschrift, 2025) - Regelung noetig, sonst
     bricht der Import an dieser einen Stelle ab (Abschnitt 8.3 b1/b2/b3).
K2b Nummernformat: 2019 mit 5 Stellen (R-1900001), ab 2020 mit 3 Stellen (R-20001).
     Fortsetzung ab der hoechsten Nummer moeglich; Frage: welches Format soll
     weiterlaufen (Vorschlag: das Format des letzten Jahres).
K2c Pruefpfad/Audit (Buchungen festschreiben): vor der Migration entscheiden, ob er
     aktiviert wird - danach sind Nummern gebuchter Belege unveraenderlich.
K5  Steuern: Das Steuer-Mapping (77 gegen 53) wird im Stammdatenteil (Teil 5)
     vorbereitet; das Feldinventar ist damit abgeschlossen.
K9  USD: 4 Rechnungen mit USD (F4) sind betroffen; Feld currency_id ist in beiden
     Systemen vorhanden, unveraendert offener Pruefpunkt.
```

## 10. Rahmenbedingungen und Nachweise

```
Keine Aenderung an Odoo 18: kein Upgrade, kein Neustart, kein Schreibvorgang;
  alle Messungen per search_read/search_count/fields_get/ir.model.constraint
  sowie Quellcode-Lesen im Container (docker exec ... sed/grep, read-only).
Odoo 11 Prod ausschliesslich read-only.
Keine Datenmigration: 0 Datensaetze uebernommen, keine Nummer geaendert.
Rohdaten (Feldinventar-JSON) liegen nur im Temp-Verzeichnis, nicht im Repo.
Lokal und VM: Account-Module identisch; das Feldinventar wurde lokal gemessen und
  ueber die im Teil 1 geprueften identischen Modulversionen auf die VM bezogen.
```

## 11. Naechster Schritt (Vorschlag)

```
Teil 3: Formulare, Reiter, Buttons, Smart Buttons und Zustandswechsel der Rechnung
  im echten Browser (lokal und auf der VM), inklusive Zahlungs- und Abstimmungslogik
  sowie Rechnungsdruck/Versand. Vor Teil 3 werden die Entscheidungen zu K1, K3, K4
  und K6 sowie zu K2a/K2b aus diesem Teil erbeten.
```

## 12. Nachtrag 30.09.2026: Messkorrektur zum Nummernkreis und K2-Klaerung

```
Messkorrektur (datiert, alte Zeile bleibt stehen): In Abschnitt 8.1 stand
  "2026: kleinste R-26001, groesste R-26989". Die Angabe entstand durch alphabetische
  Sortierung und ist falsch. Numerisch ausgewertet ist die hoechste Nummer 2026 = R-261139
  (1.139 Rechnungen; die laufende Nummer wechselt bei Ueberschreitung von 999 in die
  Vierstelligkeit: R-26989 -> R-260990 ... R-260999 -> R-261000 ... R-261139).
  Der Aufbau "R-" + zweistelliges Jahr + laufende Nummer bleibt unveraendert.
K2 vollstaendig geklaert: eigenes Dokument docs/o11-o18-vergleich-abrechnung-k2-nummern.md
  mit K2a (Loesungswege fuer die Doppelnummer R-25001 samt Vorschlag fuer ein Feld
  "Odoo-11-Rechnungsnummer"), K2b (nachgerechnetes Weiterzaehlen: ohne Zusatzkonfiguration
  wuerde Odoo 18 bei R-1900003 weiterlaufen, mit sequence_override_regex je Jahr korrekt
  bei R-261140 bzw. R-2700001) und K2c (Hash-Sicherung je Journal schuetzt genau die Felder
  name/date/journal_id/company_id; Loesch- und Schreibsperren; Pruefpfad).
  Es wurde nichts migriert, keine Nummer geaendert, kein Schreibvorgang ausgefuehrt.
```

## 13. Nachtrag 30.09.2026: Zielfeld fuer das Odoo-11-Feld `name` (Befund B2, Gutschrift)

```
Befund aus B2 (docs/o11-o18-vergleich-abrechnung-b2-gutschrift.md, Abschnitt 6, Punkt U3):
Das Odoo-11-Feld `name` (Beschriftung "Referenz/Beschreibung") ist ein Freitextfeld und in
1.418 Belegen belegt, davon 215 Gutschriften mit der Begruendung aus dem Gutschrift-Assistenten
(z. B. "irrtuemlich ausgestellt", "falsch fakturiert").
In Odoo 18 traegt `name` die Belegnummer; ein gleichnamiges Zielfeld gibt es nicht. In der
Zuordnungstabelle (Abschnitt 2.1) war fuer dieses Feld daher kein Ziel definiert.
Entscheidung von Anna (30.09.2026): den historischen Grund erhalten und fachlich korrekt in
Odoo 18 abbilden, ohne ungenutzte Odoo-11-Felder zu rekonstruieren.
Zuordnungsregel (Migration, noch nicht ausgefuehrt):
  - Bei Belegen mit Gutschriftsbezug (refund_invoice_id gesetzt): `ref` nach Odoo-18-Muster
    bilden ("Stornierung von: <alte Nummer der Rechnung>, <alter Grund>"); der Grund bleibt
    zusaetzlich in der mitmigrierten Chatter-Nachricht "Gutschrift" erhalten.
  - Bei den uebrigen Belegen mit gefuelltem `name` (1.203): Inhalt als Buchungstext/Ursprung
    dokumentieren und zusammen mit der Regel fuer das Feld "Odoo-11-Rechnungsnummer" (K2a) in
    Teil 5 festlegen; nichts loeschen, nichts umdeuten.
  - Das Feld `reference` der Altdaten (0 Belege) wird nicht migriert.
```
