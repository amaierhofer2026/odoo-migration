"""Listet alle Views, die das Zahlungsformular erben, mit Prioritaet und gesetzten Bezeichnungen."""
import sys

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o18  # noqa: E402

k = o18(sys.argv[1] if len(sys.argv) > 1 else "lokal")
CTX = {"lang": "de_DE"}

basis = k.kw("ir.model.data", "search_read", [[["module", "=", "account"], ["model", "=", "ir.ui.view"],
                                                ["name", "=", "view_account_payment_form"]], ["res_id"]], context=CTX)
basis_id = basis[0]["res_id"] if basis else 0
print("Basis-View account.view_account_payment_form =", basis_id)

views = k.kw("ir.ui.view", "search_read",
             [[["model", "=", "account.payment"], ["type", "=", "form"], ["inherit_id", "=", basis_id],
               ["active", "=", True]], ["id", "name", "priority"]], context=CTX)
for v in sorted(views, key=lambda x: (x["priority"], x["id"])):
    arch = k.kw("ir.ui.view", "read", [[v["id"]], ["arch_db"]], context=CTX)[0]["arch_db"]
    treffer = [w for w in ("Betrag", "Zahlungsbetrag", "Zahlungsmethod", "Rechnungen", "payment_method_line_id",
                           "partner_id", "memo") if w in arch]
    print("   prio=%-4s id=%-6s %-46s %s" % (v["priority"], v["id"], (v["name"] or "")[:46], treffer))
