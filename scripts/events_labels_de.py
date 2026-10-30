"""Deutsche Bezeichnungen im Bereich Events (Odoo-11-Wortlaut).

Das Modul itk_events_compat setzt die Basistexte von Menues, Phasen und
Ansichten. Die Oberflaeche liest aber den de_DE-Slot; dort steht noch die
Odoo-18-Bezeichnung ("Veranstaltungen", "Gebucht", ...). Dieses Skript
schreibt die de_DE-Slots und prueft anschliessend die gerenderten
Ansichten im Odoo-11-Wortlaut. Idempotent: bereits richtige Slots werden
nicht erneut geschrieben.

Aufruf:
    python scripts/events_labels_de.py --instanz lokal [--setzen]
"""
from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o18  # noqa: E402

DE = {"lang": "de_DE"}

# (Modell, XML-ID, Solltext im de_DE-Slot)
SLOTS = [
    ("ir.ui.menu", "event.event_main_menu", "Events"),
    ("ir.ui.menu", "event.menu_event_event", "Events"),
    ("ir.ui.menu", "event.menu_reporting_events", "Berichtswesen"),
    ("ir.ui.menu", "event.menu_event_configuration", "Konfiguration"),
    ("ir.ui.menu", "event.menu_event_type", "Anlasskategorien"),
    ("ir.ui.menu", "itk_events_compat.menu_report_event_itk_events", "Events"),
    ("ir.actions.act_window", "itk_events_compat.action_event_report_itk_events", "Events"),
]

# Odoo-11-Status auf den Odoo-18-Phasen
PHASEN = [
    ("event.event_stage_new", "Nicht bestätigt"),
    ("event.event_stage_booked", "Bestätigt"),
    ("event.event_stage_announced", "Angekündigt"),
    ("event.event_stage_done", "Erledigt"),
    ("event.event_stage_cancelled", "Abgebrochen"),
]

# Gerenderte Feldbeschriftungen: (Modell, View-XML-ID, Typ, Feld, Solltext)
ANSICHTEN = [
    ("event.event", "event.view_event_form", "form", "stage_id", "Status"),
    ("event.event", "event.view_event_form", "form", "event_type_id", "Kategorie"),
    ("event.event", "event.view_event_form", "form", "x_is_online", "Online-Event"),
    ("event.event", "event.view_event_form", "form", "x_seats_min", "Mindestzahl an Teilnehmern"),
    ("event.event", "event.view_event_form", "form", "x_o11_id", "Odoo-11-ID"),
    ("event.event", "event.view_event_tree", "list", "stage_id", "Status"),
    ("event.event", "event.view_event_tree", "list", "event_type_id", "Kategorie"),
    ("event.event", "event.view_event_tree", "list", "x_seats_min", "Mindestzahl an Teilnehmern"),
    ("event.event", "event.view_event_tree", "list", "seats_reserved", "Reservierungen"),
    ("event.event", "event.view_event_tree", "list", "user_id", "Verantwortlich"),
    ("event.type", "event.view_event_type_form", "form", "name", "Anlasskategorie"),
    ("event.type", "event.view_event_type_tree", "list", "name", "Anlasskategorie"),
]

# Suchfilter des Odoo-11-Stands
FILTER = [
    ("event.event", "event.view_event_search", "search", "Nicht bestätigt"),
    ("event.event", "event.view_event_search", "search", "Bestätigt"),
    ("event.event", "event.view_event_search", "search", "Erledigt"),
    ("event.event", "event.view_event_search", "search", "Abgebrochen"),
]


def rec_id(k, xmlid):
    modul, name = xmlid.split(".")
    treffer = k.kw("ir.model.data", "search_read",
                   [[("module", "=", modul), ("name", "=", name)], ["res_id", "model"]], context=DE)
    return treffer[0] if treffer else None


def arch(k, xmlid, typ):
    d = rec_id(k, xmlid)
    if not d:
        return ""
    r = k.kw("ir.ui.view", "get_views", [[[d["res_id"], typ]]], context=DE)
    return r["views"].get(typ, {}).get("arch", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    ap.add_argument("--setzen", action="store_true")
    a = ap.parse_args()
    k = o18(a.instanz)
    offen = []

    print("=== de_DE-Slots Menues und Aktionen ===")
    for modell, xmlid, text in SLOTS:
        d = rec_id(k, xmlid)
        if not d:
            print("  %-58s XML-ID FEHLT" % xmlid)
            offen.append(xmlid)
            continue
        rid = d["res_id"]
        ist = k.kw(modell, "read", [[rid], ["name"]], context=DE)[0]["name"]
        print("  %-56s de=%-24r %s" % (xmlid[-56:], ist, "OK" if ist == text else "SETZEN"))
        if a.setzen and ist != text:
            k.kw(modell, "write", [[rid], {"name": text}], context=DE)
            neu = k.kw(modell, "read", [[rid], ["name"]], context=DE)[0]["name"]
            print("        -> jetzt de=%r" % neu)
            if neu != text:
                offen.append(xmlid)
        elif ist != text:
            offen.append(xmlid)

    print("\n=== Phasen (Odoo-11-Status) ===")
    for xmlid, text in PHASEN:
        d = rec_id(k, xmlid)
        if not d:
            print("  %-58s XML-ID FEHLT" % xmlid)
            offen.append(xmlid)
            continue
        rid = d["res_id"]
        ist = k.kw("event.stage", "read", [[rid], ["name"]], context=DE)[0]["name"]
        print("  %-40s de=%-22r %s" % (xmlid, ist, "OK" if ist == text else "SETZEN"))
        if a.setzen and ist != text:
            k.kw("event.stage", "write", [[rid], {"name": text}], context=DE)
            neu = k.kw("event.stage", "read", [[rid], ["name"]], context=DE)[0]["name"]
            print("        -> jetzt de=%r" % neu)
            if neu != text:
                offen.append(xmlid)
        elif ist != text:
            offen.append(xmlid)

    print("\n=== Gerenderte Ansichten: Feldbeschriftungen ===")
    for modell, xmlid, typ, feld, soll in ANSICHTEN:
        text = arch(k, xmlid, typ)
        treffer = re.search(r"<field[^>]*name=\"%s\"[^>]*>" % re.escape(feld), text)
        if not treffer:
            print("  %-40s %-26s FELD NICHT IN DER ANSICHT" % (xmlid[-40:], feld))
            offen.append("%s.%s" % (xmlid, feld))
            continue
        m = re.search(r'string="([^"]*)"', treffer.group(0))
        ist = m.group(1) if m else ""
        if not ist:
            ist = k.kw(modell, "fields_get", [[feld], ["string"]], context=DE)[feld]["string"]
        ok = ist == soll
        print("  %-40s %-26s = %-34r %s" % (xmlid[-40:], feld, ist, "OK" if ok else "ABWEICHUNG"))
        if not ok:
            offen.append("%s.%s" % (xmlid, feld))

    print("\n=== Gerenderte Suchansichten: Filter ===")
    for modell, xmlid, typ, text_soll in FILTER:
        text = arch(k, xmlid, typ)
        ok = ('string="%s"' % text_soll) in text
        print("  %-40s %-28s %s" % (xmlid[-40:], text_soll, "OK" if ok else "FEHLT"))
        if not ok:
            offen.append("%s/%s" % (xmlid, text_soll))

    print("\n=== Ergebnis:", "0 offen" if not offen else "%d offen" % len(offen), "===")
    for x in offen:
        print("   -", x)
    return 0 if not offen else 1


if __name__ == "__main__":
    sys.exit(main())
