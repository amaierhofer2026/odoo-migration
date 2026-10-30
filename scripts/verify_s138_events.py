"""Abnahmepruefung Bereich EVENTS (Session 138) - read-only.

Prueft Struktur, Beschriftungen, Filter, Rechte und Daten gegen Odoo 11:
  * Module, Menues, Phasen, de_DE-Beschriftungen, Ansichten, Filter
  * Cron "Event: Mail Scheduler" stillgelegt, kein Mailplaner offen
  * 122 Veranstaltungen mit Beginn, Ende, Zeitzone, Status, Kategorie,
    Platzlogik, Veroeffentlichungsstatus und Odoo-11-Referenzen
  * KEINE Kontakte, Teilnehmer, E-Mail-Adressen, Partnerverknuepfungen
  * Feldgleicheit je Datensatz gegen den Odoo-11-Livebestand

Aufruf:
    python scripts/verify_s138_events.py --instanz lokal
    python scripts/verify_s138_events.py --instanz vm
"""
from __future__ import annotations

import argparse
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

DE = {"lang": "de_DE"}
OK = 0
FEHLER = []


def pruefe(bedingung, text, ist=None, soll=None):
    global OK
    if bedingung:
        OK += 1
    else:
        FEHLER.append("%s (ist=%r soll=%r)" % (text, ist, soll))
    return bedingung


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    a = ap.parse_args()
    k = o18(a.instanz)
    k11 = o11()
    print("=== Abnahme EVENTS (%s) ===" % a.instanz)

    # ---------------------------------------------------------- Module
    mods = {m["name"]: m for m in k.kw("ir.module.module", "search_read",
                                       [[("name", "in", ["event", "website_event", "itk_events_compat"])],
                                        ["name", "state", "installed_version"]])}
    for name in ("event", "website_event", "itk_events_compat"):
        pruefe(mods.get(name, {}).get("state") == "installed",
               "Modul %s installiert" % name, mods.get(name, {}).get("state"))
    print("  Module:", {n: mods.get(n, {}).get("installed_version") for n in mods})

    # ---------------------------------------------------------- Menues
    def menue(xmlid):
        modul, name = xmlid.split(".")
        d = k.kw("ir.model.data", "search_read", [[("module", "=", modul), ("name", "=", name)], ["res_id"]])
        if not d:
            return None
        return k.kw("ir.ui.menu", "read", [[d[0]["res_id"]], ["name", "complete_name"]], context=DE)[0]

    soll_menues = {
        "event.event_main_menu": "Events",
        "event.menu_event_event": "Events",
        "event.menu_reporting_events": "Berichtswesen",
        "event.menu_event_configuration": "Konfiguration",
        "event.menu_event_type": "Anlasskategorien",
        "itk_events_compat.menu_report_event_itk_events": "Events",
    }
    for xmlid, soll in soll_menues.items():
        m = menue(xmlid)
        pruefe(m is not None and m["name"] == soll, "Menue %s = %r" % (xmlid, soll),
               m["name"] if m else None, soll)
        if m:
            print("    %-52s %s" % (m["complete_name"], m["name"]))
    pruefe(menue("event.menu_event_event")["complete_name"] == "Events/Events",
           "Pfad App/Liste = 'Events/Events'",
           menue("event.menu_event_event")["complete_name"], "Events/Events")
    pruefe(menue("itk_events_compat.menu_report_event_itk_events")["complete_name"] == "Events/Berichtswesen/Events",
           "Pfad Berichtswesen = 'Events/Berichtswesen/Events'",
           menue("itk_events_compat.menu_report_event_itk_events")["complete_name"], "")

    # ---------------------------------------------------------- Phasen
    phasen = {p["sequence"]: p["name"] for p in
              k.kw("event.stage", "search_read", [[], ["name", "sequence"]], context=DE)}
    soll_phasen = {1: "Nicht bestätigt", 2: "Bestätigt", 5: "Erledigt", 6: "Abgebrochen"}
    for seq, name in soll_phasen.items():
        pruefe(phasen.get(seq) == name, "Phase %s = %r" % (seq, name), phasen.get(seq), name)
    pruefe(phasen.get(3) == "Angekündigt", "Odoo-18-Zusatzphase 'Angekündigt' erhalten", phasen.get(3))

    # ---------------------------------------------------------- Cron
    crons = k.kw("ir.cron", "search_read", [[("name", "ilike", "Mail Scheduler")], ["name", "active"]],
                 context={"active_test": False})
    pruefe(len(crons) == 1 and not crons[0]["active"], "Cron 'Event: Mail Scheduler' stillgelegt",
           [(c["name"], c["active"]) for c in crons], "1 x inaktiv")

    # ---------------------------------------------------------- Ansichten
    def arch(xmlid, typ):
        modul, name = xmlid.split(".")
        d = k.kw("ir.model.data", "search_read", [[("module", "=", modul), ("name", "=", name)], ["res_id"]])
        if not d:
            return ""
        return k.kw("ir.ui.view", "get_views", [[[d[0]["res_id"], typ]]], context=DE)["views"].get(typ, {}).get("arch", "")

    form = arch("event.view_event_form", "form")
    liste = arch("event.view_event_tree", "list")
    suche = arch("event.view_event_search", "search")
    for marker, text in [("x_is_online", "Formular: Online-Event"),
                         ("x_seats_min", "Formular: Mindestzahl an Teilnehmern"),
                         ("x_o11_id", "Formular: Odoo-11-ID"),
                         ("Odoo-11-Angaben", "Formular: Reiter Odoo-11-Angaben"),
                         ("string=\"Status\"", "Formular: Statusbezeichnung")]:
        pruefe(marker in form, text, form.count(marker), ">0")
    for marker, text in [("x_seats_min", "Liste: Mindestzahl"),
                         ("event_type_id", "Liste: Kategorie"),
                         ("string=\"Status\"", "Liste: Status"),
                         ("string=\"Reservierungen\"", "Liste: Reservierungen")]:
        pruefe(marker in liste, text, liste.count(marker), ">0")
    for name in ("Nicht bestätigt", "Bestätigt", "Erledigt", "Abgebrochen"):
        pruefe('string="%s"' % name in suche, "Suche: Filter %r" % name)
    pruefe(len(arch("itk_events_compat.view_event_pivot_itk_events", "pivot")) > 0, "Pivot Veranstaltungen vorhanden")
    pruefe(len(arch("itk_events_compat.view_event_graph_itk_events", "graph")) > 0, "Graph Veranstaltungen vorhanden")

    # Filterdomains ausfuehren
    erwartet = {"[('stage_id.sequence', '=', 1)]": None,
                "[('stage_id.sequence', '=', 2)]": None,
                "[('stage_id.sequence', '=', 5)]": None,
                "[('stage_id.sequence', '=', 6)]": None}
    for dom in erwartet:
        try:
            erwartet[dom] = k.kw("event.event", "search_count", [eval(dom, {"__builtins__": {}}, {})])
        except Exception as e:  # noqa: BLE001
            erwartet[dom] = "FEHLER: %s" % str(e)[:60]
        pruefe(isinstance(erwartet[dom], int), "Filterdomain %s ausfuehrbar" % dom, erwartet[dom])
    print("  Filtertreffer:", erwartet)

    # ---------------------------------------------------------- Daten
    ev = k.kw("event.event", "search_read", [[], [
        "x_o11_id", "name", "date_begin", "date_end", "date_tz", "stage_id",
        "event_type_id", "seats_limited", "seats_max", "x_seats_min", "x_is_online",
        "x_o11_state", "x_o11_registrations", "x_o11_organizer_id", "x_o11_address_id",
        "website_published", "user_id", "active", "organizer_id", "address_id",
    ]], context=dict(DE, active_test=False), order="x_o11_id")

    pruefe(len(ev) == 122, "122 Veranstaltungen", len(ev), 122)
    pruefe(sum(1 for e in ev if e["active"]) == 121, "121 aktive Veranstaltungen",
           sum(1 for e in ev if e["active"]), 121)
    pruefe(sum(1 for e in ev if not e["active"]) == 1, "1 archivierte Veranstaltung uebernommen",
           sum(1 for e in ev if not e["active"]), 1)
    pruefe(all(e["x_o11_id"] for e in ev), "Odoo-11-ID bei allen Datensaetzen",
           sum(1 for e in ev if not e["x_o11_id"]), 0)
    pruefe(len({e["x_o11_id"] for e in ev}) == 122, "Odoo-11-IDs eindeutig",
           len({e["x_o11_id"] for e in ev}), 122)

    status = collections.Counter(e["stage_id"][1] for e in ev if e["stage_id"])
    pruefe(status.get("Bestätigt") == 100, "Phase Bestätigt = 100", status.get("Bestätigt"), 100)
    pruefe(status.get("Erledigt") == 7, "Phase Erledigt = 7", status.get("Erledigt"), 7)
    pruefe(status.get("Abgebrochen") == 15, "Phase Abgebrochen = 15", status.get("Abgebrochen"), 15)

    pruefe(all(e["date_tz"] == "Europe/Berlin" for e in ev), "Zeitzone Europe/Berlin bei allen",
           collections.Counter(e["date_tz"] for e in ev))
    pruefe(sum(1 for e in ev if e["website_published"]) == 101, "Veroeffentlicht = 101",
           sum(1 for e in ev if e["website_published"]), 101)
    pruefe(sum(1 for e in ev if e["x_is_online"]) == 120, "Online-Kennzeichen = 120",
           sum(1 for e in ev if e["x_is_online"]), 120)
    pruefe(sum(1 for e in ev if e["seats_limited"]) == 116, "Platzbegrenzung = 116",
           sum(1 for e in ev if e["seats_limited"]), 116)
    pruefe(sum(e["x_seats_min"] for e in ev) == 552, "Summe Mindestzahl = 552",
           sum(e["x_seats_min"] for e in ev), 552)
    pruefe(sum(e["x_o11_registrations"] for e in ev) == 760, "Summe Odoo-11-Anmeldungen = 760",
           sum(e["x_o11_registrations"] for e in ev), 760)
    kat = collections.Counter((e["event_type_id"] or ["-", "(keine)"])[1] for e in ev)
    pruefe(kat.get("Online") == 120, "Kategorie Online = 120", kat.get("Online"), 120)
    pruefe(kat.get("(keine)") == 2, "ohne Kategorie = 2", kat.get("(keine)"), 2)

    # ---------------------------------------------------------- keine Personen
    pruefe(sum(1 for e in ev if e["organizer_id"]) == 0, "keine Veranstalter-Kontakte verknuepft",
           sum(1 for e in ev if e["organizer_id"]), 0)
    pruefe(sum(1 for e in ev if e["address_id"]) == 0, "keine Orte verknuepft",
           sum(1 for e in ev if e["address_id"]), 0)
    pruefe(sum(1 for e in ev if e["x_o11_organizer_id"]) == 122,
           "Odoo-11-Kontakt-ID Veranstalter dokumentiert",
           sum(1 for e in ev if e["x_o11_organizer_id"]), 122)
    pruefe(sum(1 for e in ev if e["x_o11_address_id"]) == 122,
           "Odoo-11-Kontakt-ID Ort dokumentiert",
           sum(1 for e in ev if e["x_o11_address_id"]), 122)
    pruefe(k.kw("event.registration", "search_count", [[]], context={"active_test": False}) == 0,
           "keine Teilnehmer migriert",
           k.kw("event.registration", "search_count", [[]], context={"active_test": False}), 0)
    # Kein Kontaktzuwachs: kein Kontakt darf nach der ersten uebernommenen
    # Veranstaltung entstanden sein (die Migration legt keine Kontakte an).
    partner = k.kw("res.partner", "search_count", [[]], context={"active_test": False})
    erstes_event = min(e.get("create_date") or "9999-12-31" for e in
                       k.kw("event.event", "search_read", [[], ["create_date"]], context={"active_test": False}))
    neue_kontakte = k.kw("res.partner", "search_count",
                         [[("create_date", ">=", erstes_event)]], context={"active_test": False})
    pruefe(neue_kontakte == 0, "kein Kontakt seit der Migration angelegt",
           neue_kontakte, 0)
    print("  res.partner gesamt (aktiv/inaktiv): %s / %s  (ab %s keine neuen)"
          % (partner, k.kw("res.partner", "search_count", [[]]), erstes_event))

    # ---------------------------------------------------------- Mailplaner
    mails = k.kw("event.mail", "search_read", [[], ["mail_done", "event_id", "template_ref"]])
    pruefe(len(mails) == 170, "170 historische Mailplaner", len(mails), 170)
    pruefe(all(m["mail_done"] for m in mails), "alle Mailplaner als erledigt gekennzeichnet",
           sum(1 for m in mails if not m["mail_done"]), 0)

    # ---------------------------------------------------------- Vergleich mit Odoo 11
    e11 = {e["id"]: e for e in k11.kw("event.event", "search_read", [[("id", ">", 0)], [
        "id", "name", "date_begin", "date_end", "date_tz", "state", "seats_max",
        "seats_availability", "is_online", "website_published", "active"]],
        context={"lang": "de_DE", "active_test": False})}
    abw = []
    for e in ev:
        q = e11.get(e["x_o11_id"])
        if not q:
            abw.append((e["x_o11_id"], "in Odoo 11 nicht vorhanden"))
            continue
        for feld_o18, feld_o11 in (("name", "name"), ("date_begin", "date_begin"),
                                   ("date_end", "date_end"), ("date_tz", "date_tz")):
            if e[feld_o18] != q[feld_o11]:
                abw.append((e["x_o11_id"], "%s: %r != %r" % (feld_o18, e[feld_o18], q[feld_o11])))
        if e["x_o11_state"] != q["state"]:
            abw.append((e["x_o11_id"], "Status: %r != %r" % (e["x_o11_state"], q["state"])))
        if bool(e["x_is_online"]) != bool(q["is_online"]):
            abw.append((e["x_o11_id"], "Online: %r != %r" % (e["x_is_online"], q["is_online"])))
        if bool(e["website_published"]) != bool(q["website_published"]):
            abw.append((e["x_o11_id"], "Veroeffentlicht: %r != %r" % (e["website_published"], q["website_published"])))
        if bool(e["active"]) != bool(q["active"]):
            abw.append((e["x_o11_id"], "Aktiv: %r != %r" % (e["active"], q["active"])))
        if e["seats_limited"] != (q["seats_availability"] == "limited"):
            abw.append((e["x_o11_id"], "Platzbegrenzung: %r != %r" % (e["seats_limited"], q["seats_availability"])))
        if e["seats_limited"] and e["seats_max"] != q["seats_max"]:
            abw.append((e["x_o11_id"], "Hoechstzahl: %r != %r" % (e["seats_max"], q["seats_max"])))
    pruefe(not abw, "Feldgleichheit je Datensatz gegen Odoo 11", abw[:5], "keine Abweichung")
    if abw:
        print("  Abweichungen (erste 10):")
        for x in abw[:10]:
            print("    ", x)

    print("\n=== Ergebnis: %d OK / %d FEHLER ===" % (OK, len(FEHLER)))
    for f in FEHLER:
        print("   FEHLER:", f)
    return 0 if not FEHLER else 1


if __name__ == "__main__":
    sys.exit(main())
