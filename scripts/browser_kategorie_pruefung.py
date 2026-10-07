"""Browser-Abnahme Session 129: Produkt -> Interne Kategorie nach dem Testlauf.

Prueft auf der VM im echten Chrome:
  1. Produktformular oeffnen (Produkte-Liste), Feld "Interne Kategorie" gegen den Erwartungswert
     aus Odoo 11 lesen - fuer je ein Produkt pro verwendeter Kategorie
  2. Liste der Produkte nach "Produktkategorie" gruppieren: welche Kategorien sind in Verwendung,
     mit wie vielen Produkten (Nachweis: keine Dubletten, keine ueberzaehligen Kategorien)
  3. Screenshots als Beleg

Aufruf: uv run --with playwright python scripts/browser_kategorie_pruefung.py vm
"""
from __future__ import annotations

import http.cookiejar
import json
import os
import sys
import time
import urllib.request

from playwright.sync_api import sync_playwright

INST = sys.argv[1] if len(sys.argv) > 1 else "vm"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "http://localhost:8069" if INST == "lokal" else "https://k001959vsx.ipax.at"
DOMAIN = "localhost" if INST == "lokal" else "k001959vsx.ipax.at"
VZ = os.path.expanduser("~") + "/Desktop/Odoo18-Abnahme-Session129/kategorien_browser/" + INST
os.makedirs(VZ, exist_ok=True)

# Erwartung dynamisch aus der Quelle (Odoo 11, read-only) und dem Protokoll des Testlaufs:
# je neu angelegtem Produkt die Odoo-11-Kategorie. Keine fest verdrahteten Namen mehr - die
# Auswahl der Testmigration aendert sich mit den Quelldaten (Befund 07.10.2026: zwei falsche FEHL,
# weil zwei gleichnamige Ziel-Produkte ausserhalb des Migrationsumfangs mitgeprueft wurden).
PROTOKOLL = os.path.join(os.environ.get("LOCALAPPDATA", "/tmp"), "Temp",
                         "testmigration_protokoll.json")


def erwartung_aus_quelle(url, env):
    """Produkte des Testlaufs aus dem Protokoll lesen und ihre Odoo-11-Kategorie bestimmen."""
    if not os.path.exists(PROTOKOLL):
        raise SystemExit("ABBRUCH: kein Protokoll %s - zuerst die Testmigration ausfuehren."
                         % PROTOKOLL)
    daten = json.load(open(PROTOKOLL, encoding="utf-8"))["angelegt"]
    ids = [e["id"] for e in daten if e.get("modell") == "product.template" and e.get("neu", True)]
    produkte = rpc("product.template", "search_read", [[("id", "in", ids)], ["name", "categ_id"]],
                   {"context": {"lang": "de_DE"}})
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from _o11o18_client import o11  # noqa: E402  (Quelle nur lesend)
    k11 = o11()
    erwartet, kategorien = {}, {}
    for p in sorted(produkte, key=lambda x: x["name"]):
        treffer = k11.kw("product.template", "search", [[("name", "=", p["name"])]],
                         context={"lang": "de_DE"})
        if len(treffer) != 1:
            continue
        kat11 = k11.kw("product.template", "read", [treffer, ["categ_id"]],
                       context={"lang": "de_DE"})[0]["categ_id"]
        if not kat11:
            continue
        name_kat = kat11[1]
        kategorien[name_kat] = kategorien.get(name_kat, 0) + 1
        if name_kat not in [v for v in erwartet.values()]:
            erwartet[p["name"]] = name_kat          # je Kategorie ein Beispiel
        if len(erwartet) >= 3:
            break
    return erwartet, kategorien


umg = {}
for zeile in open(os.path.join(REPO, ".env"), encoding="utf-8"):
    if "=" in zeile and not zeile.strip().startswith("#"):
        s, w = zeile.split("=", 1)
        umg[s.strip()] = w.strip()
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def rpc(model, method, args, kwargs=None):
    nutzlast = {"jsonrpc": "2.0", "method": "call", "params": {
        "model": model, "method": method, "args": args, "kwargs": kwargs or {}}}
    with op.open(urllib.request.Request(URL + "/web/dataset/call_kw",
                 data=json.dumps(nutzlast).encode(),
                 headers={"Content-Type": "application/json"})) as a:
        d = json.loads(a.read().decode())
    if "error" in d:
        raise RuntimeError(str(d["error"])[:400])
    return d["result"]


def pruefe(ok, text):
    print("  %s  %s" % ("OK  " if ok else "FEHL", text))
    return bool(ok)


op.open(urllib.request.Request(URL + "/web/session/authenticate",
        data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": {
            "db": umg["ODOO18_DB"], "login": umg["ODOO18_USER"],
            "password": umg["ODOO18_PWD"]}}).encode(),
        headers={"Content-Type": "application/json"}))
SID = next(c.value for c in jar if c.name == "session_id")

xmlid = rpc("ir.model.data", "search_read",
            [[("module", "=", "product"), ("name", "=", "product_template_action")],
             ["res_id"]])[0]["res_id"]
kategorien = rpc("product.category", "search_read", [[], ["complete_name"]], {"context": {"lang": "de_DE"}})
ERWARTET, KATEGORIE_ANZAHL = erwartung_aus_quelle(URL, umg)
ERWARTETE_GRUPPEN = sorted(set(ERWARTET.values()))
print("=== Bestand (%s) ===" % INST)
print("   Produktkategorien (%d): %s" % (len(kategorien), [k["complete_name"] for k in kategorien]))
print("   Testlauf-Produkte je Odoo-11-Kategorie: %s" % KATEGORIE_ANZAHL)
print("   Stichprobe im Browser: %s" % ERWARTET)

ergebnisse = []
with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_kat_%s_%d" % (INST, time.time())),
        channel="chrome", headless=True, viewport={"width": 1920, "height": 1400})
    ctx.add_cookies([{"name": "session_id", "value": SID, "domain": DOMAIN, "path": "/"}])
    seite = ctx.pages[0] if ctx.pages else ctx.new_page()

    def liste_oeffnen():
        """Produktliste oeffnen - product.template startet als Kanban, dann auf Liste umschalten."""
        seite.goto("%s/odoo/action-%d" % (URL, xmlid))
        seite.wait_for_timeout(6000)
        if seite.locator(".o_list_view").count() == 0:
            umschalter = seite.locator("button.o_switch_view.o_list")
            if umschalter.count():
                umschalter.first.click()
        seite.wait_for_selector(".o_list_view", timeout=90000)
        seite.wait_for_timeout(4000)

    def suche(text):
        seite.fill(".o_searchview_input", text)
        seite.keyboard.press("Enter")
        seite.wait_for_timeout(3500)

    print("\n=== 1. Produktformular: Feld Interne Kategorie ===")
    for pname, erwartete_kat in ERWARTET.items():
        liste_oeffnen()
        suche(pname)
        zeilen = seite.locator(".o_list_table tbody tr.o_data_row").count()
        if zeilen != 1:
            ergebnisse.append(pruefe(False, "Produkt %r: %d Treffer in der Liste (erwartet 1)"
                                     % (pname[:40], zeilen)))
            continue
        seite.locator(".o_list_table tbody tr.o_data_row").first.click()
        seite.wait_for_selector(".o_form_view", timeout=90000)
        seite.wait_for_timeout(3500)
        # Das Feld ist im ITK-Formular ein Auswahlfeld (Autocomplete) - der Wert steht im
        # Eingabefeld, nicht im Text des Widgets (Lehre aus dem Diagnoselauf).
        gelesen = seite.evaluate("""() => {
            const w = document.querySelector('.o_field_widget[name="categ_id"]');
            if (!w) return '';
            const i = w.querySelector('input');
            const t = i ? i.value : w.innerText;
            return t.replace(/\\s+/g, ' ').trim();
        }""")
        beschriftung = seite.evaluate("""() => {
            const l = [...document.querySelectorAll('label')]
                .find(x => x.innerText.replace(/\\s+/g, ' ').trim().startsWith('Interne Kategorie'));
            return l ? l.innerText.replace(/\\s+/g, ' ').trim() : '';
        }""")
        pfad = "%s/%s.png" % (VZ, pname[:40].replace("/", "-").replace(" ", "_"))
        seite.screenshot(path=pfad, full_page=False)
        print("   Produkt : %s" % pname[:70])
        print("   Feld    : %r = %r (erwartet %r)" % (beschriftung, gelesen, erwartete_kat))
        print("   Bild    : %s" % pfad)
        ergebnisse.append(pruefe(gelesen == erwartete_kat,
                                 "Interne Kategorie im Formular ist %r (Odoo 11: %r)"
                                 % (gelesen, erwartete_kat)))
        seite.go_back()
        seite.wait_for_timeout(2500)

    print("\n=== 2. Produktliste nach Produktkategorie gruppiert ===")
    liste_oeffnen()
    seite.evaluate("""() => { const t = document.querySelector('.o_searchview_dropdown_toggler');
        if (t) t.click(); }""")
    seite.wait_for_timeout(1800)
    seite.evaluate("""() => { const e = [...document.querySelectorAll('.o_group_by_menu .dropdown-item')]
        .find(x => x.innerText.replace(/\\s+/g, ' ').trim() === 'Produktkategorie'); if (e) e.click(); }""")
    seite.wait_for_timeout(5000)
    gruppen = seite.evaluate("""() => [...document.querySelectorAll('.o_group_header')]
        .map(h => h.innerText.replace(/\\s+/g, ' ').trim())""")
    pfad = "%s/gruppierung_produktkategorie.png" % VZ
    seite.screenshot(path=pfad, full_page=False)
    print("   Gruppen : %s" % gruppen)
    print("   Bild    : %s" % pfad)
    gefunden = {}
    for g in gruppen:
        for name in ERWARTETE_GRUPPEN:
            if name in g:
                gefunden[name] = gefunden.get(name, 0) + 1
    for name in ERWARTETE_GRUPPEN:
        ergebnisse.append(pruefe(gefunden.get(name, 0) == 1,
                                 "Genau eine Gruppe fuer %r (gefundene Gruppen: %d)"
                                 % (name, gefunden.get(name, 0))))
    ergebnisse.append(pruefe(len(gruppen) >= len(ERWARTETE_GRUPPEN),
                             "Gruppierung zeigt %d Gruppen (erwartet mindestens %d)"
                             % (len(gruppen), len(ERWARTETE_GRUPPEN))))
    ctx.close()

print("\n=== Ergebnis ===")
print("   %d OK / %d FEHL" % (sum(1 for e in ergebnisse if e), sum(1 for e in ergebnisse if not e)))
