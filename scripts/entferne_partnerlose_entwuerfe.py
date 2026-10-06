"""Entfernt Rechnungs-/Gutschriftenentwuerfe ohne Partner (Auftrag Anna, 05.10.2026).

Betroffen sind ausschliesslich Entwuerfe vom Typ Rechnung oder Gutschrift ohne Partner.
Buchungszeilen (move_type='entry') haben fachlich keinen Partner und bleiben unberuehrt.
Gebuchte Belege werden nie angefasst.

Aufruf:
  python scripts/entferne_partnerlose_entwuerfe.py lokal|vm --pruefen
  python scripts/entferne_partnerlose_entwuerfe.py lokal|vm --entfernen
"""
import sys

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o18  # noqa: E402

instanz = sys.argv[1] if len(sys.argv) > 1 else "lokal"
was = sys.argv[2] if len(sys.argv) > 2 else "--pruefen"
k = o18(instanz)
CTX = {"lang": "de_DE"}

TYPEN = ["out_invoice", "out_refund", "in_invoice", "in_refund", "out_receipt", "in_receipt"]
DOMAIN = [["partner_id", "=", False], ["move_type", "in", TYPEN]]
FELDER = ["id", "move_type", "state", "name", "ref", "create_date", "write_date",
          "invoice_line_ids", "amount_total", "invoice_date", "journal_id"]

print("Instanz:", instanz, "|", k.url)
bestand = k.kw("account.move", "search_count", [[]], context=CTX)
treffer = k.kw("account.move", "search_read", [DOMAIN, FELDER], context=CTX)
print("Bestand gesamt:", bestand)
print("Entwuerfe ohne Partner:", len(treffer))
for x in treffer:
    print("   id=%-4s %-12s %-6s name=%s ref=%s Zeilen=%d Summe=%s angelegt=%s Journal=%s"
          % (x["id"], x["move_type"], x["state"], x["name"], x["ref"],
             len(x["invoice_line_ids"]), x["amount_total"], x["create_date"],
             x["journal_id"][1] if x["journal_id"] else "-"))

gepostet = [x for x in treffer if x["state"] != "draft"]
if gepostet:
    print("ABBRUCH: gebuchte Belege enthalten:", gepostet)
    sys.exit(2)

if was == "--entfernen" and treffer:
    ids = [x["id"] for x in treffer]
    k.kw("account.move", "unlink", [ids], context=CTX)
    print("entfernt:", ids)

rest = k.kw("account.move", "search_read", [DOMAIN, FELDER], context=CTX)
nachher = k.kw("account.move", "search_count", [[]], context=CTX)
print("Kontrolle: Entwuerfe ohne Partner =", len(rest), "| Bestand =", nachher,
      "(vorher %s)" % bestand)
print("Buchungszeilen (move_type=entry) unveraendert:",
      k.kw("account.move", "search_count", [[["move_type", "=", "entry"]]], context=CTX))
