"""Rechte im Bereich Events: Odoo-11-Gruppen abbilden und pruefen.

Odoo 11:
  Gruppe 87 "Events / Benutzer" (41 aktive Benutzer) - Veranstaltungen lesen,
      Teilnehmer bearbeiten
  Gruppe 88 "Events / Manager" (28 aktive Benutzer) - alles bearbeiten

Odoo 18:
  event.group_event_user              - Veranstaltungen lesen
  event.group_event_registration_desk - Menue "Events" sichtbar
  event.group_event_manager           - Veranstaltungen bearbeiten

Die Zuordnung erfolgt ueber den Login; Benutzer, die es in Odoo 18 nicht
gibt, werden nur berichtet (es werden keine Benutzer angelegt).

Aufruf:
    python scripts/events_rechte.py --instanz lokal                 # nur Bericht
    python scripts/events_rechte.py --instanz lokal --setzen        # Gruppen setzen
    python scripts/events_rechte.py --instanz lokal --pruefen       # Testbenutzer
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18, Client, lade_env  # noqa: E402

DE = {"lang": "de_DE"}
GRUPPEN = {
    87: ["event.group_event_user", "event.group_event_registration_desk"],
    88: ["event.group_event_manager"],
}


def xmlid_id(k, xmlid):
    modul, name = xmlid.split(".")
    d = k.kw("ir.model.data", "search_read", [[("module", "=", modul), ("name", "=", name)], ["res_id"]])
    return d[0]["res_id"] if d else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    ap.add_argument("--setzen", action="store_true")
    ap.add_argument("--pruefen", action="store_true")
    a = ap.parse_args()
    k11 = o11()
    k = o18(a.instanz)

    print("=== Odoo-11-Gruppen und Odoo-18-Zuordnung (%s) ===" % a.instanz)
    benutzer18 = {u["login"].lower(): u["id"] for u in
                  k.kw("res.users", "search_read", [[], ["id", "login", "active"]],
                       context={"active_test": False})}
    gesetzt, fehlend = 0, []
    for gid, ziel_gruppen in GRUPPEN.items():
        logins11 = k11.kw("res.users", "search_read", [[("groups_id", "in", [gid])], ["login", "name", "active"]],
                          context={"lang": "de_DE", "active_test": False})
        ziel_ids = [xmlid_id(k, x) for x in ziel_gruppen]
        if any(z is None for z in ziel_ids):
            print("  Gruppe %s: Odoo-18-Gruppe fehlt (%s)" % (gid, ziel_gruppen))
            continue
        treffer = [(u["login"], benutzer18.get((u["login"] or "").lower())) for u in logins11]
        da = [t for t in treffer if t[1]]
        nicht = [t[0] for t in treffer if not t[1]]
        print("  Odoo-11-Gruppe %s -> %s" % (gid, ziel_gruppen))
        print("     Odoo-11-Benutzer: %d, in Odoo 18 vorhanden: %d, nicht zuordenbar: %d"
              % (len(treffer), len(da), len(nicht)))
        if nicht:
            print("     nicht zuordenbar:", ", ".join(nicht[:12]))
            fehlend.extend(nicht)
        if a.setzen and da:
            for ziel in ziel_ids:
                k.kw("res.groups", "write", [[ziel], {"users": [(4, t[1]) for t in da]}], context=DE)
            gesetzt += 1
        # Kontrolle: Anzahl Benutzer in der Odoo-18-Gruppe
        for ziel in ziel_ids:
            n = k.kw("res.users", "search_count", [[("groups_id", "in", [ziel])]])
            print("     Odoo 18 %-40s Benutzer: %d" % (ziel, n))

    if a.setzen:
        print("\n  Gruppen geschrieben: %d" % gesetzt)

    if a.pruefen:
        env = lade_env()
        print("\n=== Rechteprobe mit temporaeren Benutzern ===")
        g_user = [xmlid_id(k, "base.group_user"), xmlid_id(k, "event.group_event_user"),
                  xmlid_id(k, "event.group_event_registration_desk")]
        g_mgr = g_user + [xmlid_id(k, "event.group_event_manager")]
        pwd = "Hermes-Events-2026!"
        ids = []
        for name, gruppen in (("Hermes Events Benutzer", g_user), ("Hermes Events Manager", g_mgr)):
            login = "hermes.%s@itk.local" % ("events.user" if "Benutzer" in name else "events.manager")
            alt = k.kw("res.users", "search_read", [[("login", "=", login)], ["id"]], context={"active_test": False})
            for u in alt:
                k.kw("res.users", "write", [[u["id"]], {"active": False}])
            uid = k.kw("res.users", "create", [{
                "name": name, "login": login, "password": pwd,
                "groups_id": [(6, 0, gruppen)],
            }], context={"no_reset_password": True, "tracking_disable": True})
            ids.append((login, uid[0]["id"] if isinstance(uid, list) else uid))
        # Probedatensatz ausschliesslich fuer die Rechteprobe (wird entfernt)
        bestand_vorher = k.kw("event.event", "search_count", [[]], context={"active_test": False})
        probe_id = None
        try:
            env = lade_env()
            url = env.get("ODOO18_URL", "http://localhost:8069") if a.instanz == "lokal" else "https://k001959vsx.ipax.at"
            neu = k.kw("event.event", "create", [{
                "name": "Hermes Events Rechteprobe", "date_begin": "2030-01-01 09:00:00",
                "date_end": "2030-01-01 10:00:00", "date_tz": "Europe/Vienna",
                "x_is_online": True, "event_mail_ids": [(5, 0, 0)],
            }], context={"tracking_disable": True, "mail_create_nolog": True})
            probe_id = neu[0]["id"] if isinstance(neu, list) else neu
            for login, uid in ids:
                c = Client(url, env["ODOO18_DB"], login, pwd)
                lesen = c.kw("event.event", "search_count", [[]])
                schreiben = "nein"
                try:
                    c.kw("event.event", "write", [[probe_id], {"x_seats_min": 3}])
                    schreiben = "ja"
                except Exception as exc:  # noqa: BLE001
                    schreiben = "nein (%s)" % str(exc)[:50]
                anlegen, loeschen = "nein", "nein"
                try:
                    eigener = c.kw("event.event", "create", [{
                        "name": "Hermes Events Rechteprobe User", "date_begin": "2030-01-02 09:00:00",
                        "date_end": "2030-01-02 10:00:00", "date_tz": "Europe/Vienna",
                        "event_mail_ids": [(5, 0, 0)],
                    }], context={"tracking_disable": True, "mail_create_nolog": True})
                    eid = eigener[0]["id"] if isinstance(eigener, list) else eigener
                    anlegen = "ja"
                    try:
                        c.kw("event.event", "unlink", [[eid]])
                        loeschen = "ja"
                    except Exception as exc:  # noqa: BLE001
                        loeschen = "nein (%s)" % str(exc)[:40]
                except Exception as exc:  # noqa: BLE001
                    anlegen = "nein (%s)" % str(exc)[:40]
                print("  %-28s lesen: %s | schreiben: %s | anlegen: %s | loeschen: %s"
                      % (login, lesen, schreiben, anlegen, loeschen))
        finally:
            if probe_id:
                try:
                    k.kw("event.event", "unlink", [[probe_id]])
                except Exception:  # noqa: BLE001
                    pass
            # Reste der Rechteprobe entfernen
            reste = k.kw("event.event", "search", [[("name", "ilike", "Hermes Events Rechteprobe")]],
                         context={"active_test": False})
            if reste:
                k.kw("event.event", "unlink", [reste])
            for login, uid in ids:
                k.kw("res.users", "write", [[uid], {"active": False}], context={"tracking_disable": True})
                k.kw("res.users", "unlink", [[uid]])
            # Beim Anlegen eines Benutzers entsteht automatisch ein Kontakt;
            # die verwaisten Kontakte der Rechteprobe werden mit entfernt.
            verwaist = k.kw("res.partner", "search", [[("name", "in", ("Hermes Events Benutzer",
                                                                     "Hermes Events Manager")),
                                                      ("user_ids", "=", False)]],
                            context={"active_test": False})
            if verwaist:
                k.kw("res.partner", "unlink", [verwaist])
            print("  verwaiste Testkontakte entfernt:", len(verwaist))
            rest = k.kw("res.users", "search_count", [[("login", "ilike", "hermes.events.")]],
                        context={"active_test": False})
            bestand_nachher = k.kw("event.event", "search_count", [[]], context={"active_test": False})
            print("  Testbenutzer entfernt, Rest:", rest)
            print("  Veranstaltungen vorher/nachher:", bestand_vorher, "/", bestand_nachher)

    return 0 if not fehlend else 0


if __name__ == "__main__":
    sys.exit(main())
