"""Prueflauf Verkauf Teil 4, Schritt 1: Listen-, Kanban-, Pivot-, Graph- und Kalenderansichten.

Prueft in Odoo 11 (nur lesend), Odoo 18 lokal und Odoo 18 VM:
  - Odoo 11 als Ausgangslage: Spalten der Liste, Kanban-Kartenfelder, Pivot, Graph, Kalender
  - Odoo 18: alle Odoo-11-Spalten je Menueaktion vorhanden (inkl. "Bestelldatum")
  - Odoo 18: Kanban, Pivot, Graph gleichwertig; Kalender unveraendert (Aktivitaeten-Kalender)
  - Odoo 18: die Zusatzspalten und Zusatzansichten sind weiterhin vorhanden
  - keine Default-Gruppierung in den Aktionskontexten (wie Odoo 11)

Aufruf:
    python scripts/verify_s121_verkauf_teil4_ansichten.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18
from analyse_verkauf_teil4_ansichten import ansicht_lesen, kalender_auswerten, kanban_auswerten, \
    liste_auswerten, graph_auswerten, pivot_auswerten

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP = {"lang": "de_DE"}
MODELL = "sale.order"

# Menueaktionen: Odoo 11 -> Odoo 18
AKTIONEN = {"o11": [429, 426, 427, 428], "o18": [430, 431, 429, 432, 433]}
# Spalten, die Odoo 11 in der Verkaufsliste zeigt (Reihenfolge)
SPALTEN_O11 = ["message_needaction", "name", "confirmation_date", "partner_id", "partner_invoice_id",
               "sale_contact_id", "user_id", "amount_untaxed", "currency_id", "invoice_status", "state"]
# Zusatzspalten aus Odoo 18, die erhalten bleiben muessen (Die Datumsspalte heisst in der
# Angebotsliste "Erstellungsdatum" (create_date), in der Auftragsliste "Auftragsdatum" (date_order);
# beide werden als Paar geprueft.)
SPALTEN_O18_ZUSATZ = ["commitment_date", "expected_date", "team_id", "company_id", "amount_tax",
                      "tag_ids", "client_order_ref", "validity_date", "activity_ids"]
# Ansichtsarten: Odoo 11 ohne Aktivitaeten; Odoo 18 mit Aktivitaeten
ARTEN_O11 = {"tree", "kanban", "form", "calendar", "pivot", "graph"}
ARTEN_O18 = {"list", "kanban", "form", "calendar", "pivot", "graph", "activity"}


def haupt_ansicht(client, aktion: dict, typ: str, ist18: bool):
    """Die von der Aktion verwendete Ansicht (action.view_id fuer die erste Ansichtsart)."""
    erste = aktion["view_mode"].split(",")[0].strip()
    vid = aktion["view_id"] if typ in ("list", "tree") and erste in ("list", "tree") else False
    if isinstance(vid, list):
        vid = vid[0]
    return ansicht_lesen(client, vid or False, typ, ist18)


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

    print("Prueflauf Verkauf Teil 4, Schritt 1 (Ansichten)")
    print("Odoo 11 Prod wird ausschliesslich lesend gelesen.\n")

    for schluessel, client, ist18, name in (("o11", o11(), False, "Odoo 11 Prod"),
                                            ("o18", o18("lokal"), True, "Odoo 18 lokal"),
                                            ("vm", o18("vm"), True, "Odoo 18 VM")):
        art = "o11" if not ist18 else "o18"
        print("--- %s ---" % name)
        for aktion_id in AKTIONEN[art]:
            aktion = client.kw("ir.actions.act_window", "read",
                               [[aktion_id], ["name", "view_mode", "view_id", "context"]], context=SP)[0]
            print("  Aktion %s '%s'" % (aktion_id, aktion["name"]))
            arten = {a.strip() for a in aktion["view_mode"].split(",")}
            erwartet = ARTEN_O11 if not ist18 else ARTEN_O18
            pruefe(erwartet.issubset(arten), "Ansichtsarten %s" % sorted(arten))
            if not ist18:
                pruefe("activity" not in arten, "keine Aktivitaeten-Ansicht (in Odoo 11 nicht vorhanden)")
            else:
                pruefe("activity" in arten, "Odoo-18-Aktivitaetenansicht weiterhin vorhanden")
            kontext = aktion["context"] or "{}"
            pruefe("group_by" not in kontext, "keine Default-Gruppierung im Kontext (%s)" % kontext)

            arch, _ = haupt_ansicht(client, aktion, "tree" if not ist18 else "list", ist18)
            spalten = [s["name"] for s in liste_auswerten(arch)["spalten"]]
            fehlend = [s for s in SPALTEN_O11 if s not in spalten]
            pruefe(not fehlend, "Liste: alle Odoo-11-Spalten vorhanden (%d Spalten)" % len(spalten))
            if fehlend:
                print("        fehlt: %s" % fehlend)
            if ist18:
                zusatz = [s for s in SPALTEN_O18_ZUSATZ if s in spalten]
                pruefe(len(zusatz) == len(SPALTEN_O18_ZUSATZ),
                       "Liste: Odoo-18-Zusatzspalten erhalten (%d/%d)"
                       % (len(zusatz), len(SPALTEN_O18_ZUSATZ)))
                pruefe("create_date" in spalten or "date_order" in spalten,
                       "Liste: Odoo-18-Datumsspalte erhalten (%s)"
                       % ("Erstellungsdatum" if "create_date" in spalten else "Auftragsdatum"))
                bestelldatum = [s for s in liste_auswerten(arch)["spalten"]
                                if s["name"] == "confirmation_date"]
                pruefe(bool(bestelldatum) and bestelldatum[0]["string"] == "Bestelldatum",
                       "Liste: Spalte 'Bestelldatum' mit Odoo-11-Wortlaut vorhanden")
            else:
                pruefe("confirmation_date" in spalten, "Liste: Odoo 11 zeigt 'Bestelldatum'")

            for typ in ("kanban", "pivot", "graph"):
                arch, _ = haupt_ansicht(client, aktion, typ, ist18)
                if typ == "kanban":
                    felder = kanban_auswerten(arch)["alle_felder"]
                    pruefe(all(f in felder for f in ("name", "partner_id", "amount_total", "state")),
                           "Kanban: Kartenfelder wie Odoo 11 (%s)" % ", ".join(sorted(set(felder))[:6]))
                elif typ == "pivot":
                    felder = pivot_auswerten(arch)["felder"]
                    namen = {(f["name"], f["typ"]) for f in felder}
                    pruefe(("date_order", "row") in namen and ("amount_total", "measure") in namen,
                           "Pivot: %s" % sorted("%s/%s" % (n, t or "?") for n, t in namen))
                else:
                    felder = graph_auswerten(arch)["felder"]
                    namen = [f["name"] for f in felder]
                    pruefe("partner_id" in namen and "amount_total" in namen,
                           "Graph: %s" % ", ".join(namen))

            arch, vid = haupt_ansicht(client, aktion, "calendar", ist18)
            k = kalender_auswerten(arch)
            start = k["attrs"].get("date_start")
            if ist18:
                pruefe(start == "activity_date_deadline",
                       "Kalender: Odoo-18-Aktivitaetenkalender unveraendert (date_start=%s, Ansicht %s)"
                       % (start, vid))
            else:
                pruefe(start == "date_order",
                       "Kalender (Odoo 11): date_start=%s, color=%s" % (start, k["attrs"].get("color")))
        print()

    print("Odoo 11 Prod wurde ausschliesslich lesend verwendet.")
    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
