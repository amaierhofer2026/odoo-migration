"""Read-only Erhebung des Bereichs Projekt in Odoo 11 und Odoo 18 (lokal/VM).

Aufruf:
  python scripts/erhebe_projekt.py --quelle o11
  python scripts/erhebe_projekt.py --quelle lokal
  python scripts/erhebe_projekt.py --quelle vm

Es werden ausschliesslich lesende RPC-Aufrufe gemacht. Rohdaten landen als JSON
im Ordner --ordner (Standard: Desktop\Odoo18-Projekt-Session133\rohdaten).
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

FELD_ATTR = ["string", "type", "required", "readonly", "relation", "selection",
             "store", "help", "size", "digits", "translate", "oldname"]

KERN_MODELLE = ["project.project", "project.task", "project.task.type", "project.tags"]

# Kandidatenfelder fuer Stammdaten-/Bestandslisten (werden gegen fields_get gefiltert)
STAEM_QUELLEN = {
    "project.project": ["id", "name", "partner_id", "user_id", "privacy_visibility", "description",
                        "date_start", "date", "label_tasks", "alias_id", "analytic_account_id",
                        "account_id", "type_ids", "stage_id", "tag_ids", "active", "color",
                        "currency_id", "allow_timesheets", "allow_billable", "sale_line_id",
                        "company_id", "task_count", "rating_status"],
    "project.task.type": ["id", "name", "sequence", "fold", "closed", "description",
                          "legend_priority", "project_ids", "active", "mail_template_id"],
    "project.tags": ["id", "name", "color", "active"],
    "project.task": ["id", "name", "project_id", "partner_id", "user_id", "user_ids", "priority",
                     "stage_id", "date_deadline", "date_start", "planned_hours", "remaining_hours",
                     "effective_hours", "subtask_count", "tag_ids", "parent_id", "active",
                     "kanban_state", "color", "sale_line_id", "partner_id"],
}


def felder(cli, modell):
    try:
        return cli.kw(modell, "fields_get", [], attributes=FELD_ATTR)
    except Exception as exc:  # noqa: BLE001
        return {"__fehler__": str(exc)[:200]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quelle", required=True, choices=["o11", "lokal", "vm"])
    ap.add_argument("--ordner", default=STD)
    a = ap.parse_args()
    os.makedirs(a.ordner, exist_ok=True)

    cli = o11() if a.quelle == "o11" else o18(a.quelle)
    d = {"quelle": a.quelle}

    print("### Quelle:", a.quelle)

    # 1) Module
    print("\n=== Module (project/timesheet/analytic/sale_project) ===")
    d["module"] = cli.kw("ir.module.module", "search_read",
                         [["|", "|", "|", "|",
                           ("name", "ilike", "project"),
                           ("name", "ilike", "timesheet"),
                           ("name", "ilike", "analytic"),
                           ("name", "ilike", "sale_timesheet"),
                           ("name", "ilike", "sale_project")]],
                         fields=["id", "name", "shortdesc", "state", "installed_version"],
                         order="name", limit=0)
    for m in d["module"]:
        print("  %-40s %-44s %-12s %s" % (m["name"], (m.get("shortdesc") or "")[:44],
                                          m["state"], m["installed_version"] or "-"))

    # 2) Modelle
    print("\n=== Modelle (project/analytic) ===")
    d["modelle"] = cli.kw("ir.model", "search_read",
                          [["|", ("model", "like", "project."), ("model", "like", "account.analytic")]],
                          fields=["id", "model", "name", "transient"], order="model", limit=0)
    for m in d["modelle"]:
        print("  %-40s %s%s" % (m["model"], m["name"], " (transient)" if m["transient"] else ""))

    # 3) Felder der Kernmodelle
    for modell in KERN_MODELLE:
        f = felder(cli, modell)
        d.setdefault("felder", {})[modell] = f
        print("\n=== Felder %s (%d) ===" % (modell, len(f)))
        for name in sorted(f):
            if name.startswith("__"):
                print("  FEHLER:", f[name])
                continue
            fd = f[name]
            teile = [fd.get("type") or "?"]
            if fd.get("required"):
                teile.append("PFLICHT")
            if fd.get("readonly"):
                teile.append("readonly")
            if fd.get("relation"):
                teile.append("->" + str(fd["relation"]))
            if fd.get("store") is False:
                teile.append("nicht gespeichert")
            if fd.get("translate"):
                teile.append("uebersetzbar")
            if fd.get("selection"):
                try:
                    teile.append("[" + " | ".join("%s=%s" % (s[0], s[1]) for s in fd["selection"][:14]) + "]")
                except Exception:  # noqa: BLE001
                    pass
            if fd.get("help"):
                teile.append("HILFE: " + str(fd["help"])[:60])
            print("  %-30s %-46s %s" % (name, (fd.get("string") or "")[:46], "; ".join(teile)))

    # 4) Menues
    print("\n=== Menuebaum (project/projekt/timesheet/aufgabe) ===")
    alle_menues = cli.kw("ir.ui.menu", "search_read", [[]],
                         fields=["id", "name", "complete_name", "parent_id", "sequence", "action",
                                 "groups_id", "active", "web_icon"],
                         order="id", limit=0)
    d["menues_alle"] = alle_menues
    schluessel = ("project", "projekt", "timesheet", "aufgabe", "stundenzettel", "zeiterfassung")
    menues = []
    for m in alle_menues:
        cn = (m["complete_name"] or "").lower()
        nm = (m["name"] or "").lower()
        rm = m["parent_id"][1].lower() if isinstance(m["parent_id"], list) else ""
        if cn.split("/")[0].strip() in schluessel or any(s in cn for s in schluessel) \
                or nm in schluessel or rm in schluessel:
            menues.append(m)
    d["menues"] = menues
    print("  Menues gesamt: %d, project-bezogen: %d" % (len(alle_menues), len(menues)))
    for m in menues:
        act = m["action"] or "-"
        print("  %-5s %-66s seq=%-5s aktiv=%-5s act=%s groups=%s" % (
            m["id"], (m["complete_name"] or "")[:66], m["sequence"], m["active"], act, m["groups_id"] or []))

    # 5) Fensteraktionen
    print("\n=== Fensteraktionen (project.*) ===")
    try:
        d["aktionen"] = cli.kw("ir.actions.act_window", "search_read",
                               [[("res_model", "like", "project.")]],
                               fields=["id", "name", "res_model", "view_mode", "domain", "context",
                                       "target", "limit", "search_view_id", "groups_id"], limit=0)
    except Exception as exc:  # noqa: BLE001
        d["aktionen"] = {"__fehler__": str(exc)[:200]}
    if isinstance(d["aktionen"], list):
        for x in d["aktionen"]:
            print("  %-5s %-22s %-30s %-30s dom=%s" % (
                x["id"], (x["name"] or "")[:22], x["res_model"], x["view_mode"],
                (x["domain"] or "")[:30]))

    # 6) Ansichten je Kernmodell
    for modell in KERN_MODELLE:
        print("\n=== Ansichten %s ===" % modell)
        try:
            vs = cli.kw("ir.ui.view", "search_read", [[("model", "=", modell)]],
                        fields=["id", "name", "type", "priority", "mode", "inherit_id", "active", "xml_id"],
                        order="type, priority, id", limit=0)
        except Exception as exc:  # noqa: BLE001
            print("  FEHLER:", str(exc)[:160])
            continue
        d.setdefault("ansichten", {})[modell] = vs
        for v in vs:
            inh = v["inherit_id"][1] if isinstance(v["inherit_id"], list) else "-"
            print("  %-10s prio=%-4s %-48s inh=%-38s aktiv=%s" % (
                v["type"], v["priority"], (v["name"] or "")[:48], inh[:38], v["active"]))

    # 7) Stammdaten / Bestand
    for modell, kandidaten in STAEM_QUELLEN.items():
        print("\n=== Stammdaten/Beispiel %s ===" % modell)
        f = d["felder"].get(modell) or felder(cli, modell)
        vorhanden = [x for x in kandidaten if x in f and not x.startswith("__")]
        try:
            n = cli.kw(modell, "search_count", [[]])
        except Exception as exc:  # noqa: BLE001
            n = "FEHLER %s" % str(exc)[:80]
        print("  Bestand: %s | gelesene Felder: %s" % (n, ",".join(vorhanden)))
        if modell == "project.task":
            d.setdefault("bestand", {})[modell] = n
            continue
        try:
            daten = cli.kw(modell, "search_read", [[]], fields=vorhanden,
                           order=("sequence, id" if "sequence" in vorhanden else "id"), limit=200)
        except Exception as exc:  # noqa: BLE001
            print("  FEHLER:", str(exc)[:160])
            continue
        d.setdefault("staemme", {})[modell] = daten
        for x in daten:
            rest = {k: v for k, v in x.items() if k != "id"}
            print("  %-4s %s" % (x["id"], json.dumps(rest, ensure_ascii=False)[:220]))

    # 8) Gruppen / Rechte / Rules
    print("\n=== Gruppen (project) ===")
    try:
        d["gruppen"] = cli.kw("res.groups", "search_read",
                              [["|", ("name", "ilike", "project"), ("name", "ilike", "projekt")]],
                              fields=["id", "name", "category_id", "users", "implied_ids"], limit=0)
        for g in d["gruppen"]:
            print("  %-4s %-44s %-24s Benutzer=%d" % (
                g["id"], (g["name"] or "")[:44],
                (g["category_id"][1] if isinstance(g["category_id"], list) else "-")[:24], len(g["users"])))
    except Exception as exc:  # noqa: BLE001
        print("  FEHLER:", str(exc)[:160])

    print("\n=== Zugriffsrechte (project.*) ===")
    try:
        d["zugriff"] = cli.kw("ir.model.access", "search_read",
                              [[("model_id.model", "like", "project.")]],
                              fields=["id", "name", "model_id", "group_id", "perm_read", "perm_write",
                                      "perm_create", "perm_unlink"], limit=0)
        for r in d["zugriff"]:
            print("  %-30s %-42s R=%s W=%s C=%s D=%s" % (
                (r["model_id"][1] if isinstance(r["model_id"], list) else "?")[:30],
                (r["group_id"][1] if isinstance(r["group_id"], list) else "keine")[:42],
                r["perm_read"], r["perm_write"], r["perm_create"], r["perm_unlink"]))
    except Exception as exc:  # noqa: BLE001
        print("  FEHLER:", str(exc)[:160])

    print("\n=== Record Rules (project) ===")
    try:
        d["rules"] = cli.kw("ir.rule", "search_read", [[("model_id.model", "like", "project.")]],
                            fields=["id", "name", "model_id", "domain_force", "groups", "active"], limit=0)
        for r in d["rules"]:
            print("  %-46s %-28s %-40s %s" % (
                (r["name"] or "")[:46],
                (r["model_id"][1] if isinstance(r["model_id"], list) else "?")[:28],
                (r["domain_force"] or "")[:40], r["groups"]))
    except Exception as exc:  # noqa: BLE001
        print("  FEHLER:", str(exc)[:160])

    # 9) Einstellungen
    print("\n=== Einstellungen (res.config.settings project) ===")
    try:
        f = cli.kw("res.config.settings", "fields_get", [], attributes=["string", "type"])
        treffer = {k: v for k, v in f.items() if "project" in k or "timesheet" in k}
        d["einstellungen"] = treffer
        for k, v in sorted(treffer.items()):
            print("  %-46s %-46s %s" % (k, v.get("string"), v.get("type")))
    except Exception as exc:  # noqa: BLE001
        print("  FEHLER:", str(exc)[:160])

    # 10) Mail-Vorlagen
    print("\n=== Mail-Vorlagen (project) ===")
    try:
        d["vorlagen"] = cli.kw("mail.template", "search_read",
                               [[("model", "like", "project.")]],
                               fields=["id", "name", "model", "subject", "auto_delete"], limit=0)
        for x in d["vorlagen"]:
            print("  %-4s %-50s %-22s %s" % (x["id"], (x["name"] or "")[:50], x["model"],
                                             (x["subject"] or "")[:36]))
    except Exception as exc:  # noqa: BLE001
        print("  FEHLER:", str(exc)[:160])

    # 11) Berichte
    print("\n=== Berichte (project) ===")
    try:
        d["berichte"] = cli.kw("ir.actions.report", "search_read",
                               [[("model", "like", "project.")]],
                               fields=["id", "name", "model", "report_name", "report_type"], limit=0)
        for x in d["berichte"]:
            print("  %-4s %-40s %-22s %s" % (x["id"], (x["name"] or "")[:40], x["model"],
                                             x["report_name"]))
    except Exception as exc:  # noqa: BLE001
        print("  FEHLER:", str(exc)[:160])

    # 12) Abhaengige Module (wer haengt von project ab)
    print("\n=== Abhaengigkeiten: Module mit project in depends ===")
    try:
        d["abhaengige"] = cli.kw("ir.module.module", "search_read",
                                 [[("state", "=", "installed")]],
                                 fields=["name", "shortdesc", "dependencies_id"], limit=0)
    except Exception as exc:  # noqa: BLE001
        d["abhaengige"] = {"__fehler__": str(exc)[:200]}

    pfad = os.path.join(a.ordner, "projekt_%s.json" % a.quelle)
    with open(pfad, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1, sort_keys=True, default=str)
    print("\nRohdaten:", pfad)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
