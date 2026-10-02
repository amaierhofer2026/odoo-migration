"""Legt Testdaten fuer die Zahlungsabnahme an (nur Odoo 18) und zeigt Zustaende.

Aufruf: python scripts/_zahlung_testdaten.py vm|lokal anlegen|entfernen
Erzeugt: zwei Ausgangsrechnungen und eine Zahlung, die beide Rechnungen abgleicht
         sowie eine Entwurfs-Zahlung ohne Rechnungsbezug.
"""
import json
import sys

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o18  # noqa: E402

k = o18(sys.argv[1] if len(sys.argv) > 1 else "vm")
aktion = sys.argv[2] if len(sys.argv) > 2 else "anlegen"
CTX = {"lang": "de_DE"}
DATEI = r"C:/Odoo-Test/docs/_zahlung_testdaten.json"


def erstes(model, domain, fields):
    treffer = k.kw(model, "search_read", [domain, fields], context=CTX)
    return treffer[0] if treffer else None


def anlegen():
    partner = erstes("res.partner", [["customer_rank", ">", 0]], ["id", "name"])
    steuer = erstes("account.tax", [["type_tax_use", "=", "sale"]], ["id", "name"])
    produkt = erstes("product.product", [["sale_ok", "=", True]], ["id", "name"])
    journal = erstes("account.journal", [["type", "=", "bank"]], ["id", "name"])

    def rechnung(betrag):
        return k.kw("account.move", "create", [{
            "move_type": "out_invoice",
            "partner_id": partner["id"],
            "invoice_date": "2026-10-02",
            "ref": "TEST-ZAHLUNG-ABNAHME",
            "invoice_line_ids": [(0, 0, {
                "product_id": produkt["id"] if produkt else False,
                "name": "Testzeile Zahlungsabnahme",
                "quantity": 1.0,
                "price_unit": betrag,
                "tax_ids": [(6, 0, [steuer["id"]] if steuer else [])],
            })],
        }], context=CTX)

    r1 = rechnung(100.0)
    r2 = rechnung(50.0)
    k.kw("account.move", "action_post", [[r1, r2]], context=CTX)
    print("Rechnungen:", r1, r2)

    # Eine Zahlung fuer BEIDE Rechnungen ueber den Zahlungs-Assistenten
    kontext = dict(CTX)
    kontext.update({"active_model": "account.move", "active_ids": [r1, r2]})
    assistent = k.kw("account.payment.register", "create", [{
        "journal_id": journal["id"],
        "payment_date": "2026-10-02",
    }], context=kontext)
    k.kw("account.payment.register", "action_create_payments", [[assistent]], context=kontext)
    bezahlt = k.kw("account.payment", "search_read",
                   [[["memo", "like", "TEST-ZAHLUNG-ABNAHME"]],
                    ["id", "name", "state", "is_reconciled", "reconciled_invoice_ids", "amount"]], context=CTX)
    print("Zahlung(en) mit Rechnungsbezug:", bezahlt)

    # Entwurfs-Zahlung ohne Rechnungsbezug
    entwurf = k.kw("account.payment", "create", [{
        "payment_type": "inbound", "partner_type": "customer", "partner_id": partner["id"],
        "amount": 10.0, "journal_id": journal["id"], "date": "2026-10-02",
        "memo": "TEST-ZAHLUNG ENTWURF",
    }], context=CTX)
    print("Entwurfs-Zahlung:", entwurf)
    json.dump({"rechnungen": [r1, r2], "zahlungen": [z["id"] for z in bezahlt] + [entwurf]},
              open(DATEI, "w", encoding="utf-8"))
    print("IDs gespeichert in", DATEI)
    for z in bezahlt:
        print("   Zahlung %s state=%s abgestimmt=%s Rechnungen=%s Betrag=%s" % (
            z["id"], z["state"], z["is_reconciled"], z["reconciled_invoice_ids"], z["amount"]))


def entfernen():
    daten = json.load(open(DATEI, encoding="utf-8"))
    for pid in daten["zahlungen"]:
        try:
            k.kw("account.payment", "action_draft", [[pid]], context=CTX)
        except Exception:
            pass
        try:
            k.kw("account.payment", "unlink", [[pid]], context=CTX)
            print("Zahlung %s entfernt" % pid)
        except Exception as fehler:
            print("Zahlung %s nicht entfernbar: %s" % (pid, str(fehler)[:120]))
    for rid in daten["rechnungen"]:
        try:
            k.kw("account.move", "button_draft", [[rid]], context=CTX)
        except Exception:
            pass
        try:
            k.kw("account.move", "unlink", [[rid]], context=CTX)
            print("Rechnung %s entfernt" % rid)
        except Exception as fehler:
            print("Rechnung %s nicht entfernbar: %s" % (rid, str(fehler)[:120]))
    print("Kontrolle: Zahlungen=%s Rechnungen=%s" % (
        k.kw("account.payment", "search_count", [[["id", "in", daten["zahlungen"]]]], context=CTX),
        k.kw("account.move", "search_count", [[["id", "in", daten["rechnungen"]]]], context=CTX)))


if aktion == "anlegen":
    anlegen()
else:
    entfernen()
