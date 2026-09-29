"""Teil 5, Block 2: Nachtrag - Mailvorlagen und Automatismen (Verkauf).

Klaert:
  - Feldumfang von mail.template in Odoo 18 (Abfrage ohne nicht vorhandene Felder)
  - Mailvorlagen zu sale.order in Odoo 11 und Odoo 18 samt Betreff, Textlaenge und Berichtsanhang
  - Vorlagen mit "Angebot"/"ITK" im Namen bei allen Modellen in Odoo 18
  - Server-Aktionen und automatisierte Aktionen (Auswertung im Client, keine Serverfehler)

Aufruf:
    python scripts/analyse_verkauf_teil5_luecken_detail2.py
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


def felder(client, modell):
    return sorted(f["name"] for f in client.kw("ir.model.fields", "search_read",
                                               [[("model", "=", modell)], ["name"]], context=SP))


def main() -> int:
    ergebnis = {}
    k11, k18, kvm = o11(), o18("lokal"), o18("vm")

    print("=== mail.template Felder ===")
    f11, f18 = felder(k11, "mail.template"), felder(k18, "mail.template")
    print("  nur Odoo 11: %s" % sorted(set(f11) - set(f18)))
    print("  nur Odoo 18: %s" % sorted(set(f18) - set(f11)))
    ergebnis["mail_template_felder"] = {"nur_o11": sorted(set(f11) - set(f18)),
                                        "nur_o18": sorted(set(f18) - set(f11))}

    print("\n=== Mailvorlagen zu sale.order ===")
    anhang_feld = "report_name" if "report_name" in f18 else "report_template_ids"
    for name, k in (("o11", k11), ("o18lokal", k18), ("o18vm", kvm)):
        use_feld = "report_name" if ("report_name" in (f11 if name == "o11" else f18)) else anhang_feld
        vs = k.kw("mail.template", "search_read",
                  [[("model", "=", "sale.order")],
                   ["name", "subject", "body_html", use_feld, "lang", "auto_delete"]], context=SP)
        print("  %s: %d Vorlagen (Berichtsfeld: %s)" % (name, len(vs), use_feld))
        for v in vs:
            bericht = v.get(use_feld)
            print("     %-40s Betreff=%s" % (v["name"][:40], (v["subject"] or "")[:60]))
            print("        Text %5d Zeichen, Bericht=%s, Sprache=%s"
                  % (len(v["body_html"] or ""), bericht if bericht else "-", v.get("lang")))
        ergebnis.setdefault("vorlagen_sale_order", {})[name] = [
            {"name": v["name"], "betreff": v["subject"], "text": len(v["body_html"] or ""),
             "bericht": str(v.get(use_feld) or "")} for v in vs]

    print("\n=== Vorlagen mit Angebot/ITK im Namen (alle Modelle, Odoo 18) ===")
    vs = k18.kw("mail.template", "search_read",
                [["|", ("name", "ilike", "Angebot"), "|", ("name", "ilike", "ITK"), ("name", "ilike", "Auftrag")],
                 ["name", "model", "subject"]], context=SP)
    for v in vs:
        print("  %-42s %-18s %s" % (v["name"][:42], v["model"], (v["subject"] or "")[:50]))
    ergebnis["vorlagen_itk_o18"] = [{"name": v["name"], "model": v["model"]} for v in vs]

    print("\n=== Server-Aktionen und Automatismen ===")
    for name, k in (("o11", k11), ("o18lokal", k18), ("o18vm", kvm)):
        try:
            vs = k.kw("ir.actions.server", "search_read", [[], ["name", "state", "active", "model_id"]],
                      context=SP)
            treffer = [(v["name"], v["active"]) for v in vs
                       if v.get("model_id") and v["model_id"][1] in ("sale.order", "sale.order.line")]
            print("  %-8s %d Server-Aktionen, auf Verkaufsmodelle: %s" % (name, len(vs), treffer))
        except Exception as ex:
            print("  %-8s Server-Aktionen nicht lesbar (%s)" % (name, str(ex)[:80]))
        try:
            bas = k.kw("base.automation", "search_read", [[], ["name", "active", "model_id"]],
                       context=SP)
            print("  %-8s automatisierte Aktionen: %s"
                  % ("", [(b["name"], b["model_id"][1] if b["model_id"] else "-", b["active"]) for b in bas]))
        except Exception as ex:
            print("  %-8s automatisierte Aktionen nicht lesbar (%s)" % ("", str(ex)[:80]))

    ziel = os.path.join(REPO, "docs", "_verkauf_teil5_luecken_detail2.json")
    with open(ziel, "w", encoding="utf-8") as fh:
        json.dump(ergebnis, fh, ensure_ascii=False, indent=1)
    print("\nRohdaten: %s" % ziel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
