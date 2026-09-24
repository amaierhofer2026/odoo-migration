"""Exakte Nutzung der Produktformular-Felder in Odoo 11 Prod (read-only).

Statt Domain-Zaehlungen (bei one2many/many2many unzuverlaessig) werden die Feldwerte
gelesen und in Python gezaehlt.  Zusaetzlich: ir.property (Unternehmens-Standardwerte)
und die Konten der Produktkategorien in Odoo 11 und Odoo 18.

Aufruf: python scripts/analyse_o11_produktformular_nutzung.py
"""
from __future__ import annotations

import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vergleich_abo_produktformular_felder as F  # noqa: E402

SP = {"lang": "de_DE"}

EINFACH = [
    ("weight", "Gewicht"), ("volume", "Volumen"), ("sale_delay", "Auslieferungszeit"),
    ("responsible_id", "Verantwortlich"), ("tracking", "Nachverfolgung"),
    ("invoice_policy", "Fakturierungsregel"), ("service_type", "Dienstleistungsverfolgung"),
    ("service_tracking", "Dienstverfolgung"), ("sale_line_warn", "Auftragswarnung"),
    ("purchase_line_warn", "Bestellwarnung"), ("purchase_method", "Kontrollrichtlinie"),
    ("inventory_availability", "Lagerverfuegbarkeit"), ("custom_message", "Persoenliche Nachricht"),
    ("available_threshold", "Verfuegbarkeitsgrenze"), ("is_multi_factor_product", "Faktor-Flag"),
    ("recurring_invoice", "Abonnement Produkt"), ("subscription_template_id", "Abo-Vorlage"),
    ("project_id", "Projekt"), ("property_valuation", "Bewertungsart"), ("property_cost_method", "Kalkulationsverfahren"),
    ("valuation", "Bewertung (Anzeige)"), ("cost_method", "Kostenmethode (Anzeige)"),
    ("property_stock_production", "Produktionslager"), ("property_stock_inventory", "Inventurlager"),
    ("property_account_income_id", "Erloeskonto"), ("property_account_expense_id", "Aufwandskonto"),
    ("property_account_creditor_price_difference", "Preisdifferenzkonto"),
    ("property_stock_account_input", "Konto Wareneingang"), ("property_stock_account_output", "Konto Warenversand"),
    ("taxes_id", "Steuern Verkauf"), ("supplier_taxes_id", "Steuern Einkauf"),
]
TEXT = [("description", "Beschreibung"), ("description_sale", "Verkaufsbeschreibung"),
        ("description_purchase", "Einkaufsbeschreibung"), ("description_pickingout", "Beschreibung Lieferauftrag"),
        ("description_pickingin", "Beschreibung Wareneingang"), ("description_picking", "Beschreibung Kommissionierung"),
        ("sale_line_warn_msg", "Auftragswarnung Text"), ("purchase_line_warn_msg", "Bestellwarnung Text")]
X2MANY = [("route_ids", "Routen"), ("packaging_ids", "Verpackungen"), ("item_ids", "Preislistenpositionen"),
          ("seller_ids", "Lieferanten"), ("product_image_ids", "Zusatzbilder"),
          ("public_categ_ids", "eCommerce-Kategorien"), ("website_style_ids", "Website-Stile"),
          ("accessory_product_ids", "Zubehoer"), ("alternative_product_ids", "Alternativprodukte")]


def leer(w):
    return w in (False, None, "", 0, 0.0, [], "no", "never", "no-message", "order", "manual", "purchase")


def main() -> int:
    k11 = F.client("o11")
    k18 = F.client("lokal")

    zeilen = k11("sale.subscription.line", "search_read", [[], ["product_id"]], context=SP)
    abo = {t["product_id"][0] for t in zeilen if t.get("product_id")} if isinstance(zeilen, list) else set()

    felder = [f for f, _ in EINFACH] + [f for f, _ in TEXT] + [f for f, _ in X2MANY]
    daten = k11("product.template", "search_read", [[], ["id", "name", "default_code", "type", "recurring_invoice"] + felder],
                context=SP, limit=0)
    if not isinstance(daten, list):
        print("Lesefehler product.template: %s" % daten)
        return 1
    vorhandene = {f: sum(1 for d in daten if f in d) for f in felder}
    fehlende = [f for f, n in vorhandene.items() if n == 0]
    gesamt = len(daten)
    print("=== Nutzung der Produktformular-Felder in Odoo 11 Prod (read-only) ===")
    print("Produkte (product.template): %d | davon in Abonnements verwendet: %d" % (gesamt, len(abo)))
    if fehlende:
        print("nicht vorhandene Felder (in dieser Instanz nicht definiert): %s" % ", ".join(fehlende))
    print()

    print("--- Einfache Felder: Anzahl Produkte mit gefuelltem / abweichendem Wert ---")
    print("%-42s %-28s %10s %10s  %s" % ("Feld", "Bedeutung", "gesamt", "in Abos", "Werte"))
    for f, bed in EINFACH:
        if f not in vorhandene or not vorhandene[f]:
            print("   %-39s %-28s %10s %10s  (Feld fehlt)" % (f, bed, "-", "-"))
            continue
        g = [d.get(f) for d in daten]
        ng = sum(1 for w in g if not leer(w))
        na = sum(1 for d in daten if d["id"] in abo and not leer(d.get(f)))
        haeufig = collections.Counter(str(w) for w in g if not leer(w)).most_common(3)
        print("   %-39s %-28s %10d %10d  %s" % (f, bed, ng, na, haeufig))

    print("\n--- Textfelder: Anzahl Produkte mit nicht leerem Text ---")
    print("%-42s %-28s %10s %10s  %s" % ("Feld", "Bedeutung", "gesamt", "in Abos", "Beispiel"))
    for f, bed in TEXT:
        if f not in vorhandene or not vorhandene[f]:
            print("   %-39s %-28s %10s %10s  (Feld fehlt)" % (f, bed, "-", "-"))
            continue
        g = [d.get(f) for d in daten if isinstance(d.get(f), str) and d.get(f).strip()]
        a = [d for d in daten if d["id"] in abo and isinstance(d.get(f), str) and d.get(f).strip()]
        bsp = (g[0].strip().replace("\n", " ")[:34] if g else "-")
        print("   %-39s %-28s %10d %10d  %s" % (f, bed, len(g), len(a), bsp))

    print("\n--- one2many/many2many: Anzahl Produkte mit mindestens einem Eintrag ---")
    print("%-42s %-28s %10s %10s" % ("Feld", "Bedeutung", "gesamt", "in Abos"))
    for f, bed in X2MANY:
        if f not in vorhandene or not vorhandene[f]:
            print("   %-39s %-28s %10s %10s  (Feld fehlt)" % (f, bed, "-", "-"))
            continue
        g = sum(1 for d in daten if d.get(f))
        a = sum(1 for d in daten if d["id"] in abo and d.get(f))
        print("   %-39s %-28s %10d %10d" % (f, bed, g, a))

    print("\n--- Verteilung Produktart (type) und Abo-Flag ---")
    print("   type: %s" % collections.Counter(d.get("type") for d in daten).most_common())
    print("   recurring_invoice=True: %d (davon in Abos verwendet: %d)" % (
        sum(1 for d in daten if d.get("recurring_invoice")),
        sum(1 for d in daten if d["id"] in abo and d.get("recurring_invoice"))))

    print("\n--- ir.property: Unternehmens-Standardwerte fuer Produktfelder (Odoo 11) ---")
    ids = k11("ir.model.fields", "search_read",
              [[["model", "=", "product.template"], ["name", "in", [f for f, _ in EINFACH]]], ["id", "name"]],
              context=SP)
    if isinstance(ids, list) and ids:
        m = {x["id"]: x["name"] for x in ids}
        pr = k11("ir.property", "search_read", [[["fields_id", "in", list(m)]], ["fields_id", "res_id", "company_id", "value_text", "value_reference"]],
                 context=SP, limit=0)
        zaehler = collections.Counter()
        for p in pr or []:
            zaehler[m.get(p["fields_id"][0] if p["fields_id"] else 0, "?")] += 1
        for f, n in sorted(zaehler.items()):
            print("   %-42s %d ir.property-Saetze" % (f, n))
        if not zaehler:
            print("   (keine)")
    else:
        print("   ir.model.fields nicht lesbar: %s" % str(ids)[:120])

    print("\n--- Produktkategorien: Konten (Odoo 11 gegen Odoo 18) ---")
    for name, kw in (("o11", k11), ("o18", k18)):
        kat = kw("product.category", "search_read", [[], ["id", "name"]], context=SP)
        print("   %s: %d Kategorien" % (name, len(kat) if isinstance(kat, list) else -1))
        for feld in ("property_account_income_categ_id", "property_account_expense_categ_id",
                     "property_account_income_id", "property_account_expense_id"):
            ff = kw("ir.model.fields", "search_read",
                    [[["model", "=", "product.category"], ["name", "=", feld]], ["id"]], context=SP)
            if isinstance(ff, list) and ff:
                pr = kw("ir.property", "search_read", [[["fields_id", "=", ff[0]["id"]]], ["res_id", "value_reference"]],
                        context=SP, limit=0)
                s = [p.get("value_reference") for p in (pr or []) if p.get("value_reference")]
                print("      %-38s Feld vorhanden, %d Konto-Zuordnungen %s" % (feld, len(s), s[:5]))
            else:
                print("      %-38s Feld NICHT vorhanden" % feld)

    print("\n--- Modulzustaende Ergaenzung Odoo 18 ---")
    zus = k18("ir.module.module", "search_read",
              [[["name", "in", ["sale_project", "sale_timesheet", "project", "hr_timesheet", "website_sale",
                                "product", "stock", "stock_account", "sale_stock", "account"]]],
               ["name", "state", "installed_version"]], context=SP)
    for m in sorted(zus, key=lambda x: x["name"]):
        print("   %-16s %-14s %s" % (m["name"], m["state"], m["installed_version"] or "-"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
