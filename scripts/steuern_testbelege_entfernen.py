"""Entfernt die Steuer-Testbelege (Marker 'ITK-STEUERTEST') restlos aus der Testinstanz.

Sucht unabhaengig vom Protokoll alle Belege mit Referenz/Bezeichnung 'ITK-STEUERTEST' und entfernt
sie (gebucht -> Entwurf -> geloescht). Nur die Testdatenbank ist erlaubt.

Aufruf: python scripts/steuern_testbelege_entfernen.py --instanz lokal|vm
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o18  # noqa: E402

ZIEL_DB = "odoo18_test"
CTX = {"lang": "de_DE"}
MARKER = "ITK-STEUERTEST"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    a = p.parse_args()
    env = lade_env()
    if env.get("ODOO18_DB") != ZIEL_DB:
        raise SystemExit("ABBRUCH: Ziel-DB ist %r, erlaubt ist nur %r." % (env.get("ODOO18_DB"), ZIEL_DB))
    k = o18(a.instanz)
    ids = k.kw("account.move", "search", [[("|"), ("ref", "ilike", MARKER),
                                          ("invoice_line_ids.name", "ilike", MARKER)]], context=CTX)
    print("Ziel: %s (%s) | gefundene Testbelege: %s" % (a.instanz, ZIEL_DB, ids))
    entfernt = 0
    for mid in ids:
        b = k.kw("account.move", "read", [[mid], ["name", "state", "ref"]], context=CTX)[0]
        if b["state"] != "draft":
            try:
                k.kw("account.move", "button_draft", [[mid]], context=CTX)
            except Exception as fehler:
                print("   Hinweis %s: %s" % (b["name"], str(fehler)[:120]))
        try:
            k.kw("account.move", "unlink", [[mid]], context=CTX)
            entfernt += 1
            print("   entfernt: %s (%s)" % (b["name"], b["ref"]))
        except Exception as fehler:
            print("   FEHLER beim Entfernen von %s: %s" % (b["name"], str(fehler)[:200]))
    rest = k.kw("account.move", "search_count", [[("ref", "ilike", MARKER)]], context=CTX)
    print("Entfernt: %d | Rest mit Marker: %d" % (entfernt, rest))
    return 0 if rest == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
