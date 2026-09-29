"""Inhaltsvergleich der ITK-Verkaufsberichte Odoo 11 <-> Odoo 18 (ohne HTML-Kommentare).

Die Odoo-11-Vorlage enthaelt viel auskommentierten Code des alten Standardberichts. Fuer den
fachlichen Vergleich werden HTML-Kommentare vorher entfernt, sonst entstehen Scheindifferenzen.

Verglichen wird:
  Odoo 11: sale.report_itk_saleorder_document          (aktiver Teil)
  Odoo 18: itk_reports.report_itk_saleorder_document   (aktiver Teil)
  zusaetzlich die Proforma-Vorlagen beider Instanzen.

Ergebnis: docs/_verkauf_teil4_itk_bericht_vergleich_aktiv.json (gitignoriert)

Aufruf:
    python scripts/vergleiche_verkauf_teil4_itk_bericht_aktiv.py
"""
from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP = {"lang": "de_DE"}

PAARE = [
    ("Hauptbericht (Angebot/Auftrag)",
     "sale.report_itk_saleorder_document", "itk_reports.report_itk_saleorder_document"),
    ("Proformarechnung",
     "sale.report_itk_saleorder_proforma", "itk_reports.report_itk_saleorder_proforma"),
]
FELDER = {
    "kunde": [r"partner_id", r"partner_shipping_id", r"partner_invoice_id", r"commercial_partner_id",
              r"community_salutation", r"attention_of"],
    "adresse": [r"partner_id\.street", r"partner_id\.street2", r"partner_id\.zip", r"partner_id\.city",
                r"partner_id\.country_id", r"partner_id\.vat", r"partner_id\.lang", r"partner_id\.phone",
                r"partner_id\.email"],
    "positionen": [r"order_line", r"product_id", r"product_uom_qty", r"product_uom", r"\bl\.name\b",
                   r"price_unit", r"\bdiscount\b", r"\bl\.number\b", r"price_subtotal", r"display_type"],
    "steuern": [r"tax_id", r"taxes", r"amount_tax", r"tax_totals", r"document_tax_totals"],
    "summen": [r"amount_untaxed", r"amount_total", r"amount_by_group", r"currency_id", r"pricelist_id"],
    "status": [r"doc\.state", r"date_order", r"validity_date", r"confirmation_date", r"\blocked\b"],
    "kopf_fuss": [r"company_id", r"user_id", r"\bnote\b", r"payment_term_id", r"incoterm", r"narration",
                  r"fiscal_position_id"],
    "kanaele": [r"team_id", r"source_id", r"campaign_id", r"medium_id"],
}


def ohne_kommentare(arch: str) -> str:
    return re.sub(r"<!--.*?-->", "", arch or "", flags=re.S)


def baue(arch: str) -> dict:
    arch = ohne_kommentare(arch)
    felder = {g: sorted({m.replace("\\b", "").replace("\\", "") for m in muster if re.search(m, arch)})
              for g, muster in FELDER.items()}
    texte = [re.sub(r"\s+", " ", re.sub(r"&[a-z]+;", " ", t)).strip()
             for t in re.findall(r">([^<>{}]{3,140})<", arch)]
    texte = [t for t in texte if t and not t.startswith(("t-", "/"))]
    kopf = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", k)).strip()
            for k in re.findall(r"<th[^>]*>(.*?)</th>", arch, flags=re.S)]
    return {"zeichen_aktiv": len(arch),
            "felder": felder,
            "texte": sorted(set(texte)),
            "kopfzeilen": [k for k in kopf if k],
            "status_werte": sorted(set(re.findall(r"state (?:not )?in \[([^\]]*)\]", arch))),
            "t_calls": sorted(set(re.findall(r't-call="([^"]+)"', arch))),
            "tabellen": len(re.findall(r"<table", arch))}


def hole(client, key):
    vs = client.kw("ir.ui.view", "search_read", [[("key", "=", key)], ["id", "name", "arch_db"]], context=SP)
    return max((v["arch_db"] or "" for v in vs), key=len) if vs else ""


def main() -> int:
    k11, k18 = o11(), o18("lokal")
    ergebnis = {}
    fehler = 0
    for titel, key11, key18 in PAARE:
        a, b = baue(hole(k11, key11)), baue(hole(k18, key18))
        ergebnis[titel] = {"o11": a, "o18": b, "keys": [key11, key18]}
        print("=== %s ===" % titel)
        print("   aktiv: O11 %d Zeichen / O18 %d Zeichen" % (a["zeichen_aktiv"], b["zeichen_aktiv"]))
        for g in FELDER:
            fa, fb = a["felder"][g], b["felder"][g]
            fehlt = sorted(set(fa) - set(fb))
            if fehlt:
                fehler += 1
                print("   %-10s FEHLT in O18: %s" % (g, ", ".join(fehlt)))
            else:
                print("   %-10s abgedeckt (%d Bezuege)" % (g, len(fa)))
        nur11 = sorted(set(a["texte"]) - set(b["texte"]))
        nur18 = sorted(set(b["texte"]) - set(a["texte"]))
        print("   Texte nur O11: %s" % (nur11 or "-"))
        print("   Texte nur O18: %s" % (nur18 or "-"))
        print("   Spaltenkoepfe O11: %s" % a["kopfzeilen"])
        print("   Spaltenkoepfe O18: %s" % b["kopfzeilen"])
        print("   Statusbezuege O11: %s | O18: %s" % (a["status_werte"], b["status_werte"]))
        print("   t-call O11: %s | O18: %s" % (a["t_calls"], b["t_calls"]))
        print("   Tabellen O11 %d / O18 %d" % (a["tabellen"], b["tabellen"]))

    ziel = os.path.join(REPO, "docs", "_verkauf_teil4_itk_bericht_vergleich_aktiv.json")
    with open(ziel, "w", encoding="utf-8") as fh:
        json.dump(ergebnis, fh, ensure_ascii=False, indent=1)
    print("\nFachliche Luecken (Felder, die in Odoo 11 aktiv sind und in Odoo 18 fehlen): %d" % fehler)
    print("Rohdaten: %s" % ziel)
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
