"""Prueflauf Verkauf Teil 3, Schritt 4: Suchfelder, Filter, Gruppierungen, Default-Filter.

Prueft in Odoo 11 (nur lesend), Odoo 18 lokal und Odoo 18 VM:
  - Ausgangslage in Odoo 11: Filter und Gruppierungen der vier Verkaufslisten
  - Odoo 18: die ergaenzten Filter (Ungelesene Nachrichten, Meine Aktivitaeten,
    Angebote (Entwurf), Kostenvoranschlag gesendet) sind in der jeweiligen Suchansicht vorhanden
  - Odoo 18: die vorhandenen Filter und Gruppierungen sind unveraendert erhalten
  - Odoo 18: kein Default-Filter beim Menueaufruf (Aktionskontext ohne search_default_my_quotation)
  - Suchfelder je Liste

Aufruf:
    python scripts/verify_s121_verkauf_teil3_filter.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18
from analyse_verkauf_teil3_suche import arch_auswerten, arch_lesen

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP = {"lang": "de_DE"}
MODELL = "sale.order"

# Je Aktion: Suchansicht und erwartete Filter (Name -> Beschriftung)
ERWARTET = {
    "o11": {
        429: {"filter": {"my_sale_orders_filter": "Meine Bestellungen", "draft": "Angebote",
                         "sent": "Kostenvoranschlag gesendet", "sales": "Verkauf",
                         "message_needaction": "Ungelesene Nachrichten",
                         "activities_my": "Meine Aktivitäten"},
              "gruppen": {"user_id", "partner_id", "final_customer_id", "product_category_id",
                          "date_order"},
              "felder": {"name", "partner_id", "user_id", "team_id", "analytic_account_id"},
              "kontext_ohne_default": True},
        426: {"filter": {"my_sale_orders_filter": "Meine Bestellungen", "sales": "Verkauf",
                         "message_needaction": "Ungelesene Nachrichten",
                         "activities_my": "Meine Aktivitäten"},
              "gruppen": {"user_id", "partner_id", "final_customer_id", "product_category_id",
                          "date_order"},
              "felder": {"name", "partner_id", "user_id", "team_id", "product_category_id"},
              "kontext_ohne_default": True},
        427: {"filter": {"my_sale_orders_filter": "Meine Bestellungen",
                         "message_needaction": "Ungelesene Nachrichten",
                         "activities_my": "Meine Aktivitäten"},
              "gruppen": {"user_id", "partner_id", "date_order"},
              "felder": {"name", "partner_id", "user_id", "team_id"},
              "kontext_ohne_default": True},
    },
    "o18": {
        430: {"filter": {"my_quotation": "Meine Angebote", "draft": "Angebote",
                         "sales": "Verkaufsaufträge",
                         "message_needaction": "Ungelesene Nachrichten",
                         "activities_my": "Meine Aktivitäten",
                         "itk_state_draft": "Angebote (Entwurf)",
                         "itk_state_sent": "Kostenvoranschlag gesendet"},
              "gruppen": {"user_id", "partner_id", "final_customer_id", "product_category_id",
                          "date_order"},
              "felder": {"name", "partner_id", "user_id", "team_id", "order_line"},
              "kontext_ohne_default": True},
        431: {"filter": {"my_quotation": "Meine Angebote",
                         "message_needaction": "Ungelesene Nachrichten",
                         "activities_my": "Meine Aktivitäten",
                         "itk_state_draft": "Angebote (Entwurf)",
                         "itk_state_sent": "Kostenvoranschlag gesendet"},
              "gruppen": {"user_id", "partner_id", "final_customer_id", "product_category_id",
                          "date_order"},
              "felder": {"name", "partner_id", "user_id", "team_id", "order_line"},
              "kontext_ohne_default": True},
        429: {"filter": {"my_sale_orders_filter": "Meine Aufträge",
                         "message_needaction": "Ungelesene Nachrichten",
                         "activities_my": "Meine Aktivitäten"},
              "gruppen": {"user_id", "partner_id", "final_customer_id", "product_category_id",
                          "date_order"},
              "felder": {"name", "partner_id", "user_id", "team_id", "order_line"},
              "kontext_ohne_default": True},
        432: {"filter": {"my_sale_orders_filter": "Meine Aufträge",
                         "message_needaction": "Ungelesene Nachrichten",
                         "activities_my": "Meine Aktivitäten"},
              "gruppen": {"user_id", "partner_id", "date_order"},
              "felder": {"name", "partner_id", "user_id", "team_id", "order_line"},
              "kontext_ohne_default": True},
    },
}


def main() -> int:
    ok = fehler = 0

    def pruefe(bedingung, text):
        nonlocal ok, fehler
        if bedingung:
            ok += 1
            print("  OK   %s" % text)
        else:
            fehler += 1
            print("  FEHL %s" % text)

    print("Prueflauf Verkauf Teil 3, Schritt 4 (Suchfelder, Filter, Gruppierungen, Default-Filter)")
    print("Odoo 11 Prod wird ausschliesslich lesend gelesen.\n")

    for schluessel, client, ist18, name in (("o11", o11(), False, "Odoo 11 Prod"),
                                            ("o18", o18("lokal"), True, "Odoo 18 lokal"),
                                            ("vm", o18("vm"), True, "Odoo 18 VM")):
        art = "o11" if not ist18 else "o18"
        print("--- %s ---" % name)
        for aktion_id, erwartet in ERWARTET[art].items():
            aktion = client.kw("ir.actions.act_window", "read",
                               [[aktion_id], ["name", "context", "domain"]], context=SP)
            if not aktion:
                pruefe(False, "Aktion %s vorhanden" % aktion_id)
                continue
            aktion = aktion[0]
            sv = client.kw("ir.actions.act_window", "read",
                           [[aktion_id], ["search_view_id"]], context=SP)[0]["search_view_id"]
            vid = sv[0] if isinstance(sv, list) else (sv or False)
            daten = arch_auswerten(arch_lesen(client, vid, ist18))
            namen = {f["name"]: f["string"] for f in daten["filter"]}
            gruppen = set()
            for g in daten["gruppen"]:
                treffer = __import__("re").search(r"group_by'?\s*:?\s*'?([a-z_]+)'?", g["context"] or "")
                if treffer:
                    gruppen.add(treffer.group(1))
            felder = {f["name"] for f in daten["felder"]}
            print("  Aktion %s '%s' (Suchansicht %s)" % (aktion_id, aktion["name"], vid))
            for fname, fstring in sorted(erwartet["filter"].items()):
                pruefe(fname in namen, "Filter %-24s '%s'" % (fname, fstring))
                if fname in namen and ist18:
                    pruefe(namen[fname] == fstring,
                           "   Beschriftung '%s'" % namen[fname])
            for g in sorted(erwartet["gruppen"]):
                pruefe(g in gruppen, "Gruppierung nach %s vorhanden" % g)
            for f in sorted(erwartet["felder"]):
                pruefe(f in felder, "Suchfeld %s vorhanden" % f)
            if erwartet["kontext_ohne_default"]:
                kontext = aktion["context"] or "{}"
                pruefe("search_default_my_quotation" not in kontext,
                       "kein Default-Filter im Aktionskontext (%s)" % kontext)
        print()

    print("Odoo 11 Prod wurde ausschliesslich lesend verwendet.")
    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
