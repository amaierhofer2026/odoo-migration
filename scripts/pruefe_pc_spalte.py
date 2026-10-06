"""Prueft die Project-Category-Spalte je Listenansicht (Odoo 18) - Ansichts-IDs direkt."""
import re
import sys

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o18  # noqa: E402

instanz = sys.argv[1] if len(sys.argv) > 1 else "lokal"
k = o18(instanz)
print("Instanz:", instanz, "| URL:", k.url)

for vid, name in [(951, "view_invoice_tree (Basis)"),
                  (953, "view_out_invoice_tree (Ausgangsrechnungen)"),
                  (954, "view_out_credit_note_tree (Kunden-Gutschriften)"),
                  (956, "view_in_invoice_bill_tree (Eingangsrechnungen)"),
                  (957, "view_in_invoice_refund_tree (Lieferanten-Gutschriften)")]:
    r = k.kw("account.move", "get_view", [vid, "list"], context={"lang": "de_DE"})
    arch = r.get("arch") if isinstance(r, dict) else None
    if not arch:
        arch = ""
    felder = re.findall(r"<field name=\"([^\"]+)\"", arch)
    drin = "projectcategory_id" in felder
    i = felder.index("projectcategory_id") if drin else -1
    print("%-46s Felder=%s projectcategory_id=%s pos=%s" %
          (name, len(felder), drin, i + 1 if drin else "-"))
    if drin:
        print("     Umfeld:", felder[max(0, i - 2):i + 3])
