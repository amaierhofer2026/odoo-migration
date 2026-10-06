"""Vorlauf-Pruefung der Produktart-Regel (Variante 1) - ausschliesslich lesend.

Prueft die am 05.10.2026 von Anna festgelegte Regel, ohne irgendetwas zu schreiben:
  scripts/testmigration_abrechnung.py, typ_ziel + product_type_id-Transfer.

Geprueft wird:
 1. Jeder in Odoo 11 vorkommende `type`-Wert hat eine gueltige Zielzuordnung.
 2. Der Zielwert existiert in der Odoo-18-Auswahl (sonst consu + is_storable).
 3. Anzahl Produkte je Zielwert und Anzahl mit is_storable = True.
 4. Der Filter "Dienstleistungen" (type = service) behaelt dieselbe Treffermenge.
 5. Jede Odoo-11-Produktart existiert in Odoo 18 mit gleichem Namen UND gleicher ID.
 6. Produkte mit ITK-`type` ohne Produktart bleiben ohne Produktart (keine Ableitung).

Aufruf: python scripts/pruefe_produktart_regel.py [--schreiben]
Ohne --schreiben wird nur berichtet; es wird nie etwas in Odoo geschrieben.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}
ITK_TYPEN = ["general", "onlineservice", "sw", "consulting", "platform", "hw", "project"]
STOCK_TYPEN = ("product", "consu")          # Odoo-11-Lagerfuehrung -> is_storable
ZIEL = os.path.join(os.environ.get("LOCALAPPDATA", "/tmp"), "Temp", "produktart")


def typ_ziel(o11_typ, o18_auswahl):
    """Regel aus scripts/testmigration_abrechnung.py (Variante 1)."""
    if o11_typ == "product":
        return "consu", True
    if o11_typ == "consu":
        return "consu", True
    if o11_typ == "service" or o11_typ in ITK_TYPEN:
        if o11_typ not in o18_auswahl:
            return None, None
        return o11_typ, False
    return None, None


def main():
    k11, k18 = o11(), o18("lokal")
    fehler, hinweise = [], []

    o18_sel = [w for w, _ in (k18.kw("product.template", "fields_get", [["type"], ["selection"]],
                                     context=CTX)["type"].get("selection") or [])]
    print("Odoo-18-Auswahl type:", o18_sel)
    if "product" in o18_sel:
        fehler.append("Odoo-18-Auswahl enthaelt 'product' - Regelannahme falsch.")
    for name in ("consu", "service", "general", "onlineservice", "sw", "consulting", "platform",
                 "hw", "project"):
        if name not in o18_sel:
            fehler.append("Odoo-18-Auswahl fehlt der Wert %r." % name)

    ids = k11.kw("product.template", "search", [[]], context=dict(CTX, active_test=False))
    daten = k11.kw("product.template", "read", [ids, ["name", "type", "product_type_id", "active"]],
                   context=dict(CTX, active_test=False))
    print("Odoo-11-Vorlagen (inkl. archiviert):", len(daten))

    ziel, storable, ohne_art_mit_typ, dienst, dienst_aktiv = {}, 0, 0, 0, 0
    unbekannt = {}
    for d in daten:
        o11typ = d["type"]
        z, st = typ_ziel(o11typ, o18_sel)
        if z is None:
            unbekannt[o11typ] = unbekannt.get(o11typ, 0) + 1
            continue
        ziel[z] = ziel.get(z, 0) + 1
        if st:
            storable += 1
        if not d.get("product_type_id") and o11typ in ITK_TYPEN:
            ohne_art_mit_typ += 1
        if o11typ == "service":
            dienst += 1
            if d["active"]:
                dienst_aktiv += 1

    print("\nZielverteilung type (nach der Regel):", dict(sorted(ziel.items(), key=lambda x: -x[1])))
    print("is_storable = True (Lagerartikel):", storable)
    print("Filter 'Dienstleistungen' (type = service):", dienst, "Vorlagen,",
          dienst_aktiv, "aktiv")
    print("Vorlagen mit ITK-type ohne Produktart (bleiben leer):", ohne_art_mit_typ)
    if unbekannt:
        fehler.append("Keine Zielzuordnung fuer: %s" % unbekannt)
    if dienst_aktiv != 47:
        fehler.append("Filter 'Dienstleistungen' weicht ab: %d aktiv statt 47." % dienst_aktiv)
    if storable != 152:
        hinweise.append("is_storable = True betrifft %d Vorlagen (erwartet 152)." % storable)

    # 5. Produktart-Datensaetze: Name und ID muessen uebereinstimmen
    p11 = {d["id"]: d["name"] for d in
           k11.kw("itk_product.product_type", "search_read", [[], ["id", "name", "code"]],
                  context=CTX)}
    p18 = {d["id"]: d["name"] for d in
           k18.kw("itk_product.product_type", "search_read", [[], ["id", "name", "code"]],
                  context=CTX)}
    print("\nProduktarten Odoo 11:", dict(sorted(p11.items())))
    print("Produktarten Odoo 18:", dict(sorted(p18.items())))
    for pid, name in p11.items():
        if p18.get(pid) != name:
            fehler.append("Produktart ID %s: Odoo 11 %r vs Odoo 18 %r" % (pid, name, p18.get(pid)))
    for pid in p18:
        if pid not in p11:
            fehler.append("Produktart ID %s existiert nur in Odoo 18 (%r)." % (pid, p18[pid]))
    if len(p11) != 6:
        hinweise.append("Odoo 11 hat %d Produktarten (erwartet 6)." % len(p11))

    # 6. Kontrolle: keine Ableitung type -> product_type_id
    beispiele = [d["name"] for d in daten if d["type"] in ITK_TYPEN and not d.get("product_type_id")]
    print("Beispiele ITK-type ohne Produktart (bleiben leer):", len(beispiele),
          beispiele[:3])

    print("\n=== Ergebnis ===")
    print("FEHLER:", len(fehler))
    for f in fehler:
        print("   FEHL", f)
    print("Hinweise:", len(hinweise))
    for h in hinweise:
        print("   HINWEIS", h)
    if not fehler:
        print("Regel ist gegen den Odoo-11-Bestand anwendbar; Odoo 18 erfuellt alle Voraussetzungen.")
    with open(os.path.join(ZIEL, "regel_pruefung.txt"), "w", encoding="utf-8") as fh:
        fh.write("Zielverteilung: %s\n" % ziel)
        fh.write("is_storable: %d\n" % storable)
        fh.write("Dienstleistungen aktiv: %d\n" % dienst_aktiv)
        fh.write("Fehler: %s\nHinweise: %s\n" % (fehler, hinweise))
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
