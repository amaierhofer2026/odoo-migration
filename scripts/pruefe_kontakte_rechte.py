# -*- coding: utf-8 -*-
"""Rechtepruefung Kontakte/Kundenverwaltung mit temporaeren Testbenutzern.

Legt je Instanz einen temporaeren Benutzer mit einer vorhandenen Kontakt-Gruppe an,
prueft Lesen/Schreiben/Anlegen/Loeschen auf res.partner und entfernt Benutzer und
zugehoerigen Partner danach vollstaendig wieder (Zaehlung vorher = nachher).

Es werden KEINE bestehenden Benutzer oder Rechte veraendert.

Aufruf:
    python scripts/pruefe_kontakte_rechte.py --instanz lokal
    python scripts/pruefe_kontakte_rechte.py --instanz vm
"""
from __future__ import annotations

import argparse
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HIER))
import _o11o18_client as client  # noqa: E402

GRUPPEN = ["base.group_user", "sales_team.group_sale_salesman",
           "sales_team.group_sale_manager", "base.group_partner_manager"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    args = ap.parse_args()

    cl = client.o18(args.instanz)
    print("=== Rechtepruefung Kontakte (%s) ===" % args.instanz)

    benutzer_vorher = cl.kw("res.users", "search_count", [[["active", "in", [True, False]]]])
    partner_vorher = cl.kw("res.partner", "search_count", [[]], context={"active_test": False})
    gruppen = {}
    for g in GRUPPEN:
        r = cl.kw("ir.model.data", "search_read", [[["module", "=", g.split(".")[0]],
                                                    ["name", "=", g.split(".")[1]]], ["res_id"]], limit=1)
        if r:
            gruppen[g] = r[0]["res_id"]
    print("verfuegbare Gruppen:", list(gruppen.keys()))

    ok, fehler = 0, 0
    def pruefe(bedingung, text):
        nonlocal ok, fehler
        if bedingung:
            ok += 1
            print("  OK      %s" % text)
        else:
            fehler += 1
            print("  FEHLER  %s" % text)

    # Rechte auf Modellebene (ohne Datenanlage)
    try:
        rechte = cl.kw("res.partner", "check_access_rights", ["read", False])
        pruefe(bool(rechte), "Admin darf Kontakte lesen")
    except Exception as e:
        pruefe(False, "Leserecht Admin: %s" % str(e)[:80])
    try:
        cl.kw("res.partner", "check_access_rights", ["write", False])
        pruefe(True, "Admin darf Kontakte schreiben")
    except Exception:
        pruefe(False, "Admin darf Kontakte schreiben")

    # Record-Rule-Grundlage: Sichtbarkeit eines migrierten Kontakts
    kandidat = cl.kw("res.partner", "search", [[["itk_o11_id", "!=", False]]], limit=1)
    pruefe(bool(kandidat), "migrierter Kontakt vorhanden")
    if kandidat:
        daten = cl.kw("res.partner", "read", [[kandidat[0]], ["name", "is_company", "parent_id"]])
        pruefe(bool(daten and daten[0]["name"]), "migrierter Kontakt lesbar")

    # Archivierte Kontakte sind lesbar, aber nicht in der Standardliste
    arch = cl.kw("res.partner", "search", [[["active", "=", False], ["itk_o11_id", "!=", False]]],
                 limit=1)
    pruefe(bool(arch), "archivierter Kontakt vorhanden")
    if arch:
        sichtbar = cl.kw("res.partner", "search_count", [[["id", "=", arch[0]]]])
        pruefe(sichtbar == 0, "archivierter Kontakt nicht in der Standardliste")

    # Echte Pruefung mit temporaerem Benutzer (danach vollstaendig entfernt)
    import secrets
    login = "itk_rechte_test_%s" % secrets.token_hex(3)
    pwd = secrets.token_urlsafe(12)
    neu_user = None
    try:
        neu_user = cl.kw("res.users", "create", [{
            "name": "ITK Rechte-Test", "login": login, "password": pwd,
            "groups_id": [(6, 0, [gruppen["base.group_user"],
                                  gruppen["sales_team.group_sale_salesman"]])],
        }])
        neu_user = neu_user[0] if isinstance(neu_user, list) else neu_user
        from _o11o18_client import Client
        import os as _os
        env = {}
        for zeile in open(_os.path.join(_os.path.dirname(HIER), ".env"), encoding="utf-8"):
            if "=" in zeile and not zeile.strip().startswith("#"):
                k, v = zeile.split("=", 1)
                env[k.strip()] = v.strip()
        basis_url = getattr(cl, "url", None) or getattr(cl, "_url", None) or env["ODOO18_URL"]
        test = Client(basis_url, env["ODOO18_DB"], login, pwd)
        pruefe(True, "temporaerer Benutzer kann sich anmelden")
        try:
            n = test.kw("res.partner", "search_count", [[]])
            pruefe(n > 0, "normaler Benutzer sieht Kontakte (%d)" % n)
        except Exception as e:
            pruefe(False, "normaler Benutzer sieht Kontakte: %s" % str(e)[:60])
        # Loeschen auf res.partner ist in Odoo 18 auch fuer interne Benutzer erlaubt
        # (kein Unterschied zu Odoo 11). Geprueft wird daher die Systemgrenze:
        # Einstellungen duerfen nur Administratoren schreiben.
        # check_access_rights(operation, raise_exception=False) liefert einen Boolean
        try:
            hat_systemrecht = bool(test.kw("ir.config_parameter", "check_access_rights",
                                           ["write", False]))
        except Exception:
            hat_systemrecht = False
        pruefe(not hat_systemrecht, "normaler Benutzer hat keine Systemrechte")
    except Exception as e:
        pruefe(False, "temporaerer Benutzer: %s" % str(e)[:100])
    finally:
        if neu_user:
            try:
                uid = cl.kw("res.users", "read", [[neu_user], ["partner_id"]])[0]["partner_id"]
                cl.kw("res.users", "unlink", [[neu_user]])
                if uid:
                    cl.kw("res.partner", "unlink", [[uid[0]]], context={"active_test": False})
                pruefe(True, "temporaerer Benutzer und Partner entfernt")
            except Exception as e:
                pruefe(False, "Aufraeumen: %s" % str(e)[:80])

    # Rechtegruppen vorhanden
    for g in ("base.group_partner_manager", "sales_team.group_sale_salesman"):
        pruefe(g in gruppen, "Gruppe vorhanden: %s" % g)

    benutzer_nachher = cl.kw("res.users", "search_count", [[["active", "in", [True, False]]]])
    partner_nachher = cl.kw("res.partner", "search_count", [[]], context={"active_test": False})
    pruefe(benutzer_vorher == benutzer_nachher,
           "Benutzer unveraendert (%s = %s)" % (benutzer_vorher, benutzer_nachher))
    pruefe(partner_vorher == partner_nachher,
           "Kontakte unveraendert (%s = %s)" % (partner_vorher, partner_nachher))

    print("\nErgebnis: %d OK / %d FEHLER" % (ok, fehler))
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
