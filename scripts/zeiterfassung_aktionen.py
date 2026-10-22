"""Fensteraktionen der Zeiterfassung im Detail (read-only).

Aufruf:
  python scripts/zeiterfassung_aktionen.py --quelle o11|lokal|vm --ids 406,407,...
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

IDS = {
    "o11": [406, 407, 408, 409, 410, 411, 412, 413, 415, 459, 479, 483, 484, 485, 486, 505],
    "lokal": [1187, 1190, 1193, 1194, 1195, 1196, 1202, 1574, 1341, 1450],
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quelle", required=True, choices=["o11", "lokal", "vm"])
    ap.add_argument("--ids", default="")
    a = ap.parse_args()
    cli = o11() if a.quelle == "o11" else o18(a.quelle)
    ids = [int(x) for x in a.ids.split(",")] if a.ids else IDS.get(a.quelle, [])
    felder = ["id", "name", "res_model", "view_mode", "view_ids", "domain", "context",
              "search_view_id", "limit", "help", "target"]
    for i in ids:
        try:
            rec = cli.kw("ir.actions.act_window", "read", [i], fields=felder,
                         context={"lang": "de_DE"})
        except Exception as exc:  # noqa: BLE001
            print("[%s] FEHLER %s" % (i, str(exc)[:160]))
            continue
        if not rec:
            print("[%s] nicht vorhanden" % i)
            continue
        r = rec[0]
        print("\n[%s] %s  (res_model=%s, view_mode=%s)" % (i, r["name"], r["res_model"], r["view_mode"]))
        print("   domain : %s" % (r["domain"] or ""))
        print("   context: %s" % (r["context"] or ""))
        print("   search_view_id: %s" % (r["search_view_id"] or ""))
        print("   limit: %s   target: %s" % (r["limit"], r.get("target")))
        if r.get("help"):
            print("   help: %s" % str(r["help"])[:120])
        if r.get("view_ids"):
            vs = cli.kw("ir.actions.act_window.view", "read", [r["view_ids"]],
                        fields=["sequence", "view_mode", "view_id", "act_window_id"])
            for v in sorted(vs, key=lambda x: x["sequence"]):
                print("   view: seq=%s %-7s -> %s" % (v["sequence"], v["view_mode"], v["view_id"]))
        else:
            print("   view: keine expliziten view_ids (Standardansichten)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
