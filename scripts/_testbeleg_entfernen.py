"""Entfernt den Testbeleg aus Odoo 18 und weist den Bestand nach."""
import sys

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o18  # noqa: E402

k = o18(sys.argv[1] if len(sys.argv) > 1 else "lokal")
beleg_id = int(sys.argv[2]) if len(sys.argv) > 2 else 79
CTX = {"lang": "de_DE"}

dom_alle = [["move_type", "=", "out_invoice"]]
dom_beleg = [["id", "=", beleg_id]]

print("Bestand vorher:", k.kw("account.move", "search_count", [dom_alle], context=CTX))
if k.kw("account.move", "search_count", [dom_beleg], context=CTX):
    try:
        k.kw("account.move", "unlink", [[beleg_id]], context=CTX)
        print("Testbeleg %s entfernt" % beleg_id)
    except Exception as fehler:
        print("unlink fehlgeschlagen:", str(fehler)[:160])
else:
    print("Testbeleg %s war nicht mehr vorhanden" % beleg_id)
print("Bestand nachher:", k.kw("account.move", "search_count", [dom_alle], context=CTX))
print("Testbeleg noch vorhanden:", k.kw("account.move", "search_count", [dom_beleg], context=CTX))
