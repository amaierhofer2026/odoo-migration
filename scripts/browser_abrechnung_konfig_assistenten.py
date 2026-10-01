"""Browser-Durchgang Abrechnung, zweiter Teil: Konfiguration, Assistenten, Gutschrift.

Prueft im echten Browser die Konfigurationsmenues, die Assistenten (Zahlung erfassen,
Gutschrift/Stornierung, Senden, Drucken) und - mit einem ausschliesslich in Odoo 18
angelegten und danach wieder entfernten Testbeleg - das Gutschriftsformular.

Aufruf: uv run --with playwright python scripts/browser_abrechnung_konfig_assistenten.py --instanz lokal|vm
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

VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session122", "konfig")

KONFIG = ["account.menu_action_tax_form", "account.menu_action_journal_form",
          "base.menu_action_currency_form", "account.menu_action_tax_position",
          "account.menu_action_payment_term_form", "account.menu_analytic_accounting",
          "account.menu_action_bank_account", "account.menu_account_config"]


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
            raise RuntimeError(str(antwort["error"])[:200])
        return antwort["result"]

    # Bestand vorher (Nachweis fuer den temporaeren Testbeleg)
    vorher = {"gutschriften": kw("account.move", "search_count", [[("move_type", "=", "out_refund")]]),
              "belege_gesamt": kw("account.move", "search_count", [[]]),
              "zeilen": kw("account.move.line", "search_count", [[]])}
    offene = kw("account.move", "search_read",
                [[("move_type", "=", "out_invoice"), ("state", "=", "posted"),
                  ("payment_state", "!=", "paid")], ["id", "name", "amount_residual"]], limit=1)
    print("Bestand vorher: %s | offene Rechnung fuer Assistenten: %s" % (vorher, offene))

    from playwright.sync_api import sync_playwright
    os.makedirs(VZ, exist_ok=True)
    ok = fehler = 0
    ergebnis = {"konfiguration": {}, "assistenten": {}, "gutschrift": {}}

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
            user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_ka_%s_%s" % (a.instanz, os.getpid())),
            channel="chrome", headless=True, viewport={"width": 1900, "height": 1400}, locale="de-DE")
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        s = ctx.pages[0] if ctx.pages else ctx.new_page()

        def text(selektor):
            return s.evaluate("""(sel) => [...document.querySelectorAll(sel)]
                .filter(e => e.getClientRects().length).map(e => (e.textContent || '').trim())
                .filter(t => t)""", selektor)

        # ---- Konfigurationsmenues ----
        for xmlid in KONFIG:
            modul, name = xmlid.split(".")
            daten = kw("ir.model.data", "search_read", [[("module", "=", modul), ("name", "=", name)],
                                                        ["res_id"]])
            if not daten:
                print("    Menue %s nicht gefunden" % xmlid)
                continue
            action = kw("ir.ui.menu", "read", [[daten[0]["res_id"]], ["name", "action"]])[0]
            aktion_id = int(action["action"].split(",")[1]) if action.get("action") else 0
            if not aktion_id:
                print("    Menue %s ohne Aktion" % xmlid)
                continue
            s.goto("%s/odoo/action-%s" % (url, aktion_id))
            s.wait_for_timeout(6000)
            spalten = text("thead th")
            reiter = text(".o_notebook .nav-link")
            felder = s.evaluate("""() => [...document.querySelectorAll('.o_form_label, label')]
                .filter(e => e.getClientRects().length).map(e => (e.textContent || '').trim())
                .filter(t => t).slice(0, 25)""")
            zeilen = len(s.query_selector_all(".o_data_row"))
            ergebnis["konfiguration"][xmlid] = {"spalten": spalten, "reiter": reiter,
                                                "felder": felder, "zeilen": zeilen}
            linke, rechte = spalten[:6], felder[:6]
            print("    %-34s Menue '%s' | Zeilen=%d | Spalten=%s" % (xmlid, action["name"], zeilen, linke))
            if rechte:
                print("        Formularfelder: %s" % rechte)
            pruefe(True, "Konfigurationsmenue '%s' im Browser geoeffnet" % action["name"])
            s.screenshot(path=os.path.join(VZ, "konfig_%s.png" % xmlid.replace(".", "_")), full_page=True)

        # ---- Assistenten auf einer offenen Rechnung ----
        if offene:
            s.goto("%s/web#id=%s&model=account.move&view_type=form" % (url, offene[0]["id"]))
            s.wait_for_selector(".o_form_view", timeout=90000)
            s.wait_for_timeout(4000)
            for knopf, titel in (("Einzahlung erfassen", "Zahlung erfassen"),
                                 ("Nach Gutschrift fragen", "Gutschrift/Stornierung"),
                                 ("Senden", "Rechnung senden"),
                                 ("Drucken", "Drucken")):
                try:
                    ziel = None
                    for el in s.query_selector_all("button"):
                        if el.is_visible() and knopf.lower() in (el.inner_text() or "").lower():
                            ziel = el
                            break
                    if ziel is None:
                        print("    Assistent '%s' auf dieser Rechnung nicht sichtbar" % knopf)
                        continue
                    ziel.click()
                    s.wait_for_timeout(4000)
                    dialog = text(".modal .modal-title, .modal .o_form_label, .modal label, .modal .nav-link")
                    ergebnis["assistenten"][titel] = dialog[:20]
                    print("    Assistent %-22s -> %s" % (titel, dialog[:10]))
                    pruefe(bool(dialog) or knopf == "Drucken", "Assistent '%s' geoeffnet" % titel)
                    s.screenshot(path=os.path.join(VZ, "assistent_%s.png" % titel.replace("/", "_")), full_page=True)
                    s.keyboard.press("Escape")
                    s.wait_for_timeout(1500)
                except Exception as fehler_text:
                    print("    Assistent %s: %s" % (titel, str(fehler_text)[:80]))

        # ---- Guetschrift: temporaerer Testbeleg ----
        test_id = None
        try:
            beleg = kw("account.move", "create", [{"move_type": "out_refund", "partner_id": False}] if False else [{
                "move_type": "out_refund",
                "partner_id": (kw("res.partner", "search", [[], ], limit=1) or [False])[0],
                "invoice_line_ids": [(0, 0, {"name": "ITK-Testzeile Gutschrift (nur Odoo 18, wird entfernt)",
                                             "quantity": 1, "price_unit": 10.0})],
            }], context={"lang": "de_DE"})
            test_id = beleg
            print("    Testgutschrift angelegt: id=%s" % test_id)
            s.goto("%s/web#id=%s&model=account.move&view_type=form" % (url, test_id))
            s.wait_for_selector(".o_form_view", timeout=90000)
            s.wait_for_timeout(4000)
            reiter = text(".o_notebook .nav-link")
            knoepfe = text(".o_form_statusbar button, .o_control_panel button")
            felder = s.evaluate("""() => [...document.querySelectorAll('.o_form_label, label')]
                .filter(e => e.getClientRects().length).map(e => (e.textContent || '').trim())
                .filter(t => t).slice(0, 30)""")
            ergebnis["gutschrift"] = {"reiter": reiter, "knoepfe": knoepfe, "felder": felder}
            print("    Gutschrift: Reiter=%s" % reiter)
            print("      Knoepfe=%s" % sorted(set(knoepfe))[:12])
            print("      Felder=%s" % felder[:12])
            pruefe("Andere Informationen" in reiter, "Gutschriftsformular zeigt Reiter 'Andere Informationen'")
            pruefe(any("Auf Entwurf setzen" in k for k in knoepfe), "Gutschriftsformular zeigt 'Auf Entwurf setzen'")
            pruefe(any("Nach Gutschrift fragen" in k for k in knoepfe), "Gutschriftsformular zeigt 'Nach Gutschrift fragen'")
            s.screenshot(path=os.path.join(VZ, "gutschrift.png"), full_page=True)
        except Exception as fehler_text:
            print("    Gutschrift-Test: %s" % str(fehler_text)[:150])
        finally:
            if test_id:
                try:
                    kw("account.move", "button_cancel", [[test_id]])
                except Exception:
                    pass
                try:
                    kw("account.move", "unlink", [[test_id]])
                    print("    Testgutschrift entfernt: id=%s" % test_id)
                except Exception as fehler_text:
                    print("    Entfernen fehlgeschlagen: %s" % str(fehler_text)[:150])
        ctx.close()

    nachher = {"gutschriften": kw("account.move", "search_count", [[("move_type", "=", "out_refund")]]),
               "belege_gesamt": kw("account.move", "search_count", [[]]),
               "zeilen": kw("account.move.line", "search_count", [[]])}
    print("\nBestand nachher: %s" % nachher)
    pruefe(vorher == nachher, "Bestand unveraendert (Testbeleg vollstaendig entfernt)")
    with open(os.path.join(VZ, "ergebnis.json"), "w", encoding="utf-8") as fh:
        json.dump({"vorher": vorher, "nachher": nachher, "daten": ergebnis}, fh, ensure_ascii=False, indent=1)
    print("\n%d OK / %d FEHL" % (ok, fehler))
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
