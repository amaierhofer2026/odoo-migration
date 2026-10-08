"""Helpdesk Odoo 11 - Teil 2: Menuebaum, Stammdaten, Verteilung, Ansichtsarchitekturen (read-only).

Aufruf: python scripts/erhebe_helpdesk_o11_teil2.py [--ordner PFAD]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11

STD = os.path.join(os.environ.get("USERPROFILE", "."), "Desktop",
                   "Odoo18-Helpdesk-Session132", "rohdaten")


def kurz(t, n=110):
    t = " ".join(str(t).split())
    return t if len(t) <= n else t[: n - 3] + "..."


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ordner", default=STD)
    a = ap.parse_args()
    os.makedirs(a.ordner, exist_ok=True)
    cli = o11()
    d = {}

    # --- Menuebaum unter "Customer Support" (id 359)
    alle = cli.kw("ir.ui.menu", "search_read", [[]],
                  fields=["id", "name", "complete_name", "parent_id", "sequence", "action",
                          "groups_id", "child_id"], order="complete_name", limit=0)
    d["menues_alle"] = alle
    print("=== Menuebaum Customer Support ===")
    for m in alle:
        if "Customer Support" in (m["complete_name"] or ""):
            tiefe = (m["complete_name"] or "").count("/")
            print("  %s%-58s seq=%-4s action=%s groups=%s" % (
                "  " * tiefe, m["name"], m["sequence"], m["action"] or "-",
                m["groups_id"] or []))

    # --- Zustandsmodelle / Stammdaten
    print("\n=== Ticket-Stufen (website.support.ticket.states) ===")
    st = cli.kw("website.support.ticket.states", "search_read", [[]],
                fields=["id", "name", "unattended", "mail_template_id"], limit=0)
    for s in st:
        print("  %-28s unattended=%-6s vorlage=%s" % (
            s["name"], s["unattended"],
            (s["mail_template_id"] or [None, "-"])[1] if isinstance(s["mail_template_id"], list) else "-"))
    d["states"] = st

    print("\n=== Kategorien ===")
    kat = cli.kw("website.support.ticket.categories", "search_read", [[]],
                 fields=["id", "name", "sequence", "cat_user_ids"], order="sequence", limit=0)
    for k in kat:
        print("  %-36s seq=%-4s benutzer=%s" % (k["name"], k["sequence"], len(k["cat_user_ids"])))
    d["kategorien"] = kat

    print("\n=== Unterkategorien ===")
    sub = cli.kw("website.support.ticket.subcategory", "search_read", [[]],
                 fields=["id", "name", "parent_category_id", "sequence", "additional_field_ids"],
                 order="parent_category_id, sequence", limit=0)
    for s in sub:
        print("  %-32s eltern=%-32s seq=%-4s zusatzfelder=%s" % (
            s["name"], (s["parent_category_id"] or [None, "-"])[1], s["sequence"],
            len(s["additional_field_ids"])))
    d["unterkategorien"] = sub

    print("\n=== Prioritaeten ===")
    prio = cli.kw("website.support.ticket.priority", "search_read", [[]],
                  fields=["id", "name", "sequence", "color"], order="sequence", limit=0)
    for p in prio:
        print("  %-28s seq=%-4s farbe=%s" % (p["name"], p["sequence"], p["color"]))
    d["prioritaeten"] = prio

    print("\n=== Tags ===")
    d["tags"] = cli.kw("website.support.ticket.tag", "search_read", [[]],
                       fields=["id", "name"], limit=0)
    print("  Anzahl:", len(d["tags"]))

    print("\n=== SLA ===")
    sla = cli.kw("website.support.sla", "search_read", [[]],
                 fields=["id", "name", "description", "response_time_ids", "alert_ids"], limit=0)
    for s in sla:
        print("  %-28s Antwortzeiten=%s Alarme=%s" % (s["name"], len(s["response_time_ids"]),
                                                      len(s["alert_ids"])))
    d["sla"] = sla
    d["sla_response"] = cli.kw("website.support.sla.response", "search_read", [[]],
                               fields=["id", "category_id", "response_time", "countdown_condition",
                                       "vsa_id"], limit=0)
    for r in d["sla_response"]:
        print("     - %-30s %s h (%s)" % ((r["category_id"] or [None, "?"])[1], r["response_time"],
                                          r["countdown_condition"]))
    d["sla_alert"] = cli.kw("website.support.sla.alert", "search_read", [[]],
                            fields=["id", "alert_time", "type", "vsa_id"], limit=0)

    print("\n=== Antwort-/Nachrichtenbausteine (ticket.message) ===")
    msg = cli.kw("website.support.ticket.message", "search_read", [[]],
                 fields=["id", "by", "content"], limit=0)
    d["message_bausteine"] = msg
    for m in msg[:40]:
        print("  %-12s %s" % (m.get("by"), kurz(m["content"], 90)))
    print("  Anzahl gesamt:", len(msg))

    print("\n=== Abschluss-Bausteine (ticket.close) ===")
    clo = cli.kw("website.support.ticket.close", "search_read", [[]], fields=["id", "message"], limit=0)
    d["close_bausteine"] = clo
    for c in clo[:40]:
        print("  %s" % kurz(c["message"], 100))
    print("  Anzahl gesamt:", len(clo))

    print("\n=== Compose-Vorlagen (ticket.compose) ===")
    com = cli.kw("website.support.ticket.compose", "search_read", [[]],
                 fields=["id", "subject", "body", "template_id", "approval", "planned_time"], limit=0)
    d["compose_vorlagen"] = com
    for c in com[:40]:
        print("  %-70s vorlage=%s" % (kurz(c["subject"], 70),
                                      (c["template_id"] or [None, "-"])[1] if isinstance(c["template_id"], list) else "-"))
    print("  Anzahl gesamt:", len(com))

    # --- Verteilung (korrekte read_group-Signatur)
    print("\n=== Verteilung website.support.ticket ===")
    verteilung = {}
    for feld in ("state", "category", "sub_category_id", "priority_id", "user_id", "partner_id",
                 "company_id", "sla_active", "channel", "closed_by_id"):
        try:
            res = cli.kw("website.support.ticket", "read_group", [],
                         domain=[], fields=[feld], groupby=[feld], limit=0)
        except Exception as exc:  # noqa: BLE001
            res = "FEHLER: %s" % str(exc)[:160]
        verteilung[feld] = res
        print("  -- %s" % feld)
        if isinstance(res, str):
            print("     ", kurz(res, 160))
            continue
        for g in res:
            wert = g.get(feld)
            print("     %-60s %s" % (wert, g.get("__count")))
    d["verteilung2"] = verteilung

    # --- Ticketnummernkreis
    print("\n=== Sequenz Ticketnummer ===")
    seq = cli.kw("ir.sequence", "search_read", [[("code", "=", "website.support.ticket")]],
                 fields=["id", "name", "code", "prefix", "padding", "number_next_actual",
                         "implementation", "company_id"], limit=0)
    for s in seq:
        print("  Praefix=%r Padding=%s naechste=%s no_gap=%s" % (s["prefix"], s["padding"],
                                                                 s["number_next_actual"],
                                                                 s["implementation"]))
    d["sequenz"] = seq

    # --- Beispieltickets (nur lesen, wenige Felder)
    print("\n=== Beispieltickets (5 neueste, Kurzansicht) ===")
    bsp = cli.kw("website.support.ticket", "search_read", [[]],
                 fields=["ticket_number", "subject", "state", "category", "sub_category_id",
                         "priority_id", "user_id", "partner_id", "create_date", "close_date",
                         "sla_active", "support_rating"],
                 order="create_date desc", limit=5)
    for b in bsp:
        print("  %-16s %-46s %-16s %s" % (
            b["ticket_number"], kurz(b["subject"], 46),
            (b["state"] or [None, "-"])[1] if isinstance(b["state"], list) else "-",
            b["create_date"]))
    d["beispiele"] = bsp

    # --- Benutzer in den Support-Gruppen
    print("\n=== Benutzer der Support-Gruppen ===")
    for gid, gname in ((71, "Support Client"), (72, "Support Staff"), (73, "Support Manager")):
        nutzer = cli.kw("res.users", "search_read", [[("groups_id", "in", [gid])]],
                        fields=["id", "login", "name"], limit=0)
        d.setdefault("gruppen_nutzer", {})[gname] = nutzer
        print("  %s (%d): %s" % (gname, len(nutzer), ", ".join(n["login"] for n in nutzer)))

    pfad = os.path.join(a.ordner, "helpdesk_o11_teil2.json")
    with open(pfad, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1, sort_keys=True)
    print("\nRohdaten:", pfad)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
