"""Abrechnung: vollstaendiger Menuebaum Odoo 11 vs Odoo 18, Filter, Gruppierungen, Suchfelder.

Odoo 11 nur lesend. Aufruf: python scripts/erhebe_abrechnung_menue.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18


def baum(k, ids, tiefe=0, tiefe_max=4, out=None):
    out = [] if out is None else out
    if not ids or tiefe > tiefe_max:
        return out
    for m in k.kw("ir.ui.menu", "read", [ids, ["id", "name", "sequence", "child_id", "action"]],
                  context={"lang": "de_DE"}):
        out.append({"id": m["id"], "tiefe": tiefe, "name": m["name"], "seq": m["sequence"],
                    "aktion": (m.get("action") or "")[:70]})
        baum(k, m.get("child_id") or [], tiefe + 1, tiefe_max, out)
    return out


def suchelemente(k, modell):
    views = k.kw("ir.ui.view", "search_read",
                 [[("model", "=", modell), ("type", "=", "search")], ["id", "name", "arch_db", "active"]],
                 context={"lang": "de_DE"})
    filter_, gruppen, felder = [], [], []
    for v in views:
        if not v.get("arch_db"):
            continue
        try:
            wurzel = ET.fromstring(v["arch_db"])
        except ET.ParseError:
            continue
        for e in wurzel.iter():
            tag = e.tag.split("}")[-1]
            if tag == "filter":
                filter_.append({"name": e.get("name") or "", "string": e.get("string") or "",
                                "domain": (e.get("domain") or "")[:150],
                                "context": (e.get("context") or "")[:100],
                                "ansicht": v["name"]})
            elif tag == "groupby":
                gruppen.append({"name": e.get("name") or "", "string": e.get("string") or "",
                                "ansicht": v["name"]})
            elif tag == "field" and e.get("name"):
                felder.append({"feld": e.get("name"), "string": e.get("string") or "",
                               "ansicht": v["name"]})
    return {"ansichten": [v["name"] for v in views], "filter": filter_, "gruppen": gruppen,
            "suchfelder": felder}


def zeige(titel, eintraege, schluessel):
    print("%s (%d):" % (titel, len(eintraege)))
    for e in eintraege:
        print("   %-32s %s" % (e[schluessel][:32], e.get("domain", e.get("string", ""))[:100]))


def main() -> int:
    k11, k18 = o11(), o18("lokal")
    daten = {}

    print("=== Odoo 11: Wurzeln mit Namen Abrechnung/Buchhaltung ===")
    w11 = k11.kw("ir.ui.menu", "search_read",
                 [[("name", "in", ["Abrechnung", "Buchhaltung"]), ("parent_id", "=", False)],
                  ["id", "name", "child_id"]], context={"lang": "de_DE"})
    for w in w11:
        print("   id=%-5s %s (%d Untermenues)" % (w["id"], w["name"], len(w["child_id"] or [])))
    daten["wurzeln_o11"] = w11
    baum11 = []
    for w in w11:
        print("--- Odoo 11 Baum: %s ---" % w["name"])
        b = baum(k11, [w["id"]])
        for m in b:
            print("   " + "  " * m["tiefe"] + "%s" % m["name"])
        baum11.extend(b)
    daten["menue_o11"] = baum11

    print("\n=== Odoo 18: Wurzelmenue der Rechnungsstellung ===")
    w18 = k18.kw("ir.ui.menu", "search_read",
                 [[("parent_id", "=", False), ("name", "in", ["Rechnungsstellung", "Abrechnung", "Accounting"])],
                  ["id", "name", "child_id"]], context={"lang": "de_DE"})
    for w in w18:
        print("   id=%-5s %s (%d Untermenues)" % (w["id"], w["name"], len(w["child_id"] or [])))
    daten["wurzeln_o18"] = w18
    baum18 = []
    for w in w18:
        print("--- Odoo 18 Baum: %s ---" % w["name"])
        b = baum(k18, [w["id"]])
        for m in b:
            print("   " + "  " * m["tiefe"] + "%s" % m["name"])
        baum18.extend(b)
    daten["menue_o18"] = baum18

    print("\n=== Odoo 11 account.invoice: Filter ===")
    s11 = suchelemente(k11, "account.invoice")
    zeige("Filter", s11["filter"], "name")
    zeige("Gruppierungen", s11["gruppen"], "name")
    print("Suchfelder: %s" % sorted({x["feld"] for x in s11["suchfelder"]}))
    daten["o11_invoice"] = s11

    print("\n=== Odoo 18 account.move: Filter ===")
    s18 = suchelemente(k18, "account.move")
    zeige("Filter", s18["filter"], "name")
    zeige("Gruppierungen", s18["gruppen"], "name")
    print("Suchfelder: %s" % sorted({x["feld"] for x in s18["suchfelder"]}))
    daten["o18_move"] = s18

    print("\n=== Odoo 18 account.payment: Filter ===")
    p18 = suchelemente(k18, "account.payment")
    zeige("Filter", p18["filter"], "name")
    print("Suchfelder: %s" % sorted({x["feld"] for x in p18["suchfelder"]}))
    daten["o18_payment"] = p18

    print("\n=== Odoo 11 account.payment: Filter ===")
    p11 = suchelemente(k11, "account.payment")
    zeige("Filter", p11["filter"], "name")
    print("Suchfelder: %s" % sorted({x["feld"] for x in p11["suchfelder"]}))
    daten["o11_payment"] = p11

    ziel = os.path.join(tempfile.gettempdir(), "abrechnung_menue.json")
    with open(ziel, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(daten, fh, ensure_ascii=False, indent=1, default=str)
    print("\nRohdaten: %s" % ziel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
