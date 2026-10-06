"""Testdaten fuer den Nachweis der Rechnungs-Statuskette (Odoo 18, Testinstanz odoo18_test).

Legt je Zustand eine Testrechnung an und kann sie restlos wieder entfernen:
    Entwurf        draft
    Offen          posted + not_paid
    Teilzahlung    posted + partial
    Bezahlt        posted + paid
    Abgebrochen    cancel
    Gutschrift     posted + reversed (Rechnung + vollstaendig abgestimmte Kunden-Gutschrift)

Aufruf:
    python scripts/_pc_status_testdaten.py lokal|vm anlegen
    python scripts/_pc_status_testdaten.py lokal|vm pruefen
    python scripts/_pc_status_testdaten.py lokal|vm aufraeumen
"""
import json
import sys

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o18  # noqa: E402

MARKER = "TEST-PC-"
CTX = {"lang": "de_DE"}


def sag(*args):
    print(*args, flush=True)


def testbelege(k):
    """Alle Testbelege (Rechnungen und zugehoerige Gutschriften) ueber den Marker finden."""
    rechnungen = k.kw("account.move", "search_read",
                      [[["ref", "like", MARKER]], ["id"]], context=CTX)
    ids = [r["id"] for r in rechnungen]
    gutschriften = []
    if ids:
        gutschriften = k.kw("account.move", "search_read",
                            [[["reversed_entry_id", "in", ids]], ["id"]], context=CTX)
    return ids, [g["id"] for g in gutschriften]


def testzahlungen(k, ids):
    if not ids:
        return []
    return k.kw("account.payment", "search_read",
                [[["reconciled_invoice_ids", "in", ids]], ["id", "name", "memo"]], context=CTX)


def bestand(k):
    return {"account.move": k.kw("account.move", "search_count", [[]], context=CTX),
            "account.payment": k.kw("account.payment", "search_count", [[]], context=CTX)}


def aufraeumen(k):
    ids, gut = testbelege(k)
    zah = testzahlungen(k, ids + gut)
    sag("Aufraeumen: %d Testbelege, %d Gutschriften, %d Zahlungen" % (len(ids), len(gut), len(zah)))
    for z in zah:
        for schritt in ("action_cancel", "action_draft", "unlink"):
            try:
                k.kw("account.payment", schritt, [[z["id"]]], context=CTX)
            except Exception:
                pass
    for rid in gut + ids:
        try:
            k.kw("account.move", "button_draft", [[rid]], context=CTX)
        except Exception:
            pass
        try:
            k.kw("account.move", "unlink", [[rid]], context=CTX)
        except Exception as fehler:
            sag("   Beleg %s nicht entfernbar: %s" % (rid, str(fehler)[:150]))
    rest, restg = testbelege(k)
    sag("Reste Belege: %s | Reste Gutschriften: %s | Reste Zahlungen: %s"
        % (rest, restg, testzahlungen(k, rest + restg)))
    return not rest and not restg


def main() -> int:
    instanz = sys.argv[1] if len(sys.argv) > 1 else "lokal"
    was = sys.argv[2] if len(sys.argv) > 2 else "pruefen"
    k = o18(instanz)
    sag("Instanz: %s | %s | Aktion: %s" % (instanz, k.url, was))
    sag("Bestand:", bestand(k))

    if was == "pruefen":
        ids, gut = testbelege(k)
        for r in k.kw("account.move", "search_read",
                      [[["id", "in", ids + gut]],
                       ["id", "name", "state", "payment_state", "move_type", "ref",
                        "projectcategory_id", "amount_total", "amount_residual"]], context=CTX):
            sag("   %s" % r)
        return 0

    if was == "aufraeumen":
        aufraeumen(k)
        sag("Bestand:", bestand(k))
        return 0

    # ---- anlegen ----
    journal = k.kw("account.journal", "search_read",
                   [[["type", "=", "sale"]], ["id", "name", "code", "default_account_id"]],
                   context=CTX, limit=1)[0]
    bnk = k.kw("account.journal", "search_read",
               [[["type", "=", "bank"]], ["id", "name", "code"]], context=CTX, limit=1)[0]
    partner = k.kw("res.partner", "search_read",
                   [[["is_company", "=", True], ["active", "=", True]], ["id", "name"]],
                   context=CTX, limit=1)[0]
    pc = k.kw("itk_projectcategory.projectcategory", "search_read",
              [[], ["id", "name", "code"]], context=CTX, limit=1)[0]
    konto = journal["default_account_id"] and journal["default_account_id"][0]
    if not konto:
        konto = k.kw("account.account", "search", [[["account_type", "=", "income"]]],
                     context=CTX, limit=1)[0]
    sag("Journal: %s | Bank: %s | Partner: %s | Project Category: %s | Konto: %s"
        % (journal["name"], bnk["name"], partner["name"], pc["name"], konto))

    def neuer_beleg(nr, betrag=1000.0):
        return k.kw("account.move", "create", [{
            "move_type": "out_invoice",
            "partner_id": partner["id"],
            "journal_id": journal["id"],
            "invoice_date": "2026-10-05",
            "date": "2026-10-05",
            "ref": "%s%s" % (MARKER, nr),
            "projectcategory_id": pc["id"],
            "invoice_line_ids": [(0, 0, {"name": "Testposition Statuskette",
                                         "quantity": 1.0,
                                         "price_unit": betrag,
                                         "account_id": konto})],
        }], context=CTX)

    def zahlen(mid, betrag, nr):
        ctx = dict(CTX, active_model="account.move", active_id=mid, active_ids=[mid])
        wiz = k.kw("account.payment.register", "create",
                   [{"payment_date": "2026-10-05", "journal_id": bnk["id"], "amount": betrag}],
                   context=ctx)
        k.kw("account.payment.register", "action_create_payments", [[wiz]], context=ctx)
        treffer = k.kw("account.payment", "search_read",
                       [[["reconciled_invoice_ids", "in", [mid]]], ["id", "name", "amount"]],
                       context=CTX)
        sag("   Zahlung fuer %s (Beleg %s) -> %s" % (nr, mid, treffer))

    def zustand(mid, hinweis=""):
        r = k.kw("account.move", "read", [[mid], ["name", "state", "payment_state", "amount_residual"]],
                 context=CTX)[0]
        sag("   Beleg %s (%s): %s / %s / Rest %s %s"
            % (r["id"], r["name"], r["state"], r["payment_state"], r["amount_residual"], hinweis))
        return r

    faelle = [("1-entwurf", "draft"), ("2-offen", "offen"), ("3-teilzahlung", "teilzahlung"),
              ("4-bezahlt", "bezahlt"), ("5-abgebrochen", "abgebrochen"), ("6-gutschrift", "gutschrift")]

    for nr, art in faelle:
        mid = neuer_beleg(nr)
        if art == "draft":
            zustand(mid, "= Entwurf")
            continue
        k.kw("account.move", "action_post", [[mid]], context=CTX)
        if art == "offen":
            zustand(mid, "= Offen")
        elif art == "teilzahlung":
            gesamt = k.kw("account.move", "read", [[mid], ["amount_total"]], context=CTX)[0]["amount_total"]
            zahlen(mid, round(gesamt * 0.4, 2), nr)
            zustand(mid, "= Teilzahlung")
        elif art == "bezahlt":
            gesamt = k.kw("account.move", "read", [[mid], ["amount_total"]], context=CTX)[0]["amount_total"]
            zahlen(mid, gesamt, nr)
            zustand(mid, "= Bezahlt")
        elif art == "abgebrochen":
            k.kw("account.move", "button_cancel", [[mid]], context=CTX)
            zustand(mid, "= Abgebrochen")
        elif art == "gutschrift":
            ctx = dict(CTX, active_model="account.move", active_id=mid, active_ids=[mid])
            vorgabe = k.kw("account.move.reversal", "default_get",
                           [["journal_id", "date", "move_ids", "company_id", "move_type"]],
                           context=ctx)
            vorgabe["journal_id"] = journal["id"]
            rev = k.kw("account.move.reversal", "create", [vorgabe], context=ctx)
            k.kw("account.move.reversal", "reverse_moves", [[rev]], context=ctx)
            gut = k.kw("account.move", "search_read",
                       [[["move_type", "=", "out_refund"], ["reversed_entry_id", "=", mid]],
                        ["id", "name", "state", "payment_state"]], context=CTX)
            sag("   Gutschrift: %s" % gut)
            for g in gut:
                if g["state"] != "posted":
                    k.kw("account.move", "action_post", [[g["id"]]], context=CTX)
            zustand(mid, "= Gutschrift/Gegenbeleg")
            for g in gut:
                zustand(g["id"], "= Gutschrift")

    sag("Bestand:", bestand(k))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
