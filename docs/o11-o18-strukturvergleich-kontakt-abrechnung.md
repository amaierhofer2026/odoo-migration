# Strukturvergleich Odoo 11 Prod ↔ Odoo 18: Kontakte → Kontaktformular → Abrechnung

Stand: 15.09.2026 (Session 108)
Quellen: Odoo 11 Prod `portal.it-kommunal.at` (DB `ITK_V1_a`, nur gelesen) und Odoo 18 (lokal + VM `k001959vsx.ipax.at`, DB `odoo18_test`)

Auftrag von Anna: **kein optischer Rückbau.** Ziel ist ausschließlich, dass alle abrechnungsrelevanten Informationen aus
Odoo 11 Prod bei der späteren Migration korrekt in Odoo 18 landen. Zusätzlich zu prüfen: welche Odoo-11-Felder in
Odoo 18 in andere Reiter verschoben wurden.

## 1. Ergebnis vorab

Der Tab "Abrechnung" ist in Odoo 18 **fachlich deutlich vollständiger** als in Odoo 11:

| Gruppe im Odoo-18-Tab "Abrechnung" | Inhalt | In Odoo 11 |
|---|---|---|
| Bankkonten | vollständig editierbare Bankverbindungen (`bank_ids` mit Kontonummer, Bank, Kontoinhaber, "Geld senden") | nur ein Statistik-Knopf "Bankkonten" im Tab Verkauf & Einkauf |
| Kundenrechnungen | Rechnungsversand, Format der elektronischen Rechnung, Peppol-Adresse/VOKZ, Rechnungsvorlage | nicht vorhanden |
| Kreditlimits | `credit`, `credit_limit`, Partnerlimit | Felder vorhanden, im Formular nicht sichtbar |
| Automatisierung | `autopost_bills` (Rechnungen automatisch buchen) | nicht vorhanden |

**Am Tab wurde deshalb nichts geändert** (kein Rückbau). Es ergab sich **keine strukturelle Lücke** in Odoo 18; alle
Odoo-11-Felder sind abbildbar. Offen sind ausschließlich Stammdaten- und Verfahrensentscheidungen (Abschnitt 6).

## 2. Feld-Mapping Abrechnung

| Odoo-11-Feld | Bedeutung | Odoo-18-Zielfeld bzw. Ziellogik | Feldtyp | Zuordnung |
|---|---|---|---|---|
| `property_payment_term_id` | Zahlungsbedingungen Kunde | `property_payment_term_id` (gleiche Technik, **Reiter gewechselt**: Odoo 11 "Abrechnung" → Odoo 18 "Verkauf & Einkauf") | many2one `account.payment.term`, firmenabhängig | **1:1** (Stammdaten-Mapping: "14 Tage" vorhanden) |
| `property_supplier_payment_term_id` | Zahlungsbedingungen Lieferant | gleichnamig, **Reiter gewechselt** → "Verkauf & Einkauf" | many2one `account.payment.term`, firmenabhängig | **1:1** (in Odoo 11 0 Datensätze) |
| `property_account_position_id` | Steuerzuordnung / Steuerposition | gleichnamig, **Reiter gewechselt** → "Verkauf & Einkauf" | many2one `account.fiscal.position`, firmenabhängig | **1:1** + Stammdaten-Mapping (5 Odoo-11-Positionen → 4 Odoo-18-Positionen) |
| `property_account_receivable_id` | Debitorenkonto | gleichnamiges Feld (in Odoo 18 nicht im Formular; Steuerung über die Buchhaltungs-Standardwerte) | many2one `account.account`, firmenabhängig | **1:1**; in Odoo 11 waren die Felder in einer unsichtbaren Gruppe "Buchungen" – kein Datenbestand (0 Individualwerte) |
| `property_account_payable_id` | Kreditorenkonto | gleichnamig | many2one `account.account`, firmenabhängig | **1:1**; ebenfalls 0 Individualwerte |
| `bank_ids` | Bankkonten des Kontakts | `bank_ids`, **Reiter gewechselt**: Odoo 11 "Verkauf & Einkauf" → Odoo 18 "Abrechnung", dort vollständig pflegbar | one2many `res.partner.bank` | **1:1** (in Odoo 11 genau 1 Bankverbindung) |
| – (Odoo 11 kannte das Feld nicht) | Zahlungsbezug der Bankverbindung | `res.partner.bank.allow_out_payment` ("Geld senden") | boolean | **neu in Odoo 18**; zusätzlich `acc_holder_name` (Kontoinhaber), `bank_id`, `sequence` |
| `trust` | Grad des Vertrauens in diesen Debitor | `trust` (gleiches Feld, Werte good/normal/bad) | selection | **1:1**, aber in **beiden** Systemen nicht im Formular; Datenbestand: alle 5.842 Kontakte "normal" → keine Migration nötig |
| `credit` | Summe Debitoren (berechnet) | `credit` ("Debitoren gesamt", berechnet) | monetary, berechnet | **entfällt für die Migration** (wird in Odoo 18 berechnet) |
| `credit_limit` | Kreditlinie | `credit_limit` ("Kreditlimit") + `use_partner_credit_limit` ("Partnerlimit") | float / boolean | **Transformation**: Wert > 0 → `credit_limit` setzen und `use_partner_credit_limit = True`. Odoo 11 hat **keine** Werte ungleich 0 |
| `property_stock_customer` / `property_stock_supplier` | Kundenlagerort / Lagerort des Lieferanten (in Odoo 11 im Tab Verkauf & Einkauf) | kein Feld in Odoo 18 | many2one `stock.location` | **entfällt**; Funktion über Lager/Routen → kein Nachbau (bereits im Bereich Verkauf & Einkauf dokumentiert) |
| – | **Rechnungsversand** | `invoice_sending_method` (manuell / E-Mail / Post / Peppol) | selection | **neu in Odoo 18**, keine Odoo-11-Quelle (0 Werte im Testbestand) |
| – | **Format der elektronischen Rechnung** | `invoice_edi_format` (Auswahl: UBL BIS 3, Factur-X, ZUGFeRD, XRechnung, NLCIUS, UBL A-NZ, UBL SG) + Speicherfeld `invoice_edi_format_store`, `invoice_template_pdf_report_id` (Rechnungsvorlage PDF) | selection / char / many2one | **neu in Odoo 18**, keine Odoo-11-Quelle (0 Werte im Testbestand) |
| – | **VOKZ / österreichische Rechnungsinformationen** | `peppol_eas` (Auswahl; **9915 = "VOKZ für Österreich"**) + `peppol_endpoint` + `peppol_verification_state` | selection / char / selection | **neu in Odoo 18**, keine Odoo-11-Quelle (siehe Abschnitt 4) |
| – | **Automatisierung der Rechnungsbuchung** | `autopost_bills` (immer / fragen / nie) | selection | **neu in Odoo 18**; im Testbestand steht überall der Standardwert "fragen" (kein Odoo-11-Datenbestand) |
| – | weitere neue Odoo-18-Felder | `ignore_abnormal_invoice_amount`, `ignore_abnormal_invoice_date`, `credit_to_invoice`, `days_sales_outstanding`, `duplicated_bank_account_partners_count` | boolean/monetary/float/integer | **neu in Odoo 18**, ohne Odoo-11-Quelle |
| `invoice_warn` / `invoice_warn_msg` | Warnung zu Rechnung / Warntext | gleichnamig | selection / text | **1:1** (bereits im Bereich "Interne Notizen" dokumentiert) |
| `supplier_invoice_count`, `total_invoiced`, `invoice_ids` | Statistik-/Verknüpfungsfelder | gleichnamig | integer/monetary/one2many | **entfällt für die Migration** (berechnet bzw. aus den Belegen) |

## 3. In andere Reiter verschobene Felder (Auftrag: "damit keine Information verloren geht")

| Feld | Odoo 11 im Reiter | Odoo 18 im Reiter | Folge für die Migration |
|---|---|---|---|
| `property_payment_term_id` (Zahlungsbedingungen Kunde) | Abrechnung | **Verkauf & Einkauf** | kein Informationsverlust, Feld und Technik identisch |
| `property_supplier_payment_term_id` (Zahlungsbedingungen Lieferant) | Abrechnung | **Verkauf & Einkauf** | wie oben |
| `property_account_position_id` (Steuerposition) | Abrechnung | **Verkauf & Einkauf** | wie oben, nur die Positionen selbst sind zuzuordnen |
| `bank_ids` (Bankkonten) | Verkauf & Einkauf (nur Statistik-Knopf) | **Abrechnung** (voll pflegbar) | Odoo 18 ist hier vollständiger, keine Lücke |
| `property_stock_customer` / `property_stock_supplier` | Verkauf & Einkauf | – (entfällt in Odoo 18) | Funktion über Lager/Routen, kein Nachbau |
| `invoice_warn` / `invoice_warn_msg` | Interne Notizen | Interne Notizen | unverändert |

## 4. VOKZ / österreichspezifische Rechnungsinformationen

**Befund:** "VOKZ" ist die österreichische Peppol-Teilnehmerkennung. Odoo 18 führt sie als
`peppol_eas` = **9915** mit der Beschriftung **"VOKZ für Österreich"** und dem eigentlichen Wert in `peppol_endpoint`.
Damit ist VOKZ in Odoo 18 sauber abbildbar (Peppol-Versand, Import/Export von E-Rechnungen).

**In Odoo 11 Prod gibt es kein VOKZ-Feld.** Geprüft wurde über alle Modelle (Feldnamen), über Feldbeschreibungen,
über Freitextfelder (`res.partner.comment`, `account.move.narration`/`ref`, `sale.order.note`) und über die
Berichtsvorlagen (`ir.ui.view`, inklusive Suche nach "ebInterface") – **jeweils 0 Treffer**. Es ist also nichts zu
migrieren; die Werte müssten – falls ITK über Peppol abrechnen will – für die Empfänger neu erhoben werden.

Im Testbestand Odoo 18 haben 18 Kontakte die EAS-Kennung 9915 (VOKZ für Österreich) vorbelegt; bei 6 davon ist zusätzlich ein Peppol-Endpunkt eingetragen.

## 5. Datenlage in Odoo 11 Prod (read-only)

| Feld | Kontakte mit Wert |
|---|---|
| `property_payment_term_id` | 619 (ausschließlich "14 Tage") |
| `property_supplier_payment_term_id` | 0 |
| `property_account_position_id` | 1 ("Dienstleister EU (mit USt-ID)") |
| `property_account_receivable_id` / `property_account_payable_id` | 0 Individualwerte (Firmenstandard: Konto 295 bzw. 401) |
| `bank_ids` | 1 Bankverbindung bei 1 Kontakt |
| `trust` | alle 5.842 Kontakte "normal" (Standardwert) |
| `credit_limit` | 0 Kontakte mit Wert ungleich 0 |
| `invoice_sending_method`, `invoice_edi_format`, `autopost_bills`, `peppol_*` | Feld in Odoo 11 nicht vorhanden |

## 6. Offene Punkte (Stammdaten-/Verfahrensentscheidungen, keine Strukturprobleme)

1. **Format der elektronischen Rechnung:** In Odoo 18 stehen die UBL/CII-basierten Formate zur Verfügung
   (u. a. `ubl_bis3` = Peppol BIS 3, Factur-X, ZUGFeRD, XRechnung). Ein **ebInterface**-Format (in Österreich
   verbreitet) ist im Standard **nicht** enthalten – geprüft in beiden Systemen (0 Treffer), ebenso kein
   `l10n_at_edi`-Modul im Container. Vor der Migration ist zu entscheiden, welches Format ITK bzw. die Empfänger
   verlangen (ggf. eigenes Modul oder Peppol BIS 3).
2. **Peppol/VOKZ:** Der Peppol-Versand setzt eine Peppol-Registrierung (eigene VOKZ/Peppol-ID) voraus; die
   Peppol-Module sind installiert (`account_peppol`, `account_edi_ubl_cii`, `account_edi_proxy_client`), eine
   Registrierung wurde nicht vorgenommen und ist ohne Freigabe nicht möglich. Zu klären: Soll ITK über Peppol
   abrechnen, und woher kommen die VOKZ der Empfänger?
3. **Steuerpositionen:** Zuordnung der fünf Odoo-11-Positionen auf die vier Odoo-18-Positionen (siehe Bereich
   Verkauf & Einkauf, Abschnitt 5.3; 1 Kontakt betroffen).
4. **Debitoren-/Kreditorenkonten:** In Odoo 11 existieren nur Firmenstandardwerte (Konto 295 / 401); Odoo 18
   bringt eigene Standardwerte der Lokalisierung mit. Zu bestätigen: Verwendung der Odoo-18-Standardkonten
   (keine Konten-Migration nötig).
5. **Kreditlimits:** Die Gruppe "Kreditlimits" ist im Testsystem ausgeblendet, weil das Partnerlimit nicht
   aktiviert ist. In Odoo 11 gibt es keine Werte; eine Aktivierung ist nur nötig, wenn ITK Kreditlimits nutzen will.
6. **Rechnungsversand:** Odoo 11 hat kein Feld dafür (Rechnungen wurden manuell/per E-Mail versendet). In Odoo 18
   ist `invoice_sending_method` je Kontakt setzbar – zu entscheiden, ob bei der Migration ein Standardwert
   gesetzt werden soll (z. B. "E-Mail").

## 7. Prüfwerkzeug und Nachweis

`scripts/verify_s108_abrechnung.py` (read-only) prüft Feldnamen, Typen, Relationen, den gerenderten Arch des
Reiters "Abrechnung" und die abrechnungsrelevanten Stammdaten – lokal und gegen die VM.

## 8. Nachweis (Session 108)

| Prüfung | Ergebnis |
|---|---|
| `scripts/verify_s108_abrechnung.py` | lokal **44 OK / 0 FEHL**, VM **44 OK / 0 FEHL** |
| Felder, Typen, Relationen (18 Felder) | alle vorhanden und korrekt |
| Reiter „Abrechnung“ im gerenderten Arch | `bank_ids`, `invoice_sending_method`, `invoice_edi_format`, `peppol_eas`, `peppol_endpoint`, `autopost_bills` |
| Verschobene Felder geprüft | Zahlungsbedingungen/Steuerposition jetzt in „Verkauf & Einkauf“, Bankkonten in „Abrechnung“ |
| Stammdaten | 11 Zahlungsbedingungen (inkl. „14 Tage“), 4 Steuerpositionen, 240 Konten (4 Debitoren, 7 Kreditoren) |
| VOKZ | `peppol_eas` 9915 = „VOKZ für Österreich“ vorhanden; Peppol-/EDI-Module installiert |
| Browser-Prüfung auf der VM (Kontakt 69) | sichtbar: „Rechnungsversand“, „Format der elektronischen Rechnung“, „Rechnungen automatisch buchen?“, Bankkonten |
| Screenshot | `Desktop\Odoo18-Layoutvergleich-Session95\16_VM_Abrechnung.png` |
| Kontrollzahlen | 70 Kontakte unverändert; keine Datensatzänderung |
