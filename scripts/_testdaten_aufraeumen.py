"""Entfernt Testdaten (Zahlungen und Rechnungen mit TEST- im Vermerk/Referenz).

Aufruf: python scripts/_testdaten_aufraeumen.py vm|lokal
"""
import sys

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o18  # noqa: E402

k = o18(sys.argv[1] if len(sys.argv) > 1 else "lokal")
CTX = {"lang": "de_DE"}

zahlungen = k.kw("account.payment", "search_read",
                 [[["memo", "like", "TEST-"]], ["id", "name", "memo", "state", "amount"]], context=CTX)
print("Testzahlungen gefunden: %d" % len(zahlungen))
for z in zahlungen:
    print("   id=%-3s state=%-10s Betrag=%-8s Vermerk=%s" % (z["id"], z["state"], z["amount"], z["memo"]))
for z in zahlungen:
    try:
        k.kw("account.payment", "action_draft", [[z["id"]]], context=CTX)
    except Exception:
        pass
    try:
        k.kw("account.payment", "unlink", [[z["id"]]], context=CTX)
        print("   Zahlung %s entfernt" % z["id"])
    except Exception as fehler:
        print("   Zahlung %s NICHT entfernbar: %s" % (z["id"], str(fehler)[:120]))

for dom in ([["ref", "like", "TEST-"]], [["name", "like", "TEST-"]]):
    rechnungen = k.kw("account.move", "search_read", [dom, ["id", "name", "ref", "state"]], context=CTX)
    for r in rechnungen:
        try:
            k.kw("account.move", "button_draft", [[r["id"]]], context=CTX)
        except Exception:
            pass
        try:
            k.kw("account.move", "unlink", [[r["id"]]], context=CTX)
            print("   Rechnung %s (%s) entfernt" % (r["id"], r["ref"]))
        except Exception as fehler:
            print("   Rechnung %s NICHT entfernbar: %s" % (r["id"], str(fehler)[:120]))

print("Kontrolle Zahlungen TEST-:", k.kw("account.payment", "search_count", [[["memo", "like", "TEST-"]]], context=CTX))
print("Kontrolle Rechnungen TEST-:", k.kw("account.move", "search_count", [[["ref", "like", "TEST-"]]], context=CTX))
print("Bestand Zahlungen gesamt:", k.kw("account.payment", "search_count", [[]], context=CTX))
print("Bestand Rechnungen gesamt:", k.kw("account.move", "search_count", [[]], context=CTX))
