"""O11/O18: welche Ansicht haengt an der Aktion des Menuepunkts 'Einkaufbare Produkte'.

Aufruf: python scripts/pruefe_aktion_ansicht_einkauf.py o11|lokal|vm
Zeigt action.view_id, action.view_ids, die Roharchs und den zusammengefuehrten Arch.
"""
from __future__ import annotations

import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

inst = sys.argv[1] if len(sys.argv) > 1 else "lokal"
k = o11() if inst == "o11" else o18(inst)
CTX = {"lang": "de_DE"}
LISTENTYP = "tree" if inst == "o11" else "list"

print("=== Instanz=%s ===" % inst)
m = k.kw("ir.ui.menu", "search_read",
         [[["name", "ilike", "Einkaufbare Produkte"]], ["name", "complete_name", "action"]],
         context=CTX)
aid = int(m[0]["action"].split(",")[1])
print("Menue: %s -> Aktion %s" % (m[0]["complete_name"], aid))

felder = ["name", "res_model", "view_mode", "view_id", "domain", "context", "limit",
          "search_view_id", "filter", "target"]
if inst != "o11":
    felder = [f for f in felder if f != "view_id"]
akt = k.kw("ir.actions.act_window", "read", [[aid], felder], context=CTX)[0]
for f, w in akt.items():
    print("  %-14s %s" % (f, w))

vid = akt.get("view_id") and akt["view_id"][0]
print("\nview_id (Hauptliste): %s" % vid)
if vid:
    v = k.kw("ir.ui.view", "read", [[vid], ["name", "model", "type", "mode", "priority",
                                            "inherit_id", "xml_id", "arch"]], context=CTX)[0]
    for f in ("name", "model", "type", "mode", "priority", "xml_id"):
        print("  %-12s %s" % (f, v[f]))
    print("\n--- Roharch der Ansicht %s ---" % vid)
    print(v["arch"])

# zusammengefuehrter Arch der Aktionsansicht
model = akt["res_model"]
try:
    if inst == "o11":
        zus = k.kw(model, "fields_view_get", [vid or False, LISTENTYP], context=CTX)
    else:
        zus = k.kw(model, "get_views", [[[vid or False, LISTENTYP]]], context=CTX)
    arch = zus["arch"] if inst == "o11" else zus["views"][LISTENTYP]["arch"]
    print("\n--- zusammengefuehrter Arch (Dokumentreihenfolge) ---")
    for i, f in enumerate(ET.fromstring(arch).iter("field"), 1):
        print("  %2d. %-28s string=%-22s invisible=%-8s optional=%-6s attrs=%s" % (
            i, f.get("name"), f.get("string"), f.get("invisible"), f.get("optional"),
            (f.get("attrs") or "")[:50]))
except Exception as e:
    print("  Arch nicht lesbar: %s" % str(e)[:200])
