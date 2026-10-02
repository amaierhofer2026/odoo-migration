"""Legt in Odoo 18 einen Testbeleg mit allen Odoo-11-Kopffeldern an (wird danach entfernt).

Aufruf: python scripts/_beleg_mit_werten.py lokal|vm
Ausgabe: ID des Testbelegs und Bestand vorher/nachher.
"""
import json
import sys

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o18  # noqa: E402

k = o18(sys.argv[1] if len(sys.argv) > 1 else "lokal")
CTX = {"lang": "de_DE"}
BELEGART = sys.argv[2] if len(sys.argv) > 2 else "out_invoice"


def sr(model, domain, fields, limit=None):
    args = [domain, fields]
    if limit:
        args.append(0)
        args.append(limit)
    return k.kw(model, "search_read", args, context=CTX)


def zuerst(model, domain, fields):
    treffer = sr(model, domain, fields, limit=1)
    return treffer[0] if treffer else None


dom_rech = [["move_type", "=", BELEGART]]
vorher = k.kw("account.move", "search_count", [dom_rech], context=CTX)
print("Bestand Ausgangsrechnungen vorher:", vorher)

partner = zuerst("res.partner", [["customer_rank", ">", 0]], ["id", "name"])
steuer = zuerst("account.tax", [["type_tax_use", "=", "sale"]], ["id", "name"])
produkt = zuerst("product.product", [["sale_ok", "=", True]], ["id", "name"])
zahlungsziel = zuerst("account.payment.term", [], ["id", "name"])

werte = {
    "move_type": BELEGART,
    "partner_id": partner["id"],
    "invoice_date": "2026-10-01",
    "invoice_date_due": "2026-10-31",
    "ref": "TEST-ABNAHME-2026-10-01",
    "invoice_line_ids": [(0, 0, {
        "product_id": produkt["id"] if produkt else False,
        "name": "Testzeile fuer die visuelle Abnahme",
        "quantity": 3.0,
        "price_unit": 125.0,
        "discount": 10.0,
        "tax_ids": [(6, 0, [steuer["id"]] if steuer else [])],
    })],
}
if zahlungsziel:
    werte["invoice_payment_term_id"] = zahlungsziel["id"]

typ = k.kw("account.move", "fields_get", [["sale_order_benefit_period", "projectcategory_id", "team_id"], ["type"]], context=CTX)
if typ.get("sale_order_benefit_period"):
    werte["sale_order_benefit_period"] = "2026-10-01"
if typ.get("projectcategory_id"):
    try:
        kat = zuerst("itk.project.category", [], ["id"])
        if kat:
            werte["projectcategory_id"] = kat["id"]
    except Exception as fehler:
        print("Projektkategorie nicht gesetzt:", str(fehler)[:80])
if typ.get("team_id"):
    team = zuerst("crm.team", [], ["id"])
    if team:
        werte["team_id"] = team["id"]

neu = k.kw("account.move", "create", [werte], context=CTX)
print("TESTBELEG_ID=%s" % neu)
sat = k.kw("account.move", "read", [[neu], ["name", "sale_order_benefit_period", "projectcategory_id",
                                            "team_id", "invoice_payment_term_id", "invoice_date_due"]], context=CTX)[0]
print("Beleg:", json.dumps(sat, ensure_ascii=False, default=str))
print("Bestand nachher:", k.kw("account.move", "search_count", [dom_rech], context=CTX))
