# -*- coding: utf-8 -*-
"""Produkte: Migrationsskript Odoo 11 -> Odoo 18.

Teil des ITK-Migrationsprojekts, erstellt unter Freigabe von Anna Maierhofer (11.11.2026).
Quelle: Odoo 11 Prod `ITK_V1_a` - ausschliesslich lesend. Ziel: Odoo 18.

Umfang (vollstaendiger fachlicher Bereich):
- product.category: 31 Kategorien inkl. Hierarchie
- product.template: 658 Vorlagen (consu 155, general 277, onlineservice 74, platform 94,
  sw 10, service 48 - die ITK-Typen sind in Odoo 18 ueber itk_product vorhanden)
- Produktvarianten: Odoo 11 fuehrt 0 Attributzeilen, Odoo 18 legt je Vorlage automatisch
  eine Variante an - keine separate Variantenmigration noetig.

Idempotenz: technisches Feld `itk_o11_id` (Modul itk_migration_keys).

Aufruf (Trockenlauf ist Standard und schreibt nichts):
    python scripts/migration/produkte_migration.py --instanz lokal
    python scripts/migration/produkte_migration.py --instanz lokal --ausfuehren --ich-habe-freigabe
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HIER))
import _o11o18_client as client  # noqa: E402

BATCH = 50


class Schreibschutz:
    SCHREIBEND = {"create", "write", "unlink", "copy"}

    def __init__(self, client_, schreiben: bool):
        self._client = client_
        self._schreiben = schreiben

    def kw(self, modell, methode, args, **kwargs):
        if not self._schreiben and methode in self.SCHREIBEND:
            raise RuntimeError("Schreibaufruf im Trockenlauf: %s.%s" % (modell, methode))
        return self._client.kw(modell, methode, args, **kwargs)


def text_nach_html(text):
    if not text:
        return False
    if "<p>" in text or "<br" in text or "<div" in text:
        return text
    import html as _html
    vereinheitlicht = text.replace(chr(13) + chr(10), chr(10))
    zeilen = [z.strip() for z in vereinheitlicht.split(chr(10))]
    return "".join("<p>%s</p>" % _html.escape(z) if z else "<p><br></p>" for z in zeilen)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    ap.add_argument("--ausfuehren", action="store_true")
    ap.add_argument("--ich-habe-freigabe", action="store_true")
    ap.add_argument("--grenze", type=int, default=0)
    ap.add_argument("--mapping")
    args = ap.parse_args()

    if args.ausfuehren and not args.ich_habe_freigabe:
        print("ABBRUCH: Schreiblauf nur mit --ich-habe-freigabe (Freigabe von Anna).")
        return 2

    o11 = client.o11()
    ziel = Schreibschutz(client.o18(args.instanz), args.ausfuehren)
    print("=== Produkte-Migration %s | %s ===" % (
        args.instanz, "SCHREIBEN" if args.ausfuehren else "TROCKENLAUF (schreibt nichts)"))

    kats = o11.kw("product.category", "search_read", [[], ["id", "name", "parent_id"]],
                  order="id", limit=500, context={"active_test": False})
    felder = ["id", "name", "type", "categ_id", "uom_id", "uom_po_id", "list_price",
              "standard_price", "description", "description_sale", "description_purchase",
              "barcode", "default_code", "sale_ok", "purchase_ok", "invoice_policy",
              "taxes_id", "supplier_taxes_id", "product_type_id", "responsible_id", "active"]
    tmpl = o11.kw("product.template", "search_read", [[]], fields=felder, order="id", limit=2000,
                  context={"active_test": False})
    if args.grenze:
        tmpl = tmpl[:args.grenze]

    stat = {"kat_gelesen": len(kats), "kat_neu": 0, "kat_da": 0,
            "gelesen": len(tmpl), "neu": 0, "da": 0, "uebersprungen": 0,
            "ohne_kategorie": 0, "steuer_nicht_gefunden": 0, "fehler": 0}
    mapping = {"kategorien": [], "produkte": []}

    # Bestand (inkl. archivierter)
    kat_bestand = {r["itk_o11_id"]: r["id"] for r in
                   ziel.kw("product.category", "search_read",
                           [[["itk_o11_id", "!=", False]], ["id", "itk_o11_id"]], limit=500,
                           context={"active_test": False})}
    tmpl_bestand = {r["itk_o11_id"]: r["id"] for r in
                    ziel.kw("product.template", "search_read",
                            [[["itk_o11_id", "!=", False]], ["id", "itk_o11_id"]], limit=5000,
                            context={"active_test": False})}
    # Steuern: Odoo 11 und Odoo 18 benennen die Steuern unterschiedlich. Die Zuordnung
    # erfolgt fachlich ueber Satz + Verwendungsart + Steuergruppe + Repartition-Konto und
    # schliesst Sonderfaelle (EU, Reverse Charge, Intra-Community) aus.
    # Belegte Zuordnung (12.11.2026, lokal und VM):
    #   20% Umsatzsteuer -> Odoo-18-Steuer 15 "20% Ust"   (Konto 3500 VAT 20%)
    #   20% Vorsteuer    -> Odoo-18-Steuer 43 "20% Vst"   (Konto 2500 Input tax 20%)
    #   NICHT 57 "20% Vst EU" (Konto 2505 "Other tax 13%") - das ist ein EU-Sonderfall.
    steuern18 = ziel.kw("account.tax", "search_read",
                        [[], ["id", "name", "amount", "type_tax_use", "tax_group_id",
                              "invoice_repartition_line_ids"]], limit=600,
                        context={"active_test": False})
    steuern11 = o11.kw("account.tax", "search_read",
                       [[], ["id", "name", "amount", "type_tax_use"]], limit=600,
                       context={"active_test": False})
    SONDERFALL = ("eu", "rc", "intra", "reverse", "oss", "import", "export")

    def _norm(s):
        return "".join(ch for ch in (s or "").lower() if ch.isalnum())

    def _repartition_konten(tax):
        ids = tax.get("invoice_repartition_line_ids") or []
        if not ids:
            return []
        zeilen = ziel.kw("account.tax.repartition.line", "read",
                         [ids, ["repartition_type", "account_id"]])
        return [(z["account_id"] or [0, ""])[1] for z in zeilen
                if z["repartition_type"] == "tax" and z["account_id"]]

    # Standard-Steuerkonto je Verwendungsart: das Konto, dessen Name den Steuersatz traegt
    # (z. B. "3500 VAT 20%" fuer 20% Verkauf, "2500 Input tax 20%" fuer 20% Vorsteuer).
    # Konten wie "2505 Other tax 13%" gehoeren zu anderen Saetzen oder Sonderfaellen.
    def _konto_passt(konto_name, satz):
        text = (konto_name or "").lower()
        if any(x in text for x in SONDERFALL):
            return False
        satz_text = ("%g" % (satz or 0)).replace(".", ",")
        return ("%g" % (satz or 0)) in text or satz_text in text

    steuer_protokoll = {}
    steuern11_je_id = {t["id"]: t for t in steuern11}

    def steuer_map(schluessel11):
        rec = steuern11_je_id.get(schluessel11) or next(
            (t for t in steuern11 if t["name"] == schluessel11), None)
        if not rec:
            return None
        kandidaten = [t for t in steuern18
                      if abs((t["amount"] or 0) - (rec["amount"] or 0)) < 0.001
                      and t["type_tax_use"] == rec["type_tax_use"]
                      and not any(x in (t["name"] or "").lower() for x in SONDERFALL)]
        if not kandidaten:
            return None
        mit_konto = [t for t in kandidaten
                     if any(_konto_passt(k, rec["amount"]) for k in _repartition_konten(t))]
        pool = mit_konto or kandidaten
        gewaehlt = min(pool, key=lambda t: (len(t["name"] or ""), t["id"]))
        steuer_protokoll.setdefault(rec["name"], {
            "o18_id": gewaehlt["id"], "o18_name": gewaehlt["name"],
            "betrag": rec["amount"], "konto": _repartition_konten(gewaehlt),
            "kandidaten": len(kandidaten), "mit_standardkonto": len(mit_konto),
            "status": "eindeutig" if len(mit_konto) == 1 else "fachlich begruendet"})
        return gewaehlt["id"]
    typen = {t["code"]: t["id"] for t in
             ziel.kw("itk_product.product_type", "search_read", [[], ["id", "code"]], limit=100)}
    benutzer = {u["login"]: u["id"] for u in
                ziel.kw("res.users", "search_read", [[["active", "in", [True, False]]],
                                                     ["id", "login"]], limit=200)}


    # 0) Mengeneinheiten 1:1 (Odoo 11 product.uom -> Odoo 18 uom.uom)
    # Die ITK-Einheiten ("13 Gemeinden", "15 Gemeinden", ...) sind eigene Bezugseinheiten
    # mit Faktor 1.0 und Rundung 0.01. Sie werden unveraendert uebernommen, damit der
    # fachliche Rechenwert identisch bleibt; `to_multiply_by_factor` ist dafuer nicht
    # noetig (Faktor 1, keine Multiplikation).
    # Odoo 11 nennt das Modell product.uom.categ, Odoo 18 uom.category
    uom_kats = o11.kw("product.uom.categ", "search_read", [[], ["id", "name"]],
                      limit=200, context={"active_test": False})
    uoms11 = o11.kw("product.uom", "search_read",
                    [[], ["id", "name", "category_id", "factor", "rounding", "uom_type", "active"]],
                    limit=500, context={"active_test": False})
    kat18 = {k["name"]: k["id"] for k in
             ziel.kw("uom.category", "search_read", [[], ["id", "name"]], limit=200,
                     context={"active_test": False})}
    for k in uom_kats:
        if k["name"] in kat18:
            continue
        if args.ausfuehren:
            try:
                kat18[k["name"]] = ziel.kw("uom.category", "create", [{"name": k["name"]}])
                kat18[k["name"]] = kat18[k["name"]][0] if isinstance(kat18[k["name"]], list) else kat18[k["name"]]
            except Exception as e:
                stat["fehler"] += 1
                print("  FEHLER UoM-Kategorie %s: %s" % (k["id"], str(e)[-150:]))
        else:
            kat18[k["name"]] = -k["id"]
    einheiten = {e["name"]: e["id"] for e in
                 ziel.kw("uom.uom", "search_read", [[], ["id", "name"]], limit=500,
                         context={"active_test": False})}
    stat["uom_neu"] = 0
    stat["uom_da"] = 0
    # Odoo 18 erlaubt je Kategorie nur EINE Referenzmasseinheit. Die ITK-Einheiten
    # ("13 Gemeinden", "15 Gemeinden", ...) sind eigene Bezugseinheiten mit Faktor 1.0;
    # sie kommen daher in eine eigene Kategorie "ITK Abrechnungseinheit" - erste Einheit
    # als Referenz, alle weiteren mit Faktor 1.0 (Rechenwert bleibt identisch).
    # Die ITK-Einheiten gehoeren fachlich zur Kategorie "Unit" (so fuehrt sie Odoo 11
    # ueberwiegend). Nur so koennen Auftrags- und Abozeilen sie verwenden - Odoo 18
    # verlangt fuer Zeile und Produkt dieselbe Einheitenkategorie.
    itk_kat = kat18.get("Unit") or kat18.get("Units") or kat18.get("ITK Abrechnungseinheit")
    if not itk_kat:
        if args.ausfuehren:
            itk_kat = ziel.kw("uom.category", "create", [{"name": "ITK Abrechnungseinheit"}])
            itk_kat = itk_kat[0] if isinstance(itk_kat, list) else itk_kat
        else:
            itk_kat = -999
        kat18["ITK Abrechnungseinheit"] = itk_kat
    # Hat die Zielkategorie bereits eine Referenzmasseinheit?
    bestand_uoms = ziel.kw("uom.uom", "search_read",
                           [[], ["id", "name", "uom_type", "category_id"]], limit=500,
                           context={"active_test": False})
    referenz_gesetzt = any(u["uom_type"] == "reference"
                           and (u["category_id"] or [0])[0] == itk_kat
                           for u in bestand_uoms if isinstance(itk_kat, int) and itk_kat > 0)
    for u in uoms11:
        if u["name"] in einheiten:
            stat["uom_da"] += 1
            continue
        vals = {"name": u["name"], "factor": u["factor"] or 1.0,
                "rounding": u["rounding"] or 0.01,
                "category_id": itk_kat,
                "uom_type": "bigger" if referenz_gesetzt else "reference"}
        if args.ausfuehren:
            try:
                neu_u = ziel.kw("uom.uom", "create", [vals])
                neu_u = neu_u[0] if isinstance(neu_u, list) else neu_u
                einheiten[u["name"]] = neu_u
                if vals["uom_type"] == "reference":
                    referenz_gesetzt = True
                stat["uom_neu"] += 1
            except Exception as e:
                stat["fehler"] += 1
                print("  FEHLER Einheit o11_id %s: %s" % (u["id"], str(e)[-150:]))
        else:
            einheiten[u["name"]] = -u["id"]
            referenz_gesetzt = True
            stat["uom_neu"] += 1

    einheit_std = (einheiten.get("Units") or einheiten.get("Stück")
                   or next(iter(einheiten.values())))

    # 1) Kategorien hierarchisch
    kat_sorted, offen = [], list(kats)
    while offen:
        for k in list(offen):
            pid = k["parent_id"] and k["parent_id"][0]
            if not pid or any(x["id"] == pid for x in kat_sorted):
                kat_sorted.append(k)
                offen.remove(k)
        if not offen:
            break
    for k in kat_sorted:
        if k["id"] in kat_bestand:
            stat["kat_da"] += 1
            mapping["kategorien"].append({"o11_id": k["id"], "o18_id": kat_bestand[k["id"]]})
            continue
        vals = {"name": k["name"], "itk_o11_id": k["id"]}
        if k["parent_id"] and k["parent_id"][0] in kat_bestand:
            vals["parent_id"] = kat_bestand[k["parent_id"][0]]
        try:
            if args.ausfuehren:
                kid = ziel.kw("product.category", "create", [vals])
                kid = kid[0] if isinstance(kid, list) else kid
            else:
                kid = -k["id"]
            kat_bestand[k["id"]] = kid
            stat["kat_neu"] += 1
            mapping["kategorien"].append({"o11_id": k["id"], "o18_id": kid})
        except Exception as e:
            stat["fehler"] += 1
            print("  FEHLER Kategorie o11_id %s: %s" % (k["id"], str(e)[-200:]))

    # 2) Produktvorlagen
    neu = [p for p in tmpl if p["id"] not in tmpl_bestand]
    stat["da"] = len(tmpl) - len(neu)
    for i in range(0, len(neu), BATCH):
        block = neu[i:i + BATCH]
        vals_list = []
        for p in block:
            vals = {"name": p["name"], "itk_o11_id": p["id"], "type": p["type"],
                    "list_price": p["list_price"], "standard_price": p["standard_price"],
                    "default_code": (p["default_code"] or "").strip() or False,
                    "barcode": (p["barcode"] or "").strip() or False,
                    "description": text_nach_html(p["description"]),
                    "description_sale": p["description_sale"] or False,
                    "description_purchase": p["description_purchase"] or False,
                    "sale_ok": p["sale_ok"], "purchase_ok": p["purchase_ok"],
                    "invoice_policy": p["invoice_policy"] or "order",
                    "active": p["active"],
                    "uom_id": einheit_std, "uom_po_id": einheit_std}
            if p["categ_id"] and p["categ_id"][0] in kat_bestand:
                vals["categ_id"] = kat_bestand[p["categ_id"][0]]
            else:
                stat["ohne_kategorie"] += 1
            if p["uom_id"]:
                u = einheiten.get(p["uom_id"][1])
                if u:
                    vals["uom_id"] = u
                    vals["uom_po_id"] = u
            if p["taxes_id"]:
                ids = [x for x in (steuer_map(n) for n in p["taxes_id"]) if x]
                if ids:
                    vals["taxes_id"] = [(6, 0, ids)]
                else:
                    stat["steuer_nicht_gefunden"] += 1
            if p["supplier_taxes_id"]:
                ids = [x for x in (steuer_map(n) for n in p["supplier_taxes_id"]) if x]
                if ids:
                    vals["supplier_taxes_id"] = [(6, 0, ids)]
            if p["product_type_id"]:
                code = p["product_type_id"][1]
                kandidat = [v for c, v in typen.items() if c and code and c in code] or []
                if kandidat:
                    vals["product_type_id"] = kandidat[0]
            vals_list.append(vals)
        try:
            if args.ausfuehren:
                ids = ziel.kw("product.template", "create", [vals_list])
                if not isinstance(ids, list):
                    ids = [ids]
            else:
                ids = [-p["id"] for p in block]
            for p, nid in zip(block, ids):
                tmpl_bestand[p["id"]] = nid
                stat["neu"] += 1
                mapping["produkte"].append({"o11_id": p["id"], "o18_id": nid})
        except Exception as e:
            stat["fehler"] += 1
            print("  FEHLER Produkt-Block ab o11_id %s: %s" % (block[0]["id"], str(e)[-300:]))

    # 2b) Steuerkorrektur bei bereits migrierten Produkten
    # Fruehere Laeufe haben die Vorsteuer ueber Namensaehnlichkeit der Steuer 57
    # ("20% Vst EU", Konto 2505) zugeordnet. Korrekt ist 43 ("20% Vst", Konto 2500).
    stat["steuer_korrigiert"] = 0
    if args.ausfuehren and tmpl_bestand:
        soll = {}
        for p in tmpl:
            if p["taxes_id"]:
                ids = [x for x in (steuer_map(n) for n in p["taxes_id"]) if x]
                if ids:
                    soll[p["id"]] = ids
        o18_rows = ziel.kw("product.template", "search_read",
                           [[["itk_o11_id", "in", list(soll.keys())]],
                            ["id", "itk_o11_id", "taxes_id"]], limit=2000,
                           context={"active_test": False})
        for row in o18_rows:
            if sorted(row["taxes_id"]) != sorted(soll[row["itk_o11_id"]]):
                try:
                    ziel.kw("product.template", "write",
                            [[row["id"]], {"taxes_id": [(6, 0, soll[row["itk_o11_id"]])]}])
                    stat["steuer_korrigiert"] += 1
                except Exception as e:
                    stat["fehler"] += 1
                    print("  FEHLER Steuerkorrektur %s: %s" % (row["id"], str(e)[-150:]))

    # 3) Varianten: Odoo 11 fuehrt 657 product.product, Odoo 18 legt je Vorlage automatisch
    #    eine Variante an. Die Odoo-11-Varianten-ID wird auf die Variante der zugeordneten
    #    Vorlage geschrieben (itk_o11_id), damit Auftrags- und Preislistenzeilen zuordenbar sind.
    varianten11 = o11.kw("product.product", "search_read", [[], ["id", "product_tmpl_id"]],
                         order="id", limit=2000)
    stat["var_neu"] = 0
    stat["var_da"] = 0
    stat["var_ohne_vorlage"] = 0
    var_map = {}
    for v in varianten11:
        tmpl11 = v["product_tmpl_id"] and v["product_tmpl_id"][0]
        tmpl18 = tmpl_bestand.get(tmpl11)
        if not tmpl18:
            stat["var_ohne_vorlage"] += 1
            continue
        var_map[v["id"]] = tmpl18
    if args.ausfuehren and var_map:
        vorhandene_var = {r["itk_o11_id"]: r["id"] for r in
                          ziel.kw("product.product", "search_read",
                                  [[["itk_o11_id", "!=", False]], ["id", "itk_o11_id"]],
                                  limit=5000, context={"active_test": False})}
        for o11_id, tmpl18 in var_map.items():
            if o11_id in vorhandene_var:
                stat["var_da"] += 1
                continue
            var18 = ziel.kw("product.template", "read", [[tmpl18], ["product_variant_id"]])
            var_id = var18[0]["product_variant_id"]
            if not var_id:
                stat["var_ohne_vorlage"] += 1
                continue
            try:
                ziel.kw("product.product", "write",
                        [[var_id[0]], {"itk_o11_id": o11_id}])
                stat["var_neu"] += 1
            except Exception as e:
                stat["fehler"] += 1
                print("  FEHLER Variante o11_id %s: %s" % (o11_id, str(e)[-200:]))
    else:
        stat["var_neu"] = len(var_map)

    breite = "{:<36}{:>10}"
    print(breite.format("Objekt", "Anzahl"))
    print("-" * 46)
    for k, v in (("Produktkategorien gelesen", stat["kat_gelesen"]),
                 ("davon neu angelegt", stat["kat_neu"]),
                 ("davon bereits vorhanden", stat["kat_da"]),
                 ("Produktvorlagen gelesen", stat["gelesen"]),
                 ("davon neu angelegt", stat["neu"]),
                 ("davon bereits vorhanden", stat["da"]),
                 ("Produktvarianten zugeordnet", stat.get("var_neu", 0)),
                 ("davon bereits vorhanden", stat.get("var_da", 0)),
                 ("Varianten ohne Vorlage", stat.get("var_ohne_vorlage", 0)),
                 ("ohne Kategoriezuordnung", stat["ohne_kategorie"]),
                 ("Steuer nicht zuordenbar", stat["steuer_nicht_gefunden"]),
                 ("Steuer korrigiert (57 -> 43)", stat.get("steuer_korrigiert", 0)),
                 ("nicht zuordenbar", 0),
                 ("Fehler", stat["fehler"])):
        print(breite.format(k, v))
    if steuer_protokoll:
        print("")
        print("Steuerzuordnung Odoo 11 -> Odoo 18 (Betrag, Status):")
        for name, d in sorted(steuer_protokoll.items(), key=lambda x: -x[1]["betrag"]):
            print("   %-40s -> id %-4s %-18s Betrag %-6s Konto %-28s %s"
                  % (name[:40], d["o18_id"], (d["o18_name"] or "")[:18], d["betrag"],
                     ", ".join(d["konto"])[:28], d["status"]))
    if args.mapping:
        with open(args.mapping, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(mapping, fh, ensure_ascii=False)
        print("Mapping geschrieben (nur IDs):", args.mapping)
    print("Modus:", "SCHREIBEN" if args.ausfuehren else "TROCKENLAUF")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
