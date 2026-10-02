"""Ermittelt den Serverfehler des Zahlungsformulars (Arch-Pruefung und web_read)."""
import json
import sys
import urllib.request

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o18  # noqa: E402

k = o18(sys.argv[1] if len(sys.argv) > 1 else "lokal")
CTX = {"lang": "de_DE"}


def versuch(bezeichnung, model, method, args):
    try:
        ergebnis = k.kw(model, method, args, context=CTX)
        print("OK   %s" % bezeichnung)
        return ergebnis
    except Exception as fehler:
        text = str(fehler)
        print("FEHL %s -> %s" % (bezeichnung, text[-400:]))
        return None


versuch("get_views form", "account.payment", "get_views", [[[False, "form"]]])
versuch("read Felder", "account.payment", "read",
        [[8], ["payment_type", "partner_type", "partner_id", "amount", "journal_id", "date", "memo",
               "payment_transaction_id", "itk_o11_payment_number", "is_reconciled", "state",
               "payment_method_line_id", "company_id", "currency_id", "move_id"]])
versuch("web_read", "account.payment", "web_read",
        [[8], {"specification": {"payment_type": {}, "partner_type": {}, "partner_id": {"fields": {"display_name": {}}},
                                 "amount": {}, "journal_id": {"fields": {"display_name": {}}}, "date": {}, "memo": {},
                                 "payment_transaction_id": {"fields": {"display_name": {}}},
                                 "itk_o11_payment_number": {}, "is_reconciled": {}, "state": {},
                                 "payment_method_line_id": {"fields": {"display_name": {}}}}}])
