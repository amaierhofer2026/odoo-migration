"""Deutsche Bezeichnungen im Bereich E-Mail-Marketing (Odoo-11-Wortlaut).

Das Modul itk_mass_mailing_compat setzt die Basistexte; die Oberflaeche liest
den de_DE-Slot, dort steht noch die Odoo-18-Bezeichnung. Dieses Skript
schreibt die de_DE-Slots und prueft die gerenderten Ansichten.
Idempotent: bereits richtige Slots werden nicht erneut geschrieben.

Aufruf:
    python scripts/marketing_labels_de.py --instanz lokal [--setzen]
"""
from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o18  # noqa: E402

DE = {"lang": "de_DE"}

SLOTS = [
    ("ir.ui.menu", "mass_mailing.mass_mailing_menu", "Massenmailings"),
    ("ir.ui.menu", "itk_mass_mailing_compat.menu_itk_mailing_campaign", "Kampagnen"),
    ("ir.ui.menu", "itk_mass_mailing_compat.menu_itk_mailing_campaign_stage", "Kampagnenstufen"),
    ("ir.ui.menu", "itk_mass_mailing_compat.menu_itk_mailing_tag", "Kampagnen-Tags"),
    ("ir.actions.act_window", "itk_mass_mailing_compat.action_itk_mailing_campaign", "Kampagnen"),
    ("ir.actions.act_window", "itk_mass_mailing_compat.action_itk_mailing_campaign_stage", "Kampagnenstufen"),
    ("ir.actions.act_window", "itk_mass_mailing_compat.action_itk_mailing_tag", "Kampagnen-Tags"),
]

ANSICHTEN = [
    ("mailing.mailing", "itk_mass_mailing_compat.view_mailing_list_itk_marketing", "list",
     "x_o11_name", "Bezeichnung (Odoo 11)"),
    ("mailing.mailing", "itk_mass_mailing_compat.view_mailing_list_itk_marketing", "list",
     "itk_campaign_id", "Kampagne (Odoo 11)"),
    ("mailing.mailing", "itk_mass_mailing_compat.view_mailing_list_itk_marketing", "list",
     "x_o11_sent", "Gesendet (Odoo 11)"),
    ("mailing.mailing", "itk_mass_mailing_compat.view_mailing_list_itk_marketing", "list",
     "x_o11_delivered", "Zugestellt (Odoo 11)"),
    ("mailing.mailing", "itk_mass_mailing_compat.view_mailing_list_itk_marketing", "list",
     "x_o11_opened", "Geöffnet (Odoo 11)"),
    ("mailing.mailing", "itk_mass_mailing_compat.view_mailing_list_itk_marketing", "list",
     "x_o11_replied", "Geantwortet (Odoo 11)"),
    ("mailing.mailing", "itk_mass_mailing_compat.view_mailing_form_itk_marketing", "form",
     "itk_campaign_id", "Kampagne (Odoo 11)"),
]

FILTER = [
    ("mailing.mailing", "itk_mass_mailing_compat.view_mailing_search_itk_marketing", "search",
     "Aus Odoo 11 übernommen"),
    ("mailing.mailing", "itk_mass_mailing_compat.view_mailing_search_itk_marketing", "search",
     "Odoo-11-Entwürfe"),
]


def rec_id(k, xmlid):
    modul, name = xmlid.split(".")
    t = k.kw("ir.model.data", "search_read",
             [[("module", "=", modul), ("name", "=", name)], ["res_id", "model"]], context=DE)
    return t[0] if t else None


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

    print("=== de_DE-Slots Menues und Aktionen (%s) ===" % a.instanz)
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

    print("\n=== Gerenderte Ansichten: Feldbeschriftungen ===")
    for modell, xmlid, typ, feld, soll in ANSICHTEN:
        text = arch(k, xmlid, typ)
        treffer = re.search(r"<field[^>]*name=\"%s\"[^>]*>" % re.escape(feld), text)
        if not treffer:
            print("  %-44s %-24s FELD NICHT IN DER ANSICHT" % (xmlid[-44:], feld))
            offen.append("%s.%s" % (xmlid, feld))
            continue
        m = re.search(r'string="([^"]*)"', treffer.group(0))
        ist = m.group(1) if m else ""
        if not ist:
            ist = k.kw(modell, "fields_get", [[feld], ["string"]], context=DE)[feld]["string"]
        ok = ist == soll
        print("  %-44s %-24s = %-32r %s" % (xmlid[-44:], feld, ist, "OK" if ok else "ABWEICHUNG"))
        if not ok:
            offen.append("%s.%s" % (xmlid, feld))

    print("\n=== Suchfilter ===")
    for modell, xmlid, typ, text_soll in FILTER:
        text = arch(k, xmlid, typ)
        ok = ('string="%s"' % text_soll) in text
        print("  %-44s %-28s %s" % (xmlid[-44:], text_soll, "OK" if ok else "FEHLT"))
        if not ok:
            offen.append("%s/%s" % (xmlid, text_soll))

    print("\n=== Ergebnis:", "0 offen" if not offen else "%d offen" % len(offen), "===")
    for x in offen:
        print("   -", x)
    return 0 if not offen else 1


if __name__ == "__main__":
    sys.exit(main())
