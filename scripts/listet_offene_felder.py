"""Listet alle noch nicht dokumentierten belegten Odoo-11-Felder und prueft sie in Odoo 18."""
import glob
import io
import sys

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}
k11, k18 = o11(), o18("vm")

doku = ""
for datei in glob.glob(r"C:/Odoo-Test/docs/o11-o18-*.md") + glob.glob(r"C:/Odoo-Test/docs/*abrechnung*.md"):
    doku += io.open(datei, encoding="utf-8").read()

OHNE = {"id", "create_uid", "create_date", "write_uid", "write_date", "__last_update", "display_name"}

for modell in ("res.partner", "product.template"):
    felder11 = k11.kw(modell, "fields_get", [[], ["type", "compute", "related", "store", "string", "relation"]], context=CTX)
    felder18 = k18.kw(modell, "fields_get", [[], ["type", "string"]], context=CTX)
    gesamt = k11.kw(modell, "search_count", [[]], context=CTX)
    print("=== %s (belegt von %d) ===" % (modell, gesamt))
    for name, info in sorted(felder11.items()):
        if info.get("type") in ("binary", "image") or name in OHNE:
            continue
        if info.get("compute") or info.get("related") or info.get("store") is False:
            continue
        if name in doku:
            continue
        anzahl = k11.kw(modell, "search_count", [[[name, "!=", False]]], context=CTX)
        if not anzahl:
            continue
        in18 = "vorhanden" if name in felder18 else "FEHLT in Odoo 18"
        print("   %-28s %5d/%-5d  %-38s %s" % (name, anzahl, gesamt, (info.get("string") or "")[:38], in18))
