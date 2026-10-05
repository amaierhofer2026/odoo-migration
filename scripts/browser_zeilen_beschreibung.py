"""Browser-Abnahme: Spalte "Beschreibung" in den Rechnungszeilen (Odoo 18).

Prueft im echten Browser gegen lokale Instanz oder Test-VM, fuer alle vier Belegarten:
  1. genau eine sichtbare Spalte "Beschreibung" in der Zeilentabelle,
  2. Position wie in Odoo 11 (direkt nach "Sektion", vor "Kostenstelle"),
  3. sichtbarer Beschreibungstext aus der Datenbank,
  4. Spaltenauswahl-Menue enthaelt jeden Eintrag nur einmal,
  5. keine andere Spalte fehlt oder ist doppelt,
  6. Abschnitte/Notizen und die Odoo-18-Bedienung der Zeilenliste bleiben erhalten,
  7. Eingabe in die Spalte funktioniert (Wert wird nicht gespeichert).
Es wird nichts gespeichert.

Aufruf:
    uv run --with playwright python scripts/browser_zeilen_beschreibung.py --instanz lokal
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKER = "TEST-ZEILE-"
ARTEN = [("out_invoice", "Ausgangsrechnung", "action-354"),
         ("out_refund", "Kunden-Gutschrift", "action-355"),
         ("in_invoice", "Eingangsrechnung", "action-357"),
         ("in_refund", "Lieferanten-Gutschrift", "action-358")]
# Sichtbare Spalten der Rechnungszeilen in Odoo 11 (account.invoice.form, read-only gemessen)
ERWARTETE_SPALTEN = ["Pos", "Produkt", "Sektion", "Beschreibung", "Kostenstelle", "Menge",
                     "Preis pro ME", "Rabatt (%)", "Steuern", "Zwischensumme", "Total"]


def lade_env(pfad):
    werte = {}
    for zeile in open(pfad, encoding="utf-8"):
        if "=" in zeile and not zeile.strip().startswith("#"):
            k, v = zeile.split("=", 1)
            werte[k.strip()] = v.strip().strip('"')
    return werte


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["vm", "lokal"], default="lokal")
    a = p.parse_args()

    env = lade_env(os.path.join(REPO, ".env"))
    url = "https://k001959vsx.ipax.at" if a.instanz == "vm" else "http://localhost:8069"
    domain = "k001959vsx.ipax.at" if a.instanz == "vm" else "localhost"
    VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session125",
                      "zeilen_beschreibung", a.instanz)
    os.makedirs(VZ, exist_ok=True)

    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def rufe(pfad, prm):
        req = urllib.request.Request(url + pfad, data=json.dumps(
            {"jsonrpc": "2.0", "method": "call", "params": prm}).encode(),
            headers={"Content-Type": "application/json"})
        with op.open(req, timeout=180) as f:
            return json.loads(f.read().decode())

    rufe("/web/session/authenticate", {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"],
                                       "password": env["ODOO18_PWD"]})
    sid = next(c.value for c in jar if c.name == "session_id")

    def kw(model, methode, args, **kwargs):
        o = rufe("/web/dataset/call_kw", {"model": model, "method": methode,
                                          "args": args, "kwargs": kwargs})
        if "error" in o:
            raise RuntimeError(str(o["error"])[:300])
        return o.get("result")

    CTX = {"lang": "de_DE"}
    belege = kw("account.move", "search_read",
                [[["ref", "like", MARKER]], ["id", "name", "ref", "move_type"]], context=CTX)
    nach_typ = {b["move_type"]: b for b in belege}
    print("Instanz: %s | Testbelege: %d" % (url, len(belege)))
    for name, wert in sorted(nach_typ.items()):
        print("   %-12s id %-4s ref %s" % (name, wert["id"], wert["ref"]))

    from playwright.sync_api import sync_playwright
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

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"),
                                       "pw_zeilen_%s_%s" % (a.instanz, os.getpid())),
            channel="chrome", headless=True, viewport={"width": 1900, "height": 1300})
        ctx.add_init_script(
            "window.__errs=[];"
            "window.addEventListener('error', e => window.__errs.push(''+e.message));"
            "window.addEventListener('unhandledrejection', e => window.__errs.push(''+e.reason));"
            "const ce=console.error; console.error=(...x)=>{window.__errs.push(x.map(String).join(' ')); ce(...x);};")
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        seite = ctx.pages[0] if ctx.pages else ctx.new_page()
        seite.on("response", lambda resp: rpc_fehler.append("%s %s" % (resp.status, resp.url))
                 if ("/web/dataset/call_kw" in resp.url and resp.status >= 400) else None)

        def form_oeffnen(pfad, ref):
            seite.goto("%s/odoo/%s" % (url, pfad))
            seite.wait_for_selector(".o_data_row", timeout=90000)
            seite.wait_for_timeout(3000)
            seite.locator(".o_data_row", has_text=ref).first.locator("td").nth(1).click()
            seite.wait_for_selector(".o_form_view", timeout=60000)
            seite.wait_for_timeout(4000)

        def tabelle_lesen():
            return seite.evaluate("""() => {
                const tab = document.querySelector("div[name='invoice_line_ids']");
                if (!tab) return null;
                const ths = [...tab.querySelectorAll('thead th')]
                    .map(th => ({i: th.cellIndex, t: th.innerText.replace(/\\s+/g,' ').trim()}));
                const zeilen = [...tab.querySelectorAll('tbody tr.o_data_row')].map(tr => ({
                    klasse: tr.className,
                    text: tr.innerText.replace(/\\s+/g,' ').trim(),
                    zellen: [...tr.querySelectorAll('td')].reduce((acc, td) => {
                        acc[td.cellIndex] = td.innerText.replace(/\\s+/g,' ').trim(); return acc; }, {})}));
                const steuerung = [...tab.querySelectorAll('.o_field_x2many_list_row_add, .o_field_x2many_list_row_add a, tfoot a, .o_field_x2many_list_row_add button')]
                    .map(e => e.innerText.replace(/\\s+/g,' ').trim()).filter(t => t);
                const griff = !!tab.querySelector('.o_handle_cell, .o_row_handle');
                return {ths, zeilen, steuerung, griff};}""")

        def auswahl_lesen():
            knopf = seite.locator("div[name='invoice_line_ids'] .o_optional_columns_dropdown_toggle").first
            if not knopf.count():
                return None
            knopf.click()
            seite.wait_for_timeout(2000)
            eintraege = seite.evaluate("""() => [...document.querySelectorAll('.o-dropdown--menu .dropdown-item')]
                .filter(e => e.getClientRects().length)
                .map(e => e.innerText.replace(/\\s+/g,' ').trim())""")
            seite.keyboard.press("Escape")
            seite.wait_for_timeout(1200)
            return eintraege

        for typ, bezeichnung, pfad in ARTEN:
            b = nach_typ.get(typ)
            print("\n--- %s (%s) ---" % (bezeichnung, typ))
            if not b:
                pruefe(False, "Testbeleg fuer %s vorhanden" % typ)
                continue
            form_oeffnen(pfad, b["ref"])
            d = tabelle_lesen()
            if not d:
                pruefe(False, "%s: Zeilenliste im Formular gefunden" % bezeichnung)
                continue
            kopf = [t["t"] for t in d["ths"]]
            print("    Spalten: %s" % kopf)
            anzahl = kopf.count("Beschreibung")
            pruefe(anzahl == 1, "%s: Spalte 'Beschreibung' genau einmal sichtbar (%d)" % (bezeichnung, anzahl))
            if anzahl == 1:
                i_bes = kopf.index("Beschreibung")
                i_sek = kopf.index("Sektion") if "Sektion" in kopf else -99
                pruefe(i_bes == i_sek + 1,
                       "%s: 'Beschreibung' direkt nach 'Sektion' (Position %d)" % (bezeichnung, i_bes + 1))
            for spalte in ERWARTETE_SPALTEN:
                n = kopf.count(spalte)
                pruefe(n == 1, "%s: Spalte '%s' genau einmal vorhanden (%d)" % (bezeichnung, spalte, n))
            unbekannt = [t for t in kopf if t and t not in ERWARTETE_SPALTEN]
            pruefe(not unbekannt, "%s: keine unerwartete Spalte (%s)" % (bezeichnung, unbekannt or "keine"))
            idx = kopf.index("Beschreibung") if "Beschreibung" in kopf else None
            if idx is not None:
                werte = [z["zellen"].get(str(idx), "") for z in d["zeilen"]]
                print("    Beschreibungsspalte je Zeile: %s" % werte)
                pruefe("BESCHREIBUNG %s" % typ in werte,
                       "%s: Beschreibungstext in der Zeile sichtbar" % bezeichnung)
            abschnitte = [z for z in d["zeilen"] if "ABSCHNITT %s" % typ in z["text"]]
            notizen = [z for z in d["zeilen"] if "NOTIZ %s" % typ in z["text"]]
            pruefe(bool(abschnitte), "%s: Abschnittszeile weiterhin sichtbar" % bezeichnung)
            pruefe(bool(notizen), "%s: Notizzeile weiterhin sichtbar" % bezeichnung)
            pruefe(any("line_section" in z["klasse"] for z in d["zeilen"]),
                   "%s: Abschnittszeile wird als Abschnitt gezeichnet" % bezeichnung)
            pruefe(d["griff"], "%s: Griffspalte (Zeilen verschieben) erhalten" % bezeichnung)
            steuer = " ".join(d["steuerung"])
            for eintrag in ("Zeile hinzufügen", "Abschnitt hinzufügen", "Notiz hinzufügen", "Katalog"):
                pruefe(eintrag in steuer, "%s: Odoo-18-Bedienung '%s' vorhanden" % (bezeichnung, eintrag))
            auswahl = auswahl_lesen()
            print("    Spaltenauswahl: %s" % auswahl)
            pruefe(auswahl is not None, "%s: Spaltenauswahl-Menue vorhanden" % bezeichnung)
            if auswahl:
                pruefe(auswahl.count("Beschreibung") == 1,
                       "%s: Spaltenauswahl enthaelt 'Beschreibung' genau einmal (%d)"
                       % (bezeichnung, auswahl.count("Beschreibung")))
                doppelt = sorted({e for e in auswahl if auswahl.count(e) > 1})
                pruefe(not doppelt, "%s: keine doppelten Eintraege in der Spaltenauswahl (%s)"
                       % (bezeichnung, doppelt or "keine"))
            seite.screenshot(path=os.path.join(VZ, "01_%s.png" % typ), full_page=True)

        # --- Eingabe/Bearbeitung ---
        b = nach_typ.get("out_invoice")
        if b:
            print("\n--- Eingabe in die Spalte Beschreibung (Ausgangsrechnung, Entwurf) ---")
            form_oeffnen("action-354", b["ref"])
            kopf = [t["t"] for t in tabelle_lesen()["ths"]]
            print("    Spalten: %s" % kopf)
            # stabile Anker: Produktzeile + Beschreibungszelle (eigene CSS-Klasse des Feldes)
            zelle = seite.locator(
                "div[name='invoice_line_ids'] tbody tr.o_is_product td.o_section_and_note_text_cell").first
            pruefe(zelle.count() > 0, "Beschreibungszelle der Produktzeile vorhanden")
            if zelle.count():
                alt = zelle.inner_text().strip()
                pruefe(alt == "BESCHREIBUNG out_invoice",
                       "Zelle zeigt den Wert aus der Datenbank (%r)" % alt)
                zelle.click()
                seite.wait_for_timeout(2000)
                eingabe = zelle.locator("input, textarea").first
                pruefe(eingabe.count() > 0, "Zelle wird beim Klick zum Eingabefeld")
                if eingabe.count():
                    pruefe(eingabe.input_value().strip() == "BESCHREIBUNG out_invoice",
                           "Eingabefeld enthaelt den Datenbankwert (%r)" % eingabe.input_value())
                    eingabe.fill("BESCHREIBUNG GEAENDERT (nicht gespeichert)")
                    seite.wait_for_timeout(800)
                    pruefe(eingabe.input_value().startswith("BESCHREIBUNG GEAENDERT"),
                           "Eingabe wird angenommen (%r)" % eingabe.input_value())
                    seite.screenshot(path=os.path.join(VZ, "02_eingabe.png"), full_page=True)
            # ohne Speichern verlassen
            seite.keyboard.press("Escape")
            seite.goto("%s/odoo/action-354" % url)
            seite.wait_for_timeout(3000)
            rest = kw("account.move.line", "search_read",
                      [[["move_id", "=", b["id"]], ["display_type", "=", "product"]],
                       ["id", "name"]], context=CTX)
            pruefe(rest and rest[0]["name"] == "BESCHREIBUNG out_invoice",
                   "Datenbankwert unveraendert (nichts gespeichert): %s" % rest)

        js_fehler.extend(seite.evaluate("window.__errs") or [])
        pruefe(not js_fehler, "keine JavaScript-Fehler (%d)" % len(js_fehler))
        pruefe(not rpc_fehler, "keine RPC-Fehler (%d)" % len(rpc_fehler))
        if js_fehler:
            print("       JS: %s" % js_fehler[:3])
        if rpc_fehler:
            print("       RPC: %s" % rpc_fehler[:3])
        ctx.close()

    print("\n%d OK / %d FEHL" % (ok, fehler))
    print("Screenshots: %s" % VZ)
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
