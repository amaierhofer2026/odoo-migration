"""Teil 5, Block 2: Nachtrag 2 - E-Mail-Versand von Angeboten (Nutzung und Berichtsanhang).

Klaert:
  - welche Berichte die E-Mail-Vorlagen anhaengen (Odoo 11: report_template; Odoo 18: report_template_ids)
  - ob die Odoo-11-ITK-Vorlage "IT-Kommunal GmbH Angebot" tatsaechlich verwendet wurde
    (Zaehlung der Nachrichten auf Verkaufsauftraegen mit passendem Betreff)
  - welche Vorlage die Odoo-18-Versandassistenz vorauswaehlt
  - Server-Aktionen in Odoo 18 (reduzierte Feldliste, um Serverfehler zu vermeiden)

Aufruf:
    python scripts/analyse_verkauf_teil5_luecken_detail3.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP = {"lang": "de_DE"}


def main() -> int:
    ergebnis = {}
    k11, k18, kvm = o11(), o18("lokal"), o18("vm")

    print("=== Berichtsanhang der E-Mail-Vorlagen ===")
    vs = k11.kw("mail.template", "search_read",
                [[("model", "=", "sale.order")], ["name", "report_template", "report_name"]], context=SP)
    for v in vs:
        rt = v.get("report_template")
        bericht = "-"
        if rt:
            rid = rt[0] if isinstance(rt, (list, tuple)) else rt
            r = k11.kw("ir.actions.report", "read", [[rid], ["name", "report_name"]], context=SP)
            bericht = "%s -> %s" % (r[0]["name"], r[0]["report_name"]) if r else str(rid)
        print("  O11 %-40s Bericht=%s" % (v["name"][:40], bericht))
        ergebnis.setdefault("o11_report_anhang", []).append({"vorlage": v["name"], "bericht": bericht})

    for name, k in (("o18lokal", k18), ("o18vm", kvm)):
        vs = k.kw("mail.template", "search_read",
                  [[("model", "=", "sale.order")], ["name", "report_template_ids"]], context=SP)
        for v in vs:
            ids = v.get("report_template_ids") or []
            namen = []
            if ids:
                rs = k.kw("ir.actions.report", "read", [ids, ["name", "report_name"]], context=SP)
                namen = ["%s -> %s" % (r["name"], r["report_name"]) for r in rs]
            print("  %-8s %-40s Bericht=%s" % (name, v["name"][:40], namen or "-"))
            ergebnis.setdefault(name + "_report_anhang", []).append({"vorlage": v["name"], "berichte": namen})

    print("\n=== Nutzung der Odoo-11-ITK-Vorlage (Nachrichten auf Verkaufsauftraegen) ===")
    for begriff in ("IT-Kommunal GmbH Angebot", "Angebot", "Auftragsbestätigung"):
        n = k11.kw("mail.message", "search_count",
                   [[("model", "=", "sale.order"), ("subject", "ilike", begriff)]], context=SP)
        print("  O11 Nachrichten mit '%s' im Betreff: %d" % (begriff, n))
        ergebnis.setdefault("nutzung_o11", {})[begriff] = n
    n18 = k18.kw("mail.message", "search_count",
                 [[("model", "=", "sale.order"), ("subject", "ilike", "Angebot")]], context=SP)
    print("  O18 (lokal) Nachrichten mit 'Angebot' im Betreff: %d" % n18)
    ergebnis["nutzung_o18_angebot"] = n18

    print("\n=== Vorauswahl der Versandassistenz (Standardvorlage je Modell) ===")
    for name, k in (("o11", k11), ("o18lokal", k18)):
        try:
            treffer = k.kw("ir.model.data", "search_read",
                           [[("model", "=", "mail.template"), ("module", "=", "sale")],
                            ["name", "res_id"]], context=SP)
            print("  %s sale-Modulvorlagen: %s" % (name, [(t["name"], t["res_id"]) for t in treffer]))
        except Exception as ex:
            print("  %s nicht lesbar (%s)" % (name, str(ex)[:70]))

    print("\n=== Server-Aktionen Odoo 18 (reduzierte Felder) ===")
    for name, k in (("o18lokal", k18), ("o18vm", kvm)):
        try:
            vs = k.kw("ir.actions.server", "search_read", [[], ["name", "active"]], context=SP)
            print("  %-8s %d Server-Aktionen: %s" % (name, len(vs), [v["name"] for v in vs][:12]))
        except Exception as ex:
            print("  %-8s nicht lesbar (%s)" % (name, str(ex)[:70]))

    ziel = os.path.join(REPO, "docs", "_verkauf_teil5_luecken_detail3.json")
    with open(ziel, "w", encoding="utf-8") as fh:
        json.dump(ergebnis, fh, ensure_ascii=False, indent=1)
    print("\nRohdaten: %s" % ziel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
