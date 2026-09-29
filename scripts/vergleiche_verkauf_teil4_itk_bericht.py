"""Inhaltsvergleich der ITK-Verkaufsberichte Odoo 11 <-> Odoo 18.

Vergleicht die Dokumentvorlagen
  Odoo 11: sale.report_itk_saleorder_document
  Odoo 18: itk_reports.report_itk_saleorder_document
auf
  - Feldbezuege (Kunde, Adresse, Positionen, Preise, Steuern, Summen, Status, Kopf/Fuss)
  - sichtbare Textbausteine (Ueberschriften, Spaltenkoepfe, Hinweise)
  - Spaltenkoepfe der Positionstabelle (th)
  - Summenbloecke (amount_*)
  - steuerrelevante Bezuege (tax_id/amount_tax/tax_totals)
  - Statusabhaengigkeiten (state-Vergleiche)

Ergebnis: docs/_verkauf_teil4_itk_bericht_vergleich.json (gitignoriert)

Aufruf:
    python scripts/vergleiche_verkauf_teil4_itk_bericht.py
"""
from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP = {"lang": "de_DE"}
QUELLEN = {
    "o11": ("sale.report_itk_saleorder_document", o11()),
    "o18": ("itk_reports.report_itk_saleorder_document", o18("lokal")),
}
FELDER = {
    "kunde": [r"partner_id", r"partner_shipping_id", r"partner_invoice_id", r"commercial_partner_id"],
    "adresse": [r"\.street2?", r"\.city", r"\.zip", r"\.country_id", r"\.vat", r"\.phone", r"\.email",
                r"\.lang"],
    "positionen": [r"order_line", r"product_id", r"product_uom_qty", r"product_uom", r"\.name",
                   r"price_unit", r"discount", r"display_type"],
    "steuern": [r"tax_id", r"taxes", r"amount_tax", r"tax_totals"],
    "summen": [r"amount_untaxed", r"amount_total", r"amount_%", r"currency_id"],
    "status": [r"state", r"date_order", r"validity_date", r"confirmation_date", r"locked"],
    "kopf_fuss": [r"company_id", r"user_id", r"note", r"payment_term_id", r"incoterm", r"narration"],
    "kanaele": [r"team_id", r"source_id", r"campaign_id", r"medium_id"],
}


def hole(client, key):
    treffer = client.kw("ir.ui.view", "search_read", [[("key", "=", key)], ["id", "name", "key", "arch_db"]],
                        context=SP)
    return treffer[0]["arch_db"] if treffer else ""


def baue_aus(arch: str) -> dict:
    arch = arch or ""
    felder = {g: sorted({m.replace("\\b", "").replace("\\", "") for m in muster if re.search(m, arch)})
              for g, muster in FELDER.items()}
    texte = re.findall(r">([^<>{}]{3,120})<", arch)
    texte = [re.sub(r"&[a-z]+;", " ", t).strip() for t in texte]
    texte = [t for t in texte if t and not t.startswith(("t-", "/", "<!--"))]
    kopfzeilen = re.findall(r"<th[^>]*>(.*?)</th>", arch, flags=re.S)
    kopfzeilen = [re.sub(r"<[^>]+>", " ", k).strip() for k in kopfzeilen]
    status = sorted(set(re.findall(r"state\s*[!=]=\s*'([a-z_]+)'", arch)))
    summenspalten = sorted(set(re.findall(r"amount_[a-z_]+", arch)))
    return {
        "zeichen": len(arch),
        "felder": felder,
        "texte": sorted(set(texte)),
        "kopfzeilen": [k for k in kopfzeilen if k],
        "status_bezuege": status,
        "summenfelder": summenspalten,
        "anzahl_positionstabellen": len(re.findall(r"<table", arch)),
        "t_call_vorlagen": sorted(set(re.findall(r't-call="([^"]+)"', arch))),
        "css_bloecke": len(re.findall(r"<style", arch)),
    }


def main() -> int:
    ergebnis = {}
    for name, (key, client) in QUELLEN.items():
        arch = hole(client, key)
        ergebnis[name] = baue_aus(arch)
        ergebnis[name]["key"] = key
        print("%s: %s, %d Zeichen" % (name, key, len(arch)))

    a, b = ergebnis["o11"], ergebnis["o18"]
    print("\n--- Felder ---")
    for g in FELDER:
        fa, fb = a["felder"][g], b["felder"][g]
        print("  %-10s O11: %s" % (g, ", ".join(fa) or "-"))
        print("  %-10s O18: %s %s" % ("", ", ".join(fb) or "-",
                                      "" if set(fa) <= set(fb) else "FEHLT: %s" % sorted(set(fa) - set(fb))))
    print("\n--- Textbausteine: nur in O11 (%d) ---" % len(set(a["texte"]) - set(b["texte"])))
    for t in sorted(set(a["texte"]) - set(b["texte"]))[:25]:
        print("   O11> %s" % t[:90])
    print("\n--- Textbausteine: nur in O18 (%d) ---" % len(set(b["texte"]) - set(a["texte"])))
    for t in sorted(set(b["texte"]) - set(a["texte"]))[:25]:
        print("   O18> %s" % t[:90])
    print("\n--- Spaltenkoepfe ---")
    print("   O11: %s" % (a["kopfzeilen"] or "-"))
    print("   O18: %s" % (b["kopfzeilen"] or "-"))
    print("\n--- Summen/Steuern ---")
    print("   O11: %s | Status: %s" % (a["summenfelder"], a["status_bezuege"]))
    print("   O18: %s | Status: %s" % (b["summenfelder"], b["status_bezuege"]))
    print("\n--- Aufrufe/Struktur ---")
    print("   O11: Tabellen %d, t-call %s" % (a["anzahl_positionstabellen"], a["t_call_vorlagen"]))
    print("   O18: Tabellen %d, t-call %s" % (b["anzahl_positionstabellen"], b["t_call_vorlagen"]))

    ziel = os.path.join(REPO, "docs", "_verkauf_teil4_itk_bericht_vergleich.json")
    with open(ziel, "w", encoding="utf-8") as fh:
        json.dump(ergebnis, fh, ensure_ascii=False, indent=1)
    print("\nRohdaten: %s" % ziel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
