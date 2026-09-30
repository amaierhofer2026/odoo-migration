"""Read-only B2: Gutschrift-Funktion Odoo 11 (account.invoice.refund) gegen Odoo 18
(account.move.reversal).

Aufruf:  python scripts/analyse_abrechnung_b2_gutschrift.py
Odoo 11 Prod wird ausschliesslich lesend verwendet.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o11, o18

FELDER = ["id", "name", "field_description", "ttype", "relation", "required", "readonly",
          "store", "help", "modules", "copied", "related"]


def felder(k, modell, sprache="de_DE"):
    """Felder ueber ir.model.fields (lokal, schnell) plus Auswahlwerte ueber fields_get (uebersetzt)."""
    roh = k.kw("ir.model.fields", "search_read", [[("model", "=", modell)], FELDER], order="name")
    beschriftet = {}
    try:
        beschriftet = k.kw(modell, "fields_get", [[], ["string", "type", "selection", "required",
                                                        "readonly", "relation"]], context={"lang": sprache})
    except Exception as fehler:
        print("   (fields_get nicht verfuegbar: %s)" % str(fehler)[:60])
    return roh, beschriftet


def views(k, modell):
    return k.kw("ir.ui.view", "search_read", [[("model", "=", modell)],
                ["id", "name", "type", "priority", "mode", "arch_db"]], order="priority,id")


def main() -> int:
    lade_env()
    k11, k18 = o11(), o18("lokal")
    bericht = {}

    for name, k, modell, archmodell in (("O11", k11, "account.invoice.refund", "account.invoice.refund"),
                                        ("O18", k18, "account.move.reversal", "account.move.reversal")):
        print("=" * 78)
        print("%s: Modell %s" % (name, modell))
        print("=" * 78)
        roh, beschriftet = felder(k, modell)
        print("Felder gesamt: %d" % len(roh))
        for f in roh:
            beschr = beschriftet.get(f["name"], {})
            zusatz = ""
            if beschr.get("selection"):
                zusatz = " | Auswahl: %s" % beschr["selection"]
            print("   %-22s %-12s %-34s req=%-5s ro=%-5s store=%s%s"
                  % (f["name"], f["ttype"], (f["field_description"] or "")[:34],
                     f["required"], f["readonly"], f["store"], zusatz))
        print("-- Auswahlwerte (de_DE) --")
        for fname in ("filter_refund", "refund_method", "date", "date_invoice", "description", "reason"):
            if fname in beschriftet:
                daten = beschriftet[fname]
                print("   %-16s %-28s %s" % (fname, daten.get("string"), daten.get("selection")))
        print("-- Views des Assistenten --")
        for v in views(k, modell):
            print("   id=%-6s prio=%-4s typ=%-6s %-42s mode=%s" % (v["id"], v["priority"], v["type"],
                                                                   v["name"][:42], v["mode"]))
        print("-- Quellmodul (ir.model.data) --")
        for d in k.kw("ir.model.data", "search_read", [[("model", "=", "ir.ui.view"), ("res_id", "in", [v["id"] for v in views(k, modell)] or [0])],
                                                       ["module", "name", "res_id"]], order="res_id"):
            print("   %-14s %-40s view=%s" % (d["module"], d["name"][:40], d["res_id"]))
        bericht[name] = {"felder": roh, "beschriftet": {kk: vv for kk, vv in beschriftet.items()},
                         "views": [{kk: vv for kk, vv in v.items() if kk != "arch_db"} for v in views(k, modell)]}

    print("\n" + "=" * 78)
    print("Befunde in Odoo 11: wie wurden die 237 Gutschriften tatsaechlich erzeugt?")
    print("=" * 78)
    k11.invalidate() if hasattr(k11, "invalidate") else None
    print("Gutschriften (out_refund): %s" % k11.kw("account.invoice", "search_count", [[("type", "=", "out_refund")]]))
    for feld, txt in (("state", "Zustand"),):
        for w in k11.kw("account.invoice", "read_group", [[("type", "=", "out_refund")], [feld], [feld]],
                        context={"lang": "de_DE"}):
            print("   %-10s %-14s %s" % (txt, w.get(feld), w.get("__count")))
    print("mit Ursprungsrechnung (refund_invoice_id): %s"
          % k11.kw("account.invoice", "search_count", [[("type", "=", "out_refund"), ("refund_invoice_id", "!=", False)]]))
    print("mit Herkunft (origin) gefuellt: %s"
          % k11.kw("account.invoice", "search_count", [[("type", "=", "out_refund"), ("origin", "!=", False)]]))
    print("mit Kommentar (comment) gefuellt: %s"
          % k11.kw("account.invoice", "search_count", [[("type", "=", "out_refund"), ("comment", "!=", False)]]))
    print("Beispiele Gutschriften:")
    for g in k11.kw("account.invoice", "search_read", [[("type", "=", "out_refund")],
                    ["id", "number", "state", "date_invoice", "refund_invoice_id", "origin",
                     "comment", "residual", "amount_total"]], order="id", limit=6):
        print("   id=%-6s %-12s %-9s refund_invoice_id=%-22s origin=%-14s comment=%s"
              % (g["id"], g["number"], g["state"], g["refund_invoice_id"], g["origin"],
                 (g["comment"] or "")[:40]))

    ziel = os.path.join(tempfile.gettempdir(), "abrechnung_b2_gutschrift.json")
    with open(ziel, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(bericht, fh, ensure_ascii=False, indent=1, default=str)
    print("\nRohdaten: %s" % ziel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
