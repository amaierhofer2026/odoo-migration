"""Read-only Menuebaum-Dump fuer den Bereich Personal - Odoo 11 und Odoo 18 (lokal/vm).

Aufruf: python scripts/hr_menuebaum.py o11|lokal|vm
Schreibt JSON nach %LOCALAPPDATA%\\Temp\\hr_erhebung\\menue_<instanz>.json, gibt den Baum aus.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

ZIEL = os.path.join(os.environ.get("LOCALAPPDATA", "."), "Temp", "hr_erhebung")
CTX = {"lang": "de_DE"}
FELDER = ["id", "name", "parent_id", "sequence", "action", "web_icon", "groups_id"]


def hole(k, instanz):
    alle = k.kw("ir.ui.menu", "search_read", [[]], fields=FELDER, context=CTX, order="sequence,id")
    print("%s: %d Menues gesamt" % (instanz, len(alle)))
    return alle


def baum(alle):
    kinder = {}
    for m in alle:
        pid = m["parent_id"][0] if m["parent_id"] else None
        kinder.setdefault(pid, []).append(m)
    for pid in kinder:
        kinder[pid].sort(key=lambda x: (x["sequence"], x["id"]))
    return kinder


def zeige(kinder, pid, tiefe=0, max_tiefe=6):
    for m in kinder.get(pid, []):
        akt = m["action"] or ""
        print("%s%s (id %s, seq %s)%s" % ("   " * tiefe, m["name"], m["id"], m["sequence"],
                                          ("  -> " + akt) if akt else ""))
        if tiefe < max_tiefe:
            zeige(kinder, m["id"], tiefe + 1, max_tiefe)


def haupt():
    instanz = sys.argv[1] if len(sys.argv) > 1 else "o11"
    k = o11() if instanz == "o11" else o18(instanz)
    alle = hole(k, instanz)
    os.makedirs(ZIEL, exist_ok=True)
    with open(os.path.join(ZIEL, "menue_%s.json" % instanz), "w", encoding="utf-8") as fh:
        json.dump(alle, fh, ensure_ascii=False, indent=1, default=str)
    kinder = baum(alle)
    print("\n=== WURZELN (Apps) ===")
    for m in kinder.get(None, []):
        print("  %s (id %s, seq %s)" % (m["name"], m["id"], m["sequence"]))
    # Personal-Wurzel finden
    for m in kinder.get(None, []):
        if m["name"].strip().lower() in ("personal", "mitarbeiter", "employees"):
            print("\n=== BAUM UNTER %s (id %s) ===" % (m["name"], m["id"]))
            zeige(kinder, m["id"])


if __name__ == "__main__":
    haupt()
