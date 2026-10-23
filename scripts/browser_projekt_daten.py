#!/usr/bin/env python3
"""Browserpruefung der MIGRIERTEN Projektdaten (Session 135).

Prueft im echten Browser (Chrome/Playwright, Login aus .env):
  * Projektliste: migrierte Projekte, Pager, Spalten
  * Projektformular: Kostenstelle (account_id), Zeiterfassung erlauben, Kunde
  * Aufgabenliste: Spalten, Filter "Meine Aufgaben", Gruppierung "Stufe"
  * Aufgabe: Startdatum, Bearbeiter, Stufe, Frist
  * Menue Projekt/Konfiguration/Stufen
Screenshots + JSON unter --out.

Aufruf:
  uv run --with playwright python scripts/browser_projekt_daten.py --instanz lokal
"""
import argparse
import json
import os
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))


def zugang(instanz):
    env = {}
    with open(os.path.join(REPO, ".env"), encoding="utf-8") as fh:
        for zeile in fh:
            if "=" in zeile and not zeile.strip().startswith("#"):
                k, v = zeile.split("=", 1)
                env[k.strip()] = v.strip()
    url = env["ODOO18_URL"] if instanz == "lokal" else "https://k001959vsx.ipax.at"
    return {"url": url.rstrip("/"), "user": env["ODOO18_USER"], "pwd": env["ODOO18_PWD"]}


def texte(seite, sel, grenze=40):
    return [t.strip() for t in seite.eval_on_selector_all(
        sel, "(els) => els.map(e => (e.innerText || e.textContent || '').replace(/\\s+/g, ' ').trim())"
    ) if t.strip()][:grenze]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", required=True, choices=["lokal", "vm"])
    ap.add_argument("--out", default=os.path.join(os.environ.get("TEMP", "."), "projekt_daten"))
    a = ap.parse_args()
    c = zugang(a.instanz)
    e = {"instanz": a.instanz, "url": c["url"]}

    from _o11o18_client import o18
    k = o18(a.instanz)
    pid = k.kw("project.project", "search_read", [[("name", "ilike", "amtsweg.gv.at - Support")]],
               fields=["id", "name"], limit=1)
    tid = k.kw("project.task", "search_read", [[("itk_date_start", "!=", False)]],
               fields=["id", "name"], order="id desc", limit=1)
    e["projekt_id"] = pid[0]["id"] if pid else None
    e["aufgabe_id"] = tid[0]["id"] if tid else None
    e["erwartung_projekte"] = k.kw("project.project", "search_count", [[]])
    e["erwartung_aufgaben"] = k.kw("project.task", "search_count", [[]])

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = None
        for kanal in ("chrome", "msedge", None):
            try:
                b = p.chromium.launch(channel=kanal) if kanal else p.chromium.launch()
                e["browser"] = kanal or "chromium"
                break
            except Exception as exc:  # noqa: BLE001
                e.setdefault("browser_fehler", []).append(str(exc)[:80])
        s = b.new_page(viewport={"width": 1600, "height": 1000})
        s.goto(c["url"] + "/web/login", wait_until="domcontentloaded", timeout=90000)
        time.sleep(2)
        if not s.query_selector(".o_main_navbar"):
            s.fill("input[name='login']", c["user"])
            s.fill("input[name='password']", c["pwd"])
            s.click(".oe_login_form button[type='submit']")
        s.wait_for_selector(".o_main_navbar", timeout=90000)
        time.sleep(2)

        # 1) Projektliste
        s.goto(c["url"] + "/odoo/project", wait_until="domcontentloaded")
        time.sleep(4)
        s.screenshot(path=a.out + "_1_projektliste.png")
        e["projektliste_spalten"] = texte(s, "thead th")
        e["projektliste_pager"] = texte(s, ".o_pager_value, .o_pager_limit")
        e["projektliste_zeilen"] = len(s.query_selector_all("tbody tr.o_data_row"))
        e["projektnamen_beispiel"] = texte(s, "tbody tr.o_data_row td:nth-child(2)", 6)

        # 2) Projektformular (migriertes Projekt)
        if e["projekt_id"]:
            s.goto(c["url"] + "/odoo/project/%s" % e["projekt_id"], wait_until="domcontentloaded")
            time.sleep(4)
            s.screenshot(path=a.out + "_2_projektformular.png")
            e["projektfelder"] = texte(s, ".o_form_view .o_field_widget[name]", 40)
            e["projekt_labels"] = texte(s, ".o_form_view label.o_form_label", 40)

        # 3) Aufgabenliste mit Filter und Gruppierung
        s.goto(c["url"] + "/odoo/project.task", wait_until="domcontentloaded")
        time.sleep(4)
        s.screenshot(path=a.out + "_3_aufgabenliste.png")
        e["aufgaben_spalten"] = texte(s, "thead th")
        e["aufgaben_pager"] = texte(s, ".o_pager_value, .o_pager_limit")
        try:
            s.click(".o_searchview_input")
            time.sleep(1)
            s.keyboard.type("Meine Aufgaben")
            time.sleep(2)
            s.keyboard.press("Enter")
            time.sleep(3)
            e["filter_meine_aufgaben"] = texte(s, ".o_searchview_facet", 3)
            s.screenshot(path=a.out + "_4_aufgaben_meine.png")
        except Exception as exc:  # noqa: BLE001
            e["filter_fehler"] = str(exc)[:150]

        # 4) Aufgabe mit Startdatum
        if e["aufgabe_id"]:
            s.goto(c["url"] + "/odoo/project.task/%s" % e["aufgabe_id"], wait_until="domcontentloaded")
            time.sleep(4)
            s.screenshot(path=a.out + "_5_aufgabe.png")
            e["aufgabe_daten"] = s.evaluate(
                "() => { const g = (n) => { const el = document.querySelector('.o_field_widget[name=\"'+n+'\"]');"
                " return el ? (el.innerText||el.value||'').replace(/\\s+/g,' ').trim().slice(0,60) : null; };"
                " return {name: g('name'), start: g('itk_date_start'), stage: g('stage_id'),"
                " users: g('user_ids'), deadline: g('date_deadline'), allocated: g('allocated_hours')}; }")

        # 5) Stufen-Menue
        s.goto(c["url"] + "/odoo/action-project.open_task_type_form", wait_until="domcontentloaded")
        time.sleep(4)
        s.screenshot(path=a.out + "_6_stufen.png")
        e["stufen_pager"] = texte(s, ".o_pager_value, .o_pager_limit")
        e["stufen_titel"] = s.title()

        b.close()

    with open(a.out + ".json", "w", encoding="utf-8") as fh:
        json.dump(e, fh, ensure_ascii=False, indent=1)
    print(json.dumps(e, ensure_ascii=False, indent=1)[:3500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
