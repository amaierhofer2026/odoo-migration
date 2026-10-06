"""Produktart: Detailmessungen (Kreuztabelle type x product_type_id, Filter, Suchansichten).

Read-only. Aufruf: python scripts/produktart_details.py [o11|lokal|vm]
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}
WERTE = ["consu", "service", "general", "onlineservice", "sw", "consulting",
         "platform", "hw", "project", "product"]


def kreuz(k):
    """Kreuztabelle: type x product_type_id (nur lesend, in Python gezaehlt)."""
    ids = k.kw("product.template", "search", [[]], context=CTX)
    daten = k.kw("product.template", "read", [ids, ["type", "product_type_id", "active", "name"]],
                 context=CTX)
    tabelle = {}
    for d in daten:
        t = d.get("type") or "(leer)"
        p = d["product_type_id"][1] if d.get("product_type_id") else "(leer)"
        tabelle.setdefault(t, {}).setdefault(p, 0)
        tabelle[t][p] += 1
    return {"gesamt": len(daten), "tabelle": tabelle}


def felder_im_modell(k, modelle, feld):
    try:
        return k.kw("ir.model.fields", "search_read",
                    [[("model", "in", modelle), ("name", "=", feld)],
                     ["model", "field_description", "ttype", "selection", "module", "required",
                      "relation", "store"]])
    except RuntimeError as fehler:
        return "Fehler: %s" % str(fehler)[:150]


def filter_treffer(k):
    try:
        fs = k.kw("ir.filters", "search_read", [[], ["name", "model_id", "domain", "context",
                                                    "user_id", "is_default"]])
    except RuntimeError as fehler:
        return "Fehler: %s" % str(fehler)[:150]
    treffer = []
    for f in fs:
        text = "%s %s" % (f.get("domain") or "", f.get("context") or "")
        if "product_type" in text or any("'%s'" % w in text for w in WERTE):
            treffer.append({"name": f.get("name"),
                            "model": f["model_id"][1] if f.get("model_id") else None,
                            "domain": f.get("domain"), "context": f.get("context")})
    return {"gesamt": len(fs), "treffer": treffer}


def ansicht_arch(k, namen):
    aus = {}
    for name in namen:
        try:
            vs = k.kw("ir.ui.view", "search_read", [[("name", "=", name)], ["name", "model", "arch_db"]],
                      )
        except RuntimeError:
            vs = k.kw("ir.ui.view", "search_read", [[("name", "=", name)], ["name", "model", "arch"]])
        for v in vs:
            arch = v.get("arch_db") or v.get("arch") or ""
            zeilen = [z.strip() for z in arch.splitlines()
                      if any(w in z for w in ("product_type_id", "type", "domain", "context"))]
            aus[name] = {"model": v.get("model"), "zeilen": zeilen[:25]}
    return aus


if __name__ == "__main__":
    inst = sys.argv[1] if len(sys.argv) > 1 else "o11"
    k = o11() if inst == "o11" else o18(inst)
    bericht = {
        "instanz": inst,
        "kreuztabelle": kreuz(k),
        "feld_type_modellebene": felder_im_modell(k, ["product.template", "product.product"], "type"),
        "feld_product_type_id_modellebene": felder_im_modell(
            k, ["product.template", "product.product"], "product_type_id"),
        "filter": filter_treffer(k),
    }
    if inst == "o11":
        bericht["ansichten"] = ansicht_arch(
            k, ["product.template.search.inherit", "Product Template ITK",
                "Product Template Tree ITK"])
    else:
        bericht["ansichten"] = ansicht_arch(
            k, ["Product Template Search ITK Produktfilter", "product.template.search.abo.produkte",
                "Product Template ITK"])
    ziel = os.path.join(os.environ.get("LOCALAPPDATA", "/tmp"), "Temp", "produktart",
                        "details_%s.json" % inst)
    with open(ziel, "w", encoding="utf-8") as fh:
        json.dump(bericht, fh, ensure_ascii=False, indent=1, default=str)
    print("Kreuztabelle:")
    for t, werte in sorted(bericht["kreuztabelle"]["tabelle"].items(), key=lambda x: -sum(x[1].values())):
        print("   %-14s %s" % (t, dict(sorted(werte.items(), key=lambda y: -y[1]))))
    print("\nFeld type (Modellebene):")
    for f in bericht["feld_type_modellebene"]:
        if isinstance(f, dict):
            print("   ", {kk: f.get(kk) for kk in ("model", "field_description", "ttype", "module",
                                                   "required")})
            print("      Auswahlwerte:", [(w, b) for w, b in (f.get("selection") or [])])
    print("\nFeld product_type_id (Modellebene):")
    for f in bericht["feld_product_type_id_modellebene"]:
        if isinstance(f, dict):
            print("   ", {kk: f.get(kk) for kk in ("model", "field_description", "ttype", "module",
                                                   "required", "relation", "store")})
    print("\nFilter:", bericht["filter"] if isinstance(bericht["filter"], str)
          else (bericht["filter"]["gesamt"], bericht["filter"]["treffer"]))
    for name, d in bericht["ansichten"].items():
        print("\nAnsicht %s (%s):" % (name, d.get("model")))
        for z in d.get("zeilen", []):
            print("   ", z[:160])
    print("\ngespeichert:", ziel)
