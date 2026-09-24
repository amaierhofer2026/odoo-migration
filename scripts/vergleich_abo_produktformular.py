"""Vergleich Produktformular (product.template, form) Odoo 11 Prod gegen Odoo 18.

Read-only: es werden ausschliesslich Leseaufrufe abgesetzt (get_views / fields_view_get,
fields_get, search_read).  Es werden keine Datensaetze angelegt, geaendert oder geloescht.

Aufruf:
    python scripts/vergleich_abo_produktformular.py --instanz o11|vm|lokal [--ausgabe DATEI]

Ausgabe: normalisierte Textliste des gerenderten Formulars (Reiter, Felder je Reiter,
Button, Pflichtfelder, Feldtypen, mitwirkende Ansichten), damit zwei Instanzen zeilenweise
verglichen werden koennen.
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def lade_env(pfad):
    w = {}
    for z in open(pfad, encoding="utf-8"):
        if "=" in z and not z.strip().startswith("#"):
            k, v = z.split("=", 1)
            w[k.strip()] = v.strip().strip('"')
    return w


def client(instanz):
    env = lade_env(os.path.join(REPO, ".env"))
    if instanz == "o11":
        url, db = "https://portal.it-kommunal.at", "ITK_V1_a"
        user, pwd = "anna.maierhofer@it-kommunal.at", env["ODOO11_PWD"]
    elif instanz == "vm":
        url, db = "https://k001959vsx.ipax.at", env["ODOO18_DB"]
        user, pwd = env["ODOO18_USER"], env["ODOO18_PWD"]
    else:
        url, db = "http://localhost:8069", env["ODOO18_DB"]
        user, pwd = env["ODOO18_USER"], env["ODOO18_PWD"]
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def rufe(pfad, params):
        r = urllib.request.Request(url + pfad,
                                   data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": params}).encode(),
                                   headers={"Content-Type": "application/json"})
        with op.open(r, timeout=600) as f:
            return json.loads(f.read().decode())

    anmeldung = rufe("/web/session/authenticate", {"db": db, "login": user, "password": pwd})
    if anmeldung.get("error"):
        raise SystemExit("Anmeldung fehlgeschlagen (%s): %s" % (instanz, str(anmeldung["error"])[:200]))

    def kw(model, methode, args, **kwargs):
        o = rufe("/web/dataset/call_kw", {"model": model, "method": methode, "args": args, "kwargs": kwargs})
        if "error" in o:
            return {"__fehler__": str(o["error"].get("data", {}).get("message", o["error"].get("message")))[:200]}
        return o.get("result")

    return kw


def hol_arch(kw, modell, art, sprache):
    """Gerenderte Ansicht lesen - Odoo 11 nutzt fields_view_get, Odoo 18 get_views."""
    for methode, args in (("fields_view_get", [False, art]),
                          ("get_views", [[[False, art]]]),
                          ("get_view", [False, art])):
        e = kw(modell, methode, args, context=sprache)
        if isinstance(e, dict) and e.get("arch"):
            return e["arch"], e.get("views") or {}
        if isinstance(e, dict) and "views" in e:
            for _n, v in e["views"].items():
                if v.get("arch"):
                    return v["arch"], e["views"]
    return "", {}


def attr(elt, name):
    return (elt.get(name) or "").strip()


def sichtbar(elt):
    """Rohe Sichtbarkeitsangabe eines Feldes - Odoo 11 (attrs) und Odoo 18 (invisible/readonly)."""
    teile = []
    for n in ("invisible", "readonly", "required", "attrs", "column_invisible", "force_save"):
        v = elt.get(n)
        if v:
            teile.append("%s=%s" % (n, v))
    return " ".join(teile)


def sammle(elt, pfad, felder, seiten, buttons, label_fuer):
    """Rekursiv durch den Arch: Seiten, Felder, Buttons in Dokumentreihenfolge."""
    for kind in list(elt):
        tag = kind.tag
        name = attr(kind, "name")
        if tag == "page":
            seiten.append({"name": name, "string": attr(kind, "string") or name,
                           "attrs": attr(kind, "attrs"), "invisible": attr(kind, "invisible"),
                           "felder": []})
            sammle(kind, pfad + [attr(kind, "string") or name], felder, seiten, buttons, label_fuer)
        elif tag == "field":
            eintrag = {
                "name": name,
                "string": attr(kind, "string"),
                "widget": attr(kind, "widget"),
                "class": attr(kind, "class"),
                "sichtbarkeit": sichtbar(kind),
                "pfad": list(pfad),
                "ebene": len(pfad),
            }
            felder.append(eintrag)
            if seiten:
                seiten[-1]["felder"].append(eintrag)
        elif tag == "label":
            if attr(kind, "for"):
                label_fuer.setdefault(attr(kind, "for"), []).append(attr(kind, "string"))
            sammle(kind, pfad, felder, seiten, buttons, label_fuer)
        elif tag == "button":
            buttons.append({
                "name": name,
                "string": attr(kind, "string"),
                "type": attr(kind, "type"),
                "class": attr(kind, "class"),
                "sichtbarkeit": sichtbar(kind),
                "pfad": list(pfad),
                "smart": "oe_stat_button" in attr(kind, "class"),
            })
            sammle(kind, pfad, felder, seiten, buttons, label_fuer)
        else:
            sammle(kind, pfad, felder, seiten, buttons, label_fuer)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["o11", "vm", "lokal"], default="o11")
    p.add_argument("--modell", default="product.template")
    p.add_argument("--ausgabe", default="")
    p.add_argument("--sprache", default="de_DE")
    a = p.parse_args()
    kw = client(a.instanz)
    sprache = {"lang": a.sprache}
    z = []

    def s(text=""):
        z.append(text)
        print(text)

    s("=== Produktformular: Instanz=%s Modell=%s Sprache=%s ===" % (a.instanz, a.modell, a.sprache))

    arch, views = hol_arch(kw, a.modell, "form", sprache)
    if not arch:
        s("FEHLER: keine Formularansicht erhalten")
        return 1
    s("Arch-Laenge: %s Zeichen" % len(arch))

    s("\n--- Mitwirkende Formularansichten (ir.ui.view, type=form) ---")
    for v in kw("ir.ui.view", "search_read",
                [[["model", "=", a.modell], ["type", "=", "form"]],
                 ["id", "name", "priority", "inherit_id", "active", "mode"]], context=sprache,
                order="priority,id") or []:
        s("   %-6s %-58s prio=%-4s inherit=%-28s aktiv=%s%s" % (
            v["id"], (v["name"] or "")[:58], v["priority"],
            (str(v["inherit_id"][0]) if v["inherit_id"] else "-"), v["active"],
            " Mode=%s" % v["mode"] if v.get("mode") else ""))

    root = ET.fromstring(arch)
    felder, seiten, buttons, label_fuer = [], [], [], {}
    sammle(root, [], felder, seiten, buttons, label_fuer)

    s("\n--- Reiter (notebook/page) in Reihenfolge ---")
    if not seiten:
        s("   (kein notebook im Formular)")
    for i, pg in enumerate(seiten, 1):
        s("   %2d. %-34s name=%-26s felder=%-3s %s" % (
            i, pg["string"], pg["name"] or "-", len(pg["felder"]),
            (" ".join(x for x in ("attrs=%s" % pg["attrs"] if pg["attrs"] else "",
                                  "invisible=%s" % pg["invisible"] if pg["invisible"] else "") if x))))

    s("\n--- Felder AUSSERHALB der Reiter ---")
    drin = {id(f) for pg in seiten for f in pg["felder"]}
    for f in felder:
        if id(f) not in drin:
            s("   %-34s String=%-30s %s %s" % (f["name"], f["string"] or "-",
                                               ("widget=%s" % f["widget"]) if f["widget"] else "",
                                               f["sichtbarkeit"]))

    for i, pg in enumerate(seiten, 1):
        s("\n--- Reiter %d: %s ---" % (i, pg["string"]))
        for f in pg["felder"]:
            s("   %-36s String=%-32s %s %s" % (f["name"], f["string"] or "(Label)", f["widget"] and "widget=%s" % f["widget"] or "",
                                               f["sichtbarkeit"]))

    s("\n--- Buttons ---")
    for b in buttons:
        s("   %-28s String=%-30s type=%-10s %s%s pfad=%s" % (
            b["name"] or "-", b["string"] or "-", b["type"], "SMART " if b["smart"] else "",
            b["sichtbarkeit"], "/".join(b["pfad"]) or "-"))
    if not buttons:
        s("   (keine)")

    s("\n--- Felddefinitionen (fields_get) fuer alle Formularfelder ---")
    namen = sorted({f["name"] for f in felder})
    deps = kw(a.modell, "fields_get", [namen, ["string", "type", "relation", "required", "readonly",
                                               "store", "compute", "related", "help", "selection"]],
              context=sprache)
    if isinstance(deps, dict) and "__fehler__" not in deps:
        for n in namen:
            d = deps.get(n)
            if not d:
                s("   %-36s NICHT VORHANDEN" % n)
                continue
            ausw = ""
            if d.get("selection"):
                ausw = " auswahl=%s" % str([w[0] for w in d["selection"]])[:80]
            s("   %-36s %-32s %-14s rel=%-20s req=%-5s ro=%-5s store=%-5s %s%s" % (
                n, (d.get("string") or "")[:32], d.get("type"), str(d.get("relation")), d.get("required"),
                d.get("readonly"), d.get("store"),
                ("compute=%s" % str(d.get("compute"))[:24]) if d.get("compute") else "",
                ausw))
    else:
        s("   %s" % deps)

    if a.ausgabe:
        with open(a.ausgabe, "w", encoding="utf-8") as f:
            f.write("\n".join(z) + "\n")
        print("\n[gespeichert: %s]" % a.ausgabe)
    return 0


if __name__ == "__main__":
    sys.exit(main())
