"""Rechtepruefung Website (E10) mit temporaeren Testbenutzern - lokal und VM.

    python scripts/pruefe_website_rechte.py --instanz lokal
    python scripts/pruefe_website_rechte.py --instanz vm

Legt zwei temporaere Benutzer an (Website-Redakteur, interner Benutzer ohne
Website-Recht), prueft Schreib-/Leserechte auf website.page und website.menu,
prueft die Sichtbarkeit unveroeffentlichter Seiten fuer oeffentliche Nutzer und
entfernt die Testbenutzer danach wieder vollstaendig.

Es werden KEINE bestehenden Benutzer oder Rechte geaendert.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _o11o18_client as client  # noqa: E402

LOGIN_RED = "zz_test_red_s142"
LOGIN_LES = "zz_test_les_s142"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    ap.add_argument("--behalten", action="store_true", help="Testbenutzer nicht entfernen (Debug)")
    args = ap.parse_args()

    admin = client.o18(args.instanz)
    env = client.lade_env()
    pwd = env["ODOO18_PWD"]

    gruppen = admin.kw("res.groups", "search_read",
                       [[["category_id.name", "ilike", "Website"]], ["id", "full_name"]],
                       context={"lang": "de_DE"})
    g_red = next((g["id"] for g in gruppen if "Redakteur" in g["full_name"]), None)
    g_basis = admin.kw("res.groups", "search_read",
                       [[["full_name", "ilike", "Interner Benutzer"]], ["id"]])
    ids_basis = [g["id"] for g in g_basis]
    if not g_red:
        print("FEHLER: Gruppe 'Redakteur und Designer' nicht gefunden")
        return 1

    vorher_users = admin.kw("res.users", "search_count", [[]])
    vorher_pages = admin.kw("website.page", "search_count", [[]])
    vorher_menus = admin.kw("website.menu", "search_count", [[]])
    print("Ausgangslage %s: %d Benutzer, %d Seiten, %d Menues"
          % (args.instanz, vorher_users, vorher_pages, vorher_menus))

    # Aufraeumen, falls ein Lauf abgebrochen ist
    alt = admin.kw("res.users", "search", [[["login", "in", [LOGIN_RED, LOGIN_LES]]]])
    if alt:
        admin.kw("res.users", "unlink", [alt])

    u_red = admin.kw("res.users", "create", [[{
        "name": "ZZ Test Redakteur", "login": LOGIN_RED, "password": pwd,
        "groups_id": [(6, 0, ids_basis + [g_red])]}]])
    u_les = admin.kw("res.users", "create", [[{
        "name": "ZZ Test Leser", "login": LOGIN_LES, "password": pwd,
        "groups_id": [(6, 0, ids_basis)]}]])
    u_red = u_red[0] if isinstance(u_red, list) else u_red
    u_les = u_les[0] if isinstance(u_les, list) else u_les
    print("Testbenutzer angelegt: Redakteur %s, Leser %s" % (u_red, u_les))

    ergebnisse = []

    def pruefe(name, soll, ist):
        ergebnisse.append((soll == ist, name, soll, ist))

    try:
        # 1) Admin-Sicht: Schreibrecht des Redakteurs auf website.page (ACL-basiert)
        red = client.Client(env.get("ODOO18_URL", "http://localhost:8069")
                            if args.instanz == "lokal" else "https://k001959vsx.ipax.at",
                            env["ODOO18_DB"], LOGIN_RED, pwd)
        les = client.Client(env.get("ODOO18_URL", "http://localhost:8069")
                            if args.instanz == "lokal" else "https://k001959vsx.ipax.at",
                            env["ODOO18_DB"], LOGIN_LES, pwd)
        pruefe("Redakteur darf Seiten schreiben (ACL)",
               True, bool(red.kw("website.page", "check_access_rights", ["write", False])))
        pruefe("Leser darf Seiten NICHT schreiben (ACL)",
               False, bool(les.kw("website.page", "check_access_rights", ["write", False])))
        pruefe("Redakteur darf Menues schreiben (ACL)",
               True, bool(red.kw("website.menu", "check_access_rights", ["write", False])))
        g_red_ids = admin.kw("res.users", "read", [[u_red], ["groups_id"]])[0]["groups_id"] or []
        g_les_ids = admin.kw("res.users", "read", [[u_les], ["groups_id"]])[0]["groups_id"] or []
        pruefe("Redakteur ist in Website-Redakteur-Gruppe", True, g_red in g_red_ids)
        pruefe("Leser ist NICHT in Website-Redakteur-Gruppe", False, g_red in g_les_ids)

        # 2) Record Rule: unveroeffentlichte Seite ist fuer Nicht-Designer unsichtbar
        unpub = admin.kw("website.page", "search", [[["is_published", "=", False]]], limit=1)
        if unpub:
            pruefe("Redakteur sieht unveroeffentlichte Seite (Designer-Regel)",
                   True, bool(red.kw("website.page", "search", [[["id", "in", unpub]]])))
            # Ein interner Benutzer ohne Website-Recht bekommt auf website.page
            # einen AccessError - das ist das erwartete Ergebnis (kein Zugriff).
            try:
                les_sieht = bool(les.kw("website.page", "search", [[["id", "in", unpub]]]))
                les_darf_ueberhaupt = True
            except RuntimeError as err:
                les_sieht = False
                les_darf_ueberhaupt = "AccessError" not in str(err)
                print("  HINWEIS: Leser ohne Website-Recht erhaelt AccessError auf website.page "
                      "(erwartet) - Meldung: %s" % ("AccessError" if not les_darf_ueberhaupt else err))
            pruefe("Leser sieht unveroeffentlichte Seite NICHT", False, les_sieht)

        # 3) Menuepunkt-Sichtbarkeit haengt an der Veroeffentlichung der Zielseite
        # is_visible ist fuer interne Benutzer immer True - die Besuchersicht wird
        # ueber die oeffentliche Seite geprueft (ohne Session).
        import urllib.request
        basis = ("http://localhost:8069" if args.instanz == "lokal"
                 else "https://k001959vsx.ipax.at")
        html = urllib.request.urlopen(
            urllib.request.Request(basis + "/", headers={"User-Agent": "ITK-Abnahme"}), timeout=60
        ).read().decode("utf-8", "replace")
        for name in ("FAQ Umstellung Ebox - Gemeindecloud", "FAQS IFG-Portal (Kunden)"):
            pruefe("Menue '%s' fuer Besucher unsichtbar (Zielseite unveroeffentlicht)" % name,
                   False, name in html)
        for name in ("ITK Portal", "Kurse", "Webinare"):
            pruefe("Menue '%s' fuer Besucher sichtbar" % name, True, name in html)

        # 4) Schreibversuch des Redakteurs auf einer Website-Einstellung (nicht erlaubt)
        # Odoo-18-Standard-ACL: der Website-Designer darf die Website-Einstellungen
        # schreiben, ein interner Benutzer ohne Website-Recht nicht. Es wurden keine
        # Rechte geaendert (E10) - hier wird nur der Standard belegt.
        try:
            red.kw("website", "write", [[1], {"name": admin.kw("website", "read", [[1], ["name"]])[0]["name"]}])
            pruefe("Redakteur darf Website-Einstellungen schreiben (Odoo-18-Standard-ACL)", True, True)
        except RuntimeError:
            pruefe("Redakteur darf Website-Einstellungen schreiben (Odoo-18-Standard-ACL)", True, False)
        try:
            les.kw("website", "write", [[1], {"name": admin.kw("website", "read", [[1], ["name"]])[0]["name"]}])
            pruefe("Leser darf Website-Einstellungen NICHT schreiben", False, True)
        except RuntimeError:
            pruefe("Leser darf Website-Einstellungen NICHT schreiben", False, False)
    finally:
        if not args.behalten:
            # Benutzer UND die dabei automatisch erzeugten Partner entfernen,
            # damit keine Test-Kontakte zurueckbleiben (Regression Kontakte!).
            partner = admin.kw("res.partner", "search",
                               [[["name", "in", ["ZZ Test Redakteur", "ZZ Test Leser"]]]])
            admin.kw("res.users", "unlink", [[u_red, u_les]])
            if partner:
                admin.kw("res.partner", "unlink", [partner])
            nachher_users = admin.kw("res.users", "search_count", [[]])
            nachher_pages = admin.kw("website.page", "search_count", [[]])
            nachher_menus = admin.kw("website.menu", "search_count", [[]])
            pruefe("Testbenutzer vollstaendig entfernt", True, nachher_users == vorher_users)
            pruefe("Seitenbestand unveraendert", True, nachher_pages == vorher_pages)
            pruefe("Menuebestand unveraendert", True, nachher_menus == vorher_menus)
            print("Nachher: %d Benutzer, %d Seiten, %d Menues"
                  % (nachher_users, nachher_pages, nachher_menus))

    fehler = [e for e in ergebnisse if not e[0]]
    for ok, name, soll, ist in ergebnisse:
        print("  %s %-62s soll=%s ist=%s" % ("OK  " if ok else "FEHL", name, soll, ist))
    print("\nErgebnis %s: %d OK / %d FEHLER" % (args.instanz, len(ergebnisse) - len(fehler), len(fehler)))
    return 0 if not fehler else 1


if __name__ == "__main__":
    raise SystemExit(main())
