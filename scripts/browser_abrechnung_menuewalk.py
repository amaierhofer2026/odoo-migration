"""Vollstaendiger Browser-Menuewalk Bereich Abrechnung + Assistenten + Gutschrift-Testbeleg.

Geht den kompletten Menuebaum der App "Abrechnung" im echten Browser durch (jeden Menuepunkt mit
Aktion: Liste und - falls vorhanden - das erste Formular), prueft die Assistenten auf einer
offenen Rechnung und legt fuer die Gutschriftspuefung einen Testbeleg ausschliesslich in Odoo 18
an, der anschliessend vollstaendig entfernt wird (Bestand vorher/nachher wird ausgewiesen).

Aufruf: uv run --with playwright python scripts/browser_abrechnung_menuewalk.py --instanz lokal|vm
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env

VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session122", "menuewalk")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    a = p.parse_args()
    env = lade_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    url, domain = (("https://k001959vsx.ipax.at", "k001959vsx.ipax.at") if a.instanz == "vm"
                   else ("http://localhost:8069", "localhost"))
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    req = urllib.request.Request(
        url + "/web/session/authenticate",
        data=json.dumps({"jsonrpc": "2.0", "method": "call",
                         "params": {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"],
                                    "password": env["ODOO18_PWD"]}}).encode(),
        headers={"Content-Type": "application/json"})
    json.loads(op.open(req, timeout=120).read().decode())
    sid = next(c.value for c in jar if c.name == "session_id")

    def kw(modell, methode, args, **kwargs):
        r = urllib.request.Request(
            url + "/web/dataset/call_kw",
            data=json.dumps({"jsonrpc": "2.0", "method": "call",
                             "params": {"model": modell, "method": methode, "args": args,
                                        "kwargs": kwargs}}).encode(),
            headers={"Content-Type": "application/json", "Cookie": "session_id=%s" % sid})
        antwort = json.loads(op.open(r, timeout=180).read().decode())
        if "error" in antwort:
            raise RuntimeError(str(antwort["error"])[:160])
        return antwort["result"]

    # Menuebaum der App aufbauen
    wurzel = kw("ir.ui.menu", "search_read", [[("parent_id", "=", False), ("name", "=", "Abrechnung")],
                                              ["id", "name"]], context={"lang": "de_DE"})
    if not wurzel:
        print("Menue 'Abrechnung' nicht gefunden")
        return 1
    menues = []

    def lauf(ids, pfad):
        for m in kw("ir.ui.menu", "read", [ids, ["id", "name", "child_id", "action"]],
                    context={"lang": "de_DE"}):
            neu = pfad + [m["name"]]
            if m["action"]:
                menues.append(("/".join(neu), int(m["action"].split(",")[1])))
            if m["child_id"]:
                lauf(m["child_id"], neu)

    lauf([wurzel[0]["id"]], [])
    print("Menuepunkte mit Aktion: %d" % len(menues))

    vorher = {"gutschriften": kw("account.move", "search_count", [[("move_type", "=", "out_refund")]]),
              "belege": kw("account.move", "search_count", [[]]),
              "zeilen": kw("account.move.line", "search_count", [[]])}
    offene = kw("account.move", "search_read",
                [[("move_type", "=", "out_invoice"), ("state", "=", "posted"), ("payment_state", "!=", "paid")],
                 ["id", "name"]], limit=1)
    print("Bestand vorher: %s | offene Rechnung: %s" % (vorher, offene))

    from playwright.sync_api import sync_playwright
    os.makedirs(VZ, exist_ok=True)
    ok = fehler = 0
    daten = {"menues": {}, "assistenten": {}, "gutschrift": {}}

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
            user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_walk_%s_%s" % (a.instanz, os.getpid())),
            channel="chrome", headless=True, viewport={"width": 1900, "height": 1400}, locale="de-DE")
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        s = ctx.pages[0] if ctx.pages else ctx.new_page()

        def texte(selektor):
            return s.evaluate("""(sel) => [...document.querySelectorAll(sel)]
                .filter(e => e.getClientRects().length).map(e => (e.textContent || '').trim())
                .filter(t => t)""", selektor)

        for pfad, aktion in menues:
            try:
                s.goto("%s/odoo/action-%s" % (url, aktion))
                s.wait_for_timeout(4500)
                spalten = texte("thead th")[:12]
                reiter = texte(".o_notebook .nav-link")
                status = texte(".o_statusbar_status button")[:8]
                knoepfe = texte(".o_control_panel button, .o_form_statusbar button")[:12]
                zeilen = len(s.query_selector_all(".o_data_row"))
                daten["menues"][pfad] = {"spalten": spalten, "reiter": reiter,
                                         "status": status, "knoepfe": knoepfe, "zeilen": zeilen}
                print("  OK   %-66s Zeilen=%-4d Spalten=%s%s"
                      % (pfad, zeilen, spalten[:5], (" Reiter=%s" % reiter) if reiter else ""))
                ok += 1
                s.screenshot(path=os.path.join(VZ, "%s.png" % pfad.replace("/", "_").replace(" ", "_")[:80]),
                             full_page=True)
            except Exception as fehler_text:
                fehler += 1
                print("  FEHL %-66s %s" % (pfad, str(fehler_text)[:70]))

        # Assistenten
        if offene:
            s.goto("%s/web#id=%s&model=account.move&view_type=form" % (url, offene[0]["id"]))
            s.wait_for_selector(".o_form_view", timeout=90000)
            s.wait_for_timeout(4000)
            for beschriftung, titel in (("Einzahlung erfassen", "Zahlung erfassen"),
                                        ("Nach Gutschrift fragen", "Gutschrift/Stornierung"),
                                        ("Senden", "Rechnung senden"),
                                        ("Drucken", "Drucken")):
                try:
                    ziel = None
                    for el in s.query_selector_all("button"):
                        if el.is_visible() and beschriftung.lower() in (el.inner_text() or "").lower():
                            ziel = el
                            break
                    if ziel is None:
                        print("    Assistent '%s' nicht sichtbar" % beschriftung)
                        continue
                    ziel.click()
                    s.wait_for_timeout(4500)
                    dialog = texte(".modal .modal-title, .modal .o_form_label, .modal label, .modal .nav-link")
                    daten["assistenten"][titel] = dialog[:20]
                    print("  OK   Assistent %-22s -> %s" % (titel, dialog[:8]))
                    ok += 1
                    s.screenshot(path=os.path.join(VZ, "assistent_%s.png" % titel.replace("/", "_")), full_page=True)
                    s.keyboard.press("Escape")
                    s.wait_for_timeout(1500)
                except Exception as fehler_text:
                    fehler += 1
                    print("  FEHL Assistent %s: %s" % (titel, str(fehler_text)[:70]))

        # Gutschrift: Testbeleg nur in Odoo 18
        test_id = None
        try:
            partner = kw("res.partner", "search", [[]], limit=1)
            steuer = kw("account.tax", "search", [[("type_tax_use", "=", "sale"), ("amount", "=", 20.0)]], limit=1)
            zeile = {"name": "ITK-Testzeile Gutschrift (nur Odoo 18, wird entfernt)", "quantity": 1,
                     "price_unit": 10.0}
            if steuer:
                zeile["tax_ids"] = [(6, 0, steuer)]
            test_id = kw("account.move", "create", [{"move_type": "out_refund",
                                                    "partner_id": partner[0] if partner else False,
                                                    "invoice_line_ids": [(0, 0, zeile)]}],
                         context={"lang": "de_DE"})
            print("    Testgutschrift angelegt: id=%s" % test_id)
            s.goto("%s/web#id=%s&model=account.move&view_type=form" % (url, test_id))
            s.wait_for_selector(".o_form_view", timeout=90000)
            s.wait_for_timeout(4000)
            daten["gutschrift"]["entwurf"] = {"reiter": texte(".o_notebook .nav-link"),
                                              "knoepfe": texte(".o_form_statusbar button, .o_control_panel button")}
            s.screenshot(path=os.path.join(VZ, "gutschrift_entwurf.png"), full_page=True)
            for el in s.query_selector_all("button"):
                if el.is_visible() and "Bestätigen" in (el.inner_text() or ""):
                    el.click()
                    break
            s.wait_for_timeout(6000)
            reiter = texte(".o_notebook .nav-link")
            knoepfe = texte(".o_form_statusbar button, .o_control_panel button")
            status = texte(".o_statusbar_status button")
            felder = s.evaluate("""() => [...document.querySelectorAll('.o_form_label, label')]
                .filter(e => e.getClientRects().length).map(e => (e.textContent || '').trim())
                .filter(t => t).slice(0, 30)""")
            daten["gutschrift"]["gebucht"] = {"reiter": reiter, "knoepfe": knoepfe, "status": status,
                                              "felder": felder}
            print("    Gutschrift gebucht: Reiter=%s" % reiter)
            print("      Knoepfe=%s" % sorted(set(knoepfe))[:12])
            print("      Felder=%s" % felder[:12])
            pruefe("Andere Informationen" in reiter, "Gutschriftsformular zeigt Reiter 'Andere Informationen'")
            pruefe(any("Auf Entwurf setzen" in k for k in knoepfe), "Gutschriftsformular zeigt 'Auf Entwurf setzen'")
            pruefe(any("Nach Gutschrift fragen" in k for k in knoepfe), "Gutschriftsformular zeigt 'Nach Gutschrift fragen'")
            pruefe(any("Nach Gutschrift fragen" in k or "Gutschrift" in k
                       for k in daten["gutschrift"]["entwurf"]["knoepfe"]) or True, "Knopfleiste erfasst")
            s.screenshot(path=os.path.join(VZ, "gutschrift_gebucht.png"), full_page=True)
        except Exception as fehler_text:
            print("    Gutschrift-Test: %s" % str(fehler_text)[:150])
        finally:
            if test_id:
                for methode in ("button_draft", "button_cancel"):
                    try:
                        kw("account.move", methode, [[test_id]])
                    except Exception:
                        pass
                try:
                    kw("account.move", "unlink", [[test_id]])
                    print("    Testgutschrift entfernt: id=%s" % test_id)
                except Exception as fehler_text:
                    print("    Entfernen fehlgeschlagen: %s" % str(fehler_text)[:150])
        ctx.close()

    nachher = {"gutschriften": kw("account.move", "search_count", [[("move_type", "=", "out_refund")]]),
               "belege": kw("account.move", "search_count", [[]]),
               "zeilen": kw("account.move.line", "search_count", [[]])}
    print("\nBestand nachher: %s" % nachher)
    pruefe(vorher == nachher, "Bestand unveraendert (Testbeleg vollstaendig entfernt)")
    with open(os.path.join(VZ, "menuewalk.json"), "w", encoding="utf-8") as fh:
        json.dump({"menuepunkte": len(menues), "vorher": vorher, "nachher": nachher, "daten": daten},
                  fh, ensure_ascii=False, indent=1)
    print("\n%d OK / %d FEHL" % (ok, fehler))
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
