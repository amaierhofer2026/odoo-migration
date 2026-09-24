"""Abgleich der Produktformular-Felder Odoo 11 Prod gegen Odoo 18 + Nutzungszahlen Odoo 11.

Read-only.  Es werden ausschliesslich Leseaufrufe abgesetzt (fields_get, search_count,
search_read, read).  Auf Odoo 11 Prod wird nichts angelegt, geaendert oder geloescht.

Aufruf:
    python scripts/vergleich_abo_produktformular_felder.py [--o11 o11] [--o18 lokal]

Ausgabe:
    A) Reiter und Buttons beider Seiten (Kurzform)
    B) Felddiff: Odoo-11-Formularfeld -> in Odoo 18 im Formular / nur im Modell / fehlt
    C) Felder, die es nur in Odoo 18 gibt (Zusatzfunktionen, bleiben erhalten)
    D) Modulzustaende beider Instanzen
    E) Nutzung in Odoo 11 je Feld (alle Produkte und die in Abos verwendeten)
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def lade_env(pfad):
    w = {}
    for z in open(pfad, encoding="utf-8"):
        if "=" in z and not z.strip().startswith("#"):
            k, v = z.split("=", 1)
            w[k.strip()] = v.strip().strip('"')
    return w


def client(instanz):
    env = lade_env(os.path.join(REPO, ".env"))
    if instanz == "o11":
        url, db = "https://portal.it-kommunal.at", "ITK_V1_a"
        user, pwd = "anna.maierhofer@it-kommunal.at", env["ODOO11_PWD"]
    elif instanz == "vm":
        url, db = "https://k001959vsx.ipax.at", env["ODOO18_DB"]
        user, pwd = env["ODOO18_USER"], env["ODOO18_PWD"]
    else:
        url, db = "http://localhost:8069", env["ODOO18_DB"]
        user, pwd = env["ODOO18_USER"], env["ODOO18_PWD"]
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def rufe(pfad, params):
        r = urllib.request.Request(url + pfad,
                                   data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": params}).encode(),
                                   headers={"Content-Type": "application/json"})
        with op.open(r, timeout=900) as f:
            return json.loads(f.read().decode())

    a = rufe("/web/session/authenticate", {"db": db, "login": user, "password": pwd})
    if a.get("error"):
        raise SystemExit("Anmeldung %s fehlgeschlagen: %s" % (instanz, str(a["error"])[:200]))

    def kw(model, methode, args, **kwargs):
        o = rufe("/web/dataset/call_kw", {"model": model, "method": methode, "args": args, "kwargs": kwargs})
        if "error" in o:
            return {"__fehler__": str(o["error"].get("data", {}).get("message", o["error"].get("message")))[:180]}
        return o.get("result")

    return kw


def hol_arch(kw, modell, art, sprache):
    for methode, args in (("fields_view_get", [False, art]), ("get_views", [[[False, art]]])):
        e = kw(modell, methode, args, context=sprache)
        if isinstance(e, dict) and e.get("arch"):
            return e["arch"]
        if isinstance(e, dict) and "views" in e:
            for _n, v in e["views"].items():
                if v.get("arch"):
                    return v["arch"]
    return ""


def formular_struktur(arch):
    """Reiter (string), Buttons, Felder je Reiter aus dem gerenderten Arch."""
    root = ET.fromstring(arch)
    seiten, buttons, felder = [], [], []

    def lauf(e, pfad):
        for k in list(e):
            if k.tag == "page":
                seiten.append((k.get("string") or k.get("name") or "?", k.get("name") or ""))
                lauf(k, pfad + [k.get("string") or k.get("name") or "?"])
            elif k.tag == "field":
                felder.append({"name": k.get("name"), "seite": pfad[-1] if pfad else "(ausserhalb)",
                               "string": k.get("string") or "", "invisible": k.get("invisible") or k.get("attrs") or "",
                               "required": k.get("required") or ""})
                lauf(k, pfad)
            elif k.tag == "button":
                buttons.append({"name": k.get("name") or "-", "string": k.get("string") or "",
                                "class": k.get("class") or "", "invisible": k.get("invisible") or k.get("attrs") or "",
                                "smart": "oe_stat_button" in (k.get("class") or "")})
                lauf(k, pfad)
            else:
                lauf(k, pfad)

    lauf(root, [])
    return seiten, buttons, felder


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--o11", default="o11")
    p.add_argument("--o18", default="lokal")
    p.add_argument("--modell", default="product.template")
    p.add_argument("--ausgabe", default="")
    a = p.parse_args()
    z = []

    def s(t=""):
        z.append(t)
        print(t)

    k11, k18 = client(a.o11), client(a.o18)
    sp = {"lang": "de_DE"}

    arch11 = hol_arch(k11, a.modell, "form", sp)
    arch18 = hol_arch(k18, a.modell, "form", sp)
    seiten11, buttons11, felder11 = formular_struktur(arch11)
    seiten18, buttons18, felder18 = formular_struktur(arch18)

    s("=== A) Reiter und Buttons ===")
    s("\nReiter Odoo 11 (%d):" % len(seiten11))
    for i, (st, nm) in enumerate(seiten11, 1):
        s("   %d. %-32s name=%s" % (i, st, nm))
    s("\nReiter Odoo 18 (%d):" % len(seiten18))
    for i, (st, nm) in enumerate(seiten18, 1):
        s("   %d. %-32s name=%s" % (i, st, nm))
    s("\nButtons/Smartbuttons Odoo 11 (%d):" % len(buttons11))
    for b in buttons11:
        s("   %-30s %-32s %s%s" % (b["name"], b["string"] or "-", "SMART " if b["smart"] else "", b["invisible"]))
    s("\nButtons/Smartbuttons Odoo 18 (%d):" % len(buttons18))
    for b in buttons18:
        s("   %-30s %-32s %s%s" % (b["name"], b["string"] or "-", "SMART " if b["smart"] else "", b["invisible"]))

    f11 = {f["name"]: f for f in felder11}
    f18 = {f["name"]: f for f in felder18}
    felder18_modell = k18(a.modell, "fields_get", [[], ["string", "type", "relation", "required", "store", "compute"]], context=sp)
    felder11_modell = k11(a.modell, "fields_get", [[], ["string", "type", "relation", "required", "store"]], context=sp)

    s("\n=== B) Odoo-11-Formularfelder: wo sind sie in Odoo 18? ===")
    s("%-44s %-30s %s" % ("Feld", "Odoo 11 Reiter", "Odoo 18"))
    for n, f in f11.items():
        if n in f18:
            wo = "Formular: Reiter %s" % f18[n]["seite"]
            if f18[n]["invisible"]:
                wo += "  [%s]" % f18[n]["invisible"]
        elif isinstance(felder18_modell, dict) and n in felder18_modell:
            wo = "NUR IM MODELL (nicht im Formular)"
        else:
            wo = "FEHLT in Odoo 18"
        s("   %-41s %-30s %s" % (n, f["seite"], wo))

    s("\n=== C) Felder, die nur Odoo 18 im Formular hat (Zusatz, bleibt erhalten) ===")
    for n, f in f18.items():
        if n not in f11:
            s("   %-44s Reiter %s   typ=%s" % (n, f["seite"], (felder18_modell.get(n, {}) or {}).get("type", "-")))
    s("\n   Felder nur in Odoo 18 im Modell (nicht im Formular):")
    nur18 = sorted(set(felder18_modell) - set(felder11_modell)) if isinstance(felder11_modell, dict) else []
    s("   %s" % ", ".join(nur18))
    nur11 = sorted(set(felder11_modell) - set(felder18_modell)) if isinstance(felder11_modell, dict) else []
    s("\n   Felder nur in Odoo 11 im Modell: %s" % ", ".join(nur11))

    s("\n=== D) Modulzustaende ===")
    for name, kw in ((a.o11, k11), (a.o18, k18)):
        mods = kw("ir.module.module", "search_read", [[["name", "in", ["stock", "stock_account", "sale_stock", "purchase",
                                                                       "purchase_stock", "account", "sale", "sale_management",
                                                                       "sale_subscription", "project", "website_sale", "website",
                                                                       "delivery", "product", "itk_product", "itk_multifactor",
                                                                       "mrp", "hr_timesheet", "sale_timesheet"]]],
                                                     ["name", "state", "installed_version"]], context=sp)
        s("   --- %s ---" % name)
        if isinstance(mods, dict):
            s("      %s" % mods)
            continue
        for m in sorted(mods, key=lambda x: x["name"]):
            s("      %-20s %-14s %s" % (m["name"], m["state"], m["installed_version"] or "-"))

    s("\n=== E) Nutzung in Odoo 11 (read-only gezaehlt) ===")
    abo_ids = []
    zeilen = k11("sale.subscription.line", "search_read", [[], ["product_id"]], context=sp)
    if isinstance(zeilen, list):
        abo_ids = sorted({t["product_id"][0] for t in zeilen if t.get("product_id")})
    s("   in Abos verwendete Produkte: %s" % len(abo_ids))
    pr = [("property_account_income_id", "Erloeskonto gesetzt", [["property_account_income_id", "!=", False]]),
          ("property_account_expense_id", "Aufwandskonto gesetzt", [["property_account_expense_id", "!=", False]]),
          ("property_account_creditor_price_difference", "Preisdifferenzkonto", [["property_account_creditor_price_difference", "!=", False]]),
          ("property_stock_account_input", "Konto Wareneingang", [["property_stock_account_input", "!=", False]]),
          ("property_stock_account_output", "Konto Warenversand", [["property_stock_account_output", "!=", False]]),
          ("property_valuation", "Bewertungsart gesetzt", [["property_valuation", "!=", False]]),
          ("property_stock_production", "Produktionslager", [["property_stock_production", "!=", False]]),
          ("property_stock_inventory", "Inventurlager", [["property_stock_inventory", "!=", False]]),
          ("weight", "Gewicht != 0", [["weight", "!=", 0]]),
          ("volume", "Volumen != 0", [["volume", "!=", 0]]),
          ("responsible_id", "Verantwortlich gesetzt", [["responsible_id", "!=", False]]),
          ("sale_delay", "Auslieferungszeit != 0", [["sale_delay", "!=", 0]]),
          ("tracking", "Nachverfolgung != none", [["tracking", "!=", "none"]]),
          ("invoice_policy", "Fakturierungsregel != order", [["invoice_policy", "!=", "order"]]),
          ("service_type", "Dienstleistungsverfolgung != manual", [["service_type", "!=", "manual"]]),
          ("service_tracking", "Dienstverfolgung != no", [["service_tracking", "!=", "no"]]),
          ("sale_line_warn", "Auftragswarnung != no-message", [["sale_line_warn", "!=", "no-message"]]),
          ("purchase_line_warn", "Bestellwarnung != no-message", [["purchase_line_warn", "!=", "no-message"]]),
          ("purchase_method", "Kontrollrichtlinie != purchase", [["purchase_method", "!=", "purchase"]]),
          ("description", "Beschreibung gefuellt", [["description", "!=", False]]),
          ("description_sale", "Verkaufsbeschreibung gefuellt", [["description_sale", "!=", False]]),
          ("description_purchase", "Einkaufsbeschreibung gefuellt", [["description_purchase", "!=", False]]),
          ("description_pickingout", "Beschreibung Lieferauftrag", [["description_pickingout", "!=", False]]),
          ("description_pickingin", "Beschreibung Wareneingang", [["description_pickingin", "!=", False]]),
          ("description_picking", "Beschreibung Kommissionierung", [["description_picking", "!=", False]]),
          ("inventory_availability", "Lagerverfuegbarkeit != never", [["inventory_availability", "!=", "never"]]),
          ("custom_message", "Persoenliche Nachricht gesetzt", [["custom_message", "!=", False]]),
          ("available_threshold", "Verfuegbarkeitsgrenze != 0", [["available_threshold", "!=", 0]]),
          ("public_categ_ids", "eCommerce-Kategorie gesetzt", [["public_categ_ids", "!=", False]]),
          ("website_style_ids", "Website-Stil gesetzt", [["website_style_ids", "!=", False]]),
          ("alternative_product_ids", "Alternativprodukte", [["alternative_product_ids", "!=", False]]),
          ("accessory_product_ids", "Zubehoer", [["accessory_product_ids", "!=", False]]),
          ("item_ids", "Preislistenposition", [["item_ids", "!=", False]]),
          ("seller_ids", "Lieferant", [["seller_ids", "!=", False]]),
          ("variant_seller_ids", "Verkäufer Variante", [["variant_seller_ids", "!=", False]]),
          ("route_ids", "Route gesetzt", [["route_ids", "!=", False]]),
          ("packaging_ids", "Verpackung", [["packaging_ids", "!=", False]]),
          ("product_image_ids", "Zusatzbilder", [["product_image_ids", "!=", False]]),
          ("is_multi_factor_product", "Faktor-Flag", [["is_multi_factor_product", "=", True]]),
          ("recurring_invoice", "Abonnement Produkt", [["recurring_invoice", "=", True]]),
          ("subscription_template_id", "Abo-Vorlage gesetzt", [["subscription_template_id", "!=", False]]),
          ("project_id", "Projekt gesetzt", [["project_id", "!=", False]]),
          ("currency_id", "Waehrung gesetzt", [["currency_id", "!=", False]]),
          ]
    gesamt = k11(a.modell, "search_count", [[]], context=sp)
    s("   Produkte gesamt (product.template): %s\n" % gesamt)
    s("   %-42s %-26s %8s %8s" % ("Feld", "Bedeutung", "gesamt", "in Abos"))
    for feld, bedeutung, dom in pr:
        try:
            g = k11(a.modell, "search_count", [dom], context=sp)
        except Exception as e:
            g = "Fehler:%s" % e
        if abo_ids:
            try:
                av = k11(a.modell, "search_count", [dom + [["id", "in", abo_ids]]], context=sp)
            except Exception as e:
                av = "Fehler:%s" % e
        else:
            av = "-"
        if isinstance(g, dict) or isinstance(av, dict):
            s("   %-42s %-26s %8s %8s  (nicht abfragbar)" % (feld, bedeutung, g, av))
        else:
            s("   %-42s %-26s %8s %8s" % (feld, bedeutung, g, av))

    if a.ausgabe:
        with open(a.ausgabe, "w", encoding="utf-8") as f:
            f.write("\n".join(z) + "\n")
        print("\n[gespeichert: %s]" % a.ausgabe)
    return 0


if __name__ == "__main__":
    sys.exit(main())
