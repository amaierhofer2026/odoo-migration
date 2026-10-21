"""Read-only: gerenderte Ansicht (form/tree/search/kanban) eines Modells je Instanz.

Aufruf: python scripts/hr_gerenderte_ansicht.py o11|lokal|vm <modell> <typ>
Schreibt das Arch nach %LOCALAPPDATA%\\Temp\\hr_erhebung\\arch_<instanz>_<modell>_<typ>.xml
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

ZIEL = os.path.join(os.environ.get("LOCALAPPDATA", "."), "Temp", "hr_erhebung")


def arch(k, modell, typ, ist_o11):
    if ist_o11:
        res = k.kw(modell, "fields_view_get", [False, typ], context={"lang": "de_DE"})
        return res["arch"]
    res = k.kw(modell, "get_views", [[[False, typ]]], context={"lang": "de_DE"})
    return res["views"][typ]["arch"]


def haupt():
    instanz, modell, typ = sys.argv[1], sys.argv[2], sys.argv[3]
    k = o11() if instanz == "o11" else o18(instanz)
    text = arch(k, modell, typ, instanz == "o11")
    os.makedirs(ZIEL, exist_ok=True)
    name = "arch_%s_%s_%s.xml" % (instanz, modell.replace(".", "_"), typ)
    pfad = os.path.join(ZIEL, name)
    with open(pfad, "w", encoding="utf-8") as fh:
        fh.write(text)
    print("%s %s/%s: %d Zeichen -> %s" % (instanz, modell, typ, len(text), pfad))


if __name__ == "__main__":
    haupt()
