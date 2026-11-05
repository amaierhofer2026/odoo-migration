"""Vergleich Massenbearbeitung Odoo 11 -> Odoo 18 (read-only, beide Instanzen).

Liest den O11-Baseline aus docs/_massenbearbeitung_o11.json (erzeugt von
scripts/analyse_o11_massenbearbeitung.py) und misst dagegen den Odoo-18-Stand:
  - Modul server_action_mass_edit
  - vorhandene Massenbearbeitungs-Aktionen (ir.actions.server mit mass_edit_line_ids)
  - Existenz, Typ und Schreibbarkeit der Zielfelder
  - Standard-Alternativen (Aktionen, die Odoo 18 von sich aus am Modell anbietet)
  - Rechte auf mass.editing.wizard

Aufruf: python scripts/vergleich_massenbearbeitung.py --instanz lokal|vm [--json PFAD]
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import REPO, o18  # noqa: E402

DE = {"lang": "de_DE"}

# O11-Objekt-ID -> (O18-Modell, O18-Feld, Begruendung der Zuordnung)
MAPPING = {
    1: ("res.partner", "property_product_pricelist", "gleiches Feld, firmenabhaengig"),
    2: ("sale.order", "pricelist_id", "gleiches Feld"),
    4: ("sale.subscription.line", "quantity", "gleiches Feld"),
    5: ("sale.order", "state", "gleiches Feld, in O18 zusaetzlich Standard-Aktion Bestaetigen"),
    6: ("res.partner", "status_of_partner_id", "ITK-Feld, gleicher Name"),
    7: ("sale.order", "payment_term_id", "gleiches Feld"),
    8: ("sale.subscription", "recurring_next_date", "gleiches Feld"),
    9: ("sale.subscription", "state", "gleiches Feld, in O18 zusaetzlich Standard-Aktionen"),
    13: ("product.product", "categ_id", "gleiches Feld (verknuepft auf product.template.categ_id)"),
    14: ("account.move", "valorisierung_id", "account.invoice -> account.move, Feldname gleich"),
    18: ("account.move", "invoice_payment_term_id", "payment_term_id -> invoice_payment_term_id"),
    19: ("account.move", "invoice_date", "date_invoice -> invoice_date"),
    20: ("sale.subscription", "recurring_next_date", "gleiches Feld; in O11 Dublette zu Objekt 8"),
    21: ("account.move", "sale_order_benefit_period", "account.invoice -> account.move, Feldname gleich"),
    22: ("account.move", "projectcategory_id", "account.invoice -> account.move, Feldname gleich"),
    23: ("res.partner", "category_id", "gleiches m2m-Feld"),
    25: ("crm.lead", "x_Produktinteresse", "ITK-Auswahlfeld, gleicher Name"),
    26: ("crm.lead", "x_Lead_Quelle", "ITK-Auswahlfeld, gleicher Name"),
    27: ("crm.lead", "tag_ids", "gleiches m2m-Feld"),
    28: ("crm.lead", "x_lead_status", "ITK-Auswahlfeld, gleicher Name"),
}

MODELLE = ["res.partner", "sale.order", "sale.subscription", "sale.subscription.line",
           "account.move", "product.product", "crm.lead"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    ziel = a.json or os.path.join(REPO, "docs", "_massenbearbeitung_o18_%s.json" % a.instanz)

    o11d = json.load(open(os.path.join(REPO, "docs", "_massenbearbeitung_o11.json"), encoding="utf-8"))
    objekte = {o["id"]: o for o in o11d["objekte"]}

    k = o18(a.instanz)
    erg = {"stand": datetime.datetime.now().isoformat(timespec="seconds"),
           "instanz": a.instanz, "pruefungen": []}

    def pruef(name, soll, ist):
        ok = (soll == ist)
        erg["pruefungen"].append({"pruefung": name, "soll": soll, "ist": ist, "ok": ok})
        return ok

    mod = k.kw("ir.module.module", "search_read",
               [[("name", "in", ["server_action_mass_edit"])],
                ["name", "state", "installed_version"]]) or []
    erg["modul"] = mod
    ist_inst = bool(mod) and mod[0]["state"] == "installed"
    pruef("Modul server_action_mass_edit installiert", True, ist_inst)

    # Zielfelder
    felder_cache = {}
    erg["felder"] = []
    for oid, o in objekte.items():
        modell, feld, grund = MAPPING[oid]
        if modell not in felder_cache:
            felder_cache[modell] = k.kw(modell, "fields_get", [[], ["string", "type", "relation", "readonly",
                                                                 "store", "compute"]], context=DE) or {}
        fdef = felder_cache[modell].get(feld)
        eintrag = {"o11_id": oid, "o11_name": o["name"], "o11_modell": o["modell"],
                   "o11_feld": o["felder"][0]["name"] if o["felder"] else None,
                   "o18_modell": modell, "o18_feld": feld, "zuordnung": grund}
        if not fdef:
            eintrag["zustand"] = "FEHLT"
        else:
            eintrag["o18_label"] = fdef.get("string")
            eintrag["o18_typ"] = fdef.get("type")
            eintrag["o18_relation"] = fdef.get("relation")
            eintrag["o18_readonly"] = fdef.get("readonly")
            eintrag["o18_compute"] = fdef.get("compute")
            eintrag["o18_store"] = fdef.get("store")
            eintrag["zustand"] = "OK" if not fdef.get("compute") else "BERECHNET"
        erg["felder"].append(eintrag)
        pruef("Zielfeld %s.%s vorhanden" % (modell, feld), True, fdef is not None)

    # Vorhandene Massenbearbeitungs-Aktionen in O18
    sa = k.kw("ir.actions.server", "search_read",
              [[("mass_edit_line_ids", "!=", False)],
               ["id", "name", "model_id", "state", "usage", "groups_id", "binding_model_id",
                "binding_type", "binding_view_types", "mass_edit_line_ids", "mass_edit_message"]],
              context=DE) or []
    lines = {}
    if sa:
        lids = [l for s in sa for l in s["mass_edit_line_ids"]]
        for ln in k.kw("ir.actions.server.mass.edit.line", "read",
                       [lids, ["id", "server_action_id", "field_id", "sequence"]], context=DE) or []:
            lines.setdefault(ln["server_action_id"][0], []).append(ln["field_id"][1].split(".")[-1]
                                                                    if "." in ln["field_id"][1]
                                                                    else ln["field_id"][1])
    for s in sa:
        s["felder"] = sorted(lines.get(s["id"], []))
    erg["aktionen"] = sorted(sa, key=lambda s: s["id"])
    pruef("Anzahl Massenbearbeitungs-Aktionen in Odoo 18 (Soll 20)", 20, len(erg["aktionen"]))

    # Standard-Alternativen je Modell (Aktionen, die Odoo 18 selbst am Modell anbietet)
    erg["standard_aktionen"] = {}
    for m in MODELLE:
        acts = k.kw("ir.actions.server", "search_read",
                    [[("binding_model_id.model" if False else "model_id.model", "=", m),
                      ("mass_edit_line_ids", "=", False)],
                     ["id", "name", "state", "usage", "binding_model_id", "binding_type", "groups_id"]],
                    context=DE) or []
        erg["standard_aktionen"][m] = [x for x in acts if x.get("binding_model_id")]
        erg["standard_aktionen"][m].sort(key=lambda x: x["name"])

    # Rechte
    acc = k.kw("ir.model.access", "search_read",
               [[("model_id.model", "in", ["mass.editing.wizard", "ir.actions.server"])],
                ["name", "model_id", "group_id", "perm_read", "perm_write", "perm_create", "perm_unlink"]],
               context=DE) or []
    erg["zugriff"] = acc

    with open(ziel, "w", encoding="utf-8") as fh:
        json.dump(erg, fh, ensure_ascii=False, indent=1)

    ok = sum(1 for p in erg["pruefungen"] if p["ok"])
    print("Instanz: %s   Stand: %s" % (a.instanz, erg["stand"]))
    print("Modul:", mod)
    print("%-4s %-38s %-34s %-10s %s" % ("O11", "O11-Name", "O18-Feld", "Typ", "Zustand"))
    for e in erg["felder"]:
        print("%-4s %-38s %-34s %-10s %s" % (e["o11_id"], e["o11_name"][:38],
                                             "%s.%s" % (e["o18_modell"], e["o18_feld"]),
                                             e.get("o18_typ", "-"), e["zustand"]))
    print("\nMassenbearbeitungs-Aktionen in Odoo 18: %d" % len(erg["aktionen"]))
    for s in erg["aktionen"]:
        print("  %4d | %-45s | %-22s | Felder: %s" % (s["id"], s["name"], s["model_id"][1],
                                                      ", ".join(s["felder"])))
    print("\nStandard-Aktionen je Modell (ohne Massenbearbeitung):")
    for m, acts in erg["standard_aktionen"].items():
        print("  %-24s %s" % (m, "; ".join(x["name"] for x in acts) or "-"))
    print("\n=== Ergebnis: %d OK / %d FEHL ===" % (ok, len(erg["pruefungen"]) - ok))
    print("JSON:", ziel)


if __name__ == "__main__":
    main()
