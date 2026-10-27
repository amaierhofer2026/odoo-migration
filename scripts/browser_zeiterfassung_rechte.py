#!/usr/bin/env python3
"""Browserabnahme RECHTE der Zeiterfassung (Session 136).

Zwei Testbenutzer werden angelegt, im echten Browser geprueft und wieder geloescht:

  * "nur eigene Zeiterfassungen" (Gruppe 607): sieht keine fremden Zeilen
  * "Alle Zeiterfassungen" (Gruppe 608): sieht alle Zeilen

Geprueft wird je Benutzer: Menue, Liste "Meine Stundenzettel", direkter Aufruf der
Aktion "Alle Zeiterfassungen", Suche nach einer fremden Beschreibung und das
Oeffnen einer fremden Zeile ueber die URL.

Aufruf:
  uv run --with playwright python scripts/browser_zeiterfassung_rechte.py --instanz lokal
"""
import argparse
import json
import os
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
from _o11o18_client import o18  # noqa: E402

PASSWORT = "Hermes-Rechte-136!"


def zugang(instanz):
    env = {}
    with open(os.path.join(REPO, ".env"), encoding="utf-8") as fh:
        for zeile in fh:
            if "=" in zeile and not zeile.strip().startswith("#"):
                k, v = zeile.split("=", 1)
                env[k.strip()] = v.strip()
    url = env["ODOO18_URL"] if instanz == "lokal" else "https://k001959vsx.ipax.at"
    return {"url": url.rstrip("/"), "user": env["ODOO18_USER"], "pwd": env["ODOO18_PWD"]}


def xmlid(cli, modul, name):
    d = cli.kw("ir.model.data", "search_read", [[("module", "=", modul), ("name", "=", name)]],
               fields=["res_id"], limit=1)
    return d[0]["res_id"] if d else None


def texte(seite, selektor, grenze=30):
    return [t for t in (t.strip() for t in seite.eval_on_selector_all(
        selektor, "(els) => els.map(e => (e.innerText || e.textContent || '').replace(/\\s+/g, ' ').trim())"
    )) if t][:grenze]


def pager(seite):
    return texte(seite, ".o_pager_value, .o_pager_limit", 4)


def lege_benutzer(cli, login, name, gruppen):
    alt = cli.kw("res.users", "search_read", [[("login", "=", login)]], fields=["id"], limit=1)
    if alt:
        cli.kw("res.users", "unlink", [[alt[0]["id"]]])
    uid = cli.kw("res.users", "create", [{
        "name": name, "login": login, "password": PASSWORT, "active": True,
        "groups_id": [(6, 0, gruppen)],
    }], context={"tracking_disable": True, "no_reset_password": True})
    return uid


def loesche_benutzer(cli, uid):
    try:
        cli.kw("res.users", "write", [[uid], {"active": False}])
        cli.kw("res.users", "unlink", [[uid]])
        return True
    except Exception as fehler:  # noqa: BLE001
        return str(fehler)[:200]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", required=True, choices=["lokal", "vm"])
    ap.add_argument("--out", default=os.path.join(os.environ.get("TEMP", "."), "zeit_rechte"))
    a = ap.parse_args()
    c = zugang(a.instanz)
    k = o18(a.instanz)
    ergebnis = {"instanz": a.instanz, "url": c["url"], "benutzer": {}}

    g607 = xmlid(k, "itk_timesheet", "group_timesheet_own_itk") or 607
    g608 = xmlid(k, "itk_timesheet", "group_timesheet_all_itk") or 608
    g_intern = xmlid(k, "base", "group_user")
    g_projekt = xmlid(k, "project", "group_project_user")
    gemeinsame = [g for g in (g_intern, g_projekt) if g]
    print("Gruppen: 607=%s 608=%s Basis=%s" % (g607, g608, gemeinsame))

    fremd = k.kw("account.analytic.line", "search_read",
                 [[("employee_id", "!=", False)]],
                 fields=["id", "name", "employee_id"], order="id asc", limit=1)
    fremd_id = fremd[0]["id"] if fremd else 0
    ergebnis["fremde_zeile"] = fremd[0] if fremd else None
    ergebnis["zeilen_gesamt"] = k.kw("account.analytic.line", "search_count", [[]])
    beschreibung = (fremd[0]["name"] or "").strip()[:40] if fremd else ""

    benutzer = [
        ("hermes.rechte.eigene@itk.local", "Hermes Rechte eigene", gemeinsame + [g607], "nur_eigene"),
        ("hermes.rechte.alle@itk.local", "Hermes Rechte alle", gemeinsame + [g608], "alle"),
    ]
    ids = {}
    for login, name, gruppen, schluessel in benutzer:
        ids[schluessel] = lege_benutzer(k, login, name, gruppen)
    print("Testbenutzer:", ids)

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        b = None
        for kanal in ("chrome", "msedge", None):
            try:
                b = p.chromium.launch(channel=kanal) if kanal else p.chromium.launch()
                break
            except Exception:  # noqa: BLE001
                continue
        if b is None:
            raise SystemExit("Kein Browser startbar")

        for login, name, gruppen, schluessel in benutzer:
            s = b.new_page(viewport={"width": 1500, "height": 950})
            eintrag = {}
            try:
                s.goto(c["url"] + "/web/login", wait_until="domcontentloaded", timeout=90000)
                time.sleep(2)
                s.fill("input[name='login']", login)
                s.fill("input[name='password']", PASSWORT)
                s.click(".oe_login_form button[type='submit']")
                s.wait_for_selector(".o_main_navbar", timeout=90000)
                time.sleep(3)
                eintrag["menue_zeiterfassung"] = "Zeiterfassung" in (s.inner_text(".o_main_navbar") or "")

                s.goto(c["url"] + "/odoo/action-1187", wait_until="domcontentloaded")
                time.sleep(5)
                s.screenshot(path="%s_%s_1_meine.png" % (a.out, schluessel))
                eintrag["meine"] = {"pager": pager(s),
                                    "zeilen": len(s.query_selector_all("tbody tr.o_data_row")),
                                    "fehler": "Zugriffsfehler" in (s.inner_text("body") or "")}

                s.goto(c["url"] + "/odoo/action-1190", wait_until="domcontentloaded")
                time.sleep(5)
                s.screenshot(path="%s_%s_2_alle.png" % (a.out, schluessel))
                rumpf = s.inner_text("body") or ""
                eintrag["alle"] = {"pager": pager(s),
                                   "zeilen": len(s.query_selector_all("tbody tr.o_data_row")),
                                   "zugriffsfehler": "Zugriffsfehler" in rumpf,
                                   "meldung": ("Zugriffsfehler" in rumpf)}

                s.goto(c["url"] + "/odoo/action-1190/%s" % fremd_id, wait_until="domcontentloaded")
                time.sleep(4)
                s.screenshot(path="%s_%s_3_fremde_zeile.png" % (a.out, schluessel))
                rumpf = s.inner_text("body") or ""
                eintrag["fremde_zeile"] = {
                    "zugriffsfehler": "Zugriffsfehler" in rumpf or "nicht gefunden" in rumpf,
                    "beschreibung_sichtbar": bool(beschreibung) and beschreibung in rumpf,
                }

                if beschreibung:
                    s.goto(c["url"] + "/odoo/action-1190", wait_until="domcontentloaded")
                    time.sleep(3)
                    feld = s.query_selector(".o_searchview_input")
                    if feld:
                        feld.click()
                        feld.fill(beschreibung[:25])
                        time.sleep(1.5)
                        s.keyboard.press("Enter")
                        time.sleep(3)
                    eintrag["suche_fremd"] = {"pager": pager(s),
                                              "zeilen": len(s.query_selector_all("tbody tr.o_data_row"))}
                    s.screenshot(path="%s_%s_4_suche.png" % (a.out, schluessel))
            except Exception as fehler:  # noqa: BLE001
                eintrag["fehler"] = str(fehler)[:300]
            ergebnis["benutzer"][schluessel] = eintrag
            s.close()
        b.close()

    ergebnis["geloescht"] = {schluessel: loesche_benutzer(k, uid) for schluessel, uid in ids.items()}
    pfad = a.out + ".json"
    os.makedirs(os.path.dirname(pfad) or ".", exist_ok=True)
    with open(pfad, "w", encoding="utf-8") as fh:
        json.dump(ergebnis, fh, ensure_ascii=False, indent=1, default=str)
    print(json.dumps(ergebnis, ensure_ascii=False, indent=1, default=str)[:4000])
    print("\nScreenshots:", a.out + "_*.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
