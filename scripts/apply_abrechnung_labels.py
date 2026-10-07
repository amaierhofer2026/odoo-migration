"""Sichtbare Odoo-11-Bezeichnungen im Bereich Abrechnung setzen (Regel Anna, 30.09.2026).

Setzt ausschliesslich Feldbeschreibungen (de_DE) auf den Odoo-11-Wortlaut, wenn das Feld in
Odoo 18 fachlich dieselbe Bedeutung hat. Interne Feldnamen bleiben unveraendert.

Warum ein Skript: Odoo 18 setzt die deutschen Feldbeschriftungen bei einem Modul-Upgrade auf die
Quelltexte zurueck. Das Skript laeuft deshalb nach jedem Upgrade - lokal und auf der VM.

Aufruf:
    python scripts/apply_abrechnung_labels.py --instanz lokal
    python scripts/apply_abrechnung_labels.py --instanz vm
    python scripts/apply_abrechnung_labels.py --instanz vm --pruefen    (nur lesen)

Nicht gesetzt (bewusst, siehe docs/o11-o18-abrechnung-labelmapping.md):
    - account.move.ref          Odoo-11-Feld reference war ungenutzt (0 Belege)
    - account.move.name         Odoo-11-Feld name hatte eine andere Bedeutung (Begruendung)
    - account.move.move_name    in name aufgegangen, kein eigenes Feld
    - account.move.payment_reference  in Odoo 11 nicht vorhanden
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (Modell, Feld) -> Odoo-11-Wortlaut
LABELS = {
    # Rechnungskopf
    ("account.move", "partner_id"): "Partner",
    ("account.move", "commercial_partner_id"): "Gewerbliche Einheit",
    ("account.move", "invoice_date"): "Rechnungsdatum",
    ("account.move", "invoice_date_due"): "Fälligkeit",
    ("account.move", "date"): "Buchungsdatum",
    ("account.move", "invoice_origin"): "Referenzbeleg",
    ("account.move", "narration"): "Weitere Informationen",
    ("account.move", "invoice_user_id"): "Verkäufer",
    ("account.move", "team_id"): "Vertriebskanal",
    ("account.move", "fiscal_position_id"): "Steuerzuordnung",
    ("account.move", "partner_bank_id"): "Bankkonto",
    ("account.move", "amount_total"): "Total",
    ("account.move", "amount_untaxed_signed"): "Nettobetrag in Unternehmenswährung",
    ("account.move", "amount_total_signed"): "Gesamtbetrag in Rechnungswährung",
    ("account.move", "amount_total_in_currency_signed"): "Gesamt (in eigener Währung)",
    ("account.move", "projectcategory_id"): "Project Category",
    ("account.move", "valorisierung_id"): "Valorisation Text",
    ("account.move", "is_move_sent"): "Gesendet",
    ("account.move", "has_reconciled_entries"): "Bezahlt/Abgestimmt",
    ("account.move", "matched_payment_ids"): "Zahlungsbuchungszeilen",
    ("account.move", "invoice_incoterm_id"): "Lieferbedingungen",
    ("account.move", "invoice_cash_rounding_id"): "Methode zur Bargeldrundung",
    # Rechnungszeile
    ("account.move.line", "move_id"): "Rechnungsreferenz",
    ("account.move.line", "name"): "Beschreibung",
    ("account.move.line", "price_unit"): "Preis pro ME",
    ("account.move.line", "price_subtotal"): "Betrag",
    ("account.move.line", "price_total"): "Betrag",
    ("account.move.line", "product_uom_id"): "Mengeneinheit",
    ("account.move.line", "purchase_line_id"): "Bestellposition",
    ("account.move.line", "sequence"): "Nummernfolge",
    ("account.move.line", "company_currency_id"): "Betriebl. Währung",
    ("account.move.line", "partner_id"): "Partner",
    ("account.move.line", "analytic_distribution"): "Kostenstelle",
    # --- Produkte (Odoo-11-Wortlaut, verkaufbare/einkaufbare Produkte) ---
    ("product.template", "barcode"): "Strichcode",
    ("product.product", "barcode"): "Strichcode",
    ("product.template", "categ_id"): "Interne Kategorie",
    ("product.product", "categ_id"): "Interne Kategorie",
    ("product.template", "cost_method"): "Kostenmethode",
    ("product.product", "cost_method"): "Kostenmethode",
    ("product.template", "description_picking"): "Beschreibung der Kommisionierung",
    ("product.product", "description_picking"): "Beschreibung der Kommisionierung",
    ("product.template", "expense_policy"): "Spesen weiter verrechnen",
    ("product.product", "expense_policy"): "Spesen weiter verrechnen",
    ("product.template", "invoice_policy"): "Fakturierungsregel",
    ("product.product", "invoice_policy"): "Fakturierungsregel",
    ("product.template", "is_multi_factor_product"): "To multiply by Factor(per 1000)",
    ("product.product", "is_multi_factor_product"): "To multiply by Factor(per 1000)",
    ("product.template", "nbr_reordering_rules"): "Meldebestände",
    ("product.product", "nbr_reordering_rules"): "Meldebestände",
    ("product.template", "orderpoint_ids"): "Meldebestandsregeln",
    ("product.product", "orderpoint_ids"): "Meldebestandsregeln",
    ("product.template", "outgoing_qty"): "Ausgehend",
    ("product.product", "outgoing_qty"): "Ausgehend",
    ("product.template", "packaging_ids"): "Produktverpackungen",
    ("product.product", "packaging_ids"): "Produktverpackungen",
    ("product.template", "partner_ref"): "Kunden Ref",
    ("product.product", "partner_ref"): "Kunden Ref",
    ("product.template", "product_type_id"): "Produktart",
    ("product.product", "product_type_id"): "Produktart",
    ("product.template", "product_variant_count"): "# Produkt Varianten",
    ("product.product", "product_variant_count"): "# Produkt Varianten",
    ("product.template", "property_account_income_id"): "Erlöskonto",
    ("product.product", "property_account_income_id"): "Erlöskonto",
    ("product.template", "property_stock_inventory"): "Lagerort Bestandsaufnahme",
    ("product.product", "property_stock_inventory"): "Lagerort Bestandsaufnahme",
    ("product.template", "property_stock_production"): "Fertigungort (virtuelles Lager)",
    ("product.product", "property_stock_production"): "Fertigungort (virtuelles Lager)",
    ("product.template", "purchase_line_warn"): "Bestellposition",
    ("product.product", "purchase_line_warn"): "Bestellposition",
    ("product.template", "purchase_ok"): "Kann eingekauft werden",
    ("product.product", "purchase_ok"): "Kann eingekauft werden",
    ("product.template", "qty_available"): "Bestandsmenge",
    ("product.product", "qty_available"): "Bestandsmenge",
    ("product.template", "sale_delay"): "Auslieferungszeit",
    ("product.product", "sale_delay"): "Auslieferungszeit",
    ("product.template", "sale_line_warn"): "Auftragsposition",
    ("product.product", "sale_line_warn"): "Auftragsposition",
    ("product.template", "sale_line_warn_msg"): "Mitteilung für Auftragszeile",
    ("product.product", "sale_line_warn_msg"): "Mitteilung für Auftragszeile",
    ("product.template", "sale_ok"): "Kann verkauft werden",
    ("product.product", "sale_ok"): "Kann verkauft werden",
    ("product.template", "sales_count"): "# Verkäufe",
    ("product.product", "sales_count"): "# Verkäufe",
    ("product.template", "sequence"): "Nummernfolge",
    ("product.product", "sequence"): "Nummernfolge",
    ("product.template", "service_type"): "Dienstleistungsverfolgung",
    ("product.product", "service_type"): "Dienstleistungsverfolgung",
    ("product.template", "supplier_taxes_id"): "Steuern (Einkauf)",
    ("product.product", "supplier_taxes_id"): "Steuern (Einkauf)",
    ("product.template", "taxes_id"): "Steuern (Verkauf)",
    ("product.product", "taxes_id"): "Steuern (Verkauf)",
    ("product.template", "uom_id"): "Mengeneinheit",
    ("product.product", "uom_id"): "Mengeneinheit",
    ("product.template", "uom_po_id"): "Einkauf ME",
    ("product.product", "uom_po_id"): "Einkauf ME",
    ("product.template", "valuation"): "Bewertung",
    ("product.product", "valuation"): "Bewertung",
    ("product.template", "warehouse_id"): "Lager",
    ("product.product", "warehouse_id"): "Lager",
    ("product.template", "lst_price"): "Verkaufspreis",
    ("product.product", "lst_price"): "Verkaufspreis",
    ("product.template", "is_product_variant"): "Ist eine Produktvariante",
    ("product.product", "is_product_variant"): "Ist eine Produktvariante",
    ("product.template", "virtual_available"): "Geplante Bestandsmenge",
    ("product.product", "virtual_available"): "Prognostizierter Bestand",
    # --- Instanzangleich lokal/VM (Befund Session 131, 07.10.2026) ---
    # Beim Beschriftungsvergleich lokal gegen VM zeigten diese Felder des Abrechnungsbereichs
    # unterschiedliche deutsche Texte. Werte: Odoo-11-Wortlaut, wo es das Feld in Odoo 11 gab,
    # sonst der Odoo-18-Standardwortlaut (dort hatte lokal einen aelteren Stand).
    ("account.move", "status_in_payment"): "Status „In Zahlung“",          # Odoo-11-Feld unbekannt; VM zeigte englisch
    ("account.move", "delivery_date"): "Liefer-/Leistungsdatum",            # Odoo-18-Standard (Odoo 11 hatte das Feld nicht)
    ("account.move", "show_delivery_date"): "Liefer-/Leistungsdatum anzeigen",
    ("res.partner", "multi_factor"): "Multiplication Factor/Thsd",          # Odoo-11-Wortlaut
    ("product.template", "rating_ids"): "Bewertung",                        # Odoo-11-Wortlaut
    ("product.template", "website_message_ids"): "Website-Nachrichten",     # Odoo-11-Wortlaut
}


def lade_env(pfad):
    werte = {}
    with open(pfad, encoding="utf-8") as fh:
        for zeile in fh:
            if "=" in zeile and not zeile.strip().startswith("#"):
                s, w = zeile.split("=", 1)
                werte[s.strip()] = w.strip().strip('"')
    return werte


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    p.add_argument("--pruefen", action="store_true")
    a = p.parse_args()
    env = lade_env(os.path.join(REPO, ".env"))
    url = "http://localhost:8069" if a.instanz == "lokal" else "https://k001959vsx.ipax.at"

    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def rufe(pfad, prm):
        req = urllib.request.Request(url + pfad, data=json.dumps({"jsonrpc": "2.0", "method": "call",
                                                                  "params": prm}).encode(),
                                     headers={"Content-Type": "application/json"})
        with op.open(req, timeout=300) as f:
            return json.loads(f.read().decode())

    rufe("/web/session/authenticate", {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"],
                                       "password": env["ODOO18_PWD"]})

    def kw(model, methode, args, **kwargs):
        o = rufe("/web/dataset/call_kw", {"model": model, "method": methode, "args": args, "kwargs": kwargs})
        if "error" in o:
            raise RuntimeError(str(o["error"])[:300])
        return o.get("result")

    print("Instanz: %s (%s)" % (a.instanz, url))
    gesetzt = abweichung = fehlt = 0
    for (modell, fname), wunsch in sorted(LABELS.items()):
        treffer = kw("ir.model.fields", "search_read",
                     [[("model", "=", modell), ("name", "=", fname)], ["id"]], context={"lang": "en_US"})
        if not treffer:
            fehlt += 1
            print("  --   %s.%s nicht vorhanden" % (modell, fname))
            continue
        fid = treffer[0]["id"]
        ist = kw("ir.model.fields", "read", [[fid], ["field_description"]], context={"lang": "de_DE"})[0]["field_description"]
        if ist == wunsch:
            continue
        if a.pruefen:
            abweichung += 1
            print("  FEHL %-42s = '%s' (erwartet '%s')" % ("%s.%s" % (modell, fname), ist, wunsch))
            continue
        kw("ir.model.fields", "write", [[fid], {"field_description": wunsch}], context={"lang": "de_DE"})
        ist2 = kw("ir.model.fields", "read", [[fid], ["field_description"]], context={"lang": "de_DE"})[0]["field_description"]
        if ist2 == wunsch:
            gesetzt += 1
            print("  OK   %-42s = '%s'" % ("%s.%s" % (modell, fname), wunsch))
        else:
            abweichung += 1
            print("  FEHL %-42s nicht gesetzt (Ist: '%s')" % ("%s.%s" % (modell, fname), ist2))
    # --- Sichtbare Bezeichnungen der Stammdaten (Entscheidungen Anna, 30.09.2026) -------------
    # Zahlungsart des Bankjournals und Name des Bankjournals sichtbar wie in Odoo 11.
    # Technische Codes (BNK1) und Feldnamen bleiben unveraendert.
    print("\nStammdaten-Bezeichnungen:")
    for code, wunsch in {"BNK1": "Bank für Tirol und Vorarlberg AG (EUR)"}.items():
        journale = kw("account.journal", "search_read",
                      [[("code", "=", code)], ["id", "name", "code"]], context={"lang": "de_DE"})
        if not journale:
            fehlt += 1
            print("  --   Journal %s nicht vorhanden" % code)
            continue
        j = journale[0]
        if j["name"] != wunsch and not a.pruefen:
            kw("account.journal", "write", [[j["id"]], {"name": wunsch}], context={"lang": "de_DE"})
            gesetzt += 1
            print("  OK   Journal %s Name = '%s'" % (code, wunsch))
        elif j["name"] != wunsch:
            abweichung += 1
            print("  FEHL Journal %s Name = '%s' (erwartet '%s')" % (code, j["name"], wunsch))
        else:
            print("  OK   Journal %s Name = '%s'" % (code, j["name"]))
    zahlungsziel = "Manuelle Zahlung (Bank)"
    zeilen = kw("account.payment.method.line", "search_read",
                [[("journal_id.code", "=", "BNK1")], ["id", "name", "journal_id"]], context={"lang": "de_DE"})
    for zeile in zeilen:
        if zeile["name"] != zahlungsziel and not a.pruefen:
            kw("account.payment.method.line", "write", [[zeile["id"]], {"name": zahlungsziel}],
               context={"lang": "de_DE"})
            gesetzt += 1
            print("  OK   Zahlungsart Zeile %s = '%s'" % (zeile["id"], zahlungsziel))
        elif zeile["name"] != zahlungsziel:
            abweichung += 1
            print("  FEHL Zahlungsart Zeile %s = '%s' (erwartet '%s')"
                  % (zeile["id"], zeile["name"], zahlungsziel))
        else:
            print("  OK   Zahlungsart Zeile %s = '%s'" % (zeile["id"], zeile["name"]))

    # --- App- und Menuebezeichnungen (Odoo-11-Wortlaut, Entscheidung Anna 30.09.2026) ----------
    # Sichtbare Bezeichnungen (de_DE) angleichen; technische Menue-IDs und Modulnamen bleiben.
    print("\nApp- und Menuebezeichnungen (Abrechnung):")

    def menue(eltern_id, namen):
        dom = [("name", "in", list(namen))]
        dom.append(("parent_id", "=", eltern_id) if eltern_id else ("parent_id", "=", False))
        treffer = kw("ir.ui.menu", "search_read", [dom, ["id", "name"]], context={"lang": "de_DE"})
        return treffer[0]["id"] if treffer else None

    # (Liste der Pfadschritte mit Auswahlnamen, Zielbezeichnung)
    pfade = [
        ([], ("Rechnungsstellung", "Abrechnung"), "Abrechnung"),
        ([("Abrechnung", "Rechnungsstellung")], ("Kunden", "Verkauf"), "Verkauf"),
        ([("Abrechnung", "Rechnungsstellung")], ("Lieferanten", "Einkauf"), "Einkauf"),
        ([("Abrechnung", "Rechnungsstellung"), ("Verkauf", "Kunden")],
         ("Gutschriften", "Kunden-Gutschriften"), "Kunden-Gutschriften"),
        ([("Abrechnung", "Rechnungsstellung"), ("Einkauf", "Lieferanten")],
         ("Rückerstattungen", "Rueckerstattungen", "Lieferanten-Gutschriften"), "Lieferanten-Gutschriften"),
        ([("Abrechnung", "Rechnungsstellung"), ("Verkauf", "Kunden")],
         ("Produkte", "Verkaufbare Produkte"), "Verkaufbare Produkte"),
        ([("Abrechnung", "Rechnungsstellung"), ("Einkauf", "Lieferanten")],
         ("Produkte", "Einkaufbare Produkte"), "Einkaufbare Produkte"),
        ([("__GLOBAL__",)], ("Buchhaltung", "Finanzen"), "Finanzen"),
        ([("__GLOBAL__",)], ("Steuerpositionen", "Steuerzuordnung"), "Steuerzuordnung"),
        ([("__GLOBAL__",)], ("Banken",), "Bankkonten"),
        ([("__GLOBAL__",)], ("Online-Zahlungen", "Zahlungen"), "Zahlungen"),
    ]
    for pfad, auswahl, ziel in pfade:
        eltern = None
        gefunden = True
        for schritt in pfad:
            if schritt == ("__GLOBAL__",):
                eltern = -1          # -1 = im gesamten Menuebaum suchen (eindeutige Namen)
                continue
            eltern = menue(eltern, schritt)
            if eltern is None:
                gefunden = False
                break
        if not gefunden:
            fehlt += 1
            beschreibung = " / ".join("|".join(s) for s in pfad) or "Wurzel"
            print("  --   Menue nicht gefunden: %s" % beschreibung)
            continue
        dom = [("name", "in", list(auswahl))]
        if eltern != -1:
            dom.append(("parent_id", "=", eltern) if eltern else ("parent_id", "=", False))
        treffer = kw("ir.ui.menu", "search_read", [dom, ["id", "name", "complete_name"]],
                     context={"lang": "de_DE"})
        if not treffer:
            fehlt += 1
            print("  --   Menue nicht vorhanden: %s (%s)"
                  % (" / ".join("|".join(s) for s in pfad), ziel))
            continue
        m = treffer[0]
        if m["name"] == ziel:
            print("  OK   Menue '%s'" % m["complete_name"])
            continue
        if a.pruefen:
            abweichung += 1
            print("  FEHL Menue '%s' heisst '%s' (erwartet '%s')" % (m["complete_name"], m["name"], ziel))
            continue
        kw("ir.ui.menu", "write", [[m["id"]], {"name": ziel}], context={"lang": "de_DE"})
        gesetzt += 1
        print("  OK   Menue '%s' -> '%s'" % (m["complete_name"], ziel))

    print("\nErgebnis: %d gesetzt, %d Abweichungen, %d nicht vorhanden%s"
          % (gesetzt, abweichung, fehlt, " (Pruefmodus)" if a.pruefen else ""))
    # --- Menueposition: Zahlungsbedingungen liegt in Odoo 11 unter Konfiguration > Verwaltung ---
    # Verwaltung ist das Menue "Verwaltung" mit dem Kind "Bargeldrundungen" (eindeutig)
    verwaltung = None
    for kandidat in kw("ir.ui.menu", "search_read",
                       [[("name", "=", "Verwaltung")], ["id", "name", "complete_name"]],
                       context={"lang": "de_DE"}):
        kinder = kw("ir.ui.menu", "search_read", [[("parent_id", "=", kandidat["id"])], ["name"]],
                    context={"lang": "de_DE"})
        if any(k["name"] in ("Bargeldrundungen", "Cash Roundings") for k in kinder):
            verwaltung = kandidat["id"]
            break
    bedingungen = None
    if verwaltung:
        t2 = kw("ir.ui.menu", "search_read",
                [[("name", "in", ("Zahlungsbedingungen", "Payment Terms"))],
                 ["id", "name", "parent_id", "complete_name"]], context={"lang": "de_DE"})
        bedingungen = t2[0] if t2 else None
    print("\nMenuepositionen:")
    if verwaltung and bedingungen:
        if bedingungen["parent_id"] and bedingungen["parent_id"][0] == verwaltung:
            print("  OK   Zahlungsbedingungen liegt unter Konfiguration > Verwaltung")
        elif a.pruefen:
            abweichung += 1
            print("  FEHL Zahlungsbedingungen liegt unter '%s' (erwartet Verwaltung)"
                  % (bedingungen["parent_id"] and bedingungen["parent_id"][1]))
        else:
            kw("ir.ui.menu", "write", [[bedingungen["id"]], {"parent_id": verwaltung}],
               context={"lang": "de_DE"})
            gesetzt += 1
            print("  OK   Zahlungsbedingungen nach Konfiguration > Verwaltung verschoben")
    else:
        fehlt += 1
        print("  --   Zahlungsbedingungen oder Verwaltung nicht gefunden")

    # --- Aktionsbezeichnung "Bankkonto hinzufuegen" (Befund Session 131, 07.10.2026) -----------
    # Beim read-only Vergleich der Menuepunkte fiel auf: die Odoo-18-Server-Aktion
    # account.action_new_bank_setting (Menue Abrechnung > Konfiguration > Bankkonten) heisst
    # lokal "Ein Bankkonto hinzufuegen", auf der VM dagegen "Bankkonto hinzufuegen" (Odoo-18-
    # Standarduebersetzung zu "Add a Bank Account"). Lokal trug also einen veralteten
    # Uebersetzungsstand. Hier wird der Standardwortlaut gesetzt, damit lokal und VM gleich sind.
    # Keine Odoo-11-Entsprechung vorhanden (Odoo 11 hatte diesen Menuepunkt nicht).
    print("\nAktionsbezeichnung 'Bankkonto hinzufuegen':")
    ziel_bank = "Bankkonto hinzufügen"
    md = kw("ir.model.data", "search_read",
            [[("module", "=", "account"), ("name", "=", "action_new_bank_setting"),
              ("model", "=", "ir.actions.server")], ["res_id", "module", "name"]])
    if not md:
        fehlt += 1
        print("  --   Server-Aktion account.action_new_bank_setting nicht gefunden")
    else:
        bank_id = md[0]["res_id"]
        ist = kw("ir.actions.server", "read", [[bank_id], ["name"]], context={"lang": "de_DE"})[0]["name"]
        if ist == ziel_bank:
            print("  OK   Server-Aktion %s de_DE = '%s'" % (bank_id, ist))
        elif a.pruefen:
            abweichung += 1
            print("  FEHL Server-Aktion %s de_DE = '%s' (erwartet '%s')" % (bank_id, ist, ziel_bank))
        else:
            kw("ir.actions.server", "write", [[bank_id], {"name": ziel_bank}], context={"lang": "de_DE"})
            gesetzt += 1
            print("  OK   Server-Aktion %s de_DE '%s' -> '%s'" % (bank_id, ist, ziel_bank))

    print("\nErgebnis: %d gesetzt, %d Abweichungen, %d nicht vorhanden%s"
          % (gesetzt, abweichung, fehlt, " (Pruefmodus)" if a.pruefen else ""))
    return 0 if abweichung == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
