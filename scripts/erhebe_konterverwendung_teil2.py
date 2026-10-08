"""Read-only Belegsammlung Teil 2: Kontentypen Odoo 18, Steuerbezug, Kategorie-Kontenvorgabe,
Bezeichnungen 'Projektkategor'/'Kostenstellenkonten'.

Aufruf: python scripts/erhebe_konterverwendung_teil2.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}
ZIEL = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session131", "konten")
CODES = ["4000", "4001", "4100", "4110", "4200", "5000", "5010", "5011", "5050", "5051", "5052", "5090"]


def kontentypen(k, codes):
    vorhanden = k.kw("account.account", "fields_get", [[], ["type", "relation"]], context=CTX)
    felder = [f for f in ("code", "name", "account_type", "internal_group", "user_type_id", "reconcile",
                          "tax_ids", "active") if f in vorhanden]
    print("   Felder in account.account: %s" % felder)
    aus = []
    for a in k.kw("account.account", "search_read", [[("code", "in", codes)], felder], context=CTX, limit=0):
        typ = a.get("account_type") or (a.get("user_type_id")[1] if a.get("user_type_id") else None)
        gruppe = a.get("internal_group")
        steuern = [t[1] for t in (a.get("tax_ids") or [])]
        aus.append({"id": a["id"], "code": a["code"], "name": a["name"], "typ": typ, "gruppe": gruppe,
                    "steuern": steuern, "abstimmbar": a.get("reconcile"), "aktiv": a.get("active")})
        print("   %-6s %-52s typ=%-18s gruppe=%-10s Steuern=%s" % (a["code"], a["name"], typ, gruppe, steuern))
    return aus


def verwendung_und_steuern(k):
    """Odoo 11: Steuern auf den 8400-Belegzeilen und die meistgenutzten Konten."""
    zeilen = k.kw("account.move.line", "search_read",
                  [[("account_id.code", "=", "8400")], ["invoice_line_tax_ids", "move_id"]], context=CTX,
                  limit=200)
    from collections import Counter
    zaehler = Counter()
    for z in zeilen:
        for t in (z.get("invoice_line_tax_ids") or []):
            zaehler[t[1]] += 1
    print("   Steuern auf 8400-Belegzeilen (Stichprobe %d): %s" % (len(zeilen), zaehler.most_common(8)))
    # Belegarten
    arten = Counter()
    for z in zeilen:
        arten[str(z.get("move_id"))] += 1
    print("   Belege in der Stichprobe: %d" % len(arten))
    return {"steuern_stichprobe": zaehler.most_common(8)}


def kategorie_konten(k, bezeichnung):
    vorhanden = k.kw("product.category", "fields_get", [[], ["type", "relation", "company_dependent"]],
                     context=CTX)
    felder = [f for f in ("property_account_income_categ_id", "property_account_expense_categ_id")
              if f in vorhanden]
    print("   %s: Konto-Felder %s" % (bezeichnung, {f: {"typ": vorhanden[f].get("type"),
                                                       "company_dependent": vorhanden[f].get("company_dependent")}
                                                   for f in felder}))
    kats = k.kw("product.category", "search_read", [[], ["id", "complete_name"] + felder], context=CTX, limit=0)
    for c in kats:
        print("      id=%-3s %-32s Ertrag=%-24s Aufwand=%s"
              % (c["id"], c.get("complete_name"), c.get("property_account_income_categ_id"),
                 c.get("property_account_expense_categ_id")))
    # Firmenvorgabe: gibt es ein ir.default?
    try:
        d = k.kw("ir.default", "search_read", [[("model", "=", "product.category")],
                                              ["field_id", "company_id", "json_value"]], context=CTX, limit=0)
        print("      ir.default fuer product.category: %s" % d)
    except Exception as exc:  # noqa: BLE001
        print("      ir.default nicht abfragbar: %s" % str(exc)[:120])
    return kats


def steuern_im_ziel(k):
    print("   Odoo 18 Steuern (Auswahl Steuersatz 20%/10%):")
    for t in k.kw("account.tax", "search_read", [[("name", "ilike", "20")], ["name", "description", "amount",
                                                                            "type_tax_use"]],
                  context=CTX, limit=10):
        print("      %-40s %-24s %s%% %s" % (t["name"], t.get("description"), t["amount"], t["type_tax_use"]))
    return True


def bezeichnungen(k, bezeichnung, begriffe):
    aus = {}
    for b in begriffe:
        menues = k.kw("ir.ui.menu", "search_read", [[("name", "ilike", b)], ["id", "name", "complete_name"]],
                      context=CTX, limit=0)
        aktionen = k.kw("ir.actions.act_window", "search_read", [[("name", "ilike", b)],
                                                                ["id", "name", "res_model"]], context=CTX, limit=0)
        aus[b] = {"menues": [(m["name"], m["complete_name"]) for m in menues],
                  "aktionen": [(a["name"], a["res_model"]) for a in aktionen]}
        print("   %s '%s' Menues=%s Aktionen=%s" % (bezeichnung, b, aus[b]["menues"], aus[b]["aktionen"]))
    return aus


def quelle_company_dependent():
    """Odoo 18: wie werden Firmenvorgaben (company_dependent) gespeichert?"""
    print("\n=== Odoo 18 Quelle: Speicherung company_dependent ===")
    treffer = subprocess.run(["docker", "exec", "odoo18", "grep", "-rn", "ir.property",
                              "/usr/lib/python3/dist-packages/odoo/addons/base/models/ir_default.py"],
                             capture_output=True, text=True)
    print("   ir_default.py nennt ir.property: %d Zeilen" % len(treffer.stdout.strip().splitlines()))
    for name in ("ir_property.py", "ir_default.py"):
        r = subprocess.run(["docker", "exec", "odoo18", "sh", "-c",
                            "ls -1 /usr/lib/python3/dist-packages/odoo/addons/base/models/ | grep -i propert"],
                           capture_output=True, text=True)
        print("   Dateien mit 'propert': %s" % r.stdout.strip().replace("\n", ", ") or "keine")
        break
    r = subprocess.run(["docker", "exec", "odoo18", "sh", "-c",
                        "grep -rn \"company_dependent\" /usr/lib/python3/dist-packages/odoo/fields.py | head -12"],
                       capture_output=True, text=True)
    print("   fields.py company_dependent:\n%s" % r.stdout.strip()[:1500])
    r = subprocess.run(["docker", "exec", "odoo18", "sh", "-c",
                        "grep -rn \"def _get_company_dependent\\|def _set_company_dependent\\|ir.default\" "
                        "/usr/lib/python3/dist-packages/odoo/fields.py | head -12"],
                       capture_output=True, text=True)
    print("   Zugriff auf Firmenvorgabe:\n%s" % r.stdout.strip()[:1200])


def main() -> int:
    os.makedirs(ZIEL, exist_ok=True)
    k11, k18 = o11(), o18("lokal")
    daten = {}
    print("=== Odoo 11: Steuern und Verwendung von 8400 ===", flush=True)
    daten["o11_verwendung_8400"] = verwendung_und_steuern(k11)

    print("\n=== Odoo 11: Kategorie-Konten (je Kategorie) ===", flush=True)
    daten["o11_kategorien"] = kategorie_konten(k11, "Odoo 11")

    print("\n=== Odoo 18 lokal: Kandidatenkonten mit Typ ===", flush=True)
    daten["o18_kontentypen"] = kontentypen(k18, CODES)

    print("\n=== Odoo 18 lokal: Steuern ===", flush=True)
    steuern_im_ziel(k18)

    print("\n=== Odoo 18 lokal: Kategorie-Konten (je Kategorie) ===", flush=True)
    daten["o18_kategorien"] = kategorie_konten(k18, "Odoo 18")

    print("\n=== Bezeichnungen Odoo 11 ===", flush=True)
    daten["o11_bezeichnungen"] = bezeichnungen(k11, "Odoo 11", ["Projektkategor", "Kostenstellenkonten", "Kostenstellen"])
    print("\n=== Bezeichnungen Odoo 18 ===", flush=True)
    daten["o18_bezeichnungen"] = bezeichnungen(k18, "Odoo 18", ["Projektkategor", "Kostenstellenkonten", "Kostenstellen"])

    quelle_company_dependent()

    p = os.path.join(ZIEL, "konten_rohdaten_teil2.json")
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(daten, fh, ensure_ascii=False, indent=1, default=str)
    print("\nRohdaten: %s" % p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
