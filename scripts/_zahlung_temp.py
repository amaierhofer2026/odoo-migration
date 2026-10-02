"""Legt eine Test-Zahlung (Lieferant, Entwurf) an bzw. entfernt sie wieder."""
import sys

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o18  # noqa: E402

k = o18(sys.argv[1] if len(sys.argv) > 1 else "vm")
aktion = sys.argv[2] if len(sys.argv) > 2 else "anlegen"
CTX = {"lang": "de_DE"}


def zuerst(model, domain, fields):
    treffer = k.kw(model, "search_read", [domain, fields], context=CTX)
    return treffer[0] if treffer else None


if aktion == "anlegen":
    vorher = k.kw("account.payment", "search_count", [[["payment_type", "=", "outbound"]]], context=CTX)
    partner = zuerst("res.partner", [["supplier_rank", ">", 0]], ["id", "name"])
    if not partner:
        partner = zuerst("res.partner", [["name", "!=", False]], ["id", "name"])
    journal = zuerst("account.journal", [["type", "=", "bank"]], ["id", "name"])
    methode = zuerst("account.payment.method.line",
                     [["journal_id", "=", journal["id"]]], ["id", "name"])
    werte = {
        "payment_type": "outbound",
        "partner_type": "supplier",
        "partner_id": partner["id"],
        "amount": 123.45,
        "journal_id": journal["id"],
        "date": "2026-10-02",
        "memo": "TEST-ABNAHME LIEFERANTENZAHLUNG",
    }
    if methode:
        werte["payment_method_line_id"] = methode["id"]
    neu = k.kw("account.payment", "create", [werte], context=CTX)
    print("TESTZAHLUNG_ID=%s" % neu)
    print("Bestand Auszahlungen vorher=%s nachher=%s" % (
        vorher, k.kw("account.payment", "search_count", [[["payment_type", "=", "outbound"]]], context=CTX)))
else:
    pid = int(sys.argv[3])
    try:
        k.kw("account.payment", "unlink", [[pid]], context=CTX)
        print("Testzahlung %s entfernt" % pid)
    except Exception as fehler:
        print("unlink fehlgeschlagen:", str(fehler)[:150])
    print("noch vorhanden:", k.kw("account.payment", "search_count", [[["id", "=", pid]]], context=CTX))
