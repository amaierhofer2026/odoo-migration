"""Read-only: Ansichtsart je Menuepunkt im Bereich Abrechnung (Odoo 11 gegen Odoo 18).

Geht die Menuebaeume unter der App "Abrechnung"/"Rechnungsstellung" durch und stellt je Menuepunkt
gegenueber:
  Modell, Ansichtsarten (view_mode des Fensters), gebundene Ansicht, Anzahl Datensaetze.
Odoo 11 wird ausschliesslich gelesen. Keine Aenderung, keine Datenmigration.

Aufruf: python scripts/vergleiche_abrechnung_menue_ansichten.py
"""
from __future__ import annotations

import sys

sys.path.insert(0, "C:/Odoo-Test/scripts")
from _o11o18_client import o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}
WURZEL = ("Abrechnung", "Rechnungsstellung", "Invoicing")


def menuebaum(k):
    """Menuepunkte mit Aktion je System (read-only)."""
    alle = k.kw("ir.ui.menu", "search_read", [[], ["name", "parent_id", "action"]], context=CTX)
    nach_id = {m["id"]: m for m in alle}

    def pfad(m):
        teile, cur, tiefe = [], m, 0
        while cur is not None and tiefe < 6:
            teile.append(cur["name"])
            cur = nach_id.get(cur["parent_id"][0]) if cur["parent_id"] else None
            tiefe += 1
        return "/".join(reversed(teile))

    ergebnis = {}
    for m in alle:
        if not m["action"]:
            continue
        p = pfad(m)
        if not p.startswith(WURZEL):
            continue
        art, xmlid, aid = (str(m["action"]).split(",") + ["-"])[:3] if "," in str(m["action"]) else (str(m["action"]), "-", "-")
        teile = str(m["action"]).split(",")
        art = teile[0]
        aid = teile[-1]
        if art != "ir.actions.act_window":
            ergebnis[p] = {"modell": "-", "ansichten": "(kein Fenster: %s)" % art, "vorlage": "-",
                           "treffer": "", "aktion": aid}
            continue
        action_id = int(aid)
        a = k.kw("ir.actions.act_window", "read", [[action_id], ["res_model", "view_mode", "view_id"]],
                 context=CTX)[0]
        treffer = ""
        try:
            treffer = k.kw(a["res_model"], "search_count", [[]], context=CTX)
        except Exception:
            treffer = "?"
        ergebnis[p] = {"modell": a["res_model"], "ansichten": a["view_mode"],
                       "vorlage": (a["view_id"] or ["-", "-"])[1], "treffer": treffer,
                       "aktion": action_id}
    return ergebnis


def art_set(view_mode):
    """Ansichtsarten vergleichbar machen: tree == list, 'activity' ignorieren."""
    arten = set()
    for a in (view_mode or "").split(","):
        a = a.strip()
        if not a or a == "activity":
            continue
        arten.add("list" if a == "tree" else a)
    return arten


print("Lese Odoo 11 (nur lesend) ...")
o11baum = menuebaum(o11())
# Vergleich ueber den Menuenamen (letztes Pfadstueck): die Menuebaeume sind unterschiedlich
# benannt (Odoo 11 fuehrt z. B. "Einkauf/Dokumente"), die Menuepunkte selbst sind gleich.
def nach_name(baum):
    kurz = {}
    for pfad, e in baum.items():
        name = pfad.split("/")[-1]
        kurz.setdefault(name, []).append(e)
    return kurz


o11kurz = nach_name(o11baum)
print("\n%-52s %-22s %-26s %-26s %s" % ("Menuepunkt (Odoo-11-Pfad)", "Modell", "Odoo 11",
                                       "Odoo 18", "gleich"))
for inst in ("lokal", "vm"):
    print("\n================ Odoo 18 %s ================" % inst)
    o18kurz = nach_name(menuebaum(o18(inst)))
    namen = sorted(set(o11kurz) | set(o18kurz))
    for name in namen:
        e11 = o11kurz.get(name)
        e18 = o18kurz.get(name)
        if not e11 or not e18:
            fehlt = "nur Odoo 11" if e11 else "nur Odoo 18"
            quelle = (e11 or e18)[0]
            print("%-52s %-22s %-26s %-26s %s" % (name[:52], quelle["modell"],
                                                  quelle["ansichten"] if e11 else "-",
                                                  quelle["ansichten"] if e18 else "-", fehlt))
            continue
        gleich = art_set(e11[0]["ansichten"]) == art_set(e18[0]["ansichten"])
        print("%-52s %-22s %-26s %-26s %s"
              % (name[:52], e18[0]["modell"], e11[0]["ansichten"], e18[0]["ansichten"],
                 "ja" if gleich else "NEIN"))
        if not gleich:
            print("      O11 zusaetzlich: %s | O18 zusaetzlich: %s"
                  % (sorted(art_set(e11[0]["ansichten"]) - art_set(e18[0]["ansichten"])),
                     sorted(art_set(e18[0]["ansichten"]) - art_set(e11[0]["ansichten"]))))
