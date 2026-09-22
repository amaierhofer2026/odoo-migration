"""Pre-Upgrade-Rendertest fuer Ansichten (Arbeitsregel Session 118, Punkt 3).

Legt die Ansichten einer Moduldatei als Testdatensatz an (ir.ui.view.create), laesst den
Zielarch von Odoo rendern (product.template.get_views) und loescht den Testdatensatz wieder.
Damit sind XPath-Anker und group_by-Format vor dem Modul-Upgrade belegt.

Aufruf: python scripts/pruefe_view_render.py --instanz lokal --datei addons/itk_multifactor/views/itk_product.xml --erwartete-filter filter_multi_factor,filter_abo_aktiv --erwartete-gruppen categ_id,type,product_type_id,is_multi_factor_product
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import re
import sys
import urllib.request

from lxml import etree

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    p.add_argument("--datei", required=True)
    p.add_argument("--erwartete-filter", default="")
    p.add_argument("--erwartete-gruppen", default="")
    a = p.parse_args()

    env = {}
    for z in open(os.path.join(REPO, ".env"), encoding="utf-8"):
        if "=" in z and not z.strip().startswith("#"):
            k, v = z.split("=", 1)
            env[k.strip()] = v.strip()
    url = "http://localhost:8069" if a.instanz == "lokal" else "https://k001959vsx.ipax.at"
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def rpc(pfad, prm):
        r = urllib.request.Request(url + pfad,
                                   data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": prm}).encode(),
                                   headers={"Content-Type": "application/json"})
        with op.open(r, timeout=300) as f:
            return json.loads(f.read().decode())

    rpc("/web/session/authenticate", {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"], "password": env["ODOO18_PWD"]})

    def kw(m, me, args, **K):
        o = rpc("/web/dataset/call_kw", {"model": m, "method": me, "args": args, "kwargs": K})
        if "error" in o:
            raise RuntimeError(str(o["error"].get("data", {}).get("message"))[:400])
        return o["result"]

    baum = etree.parse(os.path.join(REPO, a.datei))
    ok = fehler = 0

    def pruefe(bed, txt):
        nonlocal ok, fehler
        if bed:
            ok += 1
            print("  OK   %s" % txt)
        else:
            fehler += 1
            print("  FEHL %s" % txt)

    print("Datei: %s | Instanz: %s" % (a.datei, a.instanz))
    for rec in baum.getroot().iter("record"):
        if rec.get("model") != "ir.ui.view":
            continue
        rid = rec.get("id")
        werte = {f.get("name"): f for f in rec.findall("field")}
        if "inherit_id" not in werte or "arch" not in werte:
            continue
        ref = werte["inherit_id"].get("ref")
        modul, name = ref.split(".", 1)
        modell = (werte["model"].text or "").strip()
        arch_xml = (werte["arch"].text or "") + "".join(
            etree.tostring(kind, encoding="unicode") for kind in werte["arch"])
        typ = "search" if "search" in ref else ("form" if "form" in ref else "list")
        print("\n--- %s (%s, inherit %s) ---" % (rid, typ, ref))

        dom = [("module", "=", modul), ("name", "=", name)]
        eltern = kw("ir.model.data", "search_read", [dom, ["res_id", "model"]], limit=1)
        pruefe(bool(eltern), "Eltern-View %s gefunden" % ref)
        if not eltern:
            continue

        vid = None
        try:
            vid = kw("ir.ui.view", "create", [{"name": "TESTDATENSATZ %s" % rid, "model": modell,
                                               "inherit_id": eltern[0]["res_id"], "arch": arch_xml}])
            pruefe(bool(vid), "Testdatensatz angelegt (id=%s) - XPath-Anker gueltig" % vid)
        except Exception as e:  # noqa: BLE001
            pruefe(False, "Anlegen fehlgeschlagen: %s" % str(e)[:250])
            continue

        try:
            erg = kw(modell, "get_views", [[[False, typ]]], context={"lang": "de_DE"})
            gearch = ""
            for _k, v in erg["views"].items():
                gearch = v["arch"]
            pruefe(bool(gearch), "Ansicht rendert fehlerfrei (%s, %s Zeichen)" % (typ, len(gearch)))
            if typ == "search" and a.erwartete_filter:
                namen = re.findall(r'<filter[^>]*name="([^"]+)"', gearch)
                for f in a.erwartete_filter.split(","):
                    pruefe(f.strip() in namen, "Filter %s im gerenderten Arch" % f.strip())
            if typ == "search" and a.erwartete_gruppen:
                gruppen = re.findall(r"group_by'\s*:\s*'(\w+)'", gearch)
                for g in a.erwartete_gruppen.split(","):
                    pruefe(g.strip() in gruppen, "Gruppierung %s im gerenderten Arch" % g.strip())
            datei = os.path.join(os.environ.get("TEMP", "."), "render_%s_%s.xml" % (typ, a.instanz))
            with open(datei, "w", encoding="utf-8") as fh:
                fh.write(gearch)
            print("   gerenderter Arch gespeichert: %s" % datei)
        except Exception as e:  # noqa: BLE001
            pruefe(False, "Rendern fehlgeschlagen: %s" % str(e)[:250])
        finally:
            kw("ir.ui.view", "unlink", [[vid]])
            pruefe(kw("ir.ui.view", "search_count", [[("id", "=", vid)]]) == 0,
                   "Testdatensatz wieder geloescht (id=%s)" % vid)

    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
