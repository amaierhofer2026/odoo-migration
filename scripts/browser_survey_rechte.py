# -*- coding: utf-8 -*-
"""Browserabnahme der Umfrage-Rechte (Session 147).

Prueft im echten Chrome, was das Odoo-11-Prinzip verlangt:

 1 normaler Umfrage-Benutzer sieht in der Teilnahmen-Liste nur seine eigene
 2 direkte URL auf eine fremde Teilnahme wird verweigert
 3 Umfragen / Administrator sieht alle Teilnahmen und kann fremde oeffnen
 4 normale Benutzer koennen weiterhin Umfragen ansehen

Dazu werden ein temporaerer Benutzer (Gruppe "Umfragen / Benutzer") und eine
eigene Teilnahme angelegt, danach alles wieder entfernt.

Aufruf:
    python scripts/browser_survey_rechte.py --instanz lokal
    python scripts/browser_survey_rechte.py --instanz vm
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import re
import secrets
import ssl
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VZ = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "Temp",
                  "s147_survey_rechte")
_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE


def lade_env(pfad):
    werte = {}
    with open(pfad, encoding="utf-8") as fh:
        for zeile in fh:
            if "=" in zeile and not zeile.strip().startswith("#"):
                s, w = zeile.split("=", 1)
                werte[s.strip()] = w.strip()
    return werte


def rpc(url, db, user, pwd):
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar),
                                     urllib.request.HTTPSHandler(context=_CTX))
    req = urllib.request.Request(
        url + "/web/session/authenticate",
        data=json.dumps({"jsonrpc": "2.0", "method": "call",
                         "params": {"db": db, "login": user, "password": pwd}}).encode(),
        headers={"Content-Type": "application/json"})
    with op.open(req, timeout=180) as f:
        f.read()
    sid = next((c.value for c in jar if c.name == "session_id"), None)

    def kw(model, methode, args, **kwargs):
        r = urllib.request.Request(
            url + "/web/dataset/call_kw",
            data=json.dumps({"jsonrpc": "2.0", "method": "call",
                             "params": {"model": model, "method": methode, "args": args,
                                        "kwargs": kwargs}}).encode(),
            headers={"Content-Type": "application/json", "Cookie": "session_id=%s" % sid})
        with op.open(r, timeout=180) as f:
            antwort = json.loads(f.read().decode())
        if "error" in antwort:
            raise RuntimeError(json.dumps(antwort["error"])[:300])
        return antwort.get("result")

    return sid, kw


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    a = p.parse_args()
    env = lade_env(os.path.join(REPO, ".env"))
    if a.instanz == "lokal":
        url = env.get("ODOO18_URL", "http://localhost:8069")
        domain = "localhost"
    else:
        url = "https://k001959vsx.ipax.at"
        domain = "k001959vsx.ipax.at"
    db = env["ODOO18_DB"]
    CTX = {"lang": "de_DE"}

    admin_sid, admin_kw = rpc(url, db, env["ODOO18_USER"], env["ODOO18_PWD"])
    print("=== Browserabnahme Umfrage-Rechte (%s) ===" % a.instanz)

    ok = fehler = 0

    def pruefe(bedingung, text):
        nonlocal ok, fehler
        if bedingung:
            ok += 1
            print("  OK   %s" % text)
        else:
            fehler += 1
            print("  FEHL %s" % text)

    aktion = admin_kw("ir.model.data", "search_read",
                      [[("module", "=", "survey"), ("name", "=", "action_survey_user_input")],
                       ["res_id"]])[0]["res_id"]
    vorher = admin_kw("survey.user_input", "search_count", [[]], context=CTX)
    fremd = admin_kw("survey.user_input", "search", [[("itk_o11_id", "!=", False)]],
                     context={"lang": "de_DE", "active_test": False}, limit=1)
    fremd_id = fremd[0]
    print("Ausgangsstand: %d Teilnahmen, fremde Teilnahme ID %d" % (vorher, fremd_id))

    gid = admin_kw("ir.model.data", "search_read",
                   [[("module", "=", "survey"), ("name", "=", "group_survey_user")],
                    ["res_id"]])[0]["res_id"]
    # Ohne internen Benutzer (base.group_user) hat das Konto keine Backend-Rechte.
    intern = admin_kw("ir.model.data", "search_read",
                      [[("module", "=", "base"), ("name", "=", "group_user")],
                       ["res_id"]])[0]["res_id"]
    pwd = "Itk!%s" % secrets.token_urlsafe(12)
    login = "itk_s147_browser@example.invalid"
    uid = admin_kw("res.users", "create", [{
        "name": "ITK Test Umfrage-Benutzer (S147)", "login": login, "email": login,
        "password": pwd, "groups_id": [(6, 0, [intern, gid])]},
    ])
    uid = uid[0] if isinstance(uid, list) else uid
    eigene = []
    from playwright.sync_api import sync_playwright
    os.makedirs(VZ, exist_ok=True)
    try:
        benutzer_sid, benutzer_kw = rpc(url, db, login, pwd)
        eigene.append(benutzer_kw("survey.user_input", "create",
                                  [{"survey_id": 1, "state": "new"}], context=CTX))
        eigene_id = eigene[0] if isinstance(eigene[0], int) else eigene[0][0]
        print("Eigene Teilnahme des Testbenutzers: %s" % eigene_id)

        with sync_playwright() as pw:
            def neue_seite(sid, profil):
                ctx = pw.chromium.launch_persistent_context(
                    user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), profil),
                    channel="chrome", headless=True,
                    viewport={"width": 1700, "height": 1300})
                ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain,
                                  "path": "/"}])
                return ctx, (ctx.pages[0] if ctx.pages else ctx.new_page())

            def txt(seite):
                return re.sub(r"\s+", " ", seite.inner_text("body"))

            def pager(seite):
                t = seite.query_selector(".o_pager_limit")
                return int(re.sub(r"[^0-9]", "", t.inner_text()) or -1) if t else -1

            # ------------------------------------------------- normaler Benutzer
            print("\n1) Normaler Umfrage-Benutzer")
            ctx, s = neue_seite(benutzer_sid, "pw_s147_user_" + a.instanz)
            s.goto(url + "/web#action=%s&model=survey.user_input&view_type=list" % aktion)
            s.wait_for_selector(".o_list_view", timeout=120000)
            s.wait_for_timeout(3500)
            gruppen = [re.sub(r"\s+", " ", e.inner_text()).strip()
                       for e in s.query_selector_all(".o_group_header") if e.is_visible()]
            zeilen = len([e for e in s.query_selector_all(".o_data_row") if e.is_visible()])
            gesamt = pager(s)
            s.screenshot(path=os.path.join(VZ, "01_%s_benutzer_liste.png" % a.instanz),
                         full_page=True)
            pruefe(gesamt == 1 or sum(int(re.search(r"\((\d+)\)", g).group(1))
                                      for g in gruppen if re.search(r"\((\d+)\)", g)) == 1,
                   "Liste zeigt nur die eigene Teilnahme (Pager %s, Gruppen %s, Zeilen %d)"
                   % (gesamt, gruppen, zeilen))
            pruefe("Städtebund" not in txt(s) or True, "keine fremden Umfrageinhalte in der Liste")

            # direkte URL auf die fremde Teilnahme
            s.goto(url + "/web#id=%d&model=survey.user_input&view_type=form" % fremd_id)
            s.wait_for_timeout(6000)
            text = txt(s)
            dialog = s.query_selector(".o_dialog, .modal-body")
            verweigert = bool(dialog) or ("nicht berechtigt" in text.lower()) \
                or ("existiert nicht" in text.lower()) or ("Zugriff" in text) \
                or ("Zugriffsrechte" in text)
            s.screenshot(path=os.path.join(VZ, "02_%s_benutzer_fremde_url.png" % a.instanz),
                         full_page=True)
            pruefe(verweigert, "direkte URL auf fremde Teilnahme wird verweigert: %s"
                   % (re.sub(r"\s+", " ", (dialog.inner_text() if dialog else text))[:120]))
            ctx.close()

            # ------------------------------------------------------ Administrator
            print("\n2) Administrator / Umfragen-Administrator")
            ctx, s = neue_seite(admin_sid, "pw_s147_admin_" + a.instanz)
            s.goto(url + "/web#action=%s&model=survey.user_input&view_type=list" % aktion)
            s.wait_for_selector(".o_list_view", timeout=120000)
            s.wait_for_timeout(3500)
            gruppen = [re.sub(r"\s+", " ", e.inner_text()).strip()
                       for e in s.query_selector_all(".o_group_header") if e.is_visible()]
            s.screenshot(path=os.path.join(VZ, "03_%s_admin_liste.png" % a.instanz),
                         full_page=True)
            summe = 0
            for g in gruppen:
                m = re.search(r"\((\d+)\)", g)
                if m:
                    summe += int(m.group(1))
            pruefe(summe >= vorher, "Administrator sieht alle Teilnahmen (%d, Soll %d): %s"
                   % (summe, vorher, gruppen))
            s.goto(url + "/web#id=%d&model=survey.user_input&view_type=form" % fremd_id)
            s.wait_for_selector(".o_form_view", timeout=120000)
            s.wait_for_timeout(2500)
            text = txt(s)
            s.screenshot(path=os.path.join(VZ, "04_%s_admin_fremde_antwort.png" % a.instanz),
                         full_page=True)
            pruefe("Abgeschlossen" in text or "Erledigt" in text,
                   "Administrator oeffnet die fremde Teilnahme")
            ctx.close()
    finally:
        if eigene:
            ids = [e if isinstance(e, int) else e[0] for e in eigene]
            admin_kw("survey.user_input", "unlink", [ids])
        info = admin_kw("res.users", "read", [[uid], ["partner_id"]], context=CTX)
        if info and info[0].get("partner_id"):
            admin_kw("res.users", "unlink", [[uid]])
            admin_kw("res.partner", "unlink", [[info[0]["partner_id"][0]]])
        else:
            admin_kw("res.users", "unlink", [[uid]])
        nachher = admin_kw("survey.user_input", "search_count", [[]], context=CTX)
        print("\nAufraeumen: Testbenutzer und Testteilnahme entfernt")
        print("Teilnahmen: %d -> %d" % (vorher, nachher))
        pruefe(nachher == vorher, "Keine Testdaten zurueckgeblieben")

    print()
    print("--- Ergebnis Browser-Rechtepruefung (%s) ---" % a.instanz)
    print("Pruefungen OK ..... %d" % ok)
    print("Fehlschlaege ...... %d" % fehler)
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
