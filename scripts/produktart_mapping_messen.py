"""Produktart / product_type_id: datenbasierte Bestandsaufnahme (read-only).

Odoo 11 Prod (nur lesende Aufrufe) und Odoo 18 lokal/VM:
  A) Auswahlwerte und Beschriftungen der Felder type und product_type_id
  B) Anzahl Produkte je Wert (alle / aktiv / archiviert)
  C) tatsaechlich verwendete Produkte (in Belegzeilen) je Wert
  D) Zielmodell der Produktart (itk_product.product_type) mit Datensaetzen
  E) Abhaengigkeiten: Filter, Ansichten, Automationen, Serveraktionen, andere Modelle

Aufruf: python scripts/produktart_mapping_messen.py [o11|lokal|vm|alle]
Schreibt JSON nach $LOCALAPPDATA/Temp/produktart/<instanz>.json (keine Daten im Repo).
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}
ZIEL = os.path.join(os.environ.get("LOCALAPPDATA", "/tmp"), "Temp", "produktart")
os.makedirs(ZIEL, exist_ok=True)

ITK_WERTE = ["consu", "service", "general", "onlineservice", "sw", "consulting",
             "platform", "hw", "project", "product"]


def felder(k, modell, feldnamen):
    return k.kw(modell, "fields_get", [feldnamen, ["string", "type", "relation",
                                                   "selection", "required", "help"]])


def werteliste(sel):
    if not sel:
        return []
    return [{"wert": w, "bezeichnung": b} for w, b in sel]


def gruppieren(k, modell, feld):
    try:
        erw = k.kw(modell, "read_group", [[], [feld], [feld]])
    except RuntimeError as fehler:
        return {"fehler": str(fehler)[:200]}
    aus = []
    for zeile in erw:
        w = zeile.get(feld)
        aus.append({"wert": w[1] if isinstance(w, (list, tuple)) else w,
                    "id": w[0] if isinstance(w, (list, tuple)) else None,
                    "anzahl": zeile.get(feld + "_count")})
    aus.sort(key=lambda x: -(x["anzahl"] or 0))
    return aus


def belegprodukte(k, modelle):
    """Je Belegmodell die Menge der verwendeten product.product-IDs."""
    gesamt = set()
    einzeln = {}
    for modell, feld in modelle:
        try:
            erw = k.kw(modell, "read_group", [[], [feld], [feld]])
        except RuntimeError:
            einzeln[modell] = None
            continue
        ids = [z[feld][0] for z in erw
               if isinstance(z.get(feld), (list, tuple)) and z[feld][0]]
        einzeln[modell] = {"zeilengruppen": len(erw), "produkte": len(ids)}
        gesamt.update(ids)
    return sorted(gesamt), einzeln


def nutzung_je_wert(k, tmpl_feld, produkt_ids):
    """Verwendete Produkte (product.product) auf Produktart ihres Templates abbilden."""
    if not produkt_ids:
        return {}
    paare = k.kw("product.product", "read", [produkt_ids, ["product_tmpl_id"]])
    tmpls = sorted({p["product_tmpl_id"][0] for p in paare if p.get("product_tmpl_id")})
    daten = k.kw("product.template", "read", [tmpls, [tmpl_feld]])
    tmpl_wert = {d["id"]: d.get(tmpl_feld) for d in daten}
    zaehler = {}
    gesehen = set()
    for p in paare:
        t = p["product_tmpl_id"][0] if p.get("product_tmpl_id") else None
        if t in gesehen:
            continue
        gesehen.add(t)
        w = tmpl_wert.get(t)
        schluessel = w[1] if isinstance(w, (list, tuple)) else w
        schluessel = schluessel if schluessel not in (None, False) else "(leer)"
        zaehler[schluessel] = zaehler.get(schluessel, 0) + 1
    return dict(sorted(zaehler.items(), key=lambda x: -x[1]))


def abhaengigkeiten(k, ist_o11):
    aus = {}
    # 1. Filter (ir.filters)
    try:
        fs = k.kw("ir.filters", "search_read", [[], ["name", "model_id", "domain", "context"]])
        treffer = []
        for f in fs:
            text = "%s %s" % (f.get("domain") or "", f.get("context") or "")
            if "product_type" in text or any("'%s'" % w in text for w in ITK_WERTE[:8]):
                treffer.append({"name": f.get("name"), "model": f.get("model_id") and f["model_id"][1],
                                "domain": f.get("domain"), "context": f.get("context")})
        aus["ir.filters_gesamt"] = len(fs)
        aus["ir.filters_treffer"] = treffer
    except RuntimeError as fehler:
        aus["ir.filters_gesamt"] = "Fehler: %s" % str(fehler)[:120]
    # 2. Ansichten mit product_type_id oder fest verdrahteten Auswahlwerten
    for feldname in ("arch_db", "arch"):
        try:
            vs = k.kw("ir.ui.view", "search_read",
                      [[(feldname, "ilike", "product_type_id")], ["name", "model"]])
            aus["ansichten_mit_product_type_id"] = [
                {"name": v.get("name"), "model": v.get("model")} for v in vs]
            break
        except RuntimeError as fehler:
            aus["ansichten_mit_product_type_id"] = "Fehler %s: %s" % (feldname, str(fehler)[:100])
    verdrahtet = []
    for wert in ("onlineservice", "platform", "consulting", "'sw'", "'hw'", "'project'"):
        for feldname in ("arch_db", "arch"):
            try:
                vs = k.kw("ir.ui.view", "search_read",
                          [[(feldname, "ilike", wert)], ["name", "model"]])
                verdrahtet.append({"wert": wert, "ansichten": [v.get("name") for v in vs]})
                break
            except RuntimeError:
                continue
    aus["ansichten_mit_festem_auswahlwert"] = verdrahtet
    # 3. Serveraktionen / Automationen
    treffer = []
    for modell, felder_ in (("ir.actions.server", ["name", "code"]),
                            ("base.automation", ["name", "code"])):
        try:
            sa = k.kw(modell, "search_read", [[], felder_])
        except RuntimeError:
            continue
        for s in sa:
            text = " ".join(str(s.get(f) or "") for f in felder_)
            if "product_type" in text or "recurring_invoice" in text:
                treffer.append({"modell": modell, "name": s.get("name")})
    aus["aktionen_und_automationen"] = treffer
    # 4. Modelle mit einem Feld product_type_id
    try:
        fs = k.kw("ir.model.fields", "search_read",
                  [[("name", "=", "product_type_id")], ["model", "field_description", "ttype",
                                                        "relation", "module", "store"]])
        aus["felder_product_type_id"] = fs
    except RuntimeError as fehler:
        aus["felder_product_type_id"] = "Fehler: %s" % str(fehler)[:120]
    # 5. Felder mit Namen type auf Produktmodellen (Auswahlwerte anderer Module)
    try:
        fs = k.kw("ir.model.fields", "search_read",
                  [[("model", "in", ["product.template", "product.product"]), ("name", "=", "type")],
                   ["model", "field_description", "ttype", "selection", "module", "required"]])
        aus["feld_type"] = fs
    except RuntimeError as fehler:
        aus["feld_type"] = "Fehler: %s" % str(fehler)[:120]
    return aus


def produktarten_model(k):
    """itk_product.product_type: vorhandene Produktarten."""
    for modellname in ("itk_product.product_type", "product.type"):
        try:
            felder_ = k.kw(modellname, "fields_get", [[], ["string", "type", "relation"]])
            namen = [n for n in felder_ if n not in ("create_uid", "create_date", "write_uid",
                                                     "write_date", "display_name", "__last_update")]
            daten = k.kw(modellname, "search_read", [[], namen[:14]])
            return {"modell": modellname, "felder": {n: felder_[n]["string"] for n in namen[:14]},
                    "datensaetze": daten, "anzahl": len(daten)}
        except RuntimeError:
            continue
    return {"modell": None, "datensaetze": []}


def lauf(instanz):
    k = o11() if instanz == "o11" else o18(instanz)
    ist_o11 = instanz == "o11"
    bericht = {"instanz": instanz}
    f = felder(k, "product.template", ["type", "product_type_id"])
    bericht["feld_type"] = {kk: {a: (werteliste(v) if a == "selection" else v)
                                 for a, v in vv.items()}
                            for kk, vv in f.items() if kk in ("type", "product_type_id")}
    bericht["type_alle"] = gruppieren(k, "product.template", "type")
    try:
        bericht["type_aktiv"] = gruppieren(k, "product.template", "type")
    except RuntimeError:
        pass
    bericht["product_type_id_gruppen"] = gruppieren(k, "product.template", "product_type_id")
    bericht["produktarten"] = produktarten_model(k)
    if ist_o11:
        belege = [("account.move.line", "product_id"), ("account.invoice.line", "product_id"),
                  ("sale.order.line", "product_id"), ("sale.subscription.line", "product_id"),
                  ("stock.move", "product_id"), ("purchase.order.line", "product_id")]
    else:
        belege = [("account.move.line", "product_id"), ("sale.order.line", "product_id"),
                  ("sale.order.line", "product_template_id"),
                  ("sale.subscription.line", "product_id"), ("stock.move", "product_id"),
                  ("purchase.order.line", "product_id")]
    ids, einzeln = belegprodukte(k, belege)
    bericht["belegmodelle"] = einzeln
    bericht["verwendete_produkte_gesamt"] = len(ids)
    bericht["verwendet_je_type"] = nutzung_je_wert(k, "type", ids)
    bericht["verwendet_je_product_type_id"] = nutzung_je_wert(k, "product_type_id", ids)
    bericht["abhaengigkeiten"] = abhaengigkeiten(k, ist_o11)
    ziel = os.path.join(ZIEL, "%s.json" % instanz)
    with open(ziel, "w", encoding="utf-8") as fh:
        json.dump(bericht, fh, ensure_ascii=False, indent=1, default=str)
    print("\n=== %s ===" % instanz.upper())
    print("Auswahl type:", [(w["wert"], w["bezeichnung"])
                            for w in bericht["feld_type"].get("type", {}).get("selection", [])])
    print("Auswahl product_type_id-Ziel:",
          bericht["feld_type"].get("product_type_id", {}).get("relation"))
    print("Produkte je type:", bericht["type_alle"])
    print("Produkte je product_type_id:", bericht["product_type_id_gruppen"])
    print("Produktarten-Datensaetze (%s): %d" % (bericht["produktarten"]["modell"],
                                                 bericht["produktarten"]["anzahl"]))
    for d in bericht["produktarten"]["datensaetze"]:
        print("   ", {kk: d[kk] for kk in list(d)[:5]})
    print("verwendete Produkte gesamt:", len(ids))
    print("verwendet je type:", bericht["verwendet_je_type"])
    print("verwendet je product_type_id:", bericht["verwendet_je_product_type_id"])
    a = bericht["abhaengigkeiten"]
    print("Filter gesamt:", a.get("ir.filters_gesamt"), "| Treffer:", len(a.get("ir.filters_treffer") or []))
    print("Ansichten mit product_type_id:", a.get("ansichten_mit_product_type_id"))
    print("Ansichten mit festem Auswahlwert:", a.get("ansichten_mit_festem_auswahlwert"))
    print("Aktionen/Automationen:", a.get("aktionen_und_automationen"))
    fpt = a.get("felder_product_type_id")
    print("Felder product_type_id:", fpt if isinstance(fpt, str) else
          [(x.get("model"), x.get("module"), x.get("relation"), x.get("ttype")) for x in fpt])
    print("gespeichert:", ziel)
    return bericht


if __name__ == "__main__":
    was = sys.argv[1] if len(sys.argv) > 1 else "alle"
    for inst in (["o11", "lokal", "vm"] if was == "alle" else [was]):
        lauf(inst)
