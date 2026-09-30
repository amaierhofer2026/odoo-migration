"""Gezielter Migrations-Check Verkauf: Feld-fuer-Feld-Zuordnung Odoo 11 -> Odoo 18.

NUR LESEND. Odoo 11 Prod wird ausschliesslich gelesen, Odoo 18 wird nicht veraendert.

Je Feld von sale.order und sale.order.line:

  Odoo-11-Feld -> technischer Name -> Odoo-18-Zielfeld -> technischer Name
  -> Transformationsbedarf -> Status

Statuswerte:
  1:1_vorhanden
  umbenannt
  an_anderer_stelle_dargestellt
  durch_odoo18_funktion_ersetzt
  transformationsregel_erforderlich
  bewusst_nicht_zu_uebernehmen
  fehlende_zuordnung        (Odoo-11-Feld mit Belegung, in Odoo 18 nicht vorhanden)

Zusaetzlich wird je Feld geprueft, ob der gespeicherte Wert fachlich identisch erhalten bleibt:
Typgleichheit, Auswahlwerte (Selection-Schluessel), Relation, Wertebereich (Stichproben),
gespeichert vs. berechnet, Firmenabhaengigkeit (jsonb).

Ausgabe: docs/_verkauf_migrationscheck_felder.json (Analyseartefakt, gitignoriert) + Kurzbericht.

Aufruf:
    python scripts/analyse_verkauf_migrationscheck_felder.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELLE = ["sale.order", "sale.order.line"]
SP = {"lang": "de_DE"}

# Odoo-11-Feld -> Odoo-18-Feld (bekannte Umbenennungen, aus Teil 2)
UMBENANNT = {
    "amt_invoiced": "amount_invoiced",
    "amt_to_invoice": "amount_to_invoice",
    "amt_untaxed": "amount_untaxed",
    "price_reduce": "price_reduce",
    "invoice_lines": "invoice_lines",
    "note": "note",
    "layout_category_id": None,          # in Odoo 18 entfernt (tote Funktion)
    "layout_category_sequence": None,
}

# Felder, die in Odoo 18 zwar existieren, aber an anderer Stelle dargestellt werden
ANDERE_STELLE = {
    "confirmation_date": "Bestaetigungsdatum (Odoo 18: date_order bleibt Auftragsdatum)",
    "payment_term_id": "identisch, Anzeige im Reiter Weitere Informationen",
}

# Odoo-11-Felder ohne fachliche Uebernahme (dokumentiert in Teil 1/2/5)
NICHT_ZU_UEBERNEHMEN = {
    "layout_category_id": "Tote Odoo-11-Funktion (sale.layout.category nicht registriert)",
    "layout_category_sequence": "Tote Odoo-11-Funktion (Reportlayout-Kategorien)",
    "website_order_line": "Website-Bestellzeile (Website-Funktion in Odoo 11 nicht genutzt)",
    "utm_*": "UTM-Quellen in Odoo 11 ohne Verwendung",
}

# Relation-Ziele, die sich zwischen Odoo 11 und Odoo 18 unterscheiden
RELATION_MAPPING = {
    "account.invoice": "account.move",
    "account.invoice.line": "account.move.line",
    "account.tax": "account.tax",
    "crm.lead.tag": "crm.tag",
    "product.uom": "uom.uom",
    "product.packaging": "product.packaging",
    "sale.layout.category": None,
    "stock.warehouse": "stock.warehouse",
    "crm.team": "crm.team",
    "account.payment.term": "account.payment.term",
    "account.analytic.account": "account.analytic.account",
    "product.pricelist": "product.pricelist",
}

# Odoo-11-Felder, die in Odoo 18 durch eine Funktion ersetzt sind
ERSETZT_DURCH_FUNKTION = {
    "state": None,   # Zustand bleibt, aber Sperre laeuft ueber 'locked'
    "locked": "Sperre des Auftrags (Odoo 11: Zustand 'done')",
    "invoice_status": "unveraendert (Odoo-Standard)",
}

ATTRS = ["name", "field_description", "ttype", "relation", "required", "readonly", "store",
         "related", "modules", "translate", "company_dependent", "state", "compute"]


def felder(k, modell: str) -> dict:
    imf = k.kw("ir.model.fields", "search_read", [[["model", "=", modell]], ATTRS], order="name",
               context=SP)
    fg = k.kw(modell, "fields_get", [[], ["string", "type", "relation", "selection"]], context=SP)
    out = {}
    for f in imf:
        name = f["name"]
        anzeige = fg.get(name) or {}
        info = {
            "beschriftung": anzeige.get("string") or f.get("field_description"),
            "ttype": f.get("ttype"),
            "relation": f.get("relation") or None,
            "gespeichert": bool(f.get("store")),
            "berechnet": bool(f.get("compute")),
            "related": f.get("related") or None,
            "pflicht": bool(f.get("required")),
            "readonly": bool(f.get("readonly")),
            "firmenabhaengig": bool(f.get("company_dependent")),
            "uebersetzbar": bool(f.get("translate")),
            "module": f.get("modules") or "",
        }
        sel = anzeige.get("selection")
        if sel:
            info["selection"] = [[str(a), str(b)] for a, b in sel]
        out[name] = info
    return out


def belegung(k, modell: str, felder_d: dict) -> dict:
    """Wie viele Datensaetze fuehren je Feld einen Wert?"""
    gesamt = k.kw(modell, "search_count", [[]])
    zahlen = {}
    for name, info in felder_d.items():
        if not info["gespeichert"] or info["related"]:
            continue
        if info["ttype"] in ("one2many", "many2many"):
            try:
                n = k.kw(modell, "search_count", [[(name, "!=", False)]])
            except Exception:
                n = None
        elif info["ttype"] in ("integer", "float", "monetary"):
            n = k.kw(modell, "search_count", [[(name, "!=", 0)]])
        elif info["ttype"] in ("char", "text", "html", "selection", "many2one", "date",
                               "datetime", "binary"):
            n = k.kw(modell, "search_count", [[(name, "!=", False)]])
        elif info["ttype"] == "boolean":
            n = k.kw(modell, "search_count", [[(name, "=", True)]])
        else:
            n = None
        zahlen[name] = {"belegt": n, "gesamt": gesamt}
    return zahlen


def stichproben(k, modell: str, felder_d: dict, n: int = 5) -> dict:
    """Beispielwerte je belegtem Feld, um fachliche Bedeutung und Transformationsbedarf zu sehen."""
    wichtig = [f for f, i in felder_d.items()
               if i["gespeichert"] and not i["related"]
               and i["ttype"] in ("char", "text", "selection", "date", "datetime", "many2one",
                                  "float", "monetary", "integer")]
    out = {}
    for f in wichtig:
        try:
            daten = k.kw(modell, "search_read", [[(f, "!=", False)], [f]], limit=n, context=SP,
                         order="id desc")
            werte = []
            for d in daten:
                w = d.get(f)
                if isinstance(w, list):
                    w = w[1] if len(w) > 1 else w
                werte.append(w)
            if any(w not in (None, False, "") for w in werte):
                out[f] = werte
        except Exception:
            pass
    return out


def status(feld: str, o11: dict, o18: dict | None) -> tuple[str, list[str]]:
    hinweise: list[str] = []
    if feld in NICHT_ZU_UEBERNEHMEN:
        return "bewusst_nicht_zu_uebernehmen", [NICHT_ZU_UEBERNEHMEN[feld]]
    if feld.startswith("utm_"):
        return "bewusst_nicht_zu_uebernehmen", [NICHT_ZU_UEBERNEHMEN["utm_*"]]
    ziel = UMBENANNT.get(feld, feld)
    if ziel is None:
        return "bewusst_nicht_zu_uebernehmen", ["In Odoo 18 entfernt (tote Funktion)"]
    if o18 is None:
        return "fehlende_zuordnung", ["Feld in Odoo 18 nicht vorhanden"]
    s = "1:1_vorhanden"
    if ziel != feld:
        s = "umbenannt"
        hinweise.append("Name in Odoo 18: %s" % ziel)
    if o11["ttype"] != o18["ttype"]:
        s = "transformationsregel_erforderlich"
        hinweise.append("Typ Odoo 11 %s -> Odoo 18 %s" % (o11["ttype"], o18["ttype"]))
    if o11.get("relation") and o18.get("relation") and o11["relation"] != o18["relation"]:
        s = "transformationsregel_erforderlich"
        hinweise.append("Relation %s -> %s" % (o11["relation"], o18["relation"]))
    if o11.get("selection") and o18.get("selection"):
        k11 = {a for a, _ in o11["selection"]}
        k18 = {a for a, _ in o18["selection"]}
        fehlend = k11 - k18
        if fehlend:
            s = "transformationsregel_erforderlich"
            hinweise.append("Auswahlwerte ohne Entsprechung in Odoo 18: %s" % sorted(fehlend))
    if feld == "state":
        hinweise.append("Zustand bleibt, Sperre laeuft in Odoo 18 ueber Feld 'locked'")
        if s == "1:1_vorhanden":
            s = "durch_odoo18_funktion_ersetzt"
    if feld in ERSETZT_DURCH_FUNKTION and ERSETZT_DURCH_FUNKTION[feld]:
        hinweise.append(ERSETZT_DURCH_FUNKTION[feld])
    if feld in ANDERE_STELLE:
        hinweise.append(ANDERE_STELLE[feld])
        if s == "1:1_vorhanden":
            s = "an_anderer_stelle_dargestellt"
    return s, hinweise


def main() -> int:
    print("Gezielter Migrations-Check Verkauf (nur lesend)")
    k11, k18l, k18v = o11(), o18("lokal"), o18("vm")

    ergebnis = {"hinweis": "Nur Analyse, keine Aenderung, keine Datenmigration",
                "modelle": {}}
    for modell in MODELLE:
        print("=" * 78)
        print(modell)
        f11 = felder(k11, modell)
        f18l = felder(k18l, modell)
        f18v = felder(k18v, modell)
        blg = belegung(k11, modell, f11)
        stp = stichproben(k11, modell, f11)

        zeilen = []
        for name in sorted(f11):
            info11 = f11[name]
            ziel = UMBENANNT.get(name, name)
            info18 = f18l.get(ziel) if ziel else None
            belegt = (blg.get(name) or {}).get("belegt")
            if belegt in (0, None) and name not in ("id",):
                # unbelegte Felder nur kurz fuehren (kein Migrationsrisiko)
                zeilen.append({"o11_feld": name, "o11_technisch": name,
                               "o18_feld": ziel, "o18_technisch": ziel if info18 else None,
                               "o11_beschriftung": info11["beschriftung"],
                               "o11_typ": info11["ttype"], "o11_relation": info11["relation"],
                               "belegt": belegt, "gesamt": (blg.get(name) or {}).get("gesamt"),
                               "status": "unbelegt_kein_risiko",
                               "hinweise": ["Feld in Odoo 11 ohne Wert"],
                               "werte": stp.get(name, [])})
                continue
            s, h = status(name, info11, info18)
            zeilen.append({
                "o11_feld": name, "o11_technisch": name,
                "o18_feld": (info18 or {}).get("beschriftung") if info18 else None,
                "o18_technisch": ziel if info18 else None,
                "o11_beschriftung": info11["beschriftung"],
                "o11_typ": info11["ttype"], "o11_relation": info11["relation"],
                "o11_gespeichert": info11["gespeichert"], "o11_berechnet": info11["berechnet"],
                "o18_typ": (info18 or {}).get("ttype"),
                "o18_relation": (info18 or {}).get("relation"),
                "o18_gespeichert": (info18 or {}).get("gespeichert"),
                "o18_berechnet": (info18 or {}).get("berechnet"),
                "o18_firmenabhaengig": (info18 or {}).get("firmenabhaengig"),
                "belegt": belegt, "gesamt": (blg.get(name) or {}).get("gesamt"),
                "status": s, "hinweise": h, "werte": stp.get(name, [])[:5],
                "auswahl_o11": info11.get("selection"),
                "auswahl_o18": (info18 or {}).get("selection"),
            })
        ergebnis["modelle"][modell] = zeilen

        risiken = [z for z in zeilen if z["status"] in
                   ("fehlende_zuordnung", "transformationsregel_erforderlich")]
        print("Felder gesamt: %d | belegt: %d | unbelegt: %d"
              % (len(zeilen), sum(1 for z in zeilen if z["belegt"]), 
                 sum(1 for z in zeilen if z["status"] == "unbelegt_kein_risiko")))
        print("Risiken/Klaerungsbedarf: %d" % len(risiken))
        for z in risiken:
            print("  %-26s %-32s belegt %s/%s" % (z["o11_technisch"], z["status"],
                                                  z["belegt"], z["gesamt"]))
            for h in z["hinweise"]:
                print("      - %s" % h)

    pfad = os.path.join(REPO, "docs", "_verkauf_migrationscheck_felder.json")
    with open(pfad, "w", encoding="utf-8") as fh:
        json.dump(ergebnis, fh, ensure_ascii=False, indent=1)
    print()
    print("Rohdaten: %s" % pfad)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
