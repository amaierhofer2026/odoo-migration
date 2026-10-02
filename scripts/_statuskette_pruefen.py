"""Prueft die Statuskette und Sucht eine Zahlung mit mehreren Rechnungen (nur lesend)."""
import sys

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o18  # noqa: E402

k = o18(sys.argv[1] if len(sys.argv) > 1 else "vm")
CTX = {"lang": "de_DE"}

zahlungen = k.kw("account.payment", "search_read",
                 [[], ["id", "name", "state", "is_reconciled", "is_matched", "itk_o11_status",
                       "reconciled_invoice_ids", "reconciled_bill_ids", "amount"]], context=CTX)
print("Zahlungen: %d" % len(zahlungen))
for z in zahlungen[:12]:
    print("   id=%-3s %-18s state=%-10s abgestimmt=%-5s O11-Status=%-14s Rechnungen=%s Belege=%s" % (
        z["id"], z["name"], z["state"], z["is_reconciled"], z["itk_o11_status"],
        len(z["reconciled_invoice_ids"]), len(z["reconciled_bill_ids"])))
mehrfach = [z for z in zahlungen if len(z["reconciled_invoice_ids"]) > 1]
print("Zahlungen mit mehreren abgestimmten Rechnungen:", [(z["id"], z["name"], len(z["reconciled_invoice_ids"])) for z in mehrfach])
