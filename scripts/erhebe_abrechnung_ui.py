"""Abrechnung: Menuebaum, Filter, Gruppierungen und Suchfelder in Odoo 11 und Odoo 18 erheben.

Odoo 11 wird ausschliesslich gelesen. Ausgabe: kompakte Gegenueberstellung auf der Konsole und
vollstaendige Rohdaten als JSON (Temp-Ordner) fuer die weitere Umsetzung.

Aufruf:  python scripts/erhebe_abrechnung_ui.py
"""
from __future__ import annotations

import collections
import json
import os
import re
import sys
import tempfile
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18

ERGEBNIS = {}


def mengebaum(k, wurzel_ids, tiefe=0, max_tiefe=3, out=None):
    out = out if out is not None else []
    for m in k.kw("ir.ui.menu", "read", [wurzel_ids, ["id", "name", "complete_name", "child_id",
                                                      "action", "parent_id", "sequence"]],
                  context={"lang": "de_DE"}):
        out.append({"id": m["id"], "tiefe": tiefe, "name": m["name"],
                    "pfad": m["complete_name"], "aktion": (m.get("action") or "")[:60]})
        if m.get("child_id") and tiefe < max_tiefe:
            mengebaum(k, m["child_id"], tiefe + 1, max_tiefe, out)
    return out


def suchelemente(k, modell):
    """Filter, Gruppierungen und Suchfelder aller Suchansichten eines Modells."""
    views = k.kw("ir.ui.view", "search_read",
                 [[("model", "=", modell), ("type", "=", "search")], ["id", "name", "arch_db", "active"]],
                 context={"lang": "de_DE"})
    filter_, gruppen, felder = [], [], []
    for v in views:
        arch = v.get("arch_db") or ""
        try:
            wurzel = ET.fromstring(arch)
        except ET.ParseError:
            continue
        for e in wurzel.iter():
            tag = e.tag.split("}")[-1]
            if tag in ("filter", "groupby"):
                name = e.get("name") or e.get("string") or ""
                if name:
                    filter_.append({"ansicht": v["name"], "name": name,
                                    "domain": (e.get("domain") or "")[:160],
                                    "context": (e.get("context") or "")[:120]})
            if tag == "field" and (e.get("name") or ""):
                felder.append({"ansicht": v["name"], "feld": e.get("name"),
                               "string": e.get("string") or ""})
    return {"filter": filter_, "gruppen": gruppen, "suchfelder": felder}


def main() -> int:
    k11, k18 = o11(), o18("lokal")

    # ---------- Menuebaeume ----------
    print("=== Odoo 11: Menues zum Bereich Abrechnung ===")
    w11 = k11.kw("ir.ui.menu", "search_read",
                 [[("name", "ilike", "abrechnung")], ["id", "name", "complete_name", "child_id"]],
                 context={"lang": "de_DE"})
    baum11 = []
    if w11:
        baum11 = mengebaum(k11, [w11[0]["id"]])
        print("Wurzel: %s (id %s)" % (w11[0]["name"], w11[0]["id"]))
        for m in baum11:
            print("   " + "   " * m["tiefe"] + "%s%s" % ("- " if m["tiefe"] else "", m["name"]))
    ERGEBNIS["menue_o11"] = baum11

    print("\n=== Odoo 18: Menues zum Bereich Abrechnung ===")
    w18 = k18.kw("ir.ui.menu", "search_read",
                 [[("name", "in", ["Rechnungsstellung", "Abrechnung", "Accounting"])],
                  ["id", "name", "complete_name", "child_id"]], context={"lang": "de_DE"})
    baum18 = []
    for w in w18:
        if w["name"] in ("Rechnungsstellung", "Abrechnung"):
            baum18 = mengebaum(k18, [w["id"]])
            print("Wurzel: %s (id %s)" % (w["name"], w["id"]))
            for m in baum18:
                print("   " + "   " * m["tiefe"] + "%s%s" % ("- " if m["tiefe"] else "", m["name"]))
    ERGEBNIS["menue_o18"] = baum18

    # ---------- Filter und Gruppierungen ----------
    print("\n=== Filter/Suchfelder: Odoo 11 account.invoice ===")
    s11 = suchelemente(k11, "account.invoice")
    for f in s11["filter"]:
        print("   Filter: %-28s domain=%s" % (f["name"], f["domain"]))
    print("   Suchfelder: %s" % ", ".join(sorted({x["feld"] for x in s11["suchfelder"]})))
    ERGEBNIS["filter_o11_invoice"] = s11

    print("\n=== Filter/Suchfelder: Odoo 18 account.move ===")
    s18 = suchelemente(k18, "account.move")
    for f in s18["filter"]:
        print("   Filter: %-28s domain=%s" % (f["name"], f["domain"]))
    print("   Suchfelder: %s" % ", ".join(sorted({x["feld"] for x in s18["suchfelder"]})))
    ERGEBNIS["filter_o18_move"] = s18

    # ---------- Odoo-11-Filter auch aus ir.filters (benutzerdefinierte Filter) ----------
    print("\n=== Odoo 11 zusaetzliche Filter (ir.filters) ===")
    if11 = []
    for f in k11.kw("ir.filters", "search_read", [[], ["name", "model_id", "domain", "context"]],
                    context={"lang": "de_DE"}):
        if f["model_id"] in ("account.invoice", "account.move", "account.payment"):
            if11.append(f)
            print("   %-40s %s domain=%s" % (f["name"], f["model_id"], (f["domain"] or "")[:120]))
    ERGEBNIS["ir_filters_o11"] = if11
    if18 = []
    for f in k18.kw("ir.filters", "search_read", [[], ["name", "model_id", "domain"]],
                    context={"lang": "de_DE"}):
        if f["model_id"] in ("account.move", "account.payment"):
            if18.append(f)
    ERGEBNIS["ir_filters_o18"] = if18
    print("   Odoo 18 eigene Filter: %d" % len(if18))

    ziel = os.path.join(tempfile.gettempdir(), "abrechnung_ui.json")
    with open(ziel, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(ERGEBNIS, fh, ensure_ascii=False, indent=1, default=str)
    print("\nRohdaten: %s" % ziel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
