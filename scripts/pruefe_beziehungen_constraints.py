"""Abschlusspruefung Teil 2: Beziehungen und Constraints (Odoo 11 gegen Odoo 18).

Aufruf: python scripts/pruefe_beziehungen_constraints.py
"""
import sys

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}
MODELLE = ["account.invoice", "account.invoice.line", "account.payment", "res.partner",
           "product.template", "account.tax", "account.journal", "account.move", "account.move.line"]


def beziehungen(k, modell):
    try:
        felder = k.kw(modell, "fields_get", [[], ["type", "relation", "required"]], context=CTX)
    except Exception:
        return None
    aus = []
    for name, info in felder.items():
        if info.get("type") in ("many2one", "many2many", "one2many"):
            aus.append((name, info.get("type"), info.get("relation"), bool(info.get("required"))))
    return aus


def constraints(k, modell, version):
    aus = []
    try:
        cs = k.kw("ir.model.constraint", "search_read",
                  [[["model", "=", modell]], ["name", "type", "definition"]], context=CTX)
        aus.extend(("constraint", c["name"], c["type"], (c.get("definition") or "")[:60]) for c in cs)
    except Exception:
        pass
    try:
        felder = k.kw(modell, "fields_get", [["name", "code", "email", "vat", "default_code", "barcode"],
                                            ["type", "required"]], context=CTX)
    except Exception:
        felder = {}
    return aus


k11, k18 = o11(), o18("lokal")
for modell in MODELLE:
    b11 = beziehungen(k11, modell) if modell in ("account.invoice", "account.invoice.line", "account.payment") else []
    b18 = beziehungen(k18, modell) if modell in ("account.move", "account.move.line", "account.payment") else []
    if modell == "account.invoice":
        b18 = beziehungen(k18, "account.move")
    if modell == "account.invoice.line":
        b18 = beziehungen(k18, "account.move.line")
    if not b11 or not b18:
        continue
    namen18 = {n for n, _, _, _ in b18}
    print("\n===== %s =====" % modell)
    print("   Odoo 11 Beziehungen: %d | Odoo 18 (Zielmodell): %d" % (len(b11), len(b18)))
    wichtig = [b for b in b11 if b[0] in ("partner_id", "journal_id", "payment_term_id", "account_id",
                                          "product_id", "invoice_line_tax_ids", "tax_ids", "payment_method_id",
                                          "invoice_ids", "categ_id", "taxes_id", "supplier_taxes_id",
                                          "invoice_line_ids", "tax_line_ids", "analytic_account_id",
                                          "account_analytic_id", "move_id", "payment_id")]
    for name, typ, rel, pflicht in wichtig:
        vorhanden = "ja" if name in namen18 else "NEIN"
        print("      %-26s %-12s -> %-24s Pflicht=%-5s in Odoo 18: %s" % (name, typ, rel, pflicht, vorhanden))

print("\n===== Constraints Odoo 18 (Auswahl) =====")
for modell in ("account.move", "account.move.line", "account.payment", "res.partner", "product.template",
               "account.journal", "account.tax"):
    cs = k18.kw("ir.model.constraint", "search_read", [[["model", "=", modell]], ["name", "type"]], context=CTX)
    if cs:
        print("   %-22s %s" % (modell, [c["name"] for c in cs][:6]))
