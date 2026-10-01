"""Sucht lokal einen Ausgangsrechnungs-Datensatz mit gefuellten ITK-Feldern."""
import sys

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o18  # noqa: E402

k = o18(sys.argv[1] if len(sys.argv) > 1 else "lokal")
domain = [["move_type", "=", "out_invoice"], ["state", "=", "posted"],
          ["sale_order_benefit_period", "!=", False]]
felder = ["id", "name", "sale_order_benefit_period", "projectcategory_id", "invoice_date"]
treffer = k.kw("account.move", "search_read", [domain, felder], context={"lang": "de_DE"})
print("Belege mit Leistungszeitraum:", len(treffer))
for t in treffer[:5]:
    print("   id=%s %s Leistungszeitraum=%s ProjectCategory=%s Datum=%s" % (
        t["id"], t["name"], t["sale_order_benefit_period"], t["projectcategory_id"], t["invoice_date"]))
