"""Vergleicht Suchansichten (Filter, Gruppierungen, Suchfelder) Odoo 11 gegen Odoo 18."""
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o11, o18  # noqa: E402


def hole(client, modell, version):
    try:
        if version == 11:
            return client.kw(modell, "fields_view_get", [False, "search"], context={"lang": "de_DE"}).get("arch")
        gv = client.kw(modell, "get_views", [[[False, "search"]]], context={"lang": "de_DE"})
        return list((gv.get("views") or {}).values())[0]["arch"]
    except Exception as fehler:
        return "FEHLER: %s" % str(fehler)[:110]


def auswerten(arch):
    if not arch or arch.startswith("FEHLER"):
        return set(), set(), arch
    w = ET.fromstring(arch)
    filter_, gruppen = set(), set()
    for f in w.iter("filter"):
        name = (f.get("string") or f.get("name") or "").strip()
        if not name:
            continue
        if (f.get("context") or "").find("group_by") >= 0:
            gruppen.add(name)
        else:
            filter_.add(name)
    return filter_, gruppen, None


k11, k18 = o11(), o18("lokal")
for modell in ("account.move", "account.payment", "res.partner", "product.template", "account.tax", "account.journal"):
    f11, g11, e11 = auswerten(hole(k11, modell, 11))
    f18, g18, e18 = auswerten(hole(k18, modell, 18))
    print("\n===== %s =====" % modell)
    if e11 or e18:
        print("   Fehler:", e11 or e18)
        continue
    print("   Odoo 11 Filter (%d): %s" % (len(f11), sorted(f11)))
    print("   Odoo 18 Filter (%d)" % len(f18))
    print("   Odoo 11 Gruppierungen (%d): %s" % (len(g11), sorted(g11)))
    fehlend_f = sorted(x for x in f11 if x not in f18)
    fehlend_g = sorted(x for x in g11 if x not in g18)
    print("   FEHLT in Odoo 18 - Filter: %s" % fehlend_f)
    print("   FEHLT in Odoo 18 - Gruppierungen: %s" % fehlend_g)
