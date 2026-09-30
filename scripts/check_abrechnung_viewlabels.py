"""Automatischer Label-Check fuer die in Views gesetzten Bezeichnungen (Bereich Abrechnung).

Zweiter Teil der Label-Regel (Anna, 30.09.2026): auch die direkt in Ansichten gesetzten
string=-Bezeichnungen (Formulare, Listen/Spalten, Reiter, Gruppen, Suchansichten, Filter,
Gruppierungen, Assistenten) sollen bei fachlich identischer Bedeutung den Odoo-11-Wortlaut
zeigen. Technische Feldnamen bleiben unveraendert.

Das Skript liest die zusammengesetzten Ansichten beider Systeme, stellt die Bezeichnungen
gegenueber und schreibt die Vergleichstabelle nach docs/o11-o18-abrechnung-viewlabels.md.

Aufruf:
    python scripts/check_abrechnung_viewlabels.py                # lokal und VM
    python scripts/check_abrechnung_viewlabels.py --instanz lokal
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o11, o18

# Zuordnung der Reiter/Gruppen und Suchleisten-Eintraege (fachlich identische Funktion)
GRUPPEN = [
    ("Kunde", "Partner"),
    ("Vertriebsmitarbeiter", "Verkäufer"),
    ("Verkaufsteam", "Vertriebskanal"),
    ("Status", "Status"),
    ("Rechnungsdatum", "Rechnungsdatum"),
    ("Fälligkeitsdatum", "Fälligkeit"),
    ("Buchungsdatum", "Fälligkeitsdatum"),
    ("Meine Rechnungen", "Meine Rechnungen"),
    ("Überfällig", "Überfällig"),
    ("Entwurf", "Entwurf"),
]

# Felder, deren Spalte/Beschriftung verglichen werden soll (O11-Feldname -> O18-Feldname)
SPALTEN = {
    "partner_id": "invoice_partner_display_name",
    "date_invoice": "invoice_date",
    "number": "name",
    "reference": "ref",
    "date_due": "invoice_date_due",
    "origin": "invoice_origin",
    "amount_total_signed": "amount_total_in_currency_signed",
    "residual_signed": "amount_residual_signed",
    "state": "state",
    "type": "move_type",
    "user_id": "invoice_user_id",
    "team_id": "team_id",
    "payment_term_id": "invoice_payment_term_id",
    "name": "narration",
}


def arch(k, modell, typ):
    try:
        d = k.kw(modell, "get_views", [[[False, typ]]], context={"lang": "de_DE"})
        return d["views"][typ]["arch"]
    except Exception:
        return k.kw(modell, "fields_view_get", [[], typ], context={"lang": "de_DE"})["arch"]


def xml(text):
    text = text.replace("&nbsp;", " ")
    text = re.sub(r"&(?!(amp|lt|gt|quot|apos|#\d+);)", "&amp;", text)
    return ET.fromstring(text)


def sammle(arch_text):
    w = xml(arch_text)
    daten = {"felder": {}, "buttons": [], "reiter": [], "gruppen": [], "filter": [], "gruppierungen": []}
    for f in w.findall(".//field"):
        name = f.get("name")
        if name and f.get("string"):
            daten["felder"][name] = f.get("string")
    for b in w.findall(".//button"):
        if b.get("string"):
            daten["buttons"].append(b.get("string"))
    for seite in w.findall(".//page"):
        if seite.get("string"):
            daten["reiter"].append(seite.get("string"))
    for gr in w.findall(".//group"):
        if gr.get("string"):
            daten["gruppen"].append(gr.get("string"))
    for f in w.findall(".//filter"):
        eintrag = (f.get("string") or "", f.get("domain") or "", f.get("context") or "")
        if "group_by" in eintrag[2]:
            daten["gruppierungen"].append(eintrag)
        else:
            daten["filter"].append(eintrag)
    return daten


# Begruendete Abweichungen (fachlich nicht identisch, dokumentiert)
BEGRUENDET = {
    ("liste", "invoice_partner_display_name"): "Odoo 11 beschriftete die Kundenspalte irrefuehrend mit 'Lieferant'; Odoo 18 trennt nach Belegart",
}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm", "beide"], default="beide")
    a = p.parse_args()
    lade_env()
    k11 = o11()
    instanzen = {"lokal": o18("lokal"), "vm": o18("vm")}
    if a.instanz != "beide":
        instanzen = {a.instanz: instanzen[a.instanz]}
    k18 = list(instanzen.values())[0]

    daten11 = {}
    for typ, modell in (("tree", "account.invoice"), ("form", "account.invoice"), ("search", "account.invoice")):
        daten11[typ] = sammle(arch(k11, modell, typ))
    daten18 = {}
    for typ, modell in (("list", "account.move"), ("form", "account.move"), ("search", "account.move")):
        daten18[typ] = sammle(arch(k18, modell, typ))

    print("=== Listen: Spaltenbezeichnungen ===")
    for f11, f18 in SPALTEN.items():
        s11 = daten11["tree"]["felder"].get(f11, "")
        s18 = daten18["list"]["felder"].get(f18, "")
        print("   %-28s O11 %-24s -> %-30s O18 %s" % (f11, s11 or "-", f18, s18 or "-"))
    print("\n=== Suche: Filter und Gruppierungen ===")
    for eintrag in daten11["search"]["filter"]:
        print("   O11 Filter : %-28s %s" % (eintrag[0], eintrag[1][:60]))
    for eintrag in daten18["search"]["filter"]:
        print("   O18 Filter : %-28s %s" % (eintrag[0], eintrag[1][:60]))
    for eintrag in daten11["search"]["gruppierungen"]:
        print("   O11 Gruppe : %-28s %s" % (eintrag[0], eintrag[2][:50]))
    for eintrag in daten18["search"]["gruppierungen"]:
        print("   O18 Gruppe : %-28s %s" % (eintrag[0], eintrag[2][:50]))
    print("\n=== Formular: Reiter und Gruppen ===")
    print("   O11 Reiter : %s" % daten11["form"]["reiter"])
    print("   O18 Reiter : %s" % daten18["form"]["reiter"])
    print("   O11 Gruppen: %s" % sorted(set(daten11["form"]["gruppen"]))[:14])
    print("   O18 Gruppen: %s" % sorted(set(daten18["form"]["gruppen"]))[:14])
    print("\n=== Formular: Buttons ===")
    print("   O11: %s" % daten11["form"]["buttons"])
    print("   O18: %s" % sorted(set(daten18["form"]["buttons"])))

    ziel = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "docs", "o11-o18-abrechnung-viewlabels.md")
    with open(ziel, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# View-Bezeichnungen Abrechnung (Odoo 11 gegen Odoo 18)\n\n")
        fh.write("Erzeugt von `scripts/check_abrechnung_viewlabels.py` (Stand 30.09.2026, Session 122).\n\n")
        fh.write("## Listen: Spalten\n\n| Odoo-11-Feld | Odoo-11-Bezeichnung | Odoo-18-Feld | Odoo-18-Bezeichnung |\n| --- | --- | --- | --- |\n")
        for f11, f18 in SPALTEN.items():
            fh.write("| `%s` | %s | `%s` | %s |\n" % (f11, daten11["tree"]["felder"].get(f11, "-"),
                                                      f18, daten18["list"]["felder"].get(f18, "-")))
        for titel, schluessel in (("Filter", "filter"), ("Gruppierungen", "gruppierungen")):
            fh.write("\n## Suche: %s\n\n| System | Bezeichnung | Bedingung |\n| --- | --- | --- |\n" % titel)
            for system, daten in (("Odoo 11", daten11["search"]), ("Odoo 18", daten18["search"])):
                for e in daten[schluessel]:
                    fh.write("| %s | %s | %s |\n" % (system, e[0] or "-", (e[1] or e[2])[:80]))
        fh.write("\n## Formular: Reiter, Gruppen, Knoepfe\n\n")
        fh.write("- Odoo 11 Reiter: %s\n- Odoo 18 Reiter: %s\n" % (daten11["form"]["reiter"], daten18["form"]["reiter"]))
        fh.write("- Odoo 11 Gruppen: %s\n- Odoo 18 Gruppen: %s\n" % (sorted(set(daten11["form"]["gruppen"])),
                                                                      sorted(set(daten18["form"]["gruppen"]))))
        fh.write("- Odoo 11 Knoepfe: %s\n- Odoo 18 Knoepfe: %s\n" % (daten11["form"]["buttons"],
                                                                      sorted(set(daten18["form"]["buttons"]))))
    print("\nVergleichstabelle: %s" % ziel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
