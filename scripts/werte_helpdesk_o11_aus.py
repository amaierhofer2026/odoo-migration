"""Wertet die Odoo-11-Helpdesk-Rohdaten aus und druckt eine lesbare Bestandsaufnahme.

Aufruf: python scripts/werte_helpdesk_o11_aus.py [--datei PFAD] [--modell MODELL]
"""
from __future__ import annotations

import argparse
import json
import os

STD = os.path.join(os.environ.get("USERPROFILE", "."), "Desktop",
                   "Odoo18-Helpdesk-Session132", "rohdaten", "helpdesk_o11.json")


def kurz(text, n=90):
    text = " ".join(str(text or "").split())
    return text if len(text) <= n else text[: n - 3] + "..."


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", default=STD)
    ap.add_argument("--modell", default="")
    a = ap.parse_args()
    with open(a.datei, encoding="utf-8") as fh:
        d = json.load(fh)

    print("=" * 100)
    print("ODOO 11 HELPDESK (website_support) - Bestandsaufnahme")
    print("=" * 100)

    print("\n--- Module ---")
    for m in d["module"]:
        print("  %-42s %-45s %-12s %s" % (m["name"], kurz(m["shortdesc"], 45), m["state"],
                                          m["installed_version"]))

    print("\n--- Modelle und Bestand ---")
    for m in d["modelle"]:
        print("  %-42s %-45s %6s" % (m["model"], kurz(m["name"], 45),
                                     d["bestand"].get(m["model"], "?")))

    ziele = [a.modell] if a.modell else [
        "website.support.ticket", "website.support.ticket.states",
        "website.support.ticket.categories", "website.support.ticket.subcategory",
        "website.support.ticket.subcategory.field", "website.support.ticket.priority",
        "website.support.ticket.field", "website.support.ticket.message",
        "website.support.ticket.close", "website.support.ticket.compose",
        "website.support.ticket.approval", "website.support.sla",
        "website.support.sla.response", "website.support.sla.alert",
        "website.support.department", "website.support.ticket.tag",
    ]

    for modell in ziele:
        f = d["felder"].get(modell)
        if not f or "__fehler__" in f:
            print("\n--- %s: keine Felder ---" % modell)
            continue
        print("\n--- Felder %s (%d) ---" % (modell, len(f)))
        for name in sorted(f):
            fd = f[name]
            teile = [fd.get("type") or "?"]
            if fd.get("required"):
                teile.append("PFLICHT")
            if fd.get("readonly"):
                teile.append("readonly")
            if fd.get("relation"):
                teile.append("->" + str(fd["relation"]))
            if fd.get("selection"):
                try:
                    sel = ", ".join("%s=%s" % (s[0], s[1]) for s in fd["selection"][:14])
                except Exception:  # noqa: BLE001
                    sel = str(fd["selection"])[:120]
                teile.append("[" + sel + "]")
            if fd.get("store") is False:
                teile.append("nicht gespeichert")
            print("  %-34s %-42s %s" % (name, kurz(fd.get("string"), 42), "; ".join(teile)))

    print("\n--- Menues (Support/Ticket/Help) ---")
    for m in d["menues_filter"]:
        print("  %-4s %-70s seq=%-4s action=%s" % (m["id"], kurz(m["complete_name"], 70),
                                                   m["sequence"], m["action"] or "-"))

    print("\n--- Fensteraktionen ---")
    for x in d["aktionen"]:
        print("  %-46s %-30s %-18s domain=%s" % (x["res_model"], kurz(x["name"], 30),
                                                 x["view_mode"], kurz(x["domain"], 60)))

    print("\n--- Ansichten ---")
    for v in d["ansichten"]:
        print("  %-36s %-12s prio=%-4s %-40s inherit=%s" % (
            v["model"], v["type"], v["priority"], kurz(v["name"], 40),
            v["inherit_id"] or "-"))

    print("\n--- Gruppen (Support/Ticket/Help) ---")
    for g in d["gruppen"]:
        print("  %-4s %-44s %s  Benutzer=%s" % (
            g["id"], kurz(g["name"], 44),
            (g["category_id"] or [None, "-"])[1] if isinstance(g["category_id"], list) else "-",
            len(g["users"])))

    print("\n--- Zugriffsrechte je Gruppe ---")
    for r in d["zugriff"]:
        print("  %-36s %-46s R=%s W=%s C=%s D=%s" % (
            kurz((r["model_id"] or [None, "?"])[1] if isinstance(r["model_id"], list) else "?", 36),
            kurz((r["group_id"] or [None, "keine Gruppe"])[1] if isinstance(r["group_id"], list) else "keine Gruppe", 46),
            r["perm_read"], r["perm_write"], r["perm_create"], r["perm_unlink"]))

    print("\n--- Record Rules ---")
    for r in d["record_rules"]:
        print("  %-40s %-36s %s" % (kurz(r["name"], 40),
                                    kurz((r["model_id"] or [None, "?"])[1], 36),
                                    kurz(r["domain_force"], 60)))

    for schluessel, titel in (("mail_vorlagen", "Mail-Vorlagen"), ("mail_aliase", "Mail-Aliase"),
                              ("sequenzen", "Sequenzen"), ("cron", "Cron"),
                              ("server_actions", "Server-Aktionen"),
                              ("config_parameter", "Konfigurationswerte")):
        wert = d.get(schluessel)
        print("\n--- %s ---" % titel)
        if isinstance(wert, dict):
            print("  FEHLER:", kurz(wert.get("__fehler__"), 200))
        elif not wert:
            print("  (keine)")
        else:
            for x in wert:
                print("  " + kurz(json.dumps(x, ensure_ascii=False), 170))

    print("\n--- Verteilung ---")
    for modell, gruppen in d.get("verteilung", {}).items():
        print("  %s:" % modell)
        if isinstance(gruppen, str):
            print("     ", kurz(gruppen, 150))
            continue
        for g in gruppen:
            werte = {k: v for k, v in g.items() if k not in ("__count", "__domain")}
            print("     %-100s __count=%s" % (kurz(json.dumps(werte, ensure_ascii=False), 100),
                                              g.get("__count")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
