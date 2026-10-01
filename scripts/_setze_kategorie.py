"""Setzt auf dem Testbeleg die Projektkategorie (Relation aus dem Feld ermitteln)."""
import sys

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o18  # noqa: E402

k = o18(sys.argv[1] if len(sys.argv) > 1 else "lokal")
beleg_id = int(sys.argv[2]) if len(sys.argv) > 2 else 79
CTX = {"lang": "de_DE"}

info = k.kw("account.move", "fields_get", [["projectcategory_id"], ["relation", "string"]], context=CTX)
print("Feld info:", info)
modell = (info.get("projectcategory_id") or {}).get("relation")
if not modell:
    sys.exit("Keine Relation gefunden")
sat = k.kw(modell, "search_read", [[[], ["id", "display_name"]]], context=CTX)
print("Datensaetze in %s: %s" % (modell, sat[:4]))
if sat:
    k.kw("account.move", "write", [[beleg_id], {"projectcategory_id": sat[0]["id"]}], context=CTX)
    neu = k.kw("account.move", "read", [[beleg_id], ["projectcategory_id"]], context=CTX)
    print("auf Beleg %s gesetzt: %s" % (beleg_id, neu))
