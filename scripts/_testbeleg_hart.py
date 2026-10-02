"""Entfernt hartnaeckige Testzahlung und Testrechnung (Verknuepfung loesen)."""
import sys

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o18  # noqa: E402

k = o18(sys.argv[1] if len(sys.argv) > 1 else "lokal")
CTX = {"lang": "de_DE"}
zahlung = int(sys.argv[2]) if len(sys.argv) > 2 else 14
rechnung = int(sys.argv[3]) if len(sys.argv) > 3 else 89


def info(model, pid, felder):
    return k.kw(model, "read", [[pid], felder], context=CTX)[0]


print("Zahlung:", info("account.payment", zahlung,
                       ["name", "state", "move_id", "reconciled_invoice_ids", "is_reconciled"]))
print("Rechnung:", info("account.move", rechnung, ["name", "state", "payment_state"]))

# 1) Zahlung abbrechen, damit die Verknuepfung geloest wird
for schritt in ("action_cancel", "action_draft", "unlink"):
    try:
        k.kw("account.payment", schritt, [[zahlung]], context=CTX)
        print("Zahlung: %s ok" % schritt)
    except Exception as fehler:
        print("Zahlung: %s fehlgeschlagen -> %s" % (schritt, str(fehler)[:180]))
print("Zahlung noch vorhanden:", k.kw("account.payment", "search_count", [[["id", "=", zahlung]]], context=CTX))

# 2) Rechnung auf Entwurf, dann loeschen
for schritt in ("button_draft", "unlink"):
    try:
        k.kw("account.move", schritt, [[rechnung]], context=CTX)
        print("Rechnung: %s ok" % schritt)
    except Exception as fehler:
        print("Rechnung: %s fehlgeschlagen -> %s" % (schritt, str(fehler)[:180]))
print("Rechnung noch vorhanden:", k.kw("account.move", "search_count", [[["id", "=", rechnung]]], context=CTX))
print("Bestand Zahlungen:", k.kw("account.payment", "search_count", [[]], context=CTX),
      "Rechnungen:", k.kw("account.move", "search_count", [[]], context=CTX))
