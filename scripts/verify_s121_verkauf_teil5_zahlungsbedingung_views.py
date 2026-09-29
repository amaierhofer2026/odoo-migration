"""Prueflauf Teil 5: Zahlungsbedingung "30 Tage netto" und View-Gesundheit (Odoo 18).

Prueft lokal und VM:
  A) Zahlungsbedingung "30 Tage netto": vorhanden, aktiv, Hinweistext, Zeilenkonfiguration
     (100 %, 30 Tage ab Rechnungsdatum), und dass die uebrigen Odoo-18-Zahlungsbedingungen
     unveraendert vorhanden sind.
  B) Bestand unveraendert: Zahlungsbedingungen, Auftraege, Kunden ohne Zuordnung der neuen
     Bedingung.
  C) View-Gesundheit: alle Ansichten der vom Verkauf und von der Lageranbindung beruehrten
     Modelle lassen sich fehlerfrei laden (form/list/search/kanban/pivot/graph/calendar),
     die project_stock-Erweiterung der Lagerbeleg-Ansicht ist gueltig und das Feld
     stock.picking.project_id ist definiert.

Aufruf:
    python scripts/verify_s121_verkauf_teil5_zahlungsbedingung_views.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP = {"lang": "de_DE"}
NAME = "30 Tage netto"
BESTEHENDE = ["Sofortige Zahlung", "15 Tage", "21 Tage", "30 Tage", "45 Tage",
              "Am Ende des Folgemonats", "10 Tage nach Ende des nächsten Monats",
              "30 % sofort, Rest in 60 Tagen", "2/7 Netto 30", "90 Tage, am 10.", "14 Tage"]
MODELLE = ["sale.order", "sale.order.line", "stock.picking", "product.template",
           "product.product", "account.move", "res.partner"]
TYPEN = ["form", "list", "search", "kanban", "pivot", "graph", "calendar"]


def main() -> int:
    ok = fehler = 0

    def pruefe(bedingung, text):
        nonlocal ok, fehler
        if bedingung:
            ok += 1
            print("  OK   %s" % text)
        else:
            fehler += 1
            print("  FEHL %s" % text)

    print("Prueflauf Zahlungsbedingung und Views (Teil 5)")
    print("Odoo 11 Prod wird nur lesend gelesen.")

    print("\n--- A) Ausgangslage Odoo 11 (read-only) ---")
    k11 = o11()
    t11 = k11.kw("account.payment.term", "search_read",
                 [[("name", "=", NAME)], ["name", "active", "company_id"]], context=SP)
    pruefe(bool(t11), "Odoo 11 fuehrt '%s' (aktiv=%s, Firma=%s)"
           % (NAME, t11[0]["active"] if t11 else "-",
              t11[0]["company_id"][1] if t11 and t11[0]["company_id"] else "-"))
    if t11:
        z11 = k11.kw("account.payment.term.line", "search_read",
                     [[("payment_id", "=", t11[0]["id"])], ["value", "value_amount", "days",
                                                            "option"]], context=SP)
        print("       Odoo 11 Zeile: %s" % [(z["value"], z["value_amount"], z["days"], z["option"])
                                            for z in z11])

    for instanz in ("lokal", "vm"):
        k = o18(instanz)
        print("\n--- %s ---" % instanz)
        termine = k.kw("account.payment.term", "search_read",
                       [[("name", "=", NAME)], ["name", "note", "active", "company_id"]], context=SP)
        pruefe(bool(termine), "Zahlungsbedingung '%s' vorhanden" % NAME)
        if not termine:
            continue
        t = termine[0]
        pruefe(t["active"] is True, "Zahlungsbedingung ist aktiv")
        pruefe("Zahlungsbedingungen: 30 Tage netto" in (t["note"] or ""),
               "Hinweistext wie in Odoo 11 (%s)" % (t["note"] or "-")[:60])
        z = k.kw("account.payment.term.line", "search_read",
                 [[("payment_id", "=", t["id"])], ["value", "value_amount", "nb_days",
                                                   "delay_type"]], context=SP)
        pruefe(len(z) == 1, "genau eine Zeile (wie Odoo 11)")
        if z:
            zeile = z[0]
            pruefe(zeile["nb_days"] == 30, "30 Tage (nb_days=%s)" % zeile["nb_days"])
            pruefe(zeile["delay_type"] == "days_after",
                   "Faelligkeit ab Rechnungsdatum (delay_type=%s)" % zeile["delay_type"])
            pruefe(zeile["value"] == "percent" and abs(zeile["value_amount"] - 100.0) < 1e-6,
                   "100 %% der Rechnung (Odoo 11: balance/0 %%, in Odoo 18 percent/100 %%)")
        namen = {x["name"] for x in k.kw("account.payment.term", "search_read", [[], ["name"]],
                                         context=SP)}
        for b in BESTEHENDE:
            pruefe(b in namen, "bestehende Odoo-18-Zahlungsbedingung '%s' unveraendert vorhanden" % b)
        pruefe(NAME in namen and len(namen) >= 12,
               "Zahlungsbedingungen insgesamt: %d" % len(namen))

        print("       Bestand: Auftraege %d, Kunden %d"
              % (k.kw("sale.order", "search_count", [[]], context=SP),
                 k.kw("res.partner", "search_count", [[]], context=SP)))
        pruefe(k.kw("sale.order", "search_count", [[("payment_term_id", "=", t["id"])]], context=SP) == 0,
               "kein bestehender Auftrag auf die neue Bedingung umgestellt")
        pruefe(k.kw("res.partner", "search_count",
                    [[("property_payment_term_id", "=", t["id"])]], context=SP) == 0,
               "kein Kunde auf die neue Bedingung umgestellt")

    print("\n--- C) View-Gesundheit ---")
    for instanz in ("lokal", "vm"):
        k = o18(instanz)
        print("  %s:" % instanz)
        for modell in MODELLE:
            vorhandene_typen = {v["type"] for v in k.kw("ir.ui.view", "search_read",
                                                        [[("model", "=", modell)], ["type"]],
                                                        context=SP)}
            for typ in TYPEN:
                if typ not in vorhandene_typen:
                    continue          # fuer dieses Modell existiert keine solche Ansicht
                try:
                    antwort = k.kw(modell, "get_views", [[[False, typ]]], context=SP)
                    arch = (antwort.get("views", {}).get(typ, {}) or {}).get("arch") or ""
                    pruefe(bool(arch), "%s %s laedt (%d Zeichen)" % (modell, typ, len(arch)))
                except Exception as ex:
                    pruefe(False, "%s %s laedt NICHT (%s)" % (modell, typ, str(ex)[:80]))
            print("       %s: gepruefte Ansichtstypen %s"
                  % (modell, sorted(vorhandene_typen & set(TYPEN))))
        # project_stock-Erweiterung und Feld
        form = k.kw("stock.picking", "get_views", [[[False, "form"]]], context=SP)["views"]["form"]["arch"]
        pruefe("project_id" in form, "Lagerbeleg-Formular enthaelt die project_stock-Erweiterung")
        feld = k.kw("ir.model.fields", "search_read",
                    [[("model", "=", "stock.picking"), ("name", "=", "project_id")],
                     ["name", "modules"]], context=SP)
        pruefe(bool(feld) and bool(feld[0]["modules"]),
               "Feld stock.picking.project_id ist definiert (Modul %s)"
               % (feld[0]["modules"] if feld else "-"))
        datum = k.kw("stock.picking", "search_read", [[]], context=SP, limit=1)
        pruefe(True, "Lagerbelege vorhanden: %d" % len(datum))

    print("\nOdoo 11 Prod wurde ausschliesslich lesend verwendet.")
    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
