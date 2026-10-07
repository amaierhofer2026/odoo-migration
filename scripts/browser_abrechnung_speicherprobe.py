"""Browser-Speicherprobe im Bereich Abrechnung (ungefaehrliche Testdaten, danach entfernt).

Legt im Menue Abrechnung > Konfiguration > Verwaltung > Produktkategorien (Aktion 299) ueber die
Oberflaeche genau eine Testkategorie an, prueft Speichern und Suche, entfernt sie wieder und
vergleicht den Bestand vorher/nachher.

Aufruf: uv run --with playwright python scripts/browser_abrechnung_speicherprobe.py --instanz lokal|vm
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import shutil
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env  # noqa: E402

TESTNAME = "ITK-TEST-S131"
VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session131")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], required=True)
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
        antwort = json.loads(op.open(r, timeout=300).read().decode())
        if "error" in antwort:
            raise RuntimeError(str(antwort["error"])[:200])
        return antwort["result"]

    modelle = ["product.category", "account.analytic.account", "account.tax", "account.journal",
               "account.payment.term", "account.move"]
    vorher = {m: kw(m, "search_count", [[]]) for m in modelle}

    from playwright.sync_api import sync_playwright
    vz = os.path.join(VZ, "browser", a.instanz)
    os.makedirs(vz, exist_ok=True)
    profil = os.path.join(os.environ.get("TEMP", "/tmp"), "pw_speicherprobe_%s" % a.instanz)
    if os.path.isdir(profil):
        shutil.rmtree(profil, ignore_errors=True)
    ok = fehler = 0

    def pruefe(bedingung, text, detail=""):
        nonlocal ok, fehler
        if bedingung:
            ok += 1
            print("   OK   %s%s" % (text, (" -> %s" % detail) if detail else ""), flush=True)
        else:
            fehler += 1
            print("   FEHL %s%s" % (text, (" -> %s" % detail) if detail else ""), flush=True)

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(user_data_dir=profil, channel="chrome",
                                                    headless=True, locale="de-DE",
                                                    viewport={"width": 1800, "height": 1300})
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        s = ctx.pages[0] if ctx.pages else ctx.new_page()
        ctx.set_default_timeout(12000)
        neu = []
        try:
            s.goto("%s/odoo/action-299" % url)          # Produktkategorien
            s.wait_for_timeout(4000)
            s.screenshot(path=os.path.join(vz, "speicherprobe_liste.png"), full_page=True)
            s.click(".o_list_button_add")
            s.wait_for_timeout(3000)
            pruefe(bool(s.query_selector(".o_form_view")), "Neuanlage-Formular geoeffnet")
            s.fill(".o_field_widget[name='name'] input", TESTNAME)
            s.wait_for_timeout(800)
            s.screenshot(path=os.path.join(vz, "speicherprobe_neu.png"), full_page=True)
            s.click(".o_form_button_save")
            s.wait_for_timeout(5000)
            body = s.inner_text("body")[:5000]
            pruefe("RPC_ERROR" not in body and "Traceback" not in body, "Speichern ohne Serverfehler")
            neu = kw("product.category", "search_read", [[("name", "=", TESTNAME)], ["id", "name", "parent_id"]])
            pruefe(len(neu) == 1, "Testkategorie gespeichert", "id=%s" % (neu[0]["id"] if neu else "-"))
            s.screenshot(path=os.path.join(vz, "speicherprobe_gespeichert.png"), full_page=True)
            s.goto("%s/odoo/action-299" % url)
            s.wait_for_timeout(3000)
            s.click(".o_searchview_input")
            s.fill(".o_searchview_input", TESTNAME)
            s.keyboard.press("Enter")
            s.wait_for_timeout(4000)
            treffer = s.evaluate("""(n) => [...document.querySelectorAll('td.o_data_cell')]
                .filter(e => e.getClientRects().length && (e.textContent || '').includes(n)).length""", TESTNAME)
            pruefe(treffer >= 1, "Testkategorie in der Suche gefunden", "%d Treffer" % treffer)
            s.screenshot(path=os.path.join(vz, "speicherprobe_suche.png"), full_page=True)
        except Exception as ex:
            pruefe(False, "Speicherprobe ohne Fehler", str(ex)[:120])
        finally:
            for r in kw("product.category", "search_read", [[("name", "=", TESTNAME)], ["id"]]):
                kw("product.category", "unlink", [[r["id"]]])
            ctx.close()

    nachher = {m: kw(m, "search_count", [[]]) for m in modelle}
    rest = kw("product.category", "search_read", [[("name", "=", TESTNAME)], ["id"]])
    print("Bestand vorher : %s" % vorher)
    print("Bestand nachher: %s" % nachher)
    print("Reste zur Testkategorie: %s" % rest)
    pruefe(vorher == nachher and not rest, "Bestand unveraendert, keine Testdaten zurueckgeblieben")
    with open(os.path.join(vz, "speicherprobe.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"vorher": vorher, "nachher": nachher, "angelegt": neu, "reste": rest,
                   "ok": ok, "fehler": fehler}, fh, ensure_ascii=False, indent=1)
    print("\nErgebnis: %d OK / %d FEHL" % (ok, fehler))
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
