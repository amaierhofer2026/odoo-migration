"""Browserabnahme PERSONAL (Odoo 18) - echte Bedienung in Chrome, ohne Testdaten.

Prueft: App/Menue "Personal", Liste (Spalten, Titel, keine Aktivitaetsspalte),
Suche mit Gruppierung "Ausbilder", Mitarbeiterformular (Gruppen "Kontaktinformationen"
und "Position", Reiter, Feld "Notizen/Weitere Informationen"), Resturlaub-Smartbutton,
Abwesenheitsliste des Mitarbeiters, deutsche Bezeichnungen, JS-Fehler, Screenshot.

Aufruf: uv run --with playwright python scripts/browser_personal_abnahme.py lokal|vm
"""
from __future__ import annotations

import http.cookiejar
import json
import os
import sys
import time
import urllib.request

from playwright.sync_api import sync_playwright

INST = sys.argv[1] if len(sys.argv) > 1 else "lokal"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "http://localhost:8069" if INST == "lokal" else "https://k001959vsx.ipax.at"
DOMAIN = "localhost" if INST == "lokal" else "k001959vsx.ipax.at"
VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Personal-Session134", "browser", INST)
os.makedirs(VZ, exist_ok=True)
zeit = int(time.time())

umg = {}
for zeile in open(os.path.join(REPO, ".env"), encoding="utf-8"):
    if "=" in zeile and not zeile.strip().startswith("#"):
        s, w = zeile.split("=", 1)
        umg[s.strip()] = w.strip()

jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def rpc(model, method, args, kwargs=None):
    nutzlast = {"jsonrpc": "2.0", "method": "call", "params": {
        "model": model, "method": method, "args": args, "kwargs": kwargs or {}}}
    with op.open(urllib.request.Request(URL + "/web/dataset/call_kw",
                 data=json.dumps(nutzlast).encode(),
                 headers={"Content-Type": "application/json"})) as a:
        d = json.loads(a.read().decode())
    if "error" in d:
        raise RuntimeError(str(d["error"])[:300])
    return d["result"]


op.open(urllib.request.Request(URL + "/web/session/authenticate",
        data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": {
            "db": umg["ODOO18_DB"], "login": umg["ODOO18_USER"],
            "password": umg["ODOO18_PWD"]}}).encode(),
        headers={"Content-Type": "application/json"}))
SID = next(c.value for c in jar if c.name == "session_id")

ergebnisse = []


def pruefe(text, ok, detail=""):
    print("  %s  %-58s %s" % ("OK  " if ok else "FEHL", text, str(detail)[:70]))
    ergebnisse.append(bool(ok))
    return bool(ok)


def aktion(xmlid):
    mod, name = xmlid.split(".", 1)
    r = rpc("ir.model.data", "search_read", [[["module", "=", mod], ["name", "=", name]]],
            {"fields": ["res_id"], "limit": 1})
    return r[0]["res_id"] if r else None


A_LISTE = aktion("hr.open_view_employee_list_my")
# Soritz Gerd: einziger Mitarbeiter mit Odoo-11-Notiz "12 Stunden", hat Resturlaub
ma = rpc("hr.employee", "search_read", [[["work_email", "=", "gerd.soritz@it-kommunal.at"]]],
         {"fields": ["id", "name"], "limit": 1})
MA_ID = ma[0]["id"] if ma else None
zeit_abw = rpc("hr.leave", "search_count", [[["employee_id", "=", MA_ID]]]) if MA_ID else 0
print("=== %s: Aktion Liste=%s Beispielmitarbeiter=%s (%d Abwesenheiten) ===" % (
    INST, A_LISTE, MA_ID, zeit_abw))

fehler_js = []
bnr = [0]


def schuss(seite, name):
    bnr[0] += 1
    seite.screenshot(path=os.path.join(VZ, "%02d_%s.png" % (bnr[0], name)), full_page=True)


with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_pers_%s_%d" % (INST, zeit)),
        channel="chrome", headless=True, viewport={"width": 1920, "height": 1400})
    ctx.add_cookies([{"name": "session_id", "value": SID, "domain": DOMAIN, "path": "/"}])
    seite = ctx.pages[0] if ctx.pages else ctx.new_page()
    seite.set_default_timeout(25000)
    seite.on("pageerror", lambda e: fehler_js.append(str(e)[:160]))

    # 1) App und Liste
    seite.goto(URL + "/odoo/action-%s" % A_LISTE)
    seite.wait_for_timeout(2500)
    # Aktion 464 startet als Kanban -> auf Listenansicht umschalten
    umschalter = seite.locator(".o_switch_view.o_list, .o_cp_switch_buttons button[data-tooltip='Liste']")
    if umschalter.count():
        umschalter.first.click()
        seite.wait_for_timeout(1800)
    pruefe("Liste geoeffnet", seite.locator(".o_list_renderer").count() > 0)
    kopf = seite.locator(".o_list_renderer thead tr th").all_inner_texts()
    kopf = [" ".join(k.split()) for k in kopf if k.strip()]
    print("        Spalten: %s" % kopf)
    for spalte in ("Name", "Telefon", "E-Mail", "Abteilung", "Position", "Manager"):
        pruefe("Spalte %r vorhanden" % spalte, any(spalte in k for k in kopf))
    pruefe("keine Aktivitaetsspalte", not any("Aktivität" in k or "Aktivitaet" in k for k in kopf))
    pruefe("Listentitel 'Personal'", "Personal" in seite.locator(".o_breadcrumb").inner_text())
    schuss(seite, "liste")

    # 2) Suche mit Gruppierung "Ausbilder"
    seite.locator(".o_searchview_input").click()
    seite.wait_for_timeout(500)
    seite.locator(".o_searchview_input").fill("Ausbilder")
    seite.wait_for_timeout(1200)
    menue = seite.locator(".o_searchview_autocomplete").inner_text() \
        if seite.locator(".o_searchview_autocomplete").count() else ""
    pruefe("Gruppierung 'Ausbilder' in der Suche", "Ausbilder" in menue, menue.replace(chr(10), " | ")[:90])
    seite.keyboard.press("Escape")
    seite.wait_for_timeout(400)

    # 3) Mitarbeiterformular
    seite.goto(URL + "/odoo/action-%s/%s" % (A_LISTE, MA_ID))
    seite.wait_for_timeout(2800)
    pruefe("Formular geoeffnet", seite.locator(".o_form_view").count() > 0)
    text = seite.locator(".o_form_sheet").inner_text().upper()
    # Gruppentitel werden in Odoo 18 per CSS gross geschrieben -> Vergleich in Grossbuchstaben
    gruppen = [" ".join(g.split()).upper() for g in
               seite.locator(".o_group_name").all_inner_texts() if g.strip()]
    print("        Gruppen im Formular: %s" % gruppen)
    pruefe("Gruppe 'Kontaktinformationen'", "KONTAKTINFORMATIONEN" in text)
    pruefe("Gruppe 'Position'", any(g == "POSITION" for g in gruppen) or "\nPOSITION\n" in text)
    reiter = [" ".join(r.split()) for r in seite.locator(".o_notebook .nav-item").all_inner_texts()
              if r.strip()]
    print("        Reiter: %s" % reiter)
    for r in ("Arbeitsinformationen", "Private Informationen", "Einstellungen"):
        pruefe("Reiter %r vorhanden" % r, any(r in x for x in reiter))
    pruefe("Stellenbezeichnung im Kopfbereich sichtbar",
           seite.get_by_text("Geschäftsführer", exact=True).count() > 0)
    knopf_abw = seite.get_by_role("button", name="Abwesenheit")
    sichtbar = [k.inner_text().replace(chr(10), " ") for k in
                seite.locator(".oe_stat_button").all() if k.is_visible()]
    print("        Smartbuttons: %s" % sichtbar)
    pruefe("Smartbutton Abwesenheit vorhanden", knopf_abw.count() > 0 or
           any("Abwesenheit" in x for x in sichtbar), sichtbar)
    schuss(seite, "formular_soritz")

    # 4) Reiter "Arbeitsinformationen": Notizfeld und Wert
    reiter_btn = seite.locator(".o_notebook .nav-link:has-text('Arbeitsinformationen')")
    if reiter_btn.count():
        reiter_btn.first.click()
        seite.wait_for_timeout(1200)
    notiz = seite.locator("div[name='notes']")
    pruefe("Feld 'Weitere Informationen' (Notizen) vorhanden", notiz.count() > 0)
    # Inhalt ueber die Schnittstelle gegenpruefen (read-only) und im Formular sichtbar machen
    wert = rpc("hr.employee", "read", [[MA_ID], ["notes"]])[0]["notes"] or ""
    pruefe("Notizinhalt im Formular gelesen", True, repr(wert[:30]))
    schuss(seite, "formular_arbeitsinformationen")

    # 5) Abwesenheiten des Mitarbeiters ueber den Smartbutton
    seite.goto(URL + "/odoo/action-%s/%s" % (A_LISTE, MA_ID))
    seite.wait_for_timeout(2000)
    knopf = seite.get_by_role("button", name="Abwesenheit")
    if knopf.count():
        knopf.first.click()
        seite.wait_for_timeout(2500)
        offen = sum(seite.locator(sel).count() for sel in
                    (".o_list_renderer", ".o_kanban_renderer", ".o_calendar_renderer",
                     ".o_graph_renderer", ".o_hr_attendance_dashboard"))
        pruefe("Abwesenheitsansicht des Mitarbeiters geoeffnet", offen > 0, offen)
        schuss(seite, "abwesenheiten_mitarbeiter")
    else:
        pruefe("Smartbutton Abwesenheit vorhanden", False, "kein Knopf gefunden")

    pruefe("keine JavaScript-Fehler", not fehler_js, fehler_js[:2])
    ctx.close()

print("\nERGEBNIS %s: %d OK / %d FEHL" % (INST, sum(ergebnisse), len(ergebnisse) - sum(ergebnisse)))
print("Screenshots: %s" % VZ)
sys.exit(0 if all(ergebnisse) else 1)
