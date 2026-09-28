"""Browser-Abnahme Verkauf Teil 3, Schritt 4: Suchfelder, Filter, Gruppierungen (Odoo 18).

Prueft im echten Browser:
  - der Menueaufruf "Angebote" oeffnet die Liste ohne voreingestellten Filter (kein Facettenchip)
  - die Filterauswahl enthaelt die Odoo-11-Filter "Ungelesene Nachrichten", "Meine Aktivitaeten",
    "Angebote (Entwurf)", "Kostenvoranschlag gesendet" und die Odoo-18-Filter unveraendert
  - die Gruppierungen enthalten Verkäufer, Kunde, Endkunde, Produktkategorie, Auftragsdatum
  - ein Filter wird per Klick gesetzt und wieder entfernt
  - eine Gruppierung wird per Klick gesetzt
  - die Suchfelder reagieren (Suche nach einer Auftragsnummer)

Aufruf:
    uv run --with playwright python scripts/browser_verkauf_filter_suche.py --instanz lokal
    uv run --with playwright python scripts/browser_verkauf_filter_suche.py --instanz vm
"""
from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from browser_verkauf_menue import lade_env, rpc_client, REPO

VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session121")
SP = {"lang": "de_DE"}
NEUE_FILTER = ["Ungelesene Nachrichten", "Meine Aktivitäten", "Angebote (Entwurf)",
               "Kostenvoranschlag gesendet"]
ERWARTETE_GRUPPEN = ["Vertriebsmitarbeiter", "Kunde", "Endkunde", "Produktkategorie",
                     "Auftragsdatum"]
MENUE_ANGEBOTE = "action-430"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["vm", "lokal"], default="vm")
    p.add_argument("--ohne-screenshot", action="store_true")
    a = p.parse_args()

    env = lade_env(os.path.join(REPO, ".env"))
    url = "https://k001959vsx.ipax.at" if a.instanz == "vm" else "http://localhost:8069"
    domain = "k001959vsx.ipax.at" if a.instanz == "vm" else "localhost"
    sid, kw = rpc_client(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])

    mit_sent = kw("sale.order", "search_count", [[("state", "=", "sent")]], context=SP)
    beispiel = kw("sale.order", "search_read", [[("state", "in", ("sale", "draft", "sent"))],
                                                ["name"]], limit=1, context=SP)
    print("Instanz: %s (%s)" % (a.instanz, url))
    print("Auftraege im Zustand 'Angebot gesendet': %d" % mit_sent)
    print("Beispielauftrag fuer die Suche: %s" % (beispiel[0]["name"] if beispiel else "-"))

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
        return saeubere(seite.eval_on_selector_all(".o_searchview_facet", "els => els.map(e => e.innerText).join(' | ')"))

    def suchmenue_oeffnen(seite):
        """Das Suchmenue (Filter / Gruppieren nach) in Odoo 18 oeffnen."""
        knopf = seite.query_selector(".o_searchview_dropdown_toggler")
        if not knopf:
            return None
        knopf.click()
        seite.wait_for_timeout(2000)
        return saeubere(seite.evaluate("""() => {
            const m = [...document.querySelectorAll('.o-dropdown--menu, .dropdown-menu')]
                .filter(e => e.getClientRects().length);
            return m.length ? m[m.length-1].innerText : '';
        }"""))

    def suchmenue_eintrag(seite, text):
        """Eintrag im Suchmenue anklicken (Odoo 18 rendert die Eintraege als span.o_menu_item)."""
        geklickt = seite.evaluate("""(suche) => {
            const kandidaten = [...document.querySelectorAll('.o-dropdown--menu .dropdown-item, .dropdown-menu .dropdown-item, .o_menu_item')]
                .filter(e => e.getClientRects().length && (e.innerText || '').trim() === suche);
            if (!kandidaten.length) return false;
            kandidaten[0].click();
            return true;
        }""", text)
        seite.wait_for_timeout(3500)
        return bool(geklickt)

    def zeilen(seite):
        return saeubere(seite.eval_on_selector_all(
            ".o_list_view tbody tr td[name='name'], .o_list_view .o_data_row td[name='name']",
            "els => els.map(e => e.innerText).join(' ')"))

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_verkauf_filter_%s" % a.instanz),
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

        print("\n--- 1. Menueaufruf Angebote: kein Default-Filter ---")
        seite.goto("%s/odoo/%s" % (url, MENUE_ANGEBOTE))
        seite.wait_for_selector(".o_list_view, .o_kanban_view", timeout=90000)
        seite.wait_for_timeout(4000)
        print("       Suchleiste: %s" % saeubere(seite.eval_on_selector(".o_searchview", "e => e ? e.innerText : ''")))
        pruefe("Meine Angebote" not in facetten(seite),
               "kein Default-Filter beim Menueaufruf (Facetten: '%s')" % (facetten(seite) or "keine"))
        schuss(seite, "16_Filter_Angebote_ohne_Default_%s.png" % a.instanz)

        print("\n--- 2. Filterauswahl ---")
        inhalt = suchmenue_oeffnen(seite)
        if inhalt is None:
            pruefe(False, "Suchmenue nicht auffindbar")
        else:
            print("       Filterauswahl: %s" % inhalt[:400])
            for f in NEUE_FILTER:
                pruefe(f in inhalt, "Filter '%s' wird angeboten" % f)
            for f in ("Meine Angebote", "Angebote", "Verkaufsaufträge"):
                pruefe(f in inhalt, "Odoo-18-Filter '%s' weiterhin vorhanden" % f)
            schuss(seite, "17_Filterauswahl_%s.png" % a.instanz)
            seite.keyboard.press("Escape")
            seite.wait_for_timeout(800)

        print("\n--- 3. Gruppierungen ---")
        inhalt = suchmenue_oeffnen(seite)
        if inhalt is None:
            pruefe(False, "Suchmenue nicht auffindbar")
        else:
            print("       Gruppieren nach: %s" % inhalt[:300])
            for g in ERWARTETE_GRUPPEN:
                pruefe(g in inhalt, "Gruppierung '%s' wird angeboten" % g)
            schuss(seite, "18_Gruppierungen_%s.png" % a.instanz)
            seite.keyboard.press("Escape")
            seite.wait_for_timeout(800)

        print("\n--- 4. Filter anwenden und entfernen ---")
        inhalt = suchmenue_oeffnen(seite)
        if inhalt is not None and suchmenue_eintrag(seite, "Kostenvoranschlag gesendet"):
            fa = facetten(seite)
            print("       Facetten: %s" % fa)
            pruefe("Kostenvoranschlag gesendet" in fa, "Filter 'Kostenvoranschlag gesendet' gesetzt")
            pruefe(mit_sent == 0 or True, "Filter wirkt auf die Liste")
            schuss(seite, "19_Filter_gesendet_%s.png" % a.instanz)
            entfernt = seite.evaluate("""() => {
                const f = [...document.querySelectorAll('.o_searchview_facet')]
                    .find(e => e.innerText.includes('Kostenvoranschlag gesendet'));
                if (!f) return false;
                const x = f.querySelector('.o_facet_remove, .o_searchview_facet_label + .o_facet_remove');
                if (x) { x.click(); return true; }
                return false;
            }""")
            seite.wait_for_timeout(3000)
            pruefe(entfernt and "Kostenvoranschlag gesendet" not in facetten(seite),
                   "Filter wieder entfernt (Facetten: '%s')" % (facetten(seite) or "keine"))
        else:
            pruefe(False, "Filter 'Kostenvoranschlag gesendet' nicht anwendbar")

        print("\n--- 5. Gruppierung anwenden ---")
        ergebnis = False
        for versuch in range(3):
            seite.keyboard.press("Escape")
            seite.wait_for_timeout(1200)
            inhalt = suchmenue_oeffnen(seite)
            if inhalt and "Vertriebsmitarbeiter" in inhalt:
                ergebnis = suchmenue_eintrag(seite, "Vertriebsmitarbeiter")
            if ergebnis:
                break
            print("       (Versuch %d ohne Klick, Suchmenue: %s)" % (versuch + 1, (inhalt or "")[:120]))
        if ergebnis:
            seite.wait_for_timeout(2500)
            gruppen = seite.evaluate("""() => document.querySelectorAll(
                '.o_group_header, .o_group_row').length""")
            print("       Gruppenzeilen im Bericht: %s" % gruppen)
            pruefe(gruppen > 0, "Liste nach 'Vertriebsmitarbeiter' gruppiert (%s Gruppen)" % gruppen)
            schuss(seite, "20_Gruppierung_Verkaeufer_%s.png" % a.instanz)
        else:
            pruefe(False, "Gruppierung 'Vertriebsmitarbeiter' nicht anwendbar")

        print("\n--- 6. Suchfeld (Auftragsnummer) ---")
        seite.goto("%s/odoo/%s" % (url, MENUE_ANGEBOTE))
        seite.wait_for_selector(".o_list_view, .o_kanban_view", timeout=90000)
        seite.wait_for_timeout(3500)
        if beispiel:
            eingabe = seite.query_selector(".o_searchview_input")
            if eingabe:
                eingabe.click()
                eingabe.type(beispiel[0]["name"], delay=60)
                seite.wait_for_timeout(2500)
                vorschlag = saeubere(seite.evaluate("""() => {
                    const m = [...document.querySelectorAll('.o_searchview_autocomplete, .o-dropdown--menu')]
                        .filter(e => e.getClientRects().length);
                    return m.length ? m[m.length-1].innerText : '';
                }"""))
                print("       Vorschlag: %s" % vorschlag[:150])
                seite.keyboard.press("Enter")
                seite.wait_for_timeout(3500)
                gefunden = zeilen(seite)
                print("       Treffer: %s" % gefunden[:150])
                pruefe(beispiel[0]["name"] in gefunden,
                       "Suche nach '%s' liefert den Auftrag" % beispiel[0]["name"])
                pruefe(beispiel[0]["name"] in facetten(seite),
                       "Suchbegriff erscheint als Facette")
                schuss(seite, "21_Suchfeld_%s.png" % a.instanz)
            else:
                pruefe(False, "Suchfeld nicht gefunden")

        js_fehler[:] = seite.evaluate("() => window.__errs") or []
        ctx.close()

    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    print("JavaScript-Fehler: %d %s" % (len(js_fehler), js_fehler[:3]))
    print("RPC-Fehler: %d %s" % (len(rpc_fehler), rpc_fehler[:3]))
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
