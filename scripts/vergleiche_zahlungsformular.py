"""Vergleicht das Odoo-11-Zahlungsformular mit dem Odoo-18-Zahlungsformular (nur lesend).

Aufruf: python scripts/vergliche_zahlungsformular.py
Gibt aus:
  1. Odoo 11: sichtbare Felder im Formular account.payment (technischer Name, Beschriftung, Reihenfolge)
  2. Odoo 11: Statuswerte des Feldes state und der Abstimmungsmerker
  3. Odoo 18: Felder des Modells account.payment (Name, Typ, Beziehung, Beschriftung) fuer das Mapping
"""
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o11, o18  # noqa: E402

CTX11 = {"lang": "de_DE"}
CTX18 = {"lang": "de_DE"}


def formular_11():
    k = o11()
    try:
        gv = k.kw("account.payment", "get_views", [[[False, "form"]]], context=CTX11)
        arch = list((gv.get("views") or {}).values())[0]["arch"]
    except Exception:
        gv = k.kw("account.payment", "fields_view_get", [False, "form"], context=CTX11)
        arch = gv.get("arch")
    w = ET.fromstring(arch)
    print("=== Odoo 11: sichtbare Felder im Zahlungsformular (Reihenfolge im Arch) ===")
    for f in w.iter("field"):
        inv = (f.get("invisible") or "")
        if inv in ("1", "True"):
            continue
        print("   %-28s string=%-26r widget=%-18s readonly=%s" % (
            f.get("name"), (f.get("string") or "")[:26], (f.get("widget") or "-"), (f.get("attrs") or "")[:30]))
    print("=== Odoo 11: Statuswerte (state) ===")
    info = k.kw("account.payment", "fields_get", [["state", "is_matched", "payment_type", "partner_type"], ["selection", "string", "type"]], context=CTX11)
    for name, wert in info.items():
        print("   %-16s string=%-24r typ=%s auswahl=%s" % (name, wert.get("string"), wert.get("type"), wert.get("selection")))
    print("=== Odoo 11: Smart Button im Formular (Knopftexte) ===")
    for b in w.iter("button"):
        print("   button name=%-24s string=%-20r type=%s class=%s" % (
            b.get("name"), (b.get("string") or "")[:20], b.get("type"), (b.get("class") or "")[:40]))


def felder_18():
    k = o18("vm")
    info = k.kw("account.payment", "fields_get", [[], ["string", "type", "relation", "selection", "readonly"]], context=CTX18)
    wichtig = ["payment_type", "partner_type", "partner_id", "amount", "journal_id", "date", "memo",
               "payment_method_line_id", "payment_method_id", "payment_transaction_id", "partner_bank_id",
               "state", "is_matched", "is_reconciled", "currency_id", "itk_o11_payment_number", "move_id",
               "invoice_ids", "reconciled_invoice_ids", "reconciled_bill_ids", "company_id", "payment_reference"]
    print("=== Odoo 18: Felder des Modells account.payment ===")
    for f in wichtig:
        if f not in info:
            print("   %-28s NICHT VORHANDEN" % f)
            continue
        d = info[f]
        print("   %-28s string=%-30r typ=%-12s rel=%s auswahl=%s" % (
            f, (d.get("string") or "")[:30], d.get("type"), d.get("relation"), (d.get("selection") if d.get("type") == "selection" else "")))


formular_11()
felder_18()
