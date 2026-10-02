"""Abonnement-Neuabgleich (Schritt 1): Bestandsaufnahme beider Systeme, nur lesend.

Aufruf: python scripts/abgleich_abonnements_1_bestand.py
"""
import sys

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}
k11, k18 = o11(), o18("vm")

MUSTER = ("subscription", "abonnement", "abo_", "recurring")


def modelle(client, bezeichnung):
    treffer = []
    for modell in client.kw("ir.model", "search_read", [[["model", "ilike", "%subscri%"]], ["model", "name"]],
                            context=CTX):
        treffer.append(modell)
    for modell in client.kw("ir.model", "search_read", [[["model", "ilike", "%abonnem%"]], ["model", "name"]],
                            context=CTX):
        treffer.append(modell)
    print("=== %s: Abonnement-Modelle ===" % bezeichnung)
    for eintrag in sorted(treffer, key=lambda x: x["model"]):
        try:
            anzahl = client.kw(eintrag["model"], "search_count", [[]], context=CTX)
        except Exception:
            anzahl = -1
        print("   %-42s %-34s Datensaetze: %d" % (eintrag["model"], (eintrag["name"] or "")[:34], anzahl))
    return [e["model"] for e in treffer]


m11 = modelle(k11, "Odoo 11 (Produktion)")
print()
m18 = modelle(k18, "Odoo 18 (Test-VM)")
print()
print("Nur in Odoo 11:", sorted(set(m11) - set(m18)))
print("Nur in Odoo 18:", sorted(set(m18) - set(m11)))
print("In beiden:", sorted(set(m11) & set(m18)))
