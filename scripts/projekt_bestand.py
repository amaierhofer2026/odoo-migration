"""Read-only Bestands- und Labelvergleich Projekt (Odoo 11 gegen Odoo 18).

Aufruf: python scripts/projekt_bestand.py --quelle o11|lokal|vm
Schreibt JSON (Rohdaten) und gibt eine lesbare Zusammenfassung aus.
Nur lesende Aufrufe.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

STD = os.path.join(os.environ.get("USERPROFILE", "."), "Desktop",
                   "Odoo18-Projekt-Session133", "rohdaten")

MODELLE = ["project.project", "project.task", "project.task.type", "project.tags",
           "project.milestone", "project.project.stage", "project.update",
           "account.analytic.line", "account.analytic.account", "project.task.stage.personal",
           "project.collaborator"]


def zaehle(cli, modell, domain=None):
    try:
        return cli.kw(modell, "search_count", [domain or []])
    except Exception as exc:  # noqa: BLE001
        return "FEHLER " + str(exc)[:70]


def verteile(cli, modell, feld, limit=0):
    """Verteilung eines Feldes: liest die Werte und zaehlt in Python (versionsrobust)."""
    from collections import Counter
    try:
        saetze = cli.kw(modell, "search_read", [[]], fields=[feld], limit=limit)
    except Exception as exc:  # noqa: BLE001
        return {"__fehler__": str(exc)[:120]}
    zaehler = Counter()
    for s in saetze:
        w = s.get(feld)
        if isinstance(w, list):
            w = w[1] if len(w) > 1 else w
        zaehler[str(w)] += 1
    return sorted(zaehler.items(), key=lambda kv: -kv[1])


def hat(cli, modell, feld):
    try:
        f = cli.kw(modell, "fields_get", [], attributes=["type"])
        return feld in f
    except Exception:  # noqa: BLE001
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quelle", required=True, choices=["o11", "lokal", "vm"])
    ap.add_argument("--ordner", default=STD)
    a = ap.parse_args()
    os.makedirs(a.ordner, exist_ok=True)
    cli = o11() if a.quelle == "o11" else o18(a.quelle)
    d = {"quelle": a.quelle}

    print("### Quelle:", a.quelle)

    print("\n=== Bestand je Modell ===")
    for m in MODELLE:
        n = zaehle(cli, m)
        print("  %-32s %s" % (m, n))
        d.setdefault("bestand", {})[m] = n

    print("\n=== Verteilungen project.project ===")
    for feld in ("privacy_visibility", "label_tasks", "stage_id", "user_id", "active", "rating_status"):
        if hat(cli, "project.project", feld):
            g = verteile(cli, "project.project", feld)
            d.setdefault("verteilung_project", {})[feld] = g
            print("  -- %s" % feld)
            if isinstance(g, dict):
                print("     FEHLER:", g.get("__fehler__"))
            else:
                for name, n in g:
                    print("     %-46s %s" % (name[:46], n))
        else:
            print("  -- %s: Feld nicht vorhanden" % feld)

    print("\n=== Verteilungen project.task ===")
    for feld in ("stage_id", "priority", "kanban_state", "state", "user_id", "user_ids", "active"):
        if hat(cli, "project.task", feld):
            g = verteile(cli, "project.task", feld)
            d.setdefault("verteilung_task", {})[feld] = g
            print("  -- %s" % feld)
            if isinstance(g, dict):
                print("     FEHLER:", g.get("__fehler__"))
            else:
                for name, n in g:
                    print("     %-46s %s" % (name[:46], n))
        else:
            print("  -- %s: Feld nicht vorhanden" % feld)

    print("\n=== Aufgaben-Kennzahlen ===")
    kenn = {}
    for label, modell, feld, op in [
        ("Aufgaben mit Tag", "project.task", "tag_ids", "!="),
        ("Aufgaben ohne Tag", "project.task", "tag_ids", "="),
        ("Aufgaben mit Endtermin", "project.task", "date_deadline", "!="),
        ("Aufgaben mit Auftragsposition", "project.task", "sale_line_id", "!="),
        ("Aufgaben mit Stufe", "project.task", "stage_id", "!="),
        ("Aufgaben mit Unteraufgabe", "project.task", "child_ids", "!="),
        ("Aufgaben mit gepl. Std (O11)", "project.task", "planned_hours", "!="),
        ("Aufgaben mit zugeteilten Std (O18)", "project.task", "allocated_hours", "!="),
        ("Aufgaben mit Zeiterfassung", "project.task", "timesheet_ids", "!="),
    ]:
        if hat(cli, modell, feld):
            key = (feld, op)
            if key not in kenn:
                kenn[key] = zaehle(cli, modell, [(feld, op, False)])
            print("  %-42s %s" % (label, kenn[key]))
            d.setdefault("kennzahlen", {})[label] = kenn[key]
        else:
            print("  %-42s Feld nicht vorhanden" % label)

    print("\n=== Zeiterfassung (account.analytic.line) ===")
    if hat(cli, "account.analytic.line", "project_id"):
        print("  Zeilen mit Projekt:", zaehle(cli, "account.analytic.line", [("project_id", "!=", False)]))
        d["zt_mit_projekt"] = zaehle(cli, "account.analytic.line", [("project_id", "!=", False)])
    if hat(cli, "account.analytic.line", "task_id"):
        print("  Zeilen mit Aufgabe:", zaehle(cli, "account.analytic.line", [("task_id", "!=", False)]))
    if hat(cli, "account.analytic.line", "project_id"):
        for feld in ("user_id", "employee_id", "unit_amount", "date", "so_line"):
            print("  Feld %-14s vorhanden=%s" % (feld, hat(cli, "account.analytic.line", feld)))

    print("\n=== Gruppen der Projekt-Kategorie ===")
    try:
        gruppen = cli.kw("res.groups", "search_read",
                         [[("category_id.name", "ilike", "project")]],
                         fields=["id", "name", "category_id", "users", "implied_ids", "share"], limit=0)
    except Exception as exc:  # noqa: BLE001
        gruppen = []
        print("  FEHLER:", str(exc)[:140])
    d["gruppen"] = gruppen
    for g in gruppen:
        print("  %-4s %-30s kat=%-22s Benutzer=%d implied=%s" % (
            g["id"], (g["name"] or "")[:30],
            (g["category_id"][1] if isinstance(g["category_id"], list) else "-")[:22],
            len(g["users"]), [i for i in (g["implied_ids"] or [])]))

    print("\n=== Deutsche Feldbezeichnungen (de_DE) ===")
    for modell in ("project.project", "project.task", "project.task.type", "project.tags",
                   "account.analytic.line"):
        try:
            f = cli.kw(modell, "fields_get", [], attributes=["string", "type", "required", "readonly"],
                       context={"lang": "de_DE"})
            d.setdefault("labels_de", {})[modell] = f
            print("  -- %s: %d Felder erfasst" % (modell, len(f)))
        except Exception as exc:  # noqa: BLE001
            print("  -- %s FEHLER %s" % (modell, str(exc)[:100]))

    pfad = os.path.join(a.ordner, "projekt_bestand_%s.json" % a.quelle)
    with open(pfad, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1, sort_keys=True, default=str)
    print("\nRohdaten:", pfad)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
