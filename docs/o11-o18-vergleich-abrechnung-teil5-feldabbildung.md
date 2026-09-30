# Odoo 11 gegen Odoo 18 - Bereich Abrechnung, Teil 5: Feldabbildung und Migrationsregeln

Stand: 30.09.2026, Session 122. **Reine Vorbereitung: es wurde nichts migriert.**
Odoo 11 wurde ausschliesslich lesend verwendet, Aenderungen nur in Odoo 18.

Erzeugt von `scripts/baue_abrechnung_teil5_doku.py` (Messdaten live aus beiden Systemen,
Regelspalten aus der Regel-Tabelle im Skript). Bezeichnungen entsprechen dem Stand nach dem
Label-Abgleich (Teil 4 + Label-Regel).

## 1. Feldabbildung (je tatsaechlich relevantem Odoo-11-Feld)

| Odoo-11-Modell.Feld | Odoo-11-Bezeichnung | Odoo-18-Zielmodell.Feld | Odoo-18-Bezeichnung | Zuordnung / Transformationsregel | Stammdaten / Modulabhaengigkeit | Odoo 11 | Odoo 18 | migriert oder neu berechnet | Validierung nach der Migration |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `account.invoice.amount_tax` | Steuer | `account.move.amount_tax` | Steuer | 1:1 Betrag (Kontrolle gegen Steuerzeilen) | Steuern (K5) | gespeichert (monetary) | gespeichert (monetary) | migriert und geprueft | Steuerbetrag stimmt mit den Steuerzeilen ueberein |
| `account.invoice.amount_total` | Total | `account.move.amount_total` | Total | 1:1 Betrag | Steuern (K5) | gespeichert (monetary) | gespeichert (monetary) | migriert und geprueft | Bruttobetrag = Netto + Steuer |
| `account.invoice.amount_untaxed` | Nettobetrag | `account.move.amount_untaxed` | Nettobetrag | 1:1 Betrag (Kontrolle gegen Zeilensummen) | Steuern (K5) | gespeichert (monetary) | gespeichert (monetary) | migriert und beim Import gegen die Zeilen geprueft | Nettobetrag stimmt mit Zeilensummen ueberein |
| `account.invoice.cash_rounding_id` | Methode zur Bargeldrundung | `account.move.invoice_cash_rounding_id` | Methode zur Bargeldrundung | kein Altdatenbezug (0 Belege) | - | gespeichert (many2one) | gespeichert (many2one) | neu | leer zulaessig |
| `account.invoice.comment` | Weitere Informationen | `account.move.narration` | Weitere Informationen | 1:1 (Text/HTML-sicher) | - | gespeichert (text) | gespeichert (html) | migriert | Text uebernommen, keine Umformatierung |
| `account.invoice.currency_id` | Währung | `account.move.currency_id` | Währung | 1:1 (EUR) | res.currency | gespeichert (many2one) | gespeichert (many2one) | migriert | Waehrung EUR; USD-Sonderfaelle (4 Belege, K9) gesondert pruefen |
| `account.invoice.date` | Buchungsdatum | `account.move.date` | Buchungsdatum | 1:1 (Datum) | - | gespeichert (date) | gespeichert (date) | migriert | Buchungsdatum gesetzt; in abgeschlossenen Perioden gesperrt |
| `account.invoice.date_due` | Fälligkeit | `account.move.invoice_date_due` | Fälligkeit | 1:1 (Datum) | account.payment.term (nur zur Kontrolle) | gespeichert (date) | gespeichert (date) | migriert | Faelligkeit >= Rechnungsdatum |
| `account.invoice.date_invoice` | Rechnungsdatum | `account.move.invoice_date` | Rechnungsdatum | 1:1 (Datum) | - | gespeichert (date) | gespeichert (date) | migriert | Rechnungsdatum gesetzt, nicht leer |
| `account.invoice.fiscal_position_id` | Steuerzuordnung | `account.move.fiscal_position_id` | Steuerzuordnung | Zuordnung ueber Steuerzuordnung | account.fiscal.position | gespeichert (many2one) | gespeichert (many2one) | migriert | nur wenn Odoo 11 gesetzt (0 Belege) |
| `account.invoice.incoterms_id` | Lieferbedingungen | `account.move.invoice_incoterm_id` | Lieferbedingungen | kein Altdatenbezug (0 Belege) | sale_stock | gespeichert (many2one) | gespeichert (many2one) | neu | leer zulaessig |
| `account.invoice.journal_id` | Journal | `account.move.journal_id` | Journal | Zuordnung ueber Journal-Code (Odoo 11 'Re.' -> Odoo 18 'RE') | account.journal (Stammdaten, Migration) | gespeichert (many2one) | gespeichert (many2one) | migriert | jede Rechnung hat ein Verkaufsjournal |
| `account.invoice.move_name` | Buchungssatzname | `account.move.name` | Nummer | aufgegangen in die Belegnummer, keine eigene Migration | - | gespeichert (char) | gespeichert (char) | entfaellt | - |
| `account.invoice.name` | Referenz/Beschreibung | `account.move.ref (Text) + Chatter` | - | Transformation: Inhalt ist der Gutschrifts-/Beschreibungsgrund und wird bei Gutschriften in ref geschrieben ('Stornierung von: <alte Nummer>, <Grund>'), zusaetzlich bleibt die Chatter-Nachricht erhalten | - | gespeichert (char) | berechnet (-) | migriert (Regel) | 215 Gutschriften mit Grund nachvollziehbar; 1.203 weitere Belege mit Beschreibung dokumentiert uebernehmen |
| `account.invoice.notice` | Rechnungsnotiz | `account.move.notice` | Rechnungsnotiz | 1:1 (ITK-Feld Rechnungsnotiz) | itk-Modul (Feld vorhanden) | gespeichert (text) | gespeichert (text) | migriert | Text uebernommen |
| `account.invoice.number` | Nummer | `account.move.name` | Nummer | 1:1 (Belegnummer unveraendert uebernehmen; Nummer wird beim Import gesetzt, nicht neu erzeugt) | Journal + Sequenz (K2b) | gespeichert (char) | gespeichert (char) | migriert | Nummer eindeutig je Journal; Kontrolle gegen K2a-Ausnahmefall R-25001 |
| `account.invoice.origin` | Referenzbeleg | `account.move.invoice_origin` | Referenzbeleg | 1:1 (Text) | - | gespeichert (char) | gespeichert (char) | migriert | Feld uebernommen (2.137 Belege ungenutzt/leer zulaessig) |
| `account.invoice.partner_bank_id` | Bankkonto | `account.move.partner_bank_id` | Bankkonto | Zuordnung ueber Bankverbindung | res.partner.bank | gespeichert (many2one) | gespeichert (many2one) | migriert | Bankkonto vorhanden oder leer |
| `account.invoice.partner_id` | Partner | `account.move.partner_id` | Partner | 1:1 (Partner ueber Name/ID des Altsystems, Abgleich ueber res.partner-Referenz) | res.partner | gespeichert (many2one) | gespeichert (many2one) | migriert | Kunde vorhanden und Rechnung zugeordnet; keine Rechnung ohne Partner |
| `account.invoice.payment_move_line_ids` | Zahlungsbuchungszeilen | `account.move.matched_payment_ids` | Zahlungsbuchungszeilen | anderes Modell, ueber Abstimmungen abgeleitet | - | gespeichert (many2many) | gespeichert (many2many) | neu berechnet | Zahlungen den richtigen Rechnungen zugeordnet |
| `account.invoice.payment_reference` | - | `account.move.payment_reference` | Zahlungsreferenz | kein Altdatenbezug (in Odoo 11 nicht vorhanden) | - | berechnet (-) | gespeichert (char) | neu | leer zulaessig |
| `account.invoice.payment_term_id` | Zahlungsbedingungen | `account.move.invoice_payment_term_id` | Zahlungsbedingungen | Zuordnung ueber Bezeichnung der Zahlungsbedingung | account.payment.term (Stammdaten, Migration) | gespeichert (many2one) | gespeichert (many2one) | migriert | Zahlungsbedingung vorhanden; Faelligkeit passt dazu |
| `account.invoice.projectcategory_id` | Project Category | `account.move.projectcategory_id` | Project Category | Zuordnung ueber Projektkategorie (Satzart/Code) | itk_projectcategory (Stammdaten) | gespeichert (many2one) | gespeichert (many2one) | migriert | Kategorie vorhanden; 5.254 Belege |
| `account.invoice.reconciled` | Bezahlt/Abgestimmt | `account.move.has_reconciled_entries` | Bezahlt/Abgestimmt | berechnet | - | gespeichert (boolean) | berechnet (boolean) | neu berechnet | nur abgestimmte Belege true |
| `account.invoice.reference` | Lieferantenreferenz | `account.move.ref` | Referenz | keine Migration (Feld in Odoo 11 nie belegt); ref wird bei Gutschriften nach Odoo-18-Muster gebildet | - | gespeichert (char) | gespeichert (char) | neu | leer zulaessig |
| `account.invoice.refund_invoice_id` | Rechnung, für welche diese Gutschrift ausgestellt wurde | `account.move.reversed_entry_id` | Stornierung von | 1:1 Zuordnung (215 Gutschriften); siehe Gutschriftregel | - | gespeichert (many2one) | gespeichert (many2one) | migriert (Regel) | Gutschrift verweist auf die Rechnung; abweichende 22 Belege ohne Bezug bleiben leer |
| `account.invoice.residual` | Fälliger Betrag | `account.move.amount_residual` | Fälliger Betrag | 1:1 Betrag, wird in Odoo 18 aus den Buchungszeilen neu berechnet | Abstimmungen | gespeichert (monetary) | gespeichert (monetary) | neu berechnet | nur bezahlte Rechnungen haben Restbetrag 0 |
| `account.invoice.sent` | Gesendet | `account.move.is_move_sent` | Gesendet | 1:1 Kennzeichen (2.549 Rechnungen) | - | gespeichert (boolean) | gespeichert (boolean) | migriert | Kennzeichen uebernommen |
| `account.invoice.state` | Status | `account.move.state + payment_state` | - | Transformation: Odoo 11 draft -> Entwurf; open -> gebucht, payment_state offen/teilweise; paid -> gebucht, payment_state bezahlt; cancel -> Storno. Der Odoo-11-Zustand 'Open' existiert in Odoo 18 nicht und wird ueber das Zahlungszustandsfeld abgebildet. | account.move (Zustandslogik) | gespeichert (selection) | berechnet (-) | migriert (Regel) | 43 ehemals 'open'-Belege muessen als gebucht mit offenem Restbetrag erscheinen; Stichprobe der Summen |
| `account.invoice.team_id` | Vertriebskanal | `account.move.team_id` | Vertriebskanal | Zuordnung ueber Teamnamen (Vertriebskanal) | crm.team | gespeichert (many2one) | gespeichert (many2one) | migriert | Team vorhanden oder leer |
| `account.invoice.type` | Typ | `account.move.move_type` | Typ | Transformation: out_invoice -> out_invoice, out_refund -> out_refund (Odoo 11 in_invoice/in_refund in ITK nicht verwendet) | - | gespeichert (selection) | gespeichert (selection) | migriert | Belegart stimmt je Datensatz |
| `account.invoice.user_id` | Verkäufer | `account.move.invoice_user_id` | Verkäufer | Zuordnung ueber Benutzerkennung | res.users | gespeichert (many2one) | gespeichert (many2one) | migriert | Verkaeufer vorhanden oder leer erlaubt |
| `account.invoice.valorisierung_id` | Valorisation Text | `account.move.valorisierung_id` | Valorisation Text | Zuordnung ueber Valorisierungstext (10 Texte, K4) | itk_valorisierung (Stammdaten: 10 Texte) | gespeichert (many2one) | gespeichert (many2one) | migriert | Text vorhanden; 4.216 Rechnungen betroffen |
| `account.invoice.line.account_analytic_id` | Kostenstelle | `account.move.line.analytic_distribution` | Kostenstelle | Transformation: Kostenstelle wird als Verteilungsschluessel 100 % uebernommen | account.analytic.account bzw. analytic plan (Stammdaten) | gespeichert (many2one) | gespeichert (json) | migriert (Regel) | 12.634 Kostenstellenbuchungen zugeordnet |
| `account.invoice.line.account_id` | Konto | `account.move.line.account_id` | Konto | Transformation: Odoo-11-Konto ueber Mapping-Tabelle auf Odoo-18-Konto (l10n_at) | K1-Kontenmapping (1.286 Konten) | gespeichert (many2one) | gespeichert (many2one) | migriert (Regel) | jede Zeile hat ein Erloeskonto |
| `account.invoice.line.company_currency_id` | Betriebl. Währung | `account.move.line.company_currency_id` | Betriebl. Währung | berechnet (EUR) | res.currency | berechnet (many2one) | gespeichert (many2one) | neu berechnet | EUR |
| `account.invoice.line.company_id` | Unternehmen | `account.move.line.company_id` | Unternehmen | 1:1 Unternehmen | res.company | gespeichert (many2one) | gespeichert (many2one) | migriert | Unternehmen gesetzt |
| `account.invoice.line.currency_id` | Währung | `account.move.line.currency_id` | Währung | 1:1 Waehrung | res.currency | gespeichert (many2one) | gespeichert (many2one) | migriert | EUR (USD-Sonderfaelle K9) |
| `account.invoice.line.discount` | Rabatt (%) | `account.move.line.discount` | Rabatt (%) | 1:1 Prozent | - | gespeichert (float) | gespeichert (float) | migriert | 0-100 |
| `account.invoice.line.invoice_id` | Rechnungsreferenz | `account.move.line.move_id` | Rechnungsreferenz | 1:1 Beziehung (Zeile zur Rechnung) | - | gespeichert (many2one) | gespeichert (many2one) | migriert | jede Zeile hat eine Rechnung |
| `account.invoice.line.invoice_line_tax_ids` | Steuern | `account.move.line.tax_ids` | Steuern | Transformation: Odoo-11-Steuer ueber Steuer-Mapping (77 -> 53) | K5 Steuermapping | gespeichert (many2many) | gespeichert (many2many) | migriert (Regel) | Steuersatz und Betrag stimmen |
| `account.invoice.line.name` | Beschreibung | `account.move.line.name` | Beschreibung | 1:1 (Text) | - | gespeichert (text) | gespeichert (char) | migriert | Beschreibung uebernommen |
| `account.invoice.line.partner_id` | Partner | `account.move.line.partner_id` | Partner | 1:1 Partner | res.partner | gespeichert (many2one) | gespeichert (many2one) | migriert | Partner vorhanden |
| `account.invoice.line.price_subtotal` | Betrag | `account.move.line.price_subtotal` | Betrag | neu berechnet aus Menge x Preis - Rabatt | - | gespeichert (monetary) | gespeichert (monetary) | neu berechnet | Summe der Zeilen = Nettobetrag der Rechnung |
| `account.invoice.line.price_total` | Betrag | `account.move.line.price_total` | Betrag | neu berechnet (inkl. Steuer) | Steuern (K5) | gespeichert (monetary) | gespeichert (monetary) | neu berechnet | Summe = Bruttobetrag |
| `account.invoice.line.price_unit` | Preis pro ME | `account.move.line.price_unit` | Preis pro ME | 1:1 Preis | - | gespeichert (float) | gespeichert (float) | migriert | Preis unveraendert |
| `account.invoice.line.product_id` | Produkt | `account.move.line.product_id` | Produkt | 1:1 Produkt | product.product | gespeichert (many2one) | gespeichert (many2one) | migriert | Produkt vorhanden oder Freitextposition erlaubt |
| `account.invoice.line.projectcategory_id` | - | `account.move.line.projectcategory_id` | - | Zuordnung ueber Projektkategorie | itk_projectcategory | berechnet (-) | berechnet (-) | migriert | Kategorie vorhanden |
| `account.invoice.line.purchase_line_id` | Bestellposition | `account.move.line.purchase_line_id` | Bestellposition | kein Altdatenbezug (0 Belege) | purchase | gespeichert (many2one) | gespeichert (many2one) | neu | leer |
| `account.invoice.line.quantity` | Menge | `account.move.line.quantity` | Menge | 1:1 Menge (Mengeneinheit R1 beruecksichtigen) | uom.uom (R1-Genauigkeit) | gespeichert (float) | gespeichert (float) | migriert | Menge > 0 |
| `account.invoice.line.sequence` | Nummernfolge | `account.move.line.sequence` | Nummernfolge | 1:1 Reihenfolge | - | gespeichert (integer) | gespeichert (integer) | migriert | Zeilennummern fortlaufend |
| `account.invoice.line.uom_id` | Mengeneinheit | `account.move.line.product_uom_id` | Mengeneinheit | 1:1 Mengeneinheit (R1) | uom.uom | gespeichert (many2one) | gespeichert (many2one) | migriert | Einheit vorhanden; GB als 'Datenmenge' |
| `account.invoice.line.valorisierung_id` | - | `account.move.line.valorisierung_id` | - | Zuordnung ueber Valorisierungstext | itk_valorisierung | berechnet (-) | berechnet (-) | migriert | Text vorhanden |

Pflichtfelder Odoo 11: `account.invoice.currency_id`, `account.invoice.journal_id`, `account.invoice.partner_id`, `account.invoice.line.account_id`, `account.invoice.line.name`, `account.invoice.line.price_unit`, `account.invoice.line.quantity`

Pflichtfelder Odoo 18: `account.move.currency_id`, `account.move.date`, `account.move.journal_id`, `account.move.move_type`, `account.move.line.currency_id`, `account.move.line.move_id`

## 2. Regeln ohne Feldbezug

- **K2a Doppelnummer R-25001:** Rechnung behaelt R-25001, Gutschrift erhaelt eine neue Nummer; Originalnummer im Feld 'Odoo-11-Rechnungsnummer' (Anlage in Teil 5/Migration, Feldname und Modul ueber itk_reports/neues ITK-Modul festzulegen).
- **K2b Nummerierung:** sequence_override_regex ^(?P<prefix1>R-)(?P<year>\d{2})(?P<seq>\d+)$ erst unmittelbar vor der ersten neuen Rechnung setzen; vorher Testkopie fuer den ersten Beleg eines neuen Jahres.
- **K2c Schutz:** restrict_mode_hash_table und Pruefpfad erst NACH der Migration und nach erfolgreicher Kontrolle aktivieren.
- **Gutschriften (B2):** reversed_entry_id setzen; Originalsnummer der Gutschrift in 'Odoo-11-Rechnungsnummer'; Gutschriftsgrund aus dem Odoo-11-Feld name in ref und in der Chatter-Nachricht; auto_post = no setzen, damit keine Gutschrift nachtraeglich automatisch gebucht wird.
- **Zahlungen (B3):** Historische Zahlungen werden ueber die Abstimmung abgebildet (Zahlung, Bankjournal BNK1, Memo = Rechnungsnummer). Zahlungsnummern des Altsystems werden nicht neu vergeben; Rechnungen als bezahlt ausweisen.
- **K1 Kontenrahmen:** Odoo-18-Kontenrahmen l10n_at bleibt. Mapping-Tabelle Odoo-11-Konto -> Odoo-18-Konto (1.286 Konten) ist vorzubereiten; offener Punkt aus dem Kontenvergleich (l10n_de 1.286 zu l10n_at 240).
- **K5 Steuern:** Vollstaendiges Steuer-Mapping 77 Odoo-11-Steuern auf 53 Odoo-18-Steuern vorbereiten; nichts migrieren.
- **Valorisierungstexte (K4):** 10 Stammdatensaetze in Odoo 18 anlegen (Mapping ueber Bezeichnung), danach 4.216 Rechnungen zuordnen.
- **SMTP (K7):** Versand bleibt offen; nur als Infrastrukturpunkt dokumentiert.

## 3. Umfang

- Feldpaare in dieser Tabelle: 53 (Rechnungskopf und Rechnungszeile).
- Grundlage: `docs/o11-o18-vergleich-abrechnung-teil2.md` (Feldinventar, 87/37 bzw. 189/93 Felder),
  `docs/o11-o18-abrechnung-labelmapping.md` (Label-/Feldmapping) und die Befunde B2/B3/B6.
- Nicht aufgefuehrt sind Felder ohne Datensaetze im Altsystem und reine Odoo-18-Zusatzfelder
  (bleiben erhalten, werden nicht migriert).

## 4. Naechster Schritt

Teil 6: Berichte (Vorgabe K3).
