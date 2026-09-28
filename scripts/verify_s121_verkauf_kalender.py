"""Prueflauf Verkauf Teil 4: Kalenderergaenzung (Option A) fuer Odoo 18.

Prueft:
  - Odoo 11 (nur lesend): Ausgangslage - Kalenderansicht mit date_start = date_order
  - Odoo 18 lokal und VM: die eigene Kalenderansicht "Auftragsdatum" existiert und basiert auf
    date_order (color = state), der eigene Menuepunkt haengt unter Verkauf/Auftraege, die Aktion
    zeigt den Kalender zuerst
  - Odoo 18: der Aktivitaetenkalender (sale.view_sale_order_calendar) bleibt unveraendert und
    bleibt der Standardkalender der Verkaufsmenues; die Aktivitaetenansicht bleibt vorhanden
  - Odoo 18: die Verkaufsmenues selbst sind unveraendert (Ansichtsarten und Kontexte)

Aufruf:
    python scripts/verify_s121_verkauf_kalender.py
"""
from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18
from analyse_verkauf_teil4_ansichten import ansicht_lesen, kalender_auswerten

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP = {"lang": "de_DE"}

MODELL = "sale.order"
XMLID_ANSICHT = "itk_sale_management.view_saleorder_kalender_itk"
XMLID_AKTION = "itk_sale_management.action_saleorder_kalender_itk"
XMLID_MENUE = "itk_sale_management.menu_saleorder_kalender_itk"
# Ausgangslage der Verkaufsmenues (nach Teil 3/4 unveraendert)
MENUES = {430: {"view_mode": "list,kanban,form,calendar,pivot,graph,activity", "kontext": "{}"},
          429: {"view_mode": "list,kanban,form,calendar,pivot,graph,activity", "kontext": "{}"},
          432: {"view_mode": "list,form,calendar,graph,pivot,kanban,activity", "kontext": "{'create': False}"},
          433: {"view_mode": "list,form,calendar,graph,pivot,kanban,activity", "kontext": "{'create': False}"}}


def hole_id(client, xmlid: str):
    modul, name = xmlid.split(".")
    treffer = client.kw("ir.model.data", "search_read",
                        [[("module", "=", modul), ("name", "=", name)], ["res_id", "model"]], context=SP)
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

    print("Prueflauf Verkauf Teil 4: Kalenderergaenzung (Auftragskalender nach Auftragsdatum)")
    print("Odoo 11 Prod wird ausschliesslich lesend gelesen.\n")

    print("--- Odoo 11 Prod: Ausgangslage ---")
    k11 = o11()
    arch, vid = ansicht_lesen(k11, False, "calendar", False)
    daten11 = kalender_auswerten(arch)
    pruefe(daten11["attrs"].get("date_start") == "date_order",
           "Odoo 11: Kalender nach date_order (Ansicht %s, color=%s)"
           % (vid, daten11["attrs"].get("color")))

    for schluessel, client, ist18, name in (("o18", o18("lokal"), True, "Odoo 18 lokal"),
                                            ("vm", o18("vm"), True, "Odoo 18 VM")):
        print("\n--- %s ---" % name)
        # 1. Eigene Kalenderansicht
        treffer = hole_id(client, XMLID_ANSICHT)
        pruefe(bool(treffer), "Kalenderansicht %s vorhanden" % XMLID_ANSICHT)
        if treffer:
            arch, echte_id = ansicht_lesen(client, treffer["res_id"], "calendar", ist18)
            daten = kalender_auswerten(arch)
            pruefe(daten["attrs"].get("date_start") == "date_order",
                   "Basis des Kalenders ist date_order (%s)" % daten["attrs"])
            pruefe(daten["attrs"].get("color") == "state", "Farbe nach Status")
            pruefe("partner_id" in daten["felder"] and "amount_total" in daten["felder"],
                   "Kalenderfelder Kunde und Betrag (%s)" % ", ".join(daten["felder"]))
            pruefe(daten["attrs"].get("string") == "Auftragskalender",
                   "Beschriftung '%s'" % daten["attrs"].get("string"))

        # 2. Eigene Aktion
        treffer = hole_id(client, XMLID_AKTION)
        pruefe(bool(treffer), "Aktion %s vorhanden" % XMLID_AKTION)
        if treffer:
            aktion = client.kw("ir.actions.act_window", "read",
                               [[treffer["res_id"]], ["name", "res_model", "view_mode", "views"]],
                               context=SP)[0]
            pruefe(aktion["res_model"] == MODELL, "Aktion auf %s" % aktion["res_model"])
            pruefe(aktion["view_mode"].split(",")[0] == "calendar",
                   "Kalender ist erste Ansicht (%s)" % aktion["view_mode"])
            views = client.kw("ir.actions.act_window.view", "search_read",
                              [[("act_window_id", "=", treffer["res_id"])],
                               ["sequence", "view_mode", "view_id"]], context=SP)
            kalender = [v for v in views if v["view_mode"] == "calendar"]
            pruefe(bool(kalender) and kalender[0]["view_id"] is not False,
                   "Kalenderansicht in der Aktion verknuepft (%s)" % (kalender or "keine"))

        # 3. Eigener Menuepunkt
        treffer = hole_id(client, XMLID_MENUE)
        pruefe(bool(treffer), "Menuepunkt %s vorhanden" % XMLID_MENUE)
        if treffer:
            menu = client.kw("ir.ui.menu", "read",
                             [[treffer["res_id"]], ["name", "complete_name", "parent_id", "sequence"]],
                             context=SP)[0]
            pruefe(menu["complete_name"] == "Verkauf/Aufträge/Auftragskalender",
                   "Menuepfad '%s' (Reihenfolge %s)" % (menu["complete_name"], menu["sequence"]))

        # 4. Odoo-18-Kalender und Aktivitaetenansicht unveraendert
        arch, vid = ansicht_lesen(client, 1214, "calendar", ist18)
        daten = kalender_auswerten(arch)
        pruefe(daten["attrs"].get("date_start") == "activity_date_deadline",
               "Aktivitaetenkalender unveraendert (date_start=%s)" % daten["attrs"].get("date_start"))
        for aktion_id, erwartet in MENUES.items():
            aktion = client.kw("ir.actions.act_window", "read",
                               [[aktion_id], ["view_mode", "context"]], context=SP)[0]
            gleich = (aktion["view_mode"] == erwartet["view_mode"]
                      and (aktion["context"] or "{}") == erwartet["kontext"])
            pruefe(gleich, "Menueaktion %s unveraendert (%s, %s)"
                   % (aktion_id, aktion["view_mode"], aktion["context"] or "{}"))

    print("\nOdoo 11 Prod wurde ausschliesslich lesend verwendet.")
    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
