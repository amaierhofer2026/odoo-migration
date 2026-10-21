"""Deutsche Bezeichnungen im Personalbereich (Odoo 11-Wortlaut) setzen und pruefen.

Schreibt die de_DE-Slots der Menues/Aktion, die das Modul itk_hr umbenennt (der
Modul-Record setzt nur den Basistext; die Oberflaeche liest de_DE), und sucht
englische Restbezeichnungen im Personalbereich.

Aufruf:
    python scripts/hr_labels_de.py --instanz lokal [--setzen]
"""
from __future__ import annotations

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o18  # noqa: E402

DE = {"lang": "de_DE"}
EN = {"lang": "en_US"}

# (Modell, ID, deutscher Text im Odoo-11-Wortlaut)
SLOTS = [
    ("ir.ui.menu", 297, "Personal"),
    ("ir.ui.menu", 299, "Personal"),
    ("ir.ui.menu", 300, "Personal"),
    ("ir.actions.act_window", 464, "Personal"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    ap.add_argument("--setzen", action="store_true")
    a = ap.parse_args()
    k = o18(a.instanz)

    print("=== de_DE-Slots ===")
    for modell, rec_id, text in SLOTS:
        de = k.kw(modell, "read", [[rec_id], ["name"]], context=DE)[0]["name"]
        en = k.kw(modell, "read", [[rec_id], ["name"]], context=EN)[0]["name"]
        zustand = "OK" if de == text else "SETZEN"
        print("  %-22s %-4s de=%-14r en=%-14r %s" % (modell, rec_id, de, en, zustand))
        if a.setzen and de != text:
            k.kw(modell, "write", [[rec_id], {"name": text}], context=DE)
            neu = k.kw(modell, "read", [[rec_id], ["name"]], context=DE)[0]["name"]
            print("        -> jetzt de=%r" % neu)

    print("\n=== Menues im Personalbereich (de/en) ===")
    menues = k.kw("ir.ui.menu", "search_read", [[("id", "in", [297, 299, 300, 301, 307, 316])]],
                  fields=["id", "name"], context=DE)
    for m in menues:
        de = m["name"]
        en = k.kw("ir.ui.menu", "read", [[m["id"]], ["name"]], context=EN)[0]["name"]
        print("  %-4s de=%-24r en=%-24r %s" % (m["id"], de, en, "englisch!" if de == en else ""))

    print("\n=== Feldbezeichnungen der Personal-Modelle ohne deutsche Uebersetzung ===")
    fehlt = []
    for modell, felder in (("hr.employee", ["name", "firstname", "lastname", "work_email",
                                            "work_phone", "mobile_phone", "department_id", "job_id",
                                            "parent_id", "coach_id", "resource_calendar_id",
                                            "category_ids", "notes", "address_id", "work_location_id",
                                            "barcode", "pin", "gender", "marital", "birthday",
                                            "country_id", "identification_id", "passport_id",
                                            "bank_account_id", "user_id", "company_id", "active"]),
                           ("hr.department", ["name", "manager_id", "parent_id", "active"]),
                           ("hr.job", ["name", "department_id", "no_of_employee",
                                       "expected_employees", "description"]),
                           ("hr.work.location", ["name", "location_type", "address_id"]),
                           ("hr.leave.type", ["name", "request_unit", "requires_allocation"])):
        de = k.kw(modell, "fields_get", [[felder], ["string"]], context=DE)
        en = k.kw(modell, "fields_get", [[felder], ["string"]], context=EN)
        for feld in felder:
            if feld in de and feld in en and de[feld]["string"] == en[feld]["string"] \
                    and not de[feld]["string"].isupper():
                fehlt.append("%s.%s = %r" % (modell, feld, de[feld]["string"]))
    if fehlt:
        for f in fehlt:
            print("  ohne de_DE-Slot: %s" % f)
    else:
        print("  keine (alle geprueften Felder haben eine deutsche Bezeichnung)")

    print("\n=== Sichtbare Texte der Personal-Ansichten (englische Kandidaten) ===")
    views = k.kw("hr.employee", "get_views",
                 [[[False, "form"], [False, "list"], [False, "search"]]], context=DE)["views"]
    import re
    englisch = set()
    for typ, v in views.items():
        for m in re.finditer(r'string="([^"]{3,60})"', v["arch"]):
            text = m.group(1)
            # nur Texte ohne deutsche Merkmale und ohne Zahlen
            if re.match(r"^[A-Za-z][A-Za-z /&()-]+$", text) and not re.search(
                    r"\b(der|die|das|und|für|von|mit|zur|zum|im|in|am|je|bis|pro)\b", text.lower()):
                englisch.add((typ, text))
    if englisch:
        for typ, text in sorted(englisch):
            print("  %-8s %r" % (typ, text))
    else:
        print("  keine englischen Ansichtstexte gefunden")
    return 0


if __name__ == "__main__":
    sys.exit(main())
