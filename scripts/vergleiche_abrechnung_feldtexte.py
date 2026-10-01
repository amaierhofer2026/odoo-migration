"""Abrechnung: Feldbezeichnungen der Konfiguration und Assistenten vergleichen (O11 gegen O18).

Vergleicht die sichtbaren Feldbezeichnungen (de_DE) technisch gleichnamiger Felder und listet
zusaetzlich Bezeichnungen, die es nur in Odoo 11 gibt. Odoo 11 wird ausschliesslich gelesen.

Aufruf: python scripts/vergleiche_abrechnung_feldtexte.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18

MODELLE = [
    ("account.tax", "Steuern"),
    ("account.journal", "Journale"),
    ("res.currency", "Waehrungen"),
    ("account.fiscal.position", "Steuerzuordnung"),
    ("account.payment.term", "Zahlungsbedingungen"),
    ("account.analytic.account", "Kostenstellen"),
    ("account.analytic.plan", "Kostenstellenplaene"),
    ("res.partner.bank", "Bankkonten"),
    ("product.category", "Produktkategorien"),
    ("account.payment.register", "Assistent Zahlung erfassen"),
    ("account.move.reversal", "Assistent Gutschrift/Storno"),
    ("account.payment.method.line", "Zahlungsmethoden"),
    ("account.payment.term.line", "Zahlungsbedingung Zeilen"),
]

# Fachlich gleichbedeutende Felder mit unterschiedlichem technischen Namen (O11 -> O18)
ZUORDNUNGEN = {
    "account.tax": {"type_tax_use": "type_tax_use"},
    "account.journal": {"default_debit_account_id": "default_account_id"},
    "account.invoice.refund": {"description": "reason"},
}


def felder(k, modell):
    try:
        f = k.kw(modell, "fields_get", [[], ["string", "type"]], context={"lang": "de_DE"})
    except Exception:
        return None
    return {name: (daten.get("string") or "", daten.get("type") or "") for name, daten in f.items()}


def main() -> int:
    k11, k18 = o11(), o18("lokal")
    for modell, titel in MODELLE:
        f11, f18 = felder(k11, modell), felder(k18, modell)
        if f11 is None or f18 is None:
            print("\n=== %s (%s): nur in %s vorhanden ===" % (titel, modell, "Odoo 18" if f11 is None else "Odoo 11"))
            continue
        print("\n=== %s (%s) ===" % (titel, modell))
        unterschiede = []
        for name, (text11, _typ) in sorted(f11.items()):
            if name not in f18:
                continue
            text18 = f18[name][0]
            if text11.strip() and text18.strip() and text11.strip() != text18.strip():
                unterschiede.append((name, text11, text18))
        for name, text11, text18 in unterschiede:
            print("   %-32s O11: %-38s O18: %s" % (name, text11[:38], text18[:40]))
        if not unterschiede:
            print("   keine abweichenden Bezeichnungen bei gleichnamigen Feldern")
        nur11 = sorted(set(f11) - set(f18))
        if nur11:
            print("   nur in Odoo 11: %s" % [f11[n][0] or n for n in nur11][:12])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
