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
in Odoo 11 und prueft, ob sie in dieser Doku bzw. in Teil 5 Feldabbildung enthalten sind).
Ergebnis wird hier ergaenzt, sobald der Lauf gegen die Produktionsdatenbank abgeschlossen ist.

## 8. Offene Punkte

- Produktfilter aus ITK-Zusatzmodulen (Festpreis-/Meilenstein-/zeitbasierte Dienste, Service-Typen):
  Entscheidung offen (nachbauen oder nur Standardfilter angleichen).
- In Odoo 11 vorhandene, in Odoo 18 ohne direkte Entsprechung: Kostenstellen-Tags (durch
  Kostenstellenplaene ersetzt), interne Ueberweisungen als eigener Zahlungstyp,
  Zahlungsstatus "Gesendet" je Beleg, USt-Beschriftung "UID" (Widget-gesteuert).
- Hash-Sicherung und sequence_override_regex bleiben Schritte der echten Migration.
