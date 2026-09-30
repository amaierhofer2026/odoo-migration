"""Read-only Vergleich Odoo 18 lokal gegen VM: Menuebaum Abrechnung und Modulversionen.

Aufruf:  python scripts/vergleiche_abrechnung_lokal_vm.py
Odoo 11 wird hier nicht verwendet.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o18

CTX = {"lang": "de_DE", "ir.ui.menu.full_list": True}
WURZEL = "Rechnungsstellung"
MODULE = ["account", "account_invoice_line_number", "account_invoice_line_report", "account_payment",
          "account_peppol", "account_edi_ubl_cii", "account_qr_code_sepa", "analytic",
          "itk_valorisierung", "itk_projectcategory", "mass_email_invoice",
          "sale_merge_draft_invoice", "l10n_at", "l10n_de", "purchase", "sale",
          "stock_account", "project_account", "itk_subscription", "snailmail_account"]


def baum(k):
    alle = k.kw("ir.ui.menu", "search_read",
                [[], ["name", "parent_id", "sequence", "action"]], context=CTX)
    nach_id = {m["id"]: m for m in alle}

    def pfad(mid):
        teile = []
        while mid and mid in nach_id:
            m = nach_id[mid]
            teile.insert(0, m["name"])
            mid = m["parent_id"][0] if m["parent_id"] else False
        return " / ".join(teile)

    zeilen = []
    for m in alle:
        p = pfad(m["id"])
        if p.split(" / ")[0] == WURZEL:
            a = m["action"] or "-"
            modell = ""
            if a.startswith("ir.actions.act_window,"):
                aid = int(a.split(",")[1])
                try:
                    d = k.kw("ir.actions.act_window", "read", [[aid], ["res_model"]], context=CTX)
                    modell = d[0]["res_model"]
                except Exception:
                    modell = "?"
            zeilen.append("%s | %s | %s" % (p, modell, a))
    return sorted(zeilen)


def main() -> int:
    lade_env()
    k_lokal = o18("lokal")
    k_vm = o18("vm")
    a = baum(k_lokal)
    b = baum(k_vm)
    print("Menuezeilen unter %s: lokal %d | VM %d" % (WURZEL, len(a), len(b)))
    nur_lokal = [x for x in a if x not in b]
    nur_vm = [x for x in b if x not in a]
    print("nur lokal: %d | nur VM: %d" % (len(nur_lokal), len(nur_vm)))
    for x in nur_lokal:
        print("   nur lokal: %s" % x)
    for x in nur_vm:
        print("   nur VM:    %s" % x)

    print("\nModulversionen:")
    for name in MODULE:
        z = []
        for k, bez in ((k_lokal, "lokal"), (k_vm, "VM")):
            d = k.kw("ir.module.module", "search_read", [[("name", "=", name)],
                                                         ["state", "installed_version"]],
                     context={"lang": "de_DE"})
            z.append("%s=%s/%s" % (bez, d[0]["installed_version"] if d else "-",
                                   d[0]["state"] if d else "-"))
        marke = "" if z[0].split("=", 1)[1] == z[1].split("=", 1)[1] else "   <<< UNTERSCHIED"
        print("   %-28s %s | %s%s" % (name, z[0], z[1], marke))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
