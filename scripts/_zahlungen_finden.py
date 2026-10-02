"""Listet Zahlungen je Instanz und Zustand auf (fuer die Formularabnahme)."""
import sys

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o18  # noqa: E402

k = o18(sys.argv[1] if len(sys.argv) > 1 else "lokal")
CTX = {"lang": "de_DE"}
felder = ["id", "name", "payment_type", "partner_type", "state", "is_reconciled", "is_matched", "amount", "date"]

alle = k.kw("account.payment", "search_read", [[], felder], context=CTX)
print("Zahlungen gesamt: %d" % len(alle))
nach = {}
for z in alle:
    nach.setdefault((z["payment_type"], z["partner_type"], z["state"]), []).append(z)
for schluessel in sorted(nach, key=str):
    liste = nach[schluessel]
    beispiele = ", ".join("%s(id %s%s)" % (z["name"] or "-", z["id"], ", abgestimmt" if z["is_reconciled"] else "") for z in liste[:3])
    print("   %-38s %4d  z.B. %s" % ("/".join(schluessel), len(liste), beispiele))
