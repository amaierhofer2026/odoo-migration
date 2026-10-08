"""Bestandsaufnahme Helpdesk (vorher/nachher) - read-only.

Aufruf: python scripts/helpdesk_bestand.py --instanz lokal|vm
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o18

MODELLE = [
    "helpdesk.ticket", "helpdesk.ticket.stage", "helpdesk.ticket.team",
    "helpdesk.ticket.category", "helpdesk.ticket.channel", "helpdesk.ticket.tag",
    "helpdesk.sla", "helpdesk.ticket.sla", "itk.helpdesk.priority",
    "itk.helpdesk.subcategory.field", "itk.helpdesk.subcategory.field.value",
    "itk.helpdesk.public.submission", "ir.attachment",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", default="lokal")
    a = ap.parse_args()
    cli = o18(a.instanz)
    print("=== Helpdesk-Bestand (%s) ===" % a.instanz)
    werte = {}
    for modell in MODELLE:
        try:
            if modell == "ir.attachment":
                n = cli.kw(modell, "search_count", [[("res_model", "=", "helpdesk.ticket")]])
            else:
                n = cli.kw(modell, "search_count", [[]])
        except Exception as exc:  # noqa: BLE001
            n = "FEHLER: %s" % str(exc)[:90]
        werte[modell] = n
        print("  %-38s %s" % (modell, n))
    print("\n  -- Stufen")
    for s in cli.kw("helpdesk.ticket.stage", "search_read", [[]],
                    fields=["id", "name", "sequence", "unattended", "closed", "active"],
                    order="sequence", limit=0):
        print("     %-28s seq=%-4s unbeaufsichtigt=%-6s geschlossen=%-6s aktiv=%s" % (
            s["name"], s["sequence"], s["unattended"], s["closed"], s["active"]))
    print("\n  -- Kanaele")
    for k in cli.kw("helpdesk.ticket.channel", "search_read", [[]],
                    fields=["id", "name", "active"], limit=0):
        print("     %-28s aktiv=%s" % (k["name"], k["active"]))
    print("\n  -- Prioritaeten")
    for p in cli.kw("itk.helpdesk.priority", "search_read", [[]],
                    fields=["id", "name", "sequence", "color", "active"], limit=0):
        print("     %-28s seq=%s farbe=%s" % (p["name"], p["sequence"], p["color"]))
    print("\n  -- Teams")
    for t in cli.kw("helpdesk.ticket.team", "search_read", [[]],
                    fields=["id", "name", "active", "use_sla"], limit=0):
        print("     %-28s aktiv=%s SLA=%s" % (t["name"], t["active"], t["use_sla"]))
    print("\n  -- Sequenz")
    for s in cli.kw("ir.sequence", "search_read", [[("code", "=", "helpdesk.ticket.sequence")]],
                    fields=["id", "name", "prefix", "padding", "number_next_actual",
                            "implementation"], limit=0):
        print("     %s Praefix=%r Padding=%s naechste=%s" % (
            s["name"], s["prefix"], s["padding"], s["number_next_actual"]))
    print("\n  -- Module")
    for m in cli.kw("ir.module.module", "search_read",
                    [[("name", "in", ["itk_helpdesk_compat", "itk_helpdesk_category_user",
                                      "helpdesk_mgmt", "helpdesk_mgmt_sla"])]],
                    fields=["name", "installed_version", "state"], limit=0):
        print("     %-30s %-12s %s" % (m["name"], m["installed_version"], m["state"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
