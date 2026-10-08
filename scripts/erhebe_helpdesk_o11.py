"""Vollstaendige read-only Erhebung des Helpdesk-Bereichs in Odoo 11 Prod.

Odoo 11 Helpdesk = OCA `website_support` (+ analytic_timesheets, + billing).
Erhebt Modelle, Felder, Menues, Aktionen, Ansichten, Rechte, Vorlagen, Sequenzen,
Cron, Alias, Bestand und Verteilung. Schreibt Rohdaten nach --ordner, aendert nichts.

Aufruf: python scripts/erhebe_helpdesk_o11.py [--ordner PFAD]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11

STD_ORDNER = os.path.join(os.environ.get("USERPROFILE", "."), "Desktop",
                          "Odoo18-Helpdesk-Session132", "rohdaten")
MODULE = ["website_support", "website_support_analytic_timesheets", "website_support_billing"]
FELD_ATTR = ["string", "type", "required", "readonly", "relation", "selection", "store",
             "help", "states", "size", "digits", "related", "digest", "oldname"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ordner", default=STD_ORDNER)
    a = ap.parse_args()
    os.makedirs(a.ordner, exist_ok=True)

    cli = o11()
    d = {}

    # --- Module
    d["module"] = cli.kw("ir.module.module", "search_read", [[("name", "in", MODULE)]],
                         fields=["id", "name", "shortdesc", "state", "installed_version",
                                 "author", "summary", "application"], order="name", limit=0)

    # --- Modelle (namenbasiert, damit auch geerbte Felder auffallen)
    d["modelle"] = cli.kw("ir.model", "search_read", [[("model", "like", "website.support%")]],
                          fields=["model", "name", "modules", "transient", "info"],
                          order="model", limit=0)
    modellnamen = [m["model"] for m in d["modelle"]]

    # --- Felder
    d["felder"] = {}
    for modell in modellnamen:
        try:
            d["felder"][modell] = cli.kw(modell, "fields_get", [], attributes=FELD_ATTR)
        except Exception as exc:  # noqa: BLE001
            d["felder"][modell] = {"__fehler__": str(exc)[:200]}
    print("Felder: %d Modelle" % len(d["felder"]))

    # --- Datensaetze der Module (Inventar), Menues, Aktionen, Ansichten
    for modul in MODULE:
        daten = cli.kw("ir.model.data", "search_read", [[("module", "=", modul)]],
                       fields=["model", "res_id", "name", "noupdate"], limit=0)
        d.setdefault("datensaetze", {})[modul] = daten

    menues = cli.kw("ir.ui.menu", "search_read",
                    [["|", "|", ("name", "ilike", "Support"), ("name", "ilike", "Ticket"),
                      ("name", "ilike", "Help")]],
                    fields=["id", "name", "complete_name", "parent_id", "sequence", "action",
                            "groups_id", "web_icon", "child_id"], order="complete_name", limit=0)
    d["menues_filter"] = menues
    d["menues_alle"] = cli.kw("ir.ui.menu", "search_read", [[]],
                              fields=["id", "name", "complete_name", "parent_id", "sequence",
                                      "action", "groups_id"], order="complete_name", limit=0)

    d["aktionen"] = cli.kw("ir.actions.act_window", "search_read",
                           [[("res_model", "in", modellnamen)]],
                           fields=["id", "name", "res_model", "view_mode", "domain", "context",
                                   "target", "search_view_id", "help", "limit", "usage"],
                           order="res_model, name", limit=0)

    d["ansichten"] = cli.kw("ir.ui.view", "search_read", [[("model", "in", modellnamen)]],
                            fields=["id", "name", "model", "type", "priority", "mode",
                                    "inherit_id", "active", "arch_db"],
                            order="model, type, priority", limit=0)
    print("Ansichten: %d" % len(d["ansichten"]))

    d["zugriff"] = cli.kw("ir.model.access", "search_read",
                          [[("model_id.model", "in", modellnamen)]],
                          fields=["id", "name", "model_id", "group_id", "perm_read", "perm_write",
                                  "perm_create", "perm_unlink"], limit=0)
    d["record_rules"] = cli.kw("ir.rule", "search_read",
                               [[("model_id.model", "in", modellnamen)]],
                               fields=["id", "name", "model_id", "domain_force", "groups",
                                       "perm_read", "perm_write", "perm_create", "perm_unlink",
                                       "active"], limit=0)

    d["gruppen"] = cli.kw("res.groups", "search_read",
                          [["|", "|", ("name", "ilike", "Support"), ("name", "ilike", "Ticket"),
                            ("name", "ilike", "Help")]],
                          fields=["id", "name", "category_id", "users", "implied_ids"], limit=0)
    d["gruppe_alle_support"] = cli.kw("res.groups", "search_read",
                                      [[("category_id.name", "ilike", "Support")]],
                                      fields=["id", "name", "category_id", "users",
                                              "implied_ids"], limit=0)

    # Zusaetzlich: alles, was die Module per Kennung anlegen (auch Fremdmodelle)
    kennungen = {"ir.ui.view": ("ir.ui.view", ["id", "name", "model", "type", "priority", "mode",
                                               "inherit_id", "active"]),
                 "ir.ui.menu": ("ir.ui.menu", ["id", "name", "complete_name", "parent_id",
                                               "sequence", "action", "groups_id"]),
                 "ir.actions.act_window": ("ir.actions.act_window",
                                           ["id", "name", "res_model", "view_mode", "domain",
                                            "context", "target", "search_view_id", "limit"]),
                 "res.groups": ("res.groups", ["id", "name", "category_id", "users", "implied_ids"]),
                 "ir.rule": ("ir.rule", ["id", "name", "model_id", "domain_force", "groups",
                                         "active"]),
                 "mail.template": ("mail.template", ["id", "name", "model_id", "subject",
                                                     "email_from", "email_to", "auto_delete",
                                                     "lang"]),
                 "ir.sequence": ("ir.sequence", ["id", "name", "code", "prefix", "padding",
                                                 "number_next_actual", "implementation"]),
                 "ir.cron": ("ir.cron", ["id", "name", "model", "state", "interval_number",
                                         "interval_type", "numbercall", "active", "nextcall"]),
                 "ir.actions.server": ("ir.actions.server", ["id", "name", "model_id", "state",
                                                             "usage", "code", "sequence"]),
                 "website.menu": ("website.menu", ["id", "name", "url", "parent_id", "sequence"]),
                 "website.support.ticket.states": ("website.support.ticket.states",
                                                   ["id", "name", "sequence"]),
                 }
    resolved = {}
    for modul, eintraege in d.get("datensaetze", {}).items():
        for e in eintraege:
            if e["model"] not in kennungen:
                continue
            resolved.setdefault(modul, {}).setdefault(e["model"], []).append(e["name"])
    for modul, je_modell in resolved.items():
        for modell, namen in je_modell.items():
            d.setdefault("kennungen", {}).setdefault(modul, {})[modell] = sorted(set(namen))

    for schluessel, (model, dom, felder) in {
        "mail_aliase": ("mail.alias", [], ["id", "alias_name", "alias_model_id", "alias_user_id",
                                           "alias_defaults", "alias_contact"]),
        "mail_vorlagen": ("mail.template", [("model_id.model", "in", modellnamen)],
                          ["id", "name", "model_id", "subject", "email_from", "email_to",
                           "auto_delete", "lang", "use_default_to"]),
        "sequenzen": ("ir.sequence", [("code", "ilike", "support")],
                      ["id", "name", "code", "prefix", "padding", "number_next_actual",
                       "implementation", "company_id"]),
        "cron": ("ir.cron", [("name", "ilike", "support")],
                 ["id", "name", "model", "state", "interval_number", "interval_type",
                  "numbercall", "active", "nextcall"]),
        "server_actions": ("ir.actions.server", [("model_id.model", "in", modellnamen)],
                           ["id", "name", "model_id", "state", "usage", "code", "sequence"]),
        "config_parameter": ("ir.config_parameter",
                             ["|", "|", ("key", "ilike", "support"), ("key", "ilike", "ticket"),
                              ("key", "ilike", "sla")],
                             ["id", "key", "value"]),
    }.items():
        try:
            d[schluessel] = cli.kw(model, "search_read", [dom], fields=felder, limit=0)
        except Exception as exc:  # noqa: BLE001
            d[schluessel] = {"__fehler__": str(exc)[:200]}

    # --- Bestand und Verteilung
    bestand, verteilung = {}, {}
    for modell in modellnamen:
        try:
            bestand[modell] = cli.kw(modell, "search_count", [[]])
        except Exception as exc:  # noqa: BLE001
            bestand[modell] = "FEHLER: %s" % str(exc)[:120]
        gruppen = []
        for feld in ("stage_id", "state", "category_id", "subcategory_id", "priority_id",
                     "team_id", "department_id", "user_id", "partner_id", "company_id",
                     "tag_ids", "type", "active"):
            if feld in d["felder"].get(modell, {}):
                gruppen.append(feld)
        if gruppen:
            try:
                verteilung[modell] = cli.kw(modell, "read_group", [], gruppen, ["__count"], limit=0)
            except Exception as exc:  # noqa: BLE001
                verteilung[modell] = "FEHLER: %s" % str(exc)[:150]
    d["bestand"] = bestand
    d["verteilung"] = verteilung

    pfad = os.path.join(a.ordner, "helpdesk_o11.json")
    with open(pfad, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1, sort_keys=True)
    print("Bestand:")
    for k, v in sorted(bestand.items()):
        print("  %-42s %s" % (k, v))
    print("\nRohdaten:", pfad, os.path.getsize(pfad), "Bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
