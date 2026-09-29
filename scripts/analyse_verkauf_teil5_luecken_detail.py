"""Teil 5, Block 2: Detailpruefung der Lueckenkandidaten (Verkauf).

Klaert fuer jeden Kandidaten aus analyse_verkauf_teil5_luecken.py, ob er eine echte
funktionale/strukturelle Luecke ist oder ein Scheinbefund (Namenswechsel, auskommentiert,
totes Menue, Datenmigrationsthema):

  1) Lieferabwicklung (sale_stock): installierte Module und Felder in Odoo 11 / Odoo 18
  2) Rechnungsfelder der Auftragszeile: Odoo-18-Namen der Odoo-11-Felder
     (amt_invoiced, amt_to_invoice, price_reduce)
  3) Reportlayout-Kategorien: tatsaechliche Werte in Odoo 11 (layout_category_sequence)
  4) Reklamationen (crm.claim): Modul, Datensaetze, Menuezustand in Odoo 11 / Odoo 18
  5) CRM-Statistik (crm.opportunity.report) und Lead-Tags (crm.lead.tag) in Odoo 18
  6) Mailvorlagen: Vergleich der Odoo-11-Vorlage "IT-Kommunal GmbH Angebot" mit den
     Odoo-18-Vorlagen (Betreff, Textlaenge, Anhang, Bericht)
  7) Server-Aktionen auf sale.order in Odoo 18 (Abfrage korrigiert)

Aufruf:
    python scripts/analyse_verkauf_teil5_luecken_detail.py
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


def installiert(client, namen):
    mods = client.kw("ir.module.module", "search_read",
                     [[("name", "in", namen)], ["name", "state"]], context=SP)
    return {m["name"]: m["state"] for m in mods}


def main() -> int:
    k11, k18, kvm = o11(), o18("lokal"), o18("vm")
    ergebnis = {}

    print("=== 1) Lieferabwicklung (sale_stock) ===")
    module = ["sale_stock", "stock", "stock_account", "delivery", "sale_delivery", "purchase_stock"]
    für_instanz = {}
    for name, k in (("o11", k11), ("o18lokal", k18), ("o18vm", kvm)):
        stand = installiert(k, module)
        für_instanz[name] = stand
        felder = {}
        for feld in ("warehouse_id", "picking_policy", "picking_ids", "procurement_group_id", "delivery_count"):
            treffer = k.kw("ir.model.fields", "search_count", [[("model", "=", "sale.order"), ("name", "=", feld)]],
                           context=SP)
            felder[feld] = bool(treffer)
        print("  %-8s Module %s" % (name, stand))
        print("  %-8s Felder  %s" % ("", felder))
    ergebnis["lieferabwicklung"] = für_instanz

    print("\n=== 2) Rechnungs-/Preisfelder der Auftragszeile ===")
    for name, k in (("o11", k11), ("o18lokal", k18), ("o18vm", kvm)):
        vs = k.kw("ir.model.fields", "search_read",
                  [[("model", "=", "sale.order.line"),
                    "|", "|", "|", "|",
                    ("name", "ilike", "invoiced"), ("name", "ilike", "to_invoice"),
                    ("name", "ilike", "price_reduce"), ("name", "ilike", "qty_delivered"),
                    ("name", "ilike", "qty_invoiced")], ["name"]], context=SP)
        print("  %-8s %s" % (name, sorted(f["name"] for f in vs)))
    ergebnis["zeilenfelder"] = "siehe Ausgabe"

    print("\n=== 3) Reportlayout-Kategorien (layout_category_sequence) ===")
    gruppen = k11.kw("sale.order.line", "read_group",
                     [[("layout_category_sequence", "!=", False)], ["layout_category_sequence"], ["layout_category_sequence"]],
                     context=SP)
    werte = [{"wert": g["layout_category_sequence"], "anzahl": g.get("layout_category_sequence_count") or g.get("__count")}
             for g in gruppen]
    print("  Odoo 11 Werte: %s" % werte[:10])
    model11 = k11.kw("ir.model", "search_count", [[("model", "=", "sale.layout.category")]], context=SP)
    print("  Odoo 11 Modell sale.layout.category registriert: %s" % bool(model11))
    ergebnis["layout_kategorien"] = {"werte": werte, "modell_registriert": bool(model11)}

    print("\n=== 4) Reklamationen (crm.claim) ===")
    for name, k in (("o11", k11), ("o18lokal", k18), ("o18vm", kvm)):
        for modell in ("crm.claim", "crm.claim.category", "crm.claim.stage"):
            try:
                n = k.kw(modell, "search_count", [[]], context=SP)
                print("  %-8s %-22s %s Datensaetze" % (name, modell, n))
            except Exception as ex:
                print("  %-8s %-22s nicht vorhanden" % (name, modell))
    ergebnis["reklamationen"] = "siehe Ausgabe"

    print("\n=== 5) CRM-Statistik und Lead-Tags ===")
    for name, k in (("o11", k11), ("o18lokal", k18), ("o18vm", kvm)):
        tag = k.kw("ir.model", "search_count", [[("model", "=", "crm.tag")]], context=SP)
        leadtag = k.kw("ir.model", "search_count", [[("model", "=", "crm.lead.tag")]], context=SP)
        lead = k.kw("crm.lead", "search_count", [[]], context=SP) if name == "o11" else None
        print("  %-8s crm.tag=%s crm.lead.tag=%s %s" % (name, bool(tag), bool(leadtag),
                                                        ("crm.lead %d Datensaetze" % lead) if lead is not None else ""))

    print("\n=== 6) Mailvorlagen (Betreff/Inhalt/Anhang) ===")
    for name, k in (("o11", k11), ("o18lokal", k18)):
        vs = k.kw("mail.template", "search_read",
                  [[("model", "=", "sale.order")],
                   ["name", "subject", "body_html", "report_name", "attachment_ids", "auto_delete", "lang"]],
                  context=SP)
        print("  %s: %d Vorlagen" % (name, len(vs)))
        for v in vs:
            print("     %-42s Betreff=%s" % (v["name"][:42], (v["subject"] or "")[:70]))
            print("        Text %d Zeichen, Bericht=%s, Anhaenge=%d"
                  % (len(v["body_html"] or ""), v["report_name"] or "-", len(v["attachment_ids"] or [])))
        ergebnis.setdefault("mailvorlagen", {})[name] = [
            {"name": v["name"], "betreff": v["subject"], "text_zeichen": len(v["body_html"] or ""),
             "bericht": v["report_name"], "anhaenge": len(v["attachment_ids"] or [])} for v in vs]

    print("\n=== 7) Server-Aktionen auf sale.order (Odoo 18) ===")
    for name, k in (("o11", k11), ("o18lokal", k18), ("o18vm", kvm)):
        vs = k.kw("ir.actions.server", "search_read", [[], ["name", "state", "active", "model_id"]],
                  context=SP)
        treffer = [v for v in vs if v.get("model_id") and "sale.order" == v["model_id"][1]]
        print("  %-8s %d Server-Aktionen insgesamt, auf sale.order: %s"
              % (name, len(vs), [(t["name"], t["active"]) for t in treffer]))
        bas = k.kw("base.automation", "search_read", [[], ["name", "active", "model_id"]], context=SP)
        print("  %-8s automatisierte Aktionen gesamt: %s" % ("", [(b["name"], b["model_id"][1] if b["model_id"] else "-") for b in bas[:8]]))
    ergebnis["server_aktionen"] = "siehe Ausgabe"

    ziel = os.path.join(REPO, "docs", "_verkauf_teil5_luecken_detail.json")
    with open(ziel, "w", encoding="utf-8") as fh:
        json.dump(ergebnis, fh, ensure_ascii=False, indent=1)
    print("\nRohdaten: %s" % ziel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
