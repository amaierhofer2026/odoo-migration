"""Helpdesk Odoo 11 - Teil 3: Verteilungen (search_count) und Ansichtsarchitekturen (read-only).

Aufruf: python scripts/erhebe_helpdesk_o11_teil3.py [--ordner PFAD]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11

STD = os.path.join(os.environ.get("USERPROFILE", "."), "Desktop",
                   "Odoo18-Helpdesk-Session132", "rohdaten")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ordner", default=STD)
    a = ap.parse_args()
    os.makedirs(a.ordner, exist_ok=True)
    cli = o11()
    d = {}

    print("=== Verteilungen website.support.ticket (search_count) ===")
    def zaehle(feld, werte):
        for wert in werte:
            dom = [(feld, "=", wert)] if wert is not None else [(feld, "=", False)]
            try:
                n = cli.kw("website.support.ticket", "search_count", [dom])
            except Exception as exc:  # noqa: BLE001
                n = "FEHLER %s" % str(exc)[:80]
            print("   %-24s %-46s %s" % (feld, str(wert)[:46], n))
            d.setdefault("verteilung", {}).setdefault(feld, []).append([wert, n])

    st = cli.kw("website.support.ticket.states", "search_read", [[]], fields=["id", "name"], limit=0)
    kat = cli.kw("website.support.ticket.categories", "search_read", [[]], fields=["id", "name"], limit=0)
    sub = cli.kw("website.support.ticket.subcategory", "search_read", [[]],
                 fields=["id", "name", "parent_category_id"], limit=0)
    prio = cli.kw("website.support.ticket.priority", "search_read", [[]], fields=["id", "name"], limit=0)
    print(" -- nach Stufe")
    zaehle("state", [s["id"] for s in st] + [False])
    print(" -- nach Kategorie")
    zaehle("category", [k["id"] for k in kat] + [False])
    print(" -- nach Unterkategorie")
    zaehle("sub_category_id", [s["id"] for s in sub] + [False])
    print(" -- nach Prioritaet")
    zaehle("priority_id", [p["id"] for p in prio] + [False])
    print(" -- nach Kanal")
    zaehle("channel", ["Email", "Manual", "Website (Public)", "Website (User)", False])
    print(" -- nach SLA-Aktiv")
    zaehle("sla_active", [True, False])
    print(" -- Gesamtzahl")
    print("   ", cli.kw("website.support.ticket", "search_count", [[]]))
    print(" -- mit Bearbeiter / ohne")
    for dom, titel in ([[("user_id", "!=", False)], "mit Bearbeiter"],
                       [[("user_id", "=", False)], "ohne Bearbeiter"],
                       [[("partner_id", "!=", False)], "mit Partner"],
                       [[("partner_id", "=", False)], "ohne Partner"],
                       [[("support_rating", ">", 0)], "mit Bewertung"],
                       [[("close_date", "!=", False)], "mit Abschlussdatum"],
                       [[("analytic_account_id", "!=", False)], "mit analytischem Konto"]):
        print("   %-24s %s" % (titel, cli.kw("website.support.ticket", "search_count", [dom])))
        d.setdefault("kennzahlen", {})[titel] = cli.kw("website.support.ticket", "search_count", [dom])

    print("\n=== Ansichtsarchitekturen website.support.ticket ===")
    views = cli.kw("ir.ui.view", "search_read",
                   [[("model", "=", "website.support.ticket")]],
                   fields=["id", "name", "type", "priority", "mode", "inherit_id", "arch_db"],
                   order="type, priority", limit=0)
    d["views"] = views
    for v in views:
        print("\n########## [%s] %s (id %s, %s, prio %s) inherit=%s" % (
            v["type"], v["name"], v["id"], v["mode"], v["priority"], v["inherit_id"] or "-"))
        print(v["arch_db"])

    print("\n=== Ansichten der Hilfsmodelle (tree/form/search) ===")
    for modell in ("website.support.ticket.states", "website.support.ticket.categories",
                   "website.support.ticket.subcategory", "website.support.ticket.priority",
                   "website.support.ticket.tag", "website.support.sla",
                   "website.support.ticket.compose", "website.support.ticket.close"):
        for v in cli.kw("ir.ui.view", "search_read", [[("model", "=", modell)]],
                        fields=["id", "name", "type", "arch_db"], limit=0):
            print("\n########## [%s] %s (id %s)" % (v["type"], v["name"], v["id"]))
            print(v["arch_db"])
            d.setdefault("hilfsansichten", []).append(v)

    pfad = os.path.join(a.ordner, "helpdesk_o11_teil3.json")
    with open(pfad, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1, sort_keys=True)
    print("\nRohdaten:", pfad)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
