"""Read-only Bestandsaufnahme Abrechnung Teil 1: Module, Modelle, Nutzungszahlen.

Aufruf:  python scripts/analyse_abrechnung_teil1.py [--instanz lokal|vm]
Odoo 11 Prod wird ausschliesslich lesend verwendet.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o11, o18

MODUL_MUSTER = ["account", "invoice", "payment", "valorisier", "analytic", "l10n_at", "l10n_de",
                "mass_email", "merge", "line_number", "line_report", "peppol", "qr_code",
                "reconcile", "voucher", "aged", "print_journal", "followup", "bi_"]

MODELLE = [
    "account.invoice", "account.invoice.line", "account.invoice.report", "account.journal",
    "account.payment", "account.payment.term", "account.payment.term.line", "account.tax",
    "account.tax.report", "account.account", "account.account.type", "account.fiscal.position",
    "account.bank.statement", "account.bank.statement.line", "account.analytic.account",
    "account.analytic.line", "account.analytic.tag", "account.analytic.plan",
    "account.analytic.distribution.model", "account.cash.rounding", "account.reconcile.model",
    "account.partial.reconcile", "account.full.reconcile", "account.print.journal",
    "account.aged.trial.balance", "account.move", "account.move.line", "account.move.reversal",
    "account.payment.register", "payment.acquirer", "payment.provider", "payment.method",
    "payment.transaction", "itk_valorisierung.valorisierung", "res.currency", "res.currency.rate",
    "account.asset", "account.tax.report.line", "account.report", "account.journal.group",
    "account.bank.statement.line", "account.move.send", "account.automatic.entry",
]


def modul_liste(k):
    """Alle Module holen und lokal filtern (Domain-Klammern sind in Odoo eine UND-Verknuepfung)."""
    daten = {}
    for m in k.kw("ir.module.module", "search_read",
                  [[], ["name", "shortdesc", "state", "installed_version", "author", "license"]],
                  context={"lang": "de_DE"}, order="name"):
        daten[m["name"]] = m
    return daten


def modell_zaehlen(k, modell):
    try:
        n = k.kw(modell, "search_count", [[]])
    except Exception as fehler:
        return ("FEHLT", str(fehler)[:80])
    return ("ok", n)


def verteilung(k, modell, feld, werte):
    aus = {}
    for w in werte:
        try:
            aus[w] = k.kw(modell, "search_count", [[[(feld, "=", w)]]])
        except Exception:
            aus[w] = "?"
    return aus


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    a = p.parse_args()
    lade_env()
    k11 = o11()
    k18 = o18(a.instanz)
    ausgabe = {}

    # ---------- A) Module ----------
    m11 = modul_liste(k11)
    m18 = modul_liste(k18)
    print("=== A) MODULE (Name | O11 | O18-%s | Version O11 / O18) ===" % a.instanz)
    print("Module gesamt O11: %d (davon installiert %d) | O18: %d (installiert %d)"
          % (len(m11), sum(1 for v in m11.values() if v["state"] == "installed"),
             len(m18), sum(1 for v in m18.values() if v["state"] == "installed")))
    for name in sorted(set(m11) | set(m18)):
        if not any(m in name for m in MODUL_MUSTER):
            continue
        z11 = m11.get(name, {}).get("state", "-")
        z18 = m18.get(name, {}).get("state", "-")
        print("  %-38s %-12s %-12s %s / %s" % (
            name, z11, z18,
            m11.get(name, {}).get("installed_version") or "-",
            m18.get(name, {}).get("installed_version") or "-"))
    ausgabe["module"] = {"o11": m11, "o18": m18}

    # ---------- B) Modelle ----------
    print("\n=== B) MODELLE (Datensaetze) ===")
    for modell in MODELLE:
        s11, n11 = modell_zaehlen(k11, modell)
        s18, n18 = modell_zaehlen(k18, modell)
        if s11 == s18 == "FEHLT":
            continue
        print("  %-42s O11: %-8s %s | O18: %-8s %s" % (modell, s11, n11, s18, n18))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
