"""Vergleicht Konfigurationsformulare Odoo 11 gegen Odoo 18 (nur lesend).

Aufruf: python scripts/vergleiche_konfiguration.py
Zeigt je Modell die sichtbaren Feldbeschriftungen beider Systeme gegenueber.
"""
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o11, o18  # noqa: E402

PAARE = [
    ("account.tax", "account.tax", "Steuern"),
    ("account.journal", "account.journal", "Journale"),
    ("res.currency", "res.currency", "Waehrungen"),
    ("account.fiscal.position", "account.fiscal.position", "Steuerzuordnung"),
    ("account.payment.term", "account.payment.term", "Zahlungsbedingungen"),
    ("account.analytic.account", "account.analytic.account", "Kostenstellen"),
    ("product.category", "product.category", "Produktkategorien"),
]


def hole(client, modell, version):
    try:
        if version == 11:
            return client.kw(modell, "fields_view_get", [False, "form"], context={"lang": "de_DE"}).get("arch")
        gv = client.kw(modell, "get_views", [[[False, "form"]]], context={"lang": "de_DE"})
        return list((gv.get("views") or {}).values())[0]["arch"]
    except Exception as fehler:
        return "FEHLER: %s" % str(fehler)[:110]


def beschriftungen(arch):
    if not arch or arch.startswith("FEHLER"):
        return [], arch
    w = ET.fromstring(arch)
    aus = []
    for c in w.iter():
        tag = c.tag.split("}")[-1]
        if tag == "field" and (c.get("invisible") or "") not in ("1", "True"):
            aus.append((c.get("name"), (c.get("string") or "").strip()))
        elif tag == "label" and c.get("string"):
            aus.append(("label:" + str(c.get("for")), c.get("string").strip()))
    return aus, None


k11, k18 = o11(), o18("lokal")
for m11, m18, name in PAARE:
    a11 = hole(k11, m11, 11)
    a18 = hole(k18, m18, 18)
    f11, e11 = beschriftungen(a11)
    f18, e18 = beschriftungen(a18)
    print("\n########## %s (%s / %s) ##########" % (name, m11, m18))
    if e11:
        print("   Odoo 11:", e11)
    if e18:
        print("   Odoo 18:", e18)
    nur11 = [x for x in f11 if x[0] not in [y[0] for y in f18]]
    print("   nur in Odoo 11 sichtbar: %s" % [(n, s) for n, s in nur11][:14])
