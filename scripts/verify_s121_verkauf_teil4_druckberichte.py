"""Prueflauf Verkauf Teil 4: Druckberichte in Odoo 11 <-> Odoo 18.

Prueft:
  Odoo 11 (ausschliesslich lesend)
    - die drei Report-Aktionen auf sale.order (Name, Reportname, Bindung ins Drucken-Menue)
    - die aktiv verwendeten Feldbezuege der ITK-Dokumentvorlage (ohne HTML-Kommentare)
  Odoo 18 lokal und VM
    - die vier Report-Aktionen auf sale.order sind vorhanden und gebunden
      (keine Odoo-18-Berichtsaktion wurde entfernt)
    - Zuordnung der Odoo-11-Berichte: ITK-Dokumentbericht und Proformarechnung sind abgedeckt
    - die Odoo-11-Feldgruppen sind in der Odoo-18-ITK-Vorlage enthalten
    - Hinweis (kein Fehler): die Odoo-18-Vorlage report_itk_saleorder_proforma ist vorhanden,
      aber nicht an eine Report-Aktion gebunden; das Menue nutzt den Odoo-18-Standardbericht.

Aufruf:
    python scripts/verify_s121_verkauf_teil4_druckberichte.py
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18
from analyse_verkauf_teil4_druckberichte import musterbefunde

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP = {"lang": "de_DE"}

# Odoo-11-Druckberichte (Name -> Reportname) und ihre Entsprechung in Odoo 18
O11_BERICHTE = {
    "Angebot/Auftrag": "sale.report_itk_saleorder",
    "Angebot / Auftrag ORG": "sale.report_itk_saleorder",
    "Proformarechnung": "sale.report_itk_saleorder_proforma",
}
O18_BERICHTE = {
    "Angebot/Auftrag": "sale.report_saleorder_raw",
    "ITK-Angebot/Auftrag": "itk_reports.report_itk_saleorder",
    "PDF-Angebot": "sale.report_saleorder",
    "PRO-FORMA-Rechnung": "sale.report_saleorder_pro_forma",
}


def ohne_kommentare(arch: str) -> str:
    return re.sub(r"<!--.*?-->", "", arch or "", flags=re.S)


def hole(client, key):
    vs = client.kw("ir.ui.view", "search_read", [[("key", "=", key)], ["id", "arch_db"]], context=SP)
    return max((v["arch_db"] or "" for v in vs), key=len) if vs else ""


def main() -> int:
    ok = fehler = 0

    def pruefe(bedingung, text):
        nonlocal ok, fehler
        if bedingung:
            ok += 1
            print("  OK   %s" % text)
        else:
            fehler += 1
            print("  FEHL %s" % text)

    print("Prueflauf Verkauf Teil 4 (Druckberichte)")
    print("Odoo 11 Prod wird ausschliesslich lesend gelesen.")

    print("\n--- Odoo 11 Prod: vorhandene und gebundene Verkaufsberichte ---")
    k11 = o11()
    meldungen11 = k11.kw("ir.actions.report", "search_read",
                         [[("model", "=", "sale.order")],
                          ["name", "report_name", "binding_type", "binding_model_id", "report_type"]],
                         context=SP)
    namen11 = {m["name"]: m for m in meldungen11}
    for name, report_name in O11_BERICHTE.items():
        m = namen11.get(name)
        pruefe(bool(m) and m["report_name"] == report_name,
               "Odoo 11: Bericht '%s' -> %s" % (name, report_name))
    gebunden11 = [m["name"] for m in meldungen11 if m["binding_model_id"]]
    print("       im Drucken-Menue gebunden: %s" % gebunden11)
    pruefe("Angebot/Auftrag" in gebunden11, "Odoo 11: 'Angebot/Auftrag' ist an das Menue gebunden")
    pruefe("Proformarechnung" in gebunden11, "Odoo 11: 'Proformarechnung' ist an das Menue gebunden")
    arch11 = ohne_kommentare(hole(k11, "sale.report_itk_saleorder_document"))
    felder11 = musterbefunde(arch11)
    print("       aktive Vorlage: %d Zeichen" % len(arch11))
    for gruppe, f in felder11.items():
        print("         %-10s %s" % (gruppe, ", ".join(f) or "-"))
    texte11 = set(re.findall(r">([^<>{}]{3,120})<", arch11))

    for schluessel, client, name in (("lokal", o18("lokal"), "Odoo 18 lokal"), ("vm", o18("vm"), "Odoo 18 VM")):
        print("\n--- %s: Druckberichte ---" % name)
        meldungen = client.kw("ir.actions.report", "search_read",
                              [[("model", "=", "sale.order")],
                               ["name", "report_name", "binding_type", "binding_model_id",
                                "report_type"]], context=SP)
        namen = {m["name"]: m for m in meldungen}
        gebunden = [m["name"] for m in meldungen if m["binding_model_id"]]
        print("       Meldungen: %s" % list(namen))
        print("       im Drucken-Menue gebunden: %s" % gebunden)
        for bericht, report_name in O18_BERICHTE.items():
            pruefe(bericht in namen and namen[bericht]["report_name"] == report_name,
                   "Bericht '%s' -> %s vorhanden" % (bericht, report_name))
            pruefe(bericht in gebunden, "Bericht '%s' ist im Menue Drucken gebunden" % bericht)
        pruefe(len(gebunden) >= 4, "keine Odoo-18-Berichtsaktion entfernt (%d gebunden)" % len(gebunden))

        arch18 = ohne_kommentare(hole(client, "itk_reports.report_itk_saleorder_document"))
        felder18 = musterbefunde(arch18)
        print("       ITK-Vorlage: %d Zeichen" % len(arch18))
        # In Odoo 18 kommen einzelne Bezuege aus Standardbausteinen:
        #  company_id            -> externes Layout (Briefkopf/Fuss)
        #  amount_untaxed/_total -> Steuer-Summenblock (account.document_tax_totals ueber doc.tax_totals)
        #  amount_by_group       -> Steuerzeilen des Summenblocks
        #  pricelist_id          -> Waehrung ueber doc.currency_id
        ueber_standardblock = {"company_id", "amount_untaxed", "amount_total", "amount_by_group",
                               "pricelist_id"}
        for gruppe, f in felder11.items():
            fehlt = sorted(set(f) - set(felder18[gruppe]))
            ueber_block = [x for x in fehlt if x in ueber_standardblock]
            echtes_fehlen = [x for x in fehlt if x not in ueber_standardblock]
            pruefe(not echtes_fehlen, "Odoo-11-Feldgruppe '%s' in der Odoo-18-Vorlage abgedeckt%s"
                   % (gruppe, "" if not echtes_fehlen else " (fehlt: %s)" % echtes_fehlen))
            for x in ueber_block:
                print("       %s: in Odoo 18 ueber den Standardblock abgedeckt "
                      "(externes Layout bzw. Steuer-Summenblock)" % x)
        pruefe("web.external_layout" in arch18, "Odoo-18-Vorlage nutzt das externe Layout (Firma/Adresse/Fuss)")
        pruefe("account.document_tax_totals" in arch18 or "tax_totals" in arch18,
               "Odoo-18-Vorlage nutzt den Steuer-Summenblock (Netto/Steuer/Gesamt)")
        pruefe("doc.state" in arch18, "Angebots-/Auftragstitel haengt am Status")
        for text in ("Zu Handen", "Zahlung", "Bearbeiter/in", "Währung", "Ihre UID-Nr.",
                     "Leistungsgegenstand", "Einzelpreis", "Gesamtpreis", "Steuerzuordnungshinweis"):
            pruefe(text in arch18, "Textbaustein '%s' in der Odoo-18-Vorlage" % text)

        # Zuordnung der Odoo-11-Berichte
        pruefe(namen.get("ITK-Angebot/Auftrag", {}).get("report_name") == "itk_reports.report_itk_saleorder",
               "ITK-Dokumentbericht aus Odoo 11 abgedeckt (ITK-Angebot/Auftrag)")
        pruefe(namen.get("PRO-FORMA-Rechnung", {}).get("report_name") == "sale.report_saleorder_pro_forma",
               "Proformarechnung aus Odoo 11 abgedeckt (PRO-FORMA-Rechnung)")

        # ITK-Proformavorlage vorhanden, aber nicht gebunden -> Hinweis
        vorlage = client.kw("ir.ui.view", "search_read",
                            [[("key", "=", "itk_reports.report_itk_saleorder_proforma")], ["id"]],
                            context=SP)
        pruefe(bool(vorlage), "ITK-Proformavorlage in Odoo 18 vorhanden")
        geprueft = [m["name"] for m in meldungen
                    if m["report_name"] == "itk_reports.report_itk_saleorder_proforma"]
        if geprueft:
            print("       Hinweis: ITK-Proformavorlage ist an '%s' gebunden" % geprueft)
        else:
            print("       Hinweis: ITK-Proformavorlage ist nicht an eine Report-Aktion gebunden; "
                  "das Menue Drucken nutzt den Odoo-18-Standardbericht PRO-FORMA-Rechnung")

    print("\nOdoo 11 Prod wurde ausschliesslich lesend verwendet.")
    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
