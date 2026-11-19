# -*- coding: utf-8 -*-
"""Rechtepruefung Valorisierung (Session 148).

Legt temporaere Benutzer in den Odoo-11-Gruppen an ("ITK / User (read only)",
"ITK / Manager (edit)") und prueft Lesen/Schreiben/Anlegen/Loeschen. Danach
werden Benutzer und Kontakte wieder entfernt.

Erwartung (Odoo-11-Stand):
  ohne ITK-Gruppe : kein Zugriff
  ITK / User      : nur lesen
  ITK / Manager   : lesen, schreiben, anlegen, loeschen
  Administrator   : alles (Konto unveraendert)

Aufruf:
    python scripts/migration/valorisierung_rechte_pruefung.py --instanz lokal
    python scripts/migration/valorisierung_rechte_pruefung.py --instanz vm
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
MODELL = "itk_valorisierung.valorisierung"

ROLLEN = [
    ("ohne", "Interner Benutzer ohne ITK-Gruppe", ["base.group_user"],
     {"lesen": False, "schreiben": False, "anlegen": False, "loeschen": False}),
    ("user", "ITK / User (read only)",
     ["base.group_user", "itk_crm.itk_group_user"],
     {"lesen": True, "schreiben": False, "anlegen": False, "loeschen": False}),
    ("manager", "ITK / Manager (edit)",
     ["base.group_user", "itk_crm.itk_group_user", "itk_crm.itk_group_manager"],
     {"lesen": True, "schreiben": True, "anlegen": True, "loeschen": True}),
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
    print("=== Rechtepruefung Valorisierung (%s, %s) ===" % (args.instanz, url))
    ok = fehler = 0

    def pruefe(bedingung, text):
        nonlocal ok, fehler
        if bedingung:
            ok += 1
            print("  OK   %s" % text)
        else:
            fehler += 1
            print("  FEHL %s" % text)

    vorher = {m: o18.kw(m, "search_count", [[]], context=CTX_ALLE)
              for m in (MODELL, "res.partner")}
    print("Ausgangsstand: %s" % vorher)

    angelegt, konten, neue_saetze = [], [], []
    schreibziel = None
    try:
        for praefix, label, xmlids, erwartung in ROLLEN:
            pwd = "Itk!%s" % secrets.token_urlsafe(12)
            login = "itk_s148_%s@example.invalid" % praefix
            uid = o18.kw("res.users", "create", [{
                "name": "ITK Test %s (S148)" % label,
                "login": login, "email": login, "password": pwd,
                "groups_id": [(6, 0, gruppen_ids(o18, xmlids))]}])
            uid = uid[0] if isinstance(uid, list) else uid
            angelegt.append(uid)
            print("\nRolle: %s (%s)" % (label, login))
            try:
                eigen = client.Client(url, db, login, pwd)
            except Exception as exc:  # noqa: BLE001
                pruefe(False, "%s kann sich anmelden (%s)" % (label, str(exc)[:80]))
                continue

            try:
                n = eigen.kw(MODELL, "search_count", [[]], context=CTX)
                lesen = True
            except Exception:  # noqa: BLE001
                n, lesen = 0, False
            pruefe(lesen == erwartung["lesen"],
                   "%s darf lesen: erwartet %s, ist %s (%d sichtbar)"
                   % (label, erwartung["lesen"], lesen, n))

            # Schreiben nur auf einem eigenen Testdatensatz - niemals auf migrierten
            # Daten (sonst aendert sich dort write_date/write_uid).
            if not schreibziel:
                try:
                    r = o18.kw(MODELL, "create",
                               [[{"name": "RECHTETEST S148 Schreibziel"}]], context=CTX)
                    schreibziel = r[0] if isinstance(r, list) else r
                    neue_saetze.append(schreibziel)
                except Exception as exc:  # noqa: BLE001
                    pruefe(False, "Schreibziel konnte nicht angelegt werden (%s)"
                           % str(exc)[:80])
            if schreibziel:
                try:
                    eigen.kw(MODELL, "write", [[schreibziel], {"seq": 0}], context=CTX)
                    schreiben = True
                except Exception:  # noqa: BLE001
                    schreiben = False
                pruefe(schreiben == erwartung["schreiben"],
                       "%s darf schreiben: erwartet %s, ist %s"
                       % (label, erwartung["schreiben"], schreiben))

            neu_id = None
            try:
                r = eigen.kw(MODELL, "create", [[{"name": "RECHTETEST S148 %s" % label}]],
                             context=CTX)
                neu_id = r[0] if isinstance(r, list) else r
                anlegen = True
                neue_saetze.append(neu_id)
            except Exception:  # noqa: BLE001
                anlegen = False
            pruefe(anlegen == erwartung["anlegen"],
                   "%s darf anlegen: erwartet %s, ist %s"
                   % (label, erwartung["anlegen"], anlegen))

            if neu_id:
                try:
                    eigen.kw(MODELL, "unlink", [[neu_id]], context=CTX)
                    loeschen = True
                    neue_saetze.remove(neu_id)
                except Exception:  # noqa: BLE001
                    loeschen = False
                pruefe(loeschen == erwartung["loeschen"],
                       "%s darf loeschen: erwartet %s, ist %s"
                       % (label, erwartung["loeschen"], loeschen))
    finally:
        for uid in angelegt:
            info = o18.kw("res.users", "read", [[uid], ["partner_id"]], context=CTX)
            if info and info[0].get("partner_id"):
                konten.append(info[0]["partner_id"][0])
        if neue_saetze:
            o18.kw(MODELL, "unlink", [neue_saetze])
        if angelegt:
            o18.kw("res.users", "unlink", [angelegt])
        if konten:
            o18.kw("res.partner", "unlink", [konten])
        rest = o18.kw(MODELL, "search", [[("name", "like", "RECHTETEST S148")]],
                      context=CTX_ALLE)
        if rest:
            o18.kw(MODELL, "unlink", [rest])
        nachher = {m: o18.kw(m, "search_count", [[]], context=CTX_ALLE)
                   for m in (MODELL, "res.partner")}
        print("\nAufraeumen: Testbenutzer, Testsatz und Kontakte entfernt")
        print("Endstand: %s" % nachher)
        pruefe(nachher == vorher, "Keine Testdaten zurueckgeblieben")

    print()
    print("--- Ergebnis Rechtepruefung (%s) ---" % args.instanz)
    print("Pruefungen OK ..... %d" % ok)
    print("Fehlschlaege ...... %d" % fehler)
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
