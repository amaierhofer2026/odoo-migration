"""Read-only Detailpruefung Bereich Valorisierung (Texte, Referenzen, Vergleich O11/O18).

Aufruf: python scripts/pruefe_valorisierung_details.py
"""
from __future__ import annotations

import json
import sys

sys.path.insert(0, "C:/Odoo-Test/scripts")
from _o11o18_client import o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}
MODELL = "itk_valorisierung.valorisierung"

k11, zl, zv = o11(), o18("lokal"), o18("vm")

print("=== 1. Odoo 11: Aktion, Menue und Ansichts-Texte ===")
a11 = k11.kw("ir.actions.act_window", "read", [[528], ["name", "res_model", "view_mode", "help",
                                                      "view_id"]], context=CTX)[0]
print("   Aktion 528: %s" % json.dumps(a11, ensure_ascii=False))
for v in k11.kw("ir.ui.view", "search_read", [[("model", "=", MODELL)], ["id", "name", "type",
                                                                          "arch_db"]], context=CTX):
    print("   Ansicht %-6s %-8s %-42s" % (v["id"], v["type"], v["name"]))
    print("      Arch: %s" % (v["arch_db"] or "")[:300].replace("\n", " "))
print("   Menue: %s" % k11.kw("ir.ui.menu", "search_read",
                              [[("action", "=", "ir.actions.act_window,528")], ["complete_name"]],
                              context=CTX))
print("   Feldbezeichnung account.invoice.valorisierung_id in Odoo 11: %s"
      % k11.kw("account.invoice", "fields_get", [["valorisierung_id"], ["string", "type", "required"]],
               context=CTX))

print("\n=== 2. Odoo 18: Aktion/Menue/Ansichten der Valorisierung ===")
for name, k in (("lokal", zl), ("vm", zv)):
    act = k.kw("ir.actions.act_window", "search_read",
               [[("res_model", "=", MODELL)], ["id", "name", "view_mode", "help"]], context=CTX)
    print("--- %s ---" % name)
    for a in act:
        print("   Aktion %s: %s | %s" % (a["id"], a["name"], a["view_mode"]))
        print("      Help: %s" % (a["help"] or "")[:160].replace("\n", " "))
    for v in k.kw("ir.ui.view", "search_read", [[("model", "=", MODELL)], ["id", "name", "type",
                                                                          "arch_db"]], context=CTX):
        print("   Ansicht %-6s %-8s %-44s" % (v["id"], v["type"], v["name"]))
    print("   Feldbezeichnung account.move.valorisierung_id in Odoo 18: %s"
          % k.kw("account.move", "fields_get", [["valorisierung_id"], ["string", "type", "required"]],
                 context=CTX))

print("\n=== 3. Vergleich der Datensaetze (Name, seq, Beschreibung) ===")
def hole(k):
    return {d["name"]: d for d in k.kw(MODELL, "search_read",
                                       [[], ["name", "seq", "description"]], context=CTX)}
n11, nl, nv = hole(k11), hole(zl), hole(zv)
print("   Odoo 11: %d | Odoo 18 lokal: %d | Odoo 18 VM: %d" % (len(n11), len(nl), len(nv)))
for name in sorted(set(n11) | set(nl)):
    e11, e18 = n11.get(name), nl.get(name)
    beschr11 = bool(e11 and (e11["description"] or "").strip())
    beschr18 = bool(e18 and (e18["description"] or "").strip())
    print("   %-46s O11: %s seq=%s | O18: %s seq=%s"
          % (name[:46], "da" if e11 else "-", e11["seq"] if e11 else "-",
             "da" if e18 else "-", e18["seq"] if e18 else "-"))
    if e11 and e18 and (beschr11 != beschr18):
        print("        Unterschied: Beschreibung O11 %s, O18 %s"
              % ("belegt" if beschr11 else "leer", "belegt" if beschr18 else "leer"))
print("   nur in Odoo 11: %s" % sorted(set(n11) - set(nl)))
print("   nur in Odoo 18: %s" % sorted(set(nl) - set(n11)))
print("   Namensunterschiede (Leerzeichen/Zeichen): %s"
      % [(a, b) for a in n11 for b in nl if a.strip().lower() == b.strip().lower() and a != b])

print("\n=== 4. Verwendung: wer verweist auf die Datensaetze? ===")
for name, k in (("Odoo 11", k11), ("Odoo 18 lokal", zl), ("Odoo 18 VM", zv)):
    print("--- %s ---" % name)
    for b in k.kw("ir.model.fields", "search_read",
                  [[("relation", "=", MODELL)], ["model", "name", "ttype"]], context=CTX):
        ids = k.kw(b["model"], "search", [[(b["name"], "!=", False)]], context=CTX)
        print("   %-30s %-20s belegt: %d" % (b["model"], b["name"], len(ids)))
        if b["model"] == "account.move" and len(ids) <= 12:
            for m in k.kw("account.move", "read", [ids, [b["name"], "name", "state"]], context=CTX):
                print("        %-16s %-10s -> %s" % (m["name"], m["state"], m[b["name"]]))
