"""Read-only Pruefung der Projekt-Anpassungen (itk_project) gegen die gerenderten Ansichten.

Aufruf: python scripts/verify_projekt.py --instanz lokal|vm
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o18  # noqa: E402


def arch(cli, modell, typ):
    try:
        res = cli.kw(modell, "get_views", [[(False, typ)]], options={"toolbar": False},
                     context={"lang": "de_DE"})
        for v in (res.get("views") or {}).values():
            return v.get("arch")
    except Exception:  # noqa: BLE001
        pass
    return ""


def felder_und_strings(arch_text):
    m = {}
    try:
        root = ET.fromstring(arch_text)
        for e in root.iter("field"):
            m.setdefault(e.get("name"), []).append(e.get("string"))
    except Exception:  # noqa: BLE001
        pass
    return m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", required=True, choices=["lokal", "vm"])
    a = ap.parse_args()
    cli = o18(a.instanz)

    ok = fehler = 0

    def pruefe(name, bedingung, detail=""):
        nonlocal ok, fehler
        if bedingung:
            ok += 1
            print("  OK    %-52s %s" % (name, detail))
        else:
            fehler += 1
            print("  FEHL  %-52s %s" % (name, detail))

    print("=== Modul und Modell ===")
    mm = cli.kw("ir.module.module", "search_read", [[("name", "=", "itk_project")]],
                fields=["name", "state", "installed_version"], limit=1)
    pruefe("itk_project installiert", bool(mm) and mm[0]["state"] == "installed",
           mm[0]["installed_version"] if mm else "-")
    fg = cli.kw("project.task", "fields_get", [["itk_date_start", "priority"]],
                attributes=["string", "type", "selection"])
    pruefe("Feld itk_date_start vorhanden", "itk_date_start" in fg)
    sel = fg.get("priority", {}).get("selection") or []
    pruefe("Prioritaet Niedrig/Normal", [list(x) for x in sel] == [["0", "Niedrig"], ["1", "Normal"]],
           str(sel))

    print("=== Projektansicht (project.project form) ===")
    a_form = felder_und_strings(arch(cli, "project.project", "form"))
    for feld, soll in [("task_count", "Aufgaben"), ("label_tickets", "Tickets verwenden als"),
                       ("is_favorite", "Projekt auf dem Dashboard anzeigen"),
                       ("account_id", "Kostenstelle"), ("last_update_status", "Projektstatus")]:
        werte = a_form.get(feld) or []
        pruefe("Formular %s" % feld, soll in werte, str(werte))

    print("=== Aufgabenansicht (project.task form/list/search) ===")
    a_tf = felder_und_strings(arch(cli, "project.task", "form"))
    pruefe("Startdatum im Formular", "itk_date_start" in a_tf)
    for feld, soll in [("stage_id", "Stufe"), ("user_ids", "Zugewiesen an"),
                       ("name", "Aufgabentitel"), ("child_ids", "Unteraufgaben"),
                       ("timesheet_ids", "Zeiterfassung"), ("allow_timesheets", "Zeiterfassungen erlauben")]:
        werte = a_tf.get(feld) or []
        pruefe("Formular %s" % feld, soll in werte, str(werte))
    a_tl = felder_und_strings(arch(cli, "project.task", "list"))
    pruefe("Startdatum in der Liste", "itk_date_start" in a_tl)
    a_ts = arch(cli, "project.task", "search")
    pruefe("Startdatum in der Suche", 'name="itk_date_start"' in a_ts)
    pruefe("Suchfilter Stufe deutsch", 'name="stage"' in a_ts and 'string="Stufe"' in a_ts)

    print("=== Projektphasen (Namen) ===")
    phasen = cli.kw("project.project.stage", "search_read", [[]], fields=["id", "name"],
                    order="sequence,id", limit=0)
    namen = [p["name"] for p in phasen]
    pruefe("Phasennamen deutsch", namen == ["Zu erledigen", "In Arbeit", "Erledigt", "Abgebrochen"],
           str(namen))

    print("=== Menue 'Arbeit starten' ===")
    menu = cli.kw("ir.ui.menu", "search_read",
                  [[("id", "=", 756)]], fields=["id", "name", "complete_name"], limit=0)
    pruefe("Menue 756 deutsch", bool(menu) and menu[0]["name"] == "Arbeit starten",
           str(menu[0]["complete_name"] if menu else "-"))

    print("\nErgebnis: %d OK / %d FEHL" % (ok, fehler))
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
