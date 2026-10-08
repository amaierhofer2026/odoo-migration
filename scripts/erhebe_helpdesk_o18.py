"""Read-only Erhebung des Helpdesk-Bereichs in Odoo 18 (lokal und VM).

Aufruf: python scripts/erhebe_helpdesk_o18.py --instanz lokal|vm [--ordner PFAD]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o18

STD = os.path.join(os.environ.get("USERPROFILE", "."), "Desktop",
                   "Odoo18-Helpdesk-Session132", "rohdaten")
FELD_ATTR = ["string", "type", "required", "readonly", "relation", "selection", "store",
             "help", "states", "size", "digits"]

MODELLE = [
    "helpdesk.ticket", "helpdesk.ticket.stage", "helpdesk.ticket.team",
    "helpdesk.ticket.category", "helpdesk.ticket.channel", "helpdesk.ticket.tag",
    "helpdesk.sla", "helpdesk.sla.report", "itk.helpdesk.priority",
    "itk.helpdesk.subcategory.field", "itk.helpdesk.subcategory.field.value",
    "helpdesk.ticket.team.user", "helpdesk.ticket.team.user",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", default="lokal")
    ap.add_argument("--ordner", default=STD)
    a = ap.parse_args()
    os.makedirs(a.ordner, exist_ok=True)
    cli = o18(a.instanz)
    d = {"instanz": a.instanz}

    print("### Instanz:", a.instanz)

    print("\n=== Helpdesk-Module (installiert) ===")
    d["module"] = cli.kw("ir.module.module", "search_read",
                         [["|", "|", ("name", "ilike", "helpdesk"), ("name", "ilike", "itk_helpdesk"),
                           ("name", "ilike", "website_support")]],
                         fields=["id", "name", "shortdesc", "state", "installed_version"],
                         order="name", limit=0)
    for m in d["module"]:
        print("  %-32s %-42s %-10s %s" % (m["name"], (m.get("shortdesc") or "")[:42],
                                          m["state"], m["installed_version"] or "-"))

    print("\n=== Modelle ===")
    vorhandene = []
    for modell in sorted(set(MODELLE)):
        f = cli.kw("ir.model", "search_read", [[("model", "=", modell)]],
                   fields=["model", "name"], limit=1)
        if f:
            vorhandene.append(modell)
            try:
                n = cli.kw(modell, "search_count", [[]])
            except Exception as exc:  # noqa: BLE001
                n = "FEHLER %s" % str(exc)[:80]
            print("  %-38s %-34s Bestand=%s" % (modell, f[0]["name"], n))
            d.setdefault("bestand", {})[modell] = n
        else:
            print("  %-38s FEHLT" % modell)

    print("\n=== Felder helpdesk.ticket ===")
    d["felder"] = cli.kw("helpdesk.ticket", "fields_get", [], attributes=FELD_ATTR)
    for name in sorted(d["felder"]):
        fd = d["felder"][name]
        teile = [fd.get("type") or "?"]
        if fd.get("required"):
            teile.append("PFLICHT")
        if fd.get("readonly"):
            teile.append("readonly")
        if fd.get("relation"):
            teile.append("->" + str(fd["relation"]))
        if fd.get("selection"):
            try:
                teile.append("[" + ", ".join("%s=%s" % (s[0], s[1]) for s in fd["selection"][:12]) + "]")
            except Exception:  # noqa: BLE001
                pass
        print("  %-32s %-44s %s" % (name, (fd.get("string") or "")[:44], "; ".join(teile)))

    print("\n=== Menuebaum Helpdesk ===")
    alle_menues = cli.kw("ir.ui.menu", "search_read", [[]],
                         fields=["id", "name", "complete_name", "parent_id", "sequence", "action",
                                 "groups_id", "active"], order="id", limit=0)
    menues = [m for m in alle_menues
              if (m["complete_name"] or "").lower().startswith("helpdesk")
              or (m["name"] or "").lower() in ("helpdesk", "support-tickets", "support tickets")]
    d["menues"] = menues
    d["menues_alle"] = alle_menues
    for m in menues:
        print("  %-70s seq=%-5s aktiv=%-5s action=%s groups=%s" % (
            (m["complete_name"] or "")[:70], m["sequence"], m["active"], m["action"] or "-",
            m["groups_id"] or []))

    print("\n=== Fensteraktionen ===")
    d["aktionen"] = cli.kw("ir.actions.act_window", "search_read",
                           [[("res_model", "in", ["helpdesk.ticket", "helpdesk.ticket.stage",
                                                  "helpdesk.ticket.team", "helpdesk.ticket.category",
                                                  "helpdesk.ticket.channel", "helpdesk.ticket.tag",
                                                  "helpdesk.sla", "itk.helpdesk.priority",
                                                  "itk.helpdesk.subcategory.field"])]],
                           fields=["id", "name", "res_model", "view_mode", "domain", "context",
                                   "target", "search_view_id", "limit"], limit=0)
    for x in d["aktionen"]:
        print("  %-40s %-34s %-22s ctx=%s" % (x["res_model"], (x["name"] or "")[:34],
                                              x["view_mode"], (x["context"] or "")[:60]))

    print("\n=== Ansichten helpdesk.ticket ===")
    d["ansichten"] = cli.kw("ir.ui.view", "search_read",
                            [[("model", "=", "helpdesk.ticket")]],
                            fields=["id", "name", "type", "priority", "mode", "inherit_id",
                                    "active", "xml_id"], order="type, priority", limit=0)
    for v in d["ansichten"]:
        print("  %-10s prio=%-4s %-46s inherit=%-40s aktiv=%s" % (
            v["type"], v["priority"], (v["name"] or "")[:46],
            (v["inherit_id"][1] if isinstance(v["inherit_id"], list) else "-")[:40], v["active"]))

    print("\n=== Staemme ===")
    for modell, felder in (("helpdesk.ticket.stage", ["id", "name", "sequence", "fold", "closed",
                                                      "unattended", "active"]),
                           ("helpdesk.ticket.team", ["id", "name", "active"]),
                           ("helpdesk.ticket.category", ["id", "name", "parent_id", "active"]),
                           ("helpdesk.ticket.channel", ["id", "name", "active"]),
                           ("helpdesk.ticket.tag", ["id", "name", "active"]),
                           ("itk.helpdesk.priority", ["id", "name", "sequence", "color", "active"]),
                           ("helpdesk.sla", ["id", "name", "active"])):
        try:
            daten = cli.kw(modell, "search_read", [[]], fields=felder,
                           order="sequence, id" if "sequence" in felder else "id", limit=0)
        except Exception as exc:  # noqa: BLE001
            print("  %s: FEHLER %s" % (modell, str(exc)[:120]))
            continue
        d.setdefault("staemme", {})[modell] = daten
        print("  -- %s (%d)" % (modell, len(daten)))
        for x in daten:
            rest = {k: v for k, v in x.items() if k not in ("id", "name")}
            print("     %-40s %s" % ((x.get("name") or "")[:40], rest))

    print("\n=== Gruppen ===")
    d["gruppen"] = cli.kw("res.groups", "search_read",
                          [[("name", "ilike", "helpdesk")]],
                          fields=["id", "name", "category_id", "users", "implied_ids"], limit=0)
    for g in d["gruppen"]:
        print("  %-4s %-46s %-24s Benutzer=%d" % (
            g["id"], (g["name"] or "")[:46],
            (g["category_id"][1] if isinstance(g["category_id"], list) else "-")[:24],
            len(g["users"])))

    print("\n=== Zugriffsrechte ===")
    d["zugriff"] = cli.kw("ir.model.access", "search_read",
                          [[("model_id.model", "in", ["helpdesk.ticket", "helpdesk.ticket.stage",
                                                      "helpdesk.ticket.team", "helpdesk.ticket.category",
                                                      "helpdesk.ticket.channel", "helpdesk.ticket.tag",
                                                      "itk.helpdesk.priority"])]],
                          fields=["id", "name", "model_id", "group_id", "perm_read", "perm_write",
                                  "perm_create", "perm_unlink"], limit=0)
    for r in d["zugriff"]:
        print("  %-30s %-44s R=%s W=%s C=%s D=%s" % (
            (r["model_id"][1] if isinstance(r["model_id"], list) else "?")[:30],
            (r["group_id"][1] if isinstance(r["group_id"], list) else "keine")[:44],
            r["perm_read"], r["perm_write"], r["perm_create"], r["perm_unlink"]))

    print("\n=== Record Rules ===")
    d["rules"] = cli.kw("ir.rule", "search_read", [[("model_id.model", "ilike", "helpdesk")]],
                        fields=["id", "name", "model_id", "domain_force", "groups", "active"],
                        limit=0)
    for r in d["rules"]:
        print("  %-44s %-26s %-34s %s" % ((r["name"] or "")[:44],
                                          (r["model_id"][1] if isinstance(r["model_id"], list) else "?")[:26],
                                          (r["domain_force"] or "")[:34],
                                          [g for g in (r["groups"] or [])]))

    print("\n=== Mail-Aliase (helpdesk) ===")
    try:
        d["aliase"] = cli.kw("mail.alias", "search_read",
                             [[("alias_model_id.model", "=", "helpdesk.ticket")]],
                             fields=["id", "alias_name", "alias_team_id", "alias_user_id",
                                     "alias_defaults", "alias_contact"], limit=0)
        for x in d["aliase"]:
            print("  ", x)
    except Exception as exc:  # noqa: BLE001
        print("  FEHLER:", str(exc)[:160])

    print("\n=== Mail-Vorlagen (helpdesk.ticket) ===")
    d["vorlagen"] = cli.kw("mail.template", "search_read",
                           [[("model", "=", "helpdesk.ticket")]],
                           fields=["id", "name", "subject", "auto_delete", "lang"], limit=0)
    for x in d["vorlagen"]:
        print("  %-4s %-50s %s" % (x["id"], (x["name"] or "")[:50], (x["subject"] or "")[:40]))

    print("\n=== Einstellungen (res.config.settings helpdesk) ===")
    try:
        f = cli.kw("res.config.settings", "fields_get", [],
                   attributes=["string", "type"])
        hilf = {k: v for k, v in f.items() if "helpdesk" in k or k.startswith("group_helpdesk")}
        d["helpdesk_einstellungen"] = hilf
        for k, v in sorted(hilf.items()):
            print("  %-44s %-40s %s" % (k, v.get("string"), v.get("type")))
    except Exception as exc:  # noqa: BLE001
        print("  FEHLER:", str(exc)[:160])

    pfad = os.path.join(a.ordner, "helpdesk_o18_%s.json" % a.instanz)
    with open(pfad, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1, sort_keys=True)
    print("\nRohdaten:", pfad)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
