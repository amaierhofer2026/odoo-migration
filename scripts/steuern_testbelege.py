"""Testbelege fuer die Steuerpruefung (Abrechnung > Konfiguration > Steuern).

Legt in der TESTinstanz je einen Entwurf an, prueft die Steuerlogik, bucht und wiederholt das fuer
Verkauf (Umsatzsteuer 20% Ust) und Einkauf (Vorsteuer 20% Vst). Auf Wunsch werden die Belege
wieder entfernt (Entwurf -> loeschen). Es wird nur die Testdatenbank angefasst (ODOO18_DB geprueft).

Aufruf:
    python scripts/steuern_testbelege.py --instanz lokal|vm --anlegen
    python scripts/steuern_testbelege.py --instanz lokal|vm --entfernen
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o18  # noqa: E402

ZIEL_DB = "odoo18_test"
CTX = {"lang": "de_DE"}
PROTOKOLL = os.path.join(os.environ.get("LOCALAPPDATA", "/tmp"), "Temp", "steuern_testbelege.json")


def rpc(k, modell, methode, args, was, **kwargs):
    try:
        return k.kw(modell, methode, args, context=CTX, **kwargs)
    except Exception as fehler:
        raise SystemExit("ABBRUCH: %s fehlgeschlagen (%s.%s): %s"
                         % (was, modell, methode, str(fehler)[:300]))


def anlegen(k):
    steuern = {t["name"]: t["id"] for t in
               rpc(k, "account.tax", "search_read", [[("name", "in", ["20% Ust", "20% Vst"])],
                                                     ["id", "name"]], "Steuern lesen")}
    if len(steuern) != 2:
        raise SystemExit("ABBRUCH: Steuern '20% Ust'/'20% Vst' nicht eindeutig gefunden: %s" % steuern)
    partner = rpc(k, "res.partner", "search", [[("customer_rank", ">", 0)]], "Kundenpartner suchen",
                  limit=1)
    lieferant = rpc(k, "res.partner", "search", [[("supplier_rank", ">", 0)]], "Lieferanten suchen",
                    limit=1)
    if not partner or not lieferant:
        raise SystemExit("ABBRUCH: kein Kunden- oder Lieferantenpartner im Zielbestand.")
    angelegt = []
    faelle = (("out_invoice", partner[0], "20% Ust", "ITK-STEUERTEST Verkauf 20% USt"),
              ("in_invoice", lieferant[0], "20% Vst", "ITK-STEUERTEST Einkauf 20% Vst"))
    for move_type, pid, steuer, bezeichnung in faelle:
        werte = {"move_type": move_type, "partner_id": pid, "invoice_date": "2026-10-08",
                 "ref": bezeichnung,
                 "invoice_line_ids": [(0, 0, {"name": bezeichnung, "quantity": 1.0,
                                             "price_unit": 100.0,
                                             "tax_ids": [(6, 0, [steuern[steuer]])]})]}
        mid = rpc(k, "account.move", "create", [werte], "Testbeleg anlegen (%s)" % move_type)
        angelegt.append({"modell": "account.move", "id": mid, "art": move_type, "steuer": steuer})
        z = rpc(k, "account.move", "read", [[mid], ["name", "state", "amount_untaxed", "amount_tax",
                                                    "amount_total"]], "Testbeleg lesen")[0]
        print("   angelegt %-12s %-46s Entwurf: ohne=%.2f Steuer=%.2f total=%.2f"
              % (move_type, bezeichnung, z["amount_untaxed"], z["amount_tax"], z["amount_total"]))
        rpc(k, "account.move", "action_post", [[mid]], "Testbeleg buchen (%s)" % move_type)
        z = rpc(k, "account.move", "read", [[mid], ["name", "state", "amount_untaxed", "amount_tax",
                                                    "amount_total"]], "Testbeleg lesen")[0]
        print("   gebucht  %-12s Nummer=%-14s Zustand=%-8s ohne=%.2f Steuer=%.2f total=%.2f"
              % (move_type, z["name"], z["state"], z["amount_untaxed"], z["amount_tax"], z["amount_total"]))
        for pos in rpc(k, "account.move.line", "search_read",
                       [[("move_id", "=", mid)],
                        ["account_id", "name", "debit", "credit", "tax_line_id", "tax_ids"]],
                       "Buchungszeilen lesen"):
            print("      %-34s %-38s Soll=%-9.2f Haben=%-9.2f Steuerzeile=%s Steuern=%s"
                  % (pos["account_id"][1][:34], str(pos["name"])[:38], pos["debit"], pos["credit"],
                     pos["tax_line_id"][1] if pos["tax_line_id"] else "-", pos["tax_ids"]))
        steuerzeilen = rpc(k, "account.move", "read", [[mid], ["line_ids"]], "Buchungszeilen")[0]
        for pos in rpc(k, "account.move.line", "read", [steuerzeilen["line_ids"],
                                                        ["account_id", "tax_line_id", "credit", "debit"]],
                       "Steuerzeilen pruefen"):
            if pos["tax_line_id"]:
                print("      -> Steuerbuchung auf Konto %s (Steuer %s), Betrag %.2f"
                      % (pos["account_id"][1], pos["tax_line_id"][1], pos["debit"] or pos["credit"]))
    json.dump({"angelegt": angelegt}, open(PROTOKOLL, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\nProtokoll: %s" % PROTOKOLL)
    return 0


def entfernen(k):
    if not os.path.exists(PROTOKOLL):
        raise SystemExit("ABBRUCH: kein Protokoll %s - nichts zu entfernen." % PROTOKOLL)
    eintraege = json.load(open(PROTOKOLL, encoding="utf-8")).get("angelegt", [])
    entfernt = 0
    for e in eintraege:
        if not rpc(k, "account.move", "search", [[("id", "=", e["id"])]], "Existenz pruefen"):
            continue
        try:
            rpc(k, "account.move", "button_draft", [[e["id"]]], "Testbeleg auf Entwurf setzen")
        except SystemExit as fehler:
            print("   Hinweis: %s" % str(fehler)[:140])
        rpc(k, "account.move", "unlink", [[e["id"]]], "Testbeleg entfernen")
        entfernt += 1
    print("Entfernt: %d Testbelege" % entfernt)
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    p.add_argument("--anlegen", action="store_true")
    p.add_argument("--entfernen", action="store_true")
    a = p.parse_args()
    env = lade_env()
    if env.get("ODOO18_DB") != ZIEL_DB:
        raise SystemExit("ABBRUCH: Ziel-DB ist %r, erlaubt ist nur %r." % (env.get("ODOO18_DB"), ZIEL_DB))
    if not (a.anlegen or a.entfernen):
        raise SystemExit("ABBRUCH: --anlegen oder --entfernen angeben.")
    k = o18(a.instanz)
    print("Ziel: %s (%s)" % (a.instanz, ZIEL_DB))
    return anlegen(k) if a.anlegen else entfernen(k)


if __name__ == "__main__":
    raise SystemExit(main())
