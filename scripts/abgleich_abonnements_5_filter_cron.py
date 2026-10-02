"""Abonnement-Neuabgleich (Schritt 5): Filter, Gruppierungen, Listen und Cronjobs.

Aufruf: python scripts/abgleich_abonnements_5_filter_cron.py
Nur lesend.
"""
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}
k11, k18 = o11(), o18("vm")

for client, name in ((k11, "Odoo 11"), (k18, "Odoo 18")):
    print("########## %s ##########" % name)
    for view in client.kw("ir.ui.view", "search_read",
                          [[["model", "=", "sale.subscription"], ["type", "=", "search"]],
                           ["name", "arch"]], context=CTX):
        try:
            wurzel = ET.fromstring(view["arch"])
        except Exception:
            continue
        print("  Suche %s:" % view["name"])
        for tag in ("filter", "group", "field"):
            for el in wurzel.iter(tag):
                attrs = []
                for schluessel in ("name", "string", "domain", "context", "invisible"):
                    if el.get(schluessel):
                        attrs.append("%s=%s" % (schluessel, el.get(schluessel)))
                if attrs:
                    print("      %-7s %s" % (tag, " | ".join(attrs)))
    print("  Listen-Spalten (tree):")
    for view in client.kw("ir.ui.view", "search_read",
                          [[["model", "=", "sale.subscription"], ["type", "=", "tree"]],
                           ["name", "arch"]], context=CTX):
        try:
            wurzel = ET.fromstring(view["arch"])
        except Exception:
            continue
        spalten = [f.get("name") for f in wurzel.iter("field") if f.get("name")]
        print("      %-34s %s" % (view["name"], ", ".join(spalten)))
    print("  Cronjobs Abonnement:")
    for cron in client.kw("ir.cron", "search_read",
                          [[["name", "ilike", "subscri"]], ["name", "interval_number", "interval_type",
                                                            "nextcall", "active", "model_id"]],
                          context=CTX):
        print("      %-42s alle %s %s  aktiv=%s  Modell=%s"
              % (cron["name"], cron["interval_number"], cron["interval_type"], cron["active"],
                 cron["model_id"] and cron["model_id"][1]))
    print()
