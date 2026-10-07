"""Vollstaendige Suchansicht des Menuepunkts 'Einkaufbare Produkte' ausgeben (nur lesend).

Aufruf: python scripts/dump_suchansicht_einkauf.py o11|lokal|vm [datei]
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

inst = sys.argv[1] if len(sys.argv) > 1 else "lokal"
k = o11() if inst == "o11" else o18(inst)
CTX = {"lang": "de_DE"}
MODELL = "product.product" if inst == "o11" else "product.template"

if inst == "o11":
    arch = k.kw(MODELL, "fields_view_get", [False, "search"], context=CTX)["arch"]
else:
    arch = k.kw(MODELL, "get_views", [[[False, "search"]]], context=CTX)["views"]["search"]["arch"]

zeilen = ["=== Instanz=%s Suchansicht %s ===" % (inst, MODELL), arch, "", "--- Auswertung ---"]
zeilen.append("Suchfelder : %s" % re.findall(r'<field name="([^"]+)"', arch))
zeilen.append("Filter     : %s" % re.findall(r'<filter[^>]*string="([^"]*)"', arch))
zeilen.append("Gruppierung: %s" % re.findall(r"group_by'\s*:\s*'([^']+)'", arch))
zeilen.append("qty-Domaenen: %s" % re.findall(r"qty_available'[^)]*\)", arch))
zeilen.append("Favoritenfelder (is_favorite): %s" % ("is_favorite" in arch))
text = "\n".join(zeilen)
print(text)
if len(sys.argv) > 2:
    with open(sys.argv[2], "w", encoding="utf-8") as fh:
        fh.write(text)
    print("\n[gespeichert: %s]" % sys.argv[2])
