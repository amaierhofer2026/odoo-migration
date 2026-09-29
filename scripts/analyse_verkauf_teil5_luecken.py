"""Teil 5, Block 2: Lueckenanalyse Modul Verkauf (Odoo 11 gegen Odoo 18).

Systematischer Abgleich der in Odoo 11 tatsaechlich verwendeten Verkaufsfunktionen gegen
Odoo 18, gegliedert nach:

  A) Felder: in Odoo 11 belegte Felder von sale.order / sale.order.line, die es in Odoo 18
     nicht (mehr) gibt
  B) Modelle und Menueziele: Modelle der Odoo-11-Verkaufsmenues ohne Entsprechung in Odoo 18
  C) Automatismen: Server-Aktionen und automatisierte Aktionen auf sale.order
  D) Mailvorlagen: mail.template fuer sale.order
  E) Stammdaten: in Odoo 11 tatsaechlich verwendete Stammdaten (Zahlungsbedingungen, Preislisten,
     Verkaufsteams, Steuern, Produktkategorien, UTM, Positionen, Waehrungen) und ihr Vorhandensein
     in Odoo 18 (Namensvergleich)
  F) Berichte/Druckberichte: Report-Aktionen und Ansichten (Kurzabgleich)

Ergebnis: docs/_verkauf_teil5_luecken.json (gitignoriert) und Konsolenausgabe.
Es werden ausschliesslich Leseroutinen verwendet; Odoo 11 bleibt unveraendert.

Aufruf:
    python scripts/analyse_verkauf_teil5_luecken.py
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

# Dokumentierte, bewusst nicht uebernommene Odoo-11-Felder (mit Grund)
BEWUSST_WEGFALLEND = {
    "analytic_account_id": "Kostenstelle: in Odoo 11 auf 0 Auftragszeilen belegt; Odoo 18 nutzt "
                            "analytic_distribution",
    "confirmation_date": "in Odoo 18 entfallen; gleichwertig date_order bzw. date",
}

# Stammdaten (Feld auf sale.order/sale.order.line -> Zielmodell, Anzeigefeld)
STAMMDATEN = [
    ("sale.order", "payment_term_id", "account.payment.term", "Zahlungsbedingungen"),
    ("sale.order", "pricelist_id", "product.pricelist", "Preislisten"),
    ("sale.order", "team_id", "crm.team", "Verkaufsteams/Vertriebskanaele"),
    ("sale.order", "fiscal_position_id", "account.fiscal.position", "Steuerzuordnungen"),
    ("sale.order", "incoterm", "account.incoterms", "Incoterms"),
    ("sale.order", "source_id", "utm.source", "UTM-Quellen"),
    ("sale.order", "medium_id", "utm.medium", "UTM-Medien"),
    ("sale.order", "campaign_id", "utm.campaign", "UTM-Kampagnen"),
    ("sale.order", "currency_id", "res.currency", "Waehrungen"),
    ("sale.order", "layout_category_id", "sale.layout.category", "Reportlayout-Kategorien"),
    ("sale.order.line", "product_id", "product.product", "Produkte"),
    ("sale.order.line", "tax_id", "account.tax", "Steuern"),
]
FELD_ANZEIGE = {"account.payment.term": "name", "product.pricelist": "name", "crm.team": "name",
                "account.fiscal.position": "name", "account.incoterms": "name", "utm.source": "name",
                "utm.medium": "name", "utm.campaign": "name", "res.currency": "name",
                "product.product": "display_name", "account.tax": "name"}


def lese_feldwerte(client, modell, feld, domain=None):
    """Alle belegten Werte eines Many2one-Auswahlfelds samt Anzahl."""
    domain = (domain or []) + [(feld, "!=", False)]
    gruppen = client.kw(modell, "read_group", [domain, [feld], [feld]], context=SP)
    ergebnis = []
    for g in gruppen:
        wert = g.get(feld)
        if wert:
            ergebnis.append({"id": wert[0], "name": wert[1], "anzahl": g.get("%s_count" % feld) or g.get("__count")})
    return sorted(ergebnis, key=lambda x: -(x["anzahl"] or 0))


def main() -> int:
    ergebnis = {}
    luecken = []
    hinweise = []

    print("Lueckenanalyse Verkauf (Teil 5, Block 2)")
    print("Odoo 11 wird ausschliesslich lesend gelesen.\n")
    k11, k18 = o11(), o18("lokal")
    kvm = o18("vm")

    # ---------- A) Felder ----------
    print("=== A) Felder ===")
    felder11 = json.load(open(os.path.join(REPO, "docs", "_verkauf_teil2_felder.json"), encoding="utf-8"))
    felder_o18 = {m: {f["name"] for f in k18.kw("ir.model.fields", "search_read",
                                                [[("model", "=", m)], ["name"]], context=SP)}
                  for m in ("sale.order", "sale.order.line")}
    felder_vm = {m: {f["name"] for f in kvm.kw("ir.model.fields", "search_read",
                                               [[("model", "=", m)], ["name"]], context=SP)}
                 for m in ("sale.order", "sale.order.line")}
    a_ergebnis = {}
    for modell in ("sale.order", "sale.order.line"):
        daten = felder11["o11"][modell]["felder"]
        belegt = {n: v for n, v in daten.items()
                  if (v.get("belegt") or 0) > 0 and not n.startswith("__")}
        fehlend = []
        for name, info in sorted(belegt.items(), key=lambda x: -x[1]["belegt"]):
            in18 = name in felder_o18[modell]
            in_vm = name in felder_vm[modell]
            if not in18 or not in_vm:
                grund = BEWUSST_WEGFALLEND.get(name)
                eintrag = {"feld": name, "belegt_o11": info["belegt"],
                           "lokal": in18, "vm": in_vm, "bewertet": grund}
                fehlend.append(eintrag)
                if not grund:
                    luecken.append("Feld %s.%s in Odoo 11 auf %d Datensaetzen belegt, fehlt in Odoo 18"
                                   % (modell, name, info["belegt"]))
                else:
                    hinweise.append("Feld %s.%s entfaellt bewusst (%s)" % (modell, name, grund))
        a_ergebnis[modell] = {"belegte_felder": len(belegt), "nicht_in_o18": fehlend}
        print("  %s: %d belegte Felder in Odoo 11, davon %d ohne Entsprechung in Odoo 18"
              % (modell, len(belegt), len(fehlend)))
        for e in fehlend:
            print("     %-32s belegt %-6s lokal=%s vm=%s %s"
                  % (e["feld"], e["belegt_o11"], e["lokal"], e["vm"],
                     ("(bewusst: %s)" % e["bewertet"][:60]) if e["bewertet"] else "<-- LUECKE"))
    ergebnis["A_felder"] = a_ergebnis

    # ---------- B) Modelle der Verkaufsmenues ----------
    print("\n=== B) Modelle der Odoo-11-Verkaufsmenues ===")
    modelle_o18 = {m["model"] for m in k18.kw("ir.model", "search_read", [[], ["model"]], context=SP)}
    modelle_vm = {m["model"] for m in kvm.kw("ir.model", "search_read", [[], ["model"]], context=SP)}
    ziele11 = {}
    aktionen = k11.kw("ir.actions.act_window", "search_read",
                      [[("res_model", "!=", False)], ["name", "res_model"]], context=SP)
    wizards = {a["name"]: a["res_model"] for a in aktionen
               if a["res_model"].startswith(("sale.", "report.all", "crm."))}
    for name, modell in sorted(wizards.items()):
        fehlt_lokal = modell not in modelle_o18
        fehlt_vm = modell not in modelle_vm
        eintrag = {"aktion": name, "modell": modell, "lokal": not fehlt_lokal, "vm": not fehlt_vm}
        ziele11[name] = eintrag
        if fehlt_lokal or fehlt_vm:
            luecken.append("Modell %s (Aktion '%s') fehlt in Odoo 18" % (modell, name))
            print("  FEHLT %-34s %s" % (modell, name))
    print("  geprueft: %d Aktionen auf Verkaufs-/Berichts-/CRM-Modellen, %d ohne Modell in Odoo 18"
          % (len(ziele11), sum(1 for v in ziele11.values() if not (v["lokal"] and v["vm"]))))
    ergebnis["B_modelle"] = ziele11

    # ---------- C) Automatismen ----------
    print("\n=== C) Automatismen auf sale.order ===")
    automatismen = {}
    for name, k in (("o11", k11), ("o18lokal", k18), ("o18vm", kvm)):
        try:
            bas = k.kw("base.automation", "search_read",
                       [[("model_id.model", "=", "sale.order")], ["name", "trigger", "active"]],
                       context=SP)
        except Exception as ex:
            bas = [{"name": "nicht messbar: %s" % str(ex)[:80], "trigger": "", "active": False}]
        try:
            skripte = k.kw("ir.actions.server", "search_read",
                           [[("model_id.model", "=", "sale.order")], ["name", "state", "active"]],
                           context=SP)
        except Exception as ex:
            skripte = [{"name": "nicht messbar: %s" % str(ex)[:80], "state": "", "active": False}]
        automatismen[name] = {"automatisierte_aktionen": bas, "server_aktionen": skripte}
        print("  %-8s automatisierte Aktionen: %s" % (name, [b["name"] for b in bas]))
        print("  %-8s Server-Aktionen:        %s" % ("", [s["name"] for s in skripte]))
    ergebnis["C_automatismen"] = automatismen

    # ---------- D) Mailvorlagen ----------
    print("\n=== D) Mailvorlagen fuer sale.order ===")
    vorlagen = {}
    for name, k in (("o11", k11), ("o18", k18)):
        vs = k.kw("mail.template", "search_read", [[("model", "=", "sale.order")], ["name"]],
                  context=SP)
        vorlagen[name] = [v["name"] for v in vs]
        print("  %-4s %d: %s" % (name, len(vs), [v["name"] for v in vs]))
    ergebnis["D_mailvorlagen"] = vorlagen

    # ---------- E) Stammdaten ----------
    print("\n=== E) Verwendete Stammdaten (Odoo 11) gegen Odoo 18 ===")
    stammdaten = []
    for modell, feld, ziel, titel in STAMMDATEN:
        if ziel == "sale.layout.category":
            hinweise.append("Reportlayout-Kategorien (sale.layout.category): in Odoo 11 nicht "
                            "registriert (totes Menue), in Odoo 18 nicht noetig")
            continue
        try:
            werte = lese_feldwerte(k11, modell, feld)
        except Exception as ex:
            print("  %-28s nicht messbar (%s)" % (titel, str(ex)[:60]))
            continue
        anzeige = FELD_ANZEIGE.get(ziel, "name")
        fehlend = []
        for w in werte:
            treffer = k18.kw(ziel, "search_count", [[(anzeige, "=", w["name"])]], context=SP)
            w["in_o18"] = bool(treffer)
            if not treffer:
                fehlend.append(w["name"])
        stammdaten.append({"titel": titel, "modell": modell, "feld": feld, "ziel": ziel,
                           "werte": werte, "fehlend_in_o18": fehlend})
        print("  %-28s %d verwendete Werte, in Odoo 18 fehlend: %s"
              % (titel, len(werte), fehlend or "keiner"))
        for w in werte[:6]:
            print("      %-42s %5s Verwendungen %s" % (w["name"][:42], w["anzahl"],
                                                       "vorhanden" if w["in_o18"] else "FEHLT"))
        if fehlend:
            luecken.append("Stammdaten %s: %d von %d in Odoo 11 verwendeten Werten fehlen in Odoo 18: %s"
                           % (titel, len(fehlend), len(werte), ", ".join(fehlend[:5])))
    ergebnis["E_stammdaten"] = stammdaten

    # ---------- F) Berichte/Ansichten ----------
    print("\n=== F) Berichte und Ansichten (Kurzabgleich) ===")
    for name, k in (("o11", k11), ("o18", k18), ("o18vm", kvm)):
        rep = k.kw("ir.actions.report", "search_read", [[("model", "=", "sale.order")], ["name"]],
                   context=SP)
        views = k.kw("ir.ui.view", "search_read",
                     [[("model", "=", "sale.order"), ("type", "in", ["list", "tree", "kanban",
                                                                     "pivot", "graph", "calendar"])],
                      ["type"]], context=SP)
        typen = {}
        for v in views:
            typen[v["type"]] = typen.get(v["type"], 0) + 1
        print("  %-6s Druckberichte %d %s | Ansichtstypen %s" % (name, len(rep),
                                                                 [r["name"] for r in rep][:6], typen))
        ergebnis.setdefault("F_berichte", {})[name] = {"druckberichte": [r["name"] for r in rep],
                                                       "ansichtstypen": typen}

    print("\n=== Ergebnis ===")
    print("Echte Luecken: %d" % len(luecken))
    for l in luecken:
        print("  LUECKE %s" % l)
    print("Dokumentierte Abweichungen/Hinweise: %d" % len(hinweise))
    for h in hinweise:
        print("  Hinweis %s" % h)

    ziel = os.path.join(REPO, "docs", "_verkauf_teil5_luecken.json")
    with open(ziel, "w", encoding="utf-8") as fh:
        json.dump({"ergebnis": ergebnis, "luecken": luecken, "hinweise": hinweise}, fh,
                  ensure_ascii=False, indent=1)
    print("\nRohdaten: %s" % ziel)
    return 1 if luecken else 0


if __name__ == "__main__":
    raise SystemExit(main())
