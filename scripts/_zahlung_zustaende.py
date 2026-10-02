"""Legt Testzahlungen in den Zustaenden Entwurf / Gebucht / Abgebrochen an und entfernt sie wieder.

Aufruf: python scripts/_zahlung_zustaende.py vm|lokal anlegen|entfernen
"""
import json
import sys

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o18  # noqa: E402

k = o18(sys.argv[1] if len(sys.argv) > 1 else "vm")
aktion = sys.argv[2] if len(sys.argv) > 2 else "anlegen"
CTX = {"lang": "de_DE"}
DATEI = r"C:/Odoo-Test/docs/_zahlung_zustaende.json"


def erstes(model, dom, felder):
    treffer = k.kw(model, "search_read", [dom, felder], context=CTX)
    return treffer[0] if treffer else None


if aktion == "anlegen":
    partner = erstes("res.partner", [["customer_rank", ">", 0]], ["id", "name"])
    journal = erstes("account.journal", [["type", "=", "bank"]], ["id", "name"])

    def neu(betrag, vermerk):
        return k.kw("account.payment", "create", [{
            "payment_type": "inbound", "partner_type": "customer", "partner_id": partner["id"],
            "amount": betrag, "journal_id": journal["id"], "date": "2026-10-02", "memo": vermerk}], context=CTX)

    entwurf = neu(11.11, "TEST-ZUSTAND ENTWURF")
    gebucht = neu(22.22, "TEST-ZUSTAND GEBUCHT")
    k.kw("account.payment", "action_post", [[gebucht]], context=CTX)
    abgebrochen = neu(33.33, "TEST-ZUSTAND ABGEBROCHEN")
    k.kw("account.payment", "action_post", [[abgebrochen]], context=CTX)
    k.kw("account.payment", "action_cancel", [[abgebrochen]], context=CTX)

    ids = {"entwurf": entwurf, "gebucht": gebucht, "abgebrochen": abgebrochen}
    json.dump(ids, open(DATEI, "w", encoding="utf-8"))
    for name, pid in ids.items():
        daten = k.kw("account.payment", "read", [[pid], ["name", "state", "itk_o11_status", "is_reconciled"]], context=CTX)[0]
        print("%-12s id=%-3s state=%-10s O11-Status=%-12s abgestimmt=%s" % (
            name, pid, daten["state"], daten["itk_o11_status"], daten["is_reconciled"]))
else:
    ids = json.load(open(DATEI, encoding="utf-8"))
    for name, pid in ids.items():
        try:
            k.kw("account.payment", "action_draft", [[pid]], context=CTX)
        except Exception:
            pass
        try:
            k.kw("account.payment", "unlink", [[pid]], context=CTX)
            print("%s (id %s) entfernt" % (name, pid))
        except Exception as fehler:
            print("%s (id %s) nicht entfernbar: %s" % (name, pid, str(fehler)[:120]))
    print("Kontrolle offen:", k.kw("account.payment", "search_count", [[["id", "in", list(ids.values())]]], context=CTX))
