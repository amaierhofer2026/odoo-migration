"""Browser-Abnahme Produktformular auf der Odoo-18-VM (Session 120, Teil 15).

Echte Klicks im Browser (Playwright + Chrome, headless): Produktliste "Abonnement Produkte",
Klick auf ein Abo-Produkt, Formular, Feld "Verantwortlich" sichtbar und beschreibbar
(inkl. Speichern), Gruppe "Notizen", Reiter, Filter - JS- und RPC-Fehler werden mitgezaehlt.

Alle Leseaufrufe laufen mit dem Sprachkontext lang=de_DE (Befund F53): Suchen mit 'ilike' auf
uebersetzten Feldern (z. B. ir.ui.menu.name) liefern ohne Sprachkontext keinen Treffer, der
Menueaufruf "Abonnement Produkte" schlug dadurch zunaechst fehl.

Aufruf:
    uv run --with playwright python scripts/browser_produktformular.py --instanz vm
    uv run --with playwright python scripts/browser_produktformular.py --instanz lokal --ohne-screenshot
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
VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session120")

# Sprachkontext (Befund F53): Suchen mit 'ilike' auf uebersetzten Feldern (z. B. ir.ui.menu.name,
# jsonb) liefern ohne context lang keinen Treffer. Alle Leseaufrufe hier laufen daher mit de_DE,
# damit auch uebersetzte Menue- und Feldnamen gefunden werden.
SP = {"lang": "de_DE"}


def lade_env(pfad):
    werte = {}
    for zeile in open(pfad, encoding="utf-8"):
        if "=" in zeile and not zeile.strip().startswith("#"):
            k, v = zeile.split("=", 1)
            werte[k.strip()] = v.strip().strip('"')
    return werte


def rpc_client(url, db, user, pwd):
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def rufe(pfad, prm):
        req = urllib.request.Request(url + pfad, data=json.dumps({"jsonrpc": "2.0", "method": "call",
                                                                  "params": prm}).encode(),
                                     headers={"Content-Type": "application/json"})
        with op.open(req, timeout=180) as f:
            return json.loads(f.read().decode())

    rufe("/web/session/authenticate", {"db": db, "login": user, "password": pwd})
    sid = next((c.value for c in jar if c.name == "session_id"), None)

    def kw(model, methode, args, **kwargs):
        o = rufe("/web/dataset/call_kw", {"model": model, "method": methode, "args": args, "kwargs": kwargs})
        if "error" in o:
            raise RuntimeError(str(o["error"].get("data", {}).get("message"))[:200])
        return o.get("result")

    return sid, kw


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["vm", "lokal"], default="vm")
    p.add_argument("--ohne-screenshot", action="store_true")
    p.add_argument("--produkt", type=int, default=0, help="product.template-ID (leer = erstes Abo-Produkt)")
    a = p.parse_args()
    env = lade_env(os.path.join(REPO, ".env"))
    url = "https://k001959vsx.ipax.at" if a.instanz == "vm" else "http://localhost:8069"
    domain = "k001959vsx.ipax.at" if a.instanz == "vm" else "localhost"
    sid, kw = rpc_client(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])

    def kwl(modell, methode, args, **kwargs):
        """Leseaufruf mit deutschem Sprachkontext (F53) - fuer uebersetzte Namen."""
        kwargs.setdefault("context", dict(SP))
        return kw(modell, methode, args, **kwargs)

    # Hinweis (Session 120, F53): eine Suche mit 'ilike' auf einem uebersetzten Feld (hier
    # ir.ui.menu.name, jsonb) liefert ohne Sprachkontext keinen Treffer. Deshalb context lang.
    menue = kwl("ir.ui.menu", "search_read", [[("name", "ilike", "Abonnement Produkte")], ["id", "action"]],
                limit=1)
    if not menue or not menue[0]["action"]:
        raise SystemExit("Menue 'Abonnement Produkte' nicht gefunden.")
    aktion = int(str(menue[0]["action"]).split(",")[1])

    if a.produkt:
        produkt = kwl("product.template", "read", [[a.produkt], ["id", "name", "recurring_invoice"]])[0]
    else:
        kandidaten = kwl("product.template", "search_read", [[("recurring_invoice", "=", True)], ["id", "name"]], limit=5)
        if not kandidaten:
            raise SystemExit("Kein Abo-Produkt vorhanden.")
        produkt = kandidaten[0]
    benutzer = kwl("res.users", "search_read", [[("active", "=", True), ("login", "!=", "admin")], ["id", "name"]], limit=1)
    benutzer = benutzer[0] if benutzer else kwl("res.users", "search_read",
                                                [[("active", "=", True)], ["id", "name"]], limit=1)[0]

    print("Instanz   : %s (%s)" % (a.instanz, url))
    print("Aktion    : %s | Produkt: %s %s | Benutzer: %s" % (aktion, produkt["id"], produkt["name"], benutzer["name"]))

    from playwright.sync_api import sync_playwright
    os.makedirs(VZ, exist_ok=True)
    ok = fehler = 0
    js_fehler, rpc_fehler = [], []

    def pruefe(bedingung, text):
        nonlocal ok, fehler
        if bedingung:
            ok += 1
            print("  OK   %s" % text)
        else:
            fehler += 1
            print("  FEHL %s" % text)

    def saeubere(text):
        return re.sub(r"\s+", " ", text or "").strip()

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_prodform_%s_%s" % (a.instanz, os.getpid())),
            channel="chrome", headless=True, viewport={"width": 1800, "height": 1300})
        ctx.add_init_script(
            "window.__errs=[];"
            "window.addEventListener('error', e => window.__errs.push(''+e.message));"
            "window.addEventListener('unhandledrejection', e => window.__errs.push(''+e.reason));"
            "const ce=console.error; console.error=(...x)=>{window.__errs.push(x.map(String).join(' ')); ce(...x);};")
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        seite = ctx.pages[0] if ctx.pages else ctx.new_page()
        seite.on("response", lambda r: rpc_fehler.append("%s %s" % (r.status, r.url))
                 if ("/web/dataset/call_kw" in r.url and r.status >= 400) else None)

        def schuss(name):
            if not a.ohne_screenshot:
                datei = os.path.join(VZ, name)
                seite.screenshot(path=datei, full_page=True)
                print("       Screenshot: %s" % datei)

        print("\n--- 1. Produktliste 'Abonnement Produkte' (echter Aufruf der Aktion) ---")
        seite.goto("%s/odoo/action-%s" % (url, aktion))
        seite.wait_for_selector(".o_list_view, .o_kanban_view", timeout=90000)
        seite.wait_for_timeout(3500)
        pruefe(seite.query_selector(".o_control_panel") is not None, "Liste geladen (Control Panel vorhanden)")
        # Die Aktion oeffnet standardmaessig die Kanban-Ansicht (view_mode kanban,list,form).
        ansicht = "Kanban" if seite.query_selector(".o_kanban_view") else "Liste"
        zeilen = seite.query_selector_all(".o_kanban_record")
        if not zeilen:
            zeilen = seite.query_selector_all(".o_data_row")
        pruefe(len(zeilen) > 0, "Produkteintraege sichtbar in der %s-Ansicht (%d)" % (ansicht, len(zeilen)))
        schuss("01_Liste_Abonnement_Produkte.png")

        print("\n--- 2. Klick auf ein Abo-Produkt (Formular) ---")
        ziel = None
        for z in zeilen:
            if saeubere(produkt["name"])[:14] in saeubere(z.inner_text()):
                ziel = z
                break
        ziel = ziel or (zeilen[0] if zeilen else None)
        if ziel is None:
            pruefe(False, "kein Produkteintrag zum Anklicken")
        else:
            ziel.click()
            seite.wait_for_selector(".o_form_view", timeout=90000)
            seite.wait_for_timeout(3500)
            pruefe(True, "Klick auf den Eintrag oeffnet das Formular")
            schuss("02_Formular_geoeffnet.png")

        reiter = seite.eval_on_selector_all(".o_notebook .nav-link, .o_notebook .nav-item a",
                                            "els => els.map(e => e.innerText.trim())")
        print("       Reiter im Formular: %s" % reiter)
        pruefe("Allgemeine Informationen" in reiter, "Reiter 'Allgemeine Informationen' vorhanden")
        pruefe("Buchhaltung" not in reiter, "kein Reiter 'Buchhaltung' (wie in Odoo 11, dort ausgeblendet)")

        print("\n--- 3. Gruppe 'Notizen' ---")
        text_form = ""
        if seite.query_selector(".o_form_sheet"):
            text_form = saeubere(seite.inner_text(".o_form_sheet"))
        else:
            pruefe(False, "Formularinhalt (.o_form_sheet) nicht gefunden")
        # Hinweis: Odoo 18 stellt Abschnittsueberschriften per CSS in Grossbuchstaben dar
        # (Klasse o_horizontal_separator / text-uppercase), im DOM steht dann "NOTIZEN".
        # Der Vergleich muss daher ohne Beachtung der Schreibweise erfolgen.
        pruefe(re.search(r"\bNotizen\b", text_form, re.I) is not None,
               "Beschriftung 'Notizen' sichtbar (Anzeige als Abschnittstitel, ggf. gross)")
        pruefe(re.search(r"Interne Notizen", text_form, re.I) is None,
               "alte Beschriftung 'Interne Notizen' nicht mehr sichtbar")

        print("\n--- 4. Feld 'Verantwortlich' sichtbar und beschreibbar ---")
        pruefe("Verantwortlich" in text_form, "Feldbeschriftung 'Verantwortlich' sichtbar")
        feld = seite.query_selector(".o_field_widget[name='responsible_id']")
        pruefe(feld is not None, "Feld im Formular vorhanden (Widget responsible_id)")
        if feld is not None:
            eingabe = feld.query_selector("input")
            pruefe(eingabe is not None, "Feld ist ein Eingabefeld (beschreibbar)")
            eingabe.click()
            seite.wait_for_timeout(1200)
            eingabe.fill(benutzer["name"])
            seite.wait_for_timeout(2500)
            vorschlag = seite.query_selector(".o-autocomplete--dropdown-item, .ui-autocomplete .dropdown-item, .dropdown-menu .dropdown-item")
            if vorschlag is not None:
                vorschlag.click()
                seite.wait_for_timeout(1200)
                pruefe(True, "Auswahlliste erscheint und Eintrag '%s' angeklickt" % benutzer["name"])
            else:
                pruefe(False, "keine Auswahlliste zum Feld erschienen")
            schuss("03_Feld_Verantwortlich_ausgefuellt.png")

            print("\n--- 5. Speichern ---")
            speichern = seite.query_selector(".o_form_button_save")
            pruefe(speichern is not None, "Speichern-Schaltflaeche vorhanden")
            if speichern is not None:
                speichern.click()
                seite.wait_for_timeout(3500)
            schuss("04_gespeichert.png")

        print("\n--- 6. Wert per RPC gelesen (Beweis: Schreibzugriff wirkt) ---")
        wert = kwl("product.template", "read", [[produkt["id"]], ["responsible_id"]])[0]["responsible_id"]
        print("       responsible_id nach dem Speichern: %s" % (wert,))
        pruefe(bool(wert), "Feld wurde gespeichert (%s)" % (wert,))

        print("\n--- 7. Formular weiter funktionsfaehig (Reiter anklicken) ---")
        for reiter_name in ("Verkauf", "Einkauf"):
            try:
                seite.click(".o_notebook .nav-link:has-text('%s')" % reiter_name)
                seite.wait_for_timeout(1500)
                pruefe(True, "Reiter '%s' laesst sich oeffnen" % reiter_name)
            except Exception as e:  # noqa: BLE001
                pruefe(False, "Reiter '%s' nicht oeffenbar: %s" % (reiter_name, str(e)[:80]))
        schuss("05_Reiter_wechsel.png")

        print("\n--- 8. Regression Abonnement Produkte: Filter anklicken ---")
        seite.click(".o_notebook .nav-link:has-text('Allgemeine Informationen')")
        seite.wait_for_timeout(1000)
        seite.go_back()
        seite.wait_for_selector(".o_list_view, .o_kanban_view", timeout=60000)
        seite.wait_for_timeout(2500)
        seite.click(".o_searchview_input")
        seite.wait_for_timeout(1500)
        treffer = seite.query_selector(".o_search_bar_menu li[role=option]:has-text('Mit Faktor multipliziert'), .o_search_bar_menu .dropdown-item:has-text('Mit Faktor multipliziert')")
        pruefe(treffer is not None, "Filter 'Mit Faktor multipliziert' im Suchmenue angeboten")
        if treffer is not None:
            treffer.click()
            seite.wait_for_timeout(2500)
            facetten = seite.eval_on_selector_all(".o_searchview_facet", "els => els.map(e => e.innerText.trim())")
            pruefe(any("Faktor" in f for f in facetten), "Filter wirkt (Bedingung in der Suchleiste: %s)" % facetten)
        schuss("06_Liste_Filter.png")

        print("\n--- 9. Aufraeumen: Feld wieder leeren (Formular direkt aufrufen) ---")
        geraeumt = False
        try:
            seite.goto("%s/odoo/action-%s/%s" % (url, aktion, produkt["id"]))
            seite.wait_for_selector(".o_form_view", timeout=60000)
            seite.wait_for_timeout(3000)
            feld = seite.query_selector(".o_field_widget[name='responsible_id'] input")
            if feld is not None:
                feld.click(timeout=15000)
                seite.wait_for_timeout(800)
                feld.press("Control+a")
                feld.press("Delete")
                seite.keyboard.press("Escape")
                seite.wait_for_timeout(1200)
                speichern = seite.query_selector(".o_form_button_save")
                if speichern is not None:
                    speichern.click()
                    seite.wait_for_timeout(3000)
                    geraeumt = True
        except Exception as e:  # noqa: BLE001
            print("       Aufraeumen im Browser nicht moeglich: %s" % str(e)[:100])
        if not geraeumt:
            # Rueckfall: den Testwert ueber die Schnittstelle entfernen, damit kein
            # Testdatum auf dem Produkt stehen bleibt. Die Schreibbarkeit selbst ist
            # bereits in Schritt 4-6 ueber echte Klicks belegt.
            kwl("product.template", "write", [[produkt["id"]], {"responsible_id": False}])
            print("       Testwert ueber RPC entfernt (Browser-Klick war nicht moeglich)")
        leer = kwl("product.template", "read", [[produkt["id"]], ["responsible_id"]])[0]["responsible_id"]
        pruefe(not leer, "Feld nach dem Aufraeumen wieder leer (%s)" % (leer,))

        print("\n--- 10. Fehlerbilanz im Browser ---")
        js = seite.evaluate("window.__errs")
        pruefe(not js, "keine JavaScript-Fehler (%d)" % len(js))
        if js:
            print("       JS: %s" % js[:3])
        pruefe(not rpc_fehler, "keine RPC-Fehler (%d)" % len(rpc_fehler))
        if rpc_fehler:
            print("       RPC: %s" % rpc_fehler[:3])
        ctx.close()

    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    print("Screenshots: %s" % VZ)
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
