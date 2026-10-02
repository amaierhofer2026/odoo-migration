"""ITK-Produktfilter: Funktion, Nutzung und betroffene Datensaetze in Odoo 11 - und Lage in Odoo 18.

Aufruf: python scripts/analysiere_itk_produktfilter.py
Nur lesend.
"""
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}
k11, k18 = o11(), o18("vm")

arch = k11.kw("product.template", "fields_view_get", [False, "search"], context=CTX)["arch"]
w = ET.fromstring(arch)
gesamt11 = k11.kw("product.template", "search_count", [[]], context=CTX)
gesamt18 = k18.kw("product.template", "search_count", [[]], context=CTX)
print("Produkte: Odoo 11 %d | Odoo 18 %d (Testbestand)\n" % (gesamt11, gesamt18))

print("%-34s %-52s %s" % ("Filter", "Domain in Odoo 11", "Treffer in Odoo 11"))
print("-" * 104)
ohne_zaehlung = []
for f in w.iter("filter"):
    label = (f.get("string") or "").strip()
    domain = (f.get("domain") or "").strip()
    if not label or not domain:
        continue
    if "context_today" in domain or "uid" in domain:
        ohne_zaehlung.append(label)
        continue
    try:
        geparst = eval(domain, {"__builtins__": {}}, {})       # nur die Domain-Liste
        anzahl = k11.kw("product.template", "search_count", [geparst], context=CTX)
    except Exception as fehler:
        anzahl = "Fehler: %s" % str(fehler)[:30]
    print("%-34s %-52s %s" % (label[:34], domain[:52], anzahl))

print("\nOhne Zaehlung (Kontext/Datum): %s" % ohne_zaehlung)

print("\n--- Felder hinter den ITK-Filtern ---")
for feld in ("product_type_id", "invoice_policy", "service_type", "qty_available",
             "sale_ok", "purchase_ok", "website_published", "type"):
    info11 = k11.kw("product.template", "fields_get", [[feld], ["string", "type", "selection"]], context=CTX).get(feld)
    info18 = k18.kw("product.template", "fields_get", [[feld], ["string", "type", "selection"]], context=CTX).get(feld)
    belegt11 = k11.kw("product.template", "search_count", [[[feld, "!=", False]]], context=CTX)
    zeile = "   %-20s Odoo 11: %-38s belegt %4d/%d | Odoo 18: %s" % (
        feld, ("%s" % (info11.get("string") if info11 else "FELD FEHLT"))[:38], belegt11, gesamt11,
        (info18.get("string") if info18 else "FELD FEHLT"))
    print(zeile)
    if info11 and info11.get("selection") and feld == "product_type_id":
        werte11 = []
        for wert, beschriftung in info11["selection"]:
            anzahl = k11.kw("product.template", "search_count", [[[feld, "=", wert]]], context=CTX)
            if anzahl:
                werte11.append("%s=%d" % (beschriftung, anzahl))
        print("        Odoo 11 Verteilung: %s" % ", ".join(werte11))
    if info18 and info18.get("selection") and feld == "product_type_id":
        werte18 = []
        for wert, beschriftung in info18["selection"]:
            anzahl = k18.kw("product.template", "search_count", [[[feld, "=", wert]]], context=CTX)
            if anzahl:
                werte18.append("%s=%d" % (beschriftung, anzahl))
        print("        Odoo 18 Verteilung: %s" % (", ".join(werte18) or "keine Werte im Testbestand"))

print("\n--- Produktsuche Odoo 18: vorhandene Filter ---")
arch18 = list((k18.kw("product.template", "get_views", [[[False, "search"]]], context=CTX).get("views") or {}).values())[0]["arch"]
w18 = ET.fromstring(arch18)
for f in w18.iter("filter"):
    label = (f.get("string") or "").strip()
    if not label:
        continue
    if (f.get("context") or "").find("group_by") >= 0:
        continue
    print("   %-34s %s" % (label[:34], (f.get("domain") or "")[:56]))
