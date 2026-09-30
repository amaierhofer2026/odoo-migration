"""Read-only Bestandsaufnahme Abrechnung: Menuebaum Odoo 11 Prod gegen Odoo 18.

WICHTIG: liest Menues mit context ir.ui.menu.full_list=True - ohne das filtert
ir.ui.menu._search nach Sichtbarkeit fuer den angemeldeten Benutzer und der Baum
waere unvollstaendig.

Aufruf:
    python scripts/analyse_abrechnung_menue2.py             # lokal
    python scripts/analyse_abrechnung_menue2.py --instanz vm
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
CTX = {"lang": "de_DE", "ir.ui.menu.full_list": True}


def menuebaum(k, wurzel_namen):
    alle = k.kw("ir.ui.menu", "search_read",
                [[], ["name", "parent_id", "sequence", "action", "groups_id"]], context=CTX)
    kinder = {}
    for m in alle:
        pid = m["parent_id"][0] if m["parent_id"] else False
        kinder.setdefault(pid, []).append(m)
    for v in kinder.values():
        v.sort(key=lambda x: (x["sequence"], x["id"]))
    nach_id = {m["id"]: m for m in alle}

    def aktion_info(m):
        if not m["action"]:
            return None
        art, aid = m["action"].split(",")
        aid = int(aid)
        info = {"art": art, "id": aid}
        modell = {"ir.actions.act_window": "ir.actions.act_window",
                  "ir.actions.server": "ir.actions.server",
                  "ir.actions.client": "ir.actions.client",
                  "ir.actions.report": "ir.actions.report"}.get(art)
        if modell:
            felder = {"ir.actions.act_window": ["name", "res_model", "view_mode", "domain", "context"],
                      "ir.actions.server": ["name", "model_name"],
                      "ir.actions.client": ["name", "tag"],
                      "ir.actions.report": ["name", "model", "report_name"]}[art]
            try:
                info.update(k.kw(modell, "read", [[aid], felder], context=CTX)[0])
            except Exception as fehler:
                info["fehler"] = str(fehler)[:100]
        return info

    def gruppen_namen(ids):
        if not ids:
            return []
        try:
            return [g["name"] for g in k.kw("res.groups", "read", [list(ids), ["name"]], context=CTX)]
        except Exception:
            return ["?"]

    def baum(mid):
        return [{"id": m["id"], "name": m["name"], "sequence": m["sequence"],
                 "gruppe_namen": gruppen_namen(m["groups_id"]),
                 "aktion": aktion_info(m), "kinder": baum(m["id"])}
                for m in kinder.get(mid, [])]

    ergebnis = [{"wurzel_id": m["id"], "wurzel_name": m["name"],
                 "kinder": baum(m["id"])}
                for m in alle if not m["parent_id"] and m["name"] in wurzel_namen]
    return ergebnis, nach_id


def drucke(knoten, tiefe=0):
    for n in knoten:
        a = n["aktion"] or {}
        zusatz = ""
        if a:
            zusatz = "  [%s %s%s%s]" % (a.get("art", "?"), a.get("id", ""),
                                        " -> " + str(a.get("name")) if a.get("name") else "",
                                        " (%s)" % (a.get("res_model") or a.get("model_name")
                                                   or a.get("model") or a.get("tag") or ""))
        gr = ("  Gruppen: %s" % ",".join(n["gruppe_namen"])) if n.get("gruppe_namen") else ""
        print("%s- %s%s%s" % ("   " * tiefe, n["name"], zusatz, gr))
        drucke(n["kinder"], tiefe + 1)


def zaehle(knoten):
    return sum(1 + zaehle(n["kinder"]) for n in knoten)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true")
    p.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    a = p.parse_args()
    lade_env()
    daten = {}
    for name, client, wurzel in (("o11", o11(), WURZEL["o11"]),
                                 ("o18_" + a.instanz, o18(a.instanz), WURZEL["o18"])):
        print("\n================ %s  (Wurzel: %s) ================" % (name.upper(), wurzel))
        alle = client.kw("ir.ui.menu", "search_count", [[]], context=CTX)
        print("ir.ui.menu gesamt (full_list): %d" % alle)
        baeume, _ = menuebaum(client, (wurzel,))
        daten[name] = baeume
        for b in baeume:
            print("Menues unter/mit der Wurzel: %d" % (zaehle(b["kinder"]) + 1))
            drucke(b["kinder"])
        # Wurzeln zum Vergleich
        for m in client.kw("ir.ui.menu", "search_read",
                           [[["parent_id", "=", False]], ["name", "sequence"]],
                           context=CTX, order="sequence"):
            pass
    if a.json:
        ziel = os.path.join(tempfile.gettempdir(), "abrechnung_menue2.json")
        with open(ziel, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(daten, fh, ensure_ascii=False, indent=1, sort_keys=True)
        print("\nRohdaten (nicht im Repo): %s" % ziel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
