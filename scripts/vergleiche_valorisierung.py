"""Read-only: Bereich Valorisierung Odoo 11 gegen Odoo 18 (Modell, Ansichten, Daten, Verwendung).

Aufruf: python scripts/vergleiche_valorisierung.py

Beide Systeme fuehren dasselbe Modell `itk_valorisierung.valorisierung` (ITK-Modul).
Geprueft werden Felder, Listen-/Formular-/Suchansicht, Sortierung, Buttons, Datensaetze,
Herkunft des Odoo-18-Datensatzes VAL-OK und die Verwendung des Modells in beiden Systemen.
Odoo 11 wird ausschliesslich gelesen.
"""
from __future__ import annotations

import json
import sys

sys.path.insert(0, "C:/Odoo-Test/scripts")
from _o11o18_client import o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}
MODELL = "itk_valorisierung.valorisierung"
FELDER = ["id", "name", "description", "seq", "create_date", "write_date", "create_uid", "write_uid"]


def arch(k, typ):
    """Wirksame Ansicht je Version lesen: Odoo 11 fields_view_get, Odoo 18 get_views."""
    try:
        v = k.kw(MODELL, "get_views", [[[False, typ]]], context=CTX)
        a = (v.get("views") or {}).get(typ)
        if isinstance(a, dict) and a.get("arch"):
            return a["arch"]
    except Exception:
        pass
    try:
        v = k.kw(MODELL, "fields_view_get", [False, typ, {}], context=CTX)
        return v.get("arch")
    except Exception as fehler:
        return "nicht lesbar: %s" % str(fehler)[:160]


def felder(k):
    return k.kw(MODELL, "fields_get", [[], ["string", "type", "required", "readonly", "relation",
                                             "default"]], context=CTX)


def daten(k):
    ids = k.kw(MODELL, "search", [[]], context=CTX)
    return k.kw(MODELL, "read", [ids, FELDER], context=CTX) if ids else []


for name, k, inst in (("Odoo 11 (Produktion, read-only)", o11(), None),
                      ("Odoo 18 lokal", o18("lokal"), "lokal"),
                      ("Odoo 18 VM", o18("vm"), "vm")):
    print("\n============================== %s ==============================" % name)
    print("--- Modellfelder ---")
    try:
        f = felder(k)
    except Exception as fehler:
        print("   Felder nicht lesbar: %s" % str(fehler)[:200])
        f = {}
    for fname in sorted(f):
        if fname.startswith("__"):
            continue
        d = f[fname]
        print("   %-24s %-10s Pflicht=%-5s readonly=%-5s Default=%-8s %s%s"
              % (fname, d["type"], d["required"], d["readonly"], d.get("default"),
                 "-> %s" % d["relation"] if d.get("relation") else "",
                 "Bezeichnung: %r" % d["string"]))
    for typ in ("tree", "form", "search"):
        a = arch(k, typ)
        print("--- %s-Ansicht (wirksam) ---" % typ)
        print(a if a else "(leer)")
    print("--- Datensaetze (%s) ---" % MODELL)
    try:
        for d in daten(k):
            print("   %s" % json.dumps(d, ensure_ascii=False))
    except Exception as fehler:
        print("   nicht lesbar: %s" % str(fehler)[:200])

    if inst:
        print("--- Herkunft/Referenzen des Datensatzes VAL-OK ---")
        ids = k.kw(MODELL, "search", [[("name", "=", "VAL-OK")]], context=CTX)
        if not ids:
            print("   kein Datensatz 'VAL-OK' vorhanden")
        for xid in k.kw("ir.model.data", "search_read",
                        [[("model", "=", MODELL), ("res_id", "in", ids or [0])],
                         ["module", "name", "res_id", "noupdate"]], context=CTX):
            print("   externer Bezeichner: %s.%s (res_id %s, noupdate=%s)"
                  % (xid["module"], xid["name"], xid["res_id"], xid["noupdate"]))

    print("--- Verwendung des Modells (Felder mit relation darauf) ---")
    for b in k.kw("ir.model.fields", "search_read",
                  [[("relation", "=", MODELL)], ["model", "name", "ttype", "field_description"]],
                  context=CTX):
        zahl = ""
        try:
            zahl = k.kw(b["model"], "search_count", [[(b["name"], "!=", False)]], context=CTX)
        except Exception:
            zahl = "?"
        print("   %-34s %-22s %-10s belegte Datensaetze: %s"
              % (b["model"], b["name"], b["ttype"], zahl))
