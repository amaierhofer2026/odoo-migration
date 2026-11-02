"""Read-only-Erhebung Massenbearbeitung Odoo 11 Prod (mass_editing).

Schreibt docs/_massenbearbeitung_o11.json und gibt eine kompakte Zusammenfassung aus.
Es werden ausschliesslich lesende RPC-Aufrufe ausgefuehrt.

Struktur von mass.object in Odoo 11 (mass_editing 11.0.1.0.1):
  id, name, model_id, model_list, field_ids, ref_ir_act_window_id
(keine group_ids, kein view_id - Rechte laufen ueber ir.model.access auf mass.object)
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import REPO, o11  # noqa: E402

DE = {"lang": "de_DE"}


def z(k, modell, domain):
    """search_count mit flacher Domain (verhindert die Klammer-Falle)."""
    return k.kw(modell, "search_count", [domain])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=os.path.join(REPO, "docs", "_massenbearbeitung_o11.json"))
    a = ap.parse_args()

    k = o11()
    erg = {"stand": datetime.datetime.now().isoformat(timespec="seconds"), "instanz": "O11 Prod ITK_V1_a"}

    erg["modul"] = k.kw("ir.module.module", "search_read",
                        [[("name", "in", ["mass_editing"])],
                         ["name", "state", "installed_version", "author", "license"]]) or []
    erg["mass_object_felder"] = k.kw("mass.object", "fields_get", [[], ["string", "type", "relation"]],
                                     context=DE)

    objekte = k.kw("mass.object", "search_read",
                   [[], ["id", "name", "model_id", "model_list", "field_ids", "ref_ir_act_window_id"]],
                   context=DE) or []
    objekte.sort(key=lambda o: o["id"])

    felder_cache = {}
    erg["objekte"] = []
    for o in objekte:
        eintrag = {"id": o["id"], "name": o["name"], "felder": []}
        technisch = None
        if o["model_id"]:
            m = k.kw("ir.model", "read", [[o["model_id"][0]], ["model"]])
            technisch = m[0]["model"] if m else None
        eintrag["modell_label"] = o["model_id"][1] if o["model_id"] else None
        eintrag["modell"] = technisch
        eintrag["model_list"] = o.get("model_list")
        eintrag["aktions_ref"] = o["ref_ir_act_window_id"][1] if o["ref_ir_act_window_id"] else None
        eintrag["aktions_id"] = o["ref_ir_act_window_id"][0] if o["ref_ir_act_window_id"] else None

        if technisch:
            eintrag["grundgesamtheit"] = z(k, technisch, [])
            if technisch not in felder_cache:
                felder_cache[technisch] = k.kw(technisch, "fields_get", [[], ["type"]]) or {}
            if "active" in felder_cache[technisch]:
                eintrag["grundgesamtheit_aktiv"] = z(k, technisch, [("active", "=", True)])

        fdef = k.kw("ir.model.fields", "search_read",
                    [[("id", "in", o["field_ids"])],
                     ["name", "field_description", "ttype", "relation", "modules"]],
                    context=DE) or []
        for f in sorted(fdef, key=lambda x: x["name"]):
            e = {"name": f["name"], "label": f["field_description"], "ttype": f["ttype"],
                 "relation": f["relation"], "modules": f["modules"]}
            if technisch and f["ttype"] not in ("one2many", "many2many"):
                try:
                    e["belegt"] = z(k, technisch, [(f["name"], "!=", False)])
                except Exception as exc:  # noqa: BLE001
                    e["belegt"] = "nicht messbar: %s" % str(exc)[:80]
            elif technisch:
                e["belegt"] = "m2m/o2m: nicht per search_count"
            eintrag["felder"].append(e)
        erg["objekte"].append(eintrag)

    # Sidebar-Aktionen (ir.actions.act_window mit src_model) und ihre ir.values-Verknuepfung
    aids = [o["aktions_id"] for o in erg["objekte"] if o.get("aktions_id")]
    if aids:
        erg["aktionen"] = k.kw("ir.actions.act_window", "search_read",
                               [[("id", "in", aids)],
                                ["name", "res_model", "src_model", "view_mode", "target", "domain",
                                 "context"]], context=DE) or []
        try:
            erg["werte"] = k.kw("ir.values", "search_read",
                                [[("action_id", "in", aids)], ["name", "model", "key", "action_id"]],
                                context=DE) or []
        except Exception as exc:  # noqa: BLE001
            erg["werte"] = [{"fehler": str(exc)[:300]}]

    # Rechte auf die Konfiguration
    try:
        erg["zugriff"] = k.kw("ir.model.access", "search_read",
                              [[("model_id.model", "in", ["mass.object", "mass.editing.wizard"])],
                               ["name", "model_id", "group_id", "perm_read", "perm_write",
                                "perm_create", "perm_unlink"]], context=DE) or []
    except Exception as exc:  # noqa: BLE001
        erg["zugriff"] = [{"fehler": str(exc)[:300]}]

    with open(a.json, "w", encoding="utf-8") as fh:
        json.dump(erg, fh, ensure_ascii=False, indent=1)

    print("Stand:", erg["stand"])
    print("Modul:", erg["modul"])
    print("mass.object-Objekte:", len(erg["objekte"]))
    for o in erg["objekte"]:
        feld = "; ".join("%s=%s (%s, belegt %s)" % (f["name"], f["label"], f["ttype"], f.get("belegt"))
                         for f in o["felder"])
        print(" %4d | %-45s | %-22s | Basis %s | %s" % (o["id"], o["name"], o["modell"],
                                                        o.get("grundgesamtheit"), feld))
    print("Sidebar-Aktionen:", len(erg.get("aktionen", [])), "ir.values:", len(erg.get("werte", [])))
    print("Zugriffsrechte:", len(erg.get("zugriff", [])))
    for g in erg.get("zugriff", []):
        print("   ", g)
    print("JSON:", a.json)


if __name__ == "__main__":
    main()
