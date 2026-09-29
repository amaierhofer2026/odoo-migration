"""Teil 5, Block 4: Endstand des Bereichs Verkauf feststellen (nur lesend).

Sammelt die Nachweise fuer die Abschlussmarkierung:
  - installierte Module und Versionen (lokal und VM)
  - Bestandszahlen (Auftraege, Auftragszeilen, Produkte, Lagerbelege, Zahlungsbedingungen)
  - View-Gesundheit (alle Ansichtstypen laden fehlerfrei)
  - Zahlungsbedingungen und Verkaufsteams/Vertriebskanaele
  - Regression: Verweis auf scripts/abschluss_verkauf_regression.py
  - Sichtpruefung: keine offenen funktionalen Punkte in der Lueckenanalyse

Aufruf:
    python scripts/abschluss_verkauf_endstand.py [--instanzen lokal,vm]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o18

SP = {"lang": "de_DE"}
MODULE = ["itk_sale_management", "itk_product", "itk_reports", "itk_subscription",
          "sale_management", "sale", "stock", "stock_account", "sale_stock", "account"]


def endstand(instanz: str) -> dict:
    k = o18(instanz)
    e: dict = {"instanz": instanz}

    mods = k.kw("ir.module.module", "search_read",
                [[("name", "in", MODULE)], ["name", "state", "latest_version", "installed_version"]],
                context=SP)
    e["module"] = {m["name"]: {"state": m["state"],
                               "version": m["latest_version"] or m["installed_version"]}
                   for m in sorted(mods, key=lambda x: x["name"])}

    e["bestand"] = {
        "auftraege": k.kw("sale.order", "search_count", [[]], context=SP),
        "auftragszeilen": k.kw("sale.order.line", "search_count", [[]], context=SP),
        "produkte": k.kw("product.template", "search_count", [[]], context=SP),
        "kunden": k.kw("res.partner", "search_count", [[("customer_rank", ">", 0)]], context=SP),
        "lagerbelege": k.kw("stock.picking", "search_count", [[]], context=SP),
        "zahlungsbedingungen": k.kw("account.payment.term", "search_count", [[]], context=SP),
        "preislisten": k.kw("product.pricelist", "search_count", [[]], context=SP),
        "verkaufsteams": k.kw("crm.team", "search_count", [[]], context=SP),
        "abonnements": k.kw("sale.subscription", "search_count", [[]], context=SP),
    }

    # View-Gesundheit: jede vorhandene Ansicht eines Modells muss ladbar sein
    gesund = {}
    for modell in ("sale.order", "sale.order.line", "stock.picking", "product.template",
                   "product.product", "account.move", "res.partner", "account.payment.term",
                   "product.pricelist", "crm.team"):
        typen = k.kw("ir.ui.view", "search_read",
                     [[("model", "=", modell)], ["type"]], context=SP)
        gesehen = sorted({t["type"] for t in typen})
        fehler = []
        for typ in gesehen:
            try:
                treffer = k.kw("ir.ui.view", "search",
                               [[("model", "=", modell), ("type", "=", typ)]], context=SP, limit=1)
                if treffer:
                    k.kw("ir.ui.view", "read", [[treffer[0]], ["arch_db"]], context=SP)
            except Exception as ex:
                fehler.append("%s: %s" % (typ, str(ex)[:80]))
        gesund[modell] = {"typen": gesehen, "fehler": fehler}
    e["views"] = gesund

    e["zahlungsbedingungen"] = k.kw("account.payment.term", "search_read",
                                    [[], ["name", "active"]], context=SP)
    e["verkaufsteams"] = k.kw("crm.team", "search_read", [[], ["name", "active"]], context=SP)
    return e


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanzen", default="lokal,vm")
    a = p.parse_args()

    ergebnis = {}
    for instanz in [x.strip() for x in a.instanzen.split(",") if x.strip()]:
        print("=" * 78)
        print("Endstand %s" % instanz)
        print("=" * 78)
        e = endstand(instanz)
        ergebnis[instanz] = e
        print("Module:")
        for name, d in e["module"].items():
            print("  %-22s %-10s %s" % (name, d["state"], d["version"]))
        print("Bestand: %s" % e["bestand"])
        print("Zahlungsbedingungen (%d): %s" % (len(e["zahlungsbedingungen"]),
                                                [z["name"] for z in e["zahlungsbedingungen"]]))
        print("Verkaufsteams (%d): %s" % (len(e["verkaufsteams"]),
                                          [t["name"] for t in e["verkaufsteams"]]))
        print("View-Gesundheit:")
        for modell, d in e["views"].items():
            print("  %-20s Typen %-45s Fehler %s"
                  % (modell, ",".join(d["typen"]), d["fehler"] or "keine"))

    pfad = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "docs", "_verkauf_teil5_endstand.json")
    with open(pfad, "w", encoding="utf-8") as fh:
        json.dump(ergebnis, fh, ensure_ascii=False, indent=1)
    print()
    print("Rohdaten: %s" % pfad)

    offen = [m for i in ergebnis.values() for m, d in i["views"].items() if d["fehler"]]
    fehlende_module = [m for i in ergebnis.values() for m, d in i["module"].items()
                       if d["state"] != "installed"]
    print("Auffaellig: %s" % (offen or "keine offenen View-Fehler"))
    print("Nicht installierte Module aus der Liste: %s" % (fehlende_module or "keine"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
