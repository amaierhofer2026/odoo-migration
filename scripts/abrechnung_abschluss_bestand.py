"""Bestandsaufnahme fuer den Abschlusscheck Abrechnung (read-only).

Aufruf: python scripts/abrechnung_abschluss_bestand.py lokal|vm datei.json

Schreibt Anzahlen der migrationsrelevanten Modelle, Belegsummen, Restbetraege, Statuswerte,
historische Nummern, Kategorien und Steuern in eine JSON-Datei - Grundlage fuer den
Vorher/Nachher-Vergleich (Punkt 8 des Abschlussauftrags).
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o18  # noqa: E402

CTX = {"lang": "de_DE"}
inst = sys.argv[1] if len(sys.argv) > 1 else "vm"
ziel = sys.argv[2] if len(sys.argv) > 2 else None
k = o18(inst)

MODELLE = ["account.move", "account.move.line", "account.payment", "account.payment.term",
           "res.partner", "product.template", "product.product", "product.category",
           "account.tax", "account.journal", "account.account", "sale.subscription",
           "product.pricelist", "product.pricelist.item"]

stand = {"instanz": inst, "anzahl": {}, "belege": {}, "kategorien": [], "konten_blob": None}
for m in MODELLE:
    stand["anzahl"][m] = k.kw(m, "search_count", [[]], context=CTX)

# Belege: Nummer, Odoo-11-Nummer, Zustand, Summe, Rest - sortiert nach Nummer (stabiler Digest)
for mv in k.kw("account.move", "search_read",
               [[], ["name", "itk_o11_invoice_number", "move_type", "state", "payment_state",
                     "amount_total", "amount_residual"]], context=CTX):
    schluessel = "%s|%s|%s" % (mv["name"] or "Entwurf", mv["itk_o11_invoice_number"] or "",
                               mv["move_type"])
    stand["belege"][schluessel] = {"state": mv["state"], "payment_state": mv["payment_state"],
                                   "summe": round(mv["amount_total"], 2),
                                   "rest": round(mv["amount_residual"], 2)}
stand["kategorien"] = sorted(x["complete_name"] for x in k.kw(
    "product.category", "search_read", [[], ["complete_name"]], context=CTX))
stand["produkte"] = sorted(x["name"] for x in k.kw("product.template", "search_read",
                                                   [[], ["name"]], context=CTX))
stand["partner"] = sorted(x["name"] for x in k.kw("res.partner", "search_read", [[], ["name"]],
                                                  context=CTX))

print("Bestand %s: %s" % (inst, json.dumps(stand["anzahl"], sort_keys=True)))
print("Belege: %d | Kategorien: %d | Produkte: %d | Partner: %d"
      % (len(stand["belege"]), len(stand["kategorien"]), len(stand["produkte"]),
         len(stand["partner"])))
if ziel:
    with open(ziel, "w", encoding="utf-8") as fh:
        json.dump(stand, fh, ensure_ascii=False, indent=1, sort_keys=True)
    print("gespeichert: %s" % ziel)
