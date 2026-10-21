"""Read-only: Feldbelegung hr.employee in Odoo 11 (wie viele der 25 Datensaetze haben einen Wert).
Schreibt JSON nach %LOCALAPPDATA%\\Temp\\hr_erhebung\\o11_feldbelegung.json und gibt eine Tabelle aus."""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11  # noqa: E402

ZIEL = os.path.join(os.environ.get("LOCALAPPDATA", "."), "Temp", "hr_erhebung")
CTX = {"lang": "de_DE"}
TECH = {"id", "create_date", "create_uid", "write_date", "write_uid", "__last_update",
        "display_name", "message_ids", "message_follower_ids", "message_channel_ids",
        "message_partner_ids", "message_is_follower", "message_needaction",
        "message_needaction_counter", "message_unread", "message_unread_counter",
        "message_last_post", "website_message_ids", "image", "image_medium", "image_small",
        "color", "resource_id"}


def haupt():
    k = o11()
    f = k.kw("hr.employee", "fields_get", [[], ["string", "type", "relation", "selection"]],
             context=CTX)
    felder = [n for n, d in f.items() if n not in TECH and d.get("type") not in ("binary",)]
    ids = k.kw("hr.employee", "search", [[]], context=dict(CTX, active_test=False))
    daten = k.kw("hr.employee", "read", [ids, felder], context=dict(CTX, active_test=False))
    belegung = {}
    for name in felder:
        werte = []
        for d in daten:
            w = d.get(name)
            if w in (False, None, "", [], {}):
                continue
            werte.append(w)
        belegung[name] = {"anzahl": len(werte), "beispiele": werte[:6]}
    with open(os.path.join(ZIEL, "o11_feldbelegung.json"), "w", encoding="utf-8") as fh:
        json.dump(belegung, fh, ensure_ascii=False, indent=1, default=str)
    print("%-28s %-10s %-5s %s" % ("Feld", "Typ", "belegt", "Beispiele (max 6)"))
    for name in sorted(belegung, key=lambda n: (-belegung[n]["anzahl"], n)):
        b = belegung[name]
        if b["anzahl"] == 0:
            continue
        print("%-28s %-10s %-5d %s" % (name, f[name].get("type"), b["anzahl"],
                                       str(b["beispiele"])[:110]))
    leer = [n for n in belegung if belegung[n]["anzahl"] == 0]
    print("\nUNBELEGT (%d): %s" % (len(leer), ", ".join(sorted(leer))))


if __name__ == "__main__":
    haupt()
