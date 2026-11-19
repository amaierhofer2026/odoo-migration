# -*- coding: utf-8 -*-
"""Rechtepruefung Umfragen / Survey mit drei Rollen (Session 146).

Legt drei temporaere Benutzer an (ohne Umfragegruppe, "Umfragen / Benutzer",
"Umfragen / Administrator"), meldet sich ALS JEWEILS DIESER BENUTZER an und
prueft Lesen/Anlegen/Bearbeiten/Loeschen sowie die Sichtbarkeit fremder
Teilnahmen. Danach werden Benutzer und automatisch angelegte Kontakte entfernt.

Erwartungen (Odoo-18-Standard, keine Rechteausweitung durch die Migration):

  ohne Gruppe      : kein Zugriff auf Umfragen oder Teilnahmen (AccessError)
  Umfragen/Benutzer: lesen, anlegen, bearbeiten, loeschen von Umfragen UND
                     Teilnahmen; sieht ALLE Teilnahmen (Dokumentierte Abweichung
                     zu Odoo 11, dort nur eigene - siehe
                     docs/o11-o18-vergleich-survey.md, Abschnitt 5.2)
  Umfragen/Admin   : wie Benutzer, zusaetzlich alles ohne Einschraenkung

Aufruf:
    python scripts/migration/survey_rechte_pruefung.py --instanz lokal
    python scripts/migration/survey_rechte_pruefung.py --instanz vm
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

# (Login-Praefix, Anzeige, Gruppen-XML-IDs, Erwartung)
ROLLEN = [
    ("ohne", "Interner Benutzer ohne Umfragegruppe", ["base.group_user"],
     {"lesen": False, "anlegen": False, "fremde": False, "loeschen": False}),
    ("user", "Umfragen / Benutzer", ["base.group_user", "survey.group_survey_user"],
     {"lesen": True, "anlegen": True, "fremde": True, "loeschen": True}),
    ("admin", "Umfragen / Administrator",
     ["base.group_user", "survey.group_survey_manager", "survey.group_survey_user"],
     {"lesen": True, "anlegen": True, "fremde": True, "loeschen": True}),
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
    print("=== Rechtepruefung Umfragen (%s, %s) ===" % (args.instanz, url))
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
              for m in ("survey.survey", "survey.user_input", "res.partner")}
    print("Ausgangsstand: %s" % vorher)
    fremde_inputs = o18.kw("survey.user_input", "search_count",
                           [[("create_uid", "not in", [1])]], context=CTX_ALLE)

    angelegt, konten = [], []
    neu_umfrage = None
    try:
        for praefix, label, xmlids, erwartung in ROLLEN:
            pwd = "Itk!%s" % secrets.token_urlsafe(12)
            login = "itk_s146_%s@example.invalid" % praefix
            uid = o18.kw("res.users", "create", [{
                "name": "ITK Test %s (S146)" % label,
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

            # Lesen
            try:
                n = eigen.kw("survey.survey", "search_count", [[]], context=CTX)
                lesen = True
            except Exception:  # noqa: BLE001
                n, lesen = 0, False
            pruefe(lesen == erwartung["lesen"],
                   "%s Umfragen lesen: erwartet %s, ist %s (%d sichtbar)"
                   % (label, erwartung["lesen"], lesen, n))

            # Teilnahmen lesen und fremde Antworten
            try:
                n_in = eigen.kw("survey.user_input", "search_count", [[]], context=CTX)
                sichtbar = eigen.kw("survey.user_input", "search_count",
                                    [[("itk_o11_id", "!=", False)]], context=CTX)
                sieht_fremd = sichtbar > 0
            except Exception:  # noqa: BLE001
                n_in, sieht_fremd, sichtbar = 0, False, 0
            pruefe(sieht_fremd == erwartung["fremde"],
                   "%s sieht fremde Teilnahmen: erwartet %s, ist %s "
                   "(%d migrierte Teilnahmen sichtbar, %d insgesamt)"
                   % (label, erwartung["fremde"], sieht_fremd, sichtbar, n_in))

            # Anlegen
            neu_id, anlegen_ok = None, False
            try:
                r = eigen.kw("survey.survey", "create", [[{
                    "title": "RECHTETEST S146 %s" % label, "survey_type": "survey"}]],
                    context=CTX)
                neu_id = r[0] if isinstance(r, list) else r
                anlegen_ok = True
            except Exception:  # noqa: BLE001
                pass
            pruefe(anlegen_ok == erwartung["anlegen"],
                   "%s Umfrage anlegen: erwartet %s, ist %s"
                   % (label, erwartung["anlegen"], anlegen_ok))

            if neu_id:
                if not neu_umfrage:
                    neu_umfrage = neu_id
                try:
                    eigen.kw("survey.survey", "write", [[neu_id], {"title": "RECHTETEST S146 x"}],
                             context=CTX)
                    pruefe(True, "%s darf Umfrage bearbeiten" % label)
                except Exception:  # noqa: BLE001
                    pruefe(False, "%s darf Umfrage bearbeiten" % label)
                geloescht = False
                try:
                    eigen.kw("survey.survey", "unlink", [[neu_id]], context=CTX)
                    geloescht = True
                    neu_umfrage = None
                except Exception:  # noqa: BLE001
                    pass
                pruefe(geloescht == erwartung["loeschen"],
                       "%s Umfrage loeschen: erwartet %s, ist %s"
                       % (label, erwartung["loeschen"], geloescht))

            # Konfiguration (Stufen gibt es in Odoo 18 nicht; Vorgaben schon)
            try:
                ids = eigen.kw("survey.question", "search", [[]], context=CTX, limit=1)
                if ids:
                    eigen.kw("survey.question", "write", [ids, {"sequence": 1}], context=CTX)
                    pruefe(True, "%s darf Fragen bearbeiten" % label)
                else:
                    pruefe(erwartung["lesen"], "%s Fragenzugriff: erwartet wie Lesen" % label)
            except Exception:  # noqa: BLE001
                pruefe(not erwartung["lesen"], "%s darf Fragen nicht bearbeiten" % label)
    finally:
        for uid in angelegt:
            info = o18.kw("res.users", "read", [[uid], ["partner_id"]], context=CTX)
            if info and info[0].get("partner_id"):
                konten.append(info[0]["partner_id"][0])
        if angelegt:
            o18.kw("res.users", "unlink", [angelegt])
        if konten:
            o18.kw("res.partner", "unlink", [konten])
        rest = o18.kw("survey.survey", "search",
                      [[("title", "like", "RECHTETEST S146")]], context=CTX_ALLE)
        if rest:
            o18.kw("survey.survey", "unlink", [rest])
        nachher = {m: o18.kw(m, "search_count", [[]], context=CTX_ALLE)
                   for m in ("survey.survey", "survey.user_input", "res.partner")}
        print("\nAufraeumen: Testbenutzer und Kontakte entfernt")
        print("Endstand: %s" % nachher)
        pruefe(nachher == vorher, "Keine Testdaten zurueckgeblieben")

    print()
    print("--- Ergebnis Rechtepruefung (%s) ---" % args.instanz)
    print("Pruefungen OK ..... %d" % ok)
    print("Fehlschlaege ...... %d" % fehler)
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
