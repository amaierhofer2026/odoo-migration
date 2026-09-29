"""Detailvergleich der Druckberichtsvorlagen (Verkauf) in Odoo 11 und Odoo 18.

Sucht alle QWeb-Vorlagen zu den Verkaufsberichten, folgt der Vererbungskette
(primäre Vorlage -> Dokumentvorlage) und vergleicht die fachlichen Feldbezuege:
Kunde/Adresse, Positionen, Preise, Steuern, Summen, Status, Kopf/Fuss, Kanaele.

Ergebnis: docs/_verkauf_teil4_druckberichte_vorlagen.json (gitignoriert)

Aufruf:
    python scripts/analyse_verkauf_teil4_druckberichte_vorlagen.py
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

FELD_MUSTER = {
    "kunde": [r"partner_id", r"partner_shipping_id", r"partner_invoice_id", r"commercial_partner_id"],
    "adresse": [r"\.street", r"\.street2", r"\.city", r"\.zip", r"\.country_id", r"\.vat", r"\.phone",
                r"\.email", r"\.lang"],
    "positionen": [r"order_line", r"product_id", r"product_uom_qty", r"product_uom\b", r"\.name\b",
                   r"price_unit", r"discount"],
    "steuern": [r"tax_id", r"taxes", r"amount_tax", r"tax_totals"],
    "summen": [r"amount_untaxed", r"amount_total", r"amount_%", r"currency_id"],
    "status": [r"\bstate\b", r"date_order", r"validity_date", r"confirmation_date", r"locked"],
    "kopf_fuss": [r"company_id", r"user_id", r"note\b", r"payment_term_id", r"incoterm", r"narration"],
    "kanaele": [r"team_id", r"source_id", r"campaign_id", r"medium_id", r"itk"],
    "zusatz": [r"pro.?forma", r"proforma", r"leistungszeitraum", r"vokz", r"peppol", r"uid"],
}


def felder(arch: str) -> dict:
    arch = arch or ""
    return {g: sorted({m.replace("\\b", "") for m in muster if re.search(m, arch)}) for g, muster in FELD_MUSTER.items()}


def erhebe(client) -> dict:
    vorlagen = client.kw("ir.ui.view", "search_read",
                         [[("type", "=", "qweb"),
                           "|", ("key", "ilike", "saleorder"), ("key", "ilike", "sale_order"),
                           ],
                          ["id", "name", "key", "inherit_id", "arch_db", "priority", "mode", "active"]],
                         context=SP)
    daten = []
    namen = {}
    for v in vorlagen:
        v = dict(v)
        arch = v.pop("arch_db") or ""
        iid = v["inherit_id"]
        if isinstance(iid, (list, tuple)):
            iid = iid[0]
        v["inherit_id"] = iid or None
        v["erbt_von"] = None
        if iid:
            if iid not in namen:
                treffer = client.kw("ir.ui.view", "read", [[iid], ["name", "key"]], context=SP)
                namen[iid] = (treffer[0].get("key") or treffer[0]["name"]) if treffer else str(iid)
            v["erbt_von"] = namen[iid]
        v["arch_zeichen"] = len(arch)
        v["felder"] = felder(arch)
        v["arch_kurz"] = re.sub(r"\s+", " ", arch.strip())[:1200]
        v["hat_body"] = bool(re.search(r"<t t-call|<div class=\"page\"|o_report", arch))
        daten.append(v)
    return daten


def main() -> int:
    ergebnis = {}
    for name, client in (("o11", o11()), ("o18lokal", o18("lokal")), ("o18vm", o18("vm"))):
        print("erhebe %s ..." % name)
        ergebnis[name] = erhebe(client)
        for v in ergebnis[name]:
            print("  %-34s %-40s zeichen=%-6s erbt_von=%s" % (
                (v["key"] or "-")[:34], (v["name"] or "-")[:40], v["arch_zeichen"], v["erbt_von"]))
    ziel = os.path.join(REPO, "docs", "_verkauf_teil4_druckberichte_vorlagen.json")
    with open(ziel, "w", encoding="utf-8") as fh:
        json.dump(ergebnis, fh, ensure_ascii=False, indent=1)
    print("\nRohdaten: %s" % ziel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
