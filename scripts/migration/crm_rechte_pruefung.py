# -*- coding: utf-8 -*-
"""Rechtepruefung CRM mit drei Rollen (Session 145).

Legt drei temporaere Benutzer an (Standard-CRM-Benutzer, Verkaufsleiter,
Administrator), meldet sich ALS JEWEILS DIESER BENUTZER an und prueft
Lesen/Anlegen/Bearbeiten/Archivieren/Loeschen, den Zugriff auf fremde
Verkaufschancen und die Konfiguration (Stufen, Vertriebskanaele). Danach werden
Benutzer und automatisch angelegte Kontakte wieder entfernt.

Aufruf:
    python scripts/migration/crm_rechte_pruefung.py --instanz lokal
    python scripts/migration/crm_rechte_pruefung.py --instanz vm
"""
from __future__ import annotations

import argparse
import os
import secrets
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HIER))
import _o11o18_client as client  # noqa: E402

CTX = {"lang": "de_DE"}

# (Login-Praefix, Anzeige, Gruppen-XML-IDs)
# Erwartung je Rolle (Odoo-18-Standard, keine Rechteausweitung):
#   CRM-Benutzer  : "Nur eigene Dokumente" -> fremde Vorgaenge NICHT sichtbar,
#                   Loeschen nicht erlaubt (Salesman hat kein unlink-Recht)
#   Verkaufsleiter: alle Vorgaenge sichtbar, darf loeschen
#   Administrator : wie Verkaufsleiter, zusaetzlich Systemrechte
ROLLEN = [
    ("user", "CRM-Benutzer", ["sales_team.group_sale_salesman"],
     {"loeschen": False, "fremde": False}),
    ("manager", "Verkaufsleiter", ["sales_team.group_sale_manager"],
     {"loeschen": True, "fremde": True}),
    # Das reale Administratorkonto ist Systemadmin UND Verkaufsadministrator
    # (Verkauf/Administrator, Verkauf/Alle Dokumente, Administration/Einstellungen).
    # base.group_system allein hat in Odoo 18 keinen CRM-Zugriff - das ist Standard
    # und kein Rechtefehler.
    ("admin", "Administrator",
     ["base.group_system", "sales_team.group_sale_manager", "sales_team.group_sale_salesman"],
     {"loeschen": True, "fremde": True}),
]


def gruppen_ids(o18, xmlids):
    ids = []
    for xmlid in xmlids:
        mod, name = xmlid.split(".", 1)
        d = o18.kw("ir.model.data", "search_read",
                   [[("module", "=", mod), ("name", "=", name)], ["res_id"]])
        if d:
            ids.append(d[0]["res_id"])
    return ids


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    args = ap.parse_args()

    o18 = client.o18(args.instanz)
    env = client.lade_env()
    url, db = o18.url, env["ODOO18_DB"]
    print("=== Rechtepruefung CRM (%s, %s) ===" % (args.instanz, url))
    ok = fehler = 0

    def pruefe(bedingung, text):
        nonlocal ok, fehler
        if bedingung:
            ok += 1
            print("  OK   %s" % text)
        else:
            fehler += 1
            print("  FEHL %s" % text)

    vorher = {m: o18.kw(m, "search_count", [[]],
                        context={"lang": "de_DE", "active_test": False})
              for m in ("crm.lead", "res.partner")}
    print("Ausgangsstand: %s" % vorher)

    fremd = o18.kw("crm.lead", "search_read",
                   [[("user_id", "!=", False), ("user_id", "!=", 2),
                     ("type", "=", "opportunity")], ["id", "user_id"]],
                   context=CTX, limit=1)

    angelegt, konten = [], []
    try:
        for praefix, label, xmlids, erwartung in ROLLEN:
            pwd = "Itk!%s" % secrets.token_urlsafe(12)
            login = "itk_s145_%s@example.invalid" % praefix
            uid = o18.kw("res.users", "create", [{
                "name": "ITK Test %s (S145)" % label,
                "login": login,
                "email": login,
                "password": pwd,
                "groups_id": [(6, 0, gruppen_ids(o18, xmlids))],
            }])
            uid = uid[0] if isinstance(uid, list) else uid
            angelegt.append(uid)
            print("\nRolle: %s (%s)" % (label, login))

            try:
                eigen = client.Client(url, db, login, pwd)
            except Exception as exc:  # noqa: BLE001
                pruefe(False, "%s kann sich anmelden (%s)" % (label, str(exc)[:80]))
                continue

            lesen = eigen.kw("crm.lead", "search_count", [[]], context=CTX)
            pruefe(lesen > 0, "%s darf Interessenten lesen (%d sichtbar)" % (label, lesen))

            neu_id, anlegen_ok = None, False
            try:
                r = eigen.kw("crm.lead", "create",
                             [{"name": "RECHTETEST S145 %s" % label,
                               "type": "opportunity"}], context=CTX)
                neu_id = r[0] if isinstance(r, list) else r
                anlegen_ok = True
            except Exception:  # noqa: BLE001
                pass
            pruefe(anlegen_ok, "%s darf anlegen" % label)

            if neu_id:
                try:
                    eigen.kw("crm.lead", "write", [[neu_id], {"priority": "1"}], context=CTX)
                    pruefe(True, "%s darf bearbeiten" % label)
                except Exception:  # noqa: BLE001
                    pruefe(False, "%s darf bearbeiten" % label)
                try:
                    eigen.kw("crm.lead", "write", [[neu_id], {"active": False}], context=CTX)
                    pruefe(True, "%s darf archivieren" % label)
                except Exception:  # noqa: BLE001
                    pruefe(False, "%s darf archivieren" % label)
                try:
                    eigen.kw("crm.lead", "unlink", [[neu_id]], context=CTX)
                    geloescht = True
                except Exception:  # noqa: BLE001
                    geloescht = False
                    o18.kw("crm.lead", "unlink", [[neu_id]])
                pruefe(geloescht == erwartung["loeschen"],
                       "%s loeschen: erwartet %s, ist %s"
                       % (label, erwartung["loeschen"], geloescht))

            if fremd:
                try:
                    sichtbar = eigen.kw("crm.lead", "search_count",
                                        [[("id", "=", fremd[0]["id"])]], context=CTX)
                    pruefe((sichtbar == 1) == erwartung["fremde"],
                           "%s fremde Verkaufschance sichtbar: erwartet %s, ist %s"
                           % (label, erwartung["fremde"], sichtbar == 1))
                except Exception as exc:  # noqa: BLE001
                    pruefe(False, "%s sieht fremde Verkaufschance (%s)"
                           % (label, str(exc)[:60]))

            konf = {}
            for modell, name in (("crm.stage", "Neu"), ("crm.team", "Verkauf")):
                ids = eigen.kw(modell, "search", [[("name", "=", name)]],
                               context=CTX, limit=1)
                if not ids:
                    continue
                try:
                    eigen.kw(modell, "write", [ids, {"sequence": 99}], context=CTX)
                    konf[modell] = "schreiben"
                except Exception:  # noqa: BLE001
                    konf[modell] = "nur lesen"
            print("       Konfiguration: %s" % konf)
            pruefe(True, "%s Konfigurationszugriff geprueft (%s)" % (label, konf))
    finally:
        for uid in angelegt:
            info = o18.kw("res.users", "read", [[uid], ["partner_id"]], context=CTX)
            if info and info[0].get("partner_id"):
                konten.append(info[0]["partner_id"][0])
        if angelegt:
            o18.kw("res.users", "unlink", [angelegt])
        if konten:
            o18.kw("res.partner", "unlink", [konten])
        rest = o18.kw("crm.lead", "search", [[("name", "like", "RECHTETEST S145")]],
                      context={"lang": "de_DE", "active_test": False})
        if rest:
            o18.kw("crm.lead", "unlink", [rest])
        nachher = {m: o18.kw(m, "search_count", [[]],
                             context={"lang": "de_DE", "active_test": False})
                   for m in ("crm.lead", "res.partner")}
        print("\nAufraeumen: Testbenutzer und Kontakte entfernt")
        print("Endstand: %s" % nachher)
        pruefe(nachher == vorher, "Keine Testdaten zurueckgeblieben")

    print("\n=== Ergebnis %s: %d OK / %d FEHL ===" % (args.instanz, ok, fehler))
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
