"""Kontrolle: Nur der Menuepunkt Einkaufbare Produkte hat eine gebundene Liste bekommen.

Aufruf: python scripts/pruefe_produktlisten_unveraendert.py
Prueft (read-only, lokal und VM) fuer alle Produkt-Menuepunkte, welche Liste an der Aktion haengt.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o18  # noqa: E402

CTX = {"lang": "de_DE"}
AKTIONEN = {
    382: "Abrechnung > Verkauf > Verkaufbare Produkte",
    383: "Abrechnung > Einkauf > Einkaufbare Produkte",
    166: "Verkauf > Katalog > Produkte",
    392: "Lager > Stammdaten > Produkte",
    1105: "Abonnements > Abonnement Produkte",
    167: "Verkauf > Katalog > Preislisten",
}

for inst in ("lokal", "vm"):
    k = o18(inst)
    print("=== %s ===" % inst)
    for aid, name in AKTIONEN.items():
        try:
            akt = k.kw("ir.actions.act_window", "read", [[aid], ["name", "res_model", "view_mode"]],
                       context=CTX)[0]
        except Exception as e:
            print("  %-44s Aktion %s nicht vorhanden (%s)" % (name, aid, str(e)[:40]))
            continue
        av = k.kw("ir.actions.act_window.view", "search_read",
                  [[["act_window_id", "=", aid]], ["view_mode", "view_id", "sequence"]], context=CTX)
        if akt["res_model"] != "product.template":
            print("  %-44s Aktion %-5s Modell %-17s gebundene Listen: %s (Standardliste nicht geprueft)"
                  % (name, aid, akt["res_model"],
                     [(v["view_mode"], v["view_id"][0]) for v in av] or "keine"))
            continue
        r = k.kw("product.template", "get_views", [[[False, "list"]]], context=CTX)
        views = r.get("views", {})
        standard = views["list"]["id"]
        print("  %-44s Aktion %-5s Modell %-17s gebundene Listen: %-40s Standardliste: %s"
              % (name, aid, akt["res_model"],
                 [(v["view_mode"], v["view_id"][0]) for v in av] or "keine", standard))
