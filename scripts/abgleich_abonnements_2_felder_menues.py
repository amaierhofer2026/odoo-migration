"""Abonnement-Neuabgleich (Schritt 2): Felder, Zustaende und Menues in Odoo 11 gegen Odoo 18.

Aufruf: python scripts/abgleich_abonnements_2_felder_menues.py
Nur lesend.
"""
import sys

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}
k11, k18 = o11(), o18("vm")
MODELLE = ["sale.subscription", "sale.subscription.line", "sale.subscription.template"]
OHNE = {"id", "create_uid", "create_date", "write_uid", "write_date", "__last_update", "display_name"}


def beschreibe(client, bezeichnung):
    print("############ %s ############" % bezeichnung)
    for modell in MODELLE:
        gesamt = client.kw(modell, "search_count", [[]], context=CTX)
        felder = client.kw(modell, "fields_get", [[], ["type", "compute", "store", "string"]], context=CTX)
        belegt = []
        for name, info in sorted(felder.items()):
            if info.get("type") in ("binary", "image") or name in OHNE or info.get("compute"):
                continue
            try:
                anzahl = client.kw(modell, "search_count", [[[name, "!=", False]]], context=CTX)
            except Exception:
                continue
            if anzahl and anzahl == gesamt and gesamt:
                belegt.append((name, info.get("string"), anzahl))
        print("--- %s: %d Datensaetze, %d vollstaendig belegte Felder" % (modell, gesamt, len(belegt)))
        for name, label, anzahl in belegt[:40]:
            print("      %-30s %-34s %d" % (name, (label or "")[:34], anzahl))
        # Zustandsverteilung, falls vorhanden
        if "state" in felder:
            gruppen = client.kw(modell, "read_group", [[], ["state"], ["state"]], context=CTX)
            print("      Zustaende: %s" % ", ".join(
                "%s=%s" % (g.get("state"), g.get("state_count")) for g in gruppen))


beschreibe(k11, "Odoo 11 (Produktion)")
print()
beschreibe(k18, "Odoo 18 (Test-VM)")

for client, bezeichnung in ((k11, "Odoo 11"), (k18, "Odoo 18")):
    print("\n=== Menues %s (Abonnement) ===" % bezeichnung)
    wurzel = client.kw("ir.ui.menu", "search_read",
                       [[["name", "ilike", "abonn"]], ["id", "name", "complete_name", "parent_id", "action"]],
                       context=dict(CTX, **{"ir.ui.menu.full_list": True}))
    for eintrag in wurzel[:20]:
        print("   %-40s %s" % (eintrag.get("complete_name"), eintrag.get("action")))
