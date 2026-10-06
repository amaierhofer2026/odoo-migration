"""Vergleich der Produkt-Ansichten (Liste, Suche, Kanban) und der beiden Menueaktionen.

Odoo 11 read-only. Aufruf: python scripts/vergleich_produkt_ansichten.py o11|lokal|vm
Ausgabe: normalisierte Textliste (Listenspalten, Suchfilter, Gruppierungen, Kanbanfelder,
Menueaktionen) zum zeilenweisen Vergleich zweier Instanzen.
"""
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

inst = sys.argv[1] if len(sys.argv) > 1 else "lokal"
k = o11() if inst == "o11" else o18(inst)
CTX = {"lang": "de_DE"}


def arch(vtyp):
    """Zusammengefuehrter Arch einer Ansicht (O11: fields_view_get, O18: get_views)."""
    if inst == "o11":
        try:
            return k.kw("product.template", "fields_view_get", [False, vtyp], context=CTX)["arch"]
        except Exception as e:
            return "FEHLER: %s" % str(e)[:80]
    try:
        r = k.kw("product.template", "get_views", [[[False, vtyp]]], context=CTX)
        return r["views"][vtyp]["arch"]
    except Exception as e:
        return "FEHLER: %s" % str(e)[:80]


def felder(a, tag="field"):
    return re.findall(r'<field name="([^"]+)"', a)


print("=== Instanz=%s ===" % inst)
for vtyp in ("list" if inst != "o11" else "tree", "search", "kanban"):
    a = arch(vtyp)
    print("\n--- %s ---" % vtyp)
    if a.startswith("FEHLER"):
        print("   ", a)
        continue
    if vtyp == "search":
        print("   Felder      :", felder(a))
        print("   Filter      :", re.findall(r'<filter[^>]*name="([^"]+)"[^>]*string="([^"]*)"', a)[:40])
        print("   Gruppierungen:", re.findall(r'<filter[^>]*name="([^"]+)"[^>]*context="\{\'group_by\': \'([^\']+)\'"', a))
    else:
        print("   Felder      :", felder(a))
    print("   Buttons     :", re.findall(r'<button[^>]*name="([^"]+)"', a))
    print("   Arch-Laenge :", len(a))

# Menueaktionen
print("\n--- Menueaktionen ---")
for mname in ("Verkaufbare Produkte", "Einkaufbare Produkte"):
    m = k.kw("ir.ui.menu", "search_read", [[["name", "=", mname]], ["name", "action", "complete_name"]],
             context=CTX)
    if not m:
        print("   %s: kein Menue" % mname)
        continue
    akt = k.kw("ir.actions.act_window", "read", [[int(m[0]["action"].split(",")[1])],
                                                 ["name", "res_model", "view_mode", "domain", "context",
                                                  "search_view_id", "view_ids", "limit"]], context=CTX)[0]
    print("   %s (%s)" % (mname, m[0]["complete_name"]))
    for feld in ("name", "res_model", "view_mode", "domain", "context", "limit"):
        print("      %-12s %s" % (feld, akt.get(feld)))
    vids = k.kw("ir.actions.act_window.view", "search_read", [[["act_window_id", "=", akt["id"]]],
                                                              ["sequence", "view_mode", "view_id"]], context=CTX)
    print("      view_ids     %s" % sorted([(v["sequence"], v["view_mode"], v["view_id"]) for v in vids]))
    if akt.get("search_view_id"):
        print("      search_view  %s" % (akt["search_view_id"],))
