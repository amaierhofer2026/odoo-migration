"""Testbeleg fuer den Pflichtfeld-Nachweis: Entwurfsrechnung OHNE Partner.

Aufruf:
  python scripts/_pf_testbeleg.py lokal anlegen    -> legt an, gibt id aus
  python scripts/_pf_testbeleg.py lokal entfernen  -> entfernt alles mit TEST-PF-
  python scripts/_pf_testbeleg.py lokal pruefen    -> zeigt Zustand
"""
import sys

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o18  # noqa: E402

instanz = sys.argv[1] if len(sys.argv) > 1 else "lokal"
was = sys.argv[2] if len(sys.argv) > 2 else "pruefen"
k = o18(instanz)
CTX = {"lang": "de_DE"}

MARKER = "TEST-PF-126"
DOMAIN = ["|", ["ref", "like", MARKER], ["invoice_line_ids.name", "like", MARKER]]

if was == "anlegen":
    journal = k.kw("account.journal", "search_read",
                   [[["type", "=", "sale"], ["company_id", "=", k.kw("res.company", "search", [[]])[0]]],
                    ["id", "name"]], context=CTX)
    jid = journal[0]["id"]
    vals = {
        "move_type": "out_invoice",
        "partner_id": False,
        "journal_id": jid,
        "ref": MARKER,
        "invoice_line_ids": [(0, 0, {"name": MARKER + " Zeile", "quantity": 1.0,
                                     "price_unit": 10.0, "tax_ids": [(6, 0, [])]})],
    }
    mid = k.kw("account.move", "create", [vals], context=CTX)
    print("angelegt id=%s journal=%s" % (mid, journal[0]["name"]))
elif was == "entfernen":
    ids = k.kw("account.move", "search", [DOMAIN], context=CTX)
    if ids:
        k.kw("account.move", "button_cancel", [ids], context=CTX) if False else None
        k.kw("account.move", "unlink", [ids], context=CTX)
    print("entfernt:", ids)
elif was == "pruefen":
    rest = k.kw("account.move", "search_read", [DOMAIN, ["id", "name", "ref", "state", "partner_id"]],
                context=CTX)
    print("Rest-Testbelege:", rest)
    print("ohne Partner:", k.kw("account.move", "search_read",
                               [[["partner_id", "=", False], ["move_type", "in",
                                 ["out_invoice", "out_refund", "out_receipt"]]],
                                ["id", "name", "move_type", "state"]], context=CTX))
    print("Bestand:", k.kw("account.move", "search_count", [[]], context=CTX))
    print("Kunden (Beispiel):", k.kw("account.move", "search_read",
                                     [[["move_type", "=", "out_invoice"], ["partner_id", "!=", False]],
                                      ["partner_id"]], context=CTX, limit=3))
