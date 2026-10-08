"""Vergleicht die sichtbaren Feldbezeichnungen (Sprache de_DE) Odoo 11 vs Odoo 18.

Read-only. Aufruf: python scripts/vergleiche_helpdesk_labels.py [--instanz lokal|vm]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18

STD = os.path.join(os.environ.get("USERPROFILE", "."), "Desktop",
                   "Odoo18-Helpdesk-Session132", "rohdaten")

# Odoo 11 Modell -> Odoo 18 Modell
PAARE = [
    ("website.support.ticket", "helpdesk.ticket"),
    ("website.support.ticket.states", "helpdesk.ticket.stage"),
    ("website.support.ticket.categories", "helpdesk.ticket.category"),
    ("website.support.ticket.priority", "itk.helpdesk.priority"),
    ("website.support.ticket.tag", "helpdesk.ticket.tag"),
]

# Felder, die inhaltlich dasselbe meinen (O11-Name -> O18-Name)
FELDPAARE = {
    "ticket_number": "number",
    "subject": "name",
    "description": "description",
    "category": "category_id",
    "sub_category_id": "sub_category_id",
    "priority_id": "priority_id",
    "channel": "channel_id",
    "state": "stage_id",
    "user_id": "user_id",
    "partner_id": "partner_id",
    "person_name": "partner_name",
    "email": "partner_email",
    "close_comment": "close_comment",
    "close_time": "closed_date",
    "closed_by_id": None,
    "support_comment": "support_comment",
    "support_rating": None,
    "tag_ids": "tag_ids",
    "sla_active": "sla_expired",
    "sla_timer": "sla_deadline",
    "sla_id": "sla_ids",
    "create_date": "create_date",
    "write_date": "write_date",
    "create_uid": "create_uid",
    "write_uid": "write_uid",
    "attachment_ids": "attachment_ids",
    "company_id": "company_id",
    "externe_felder": "dynamic_field_value_ids",
    "extra_field_ids": "dynamic_field_value_ids",
    "conversation_history": "message_ids",
    "website_message_ids": "website_message_ids",
    "analytic_timesheet_ids": "timesheet_ids",
}


def strings(cli, modell, sprache="de_DE"):
    try:
        f = cli.kw(modell, "fields_get", [], attributes=["string"],
                   context={"lang": sprache})
    except Exception as exc:  # noqa: BLE001
        return {"__fehler__": str(exc)[:200]}
    return {k: v.get("string") for k, v in f.items()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", default="lokal")
    ap.add_argument("--ordner", default=STD)
    a = ap.parse_args()
    os.makedirs(a.ordner, exist_ok=True)

    c11, c18 = o11(), o18(a.instanz)
    erg = {}
    print("=== Bezeichnungen de_DE: Odoo 11 gegen Odoo 18 (%s) ===" % a.instanz)
    for m11, m18 in PAARE:
        s11, s18 = strings(c11, m11), strings(c18, m18)
        erg[m11] = {"o11": s11, "o18_modell": m18, "o18": s18}
        print("\n--- %s  ->  %s" % (m11, m18))
        if "__fehler__" in s11:
            print("   O11 Fehler:", s11["__fehler__"])
        for feld in sorted(s11):
            if feld.startswith("__"):
                continue
            ziel = FELDPAARE.get(feld) if m11 == "website.support.ticket" else feld
            if ziel is None:
                print("   %-26s %-34s -> (bewusst kein Gegenstueck)" % (feld, s11[feld]))
            elif ziel in s18:
                print("   %-26s %-34s -> %-24s %-26s %s" % (
                    feld, s11[feld], ziel, s18[ziel],
                    "GLEICH" if s11[feld] == s18[ziel] else "ABWEICHUNG"))
            else:
                print("   %-26s %-34s -> FEHLT in Odoo 18 (%s)" % (feld, s11[feld], ziel))

    # Gegenrichtung: O18-Felder ohne O11-Gegenstueck
    print("\n=== Felder in Odoo 18 (helpdesk.ticket) ohne Odoo-11-Gegenstueck ===")
    s11 = erg["website.support.ticket"]["o11"]
    s18 = erg["website.support.ticket"]["o18"]
    umkehr = {v: k for k, v in FELDPAARE.items() if v}
    for feld in sorted(s18):
        if feld in umkehr or feld in s11 or feld.endswith("_ids") or feld.startswith("__"):
            continue
        print("   %-30s %s" % (feld, s18[feld]))

    pfad = os.path.join(a.ordner, "helpdesk_labels_de_%s.json" % a.instanz)
    with open(pfad, "w", encoding="utf-8") as fh:
        json.dump(erg, fh, ensure_ascii=False, indent=1, sort_keys=True)
    print("\nRohdaten:", pfad)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
