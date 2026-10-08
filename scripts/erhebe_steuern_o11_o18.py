"""Read-only Erhebung Steuern: Odoo 11 gegen Odoo 18 (Bereich Abrechnung > Konfiguration > Steuern).

Erhebt je System alle Steuern mit den vom Auftrag geforderten Merkmalen und die tatsaechliche
Verwendung (Produkte, Belegzeilen, Buchungszeilen, Steuerzuordnungen). Es wird NICHTS geschrieben.

Aufruf: python scripts/erhebe_steuern_o11_o18.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}
ZIEL = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session131", "steuern")
MERKMALE = ["id", "name", "description", "type_tax_use", "amount", "amount_type", "price_include",
            "tax_group_id", "sequence", "active", "account_id", "refund_account_id",
            "include_base_amount", "tax_scope"]


def steuern(k, bezeichnung):
    vorhanden = k.kw("account.tax", "fields_get", [[], ["type", "relation"]], context=CTX)
    felder = [f for f in MERKMALE if f in vorhanden]
    print("   %s Felder vorhanden: %s" % (bezeichnung, felder))
    daten = k.kw("account.tax", "search_read", [[], felder], context=CTX, limit=0)
    # Repartitionszeilen (Odoo 18 fuehrt die Steuerkonten dort, Odoo 11 hat account_id/refund_account_id)
    rep_felder = [f for f in ("invoice_repartition_line_ids", "refund_repartition_line_ids")
                  if f in vorhanden]
    if rep_felder:
        ids = [t["id"] for t in daten]
        for t in daten:
            t["_repartitionen"] = []
        for feld in rep_felder:
            zeilen = k.kw("account.tax.repartition.line", "search_read",
                          [[("tax_id", "in", ids)], ["tax_id", "repartition_type", "factor_percent",
                                                     "account_id", "use_in_tax_closing"]],
                          context=CTX, limit=0)
            for z in zeilen:
                for t in daten:
                    if t["id"] == z["tax_id"][0]:
                        t["_repartitionen"].append({"art": feld, "typ": z["repartition_type"],
                                                    "anteil": z["factor_percent"],
                                                    "konto": z["account_id"]})
    return daten


def verwendung(k, ist_o11):
    """Verwendung je Steuer: Produkte (Verkauf/Einkauf), Belegzeilen.

    Odoo 11 liefert m2m-Felder im search_read nur als ID-Liste - deshalb wird ueber eine
    ID-Name-Zuordnung der Steuern ausgezaehlt.
    """
    steuer_namen = {t["id"]: t["name"] for t in
                    k.kw("account.tax", "search_read", [[], ["name"]], context=CTX, limit=0)}
    aus = {}
    for feld, art in (("taxes_id", "sale"), ("supplier_taxes_id", "purchase")):
        schluessel = "produkte_" + art
        for pr in k.kw("product.template", "search_read", [[(feld, "!=", False)], [feld]],
                       context=CTX, limit=0):
            for eintrag in (pr.get(feld) or []):
                tid = eintrag[0] if isinstance(eintrag, (list, tuple)) else eintrag
                e = aus.setdefault(steuer_namen.get(tid, "id %s" % tid), {})
                e[schluessel] = e.get(schluessel, 0) + 1
    if ist_o11:
        zeilen_modell, zeilen_feld = "account.invoice.line", "invoice_line_tax_ids"
    else:
        zeilen_modell, zeilen_feld = "account.move.line", "tax_ids"
    for tid, tname in steuer_namen.items():
        n = k.kw(zeilen_modell, "search_count", [[(zeilen_feld, "in", [tid])]], context=CTX)
        if n:
            aus.setdefault(tname, {})["belegzeilen"] = n
    return aus


def steuerzuordnungen(k):
    """Steuerzuordnung: account.fiscal.position mit Steuerabbildungen."""
    vorhanden = k.kw("account.fiscal.position", "fields_get", [[], ["type", "relation"]], context=CTX)
    feld = "tax_ids" if "tax_ids" in vorhanden else None
    positionen = k.kw("account.fiscal.position", "search_read",
                      [[], ["name", "auto_apply", "country_id"] + ([feld] if feld else [])],
                      context=CTX, limit=0)
    aus = []
    for p in positionen:
        eintrag = {"name": p["name"], "auto_apply": p.get("auto_apply"),
                   "land": p.get("country_id"), "abbildungen": []}
        if feld and p.get(feld):
            abb = k.kw("account.fiscal.position.tax", "read", [p[feld], ["tax_src_id", "tax_dest_id"]],
                       context=CTX)
            eintrag["abbildungen"] = [{"von": a["tax_src_id"], "nach": a["tax_dest_id"]} for a in abb]
        aus.append(eintrag)
    return aus


def main() -> int:
    os.makedirs(ZIEL, exist_ok=True)
    k11, k18 = o11(), o18("lokal")
    daten = {}
    print("=== Odoo 11: Steuern ===", flush=True)
    daten["o11_steuern"] = steuern(k11, "Odoo 11")
    print("   Anzahl: %d" % len(daten["o11_steuern"]))
    print("\n=== Odoo 11: Verwendung ===", flush=True)
    daten["o11_verwendung"] = verwendung(k11, True)
    print("   Steuern mit Verwendung: %d" % len(daten["o11_verwendung"]))
    print("\n=== Odoo 11: Steuerzuordnungen (Fiscal Positions) ===", flush=True)
    daten["o11_zuordnungen"] = steuerzuordnungen(k11)
    for p in daten["o11_zuordnungen"]:
        print("   %-45s auto=%s Land=%s Abbildungen=%d" % (p["name"][:45], p["auto_apply"], p["land"],
                                                          len(p["abbildungen"])))

    print("\n=== Odoo 18 lokal: Steuern ===", flush=True)
    daten["o18_steuern"] = steuern(k18, "Odoo 18")
    print("   Anzahl: %d" % len(daten["o18_steuern"]))
    print("\n=== Odoo 18 lokal: Verwendung ===", flush=True)
    daten["o18_verwendung"] = verwendung(k18, False)
    print("   Steuern mit Verwendung: %d" % len(daten["o18_verwendung"]))
    print("\n=== Odoo 18 lokal: Steuerzuordnungen (Fiscal Positions) ===", flush=True)
    daten["o18_zuordnungen"] = steuerzuordnungen(k18)
    for p in daten["o18_zuordnungen"]:
        print("   %-45s auto=%s Land=%s Abbildungen=%d" % (p["name"][:45], p["auto_apply"], p["land"],
                                                          len(p["abbildungen"])))

    p = os.path.join(ZIEL, "steuern_rohdaten.json")
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(daten, fh, ensure_ascii=False, indent=1, default=str)
    print("\nRohdaten: %s" % p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
