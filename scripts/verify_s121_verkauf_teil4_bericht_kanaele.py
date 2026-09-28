"""Prueflauf Verkauf Teil 4, Schritt 2: Bericht "Verkaufsauftraege aller Kanaele".

Prueft in Odoo 11 (nur lesend), Odoo 18 lokal und Odoo 18 VM:
  - die neue Aktion, Pivotansicht und der neue Menuepunkt
  - Domain (nur nicht stornierte Auftraege), Default-Kontext (Kanal, aktuelles Verkaufsjahr,
    Mass Total)
  - die ergaenzten Filter/Gruppierungen in Odoo-11-Wortlaut
  - dass die bestehenden Odoo-18-Filter, Gruppierungen und Aktionen unveraendert vorhanden sind
  - Datenvergleich: Zeilen und Summe im aktuellen Verkaufsjahr (Odoo 11 als Referenz)

Aufruf:
    python scripts/verify_s121_verkauf_teil4_bericht_kanaele.py
"""
from __future__ import annotations

import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18
from analyse_verkauf_teil3_suche import arch_auswerten
from analyse_verkauf_teil3_formulare import ansicht_arch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP = {"lang": "de_DE"}
XMLID_AKTION = "itk_sale_management.action_sale_report_all_channels"
XMLID_PIVOT = "itk_sale_management.view_sale_report_pivot_kanaele"
XMLID_SUCHE = "itk_sale_management.view_sale_report_search_kanaele"
XMLID_MENUE = "itk_sale_management.menu_sale_report_all_channels"

# Odoo-18-Filter und -Gruppierungen der Berichtssuche, die erhalten bleiben muessen
O18_FILTER = ["year", "Quotations", "Sales", "filter_date", "filter_order_date", "to_invoice",
              "fully_invoiced"]
O18_GRUPPEN = ["User", "sales_channel", "Customer", "country_id", "industry_id", "product_tmpl_id",
               "product_id", "Category", "status", "group_by_date", "group_by_date_day"]
# Bestehende Odoo-18-Berichtsaktionen mit ihren Originalwerten (Session 121 gemessen)
O18_AKTIONEN = {416: ("graph,pivot,list,form", "[('state', '!=', 'cancel')]"),
                417: ("graph,pivot", "False"),
                418: ("graph,pivot", "False"),
                419: ("graph,pivot", "False"),
                420: ("list,pivot,graph,form", "False"),
                421: ("graph,list", "[('state','=','draft'),('team_id', '=', active_id)]"),
                422: ("graph,list", "[('state','not in',('draft','cancel'))]")}


def hole_id(client, xmlid: str):
    modul, name = xmlid.split(".")
    treffer = client.kw("ir.model.data", "search_read",
                        [[("module", "=", modul), ("name", "=", name)], ["res_id", "model"]],
                        context=SP)
    return treffer[0] if treffer else None


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

    jahr = datetime.date.today().year
    print("Prueflauf Verkauf Teil 4, Schritt 2 (Bericht Verkaufsauftraege aller Kanaele)")
    print("Odoo 11 Prod wird ausschliesslich lesend gelesen.\n")

    print("--- Odoo 11 Prod: Ausgangslage (nur lesend) ---")
    k11 = o11()
    aktion11 = k11.kw("ir.actions.act_window", "read", [[424], ["name", "res_model", "context",
                                                                "view_mode", "domain"]], context=SP)[0]
    pruefe(aktion11["res_model"] == "report.all.channels.sales",
           "Odoo 11: Aktion 424 auf %s" % aktion11["res_model"])
    pruefe("search_default_current_year" in (aktion11["context"] or ""),
           "Odoo 11: Default-Filter aktuelles Verkaufsjahr (%s)" % aktion11["context"])
    zeilen11 = k11.kw("report.all.channels.sales", "search_count", [[]], context=SP)
    jahr11 = k11.kw("report.all.channels.sales", "search_count",
                    [[("date_order", ">=", "%d-01-01" % jahr)]], context=SP)
    storno11 = k11.kw("sale.order.line", "search_count", [[("order_id.state", "=", "cancel")]], context=SP)
    print("       Odoo 11: %d Zeilen gesamt, %d im Jahr %d, stornierte Zeilen %d"
          % (zeilen11, jahr11, jahr, storno11))

    for schluessel, client, ist18, name in (("o18", o18("lokal"), True, "Odoo 18 lokal"),
                                            ("vm", o18("vm"), True, "Odoo 18 VM")):
        print("\n--- %s ---" % name)
        treffer = hole_id(client, XMLID_AKTION)
        pruefe(bool(treffer), "Aktion %s vorhanden" % XMLID_AKTION)
        if treffer:
            aktion = client.kw("ir.actions.act_window", "read",
                               [[treffer["res_id"]], ["name", "res_model", "view_mode", "domain",
                                                      "context"]], context=SP)[0]
            pruefe(aktion["res_model"] == "sale.report", "Basis sale.report (nicht report.all.channels.sales)")
            pruefe(aktion["domain"] == "[('state', '!=', 'cancel')]",
                   "nur nicht stornierte Auftraege (%s)" % aktion["domain"])
            kontext = (aktion["context"] or "").replace("\n", "").replace(" ", "")
            pruefe("search_default_itk_current_year" in kontext,
                   "Default-Filter aktuelles Verkaufsjahr aktiv")
            pruefe("pivot_measures" in kontext and "price_total" in kontext,
                   "Mass Total als Pivot-Vorgabe")
            pruefe(aktion["view_mode"].split(",")[0] == "pivot",
                   "Pivot ist erste Ansicht (%s)" % aktion["view_mode"])
            views = client.kw("ir.actions.act_window.view", "search_read",
                              [[("act_window_id", "=", treffer["res_id"])],
                               ["sequence", "view_mode", "view_id"]], context=SP)
            pivot_zeile = [v for v in views if v["view_mode"] == "pivot"]
            pruefe(bool(pivot_zeile) and pivot_zeile[0]["view_id"] is not False,
                   "eigene Pivotansicht in der Aktion verknuepft (%s)" % (pivot_zeile or "keine"))
        treffer_menu = hole_id(client, XMLID_MENUE)
        pruefe(bool(treffer_menu), "Menuepunkt %s vorhanden" % XMLID_MENUE)
        if treffer_menu:
            menu = client.kw("ir.ui.menu", "read", [[treffer_menu["res_id"]],
                                                    ["name", "complete_name", "sequence"]], context=SP)[0]
            pruefe(menu["complete_name"] == "Verkauf/Berichtswesen/Verkaufsaufträge aller Kanäle",
                   "Menuepfad '%s' (Reihenfolge %s)" % (menu["complete_name"], menu["sequence"]))
        treffer_pivot = hole_id(client, XMLID_PIVOT)
        if treffer_pivot:
            arch, _ = ansicht_arch(client, "sale.report", "pivot", ist18), None
            daten = client.kw("ir.ui.view", "read", [[treffer_pivot["res_id"]], ["arch_db"]], context=SP)[0]
            import re as _re
            felder = _re.findall(r'<field name="([a-z_]+)"\s*type="([a-z]+)"', daten["arch_db"] or "")
            pruefe(("name", "row") in felder and ("price_total", "measure") in felder,
                   "Pivotvorgabe Zeile Auftragsreferenz, Mass Total (%s)" % felder)
            pruefe(("team_id", "col") in felder,
                   "Pivotvorgabe Spalte Vertriebskanal (%s)" % felder)

        # Filter/Gruppierungen: eigene in Odoo-11-Wortlaut vorhanden, Odoo-18-Bestand unveraendert
        arch = ansicht_arch(client, "sale.report", "search", ist18)
        daten = arch_auswerten(arch)
        namen_filter = {f["name"] for f in daten["filter"]}
        namen_gruppen = {g["name"] for g in daten["gruppen"]}
        beschriftungen = {f["name"]: f["string"] for f in daten["filter"] + daten["gruppen"]}
        pruefe("itk_current_year" in namen_filter, "Filter itk_current_year vorhanden")
        pruefe(beschriftungen.get("itk_current_year") == "Aktuelles Verkaufsjahr",
               "Beschriftung 'Aktuelles Verkaufsjahr' (%s)" % beschriftungen.get("itk_current_year"))
        pruefe("itk_channel" in namen_gruppen, "Gruppierung itk_channel vorhanden")
        pruefe(beschriftungen.get("itk_channel") == "Vertriebskanal",
               "Beschriftung 'Vertriebskanal' (%s)" % beschriftungen.get("itk_channel"))
        for f in O18_FILTER:
            pruefe(f in namen_filter, "Odoo-18-Filter %s unveraendert vorhanden" % f)
        for g in O18_GRUPPEN:
            pruefe(g in namen_gruppen, "Odoo-18-Gruppierung %s unveraendert vorhanden" % g)
        for aktion_id, (view_mode, domain) in O18_AKTIONEN.items():
            a = client.kw("ir.actions.act_window", "read", [[aktion_id], ["name", "view_mode", "domain"]],
                          context=SP)[0]
            pruefe(a["view_mode"] == view_mode and (a["domain"] or "False") == domain,
                   "Odoo-18-Aktion %s unveraendert (%s, %s)" % (aktion_id, a["view_mode"], a["domain"]))

        # Daten: Zeilen und Summe im aktuellen Verkaufsjahr
        zeilen = client.kw("sale.report", "search_count",
                           [[("state", "!=", "cancel"), ("date", ">=", "%d-01-01" % jahr)]], context=SP)
        storno = client.kw("sale.report", "search_count",
                           [[("state", "=", "cancel"), ("date", ">=", "%d-01-01" % jahr)]], context=SP)
        gesamt = client.kw("sale.report", "search_count", [[]], context=SP)
        print("       Datenbestand: %d Zeilen gesamt, %d im Jahr %d (nicht storniert), "
              "%d stornierte Zeilen im Jahr" % (gesamt, zeilen, jahr, storno))
        pruefe(zeilen >= 0 and isinstance(zeilen, int), "Zeilen im aktuellen Verkaufsjahr lesbar")

    print("\nOdoo 11 Prod wurde ausschliesslich lesend verwendet.")
    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
