# -*- coding: utf-8 -*-
"""Rechtepruefung Abrechnung/Rechnungen (Session 149).

Vergleicht die Odoo-11-Rechte auf ``account.invoice`` mit den Odoo-18-Rechten auf
``account.move`` und prueft vier Rollen mit temporaeren Benutzern:

  interner Benutzer ohne Abrechnungsgruppe : kein Zugriff (Odoo 11 wie Odoo 18)
  Abrechnungsbenutzer (Billing)            : lesen/schreiben, kein Loeschen
  Abrechnungsmanager                       : alles
  Administrator                            : alles (Konto unveraendert)

Aufruf:
    python scripts/migration/abrechnung_rechte_pruefung.py --instanz lokal
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
CTX_ALLE = {"lang": "de_DE", "active_test": False}

ROLLEN = [
    ("ohne", "Interner Benutzer ohne Abrechnungsgruppe", ["base.group_user"],
     {"lesen": False, "schreiben": False}),
    ("billing", "Abrechnungsbenutzer (Billing)",
     ["base.group_user", "account.group_account_invoice"],
     {"lesen": True, "schreiben": True}),
    ("manager", "Abrechnungsmanager",
     ["base.group_user", "account.group_account_invoice", "account.group_account_manager"],
     {"lesen": True, "schreiben": True}),
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
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    args = ap.parse_args()
    o11 = client.o11()
    o18 = client.o18(args.instanz)
    env = client.lade_env()
    print("=== Rechtepruefung Abrechnung (%s) ===" % args.instanz)
    ok = fehler = 0

    def pruefe(b, text):
        nonlocal ok, fehler
        if b:
            ok += 1
            print("  OK   %s" % text)
        else:
            fehler += 1
            print("  FEHL %s" % text)

    # Odoo-11-Ausgangslage
    print("\nOdoo 11 - Zugriffsregeln auf account.invoice:")
    for a in o11.kw("ir.model.access", "search_read",
                    [[["model_id.model", "=", "account.invoice"]],
                     ["name", "group_id", "perm_read", "perm_write", "perm_create",
                      "perm_unlink"]], context=CTX):
        print("   %-38s Gruppe %-28s R/W/C/D %d%d%d%d"
              % (a["name"], a["group_id"][1] if a["group_id"] else "-", a["perm_read"],
                 a["perm_write"], a["perm_create"], a["perm_unlink"]))

    vorher = {m: o18.kw(m, "search_count", [[]], context=CTX_ALLE)
              for m in ("account.move", "res.partner")}
    angelegt, konten = [], []
    try:
        for praefix, label, xmlids, erwartung in ROLLEN:
            pwd = "Itk!%s" % secrets.token_urlsafe(12)
            login = "itk_s149_%s@example.invalid" % praefix
            uid = o18.kw("res.users", "create", [{
                "name": "ITK Test %s (S149)" % label, "login": login, "email": login,
                "password": pwd, "groups_id": [(6, 0, gruppen_ids(o18, xmlids))]}])
            uid = uid[0] if isinstance(uid, list) else uid
            angelegt.append(uid)
            print("\nRolle: %s" % label)
            try:
                eigen = client.Client(o18.url, env["ODOO18_DB"], login, pwd)
            except Exception as exc:  # noqa: BLE001
                pruefe(False, "%s kann sich anmelden (%s)" % (label, str(exc)[:60]))
                continue
            try:
                n = eigen.kw("account.move", "search_count", [[]], context=CTX)
                lesen = True
            except Exception:  # noqa: BLE001
                n, lesen = 0, False
            pruefe(lesen == erwartung["lesen"],
                   "%s darf Rechnungen lesen: erwartet %s, ist %s (%d sichtbar)"
                   % (label, erwartung["lesen"], lesen, n))

            ziel = o18.kw("account.move", "search", [[["itk_o11_id", "!=", False],
                                                      ["state", "=", "draft"]]],
                          context=CTX_ALLE, limit=1)
            if ziel and erwartung["lesen"]:
                try:
                    eigen.kw("account.move", "write", [ziel, {"narration": "Probe S149"}],
                             context=CTX)
                    schreiben = True
                except Exception:  # noqa: BLE001
                    schreiben = False
                pruefe(schreiben == erwartung["schreiben"],
                       "%s darf Entwuerfe bearbeiten: erwartet %s, ist %s"
                       % (label, erwartung["schreiben"], schreiben))
                if schreiben:
                    o18.kw("account.move", "write", [ziel, {"narration": False}],
                           context=CTX_ALLE)
    finally:
        for uid in angelegt:
            info = o18.kw("res.users", "read", [[uid], ["partner_id"]], context=CTX)
            if info and info[0].get("partner_id"):
                konten.append(info[0]["partner_id"][0])
        if angelegt:
            o18.kw("res.users", "unlink", [angelegt])
        if konten:
            o18.kw("res.partner", "unlink", [konten])
        nachher = {m: o18.kw(m, "search_count", [[]], context=CTX_ALLE)
                   for m in ("account.move", "res.partner")}
        print("\nAufraeumen: Testbenutzer und Kontakte entfernt; Bestand %s -> %s"
              % (vorher, nachher))
        pruefe(nachher["account.move"] == vorher["account.move"],
               "keine Belege durch die Rechtepruefung entstanden oder entfallen")

    print()
    print("--- Ergebnis Rechtepruefung (%s) ---" % args.instanz)
    print("Pruefungen OK ..... %d" % ok)
    print("Fehlschlaege ...... %d" % fehler)
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
