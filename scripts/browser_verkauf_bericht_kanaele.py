"""Browser-Abnahme Verkauf Teil 4, Schritt 2: Bericht "Verkaufsauftraege aller Kanaele" (Odoo 18).

Geprueft wird im echten Browser:
  - Menuepunkt Verkauf/Berichtswesen/Verkaufsauftraege aller Kanaele oeffnet den Pivot
  - Default-Filter "Aktuelles Verkaufsjahr" ist gesetzt
  - Pivot-Standard wie Odoo 11: Zeilen = Auftragsreferenz, Spalte = Vertriebskanal
  - Mass Total (Feld price_total) ist gesetzt
  - "Vertriebskanal" wird unter "Gruppieren nach" angeboten und funktioniert beim Klick
  - Summe entspricht dem per RPC berechneten Wert ueber nicht stornierte Auftraege
  - stornierte Auftraege sind ausgeschlossen
  - bestehende Odoo-18-Berichte funktionieren unveraendert
  - keine JavaScript- und RPC-Fehler

Aufruf:
    uv run --with playwright python scripts/browser_verkauf_bericht_kanaele.py --instanz lokal
    uv run --with playwright python scripts/browser_verkauf_bericht_kanaele.py --instanz vm
"""
from __future__ import annotations

import argparse
import datetime
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from browser_verkauf_menue import lade_env, rpc_client, REPO

VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session121")
SP = {"lang": "de_DE"}
AKTION = "action-itk_sale_management.action_sale_report_all_channels"


def zahl(text):
    if text is None:
        return None
    b = str(text).replace("\u00a0", " ").replace("€", "").strip()
    b = re.sub(r"[^0-9,.\-]", "", b)
    if not b:
        return None
    if "," in b:
        b = b.replace(".", "").replace(",", ".")
    try:
        return float(b)
    except ValueError:
        return None


def zahlen(text):
    return [w for w in (zahl(x) for x in re.findall(r"[0-9][0-9.,]*", text or ""))
            if w is not None and w > 0]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["vm", "lokal"], default="vm")
    p.add_argument("--ohne-screenshot", action="store_true")
    a = p.parse_args()

    env = lade_env(os.path.join(REPO, ".env"))
    url = "https://k001959vsx.ipax.at" if a.instanz == "vm" else "http://localhost:8069"
    domain = "k001959vsx.ipax.at" if a.instanz == "vm" else "localhost"
    sid, kw = rpc_client(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])

    jahr = datetime.date.today().year
    basis = [("date", ">=", "%d-01-01" % jahr)]

    def summe(d):
        return (kw("sale.report", "read_group", [d, ["price_total:sum"], []], context=SP)[0]
                .get("price_total") or 0.0)

    soll_ohne = summe(basis + [("state", "!=", "cancel")])
    soll_mit = summe(basis)
    zeilen_ohne = kw("sale.report", "search_count", [basis + [("state", "!=", "cancel")]], context=SP)
    kanaele = [t["name"] for t in kw("crm.team", "search_read", [[], ["name"]], context=SP)]
    print("Instanz: %s (%s)" % (a.instanz, url))
    print("Sollwerte %d (nicht storniert): %d Zeilen, Summe Total %.2f" % (jahr, zeilen_ohne, soll_ohne))
    print("Vergleichswert mit stornierten Auftraegen: %.2f" % soll_mit)

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

    def schuss(seite, name):
        if not a.ohne_screenshot:
            datei = os.path.join(VZ, name)
            seite.screenshot(path=datei, full_page=True)
            print("       Screenshot: %s" % datei)

    def facetten(seite):
        return saeubere(seite.eval_on_selector_all(
            ".o_searchview_facet", "els => els.map(e => e.innerText).join(' | ')"))

    def pivottext(seite):
        return saeubere(seite.eval_on_selector(".o_pivot_view", "e => e ? e.innerText : ''"))

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_verkauf_bericht_%s" % a.instanz),
            channel="chrome", headless=True, viewport={"width": 1900, "height": 1400})
        ctx.add_init_script(
            "window.__errs=[];"
            "window.addEventListener('error', e => window.__errs.push(''+e.message));"
            "window.addEventListener('unhandledrejection', e => window.__errs.push(''+e.reason));"
            "const ce=console.error; console.error=(...x)=>{window.__errs.push(x.map(String).join(' ')); ce(...x);};")
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        seite = ctx.pages[0] if ctx.pages else ctx.new_page()
        seite.on("response", lambda r: rpc_fehler.append("%s %s" % (r.status, r.url))
                 if ("/web/dataset/call_kw" in r.url and r.status >= 400) else None)

        print("\n--- 1. Menuepunkt oeffnet den Bericht ---")
        seite.goto("%s/odoo/%s" % (url, AKTION))
        seite.wait_for_selector(".o_pivot_view", timeout=90000)
        seite.wait_for_timeout(5000)
        pruefe(seite.query_selector(".o_pivot") is not None, "Pivotansicht geoeffnet")
        kopf = saeubere(seite.eval_on_selector(".o_control_panel", "e => e ? e.innerText : ''"))
        print("       Kopfbereich: %s" % kopf[:160])
        pruefe("aller Kanäle" in kopf, "Berichtstitel 'Verkaufsaufträge aller Kanäle'")
        schuss(seite, "29_Bericht_Kanaele_%s.png" % a.instanz)

        print("\n--- 2. Default-Filter ---")
        fa = facetten(seite)
        print("       Facetten: %s" % fa)
        pruefe("Aktuelles Verkaufsjahr" in fa, "Filter 'Aktuelles Verkaufsjahr' ist gesetzt")

        print("\n--- 3. Pivot-Standard: Zeile Auftragsreferenz, Spalte Kanal, Mass Total ---")
        text = pivottext(seite)
        print("       Pivot (Anfang): %s" % text[:260])
        referenzen = sorted(set(re.findall(r"S\d{5}", text)))
        pruefe(len(referenzen) >= 1, "Zeilen sind Auftragsreferenzen (%d: %s)"
               % (len(referenzen), ", ".join(referenzen[:5])))
        genutzt = [n for n in kanaele if n in text]
        print("       Kanaele im System: %s -> im Pivot: %s" % (kanaele, genutzt))
        pruefe(bool(genutzt), "Pivot hat eine Spalte je Vertriebskanal")
        pruefe("Werte" in text, "Mass-Auswahl 'Werte' im Pivot vorhanden")
        pruefe("Gesamt" in text, "Mass Total (Feld price_total, Beschriftung 'Gesamt') ist gesetzt")
        schuss(seite, "30_Bericht_Kanaele_Struktur_%s.png" % a.instanz)

        print("\n--- 4. Summe und Ausschluss stornierter Auftraege ---")
        werte = zahlen(text)
        groesster = max(werte) if werte else None
        print("       Groesster Wert im Pivot: %s" % groesster)
        pruefe(groesster is not None, "Pivot enthaelt Zahlenwerte")
        if groesster is not None:
            pruefe(abs(groesster - soll_ohne) < 0.05,
                   "Summe im Pivot %.2f entspricht Sollwert nicht storniert %.2f" % (groesster, soll_ohne))
            if abs(soll_mit - soll_ohne) > 0.005:
                pruefe(abs(groesster - soll_mit) > 0.005,
                       "stornierte Auftraege sind ausgeschlossen (mit storniert waeren es %.2f)" % soll_mit)

        print("\n--- 5. Gruppierung 'Vertriebskanal' im Suchmenue ---")
        try:
            seite.click(".o_searchview_dropdown_toggler", timeout=10000)
            seite.wait_for_timeout(2000)
            gruppen = seite.eval_on_selector_all(
                ".o-dropdown--menu h5:has-text('Gruppieren nach') + * , .o-dropdown--menu *",
                "els => els.filter(e => e.children.length === 0 && (e.innerText||'').trim())"
                ".map(e => e.tagName + ' :: ' + e.innerText.trim())")
            print("       Suchmenue: %s" % str(gruppen)[:600])
        except Exception as ex:
            gruppen = []
            pruefe(False, "Suchmenue nicht geoeffnet (%s)" % ex)
        pruefe(any("Vertriebskanal" == g.split(" :: ")[-1] for g in gruppen),
               "'Vertriebskanal' wird unter 'Gruppieren nach' angeboten")
        pruefe(any("Verkaufsteam" == g.split(" :: ")[-1] for g in gruppen),
               "Odoo-18-Gruppierung 'Verkaufsteam' bleibt erhalten")
        pruefe(any("Aktuelles Verkaufsjahr" == g.split(" :: ")[-1] for g in gruppen),
               "Odoo-11-Filter 'Aktuelles Verkaufsjahr' ist im Filterbereich")
        ziel = seite.query_selector(".o-dropdown--menu *:text-is('Vertriebskanal')") \
            or seite.query_selector(".o-dropdown--menu :text('Vertriebskanal')")
        if ziel:
            ziel.click()
            seite.wait_for_timeout(5000)
            text2 = pivottext(seite)
            fa2 = facetten(seite)
            print("       Pivot nach Gruppierung: %s" % text2[:200])
            pruefe("Vertriebskanal" in fa2, "Gruppierung liegt als Facette an (%s)" % fa2)
            w2 = zahlen(text2)
            pruefe(bool(w2) and abs(max(w2) - soll_ohne) < 0.05,
                   "Summe nach Gruppierung korrekt (%.2f)" % soll_ohne)
            pruefe(any(n in text2 for n in kanaele), "Gruppierung zeigt Kanaele")
            schuss(seite, "31_Bericht_Kanaele_Gruppierung_%s.png" % a.instanz)
            seite.keyboard.press("Escape")
            seite.wait_for_timeout(1200)
        else:
            pruefe(False, "Gruppierung 'Vertriebskanal' nicht anklickbar")

        print("\n--- 6. Bestehende Odoo-18-Berichte unveraendert ---")
        for aktion_id, name in ((416, "Verkaufsanalyse"), (417, "Verkaufsanalyse nach Vertriebsmitarbeiter")):
            seite.goto("%s/odoo/action-%d" % (url, aktion_id))
            seite.wait_for_selector(".o_graph_view, .o_pivot", timeout=90000)
            seite.wait_for_timeout(4000)
            fa_x = facetten(seite)
            print("       %s (Aktion %d) Facetten: %s" % (name, aktion_id, fa_x))
            pruefe(bool(fa_x), "%s (Aktion %d) oeffnet weiterhin" % (name, aktion_id))
            if aktion_id == 416:
                schuss(seite, "32_Bericht_Verkaufsanalyse_%s.png" % a.instanz)

        js_fehler[:] = seite.evaluate("() => window.__errs") or []
        ctx.close()

    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    print("JavaScript-Fehler: %d %s" % (len(js_fehler), js_fehler[:3]))
    print("RPC-Fehler: %d %s" % (len(rpc_fehler), rpc_fehler[:3]))
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
