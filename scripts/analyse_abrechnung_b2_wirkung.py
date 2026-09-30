"""Read-only B2: Wirkung der Gutschriften in Odoo 11 und Semantik in Odoo 18 (Assistent-Quelle).

Aufruf:  python scripts/analyse_abrechnung_b2_wirkung.py
"""
from __future__ import annotations

import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o11, o18


def main() -> int:
    lade_env()
    k11 = o11()

    print("=== 1) Zustand der 237 Gutschriften (read_group) ===")
    for gruppe in k11.kw("account.invoice", "read_group", [[("type", "=", "out_refund")], ["state", "id"], ["state"]]):
        anzahl = gruppe.get("__count", gruppe.get("state_count", gruppe.get("id_count")))
        print("   %-10s %s" % (gruppe.get("state"), anzahl))

    print("\n=== 2) Zustand Gutschrift gegen Zustand Ursprungsrechnung ===")
    gutschriften = k11.kw("account.invoice", "search_read",
                          [[("type", "=", "out_refund")],
                           ["id", "number", "state", "refund_invoice_id", "origin", "comment",
                            "date_invoice", "date", "residual", "amount_total"]], order="id")
    print("   Gutschriften gelesen: %d" % len(gutschriften))
    paare = collections.Counter()
    ohne_ursprung = 0
    for g in gutschriften:
        if not g["refund_invoice_id"]:
            ohne_ursprung += 1
            continue
        paare[(g["reference_id_state"] if "reference_id_state" in g else "",)] = 0
    ursprung_ids = [g["refund_invoice_id"][0] for g in gutschriften if g["refund_invoice_id"]]
    ursprungsdaten = {}
    for u in k11.kw("account.invoice", "search_read", [[("id", "in", ursprung_ids)],
                                                          ["id", "number", "state", "residual", "amount_total"]],
                    order="id"):
        ursprungsdaten[u["id"]] = u
    kombin = collections.Counter()
    for g in gutschriften:
        if not g["refund_invoice_id"]:
            continue
        u = ursprungsdaten.get(g["refund_invoice_id"][0])
        if u:
            kombin[(g["state"], u["state"])] += 1
    for (gz, uz), anzahl in sorted(kombin.items(), key=lambda x: -x[1]):
        print("   Gutschrift %-8s | Ursprung %-8s : %d" % (gz, uz, anzahl))
    print("   Gutschriften ohne Ursprungsrechnung: %d" % ohne_ursprung)

    print("\n=== 3) Herkunft des Textes in 'comment' (Grund aus dem Assistenten?) ===")
    mit_kommentar = [g for g in gutschriften if g["comment"]][:8]
    for g in mit_kommentar:
        u = ursprungsdaten.get((g["refund_invoice_id"] or [0])[0])
        u_kommentar = ""
        if u:
            u_kommentar = (k11.kw("account.invoice", "read", [[u["id"]], ["comment"]])[0].get("comment") or "")
        print("   Gutschrift %-12s comment=%s" % (g["number"], (g["comment"] or "")[:52]))
        print("        Ursprung %-12s comment=%s  gleich=%s"
              % ((u or {}).get("number", "-"), u_kommentar[:52], u_kommentar == g["comment"]))

    print("\n=== 4) Herkunftsnummern (origin) der Gutschriften ===")
    muster = collections.Counter()
    for g in gutschriften:
        o = (g["origin"] or "").strip()
        muster["leer" if not o else ("R-Nummer" if o.startswith("R-") else o[:20])] += 1
    for m, anzahl in muster.most_common(6):
        print("   %-16s %s" % (m, anzahl))

    print("\n=== 5) Gibt es in Odoo 11 Gutschriften im Entwurf? (Modus 'refund' ohne Ausgleich) ===")
    print("   Entwurf:", k11.kw("account.invoice", "search_count", [[("type", "=", "out_refund"), ("state", "=", "draft")]]))
    print("   Storno :", k11.kw("account.invoice", "search_count", [[("type", "=", "out_refund"), ("state", "=", "cancel")]]))
    print("   Offen  :", k11.kw("account.invoice", "search_count", [[("type", "=", "out_refund"), ("state", "=", "open")]]))
    print("   Bezahlt:", k11.kw("account.invoice", "search_count", [[("type", "=", "out_refund"), ("state", "=", "paid")]]))
    print("   Urspruenge im Zustand Storno:", k11.kw("account.invoice", "search_count",
                                                    [[("type", "=", "out_invoice"), ("state", "=", "cancel")]]))
    print("   Urspruenge mit Restbetrag 0 (ausgeglichen):",
          k11.kw("account.invoice", "search_count", [[("type", "=", "out_invoice"), ("state", "=", "paid")]]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
