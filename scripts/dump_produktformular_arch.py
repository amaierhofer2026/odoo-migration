"""Roh-Arch des Produktformulars beider Instanzen sichern und Schluesselstellen melden (read-only)."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vergleich_abo_produktformular as V  # noqa: E402

ZIEL = os.environ.get("TEMP", ".").replace("\\", "/") + "/aboform"
os.makedirs(ZIEL, exist_ok=True)

MUSTER = ["property_account_income_id", "property_account_expense_id", "chatter", "oe_chatter",
          'name="notes"', 'name="invoicing"', "product_image_ids", "image_1920", "product_document_count",
          "Bilder", "Abrechnung", "Notizen", "route_ids", "responsible_id", "service_policy",
          "description_picking", "item_ids", "optional_product_ids", "accessory_product_ids",
          "alternative_product_ids", "public_categ_ids", "available_threshold", "custom_message",
          "inventory_availability", "invoice_policy", "service_tracking", "project_id", "taxes_id",
          "categ_id", "group_account", "groups=", "<chatter"]

for name, instanz in (("o11", "o11"), ("o18", "lokal")):
    kw = V.client(instanz)
    arch, _views = V.hol_arch(kw, "product.template", "form", {"lang": "de_DE"})
    p = ZIEL + "/" + name + "_form_arch.xml"
    with open(p, "w", encoding="utf-8") as f:
        f.write(arch)
    print("%s: %d Zeichen -> %s" % (name, len(arch), p))
    for m in MUSTER:
        n = len(re.findall(re.escape(m), arch))
        if n:
            print("   %-34s %d" % (m, n))
    print()

# Gruppen des verwendeten Benutzers je Instanz (erklaert ggf. fehlende Abschnitte)
for name, instanz in (("o11", "o11"), ("o18", "lokal")):
    kw = V.client(instanz)
    u = kw("res.users", "search_read", [[["login", "=", "anna.maierhofer@it-kommunal.at"]],
                                        ["id", "login", "groups_id", "lang", "tz"]], context={"lang": "de_DE"})
    if isinstance(u, list) and u:
        g = kw("res.groups", "read", [u[0]["groups_id"], ["full_name"]], context={"lang": "de_DE"})
        namen = sorted(x.get("full_name") or "" for x in g)
        treffer = [n for n in namen if any(w in n.lower() for w in ("account", "buchh", "rechnung", "stock", "lager", "purchase", "einkauf", "sales", "verkauf", "technisch", "settings", "einstellung", "website"))]
        print("%s Benutzer id=%s lang=%s tz=%s Gruppen=%d" % (name, u[0]["id"], u[0].get("lang"), u[0].get("tz"), len(namen)))
        for n in treffer:
            print("   %s" % n)
    else:
        print("%s Benutzer nicht gefunden: %s" % (name, u))
    print()
