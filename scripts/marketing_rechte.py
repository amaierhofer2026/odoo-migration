"""Rechte im Bereich E-Mail-Marketing pruefen (Testbenutzer, read-only fuer Daten).

Prueft mit zwei temporaeren Benutzern der Gruppe "E-Mail-Marketing / Benutzer",
dass Mailings, Kampagnen und Kampagnenstufen gelesen, angelegt und bearbeitet
werden koennen; die Testdatensaetze werden anschliessend entfernt.

Aufruf:
    python scripts/marketing_rechte.py --instanz lokal
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import Client, lade_env, o18  # noqa: E402

DE = {"lang": "de_DE"}


def xmlid_id(k, xmlid):
    modul, name = xmlid.split(".")
    d = k.kw("ir.model.data", "search_read", [[("module", "=", modul), ("name", "=", name)], ["res_id"]])
    return d[0]["res_id"] if d else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    a = ap.parse_args()
    k = o18(a.instanz)
    env = lade_env()

    g_intern = xmlid_id(k, "base.group_user")
    g_mail = xmlid_id(k, "mass_mailing.group_mass_mailing_user")
    print("Gruppen: intern=%s, E-Mail-Marketing/Benutzer=%s" % (g_intern, g_mail))

    bestand = {m: k.kw(m, "search_count", [[]], context={"active_test": False})
               for m in ("mailing.mailing", "itk.mailing.campaign", "itk.mailing.campaign.stage",
                         "res.partner")}
    print("Bestand vorher:", bestand)

    login = "hermes.marketing@itk.local"
    pwd = "Hermes-Marketing-2026!"
    for u in k.kw("res.users", "search_read", [[("login", "=", login)], ["id"]], context={"active_test": False}):
        k.kw("res.users", "write", [[u["id"]], {"active": False}])
    uid = k.kw("res.users", "create", [{
        "name": "Hermes Marketing Test", "login": login, "password": pwd,
        "groups_id": [(6, 0, [g_intern, g_mail])],
    }], context={"no_reset_password": True, "tracking_disable": True})
    uid = uid[0]["id"] if isinstance(uid, list) else uid
    quelle = k.kw("utm.source", "search_read", [[("name", "=", "Odoo 11")], ["id"]])
    quelle = quelle[0]["id"] if quelle else k.kw("utm.source", "create", [{"name": "Odoo 11"}])
    if isinstance(quelle, list):
        quelle = quelle[0]["id"]

    try:
        url = env.get("ODOO18_URL", "http://localhost:8069") if a.instanz == "lokal" else "https://k001959vsx.ipax.local"
        c = Client(url, env["ODOO18_DB"], login, pwd)
        print("\n=== Rechteprobe als Benutzer der Gruppe E-Mail-Marketing ===")
        print("  Mailings lesen:", c.kw("mailing.mailing", "search_count", [[]]))
        print("  Kampagnen lesen:", c.kw("itk.mailing.campaign", "search_count", [[]]),
              "| Stufen lesen:", c.kw("itk.mailing.campaign.stage", "search_count", [[]]))
        stufe = c.kw("itk.mailing.campaign.stage", "create", [{"name": "Hermes Probe Stufe", "sequence": 99}])
        sid = stufe[0]["id"] if isinstance(stufe, list) else stufe
        kamp = c.kw("itk.mailing.campaign", "create", [{"name": "Hermes Probe Kampagne", "stage_id": sid}])
        kid = kamp[0]["id"] if isinstance(kamp, list) else kamp
        modell = k.kw("ir.model", "search_read", [[("model", "=", "res.partner")], ["id"]])[0]["id"]
        mail = c.kw("mailing.mailing", "create", [{
            "subject": "Hermes Probe Mailing", "body_html": "<p>Probe</p>",
            "email_from": "noreply@it-kommunal.at", "mailing_model_id": modell,
            "mailing_domain": "[]", "mailing_type": "mail", "schedule_type": "now",
            "source_id": quelle, "state": "draft", "itk_campaign_id": kid,
        }])
        mid = mail[0]["id"] if isinstance(mail, list) else mail
        c.kw("mailing.mailing", "write", [[mid], {"subject": "Hermes Probe Mailing 2"}])
        c.kw("itk.mailing.campaign", "write", [[kid], {"name": "Hermes Probe Kampagne 2"}])
        print("  anlegen und bearbeiten: ja (Mailing %s, Kampagne %s, Stufe %s)" % (mid, kid, sid))
        try:
            c.kw("mailing.mailing", "unlink", [[mid]])
            print("  loeschen: ja (Odoo-18-Recht, bleibt so)")
        except Exception as exc:  # noqa: BLE001
            print("  loeschen: nein (%s)" % str(exc)[:80])
    finally:
        # Aufraeumen als Administrator
        for modell, dom in (("mailing.mailing", [("subject", "like", "Hermes Probe")]),
                            ("itk.mailing.campaign", [("name", "like", "Hermes Probe")]),
                            ("itk.mailing.campaign.stage", [("name", "like", "Hermes Probe")])):
            ids = k.kw(modell, "search", [dom], context={"active_test": False})
            if ids:
                k.kw(modell, "unlink", [ids])
        k.kw("res.users", "write", [[uid], {"active": False}], context={"tracking_disable": True})
        k.kw("res.users", "unlink", [[uid]])
        verwaist = k.kw("res.partner", "search", [[("name", "=", "Hermes Marketing Test"),
                                                  ("user_ids", "=", False)]],
                        context={"active_test": False})
        if verwaist:
            k.kw("res.partner", "unlink", [verwaist])
        nachher = {m: k.kw(m, "search_count", [[]], context={"active_test": False})
                   for m in bestand}
        print("\nBestand nachher:", nachher)
        print("Testdaten entfernt:", bestand == nachher)
        print("Benutzer entfernt:", k.kw("res.users", "search_count",
                                         [[("login", "=", login)]], context={"active_test": False}) == 0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
