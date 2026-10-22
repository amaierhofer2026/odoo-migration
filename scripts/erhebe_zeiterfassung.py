"""Read-only Bestandsaufnahme Zeiterfassung: Odoo 11 gegen Odoo 18 (lokal/VM).

Aufruf:
  python scripts/erhebe_zeiterfassung.py --quelle o11  --teil 1
  python scripts/erhebe_zeiterfassung.py --quelle lokal --teil 2
  ...

Teile:
  1  Modelle, Felder (account.analytic.line, project.*, analytic), Feldattribute de_DE
  2  Menuebaum, Fensteraktionen, Ansichten je Typ (Arch de_DE), Buttons
  3  Suchansichten (Filter/Gruppierungen), gespeicherte Filter (ir.filters), Favoriten
  4  Rechte: Gruppen, ir.model.access, ir.rule, Record Rules
  5  Bestand und Verteilungen (Zeilen, Mitarbeiter inkl. archiviert, Projekte, Aufgaben,
     Monate, Betraege, Abrechnungsart, Verkaufsauftrag, Automatiken/Cron)
  6  Stammdaten-Abgleich: Projekte, Aufgaben, Mitarbeiter, Benutzer (O11 gegen O18)

Es werden ausschliesslich lesende RPC-Aufrufe gemacht; Rohdaten als JSON im Ordner --ordner.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

STD = os.path.join(os.environ.get("USERPROFILE", "."), "Desktop",
                   "Odoo18-Zeiterfassung-Session135", "rohdaten")

FELD_ATTR = ["string", "type", "required", "readonly", "relation", "selection", "store",
             "help", "size", "digits", "translate", "oldname", "compute", "related",
             "depends", "currency_field", "domain", "group_operator", "manual"]

KERN = ["account.analytic.line", "project.project", "project.task", "account.analytic.account"]


def sread(cli, modell, domain, **kw):
    """search_read mit korrekt gepackter Domain (args = [domain]) und de_DE-Kontext."""
    ctx = dict(kw.pop("context", None) or {})
    ctx.setdefault("lang", "de_DE")
    return cli.kw(modell, "search_read", [domain], context=ctx, **kw)


def arch_holen(cli, view_id, modell, typ, lang="de_DE"):
    """Arch einer Ansicht holen - O18 get_views, O11 fields_view_get als Rueckfall."""
    try:
        got = cli.kw(modell, "get_views", [[(view_id, typ)]], options={"toolbar": False},
                     context={"lang": lang})
        views = got.get("views", {})
        for vid, data in views.items():
            if "arch" in data:
                return data["arch"]
    except Exception:  # noqa: BLE001
        pass
    try:
        got = cli.kw(modell, "fields_view_get", [], view_id=view_id, view_type=typ,
                     context={"lang": lang})
        return got.get("arch", "")
    except Exception as exc:  # noqa: BLE001
        return "__FEHLER__ " + str(exc)[:150]


def felder(cli, modell):
    try:
        return cli.kw(modell, "fields_get", [], attributes=FELD_ATTR)
    except Exception as exc:  # noqa: BLE001
        return {"__fehler__": str(exc)[:300]}


def speichere(ordner, name, daten):
    os.makedirs(ordner, exist_ok=True)
    pfad = os.path.join(ordner, name)
    with open(pfad, "w", encoding="utf-8") as fh:
        json.dump(daten, fh, ensure_ascii=False, indent=1, default=str)
    print("  -> geschrieben:", pfad)


def teil1(cli, d):
    print("\n=== 1 Modelle ===")
    d["modelle"] = sread(cli, "ir.model",
                          ["|", "|", ("model", "like", "account.analytic"),
                           ("model", "like", "project."), ("model", "like", "hr.timesheet")],
                          fields=["id", "model", "name", "transient"], order="model", limit=0)
    for m in d["modelle"]:
        print("  %-40s %s" % (m["model"], m["name"]))
    print("\n=== 1 Felder ===")
    for modell in KERN:
        f = felder(cli, modell)
        d.setdefault("felder", {})[modell] = f
        print("\n--- %s (%d Felder) ---" % (modell, len(f)))
        for name in sorted(f):
            fd = f[name]
            if name.startswith("__"):
                print("  FEHLER:", fd)
                continue
            teile = [fd.get("type") or "?"]
            if fd.get("required"):
                teile.append("PFLICHT")
            if fd.get("readonly"):
                teile.append("readonly")
            if fd.get("relation"):
                teile.append("->" + str(fd["relation"]))
            if fd.get("store") is False:
                teile.append("nicht gespeichert")
            if fd.get("compute"):
                teile.append("compute=" + str(fd["compute"]))
            if fd.get("related"):
                teile.append("related=" + str(fd["related"]))
            if fd.get("oldname"):
                teile.append("oldname=" + str(fd["oldname"]))
            if fd.get("selection"):
                try:
                    teile.append("[" + " | ".join("%s=%s" % (s[0], s[1]) for s in fd["selection"][:12]) + "]")
                except Exception:  # noqa: BLE001
                    pass
            print("  %-28s %-40s %s" % (name, (fd.get("string") or "")[:40], "; ".join(teile)))


def teil2(cli, d):
    print("\n=== 2 Menuebaum ===")
    d["menues"] = sread(cli, "ir.ui.menu", [],
                        fields=["id", "name", "parent_id", "sequence", "action"],
                        order="parent_id,sequence,id", limit=0)
    by_id0 = {m["id"]: m for m in d["menues"]}

    def cname(m):
        teile = [m["name"]]
        p = m["parent_id"]
        while p:
            pm = by_id0.get(p[0])
            if not pm:
                break
            teile.insert(0, pm["name"])
            p = pm["parent_id"]
        return "/".join(teile)

    for m in d["menues"]:
        m["complete_name"] = cname(m)
    d["menue_kinder"] = {}
    for m in d["menues"]:
        pid = m["parent_id"][0] if m["parent_id"] else 0
        d["menue_kinder"].setdefault(pid, []).append(m["id"])
    by_id = {m["id"]: m for m in d["menues"]}

    def pfad(i, tiefe=0, out=None):
        out = out if out is not None else []
        m = by_id.get(i)
        if not m:
            return out
        out.append(("  " * tiefe) + "%s  [%s]  seq=%s  action=%s" % (
            m["name"], i, m["sequence"], m["action"] or "-"))
        for kid in sorted(d["menue_kinder"].get(i, []), key=lambda x: by_id[x]["sequence"]):
            pfad(kid, tiefe + 1, out)
        return out

    # Wurzeln: Projekt, Zeiterfassung und alles mit timesheet/analytic-Aktion
    wurzeln = [m for m in d["menues"] if not m["parent_id"]]
    for w in wurzeln:
        text = "\n".join(pfad(w["id"]))
        if any(k in text.lower() for k in ("projekt", "zeiterfassung", "timesheet", "aufgabe",
                                           "arbeitszeit", "stunden")):
            print("\n[Wurzel %s]" % w["name"])
            print(text)
            d.setdefault("menue_text", {})[w["name"]] = text

    print("\n=== 2 Fensteraktionen (timesheet/project/analytic) ===")
    d["aktionen"] = sread(cli, "ir.actions.act_window",
                           ["|", "|", ("res_model", "=", "account.analytic.line"),
                            ("res_model", "=", "project.project"), ("res_model", "=", "project.task")],
                           fields=["id", "name", "res_model", "view_mode", "domain", "context",
                                   "search_view_id", "help", "target"], order="res_model,name", limit=0)
    for a in d["aktionen"]:
        print("  [%s] %-30s %-22s %-16s dom=%s" % (a["id"], a["name"][:30], a["res_model"],
                                                   a["view_mode"], (a["domain"] or "")[:60]))

    print("\n=== 2 Ansichten ===")
    d["ansichten"] = sread(cli, "ir.ui.view",
                            [("model", "in", KERN)],
                            fields=["id", "name", "model", "type", "priority", "mode", "inherit_id",
                                    "active", "xml_id", "groups_id"], order="model,type,priority,id", limit=0)
    for v in sorted(d["ansichten"], key=lambda x: (x["model"], x["type"], x["priority"] or 0)):
        print("  %-22s %-6s prio=%-4s %-5s %-45s xml=%s" % (
            v["model"], v["type"], v["priority"], "prim" if v["mode"] == "primary" else "inh",
            (v["name"] or "")[:45], v["xml_id"] or "-"))

    print("\n=== 2 Arch je Ansicht (de_DE) ===")
    d["arches"] = {}
    for v in d["ansichten"]:
        d["arches"][v["id"]] = arch_holen(cli, v["id"], v["model"], v["type"])


def teil3(cli, d):
    print("\n=== 3 Suchansichten ===")
    d["suchansichten"] = [v for v in sread(cli, "ir.ui.view",
                                            [("model", "in", KERN), ("type", "=", "search")],
                                            fields=["id", "name", "model", "xml_id"],
                                            order="model,id", limit=0)]
    for v in d["suchansichten"]:
        print("  %-22s %s (%s)" % (v["model"], v["name"], v["xml_id"] or "-"))
    d["such_arch"] = {}
    for v in d["suchansichten"]:
        d["such_arch"][v["id"]] = arch_holen(cli, v["id"], v["model"], "search")
        if d["such_arch"][v["id"]].startswith("__FEHLER__"):
            print("    FEHLER", v["id"], d["such_arch"][v["id"]][:140])

    print("\n=== 3 gespeicherte Filter (ir.filters) ===")
    try:
        d["filters"] = sread(cli, "ir.filters",
                              [("model_id", "in", ["account.analytic.line", "project.task",
                                                   "project.project"])],
                              fields=["id", "name", "model_id", "domain", "context", "user_id",
                                      "is_default"], order="model_id,name", limit=0)
    except Exception as exc:  # noqa: BLE001
        d["filters"] = {"__fehler__": str(exc)[:200]}
        print("  FEHLER:", str(exc)[:200])
    for f in (d["filters"] if isinstance(d["filters"], list) else []):
        print("  [%s] %-22s %-22s default=%s dom=%s ctx=%s" % (
            f["id"], f["name"], f["model_id"], f["is_default"],
            str(f["domain"])[:70], str(f.get("context"))[:70]))


def teil4(cli, d):
    print("\n=== 4 Gruppen ===")
    d["gruppen"] = sread(cli, "res.groups",
                          ["|", "|", ("name", "ilike", "Zeiterfassung"),
                           ("name", "ilike", "timesheet"), ("name", "ilike", "Projekt")],
                          fields=["id", "name", "category_id"], order="id", limit=0)
    for g in d["gruppen"]:
        print("  [%s] %-45s %s" % (g["id"], g["name"], g["category_id"] or "-"))
    print("\n=== 4 alle Gruppen (Kategorie Projekt/Zeiterfassung) ===")
    d["gruppen_alle"] = cli.kw("res.groups", "search_read", [[]],
                               fields=["id", "name", "category_id"], order="category_id,id", limit=0)
    try:
        d["gruppen_xmlids"] = cli.kw("ir.model.data", "search_read",
                                     [("model", "=", "res.groups")],
                                     fields=["name", "res_id", "module"], limit=0)
    except Exception as exc:  # noqa: BLE001
        d["gruppen_xmlids"] = []
        print("  xmlid-Abfrage:", str(exc)[:120])
    xmap = {}
    for x in d.get("gruppen_xmlids", []):
        xmap.setdefault(x["res_id"], []).append("%s.%s" % (x["module"], x["name"]))
    for g in d["gruppen_alle"]:
        print("  [%s] %-24s %-42s %s" % (g["id"], str(g["category_id"])[:24], g["name"],
                                         ",".join(xmap.get(g["id"], [])) or "-"))

    print("\n=== 4 ir.model.access (account.analytic.line / project.*) ===")
    d["access"] = sread(cli, "ir.model.access",
                         [("model_id.model", "in", ["account.analytic.line", "project.project",
                                                    "project.task", "account.analytic.account"])],
                         fields=["id", "name", "model_id", "group_id", "perm_read", "perm_write",
                                 "perm_create", "perm_unlink"], order="model_id,name", limit=0)
    for a in d["access"]:
        print("  %-22s %-42s grp=%-28s R%sW%sC%sD%s" % (
            a["model_id"][1] if a["model_id"] else "-", a["name"][:42],
            (a["group_id"][1][:28] if a["group_id"] else "-"),
            int(a["perm_read"]), int(a["perm_write"]), int(a["perm_create"]), int(a["perm_unlink"])))

    print("\n=== 4 ir.rule ===")
    try:
        d["rules"] = sread(cli, "ir.rule",
                            [("model_id.model", "in", ["account.analytic.line", "project.project",
                                                       "project.task"])],
                            fields=["id", "name", "model_id", "groups", "domain_force", "perm_read",
                                    "perm_write", "perm_create", "perm_unlink"], order="model_id,id", limit=0)
    except Exception as exc:  # noqa: BLE001
        d["rules"] = {"__fehler__": str(exc)[:200]}
    for r in (d["rules"] if isinstance(d["rules"], list) else []):
        print("  [%s] %-22s %-40s R%sW%sC%sD%s\n       %s" % (
            r["id"], r["model_id"][1], r["name"][:40], int(r["perm_read"]), int(r["perm_write"]),
            int(r["perm_create"]), int(r["perm_unlink"]), str(r["domain_force"])[:160]))


def teil5(cli, d):
    md = "account.analytic.line"
    print("\n=== 5 Bestand ===")
    d["anzahl"] = cli.kw(md, "search_count", [[]])
    print("  Zeilen:", d["anzahl"])
    d["verteilung"] = {}
    for feld in ["employee_id", "user_id", "project_id", "task_id", "account_id",
                 "timesheet_invoice_type", "so_line", "company_id", "holiday_id"]:
        try:
            zeilen = cli.kw(md, "search_read", [[]], fields=[feld], limit=0)
        except Exception as exc:  # noqa: BLE001
            print("  %-24s FEHLER %s" % (feld, str(exc)[:80]))
            continue
        zähler = {}
        for z in zeilen:
            wert = z.get(feld)
            name = wert[1] if isinstance(wert, (list, tuple)) else wert
            key = "%s|%s" % (wert[0] if isinstance(wert, (list, tuple)) else "", name)
            zähler[key] = zähler.get(key, 0) + 1
        d["verteilung"][feld] = dict(sorted(zähler.items(), key=lambda kv: -kv[1]))
        print("  %-24s %d verschiedene Werte" % (feld, len(zähler)))
        for k, v in list(d["verteilung"][feld].items())[:12]:
            print("     %-60s %s" % (k[:60], v))

    print("\n=== 5 Summen/Monate ===")
    zeilen = cli.kw(md, "search_read", [[]], fields=["date", "unit_amount", "amount"], limit=0)
    d["summe_stunden"] = round(sum((z.get("unit_amount") or 0) for z in zeilen), 2)
    d["summe_betrag"] = round(sum((z.get("amount") or 0) for z in zeilen), 2)
    pro_monat, pro_jahr = {}, {}
    for z in zeilen:
        if not z.get("date"):
            continue
        mon, jahr = str(z["date"])[:7], str(z["date"])[:4]
        pro_monat[mon] = round(pro_monat.get(mon, 0) + (z.get("unit_amount") or 0), 2)
        pro_jahr[jahr] = round(pro_jahr.get(jahr, 0) + (z.get("unit_amount") or 0), 2)
    d["monate"] = dict(sorted(pro_monat.items()))
    d["jahre"] = dict(sorted(pro_jahr.items()))
    print("  Summe Stunden:", d["summe_stunden"], " Summe Betrag:", d["summe_betrag"])
    print("  Jahre:", d["jahre"])
    print("  Monate (erste/letzte):", list(d["monate"].items())[:3], list(d["monate"].items())[-3:])

    print("\n=== 5 leere Pflichtangaben / Auffaelligkeiten ===")
    for dom, bez in [([("task_id", "=", False)], "ohne Aufgabe"),
                     ([("project_id", "=", False)], "ohne Projekt"),
                     ([("employee_id", "=", False)], "ohne Mitarbeiter"),
                     ([("unit_amount", "=", 0)], "Dauer 0"),
                     ([("unit_amount", "<", 0)], "Dauer negativ"),
                     ([("name", "=", False)], "ohne Beschreibung")]:
        try:
            print("  %-22s %s" % (bez, cli.kw(md, "search_count", [dom])))
        except Exception as exc:  # noqa: BLE001
            print("  %-22s FEHLER %s" % (bez, str(exc)[:80]))

    print("\n=== 5 Automatiken / Cron ===")
    try:
        d["crons"] = sread(cli, "ir.cron",
                            ["|", "|", ("name", "ilike", "timesheet"), ("name", "ilike", "Zeit"),
                             ("name", "ilike", "analytic")],
                            fields=["id", "name", "model_id", "state", "interval_number",
                                    "interval_type", "active"], limit=0)
    except Exception as exc:  # noqa: BLE001
        d["crons"] = {"__fehler__": str(exc)[:200]}
    for c in (d["crons"] if isinstance(d["crons"], list) else []):
        print("  [%s] %-45s %s %s/%s active=%s" % (c["id"], c["name"], c["state"],
                                                   c["interval_number"], c["interval_type"], c["active"]))
    try:
        d["automation"] = sread(cli, "base.automation",
                                 [("model_id.model", "in", ["account.analytic.line", "project.task",
                                                            "project.project"])],
                                 fields=["id", "name", "model_id", "state", "trigger"], limit=0)
        for a in d["automation"]:
            print("  AUTO [%s] %-40s %s %s" % (a["id"], a["name"], a["model_id"][1], a["trigger"]))
    except Exception as exc:  # noqa: BLE001
        print("  base.automation:", str(exc)[:120])

    print("\n=== 5 Server Actions ===")
    try:
        d["server_actions"] = sread(cli, "ir.actions.server",
                                     [("model_id.model", "in", ["account.analytic.line", "project.task",
                                                                "project.project"])],
                                     fields=["id", "name", "model_id", "state", "code", "xml_id"], limit=0)
        for s in d["server_actions"]:
            print("  [%s] %-40s %s" % (s["id"], s["name"], s["model_id"][1] if s["model_id"] else "-"))
    except Exception as exc:  # noqa: BLE001
        print("  ir.actions.server:", str(exc)[:120])


def teil6(cli, d):
    print("\n=== 6 Mitarbeiter (inkl. archiviert) ===")
    ef = felder(cli, "hr.employee")
    felder_e = [f for f in ["id", "name", "user_id", "active", "department_id", "job_id",
                            "company_id", "has_timesheet", "parent_id", "work_email"]
                if f in ef]
    d["mitarbeiter"] = cli.kw("hr.employee", "search_read", [[]], fields=felder_e,
                              context={"active_test": False}, order="name", limit=0)
    print("  Anzahl (inkl. archiviert):", len(d["mitarbeiter"]),
          " aktiv:", sum(1 for m in d["mitarbeiter"] if m["active"]))
    for m in d["mitarbeiter"]:
        print("  [%s] %-32s user=%-28s aktiv=%s" % (
            m["id"], (m["name"] or "")[:32],
            (m["user_id"][1][:28] if m["user_id"] else "-"), m["active"]))

    print("\n=== 6 Benutzer (inkl. inaktiv) ===")
    d["benutzer"] = cli.kw("res.users", "search_read", [[]],
                           fields=["id", "login", "name", "active", "employee_ids"],
                           context={"active_test": False}, order="login", limit=0)
    print("  Anzahl:", len(d["benutzer"]))
    for b in d["benutzer"]:
        print("  [%s] %-28s %-30s aktiv=%s emp=%s" % (b["id"], b["login"][:28], (b["name"] or "")[:30],
                                                      b["active"], b.get("employee_ids")))

    print("\n=== 6 Projekte ===")
    pf = felder(cli, "project.project")
    kandidaten = ["id", "name", "partner_id", "user_id", "privacy_visibility",
                  "analytic_account_id", "account_id", "active", "date_start", "date",
                  "allow_timesheets", "is_favorite", "label_tasks", "stage_id"]
    felder_liste = [f for f in kandidaten if f in pf]
    d["projekte"] = cli.kw("project.project", "search_read", [[]], fields=felder_liste,
                           context={"active_test": False}, order="id", limit=0)
    for p in d["projekte"]:
        print("  [%s] %-52s kunde=%-26s aktiv=%s" % (p["id"], (p["name"] or "")[:52],
                                                     (p["partner_id"][1][:26] if p["partner_id"] else "-"),
                                                     p["active"]))

    print("\n=== 6 Aufgaben ===")
    tf = felder(cli, "project.task")
    kandidaten_t = ["id", "name", "project_id", "user_id", "user_ids", "stage_id", "active",
                    "planned_hours", "allocated_hours", "effective_hours", "date_start",
                    "itk_date_start", "date_deadline", "kanban_state", "priority",
                    "parent_id", "description", "tag_ids"]
    felder_t = [f for f in kandidaten_t if f in tf]
    d["aufgaben"] = cli.kw("project.task", "search_read", [[]], fields=felder_t,
                           context={"active_test": False}, order="project_id,id", limit=0)
    print("  Anzahl (inkl. archiviert):", len(d["aufgaben"]),
          " aktiv:", sum(1 for t in d["aufgaben"] if t["active"]))
    pro_projekt = {}
    for t in d["aufgaben"]:
        key = t["project_id"][1] if t["project_id"] else "(ohne Projekt)"
        pro_projekt[key] = pro_projekt.get(key, 0) + 1
    d["aufgaben_pro_projekt"] = dict(sorted(pro_projekt.items(), key=lambda kv: -kv[1]))
    for k, v in d["aufgaben_pro_projekt"].items():
        print("  %-52s %s" % (k[:52], v))


def teil7(cli, d):
    """Deutsche Bezeichnungen (de_DE) der Felder, Menues und Aktionen."""
    print("\n=== 7 Feldbezeichnungen de_DE ===")
    d["labels"] = {}
    for modell in KERN + ["hr.employee", "res.users"]:
        try:
            de = cli.kw(modell, "fields_get", [], attributes=["string", "type"],
                        context={"lang": "de_DE"})
            en = cli.kw(modell, "fields_get", [], attributes=["string", "type"],
                        context={"lang": "en_US"})
        except Exception as exc:  # noqa: BLE001
            print("  %-24s FEHLER %s" % (modell, str(exc)[:100]))
            continue
        d["labels"][modell] = {k: {"de": v.get("string"), "en": en.get(k, {}).get("string"),
                                   "typ": v.get("type")} for k, v in de.items()}
        fehlend = [k for k, v in de.items() if v.get("string") == en.get(k, {}).get("string")
                   and not k.startswith("__")]
        print("  %-24s Felder=%d  ohne de_DE-Slot=%d" % (modell, len(de), len(fehlend)))
        for k in sorted(fehlend)[:40]:
            print("       ohne de: %-30s (%s)" % (k, de[k].get("string")))

    print("\n=== 7 Menue- und Aktionsnamen de_DE ===")
    d["menue_labels"] = sread(cli, "ir.ui.menu", [], fields=["id", "name", "complete_name"],
                              order="id", limit=0)
    for m in d["menue_labels"]:
        if any(k in (m["complete_name"] or "").lower() for k in
               ("zeiterfassung", "timesheet", "projekt", "aufgabe")):
            print("  [%s] %s" % (m["id"], m["complete_name"]))

    d["aktions_labels"] = sread(cli, "ir.actions.act_window", [], fields=["id", "name", "res_model"],
                                order="id", limit=0)
    for a in d["aktions_labels"]:
        if any(k in (a["name"] or "").lower() for k in
               ("zeit", "stunde", "timesheet", "projekt", "aufgabe", "task", "project")):
            print("  AKT [%s] %-50s %s" % (a["id"], (a["name"] or "")[:50], a["res_model"]))

    print("\n=== 7 Auswahlwerte de_DE (account.analytic.line) ===")
    try:
        f = cli.kw("account.analytic.line", "fields_get", ["timesheet_invoice_type"],
                   attributes=["selection"], context={"lang": "de_DE"})
        print("  timesheet_invoice_type:", f["timesheet_invoice_type"]["selection"])
        d["auswahl"] = f
    except Exception as exc:  # noqa: BLE001
        print("  FEHLER", str(exc)[:120])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quelle", required=True, choices=["o11", "lokal", "vm"])
    ap.add_argument("--teil", required=True, choices=["1", "2", "3", "4", "5", "6", "7"])
    ap.add_argument("--ordner", default=STD)
    a = ap.parse_args()
    cli = o11() if a.quelle == "o11" else o18(a.quelle)
    print("### Quelle:", a.quelle, " Teil:", a.teil)
    d = {"quelle": a.quelle, "teil": a.teil}
    {"1": teil1, "2": teil2, "3": teil3, "4": teil4, "5": teil5, "6": teil6,
     "7": teil7}[a.teil](cli, d)
    speichere(a.ordner, "zeiterfassung_%s_teil%s.json" % (a.quelle, a.teil), d)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
