"""Read-only: Firmenvorgabe der Kategoriekonten in Odoo 18 (ir.default) und aktuelle Menuelabels.

Aufruf: python scripts/erhebe_konterverwendung_teil3.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}
CTX_EN = {"lang": "en_US"}


def ir_default(k, bezeichnung):
    vorhanden = k.kw("ir.default", "fields_get", [[], ["type", "relation"]], context=CTX)
    print("   %s ir.default-Felder: %s" % (bezeichnung, sorted(vorhanden)))
    felder = [f for f in ("field_id", "company_id", "json_value") if f in vorhanden]
    feldids = []
    try:
        feldids = k.kw("ir.model.fields", "search",
                       [[("model", "=", "product.category"), ("name", "ilike", "account")]], context=CTX)
        print("      ir.model.fields (product.category, Konto): %d" % len(feldids))
    except Exception as exc:  # noqa: BLE001
        print("      ir.model.fields nicht lesbar: %s" % str(exc)[:100])
    dom = [("field_id", "in", feldids)] if feldids else [("field_id", "ilike", "account")]
    treffer = k.kw("ir.default", "search_read", [dom, felder], context=CTX, limit=0)
    for t in treffer:
        print("      %s" % t)
    if not treffer:
        print("      keine ir.default-Eintraege fuer product.category")
    # alle Defaults, die Kontofelder betreffen
    alle = k.kw("ir.default", "search_read", [[("field_id", "ilike", "account")],
                                              [f for f in ("field_id", "json_value", "company_id") if f in vorhanden]],
                context=CTX, limit=0)
    print("      Eintraege zu Kontofeldern insgesamt: %d" % len(alle))
    for a in alle[:10]:
        print("         %s" % a)
    return {"vorhandene_felder": sorted(vorhanden), "product_category": treffer, "kontofelder": alle}


def menuelabels(k, bezeichnung, suche):
    aus = {}
    for name in suche:
        m = k.kw("ir.ui.menu", "search_read", [[("name", "=", name)], ["id", "name", "complete_name", "action"]],
                 context=CTX, limit=0)
        m_en = k.kw("ir.ui.menu", "search_read", [[("name", "=", name)], ["id", "name", "complete_name"]],
                    context=CTX_EN, limit=0)
        aus[name] = {"de": m, "en": m_en}
        print("   %s '%s': de=%s | en=%s" % (bezeichnung, name,
                                             [(x["id"], x["complete_name"]) for x in m],
                                             [(x["id"], x["name"]) for x in m_en]))
    return aus


def main() -> int:
    k11, k18 = o11(), o18("lokal")
    daten = {}
    print("=== Odoo 18 lokal: Firmenvorgabe (ir.default) ===", flush=True)
    daten["o18_ir_default"] = ir_default(k18, "Odoo 18")
    print("\n=== Odoo 11: Firmenvorgabe (ir.default) ===", flush=True)
    try:
        daten["o11_ir_default"] = ir_default(k11, "Odoo 11")
    except Exception as exc:  # noqa: BLE001
        print("   Odoo 11 ir.default nicht abfragbar: %s" % str(exc)[:150])

    print("\n=== Menuelabels ===", flush=True)
    daten["o18_labels"] = menuelabels(k18, "Odoo 18", ["Projekt Kategorie", "Projektkategorien",
                                                       "Kostenstellen", "Kostenstellenkonten"])
    daten["o11_labels"] = menuelabels(k11, "Odoo 11", ["Kostenstellenkonten", "Projektkategorien",
                                                       "Projekt Kategorie"])

    p = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session131", "konten",
                     "konten_rohdaten_teil3.json")
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(daten, fh, ensure_ascii=False, indent=1, default=str)
    print("\nRohdaten: %s" % p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
