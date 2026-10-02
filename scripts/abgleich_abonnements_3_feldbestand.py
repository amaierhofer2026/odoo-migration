"""Abonnement-Neuabgleich (Schritt 3): Feldbestand Odoo 11 gegen Odoo 18 (Existenz + Beschriftung).

Aufruf: python scripts/abgleich_abonnements_3_feldbestand.py
Nur lesend.
"""
import sys

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}
k11, k18 = o11(), o18("vm")
MODELLE = ["sale.subscription", "sale.subscription.line", "sale.subscription.template"]
OHNE = {"id", "create_uid", "create_date", "write_uid", "write_date", "__last_update", "display_name"}

for modell in MODELLE:
    a = k11.kw(modell, "fields_get", [[], ["type", "string", "compute", "store", "relation"]], context=CTX)
    b = k18.kw(modell, "fields_get", [[], ["type", "string", "compute", "store", "relation"]], context=CTX)
    fa = {n: i for n, i in a.items() if n not in OHNE and i.get("type") not in ("binary", "image")}
    fb = {n: i for n, i in b.items() if n not in OHNE and i.get("type") not in ("binary", "image")}
    print("=== %s (Odoo 11: %d Felder, Odoo 18: %d Felder) ===" % (modell, len(fa), len(fb)))
    nur11 = sorted(set(fa) - set(fb))
    nur18 = sorted(set(fb) - set(fa))
    print("  nur Odoo 11 (%d): %s" % (len(nur11), ", ".join(nur11[:25])))
    print("  nur Odoo 18 (%d): %s" % (len(nur18), ", ".join(nur18[:25])))
    abw = []
    for name in sorted(set(fa) & set(fb)):
        s11, s18 = (fa[name].get("string") or ""), (fb[name].get("string") or "")
        if s11.strip() != s18.strip():
            abw.append((name, s11, s18))
    print("  abweichende Beschriftung (%d):" % len(abw))
    for name, s11, s18 in abw:
        print("      %-32s Odoo 11: %-34s Odoo 18: %s" % (name, s11[:34], s18[:40]))
    print()
