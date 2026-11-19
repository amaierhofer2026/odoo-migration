# -*- coding: utf-8 -*-
"""Rechtepruefung Umfragen / Survey (Session 147, nach der Rechteanpassung).

Prueft das Odoo-11-Prinzip: normale Umfrage-Benutzer sehen nur ihre eigenen
Teilnahmen und Antworten, Manager und Administratoren sehen alles.

Ablauf je Rolle: temporaeren Benutzer anlegen, als dieser anmelden, eigene
Teilnahme erzeugen, eigene sehen, fremde nicht sehen, direkter Zugriff auf eine
fremde Teilnahme (wie eine URL auf den Datensatz), Schreibversuch auf fremde
Daten, fremde Antwortzeile, Gesamtzahl. Danach alle Testdaten entfernen.

Erwartungen (nach der Rechteanpassung, Modul itk_survey_security):

  ohne Gruppe      : kein Zugriff auf Umfragen oder Teilnahmen (AccessError)
  Umfragen/Benutzer: Umfragen lesen/verwalten wie bisher, Teilnahmen und Antworten
                     NUR die eigenen (create_uid = user bzw. partner_id-Prinzip)
  Umfragen/Admin   : sieht alle Teilnahmen und Antworten (Manager-Regel, ODER)

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
     {"lesen": False, "eigene": False, "fremde": False, "anlegen": False, "verwalten": False}),
    ("user", "Umfragen / Benutzer", ["base.group_user", "survey.group_survey_user"],
     {"lesen": True, "eigene": True, "fremde": False, "anlegen": True, "verwalten": True}),
    ("admin", "Umfragen / Administrator",
     ["base.group_user", "survey.group_survey_manager", "survey.group_survey_user"],
     {"lesen": True, "eigene": True, "fremde": True, "anlegen": True, "verwalten": True}),
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

    # Fremde Teilnahme = migrierte Teilnahme (gehoert dem Administrator)
    fremd = o18.kw("survey.user_input", "search", [[("itk_o11_id", "!=", False)]],
                   context=CTX_ALLE, limit=1)
    fremd_id = fremd[0] if fremd else None
    fremde_zeile = None
    if fremd_id:
        z = o18.kw("survey.user_input.line", "search", [[("user_input_id", "=", fremd_id)]],
                   context=CTX_ALLE, limit=1)
        fremde_zeile = z[0] if z else None
    print("Fremde Teilnahme (Administrator): %s, Antwortzeile: %s" % (fremd_id, fremde_zeile))

    angelegt, konten, eigene_inputs = [], [], []
    try:
        for praefix, label, xmlids, erwartung in ROLLEN:
            pwd = "Itk!%s" % secrets.token_urlsafe(12)
            login = "itk_s147_%s@example.invalid" % praefix
            uid = o18.kw("res.users", "create", [{
                "name": "ITK Test %s (S147)" % label,
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
            eigen_ctx = {"lang": "de_DE"}

            # 1 Umfragen lesen
            try:
                n = eigen.kw("survey.survey", "search_count", [[]], context=eigen_ctx)
                lesen = True
            except Exception:  # noqa: BLE001
                n, lesen = 0, False
            pruefe(lesen == erwartung["lesen"],
                   "%s Umfragen lesen: erwartet %s, ist %s (%d sichtbar)"
                   % (label, erwartung["lesen"], lesen, n))

            # 2 Eigene Teilnahme anlegen und sehen
            eigene_id = None
            anlegen_ok = False
            try:
                r = eigen.kw("survey.user_input", "create",
                             [{"survey_id": 1, "state": "new"}], context=eigen_ctx)
                eigene_id = r[0] if isinstance(r, list) else r
                anlegen_ok = True
                eigene_inputs.append(eigene_id)
            except Exception:  # noqa: BLE001
                pass
            pruefe(anlegen_ok == erwartung["anlegen"],
                   "%s eigene Teilnahme anlegen: erwartet %s, ist %s"
                   % (label, erwartung["anlegen"], anlegen_ok))
            if eigene_id:
                try:
                    eigene_sichtbar = eigen.kw("survey.user_input", "search_count",
                                               [[("id", "=", eigene_id)]],
                                               context=eigen_ctx) == 1
                except Exception:  # noqa: BLE001
                    eigene_sichtbar = False
                pruefe(eigene_sichtbar == erwartung["eigene"],
                       "%s sieht die eigene Teilnahme: erwartet %s, ist %s"
                       % (label, erwartung["eigene"], eigene_sichtbar))

            if fremd_id:
                # 3 Fremde Teilnahme in der Suche
                try:
                    n_fremd = eigen.kw("survey.user_input", "search_count",
                                       [[("id", "=", fremd_id)]], context=eigen_ctx)
                except Exception:  # noqa: BLE001
                    n_fremd = 0
                pruefe((n_fremd == 1) == erwartung["fremde"],
                       "%s sieht fremde Teilnahme in der Suche: erwartet %s, ist %s"
                       % (label, erwartung["fremde"], n_fremd == 1))

                # 4 Direkter Zugriff (wie eine URL auf den fremden Datensatz)
                try:
                    zugriff = bool(eigen.kw("survey.user_input", "read",
                                            [[fremd_id], ["id"]], context=eigen_ctx))
                except Exception:  # noqa: BLE001
                    zugriff = False
                pruefe(zugriff == erwartung["fremde"],
                       "%s direkter Zugriff auf fremde Teilnahme: erwartet %s, ist %s"
                       % (label, erwartung["fremde"], zugriff))

                # 5 Schreiben auf fremde Daten
                try:
                    schreiben = bool(eigen.kw("survey.user_input", "write",
                                              [[fremd_id], {"deadline": False}],
                                              context=eigen_ctx))
                except Exception:  # noqa: BLE001
                    schreiben = False
                pruefe(schreiben == erwartung["fremde"],
                       "%s darf fremde Teilnahme bearbeiten: erwartet %s, ist %s"
                       % (label, erwartung["fremde"], schreiben))

            # 6 Fremde Antwortzeile
            if fremde_zeile:
                try:
                    z_ok = bool(eigen.kw("survey.user_input.line", "read",
                                         [[fremde_zeile], ["id"]], context=eigen_ctx))
                except Exception:  # noqa: BLE001
                    z_ok = False
                pruefe(z_ok == erwartung["fremde"],
                       "%s sieht fremde Antwortzeile: erwartet %s, ist %s"
                       % (label, erwartung["fremde"], z_ok))

            # 7 Gesamtzahl sichtbarer Teilnahmen
            try:
                gesamt = eigen.kw("survey.user_input", "search_count", [[]],
                                  context=eigen_ctx)
            except Exception:  # noqa: BLE001
                gesamt = -1
            if erwartung["fremde"]:
                pruefe(gesamt >= vorher["survey.user_input"],
                       "%s sieht alle Teilnahmen (%d, davon %d migriert)"
                       % (label, gesamt, vorher["survey.user_input"]))
            else:
                pruefe(gesamt <= 1, "%s sieht hoechstens die eigene Teilnahme (%d)"
                       % (label, gesamt))

            # 8 Umfragen verwalten (Anlegen/Bearbeiten/Loeschen) - unveraendert
            neu_id, verwalten_ok = None, False
            try:
                r = eigen.kw("survey.survey", "create", [[{
                    "title": "RECHTETEST S147 %s" % label, "survey_type": "survey"}]],
                    context=eigen_ctx)
                neu_id = r[0] if isinstance(r, list) else r
                verwalten_ok = True
            except Exception:  # noqa: BLE001
                verwalten_ok = False
            pruefe(verwalten_ok == erwartung["verwalten"],
                   "%s Umfrage anlegen: erwartet %s, ist %s"
                   % (label, erwartung["verwalten"], verwalten_ok))
            if neu_id:
                try:
                    eigen.kw("survey.survey", "write",
                             [[neu_id], {"title": "RECHTETEST S147 x"}], context=eigen_ctx)
                    pruefe(True, "%s darf Umfrage bearbeiten" % label)
                except Exception:  # noqa: BLE001
                    pruefe(False, "%s darf Umfrage bearbeiten" % label)
                try:
                    eigen.kw("survey.survey", "unlink", [[neu_id]], context=eigen_ctx)
                    pruefe(True, "%s darf Umfrage loeschen" % label)
                except Exception:  # noqa: BLE001
                    pruefe(False, "%s darf Umfrage loeschen" % label)
    finally:
        for uid in angelegt:
            info = o18.kw("res.users", "read", [[uid], ["partner_id"]], context=CTX)
            if info and info[0].get("partner_id"):
                konten.append(info[0]["partner_id"][0])
        if eigene_inputs:
            o18.kw("survey.user_input", "unlink", [eigene_inputs])
        if angelegt:
            o18.kw("res.users", "unlink", [angelegt])
        if konten:
            o18.kw("res.partner", "unlink", [konten])
        rest = o18.kw("survey.survey", "search",
                      [[("title", "like", "RECHTETEST S147")]], context=CTX_ALLE)
        if rest:
            o18.kw("survey.survey", "unlink", [rest])
        nachher = {m: o18.kw(m, "search_count", [[]], context=CTX_ALLE)
                   for m in ("survey.survey", "survey.user_input", "res.partner")}
        print("\nAufraeumen: Testbenutzer, Testteilnahmen und Kontakte entfernt")
        print("Endstand: %s" % nachher)
        pruefe(nachher == vorher, "Keine Testdaten zurueckgeblieben")

    print()
    print("--- Ergebnis Rechtepruefung (%s) ---" % args.instanz)
    print("Pruefungen OK ..... %d" % ok)
    print("Fehlschlaege ...... %d" % fehler)
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
