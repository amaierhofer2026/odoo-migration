"""Erzeugt migration/verkauf_migrationsregeln.json (Bereich Verkauf) aus live gemessenen Daten.

Read-only gegen Odoo 11 Prod (nur Lesen) und Odoo 18 (lokal). Es wird nichts geschrieben ausser
der JSON-Datei im Repo.

Aufruf:
    python scripts/baue_verkauf_migrationsregeln.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIEL = os.path.join(REPO, "migration", "verkauf_migrationsregeln.json")


def main() -> int:
    k11, k18 = o11(), o18("lokal")

    # Preislisten: welche Odoo-11-Preisliste liefert wie viele Auftraege?
    preislisten = []
    for p in k11.kw("product.pricelist", "search_read", [[], ["name", "currency_id", "active"]],
                    order="id", context={"lang": "de_DE"}):
        n = k11.kw("sale.order", "search_count", [[["pricelist_id", "=", p["id"]]]])
        if n:
            preislisten.append({
                "o11_id": p["id"], "o11_name": p["name"],
                "waehrung": (p["currency_id"] or [0, ""])[1],
                "aktiv_in_o11": p["active"], "auftraege": n,
            })
    auftraege_gesamt = k11.kw("sale.order", "search_count", [[]])

    # Zahlungsbedingungen mit Zeilen (Sollwerte fuer die Zuordnung)
    zahlungsbedingungen = []
    for p in k11.kw("account.payment.term", "search_read", [[], ["name"]], context={"lang": "de_DE"}):
        lin = k11.kw("account.payment.term.line", "search_read",
                     [[["payment_id", "=", p["id"]]], ["value", "days", "option"]])
        zahlungsbedingungen.append({
            "o11_id": p["id"], "name": p["name"],
            "o11_zeilen": [{"wert": l["value"], "tage": l["days"], "option": l["option"]} for l in lin],
            "auftraege": k11.kw("sale.order", "search_count", [[["payment_term_id", "=", p["id"]]]]),
        })

    o18_terme = {}
    for p in k18.kw("account.payment.term", "search_read", [[], ["name"]], context={"lang": "de_DE"}):
        lin = k18.kw("account.payment.term.line", "search_read",
                     [[["payment_id", "=", p["id"]]], ["value", "value_amount", "nb_days", "delay_type"]])
        o18_terme[p["name"]] = {
            "id": p["id"],
            "zeilen": [{"wert": l["value"], "anteil": l["value_amount"], "tage": l["nb_days"],
                        "verzoegerung": l["delay_type"]} for l in lin],
        }

    # Verkaeufer und Kanaele
    verkaeufer = [{"o11_id": g["user_id"][0], "name": g["user_id"][1], "auftraege": g["user_id_count"]}
                  for g in k11.kw("sale.order", "read_group", [[], ["user_id"], ["user_id"]])]
    kanaele = [{"o11_id": g["team_id"][0], "name": g["team_id"][1], "auftraege": g["team_id_count"]}
               for g in k11.kw("sale.order", "read_group", [[], ["team_id"], ["team_id"]])]

    # Stichwort im Verkauf
    stichwort_auftraege = k11.kw("sale.order", "search_read", [[["tag_ids", "!=", False]], ["name", "tag_ids"]],
                                 context={"lang": "de_DE"})
    o18_tags = k18.kw("crm.tag", "search_read", [[], ["name"]], context={"lang": "de_DE"})

    daten = {
        "bereich": "Verkauf",
        "erstellt": "2026-09-24",
        "grundlage": {
            "odoo11": "portal.it-kommunal.at / ITK_V1_a (nur lesend verwendet)",
            "odoo18": "odoo18_test (lokal und VM k001959vsx.ipax.at)",
            "auftraege_odoo11": auftraege_gesamt,
        },
        "entscheidungen_anna": {
            "note": "Inhalt aus Odoo 11 vollstaendig uebernehmen; Zeilenumbrueche fuer das HTML-Feld "
                    "in Odoo 18 korrekt in HTML umsetzen.",
            "zahlungsbedingung_30_tage_netto": "Keine Dublette anlegen; auf die vorhandene, fachlich "
                                               "identische Zahlungsbedingung in Odoo 18 mappen.",
            "stichwort_up_sell": "Nicht verlieren; als spaeterer Stammdaten-/Migrationsschritt "
                                 "eindeutig vorbereiten und dokumentieren.",
            "sale_stock_sale_timesheet": "Felder duerfen entfallen (Module werden in Odoo 18 bewusst "
                                         "nicht installiert). Kein Nachbau, weiterhin dokumentieren.",
            "preislisten": "Spaeterer Datenmigrationsschritt; Zuordnungen vollstaendig vorbereiten, "
                           "EUR bleibt verbindlich.",
        },
        "note_feld": {
            "o11_feld": "sale.order.note (text)",
            "o18_feld": "sale.order.note (html)",
            "belegt_in_o11": k11.kw("sale.order", "search_count", [[["note", "!=", False]]]),
            "regel": "Klartext uebernehmen, Zeilenumbrueche in <br> wandeln, Sonderzeichen escapen, "
                     "keine weitere Formatierung erfinden.",
        },
        "zahlungsbedingungen": {
            "regel": "Zuordnung Odoo-11-Zahlungsbedingung auf Odoo-18-Zahlungsbedingung; keine "
                     "Dubletten anlegen.",
            "o11": zahlungsbedingungen,
            "o18_vorhanden": o18_terme,
            "zuordnung": {
                "Sofortige Zahlung": {"ziel_id": o18_terme.get("Sofortige Zahlung", {}).get("id"),
                                      "identisch": True, "auftraege": 96},
                "14 Tage": {"ziel_id": o18_terme.get("14 Tage", {}).get("id"),
                            "identisch": False,
                            "befund": "Odoo 18 fuehrt '14 Tage' mit nb_days = 0 (Zahlung sofort), "
                                      "Odoo 11 mit 14 Tagen (day_after_invoice_date). "
                                      "ENTSCHEIDUNG NOETIG: Odoo-18-Eintrag auf 14 Tage korrigieren "
                                      "oder Zuordnung anpassen.",
                            "auftraege": 515},
                "30 Tage netto": {"ziel_id": o18_terme.get("30 Tage", {}).get("id"),
                                  "identisch": True,
                                  "begruendung": "Odoo 11: Restbetrag nach 30 Tagen ab Rechnungsdatum; "
                                                 "Odoo 18 '30 Tage': 100 % nach 30 Tagen (days_after). "
                                                 "Fachlich identisch.",
                                  "auftraege": 2},
                "15 Tage": {"ziel_id": o18_terme.get("15 Tage", {}).get("id"), "identisch": True,
                            "auftraege": 0, "hinweis": "in Odoo 11 nie verwendet"},
            },
        },
        "stichworte": {
            "regel": "Stichwoerter vor der Migration in Odoo 18 anlegen (Odoo 11 crm.lead.tag -> "
                     "Odoo 18 crm.tag); im Verkauf ist genau ein Auftrag betroffen.",
            "o18_crm_tag_anzahl": len(o18_tags),
            "o18_crm_tag_namen": [t["name"] for t in o18_tags],
            "betroffene_auftraege": [
                {"auftrag": a["name"], "o11_tags": [t for t in a["tag_ids"]]} for a in stichwort_auftraege
            ],
            "vorzubereiten": ["Up-Sell"],
        },
        "preislisten": {
            "regel": "Alle Odoo-11-Preislisten werden auf die eine verbindliche Odoo-18-Preisliste "
                     "abgebildet (EUR). Keine neuen Preislisten in Odoo 18.",
            "o18_ziel": {"id": 34, "name": "Preisliste 2026 + Valorisierung", "waehrung": "EUR",
                         "aktiv": True},
            "o11_preislisten_mit_auftraegen": preislisten,
            "summe_auftraege": sum(p["auftraege"] for p in preislisten),
            "hinweis": "Die Odoo-11-Preisliste 'Preisliste 2026 + Valorisierung' (id 56, 256 Auftraege) "
                       "entspricht namentlich der Odoo-18-Zielpreisliste.",
        },
        "verkaeufer": {
            "regel": "Benutzerzuordnung vor der Migration; ausgeschiedene Benutzer deaktiviert anlegen, "
                     "historische Verkaeuferbeziehung erhalten.",
            "anzahl_verschiedene_verkaeufer_auf_auftraegen": len(verkaeufer),
            "verteilung": sorted(verkaeufer, key=lambda x: -x["auftraege"]),
        },
        "vertriebskanaele": {
            "regel": "Zuordnung der Odoo-11-Kanaele auf die Odoo-18-Verkaufsteams.",
            "o11_verwendet": kanaele,
        },
        "entfallende_felder": {
            "sale_stock": ["picking_policy", "warehouse_id", "procurement_group_id", "picking_ids",
                           "delivery_count", "move_ids", "product_packaging", "route_id", "incoterm"],
            "sale_timesheet": ["project_ids", "project_project_id", "tasks_ids", "tasks_count",
                               "timesheet_ids", "timesheet_count", "task_id"],
            "begruendung": "Module werden in Odoo 18 bewusst nicht installiert (Sessions 119/120); "
                           "Felder bleiben dokumentiert, kein Nachbau.",
        },
    }

    os.makedirs(os.path.dirname(ZIEL), exist_ok=True)
    with open(ZIEL, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(daten, fh, ensure_ascii=False, indent=1)
    print("geschrieben: %s" % ZIEL)
    print("Preislisten mit Auftraegen: %d, Summe Auftraege: %d (von %d)"
          % (len(preislisten), daten["preislisten"]["summe_auftraege"], auftraege_gesamt))
    print("Verkaeufer: %d | Kanaele: %d | O18 crm.tag: %d | betroffene Auftraege mit Stichwort: %d"
          % (len(verkaeufer), len(kanaele), len(o18_tags), len(stichwort_auftraege)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
