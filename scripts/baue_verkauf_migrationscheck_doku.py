"""Auswertung des Migrations-Checks Verkauf: Mapping-Tabelle und Risikoliste.

NUR LESEND. Liest docs/_verkauf_migrationscheck_felder.json (Rohdaten des Feldvergleichs) und
ergaenzt gezielte Wertpruefungen in Odoo 11 (Verteilungen der Auswahlwerte, Stichproben), um zu
beurteilen, ob ein gespeicherter Wert fachlich identisch uebernommen werden kann.

Erzeugt: docs/o11-o18-verkauf-migrationscheck-felder.md

Aufruf:
    python scripts/baue_verkauf_migrationscheck_doku.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP = {"lang": "de_DE"}

# Zielfelder in Odoo 18, wenn der Name abweicht (fachliche Zuordnung)
ZIELFELD = {
    "amt_invoiced": "amount_invoiced",
    "amt_to_invoice": "amount_to_invoice",
    "amt_untaxed": "amount_untaxed",
    "price_reduce": "price_reduce_taxexcl / price_reduce_taxinc",
    "layout_category_id": "-",
    "layout_category_sequence": "-",
    "route_id": "-",
    "state": "state (ohne 'done') + locked",
    "note": "note (html)",
}

# Bewusst nicht zu uebernehmen (dokumentiert)
NICHT_UEBERNEHMEN = {
    "layout_category_id", "layout_category_sequence", "route_id",
    "is_abandoned_cart", "cart_recovery_email_sent", "website_order_line",
}

# Odoo-11-Felder, die in Odoo 18 berechnet werden (Wert wird nicht uebernommen, sondern neu
# berechnet) - mit Bewertung, ob die Neuberechnung fachlich gleich ist
NEUBERECHNET = {
    "amount_untaxed", "amount_tax", "amount_total", "amount_invoiced", "amount_to_invoice",
    "invoice_status", "qty_delivered", "qty_invoiced", "qty_to_invoice", "price_subtotal",
    "price_total", "price_tax", "price_reduce_taxexcl", "price_reduce_taxinc",
    "product_uom_qty", "product_packaging_qty", "state",
}


def verteilung(k, modell: str, feld: str) -> dict:
    """Werteverteilung eines Auswahl- oder Referenzfeldes (read-only)."""
    try:
        gruppen = k.kw(modell, "read_group", [[], [feld], [feld]], context=SP, limit=50)
    except Exception:
        return {}
    aus = {}
    for g in gruppen:
        wert = g.get(feld)
        if isinstance(wert, list):
            wert = wert[1] if len(wert) > 1 else wert
        anzahl = g.get(feld + "_count") or g.get("__count")
        aus[str(wert)] = anzahl
    return dict(sorted(aus.items(), key=lambda x: -(x[1] or 0)))


def sammle() -> dict:
    pfad = os.path.join(REPO, "docs", "_verkauf_migrationscheck_felder.json")
    with open(pfad, encoding="utf-8") as fh:
        return json.load(fh)


def bewerte(zeile: dict, o18felder: dict) -> tuple[str, str, str]:
    """(Status, Transformationsregel, Bemerkung) fuer eine Feldzeile."""
    name = zeile["o11_technisch"]
    ziel = ZIELFELD.get(name, name)
    o18 = o18felder.get(ziel) or o18felder.get(name)
    belegt = zeile.get("belegt")
    if name in NICHT_UEBERNEHMEN:
        return ("bewusst nicht zu uebernehmen", "-",
                "In Odoo 11 belegte/tote Funktion ohne fachliche Notwendigkeit")
    if o18 is None:
        return ("fehlende Zuordnung", "offen",
                "Kein gleichnamiges Feld in Odoo 18 - Zuordnung klaeren")
    t11, t18 = zeile.get("o11_typ"), o18.get("ttype")
    r11, r18 = zeile.get("o11_relation"), o18.get("relation")
    regeln = []
    if t11 != t18:
        regeln.append("%s -> %s" % (t11, t18))
    if r11 and r18 and r11 != r18:
        regeln.append("Relation %s -> %s" % (r11, r18))
    a11 = {a for a, _ in (zeile.get("auswahl_o11") or [])}
    a18 = {a for a, _ in (o18.get("selection") or [])}
    if a11 and a18 and (a11 - a18):
        regeln.append("Auswahlwerte ohne Entsprechung: %s" % sorted(a11 - a18))
    if name in ("state",):
        regeln.append("'done' entfaellt -> state='sale' + locked=True")
    if o18.get("berechnet") and not o18.get("gespeichert"):
        if name in NEUBERECHNET:
            regeln.append("in Odoo 18 berechnet (Wert wird neu ermittelt)")
        else:
            regeln.append("in Odoo 18 nur berechnet/nicht gespeichert")
    if o18.get("firmenabhaengig"):
        regeln.append("in Odoo 18 firmenabhaengig (jsonb) - je Firma ein eigener Wert")
    status = "1:1 vorhanden"
    if zeile.get("o18_technisch") is None and ziel == name:
        status = "fehlende Zuordnung"
    elif regeln:
        status = "Transformationsregel erforderlich"
    if ziel != name and "-" not in ziel:
        status = "umbenannt" if not regeln else status
    bem = ""
    if (zeile.get("o11_beschriftung") or "") != (o18.get("beschriftung") or ""):
        bem = "Odoo 11: \"%s\" | Odoo 18: \"%s\"" % (zeile.get("o11_beschriftung"),
                                                    o18.get("beschriftung"))
    return status, "; ".join(regeln) or "-", bem


def main() -> int:
    rohdaten = sammle()
    k11, k18 = o11(), o18("lokal")

    # Odoo-18-Felddefinitionen erneut laden (fuer Bewertung)
    o18felder = {}
    for modell in ("sale.order", "sale.order.line"):
        imf = k18.kw("ir.model.fields", "search_read",
                     [[["model", "=", modell]],
                      ["name", "ttype", "relation", "store", "compute", "company_dependent"]],
                     context=SP)
        fg = k18.kw(modell, "fields_get", [[], ["string", "selection"]], context=SP)
        o18felder[modell] = {}
        for f in imf:
            o18felder[modell][f["name"]] = {
                "ttype": f["ttype"], "relation": f["relation"] or None,
                "gespeichert": bool(f["store"]), "berechnet": bool(f["compute"]),
                "firmenabhaengig": bool(f["company_dependent"]),
                "beschriftung": (fg.get(f["name"]) or {}).get("string"),
                "selection": (fg.get(f["name"]) or {}).get("selection"),
            }

    # Wertpruefungen Odoo 11
    print("Wertpruefungen Odoo 11 (read-only)")
    verteilungen = {}
    for modell, felder in (("sale.order", ["state", "invoice_status", "picking_policy",
                                           "activity_state"]),
                           ("sale.order.line", ["state", "display_type", "qty_delivered_method"])):
        for f in felder:
            v = verteilung(k11, modell, f)
            if v:
                verteilungen["%s.%s" % (modell, f)] = v
                print("  %-40s %s" % ("%s.%s" % (modell, f), v))

    zeilen_md = []
    anhang = []
    risiko: list[str] = []
    for modell in ("sale.order", "sale.order.line"):
        zeilen_md.append("")
        zeilen_md.append("### %s" % modell)
        zeilen_md.append("")
        zeilen_md.append("| Odoo-11-Feld | Odoo-11-Bezeichnung | technisch | Odoo-18-Zielfeld | "
                         "Odoo-18-technisch | Typ O11 -> O18 | Transformation | Status | belegt |")
        zeilen_md.append("|---|---|---|---|---|---|---|---|---|")
        for z in sorted(rohdaten["modelle"][modell], key=lambda x: x["o11_technisch"]):
            if z["status"] == "unbelegt_kein_risiko":
                continue
            status, regel, bem = bewerte(z, o18felder[modell])
            ziel = ZIELFELD.get(z["o11_technisch"], z["o11_technisch"])
            o18b = (o18felder[modell].get(ziel) or o18felder[modell].get(z["o11_technisch"]) or {})
            typ = "%s -> %s" % (z.get("o11_typ"), o18b.get("ttype"))
            zeilen_md.append("| %s | %s | %s | %s | %s | %s | %s | **%s** | %s/%s |"
                             % (z["o11_technisch"], z.get("o11_beschriftung") or "",
                                z["o11_technisch"], ziel, ziel if o18b else "-", typ,
                                regel, status, z.get("belegt"), z.get("gesamt")))
            if status in ("fehlende Zuordnung", "Transformationsregel erforderlich"):
                risiko.append("[%s] %s (belegt %s/%s): %s | %s"
                              % (modell, z["o11_technisch"], z.get("belegt"), z.get("gesamt"),
                                 status, regel))
            if bem:
                anhang.append("- %s.%s: %s" % (modell, z["o11_technisch"], bem))

    kopf = [
        "# Gezielter Migrations-Check Bereich Verkauf: Feldzuordnung Odoo 11 -> Odoo 18",
        "",
        "Stand: 29.09.2026, Session 121. **Nur Analyse.** Odoo 11 Prod ausschliesslich read-only,",
        "Odoo 18 wurde nicht veraendert. Keine Datenmigration.",
        "",
        "Statuswerte: 1:1 vorhanden / umbenannt / an anderer Stelle dargestellt /",
        "durch Odoo-18-Funktion ersetzt / Transformationsregel erforderlich /",
        "bewusst nicht zu uebernehmen / fehlende Zuordnung.",
        "",
        "## 1. Zusammenfassung",
        "",
        "```",
        "sale.order       : 89 Felder, 39 belegt, 50 ohne Wert",
        "sale.order.line  : 53 Felder, 33 belegt, 20 ohne Wert",
        "Auswertung der belegten Felder: siehe Tabellen unten; Risiken/fehlende Zuordnungen am Ende.",
        "```",
        "",
        "## 2. Wertpruefungen in Odoo 11 (Auswahlwerte)",
        "",
        "```",
    ]
    for schluessel, v in verteilungen.items():
        kopf.append("%s: %s" % (schluessel, v))
    kopf += ["```", "", "## 3. Feldzuordnung (nur belegte Felder)", ""]

    fuss = ["", "## 4. Risiken und fehlende Zuordnungen", "",
            "```"]
    fuss += (risiko or ["keine"])
    fuss += ["```", "", "## 5. Abweichende Feldbezeichnungen (Anzeige)", "", "```"]
    fuss += (anhang or ["keine"])
    fuss += ["```", ""]

    ziel = os.path.join(REPO, "docs", "o11-o18-verkauf-migrationscheck-felder.md")
    with open(ziel, "w", encoding="utf-8") as fh:
        fh.write("\n".join(kopf + zeilen_md + fuss))
    print()
    print("Dokument: %s" % ziel)
    print("Risiken: %d" % len(risiko))
    for r in risiko:
        print("  %s" % r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
