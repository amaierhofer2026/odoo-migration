"""Testdaten fuer den Nachweis der Zeilen-Spalte "Beschreibung" (Odoo 18, Testinstanz).

Legt je Belegart einen Entwurf mit Abschnittszeile, Notizzeile und Produktzeile an. Die
Produktzeile traegt bewusst eine Beschreibung, die NICHT dem Produktnamen entspricht, damit
die Spalte "Beschreibung" eindeutig nachweisbar ist.

Aufruf:
    python scripts/_zeilen_testdaten.py lokal|vm anlegen
    python scripts/_zeilen_testdaten.py lokal|vm pruefen
    python scripts/_zeilen_testdaten.py lokal|vm aufraeumen
"""
import sys

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o18  # noqa: E402

MARKER = "TEST-ZEILE-"
CTX = {"lang": "de_DE"}
ARTEN = [("out_invoice", "Ausgangsrechnung"), ("out_refund", "Kunden-Gutschrift"),
         ("in_invoice", "Eingangsrechnung"), ("in_refund", "Lieferanten-Gutschrift")]


def sag(*a):
    print(*a, flush=True)


def finden(k, name=None):
    return k.kw("account.move", "search_read",
                [[["ref", "like", MARKER if name is None else "TEST-ZEILE-" + name]],
                 ["id", "name", "move_type", "state", "ref"]], context=CTX)


def bestand(k):
    return {"account.move": k.kw("account.move", "search_count", [[]], context=CTX),
            "account.move.line": k.kw("account.move.line", "search_count", [[]], context=CTX)}


def aufraeumen(k):
    treffer = finden(k)
    sag("Aufraeumen: %d Testbelege" % len(treffer))
    for t in treffer:
        try:
            k.kw("account.move", "button_draft", [[t["id"]]], context=CTX)
        except Exception:
            pass
        try:
            k.kw("account.move", "unlink", [[t["id"]]], context=CTX)
        except Exception as f:
            sag("   Beleg %s nicht entfernbar: %s" % (t["id"], str(f)[:160]))
    rest = finden(k)
    sag("Reste:", rest)
    return not rest


def main() -> int:
    instanz = sys.argv[1] if len(sys.argv) > 1 else "lokal"
    was = sys.argv[2] if len(sys.argv) > 2 else "pruefen"
    k = o18(instanz)
    sag("Instanz: %s | %s | Aktion: %s" % (instanz, k.url, was))
    sag("Bestand:", bestand(k))

    if was == "pruefen":
        for t in finden(k):
            zeilen = k.kw("account.move.line", "search_read",
                          [[["move_id", "=", t["id"]],
                            ["display_type", "in", ["product", "line_section", "line_note"]]],
                           ["id", "display_type", "name"]], context=CTX)
            sag("  %s %-12s %s" % (t["name"] or "(Entwurf)", t["move_type"], zeilen))
        return 0

    if was == "aufraeumen":
        aufraeumen(k)
        sag("Bestand:", bestand(k))
        return 0

    verkauf = k.kw("account.journal", "search_read",
                   [[["type", "=", "sale"]], ["id", "name", "default_account_id"]], context=CTX, limit=1)[0]
    einkauf = k.kw("account.journal", "search_read",
                   [[["type", "=", "purchase"]], ["id", "name", "default_account_id"]], context=CTX, limit=1)[0]
    partner = k.kw("res.partner", "search_read",
                   [[["is_company", "=", True], ["active", "=", True]], ["id", "name"]], context=CTX, limit=1)[0]
    sag("Verkaufsjournal: %s | Einkaufsjournal: %s | Partner: %s"
        % (verkauf["name"], einkauf["name"], partner["name"]))

    for typ, bezeichnung in ARTEN:
        vk = typ.startswith("out")
        journal = verkauf if vk else einkauf
        konto = journal["default_account_id"] and journal["default_account_id"][0]
        if not konto:
            konto = k.kw("account.account", "search",
                         [[["account_type", "in", ["income", "expense"]]]], context=CTX, limit=1)[0]
        werte = {
            "move_type": typ,
            "partner_id": partner["id"],
            "journal_id": journal["id"],
            "invoice_date": "2026-10-05",
            "date": "2026-10-05",
            "ref": "%s%s" % (MARKER, typ),
            "invoice_line_ids": [
                (0, 0, {"display_type": "line_section", "name": "ABSCHNITT %s" % typ}),
                (0, 0, {"display_type": "line_note", "name": "NOTIZ %s" % typ}),
                (0, 0, {"display_type": "product", "name": "BESCHREIBUNG %s" % typ,
                        "quantity": 1.0, "price_unit": 100.0, "account_id": konto}),
            ],
        }
        mid = k.kw("account.move", "create", [werte], context=CTX)
        daten = k.kw("account.move", "read", [[mid], ["name", "move_type", "state"]], context=CTX)[0]
        zeilen = k.kw("account.move.line", "search_read",
                      [[["move_id", "=", mid]], ["display_type", "name"]], context=CTX)
        sag("  %-22s id %-4s %s | Zeilen: %s" % (bezeichnung, mid, daten, zeilen))

    sag("Bestand:", bestand(k))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
