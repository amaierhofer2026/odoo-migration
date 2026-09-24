"""Read-only Bestandsaufnahme Verkauf: Menuebaum Odoo 11 Prod gegen Odoo 18.

Aufruf:
    python scripts/analyse_verkauf_menue.py            # beide Instanzen, Menuebaum
    python scripts/analyse_verkauf_menue.py --json      # zusaetzlich Daten in docs/_verkauf_menue_daten.json

Odoo 11 Prod wird ausschliesslich lesend verwendet.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o11, o18

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def menuebaum(k, wurzel_namen) -> list:
    """Rekursiver Menuebaum ab den Menues mit den angegebenen Namen."""
    alle = k.kw("ir.ui.menu", "search_read", [[], ["name", "parent_id", "sequence", "action", "groups_id"]],
                context={"lang": "de_DE"})
    kinder = {}
    for m in alle:
        pid = m["parent_id"][0] if m["parent_id"] else False
        kinder.setdefault(pid, []).append(m)
    for v in kinder.values():
        v.sort(key=lambda x: (x["sequence"], x["id"]))

    def baum(mid):
        knoten = []
        for m in kinder.get(mid, []):
            aktion = None
            if m["action"]:
                art, aid = m["action"].split(",")
                aktion = {"art": art, "id": int(aid)}
                if art in ("ir.actions.act_window", "ir.actions.server", "ir.actions.client", "ir.actions.report"):
                    modell = {"ir.actions.act_window": "ir.actions.act_window",
                              "ir.actions.server": "ir.actions.server",
                              "ir.actions.client": "ir.actions.client",
                              "ir.actions.report": "ir.actions.report"}[art]
                    felder = ["name"]
                    if art == "ir.actions.act_window":
                        felder += ["res_model", "view_type", "domain", "context"]
                    else:
                        felder += ["model_name"] if art == "ir.actions.server" else []
                    try:
                        d = k.kw(modell, "read", [[int(aid)], felder], context={"lang": "de_DE"})
                        aktion.update(d[0])
                    except Exception as fehler:  # pragma: no cover
                        aktion["fehler"] = str(fehler)[:120]
            knoten.append({
                "id": m["id"], "name": m["name"], "sequence": m["sequence"],
                "aktion": aktion, "gruppen": [g for g in (m["groups_id"] or [])],
                "kinder": baum(m["id"]),
            })
        return knoten

    ergebnis = []
    for m in alle:
        if not m["parent_id"] and m["name"] in wurzel_namen:
            ergebnis.append(baum(m["id"]))
    return ergebnis


def drucke(knoten, tiefe=0):
    for n in knoten:
        a = n["aktion"] or {}
        zusatz = ""
        if a:
            zusatz = "  [%s %s%s%s]" % (a.get("art", "?"), a.get("id", ""),
                                        " -> " + a.get("name", "") if a.get("name") else "",
                                        " (%s)" % a.get("res_model") if a.get("res_model") else "")
        print("%s- %s%s" % ("   " * tiefe, n["name"], zusatz))
        drucke(n["kinder"], tiefe + 1)


def zaehle(knoten) -> int:
    return sum(1 + zaehle(n["kinder"]) for n in knoten)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true")
    a = p.parse_args()

    e = lade_env()
    k11 = o11()
    k18 = o18("lokal")
    daten = {}

    for name, client, wurzeln in (("o11", k11, ("Verkauf",)), ("o18", k18, ("Verkauf",))):
        print("\n================ %s ================" % name.upper())
        baeume = menuebaum(client, wurzeln)
        daten[name] = baeume
        for b in baeume:
            print("Menues gesamt: %d" % zaehle(b))
            drucke(b)

    if a.json:
        ziel = os.path.join(REPO, "docs", "_verkauf_menue_daten.json")
        with open(ziel, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(daten, fh, ensure_ascii=False, indent=1, sort_keys=True)
        print("\nDaten: %s" % ziel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
