"""Verifikation Produktformular (Session 120, Teil 15) - Odoo 11 gegen Odoo 18, lokale Umsetzung.

Prueft read-only bis auf einen Testdatensatz, der am Ende wieder geloescht wird:
  1. Modulversion und Feld "Verantwortlich" (responsible_id, many2one res.users)
  2. Feld ist im gerenderten Produktformular sichtbar
  3. Gruppe internal_notes heisst sichtbar "Notizen" und enthaelt weiterhin das Beschreibungsfeld
  4. Feld ist schreibbar (Testdatensatz anlegen, schreiben, lesen, loeschen)
  5. Die in Odoo 11 im Reiter "Abrechnung" sichtbaren Felder sind in Odoo 18 erreichbar
  6. Die in Odoo 11 ausgeblendeten Kontofelder sind auch in Odoo 18 nicht im Formular

Aufruf: python scripts/verify_produktformular.py --instanz lokal|vm
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import re
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP = {"lang": "de_DE"}

# Felder, die im Odoo-11-Reiter "Abrechnung" sichtbar waren (gemessen am gerenderten Arch)
SICHTBAR_O11 = ["taxes_id", "supplier_taxes_id", "service_tracking", "invoice_policy", "purchase_method"]
ERSATZ_O11 = [("service_policy", "expense_policy")]  # Odoo 11 -> Odoo 18 (Nachfolgefeld)
AUSGEBLENDET_O11 = ["property_account_income_id", "property_account_expense_id",
                    "property_account_creditor_price_difference", "property_valuation"]


def client(instanz):
    env = {}
    for z in open(os.path.join(REPO, ".env"), encoding="utf-8"):
        if "=" in z and not z.strip().startswith("#"):
            k, v = z.split("=", 1)
            env[k.strip()] = v.strip().strip('"')
    url = "http://localhost:8069" if instanz == "lokal" else "https://k001959vsx.ipax.at"
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def rpc(pfad, prm):
        r = urllib.request.Request(url + pfad,
                                   data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": prm}).encode(),
                                   headers={"Content-Type": "application/json"})
        with op.open(r, timeout=300) as f:
            return json.loads(f.read().decode())

    rpc("/web/session/authenticate", {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"],
                                      "password": env["ODOO18_PWD"]})

    def kw(m, me, args, **K):
        o = rpc("/web/dataset/call_kw", {"model": m, "method": me, "args": args, "kwargs": K})
        if "error" in o:
            raise RuntimeError(str(o["error"].get("data", {}).get("message", o["error"].get("message")))[:400])
        return o["result"]

    return kw


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    a = p.parse_args()
    kw = client(a.instanz)
    ok = fehler = 0

    def pruefe(bed, txt):
        nonlocal ok, fehler
        if bed:
            ok += 1
            print("  OK   %s" % txt)
        else:
            fehler += 1
            print("  FEHL %s" % txt)

    print("=== Verifikation Produktformular | Instanz: %s ===" % a.instanz)

    print("\n--- 1. Modulversion ---")
    m = kw("ir.module.module", "search_read", [[["name", "=", "itk_product"]], ["state", "installed_version"]])[0]
    pruefe(m["state"] == "installed", "itk_product installiert (%s)" % m["installed_version"])
    pruefe(m["installed_version"] == "18.0.1.0.2", "Version 18.0.1.0.2 aktiv (%s)" % m["installed_version"])

    print("\n--- 2. Feld Verantwortlich ---")
    d = kw("product.template", "fields_get", [["responsible_id"],
                                              ["string", "type", "relation", "required", "readonly", "store"]], context=SP)
    f = (d or {}).get("responsible_id")
    pruefe(bool(f), "Feld responsible_id vorhanden")
    if f:
        pruefe(f["type"] == "many2one" and f["relation"] == "res.users",
               "Typ many2one auf res.users (%s/%s)" % (f["type"], f["relation"]))
        pruefe(f.get("string") == "Verantwortlich", "Beschriftung 'Verantwortlich' (%s)" % f.get("string"))
        pruefe(f.get("store") is True, "Feld ist gespeichert (store=%s)" % f.get("store"))
        pruefe(f.get("readonly") is False, "Feld ist pflegbar (readonly=%s)" % f.get("readonly"))

    print("\n--- 3. Gerendertes Formular ---")
    arch = ""
    erg = kw("product.template", "get_views", [[[False, "form"]]], context=SP)
    for _k, v in (erg.get("views") or {}).items():
        arch = v["arch"]
    pruefe(bool(arch), "Formular rendert (%d Zeichen)" % len(arch))
    seiten = re.findall(r'<page[^>]*string="([^"]+)"', arch)
    print("   Reiter: %s" % seiten)
    pruefe('name="responsible_id"' in arch, "Feld responsible_id im Formular")
    m2 = re.search(r'<field name="responsible_id"[^>]*>', arch)
    pruefe(bool(m2) and "invisible" not in m2.group(0), "Feld nicht ausgeblendet (%s)" % (m2.group(0) if m2 else "-"))
    g = re.search(r'<group name="internal_notes"[^>]*>', arch)
    pruefe(bool(g) and 'string="Notizen"' in g.group(0), "Gruppe heisst 'Notizen' (%s)" % (g.group(0) if g else "-"))
    pruefe('string="Interne Notizen"' not in arch, "alte Beschriftung 'Interne Notizen' verschwunden")
    pruefe("Interne Notizen" not in arch, "kein Rest der alten Beschriftung im Arch")
    abschnitt = arch[g.end():g.end() + 600] if g else ""
    pruefe('name="description"' in abschnitt, "Beschreibungsfeld weiterhin in der Gruppe (nichts entfernt)")

    print("\n--- 4. Schreibbarkeit (Testdatensatz, wird wieder geloescht) ---")
    vorher = kw("product.template", "search_count", [[]])
    benutzer = kw("res.users", "search_read", [[["active", "=", True]], ["id", "name"]], limit=1)
    uid = benutzer[0]["id"] if benutzer else False
    pid = None
    try:
        pid = kw("product.template", "create", [{"name": "TESTSATZ Session 120 Produktformular"}])
        pruefe(bool(pid), "Testdatensatz angelegt (id=%s)" % pid)
        kw("product.template", "write", [[pid], {"responsible_id": uid}])
        gelesen = kw("product.template", "read", [[pid], ["responsible_id"]])[0]["responsible_id"]
        pruefe(gelesen and gelesen[0] == uid, "responsible_id schreibbar und lesbar (%s)" % (gelesen,))
    except Exception as e:  # noqa: BLE001
        pruefe(False, "Schreibtest fehlgeschlagen: %s" % str(e)[:200])
    finally:
        if pid:
            kw("product.template", "unlink", [[pid]])
        nachher = kw("product.template", "search_count", [[]])
        pruefe(nachher == vorher, "Testdatensatz geloescht (%d vorher, %d nachher)" % (vorher, nachher))

    print("\n--- 5. Odoo-11-Reiter 'Abrechnung': sichtbare Felder in Odoo 18 erreichbar ---")
    for feld in SICHTBAR_O11:
        pruefe(('name="%s"' % feld) in arch, "%s im Odoo-18-Formular" % feld)
    for alt, neu in ERSATZ_O11:
        pruefe(('name="%s"' % neu) in arch, "%s (Odoo 11) -> %s (Odoo 18) im Formular" % (alt, neu))

    print("\n--- 6. Kontofelder (in Odoo 11 bereits ausgeblendet) ---")
    for feld in AUSGEBLENDET_O11:
        pruefe(('name="%s"' % feld) not in arch, "%s nicht im Formular (wie in Odoo 11)" % feld)
    seite_buchhaltung = re.search(r'<page string="Buchhaltung"[^>]*>', arch)
    print("   Reiter 'Buchhaltung' im gerenderten Arch: %s" % (seite_buchhaltung.group(0) if seite_buchhaltung else "nein (nur fuer Konten-Gruppe, s. Doku)"))

    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
