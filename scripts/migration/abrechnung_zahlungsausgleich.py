# -*- coding: utf-8 -*-
"""Abrechnung: Zahlungsausgleich nach der Rechnungsmigration (Odoo 18).

Zweck: Nach ``abrechnung_migration.py`` sicherstellen, dass der Zahlungsstatus dem
Odoo-11-Stand entspricht:

1. Zahlungen im Zustand ``draft``/``in_process`` werden gebucht.
2. Rechnungen, die in Odoo 11 **bezahlt** sind, in Odoo 18 aber noch einen offenen Rest
   haben, erhalten einen Ausgleich. Wo Odoo 11 keinen Zahlungsbeleg kennt (227 Faelle),
   wird eine Zahlung im Bankjournal mit klarer Herkunft im Memo angelegt
   ("Odoo 11: als bezahlt markiert, ohne Zahlungsbeleg"). Ohne sie wuerden 227 bezahlte
   Rechnungen als offen erscheinen und die Debitorenbilanz waere zu hoch.

Offene Odoo-11-Rechnungen (Status ``open``) bleiben offen - sie werden nicht ausgeglichen.
Rechnung und Gutschrift werden **nicht** gegeneinander verrechnet: das setzt in Odoo 18 den
Status "storniert" (reversed) und widerspricht dem Odoo-11-Zustand "bezahlt".
Das Skript ist idempotent: gebuchte Zahlungen und ausgeglichene Belege werden uebersprungen.

Aufruf:
    python scripts/migration/abrechnung_zahlungsausgleich.py --instanz lokal
    python scripts/migration/abrechnung_zahlungsausgleich.py --instanz lokal --ausfuehren --ich-habe-freigabe
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import Counter

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HIER))
import _o11o18_client as client  # noqa: E402

CTX11 = {"lang": "de_DE", "active_test": False}
CTX18 = {"lang": "de_DE", "active_test": False}
MODELL = "account.move"
JOURNAL_BANK = "BNK1"
TOLERANZ = 0.004


def m2o(w):
    return w[0] if isinstance(w, (list, tuple)) and w else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    ap.add_argument("--ausfuehren", action="store_true")
    ap.add_argument("--ich-habe-freigabe", action="store_true")
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()
    if args.ausfuehren and not args.ich_habe_freigabe:
        print("ABBRUCH: Schreiblauf nur mit --ich-habe-freigabe (Freigabe von Anna).")
        return 2

    o11 = client.o11()
    o18 = client.o18(args.instanz)
    schreiben = args.ausfuehren
    print("=== Zahlungsausgleich %s | %s ===" % (
        args.instanz, "SCHREIBEN" if schreiben else "TROCKENLAUF"))

    def kw(modell, methode, args_, **kwargs):
        if not schreiben and methode in ("create", "write", "unlink"):
            raise RuntimeError("Schreibaufruf im Trockenlauf: %s.%s" % (modell, methode))
        return o18.kw(modell, methode, args_, **kwargs)

    stat = Counter()
    fehler = []

    # 1) Zahlungen buchen
    offene_zahlungen = o18.kw("account.payment", "search_read",
                             [[["itk_o11_id", "!=", False],
                               ["state", "in", ["draft", "in_process"]]],
                              ["id", "itk_o11_id", "amount"]], context=CTX18, limit=100000)
    print("Zahlungen im Ziel: nicht gebucht = %d" % len(offene_zahlungen))
    for p in offene_zahlungen:
        if not schreiben:
            stat["wuerde_buchen"] += 1
            continue
        try:
            kw("account.payment", "action_post", [[p["id"]]])
            stat["gebucht"] += 1
        except Exception as exc:  # noqa: BLE001
            stat["fehler"] += 1
            fehler.append({"art": "post", "o18_id": p["id"], "fehler": str(exc)[:200]})

    # 2) Ausgleich der bezahlten Rechnungen
    ids11 = o11.kw("account.invoice", "search", [[["state", "=", "paid"]]], context=CTX11,
                   limit=200000)
    bezahlt11 = set(ids11)
    journal = None
    for j in o18.kw("account.journal", "search_read", [[["code", "=", JOURNAL_BANK]],
                                                       ["id"]], context=CTX18):
        journal = j["id"]
    offen = o18.kw(MODELL, "search_read",
                   [[["itk_o11_id", "!=", False], ["state", "=", "posted"],
                     ["payment_state", "in", ["not_paid", "partial"]]],
                    ["id", "itk_o11_id", "name", "partner_id", "amount_residual",
                     "invoice_date", "date", "move_type"]], context=CTX18, limit=100000)
    zu_tun = [m for m in offen if m["itk_o11_id"] in bezahlt11
              and (m["amount_residual"] or 0) > TOLERANZ]
    print("Offene Belege: %d | davon in Odoo 11 bezahlt (auszugleichen): %d | Rest %.2f"
          % (len(offen), len(zu_tun), round(sum(m["amount_residual"] for m in zu_tun), 2)))
    if args.limit:
        zu_tun = zu_tun[:args.limit]
    for m in zu_tun:
        rest = round(m["amount_residual"], 2)
        if not schreiben:
            stat["wuerde_ausgleichen"] += 1
            continue
        try:
            # vorhandene, noch nicht ausgeglichene Zahlung zuerst versuchen
            pay_zeilen = o18.kw("account.move.line", "search",
                                [[["move_id", "in", o18.kw(MODELL, "search",
                                                           [[["itk_o11_id", "=", m["itk_o11_id"]],
                                                             ["move_type", "in",
                                                              ["out_invoice", "out_refund"]]]],
                                                           context=CTX18)],
                                  ["account_id.account_type", "=", "asset_receivable"],
                                  ["reconciled", "=", False]]], context=CTX18)
            frei = o18.kw("account.move.line", "search",
                          [[["account_id.account_type", "=", "asset_receivable"],
                            ["reconciled", "=", False], ["payment_id", "!=", False],
                            ["partner_id", "=", m["partner_id"][0]]]], context=CTX18,
                          limit=200)
            if pay_zeilen and frei:
                try:
                    o18.kw("account.move.line", "reconcile", [pay_zeilen + frei],
                           context=CTX18)
                    nach = o18.kw(MODELL, "read", [[m["id"]], ["amount_residual"]],
                                  context=CTX18)[0]["amount_residual"]
                    if (nach or 0) <= TOLERANZ:
                        stat["ausgeglichen_bestehend"] += 1
                        continue
                except Exception:  # noqa: BLE001
                    pass
            # Gutschrift = Geld zurueck an den Kunden (outbound), Rechnung = Eingang.
            art = "outbound" if m["move_type"] == "out_refund" else "inbound"
            # Gebuchte Belege haben immer ein Buchungsdatum; es ist in Odoo 18 Pflicht.
            datum = m["invoice_date"] or m["date"]
            pay = kw("account.payment", "create", [{
                "payment_type": art, "partner_type": "customer",
                "partner_id": m["partner_id"][0], "amount": rest,
                "date": datum,
                "journal_id": journal,
                "memo": "Odoo 11: als bezahlt markiert, ohne Zahlungsbeleg (%s)"
                        % (m["name"] or ""),
            }])
            pay = pay[0] if isinstance(pay, list) else pay
            kw("account.payment", "action_post", [[pay]])
            pay_line = o18.kw("account.move.line", "search",
                              [[["payment_id", "=", pay],
                                ["account_id.account_type", "=", "asset_receivable"]]],
                              context=CTX18)
            soll = o18.kw("account.move.line", "search",
                          [[["move_id", "=", m["id"]],
                            ["account_id.account_type", "=", "asset_receivable"],
                            ["reconciled", "=", False]]], context=CTX18)
            # Odoo 18 bucht die Forderung je nach Partner auf 2000 (Inland) oder 2100
            # (EU). Die Zahlung nutzt immer das Partnerkonto - fuer den Ausgleich muss
            # sie auf dem Konto der Rechnung stehen.
            if pay_line and soll:
                soll_konto = o18.kw("account.move.line", "read", [soll, ["account_id"]],
                                    context=CTX18)[0]["account_id"][0]
                pay_konto = o18.kw("account.move.line", "read", [pay_line, ["account_id"]],
                                   context=CTX18)[0]["account_id"][0]
                if soll_konto != pay_konto:
                    kw("account.move.line", "write", [pay_line, {"account_id": soll_konto}])
                    stat["konto_angeglichen"] += 1
            if pay_line and soll:
                kw("account.move.line", "reconcile", [pay_line + soll])
                stat["ersatzzahlung"] += 1
            else:
                stat["ohne_zeile"] += 1
        except Exception as exc:  # noqa: BLE001
            stat["fehler"] += 1
            fehler.append({"art": "ausgleich", "beleg": m["name"],
                           "o11_id": m["itk_o11_id"], "fehler": str(exc)[:200]})

    # 3) Nachmessung
    print()
    print("--- Ergebnis ---")
    print("gebucht .................... %d" % stat["gebucht"])
    print("Ausgleich ueber vorhandene Zahlung %d" % stat["ausgeglichen_bestehend"])
    print("Ersatzzahlung angelegt ..... %d" % stat["ersatzzahlung"])
    print("Verrechnung Rechnung/Gutschrift %d" % stat["verrechnet"])
    print("Forderungskonto angeglichen %d" % stat["konto_angeglichen"])
    print("Fehler ..................... %d" % stat["fehler"])
    if not schreiben:
        print("wuerde buchen .............. %d" % stat["wuerde_buchen"])
        print("wuerde ausgleichen ......... %d" % stat["wuerde_ausgleichen"])
    else:
        alle = o18.kw(MODELL, "search", [[["itk_o11_id", "!=", False]]], context=CTX18,
                      limit=200000)
        rest = 0.0
        for i in range(0, len(alle), 1000):
            for x in o18.kw(MODELL, "read", [alle[i:i + 1000], ["amount_residual"]],
                            context=CTX18):
                rest += x["amount_residual"] or 0
        zustand = Counter()
        for g in o18.kw(MODELL, "read_group", [[["itk_o11_id", "!=", False]],
                                              ["payment_state", "payment_state"],
                                              ["payment_state"]], context=CTX18):
            zustand[g["payment_state"]] = g["payment_state_count"]
        print("Offener Rest im Ziel ...... %.2f" % round(rest, 2))
        print("Zahlungsstatus ............ %s" % dict(zustand))
    if fehler:
        for f in fehler[:10]:
            print("  %s" % f)
    return 0 if stat["fehler"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
