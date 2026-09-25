"""Browser-Abnahme Verkauf Teil 3, Schritt 1: Formular und Reiter (Odoo 18).

Oeffnet im echten Browser (Playwright + Chrome, headless) einen Verkaufsauftrag, liest die
sichtbaren Reiter und Gruppen und klickt einen Reiter an. Read-only (kein Speichern).

Aufruf:
    uv run --with playwright python scripts/browser_verkauf_formular_reiter.py --instanz vm
    uv run --with playwright python scripts/browser_verkauf_formular_reiter.py --instanz lokal
"""
from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from browser_verkauf_menue import lade_env, rpc_client, REPO

VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session121")
REITER = ["Auftragszeilen", "Optionale Produkte", "Angebotsbauer", "Weitere Informationen"]
GRUPPEN = ["Verkauf", "Rechnungsstellung", "Versand", "Nachverfolgung"]


def erwartete_reiter(k, auftrag: dict) -> list:
    """Sichtbare Reiter aus den Sichtbarkeitsregeln des Arch und den Werten des Auftrags.

    Odoo 18: page order_lines (immer), page optional_products (invisible wenn state nicht
    draft/sent), page pdf_quote_builder (invisible ohne partner_id und
    is_pdf_quote_builder_available), page other_information (immer).
    """
    daten = k("sale.order", "read", [[auftrag["id"]],
                                     ["state", "partner_id", "is_pdf_quote_builder_available"]],
              context={"lang": "de_DE"})[0]
    sichtbar = ["Auftragszeilen"]
    if daten["state"] in ("draft", "sent"):
        sichtbar.append("Optionale Produkte")
    if daten["partner_id"] and daten["is_pdf_quote_builder_available"]:
        sichtbar.append("Angebotsbauer")
    sichtbar.append("Weitere Informationen")
    return sichtbar, daten


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["vm", "lokal"], default="vm")
    p.add_argument("--ohne-screenshot", action="store_true")
    a = p.parse_args()

    env = lade_env(os.path.join(REPO, ".env"))
    url = "https://k001959vsx.ipax.at" if a.instanz == "vm" else "http://localhost:8069"
    domain = "k001959vsx.ipax.at" if a.instanz == "vm" else "localhost"
    sid, kw = rpc_client(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])

    auftraege = kw("sale.order", "search_read", [[["order_line", "!=", False], ["state", "in", ["draft", "sent"]]],
                                                ["id", "name", "state"]], limit=1, order="id desc",
                   context={"lang": "de_DE"})
    bestaetigt = kw("sale.order", "search_read", [[["order_line", "!=", False], ["state", "=", "sale"]],
                                                 ["id", "name", "state"]], limit=1, order="id desc",
                    context={"lang": "de_DE"})
    if not auftraege or not bestaetigt:
        raise SystemExit("Es fehlen Testauftraege (Angebot/Entwurf und bestaetigter Auftrag).")
    faelle = [("Angebot/Entwurf", auftraege[0]), ("bestaetigter Auftrag", bestaetigt[0])]
    print("Instanz: %s (%s)" % (a.instanz, url))
    for bez, f in faelle:
        print("   %-22s %s (id %s, %s)" % (bez, f["name"], f["id"], f["state"]))

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

    def saeubere(t):
        return re.sub(r"\s+", " ", t or "").strip()

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_verkauf_reiter_%s" % a.instanz),
            channel="chrome", headless=True, viewport={"width": 1800, "height": 1400})
        ctx.add_init_script(
            "window.__errs=[];"
            "window.addEventListener('error', e => window.__errs.push(''+e.message));"
            "window.addEventListener('unhandledrejection', e => window.__errs.push(''+e.reason));"
            "const ce=console.error; console.error=(...x)=>{window.__errs.push(x.map(String).join(' ')); ce(...x);};")
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        seite = ctx.pages[0] if ctx.pages else ctx.new_page()
        seite.on("response", lambda r: rpc_fehler.append("%s %s" % (r.status, r.url))
                 if ("/web/dataset/call_kw" in r.url and r.status >= 400) else None)

        for bez, f in faelle:
            erwartet, daten = erwartete_reiter(kw, f)
            print("\n--- %s: %s (state %s, Angebotsbauer %s) ---"
                  % (bez, f["name"], daten["state"], daten["is_pdf_quote_builder_available"]))
            print("       erwartete Reiter (aus Sichtbarkeitsregeln): %s" % erwartet)
            seite.goto("%s/odoo/action-429/%s" % (url, f["id"]))
            seite.wait_for_selector(".o_form_view", timeout=90000)
            seite.wait_for_timeout(4000)
            pruefe(seite.query_selector(".o_form_view") is not None, "Auftragsformular geoeffnet (%s)" % f["name"])
            sichtbare = [saeubere(t) for t in seite.eval_on_selector_all(
                ".o_notebook .nav-link, .o_notebook .nav-item a", "els => els.map(e => e.innerText)")]
            print("       sichtbare Reiter im Browser: %s" % sichtbare)
            pruefe(sichtbare == erwartet, "Reiter im Browser entsprechen der Erwartung (%d)" % len(sichtbare))
            for r in erwartet:
                pruefe(r in sichtbare, "Reiter '%s' sichtbar" % r)
            if not a.ohne_screenshot:
                datei = os.path.join(VZ, "03_Reiter_%s_%s.png" % (re.sub(r"[^A-Za-z]", "", bez)[:14], a.instanz))
                seite.screenshot(path=datei, full_page=True)
                print("       Screenshot: %s" % datei)
            if "Optionale Produkte" in sichtbare:
                knopf2 = None
                for i, t in enumerate(sichtbare):
                    if t == "Optionale Produkte":
                        knopf2 = seite.query_selector_all(".o_notebook .nav-link, .o_notebook .nav-item a")[i]
                if knopf2:
                    knopf2.click()
                    seite.wait_for_timeout(2000)
                    aktiv = saeubere(seite.eval_on_selector(".o_notebook .nav-link.active", "e => e ? e.innerText : ''"))
                    pruefe(aktiv == "Optionale Produkte", "Klick auf 'Optionale Produkte' aktiviert den Reiter")

        # Gruppen des Reiters "Weitere Informationen" im Browser lesen (letzter Fall)
        knopf = None
        for i, t in enumerate(sichtbare):
            if t == "Weitere Informationen":
                knopf = seite.query_selector_all(".o_notebook .nav-link, .o_notebook .nav-item a")[i]
        if knopf is None:
            pruefe(False, "Reiter 'Weitere Informationen' nicht anklickbar")
        else:
            knopf.click()
            seite.wait_for_timeout(2500)
            gruppen = [saeubere(t) for t in seite.eval_on_selector_all(
                ".tab-pane.active .o_group_name, .tab-pane.active .o_horizontal_separator",
                "els => els.map(e => e.innerText)")]
            print("\n       sichtbare Gruppen/Ueberschriften: %s" % gruppen)
            for g in GRUPPEN:
                pruefe(any(g.lower() in x.lower() for x in gruppen), "Gruppe '%s' sichtbar" % g)
            if not a.ohne_screenshot:
                datei = os.path.join(VZ, "04_Reiter_Weitere_Informationen_%s.png" % a.instanz)
                seite.screenshot(path=datei, full_page=True)
                print("       Screenshot: %s" % datei)

        js_fehler.extend(seite.evaluate("window.__errs") or [])
        pruefe(not js_fehler, "keine JavaScript-Fehler (%d)" % len(js_fehler))
        pruefe(not rpc_fehler, "keine RPC-Fehler (HTTP >= 400) (%d)" % len(rpc_fehler))
        if js_fehler:
            print("       JS: %s" % js_fehler[:3])
        if rpc_fehler:
            print("       RPC: %s" % rpc_fehler[:3])
        ctx.close()

    print("\n%d OK / %d FEHL" % (ok, fehler))
    print("Odoo wurde nur lesend verwendet (Browser-Aufrufe ohne Speichern).")
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
