"""ITK Massenbearbeitung: Bereinigung und Pruefung (Odoo 18, lokal oder VM).

Umsetzung der Entscheidungen aus Session 140:
  K1  Dublette 1303 "Massenbearbeitung Kontakte" entfernen (behaelt "Tag-Zuweisung").
  K4  Bindung der Automatisierungs-Aktion "Execute Code" am Lead entfernen
      (Automatisierung selbst bleibt unveraendert und aktiv).
  K5  Menue Einstellungen > Massenverarbeitung nachweisen.

Das Skript ist idempotent: ein zweiter Lauf aendert nichts.
  python scripts/apply_massenbearbeitung.py --instanz lokal --pruefen   (nur lesen)
  python scripts/apply_massenbearbeitung.py --instanz lokal             (anwenden)
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o18  # noqa: E402

DE = {"lang": "de_DE"}
KONTAKT_MODELL = "res.partner"
STICHWORT_FELD = "category_id"
BEHALTEN = "Tag-Zuweisung"


def mass_edit_aktionen(k, modell=None):
    dom = [("state", "=", "mass_edit")]
    if modell:
        dom.append(("model_id.model", "=", modell))
    return k.kw("ir.actions.server", "search_read",
                [dom, ["id", "name", "model_id", "binding_model_id", "binding_type",
                       "mass_edit_line_ids"]], context=DE) or []


def zeilen_felder(k, aktion):
    """Technische Feldnamen der Massenbearbeitungszeilen (nicht die Anzeigenamen)."""
    if not aktion["mass_edit_line_ids"]:
        return []
    zeilen = k.kw("ir.actions.server.mass.edit.line", "read",
                  [aktion["mass_edit_line_ids"], ["field_id"]]) or []
    ids = [z["field_id"][0] for z in zeilen if z["field_id"]]
    if not ids:
        return []
    felder = k.kw("ir.model.fields", "read", [ids, ["name"]]) or []
    return sorted(f["name"] for f in felder)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    ap.add_argument("--pruefen", action="store_true", help="nur lesen, nichts schreiben")
    a = ap.parse_args()
    k = o18(a.instanz)
    ergebnis = []

    def melde(schritt, soll, ist, ok):
        ergebnis.append((schritt, soll, ist, ok))
        print("%-4s | %-52s | soll %-28s | ist %s" % ("OK" if ok else "FEHL", schritt, soll, ist))

    print("Instanz: %s%s\n" % (a.instanz, "  (Prueflauf, keine Aenderung)" if a.pruefen else ""))

    # ---- K1: Dubletten bei den Stichwort-Aktionen auf dem Kontakt
    kandidaten = []
    for akt in mass_edit_aktionen(k, KONTAKT_MODELL):
        felder = zeilen_felder(k, akt)
        if felder == [STICHWORT_FELD]:
            kandidaten.append(akt)
    namen = [x["name"] for x in kandidaten]
    print("Stichwort-Aktionen am Kontakt: %s" % namen)
    zu_loeschen = [x for x in kandidaten if x["name"] != BEHALTEN]
    if not zu_loeschen:
        melde("K1 Dublette entfernt (nur '%s' vorhanden)" % BEHALTEN, 1, len(kandidaten), len(kandidaten) == 1)
    else:
        for akt in zu_loeschen:
            if a.pruefen:
                melde("K1 Dublette '%s' (id %s) wuerde entfernt" % (akt["name"], akt["id"]),
                      1, len(kandidaten), False)
            else:
                k.kw("ir.actions.server", "unlink", [[akt["id"]]])
                melde("K1 Dublette '%s' (id %s) entfernt" % (akt["name"], akt["id"]), 1, 1, True)

    # ---- K4: Bindung der Automatisierungs-Aktion am Lead
    exec_aktionen = k.kw("ir.actions.server", "search_read",
                         [[("name", "=", "Execute Code"), ("model_id.model", "=", "crm.lead")],
                          ["id", "name", "binding_model_id", "binding_type", "code"]]) or []
    gebunden = [x for x in exec_aktionen if x["binding_model_id"]]
    if not exec_aktionen:
        melde("K4 Automatisierungs-Aktion 'Execute Code' vorhanden", True, False, False)
    elif not gebunden:
        melde("K4 'Execute Code' ohne Menuebindung", True, True, True)
    else:
        for akt in gebunden:
            if a.pruefen:
                melde("K4 Bindung von 'Execute Code' (id %s) wuerde entfernt" % akt["id"], True, False, False)
            else:
                k.kw("ir.actions.server", "write", [[akt["id"]], {"binding_model_id": False}])
                melde("K4 Bindung von 'Execute Code' (id %s) entfernt" % akt["id"], True, True, True)

    # Automatisierung selbst: aktiv und unveraendert
    autos = k.kw("base.automation", "search_read",
                 [[("name", "ilike", "zur Verrechnung bereit")],
                  ["id", "name", "active", "trigger", "model_id"]], context=DE) or []
    melde("K4 Automatisierung weiterhin vorhanden und aktiv",
          "1 aktiv", "%s aktiv=%s" % (len(autos), [x["active"] for x in autos]),
          len(autos) == 1 and autos[0]["active"])

    # ---- T1: many2many-Felder im Dialog als Stichwort-Feld bedienbar machen
    # Ohne widget_option rendert Odoo 18 ein many2many als Unterliste mit eigenem Dialog.
    # Odoo 11 zeigte im selben Dialog direkt ein Stichwortfeld. Das OCA-Modul bietet dafuer
    # das Feld widget_option je Zeile; hier wird es fuer die beiden Stichwort-Aktionen gesetzt.
    for akt in mass_edit_aktionen(k):
        if akt["name"] not in ("Tag-Zuweisung", "Interessent Stichwort setzen"):
            continue
        for zeile_id in akt["mass_edit_line_ids"]:
            zeile = k.kw("ir.actions.server.mass.edit.line", "read",
                         [[zeile_id], ["field_id", "widget_option"]])[0]
            if zeile["widget_option"] == "many2many_tags":
                melde("T1 '%s': Stichwortfeld als Tags" % akt["name"], "many2many_tags",
                      "many2many_tags", True)
                continue
            if a.pruefen:
                melde("T1 '%s' wuerde widget_option setzen" % akt["name"], "many2many_tags",
                      zeile["widget_option"], False)
            else:
                k.kw("ir.actions.server.mass.edit.line", "write",
                     [[zeile_id], {"widget_option": "many2many_tags"}])
                melde("T1 '%s': Stichwortfeld als Tags gesetzt" % akt["name"], "many2many_tags",
                      "many2many_tags", True)

    # ---- K5: Menue Massenverarbeitung
    xmlid = k.kw("ir.model.data", "search_read",
                 [[("module", "=", "itk_massenbearbeitung"), ("name", "=", "menu_massenbearbeitung")],
                  ["res_id", "model"]])
    if not xmlid:
        melde("K5 Menue Massenverarbeitung vorhanden", True, False, False)
    else:
        menue = k.kw("ir.ui.menu", "read", [[xmlid[0]["res_id"]], ["name", "complete_name", "action"]],
                     context=DE)[0]
        aktion_id = int((menue["action"] or "ir.actions.act_window,0").split(",")[1])
        aktion = k.kw("ir.actions.act_window", "read", [[aktion_id], ["name", "res_model", "domain"]],
                      context=DE)[0]
        melde("K5 Menuepfad", "Einstellungen/Massenverarbeitung", menue["complete_name"],
              menue["complete_name"] == "Einstellungen/Massenverarbeitung")
        melde("K5 Menueaktion filtert auf Massenbearbeitung", "mass_edit", aktion["domain"],
              "mass_edit" in (aktion["domain"] or ""))

    # ---- Bestand
    alle = mass_edit_aktionen(k)
    print("\nMassenbearbeitungs-Aktionen gesamt: %d" % len(alle))
    for akt in sorted(alle, key=lambda x: x["id"]):
        print("  %4d | %-45s | %-24s | %s" % (akt["id"], akt["name"][:45], akt["model_id"][1],
                                              ", ".join(zeilen_felder(k, akt))))

    ok = sum(1 for x in ergebnis if x[3])
    print("\n=== Ergebnis: %d OK / %d FEHL ===" % (ok, len(ergebnis) - ok))
    return 0 if ok == len(ergebnis) else 1


if __name__ == "__main__":
    sys.exit(main())
