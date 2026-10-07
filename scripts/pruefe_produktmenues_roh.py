"""Roharchs und Aktionsbindung der Produktmenues (Verkaufbar/Einkaufbar) auf beiden Seiten.

Aufruf: python scripts/pruefe_produktmenues_roh.py o11|lokal|vm [datei]
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

inst = sys.argv[1] if len(sys.argv) > 1 else "lokal"
k = o11() if inst == "o11" else o18(inst)
CTX = {"lang": "de_DE"}
MODELL = "product.product" if inst == "o11" else "product.template"
LISTE = "tree" if inst == "o11" else "list"

zeilen = []


def schreibe(t=""):
    zeilen.append(t)
    print(t)


schreibe("=== Instanz=%s ===" % inst)

for name in ("Verkaufbare Produkte", "Einkaufbare Produkte"):
    m = k.kw("ir.ui.menu", "search_read",
             [[["name", "=", name]], ["name", "complete_name", "action"]], context=CTX)
    if not m:
        schreibe("\n%s: kein Menue" % name)
        continue
    aid = int(m[0]["action"].split(",")[1])
    felder = ["name", "res_model", "view_mode", "domain", "context", "limit", "search_view_id"]
    if inst == "o11":
        felder.append("view_id")
    akt = k.kw("ir.actions.act_window", "read", [[aid], felder], context=CTX)[0]
    schreibe("\n=== %s -> Aktion %s ===" % (m[0]["complete_name"], aid))
    for f, w in akt.items():
        schreibe("  %-14s %s" % (f, w))
    vids = k.kw("ir.actions.act_window.view", "search_read",
                [[["act_window_id", "=", aid]], ["view_mode", "view_id", "sequence"]], context=CTX)
    schreibe("  view_ids      %s" % [(v["sequence"], v["view_mode"], v["view_id"]) for v in vids])

# Suchansicht im Rohzustand
schreibe("\n--- Suchansicht %s (Roharch, primaere Ansichten) ---" % MODELL)
for v in k.kw("ir.ui.view", "search_read",
              [[["model", "=", MODELL], ["type", "=", "search"], ["mode", "=", "primary"]],
               ["name", "xml_id", "priority", "arch"]], context=CTX):
    schreibe("\n### id=%s prio=%s %s (%s)" % (v["id"], v["priority"], v["name"], v["xml_id"]))
    schreibe(v["arch"])

schreibe("\n--- Ansichten, die Feldbeschriftungen (string=) auf %s setzen ---" % MODELL)
alle = k.kw("ir.ui.view", "search_read",
            [[["model", "=", MODELL]], ["name", "type", "mode", "xml_id", "arch"]], context=CTX)
for v in alle:
    arch = v["arch"] or ""
    import re
    treffer = re.findall(r'<field name="([^"]+)"[^>]*string="([^"]+)"', arch)
    if treffer:
        schreibe("  %-8s %-10s id=%-6s %-44s %s" % (v["type"], v["mode"], v["id"], (v["name"] or "")[:44],
                                                     ", ".join("%s=%s" % t for t in treffer)))

if len(sys.argv) > 2:
    with open(sys.argv[2], "w", encoding="utf-8") as fh:
        fh.write("\n".join(zeilen))
    print("\n[gespeichert: %s]" % sys.argv[2])
