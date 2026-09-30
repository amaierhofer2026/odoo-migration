"""Read-only Bestandsaufnahme Abrechnung: Menuebaum Odoo 11 Prod gegen Odoo 18.

Aufruf:
    python scripts/analyse_abrechnung_menue.py             # Menuebaum lokal
    python scripts/analyse_abrechnung_menue.py --instanz vm
    python scripts/analyse_abrechnung_menue.py --json       # Rohdaten nach %TEMP%

Odoo 11 Prod wird ausschliesslich lesend verwendet.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o11, o18

WURZEL = {"o11": "Abrechnung", "o18": "Rechnungsstellung"}


def menuebaum(k, wurzel_namen):
    alle = k.kw("ir.ui.menu", "search_read",
                [[], ["name", "parent_id", "sequence", "action", "groups_id"]],
                context={"lang": "de_DE"})
    kinder = {}
    for m in alle:
        pid = m["parent_id"][0] if m["parent_id"] else False
        kinder.setdefault(pid, []).append(m)
    for v in kinder.values():
        v.sort(key=lambda x: (x["sequence"], x["id"]))

    def aktion_info(m):
        if not m["action"]:
            return None
        art, aid = m["action"].split(",")
        aid = int(aid)
        info = {"art": art, "id": aid}
        if art == "ir.actions.act_window":
            try:
                d = k.kw("ir.actions.act_window", "read", [[aid],
                         ["name", "res_model", "view_mode", "domain", "context"]],
                         context={"lang": "de_DE"})[0]
                info.update(d)
            except Exception as fehler:
                info["fehler"] = str(fehler)[:120]
        elif art == "ir.actions.server":
            try:
                d = k.kw("ir.actions.server", "read", [[aid], ["name", "model_name"]],
                         context={"lang": "de_DE"})[0]
                info.update(d)
            except Exception as fehler:
                info["fehler"] = str(fehler)[:120]
        elif art == "ir.actions.client":
            try:
                d = k.kw("ir.actions.client", "read", [[aid], ["name", "tag"]],
                         context={"lang": "de_DE"})[0]
                info.update(d)
            except Exception as fehler:
                info["fehler"] = str(fehler)[:120]
        elif art == "ir.actions.report":
            try:
                d = k.kw("ir.actions.report", "read", [[aid], ["name", "model"]],
                         context={"lang": "de_DE"})[0]
                info.update(d)
            except Exception as fehler:
                info["fehler"] = str(fehler)[:120]
        return info

    def baum(mid):
        knoten = []
        for m in kinder.get(mid, []):
            knoten.append({"id": m["id"], "name": m["name"], "sequence": m["sequence"],
                           "aktion": aktion_info(m), "kinder": baum(m["id"])})
        return knoten

    return [baum(m["id"]) for m in alle if not m["parent_id"] and m["name"] in wurzel_namen]


def drucke(knoten, tiefe=0):
    for n in knoten:
        a = n["aktion"] or {}
        zusatz = ""
        if a:
            zusatz = "  [%s %s%s%s%s]" % (
                a.get("art", "?"), a.get("id", ""),
                " -> " + str(a.get("name")) if a.get("name") else "",
                " (%s)" % a.get("res_model") if a.get("res_model") else
                (" (%s)" % a.get("model_name") if a.get("model_name") else
                 (" (%s)" % a.get("model") if a.get("model") else "")),
                " view=%s" % a.get("view_mode") if a.get("view_mode") else "")
        print("%s- %s%s" % ("   " * tiefe, n["name"], zusatz))
        drucke(n["kinder"], tiefe + 1)


def zaehle(knoten):
    return sum(1 + zaehle(n["kinder"]) for n in knoten)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true")
    p.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    a = p.parse_args()

    lade_env()
    verbindungen = [("o11", o11(), (WURZEL["o11"],)),
                    ("o18_" + a.instanz, o18(a.instanz), (WURZEL["o18"],))]
    daten = {}
    for name, client, wurzeln in verbindungen:
        print("\n================ %s  (Wurzel: %s) ================" % (name.upper(), wurzeln[0]))
        baeume = menuebaum(client, wurzeln)
        daten[name] = baeume
        for b in baeume:
            print("Menues gesamt (inkl. Wurzel): %d" % (zaehle(b) + 1))
            drucke(b)

    if a.json:
        ziel = os.path.join(tempfile.gettempdir(), "abrechnung_menue_daten.json")
        with open(ziel, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(daten, fh, ensure_ascii=False, indent=1, sort_keys=True)
        print("\nRohdaten (nicht im Repo): %s" % ziel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
