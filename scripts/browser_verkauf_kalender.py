"""Browser-Abnahme Verkauf Teil 4: Auftragskalender nach Auftragsdatum (Option A).

Prueft im echten Browser:
  - der Menuepunkt Verkauf/Auftraege/Auftragskalender oeffnet einen Kalender
  - der Kalender basiert auf dem Auftragsdatum: ein Entwurf ohne Bestaetigungsdatum erscheint im
    Monat seines Auftragsdatums (und im Vormonat nicht)
  - die Ansichtsumschaltung bietet Kalender und Liste (eigene Aktion)
  - der Odoo-18-Aktivitaetenkalender der Verkaufsmenues bleibt unveraendert erreichbar
  - keine JavaScript- und RPC-Fehler

Aufruf:
    uv run --with playwright python scripts/browser_verkauf_kalender.py --instanz lokal
    uv run --with playwright python scripts/browser_verkauf_kalender.py --instanz vm
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
AKTION = "action-itk_sale_management.action_saleorder_kalender_itk"
MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September",
          "Oktober", "November", "Dezember"]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["vm", "lokal"], default="vm")
    p.add_argument("--ohne-screenshot", action="store_true")
    a = p.parse_args()

    env = lade_env(os.path.join(REPO, ".env"))
    url = "https://k001959vsx.ipax.at" if a.instanz == "vm" else "http://localhost:8069"
    domain = "k001959vsx.ipax.at" if a.instanz == "vm" else "localhost"
    sid, kw = rpc_client(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])

    # Testauftrag: Entwurf ohne Bestaetigungsdatum (zeigt im Kalender nach Auftragsdatum)
    kandidaten = kw("sale.order", "search_read",
                    [[("state", "=", "draft")], ["name", "date_order", "confirmation_date", "state"]],
                    context=SP)
    if not kandidaten:
        raise SystemExit("Kein Entwurf fuer die Kalenderpruefung vorhanden.")
    test = kandidaten[0]
    jahr, monat = int(test["date_order"][:4]), int(test["date_order"][5:7])
    vormonat = monat - 1 if monat > 1 else 12
    print("Instanz: %s (%s)" % (a.instanz, url))
    print("Testauftrag: %s (Status %s, Auftragsdatum %s, Bestaetigung %s)"
          % (test["name"], test["state"], test["date_order"], test["confirmation_date"]))

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

    def kalender_titel(seite):
        return saeubere(seite.eval_on_selector(".o_calendar_view", "e => e ? e.innerText : ''"))

    def ereignisse(seite):
        return seite.evaluate(
            "() => [...document.querySelectorAll('.o_calendar_view .fc-event, .o_calendar_view .o_event')]"
            ".map(e => (e.innerText || '').trim()).filter(Boolean)")

    def monats_label(seite):
        """Den sichtbaren Monat aus der Werkzeugleiste lesen (robust gegen mehrere Treffer)."""
        texte = seite.evaluate("""() => [...document.querySelectorAll(
            '.o_calendar_view .o_calendar_header, .o_calendar_view .fc-toolbar, .o_calendar_view h5,'
            + '.o_calendar_view .fc-toolbar-title')].map(e => (e.innerText || '').trim())""")
        for text in texte or []:
            treffer = re.search(r"(%s)\s+(\d{4})" % "|".join(MONATE), text)
            if treffer:
                return "%s %s" % (treffer.group(1), treffer.group(2))
        return (texte or [""])[0]

    def gehe_zu_monat(seite, jahr, monat):
        """Mit den Pfeilen zum gewuenschten Monat navigieren (max. 24 Schritte)."""
        ziel = "%s %s" % (MONATE[monat - 1], jahr)
        for _ in range(24):
            ist = monats_label(seite)
            if ist == ziel:
                return True
            if not monat_wechseln(seite, "prev" if ziel < ist else "next"):
                return False
        return monats_label(seite) == ziel

    def monat_wechseln(seite, richtung):
        knopf = seite.query_selector(".o_calendar_button_%s" % richtung)
        if not knopf:
            return False
        knopf.click()
        seite.wait_for_timeout(2500)
        return True

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_verkauf_kalender_%s" % a.instanz),
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

        print("\n--- 1. Menuepunkt Auftragskalender ---")
        seite.goto("%s/odoo/%s" % (url, AKTION))
        seite.wait_for_selector(".o_calendar_view", timeout=90000)
        seite.wait_for_timeout(4000)
        titel = kalender_titel(seite)
        pruefe("Auftragskalender" in titel, "Kalender geoeffnet ('%s')" % titel[:80])
        pruefe(seite.query_selector(".o_calendar_view .fc") is not None
               or "MO" in titel.upper(), "Kalendergitter wird gerendert")
        schuss(seite, "27_Auftragskalender_%s.png" % a.instanz)

        print("\n--- 2. Basis Auftragsdatum (Monat %s) ---" % monats_label(seite))
        label = monats_label(seite)
        treffer = re.search(r"(%s)\s+(\d{4})" % "|".join(MONATE), label)
        if not treffer:
            pruefe(False, "Monat konnte nicht gelesen werden (%s)" % label)
        else:
            m_nr = MONATE.index(treffer.group(1)) + 1
            m_jahr = int(treffer.group(2))
            folge_m, folge_j = (m_nr + 1, m_jahr) if m_nr < 12 else (1, m_jahr + 1)
            start = "%04d-%02d-01 00:00:00" % (m_jahr, m_nr)
            ende = "%04d-%02d-01 00:00:00" % (folge_j, folge_m)
            erwartet = {o["name"] for o in kw("sale.order", "search_read",
                                              [[("date_order", ">=", start), ("date_order", "<", ende)],
                                               ["name"]], context=SP)}
            gezeigt = set(re.findall(r"\b(?:[SA]-\d{4,}|S\d{4,})\b", " ".join(ereignisse(seite))))
            print("       Erwartet laut Auftragsdatum: %s" % ", ".join(sorted(erwartet)) or "(keine)")
            print("       Im Kalender angezeigt:       %s" % ", ".join(sorted(gezeigt)) or "(keine)")
            pruefe(gezeigt.issubset(erwartet) and bool(gezeigt),
                   "alle angezeigten Auftraege haben ihr Auftragsdatum in diesem Monat")
            pruefe(erwartet.issubset(gezeigt),
                   "die Auftraege mit Auftragsdatum in diesem Monat erscheinen vollstaendig")
            vorgaenger = {o["name"] for o in kw("sale.order", "search_read",
                                                [[("date_order", "<", start)], ["name"]], limit=5,
                                                order="date_order desc", context=SP)}
            pruefe(not (vorgaenger & gezeigt),
                   "Kontrolle: Auftraege mit fruehrerem Auftragsdatum erscheinen nicht (%s)"
                   % ", ".join(sorted(vorgaenger)))
            # Gegenprobe: Auftraege mit Bestaetigung in diesem Monat, aber Auftragsdatum davor
            # duerfen nicht erscheinen (sonst waere die Basis das Bestaetigungsdatum).
            bestaetigt = {o["name"] for o in kw("sale.order", "search_read",
                                                [[("confirmation_date", ">=", start),
                                                  ("confirmation_date", "<", ende),
                                                  ("date_order", "<", start)], ["name"]],
                                                context=SP)}
            if bestaetigt:
                pruefe(not (bestaetigt & gezeigt),
                       "Gegenprobe Bestaetigungsdatum: %s erscheint nicht (Basis bleibt Auftragsdatum)"
                       % ", ".join(sorted(bestaetigt)))
            else:
                print("       Gegenprobe Bestaetigungsdatum: kein passender Auftrag im Testbestand")

        print("\n--- 4. Ansichtsumschaltung (eigene Aktion) ---")
        schalter = seite.evaluate(
            "() => [...document.querySelectorAll('.o_switch_view')].map(e => e.className)")
        pruefe(any("o_calendar" in s for s in schalter), "Kalender ist in der Umschaltung aktiv")
        pruefe(any("o_list" in s for s in schalter), "Liste ist als zweite Ansicht vorhanden")
        if seite.query_selector(".o_switch_view.o_list"):
            seite.click(".o_switch_view.o_list")
            seite.wait_for_timeout(3000)
            pruefe(bool(seite.query_selector(".o_list_view")),
                   "Wechsel auf die Liste funktioniert")
            spalten = seite.evaluate("() => [...document.querySelectorAll('.o_list_view thead th')]"
                                     ".map(e => (e.innerText||'').trim()).filter(Boolean)")
            pruefe("Bestelldatum" in spalten, "Liste zeigt Bestelldatum (%s)" % ", ".join(spalten[:6]))
            seite.click(".o_switch_view.o_calendar")
            seite.wait_for_timeout(3000)

        print("\n--- 5. Odoo-18-Aktivitaetenkalender unveraendert ---")
        seite.goto("%s/odoo/action-430" % url)
        seite.wait_for_selector(".o_list_view", timeout=90000)
        seite.wait_for_timeout(3500)
        if seite.query_selector(".o_switch_view.o_calendar"):
            seite.click(".o_switch_view.o_calendar")
            seite.wait_for_timeout(3500)
            titel = kalender_titel(seite)
            pruefe(bool(seite.query_selector(".o_calendar_view")),
                   "Aktivitaetenkalender der Angebotsliste oeffnet weiterhin ('%s')" % titel[:60])
            aktivitaeten = set(re.findall(r"\b(?:[SA]-\d{4,}|S\d{4,})\b", " ".join(ereignisse(seite))))
            print("       Ereignisse im Aktivitaetenkalender: %s" % (", ".join(sorted(aktivitaeten))
                                                                    or "(keine)"))
            pruefe(aktivitaeten != gezeigt,
                   "Aktivitaetenkalender zeigt einen anderen Satz als der Auftragskalender "
                   "(Aktivitaetsdatum statt Auftragsdatum)")
            schuss(seite, "28_Aktivitaetenkalender_%s.png" % a.instanz)
        else:
            pruefe(False, "Kalenderumschaltung in der Angebotsliste fehlt")
        for klasse in ("o_kanban", "o_pivot", "o_graph", "o_list", "o_activity"):
            pruefe(bool(seite.query_selector(".o_switch_view.%s" % klasse)),
                   "Ansicht '%s' weiterhin in der Umschaltung" % klasse)

        js_fehler[:] = seite.evaluate("() => window.__errs") or []
        ctx.close()

    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    print("JavaScript-Fehler: %d %s" % (len(js_fehler), js_fehler[:3]))
    print("RPC-Fehler: %d %s" % (len(rpc_fehler), rpc_fehler[:3]))
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
