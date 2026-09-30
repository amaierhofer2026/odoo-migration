"""Erzeugt Teil 5 der Abrechnung: vollstaendige Feldabbildung und Migrationsregeln.

Je tatsaechlich relevantem Odoo-11-Feld werden festgehalten:
  Odoo-11-Modell und Feld, Odoo-11-Bezeichnung, Odoo-18-Zielmodell und Feld,
  Odoo-18-Bezeichnung, Zuordnung/Transformationsregel, benoetigte Stammdaten/Module,
  gespeichert oder berechnet, migriert oder neu berechnet, Validierungsregel nach der Migration.

Messdaten (Bezeichnungen, Typen, Pflicht, gespeichert, Herkunftsmodul) kommen live aus beiden
Systemen (Odoo 11 nur lesend). Die fachlichen Regelspalten stehen in REGELN.

Aufruf:  python scripts/baue_abrechnung_teil5_doku.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o11, o18

QUELLE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (Odoo-11-Modell, Feld) -> (Odoo-18-Modell, Feld, Zuordnung/Transformation, Abhaengigkeiten,
#                            migriert/neu berechnet, Validierungsregel)
REGELN = {
    # Rechnungskopf
    ("account.invoice", "partner_id"): ("account.move", "partner_id", "1:1 (Partner ueber Name/ID des Altsystems, Abgleich ueber res.partner-Referenz)", "res.partner", "migriert", "Kunde vorhanden und Rechnung zugeordnet; keine Rechnung ohne Partner"),
    ("account.invoice", "date_invoice"): ("account.move", "invoice_date", "1:1 (Datum)", "-", "migriert", "Rechnungsdatum gesetzt, nicht leer"),
    ("account.invoice", "date_due"): ("account.move", "invoice_date_due", "1:1 (Datum)", "account.payment.term (nur zur Kontrolle)", "migriert", "Faelligkeit >= Rechnungsdatum"),
    ("account.invoice", "date"): ("account.move", "date", "1:1 (Datum)", "-", "migriert", "Buchungsdatum gesetzt; in abgeschlossenen Perioden gesperrt"),
    ("account.invoice", "number"): ("account.move", "name", "1:1 (Belegnummer unveraendert uebernehmen; Nummer wird beim Import gesetzt, nicht neu erzeugt)", "Journal + Sequenz (K2b)", "migriert", "Nummer eindeutig je Journal; Kontrolle gegen K2a-Ausnahmefall R-25001"),
    ("account.invoice", "origin"): ("account.move", "invoice_origin", "1:1 (Text)", "-", "migriert", "Feld uebernommen (2.137 Belege ungenutzt/leer zulaessig)"),
    ("account.invoice", "comment"): ("account.move", "narration", "1:1 (Text/HTML-sicher)", "-", "migriert", "Text uebernommen, keine Umformatierung"),
    ("account.invoice", "state"): ("account.move", "state + payment_state", "Transformation: Odoo 11 draft -> Entwurf; open -> gebucht, payment_state offen/teilweise; paid -> gebucht, payment_state bezahlt; cancel -> Storno. Der Odoo-11-Zustand 'Open' existiert in Odoo 18 nicht und wird ueber das Zahlungszustandsfeld abgebildet.", "account.move (Zustandslogik)", "migriert (Regel)", "43 ehemals 'open'-Belege muessen als gebucht mit offenem Restbetrag erscheinen; Stichprobe der Summen"),
    ("account.invoice", "type"): ("account.move", "move_type", "Transformation: out_invoice -> out_invoice, out_refund -> out_refund (Odoo 11 in_invoice/in_refund in ITK nicht verwendet)", "-", "migriert", "Belegart stimmt je Datensatz"),
    ("account.invoice", "journal_id"): ("account.move", "journal_id", "Zuordnung ueber Journal-Code (Odoo 11 'Re.' -> Odoo 18 'RE')", "account.journal (Stammdaten, Migration)", "migriert", "jede Rechnung hat ein Verkaufsjournal"),
    ("account.invoice", "user_id"): ("account.move", "invoice_user_id", "Zuordnung ueber Benutzerkennung", "res.users", "migriert", "Verkaeufer vorhanden oder leer erlaubt"),
    ("account.invoice", "team_id"): ("account.move", "team_id", "Zuordnung ueber Teamnamen (Vertriebskanal)", "crm.team", "migriert", "Team vorhanden oder leer"),
    ("account.invoice", "payment_term_id"): ("account.move", "invoice_payment_term_id", "Zuordnung ueber Bezeichnung der Zahlungsbedingung", "account.payment.term (Stammdaten, Migration)", "migriert", "Zahlungsbedingung vorhanden; Faelligkeit passt dazu"),
    ("account.invoice", "fiscal_position_id"): ("account.move", "fiscal_position_id", "Zuordnung ueber Steuerzuordnung", "account.fiscal.position", "migriert", "nur wenn Odoo 11 gesetzt (0 Belege)"),
    ("account.invoice", "partner_bank_id"): ("account.move", "partner_bank_id", "Zuordnung ueber Bankverbindung", "res.partner.bank", "migriert", "Bankkonto vorhanden oder leer"),
    ("account.invoice", "currency_id"): ("account.move", "currency_id", "1:1 (EUR)", "res.currency", "migriert", "Waehrung EUR; USD-Sonderfaelle (4 Belege, K9) gesondert pruefen"),
    ("account.invoice", "amount_untaxed"): ("account.move", "amount_untaxed", "1:1 Betrag (Kontrolle gegen Zeilensummen)", "Steuern (K5)", "migriert und beim Import gegen die Zeilen geprueft", "Nettobetrag stimmt mit Zeilensummen ueberein"),
    ("account.invoice", "amount_tax"): ("account.move", "amount_tax", "1:1 Betrag (Kontrolle gegen Steuerzeilen)", "Steuern (K5)", "migriert und geprueft", "Steuerbetrag stimmt mit den Steuerzeilen ueberein"),
    ("account.invoice", "amount_total"): ("account.move", "amount_total", "1:1 Betrag", "Steuern (K5)", "migriert und geprueft", "Bruttobetrag = Netto + Steuer"),
    ("account.invoice", "residual"): ("account.move", "amount_residual", "1:1 Betrag, wird in Odoo 18 aus den Buchungszeilen neu berechnet", "Abstimmungen", "neu berechnet", "nur bezahlte Rechnungen haben Restbetrag 0"),
    ("account.invoice", "payment_reference"): ("account.move", "payment_reference", "kein Altdatenbezug (in Odoo 11 nicht vorhanden)", "-", "neu", "leer zulaessig"),
    ("account.invoice", "notice"): ("account.move", "notice", "1:1 (ITK-Feld Rechnungsnotiz)", "itk-Modul (Feld vorhanden)", "migriert", "Text uebernommen"),
    ("account.invoice", "projectcategory_id"): ("account.move", "projectcategory_id", "Zuordnung ueber Projektkategorie (Satzart/Code)", "itk_projectcategory (Stammdaten)", "migriert", "Kategorie vorhanden; 5.254 Belege"),
    ("account.invoice", "valorisierung_id"): ("account.move", "valorisierung_id", "Zuordnung ueber Valorisierungstext (10 Texte, K4)", "itk_valorisierung (Stammdaten: 10 Texte)", "migriert", "Text vorhanden; 4.216 Rechnungen betroffen"),
    ("account.invoice", "sent"): ("account.move", "is_move_sent", "1:1 Kennzeichen (2.549 Rechnungen)", "-", "migriert", "Kennzeichen uebernommen"),
    ("account.invoice", "reconciled"): ("account.move", "has_reconciled_entries", "berechnet", "-", "neu berechnet", "nur abgestimmte Belege true"),
    ("account.invoice", "payment_move_line_ids"): ("account.move", "matched_payment_ids", "anderes Modell, ueber Abstimmungen abgeleitet", "-", "neu berechnet", "Zahlungen den richtigen Rechnungen zugeordnet"),
    ("account.invoice", "incoterms_id"): ("account.move", "invoice_incoterm_id", "kein Altdatenbezug (0 Belege)", "sale_stock", "neu", "leer zulaessig"),
    ("account.invoice", "cash_rounding_id"): ("account.move", "invoice_cash_rounding_id", "kein Altdatenbezug (0 Belege)", "-", "neu", "leer zulaessig"),
    ("account.invoice", "refund_invoice_id"): ("account.move", "reversed_entry_id", "1:1 Zuordnung (215 Gutschriften); siehe Gutschriftregel", "-", "migriert (Regel)", "Gutschrift verweist auf die Rechnung; abweichende 22 Belege ohne Bezug bleiben leer"),
    ("account.invoice", "reference"): ("account.move", "ref", "keine Migration (Feld in Odoo 11 nie belegt); ref wird bei Gutschriften nach Odoo-18-Muster gebildet", "-", "neu", "leer zulaessig"),
    ("account.invoice", "name"): ("account.move", "ref (Text) + Chatter", "Transformation: Inhalt ist der Gutschrifts-/Beschreibungsgrund und wird bei Gutschriften in ref geschrieben ('Stornierung von: <alte Nummer>, <Grund>'), zusaetzlich bleibt die Chatter-Nachricht erhalten", "-", "migriert (Regel)", "215 Gutschriften mit Grund nachvollziehbar; 1.203 weitere Belege mit Beschreibung dokumentiert uebernehmen"),
    ("account.invoice", "move_name"): ("account.move", "name", "aufgegangen in die Belegnummer, keine eigene Migration", "-", "entfaellt", "-"),
    # Rechnungszeile
    ("account.invoice.line", "invoice_id"): ("account.move.line", "move_id", "1:1 Beziehung (Zeile zur Rechnung)", "-", "migriert", "jede Zeile hat eine Rechnung"),
    ("account.invoice.line", "name"): ("account.move.line", "name", "1:1 (Text)", "-", "migriert", "Beschreibung uebernommen"),
    ("account.invoice.line", "quantity"): ("account.move.line", "quantity", "1:1 Menge (Mengeneinheit R1 beruecksichtigen)", "uom.uom (R1-Genauigkeit)", "migriert", "Menge > 0"),
    ("account.invoice.line", "price_unit"): ("account.move.line", "price_unit", "1:1 Preis", "-", "migriert", "Preis unveraendert"),
    ("account.invoice.line", "discount"): ("account.move.line", "discount", "1:1 Prozent", "-", "migriert", "0-100"),
    ("account.invoice.line", "price_subtotal"): ("account.move.line", "price_subtotal", "neu berechnet aus Menge x Preis - Rabatt", "-", "neu berechnet", "Summe der Zeilen = Nettobetrag der Rechnung"),
    ("account.invoice.line", "price_total"): ("account.move.line", "price_total", "neu berechnet (inkl. Steuer)", "Steuern (K5)", "neu berechnet", "Summe = Bruttobetrag"),
    ("account.invoice.line", "product_id"): ("account.move.line", "product_id", "1:1 Produkt", "product.product", "migriert", "Produkt vorhanden oder Freitextposition erlaubt"),
    ("account.invoice.line", "uom_id"): ("account.move.line", "product_uom_id", "1:1 Mengeneinheit (R1)", "uom.uom", "migriert", "Einheit vorhanden; GB als 'Datenmenge'"),
    ("account.invoice.line", "account_id"): ("account.move.line", "account_id", "Transformation: Odoo-11-Konto ueber Mapping-Tabelle auf Odoo-18-Konto (l10n_at)", "K1-Kontenmapping (1.286 Konten)", "migriert (Regel)", "jede Zeile hat ein Erloeskonto"),
    ("account.invoice.line", "invoice_line_tax_ids"): ("account.move.line", "tax_ids", "Transformation: Odoo-11-Steuer ueber Steuer-Mapping (77 -> 53)", "K5 Steuermapping", "migriert (Regel)", "Steuersatz und Betrag stimmen"),
    ("account.invoice.line", "purchase_line_id"): ("account.move.line", "purchase_line_id", "kein Altdatenbezug (0 Belege)", "purchase", "neu", "leer"),
    ("account.invoice.line", "sequence"): ("account.move.line", "sequence", "1:1 Reihenfolge", "-", "migriert", "Zeilennummern fortlaufend"),
    ("account.invoice.line", "company_currency_id"): ("account.move.line", "company_currency_id", "berechnet (EUR)", "res.currency", "neu berechnet", "EUR"),
    ("account.invoice.line", "currency_id"): ("account.move.line", "currency_id", "1:1 Waehrung", "res.currency", "migriert", "EUR (USD-Sonderfaelle K9)"),
    ("account.invoice.line", "partner_id"): ("account.move.line", "partner_id", "1:1 Partner", "res.partner", "migriert", "Partner vorhanden"),
    ("account.invoice.line", "company_id"): ("account.move.line", "company_id", "1:1 Unternehmen", "res.company", "migriert", "Unternehmen gesetzt"),
    ("account.invoice.line", "projectcategory_id"): ("account.move.line", "projectcategory_id", "Zuordnung ueber Projektkategorie", "itk_projectcategory", "migriert", "Kategorie vorhanden"),
    ("account.invoice.line", "valorisierung_id"): ("account.move.line", "valorisierung_id", "Zuordnung ueber Valorisierungstext", "itk_valorisierung", "migriert", "Text vorhanden"),
    ("account.invoice.line", "account_analytic_id"): ("account.move.line", "analytic_distribution", "Transformation: Kostenstelle wird als Verteilungsschluessel 100 % uebernommen", "account.analytic.account bzw. analytic plan (Stammdaten)", "migriert (Regel)", "12.634 Kostenstellenbuchungen zugeordnet"),
}

# Regeln, die nicht an ein einzelnes Feld gebunden sind
REGELN_ALLGEMEIN = [
    ("K2a Doppelnummer R-25001", "Rechnung behaelt R-25001, Gutschrift erhaelt eine neue Nummer; Originalnummer im Feld 'Odoo-11-Rechnungsnummer' (Anlage in Teil 5/Migration, Feldname und Modul ueber itk_reports/neues ITK-Modul festzulegen)."),
    ("K2b Nummerierung", "sequence_override_regex ^(?P<prefix1>R-)(?P<year>\\d{2})(?P<seq>\\d+)$ erst unmittelbar vor der ersten neuen Rechnung setzen; vorher Testkopie fuer den ersten Beleg eines neuen Jahres."),
    ("K2c Schutz", "restrict_mode_hash_table und Pruefpfad erst NACH der Migration und nach erfolgreicher Kontrolle aktivieren."),
    ("Gutschriften (B2)", "reversed_entry_id setzen; Originalsnummer der Gutschrift in 'Odoo-11-Rechnungsnummer'; Gutschriftsgrund aus dem Odoo-11-Feld name in ref und in der Chatter-Nachricht; auto_post = no setzen, damit keine Gutschrift nachtraeglich automatisch gebucht wird."),
    ("Zahlungen (B3)", "Historische Zahlungen werden ueber die Abstimmung abgebildet (Zahlung, Bankjournal BNK1, Memo = Rechnungsnummer). Zahlungsnummern des Altsystems werden nicht neu vergeben; Rechnungen als bezahlt ausweisen."),
    ("K1 Kontenrahmen", "Odoo-18-Kontenrahmen l10n_at bleibt. Mapping-Tabelle Odoo-11-Konto -> Odoo-18-Konto (1.286 Konten) ist vorzubereiten; offener Punkt aus dem Kontenvergleich (l10n_de 1.286 zu l10n_at 240)."),
    ("K5 Steuern", "Vollstaendiges Steuer-Mapping 77 Odoo-11-Steuern auf 53 Odoo-18-Steuern vorbereiten; nichts migrieren."),
    ("Valorisierungstexte (K4)", "10 Stammdatensaetze in Odoo 18 anlegen (Mapping ueber Bezeichnung), danach 4.216 Rechnungen zuordnen."),
    ("SMTP (K7)", "Versand bleibt offen; nur als Infrastrukturpunkt dokumentiert."),
]


def felder(k, modell):
    return {f["name"]: f for f in k.kw("ir.model.fields", "search_read",
                                       [[("model", "=", modell)],
                                        ["name", "ttype", "required", "store", "relation", "modules",
                                         "field_description"]])}


def main() -> int:
    lade_env()
    k11, k18 = o11(), o18("lokal")
    f11 = {m: felder(k11, m) for m in ("account.invoice", "account.invoice.line")}
    f18 = {m: felder(k18, m) for m in ("account.move", "account.move.line")}
    b11 = {m: k11.kw(m, "fields_get", [[], ["string"]], context={"lang": "de_DE"}) for m in f11}
    b18 = {m: k18.kw(m, "fields_get", [[], ["string"]], context={"lang": "de_DE"}) for m in f18}

    zeilen = []
    for (m11, fld11), (m18, fld18, zuordnung, abh, mig, val) in sorted(REGELN.items()):
        d11 = f11.get(m11, {}).get(fld11, {})
        d18 = f18.get(m18, {}).get(fld18, {})
        zeilen.append({
            "m11": m11, "f11": fld11, "l11": (b11.get(m11, {}).get(fld11) or {}).get("string", "-"),
            "m18": m18, "f18": fld18, "l18": (b18.get(m18, {}).get(fld18) or {}).get("string", "-"),
            "zuordnung": zuordnung, "abh": abh, "mig": mig, "val": val,
            "pflicht11": "ja" if d11.get("required") else "-",
            "pflicht18": "ja" if d18.get("required") else "-",
            "speicher11": "gespeichert" if d11.get("store") else "berechnet",
            "speicher18": "gespeichert" if d18.get("store") else "berechnet",
            "typ11": d11.get("ttype", "-"), "typ18": d18.get("ttype", "-"),
            "modul11": d11.get("modules", "-") or "-",
        })

    ziel = os.path.join(QUELLE, "docs", "o11-o18-vergleich-abrechnung-teil5-feldabbildung.md")
    with open(ziel, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# Odoo 11 gegen Odoo 18 - Bereich Abrechnung, Teil 5: Feldabbildung und Migrationsregeln\n\n")
        fh.write("Stand: 30.09.2026, Session 122. **Reine Vorbereitung: es wurde nichts migriert.**\n")
        fh.write("Odoo 11 wurde ausschliesslich lesend verwendet, Aenderungen nur in Odoo 18.\n\n")
        fh.write("Erzeugt von `scripts/baue_abrechnung_teil5_doku.py` (Messdaten live aus beiden Systemen,\n")
        fh.write("Regelspalten aus der Regel-Tabelle im Skript). Bezeichnungen entsprechen dem Stand nach dem\n")
        fh.write("Label-Abgleich (Teil 4 + Label-Regel).\n\n")
        fh.write("## 1. Feldabbildung (je tatsaechlich relevantem Odoo-11-Feld)\n\n")
        fh.write("| Odoo-11-Modell.Feld | Odoo-11-Bezeichnung | Odoo-18-Zielmodell.Feld | Odoo-18-Bezeichnung | Zuordnung / Transformationsregel | Stammdaten / Modulabhaengigkeit | Odoo 11 | Odoo 18 | migriert oder neu berechnet | Validierung nach der Migration |\n")
        fh.write("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n")
        for z in zeilen:
            fh.write("| `%s.%s` | %s | `%s.%s` | %s | %s | %s | %s (%s) | %s (%s) | %s | %s |\n"
                     % (z["m11"], z["f11"], z["l11"], z["m18"], z["f18"], z["l18"], z["zuordnung"],
                        z["abh"], z["speicher11"], z["typ11"], z["speicher18"], z["typ18"],
                        z["mig"], z["val"]))
        fh.write("\nPflichtfelder Odoo 11: %s\n" % ", ".join(
            "`%s.%s`" % (z["m11"], z["f11"]) for z in zeilen if z["pflicht11"] == "ja"))
        fh.write("\nPflichtfelder Odoo 18: %s\n\n" % ", ".join(
            "`%s.%s`" % (z["m18"], z["f18"]) for z in zeilen if z["pflicht18"] == "ja"))
        fh.write("## 2. Regeln ohne Feldbezug\n\n")
        for titel, text in REGELN_ALLGEMEIN:
            fh.write("- **%s:** %s\n" % (titel, text))
        fh.write("\n## 3. Umfang\n\n")
        fh.write("- Feldpaare in dieser Tabelle: %d (Rechnungskopf und Rechnungszeile).\n" % len(zeilen))
        fh.write("- Grundlage: `docs/o11-o18-vergleich-abrechnung-teil2.md` (Feldinventar, 87/37 bzw. 189/93 Felder),\n")
        fh.write("  `docs/o11-o18-abrechnung-labelmapping.md` (Label-/Feldmapping) und die Befunde B2/B3/B6.\n")
        fh.write("- Nicht aufgefuehrt sind Felder ohne Datensaetze im Altsystem und reine Odoo-18-Zusatzfelder\n")
        fh.write("  (bleiben erhalten, werden nicht migriert).\n\n")
        fh.write("## 4. Naechster Schritt\n\nTeil 6: Berichte (Vorgabe K3).\n")
    print("Teil-5-Dokument geschrieben: %s (%d Feldpaare)" % (ziel, len(zeilen)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
