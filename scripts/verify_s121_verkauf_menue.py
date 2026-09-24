"""Abnahmepruefung Bereich Verkauf Teil 1 (Session 121): Menues, Module, Nutzungen.

Vergleicht READ-ONLY:
  - Odoo 11 Prod (Menuebaum und Nutzungszahlen, nur lesend)
  - Odoo 18 lokal gegen Odoo 18 VM (Menuebaum muss identisch sein)

Aufruf:
    python scripts/verify_s121_verkauf_menue.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18
from analyse_verkauf_menue import menuebaum

# Odoo-11-Menue (Pfad ab Wurzel "Verkauf") -> erwarteter Pfad in Odoo 18
MAPPING = {
    "Aufträge/Angebote nach Kunden": "Aufträge/Angebote",
    "Aufträge/Aufträge nach Kunden": "Aufträge/Aufträge",
    "Aufträge/Kunden": "Aufträge/Kunden",
    "Aufträge/Auftrag-Ansichten": "Aufträge/Alle Auftragszeilen",
    "Abrechnung/Aufträge zur Rechnung": "Abzurechnen/Abzurechnende Aufträge",
    "Abrechnung/Aufträge für Upselling": "Abzurechnen/Aufträge für Upselling",
    "Katalog/Produkte": "Produkte/Produkte",
    "Katalog/Preislisten": "Produkte/Preislisten",
    "Berichtswesen/Verkauf": "Berichtswesen/Verkauf",
    "Konfiguration/Einstellungen": "Konfiguration/Einstellungen",
    "Konfiguration/Vertriebskänale": "Konfiguration/Verkaufsteams",
}

# In Odoo 11 vorhanden, in Odoo 18 bewusst nicht (dokumentiert)
NICHT_IN_O18 = [
    "Berichtswesen/Verkaufsaufträge aller Kanäle",
    "Konfiguration/Verkaufsaufträge/Reportlayout Kategorien",
    "Konfiguration/Verkaufsaufträge/Kundendienst/Dienstleistungen/Reklamationen",
]


def pfade(knoten, pfad="", ergebnis=None):
    ergebnis = [] if ergebnis is None else ergebnis
    for n in knoten:
        p = (pfad + "/" + n["name"]) if pfad else n["name"]
        ergebnis.append((p, n))
        pfade(n["kinder"], p, ergebnis)
    return ergebnis


def nur_vergleichbar(knoten):
    """Name + Aktions-id je Menue, Reihenfolge egal (fuer lokal-gegen-VM-Vergleich)."""
    return sorted((p, (n["aktion"] or {}).get("id")) for p, n in pfade(knoten))


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

    k11 = o11()
    k18 = o18("lokal")
    kvm = o18("vm")

    b11 = menuebaum(k11, ("Verkauf",))[0]
    b18 = menuebaum(k18, ("Verkauf",))[0]
    bvm = menuebaum(kvm, ("Verkauf",))[0]
    p11 = dict(pfade(b11))
    p18 = dict(pfade(b18))

    print("Instanz lokal: sale.order %d | VM: sale.order %d" %
          (k18.kw("sale.order", "search_count", [[]]), kvm.kw("sale.order", "search_count", [[]])))
    print("\n1) Menuebaum lokal gegen VM")
    a, b = nur_vergleichbar(b18), nur_vergleichbar(bvm)
    pruefe(a == b, "Menuebaum lokal = VM (%d Menues)" % len(a))
    if a != b:
        for x in set(a) ^ set(b):
            print("       Unterschied: %s" % (x,))

    print("\n2) Wurzelmenue und Umfang")
    for name, kl, baum, soll in (("lokal", k18, b18, 37), ("VM", kvm, bvm, 37)):
        w = kl.kw("ir.ui.menu", "search_read", [[["parent_id", "=", False], ["name", "=", "Verkauf"]],
                                                ["name", "sequence"]], context={"lang": "de_DE"})
        pruefe(bool(w), "%s: Wurzelmenue 'Verkauf' vorhanden (Sequenz %s)" % (name, w[0]["sequence"] if w else "?"))
    pruefe(len(pfade(b18)) == 37, "Odoo-18-Menues unter Verkauf: %d (erwartet 37)" % len(pfade(b18)))
    pruefe(len(pfade(b11)) == 23, "Odoo-11-Menues unter Verkauf: %d (erwartet 23)" % len(pfade(b11)))

    print("\n3) Zuordnung der Odoo-11-Menues")
    for o11pfad, o18pfad in MAPPING.items():
        pruefe(o11pfad in p11, "Odoo 11 hat %s" % o11pfad)
        pruefe(o18pfad in p18, "Odoo 18 hat %s (Ziel von %s)" % (o18pfad, o11pfad))

    print("\n4) Bewusst nicht uebernommene Odoo-11-Menues")
    for p in NICHT_IN_O18:
        pruefe(p in p11, "Odoo 11 hatte %s" % p)
        pruefe(p not in p18, "Odoo 18 hat %s nicht (dokumentiert)" % p)

    print("\n5) Nutzungszahlen Odoo 11 (read-only)")
    for modell, domain, soll_min in (("sale.order", [], 2400),
                                     ("sale.order.line", [], 4000),
                                     ("product.template", [], 600),
                                     ("product.pricelist", [], 40),
                                     ("crm.team", [], 8),
                                     ("report.all.channels.sales", [], 3000)):
        n = k11.kw(modell, "search_count", [domain])
        pruefe(n >= soll_min, "Odoo 11 %s: %d (mindestens %d erwartet)" % (modell, n, soll_min))

    print("\n6) Module Odoo 18 (lokal und VM)")
    for name, kl in (("lokal", k18), ("VM", kvm)):
        mods = {m["name"]: m for m in kl.kw("ir.module.module", "search_read",
                                            [[["name", "in", ["sale", "sale_management", "sales_team",
                                                              "sale_order_line_number", "itk_sale_management",
                                                              "itk_saleorder_lines", "itk_reports"]]],
                                             ["name", "state", "latest_version"]])}
        pruefe(all(m in mods and mods[m]["state"] == "installed" for m in
                   ("sale", "sale_management", "itk_sale_management", "itk_saleorder_lines")),
               "%s: sale/sale_management/itk_sale_management/itk_saleorder_lines installiert" % name)

    print("\n%d OK / %d FEHL" % (ok, fehler))
    print("Odoo 11 Prod wurde ausschliesslich lesend verwendet.")
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
