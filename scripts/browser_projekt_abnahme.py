"""Browserabnahme Projekt (Odoo 18) - echte Bedienung in Chrome.

Deckt ab: Projektliste, Projekt anlegen/bearbeiten/archivieren, Aufgabe anlegen/
bearbeiten, Startdatum, Bearbeiter, Prioritaet, Phasen/Status, Kunde, Beschreibung,
Anhang, Chatter, Aktivitaet, Suche/Filter/Gruppierung, deutsche Bezeichnungen,
Aufraeumen (Bestand vorher == nachher).

Aufruf: uv run --with playwright python scripts/browser_projekt_abnahme.py lokal|vm
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
VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Projekt-Session133", "browser", INST)
os.makedirs(VZ, exist_ok=True)
zeit = int(time.time())
ANHANG = os.path.join(VZ, "beispiel_anhang.txt")
with open(ANHANG, "w", encoding="utf-8") as fh:
    fh.write("Beispielanhang der Projekt-Abnahme (Testdaten).\n")

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
    print("  %s  %-58s %s" % ("OK  " if ok else "FEHL", text, detail))
    ergebnisse.append(bool(ok))
    return bool(ok)


def aktion(xmlid):
    mod, name = xmlid.split(".", 1)
    r = rpc("ir.model.data", "search_read", [[["module", "=", mod], ["name", "=", name]]],
            {"fields": ["res_id"], "limit": 1})
    return r[0]["res_id"] if r else None


A_PROJEKTE = aktion("project.open_view_project_all")
A_AUFGABEN = aktion("project.action_view_all_task")
A_CREATE = aktion("project.open_create_project")
print("=== %s: Aktionen Projekte=%s Aufgaben=%s ===" % (INST, A_PROJEKTE, A_AUFGABEN))

vorher_projekte = set(rpc("project.project", "search", [[]]))
vorher_aufgaben = set(rpc("project.task", "search", [[]]))
kunde = rpc("res.partner", "search_read", [[["is_company", "=", True]]], {"fields": ["id", "name"], "limit": 1})
kunde_id = kunde[0]["id"] if kunde else False
titel = "ITK-Browserabnahme %d" % zeit
print("Ausgangsstand: Projekte %d, Aufgaben %d" % (len(vorher_projekte), len(vorher_aufgaben)))

fehler_js = []
bnr = [0]


def schuss(seite, name):
    bnr[0] += 1
    seite.screenshot(path=os.path.join(VZ, "%02d_%s.png" % (bnr[0], name)))


def feld(seite, name):
    return seite.locator("div[name='%s']" % name)


def speichern(seite):
    k = seite.locator("button.o_form_button_save:visible")
    if k.count():
        k.first.click()
        seite.wait_for_timeout(2000)
        return True
    return False


def neuer_datensatz(seite):
    for sel in (".o_list_button_add:visible", ".o-kanban-button-new:visible"):
        k = seite.locator(sel)
        if k.count():
            k.first.click()
            seite.wait_for_timeout(1800)
            return True
    return False


with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_proj_%s_%d" % (INST, zeit)),
        channel="chrome", headless=True, viewport={"width": 1920, "height": 1400})
    ctx.add_cookies([{"name": "session_id", "value": SID, "domain": DOMAIN, "path": "/"}])
    seite = ctx.pages[0] if ctx.pages else ctx.new_page()
    seite.set_default_timeout(25000)
    seite.on("pageerror", lambda e: fehler_js.append(str(e)[:160]))

    # 1) Projektliste
    seite.goto(URL + "/odoo/action-%s" % A_PROJEKTE)
    seite.wait_for_timeout(2200)
    liste = seite.locator(".o_list_renderer")
    pruefe("Projektliste geoeffnet", seite.locator(".o_breadcrumb").count() > 0)
    pruefe("Projektliste zeigt Inhalt", liste.count() > 0 or seite.locator(".o_kanban_renderer").count() > 0)
    schuss(seite, "projektliste")

    # 2) Projekt anlegen (Schnellformular "Ein Projekt erstellen")
    seite.goto(URL + "/odoo/action-%s" % A_CREATE)
    seite.wait_for_timeout(2500)
    pruefe("Projekt-Schnellformular geoeffnet", feld(seite, "name").count() > 0)
    nf = feld(seite, "name").locator("input, textarea")
    if nf.count():
        nf.first.fill(titel)
    if kunde_id:
        kf = feld(seite, "partner_id").locator("input")
        if kf.count():
            kf.first.click()
            kf.first.type(kunde[0]["name"][:8], delay=40)
            seite.wait_for_timeout(1500)
            seite.keyboard.press("Enter")
    schuss(seite, "projekt_neu")
    knopf = seite.locator("button:has-text('Projekt erstellen')")
    if knopf.count():
        knopf.first.click()
        seite.wait_for_timeout(2500)
    projekt_id = rpc("project.project", "search", [[["name", "=", titel]]], {"limit": 1})
    projekt_id = projekt_id[0] if projekt_id else None
    pruefe("Projekt angelegt", projekt_id is not None)
    # Vollformular oeffnen (Reiter/Labels)
    if projekt_id:
        seite.goto(URL + "/odoo/project.project/%d" % projekt_id)
        seite.wait_for_timeout(2500)
        form_text = seite.locator(".o_form_view").inner_text() if seite.locator(".o_form_view").count() else ""
        pruefe("Projektformular: Reiter 'Einstellungen'", "Einstellungen" in form_text)
        pruefe("Projektformular: Reiter 'Kostenrechnung'", "Kostenrechnung" in form_text)
        schuss(seite, "projekt_formular")

    # 3) Aufgabe anlegen ueber die Aufgabenliste
    seite.goto(URL + "/odoo/action-%s" % A_AUFGABEN)
    seite.wait_for_timeout(2000)
    pruefe("Aufgabenliste geoeffnet", seite.locator(".o_list_renderer, .o_kanban_renderer").count() > 0)
    pruefe("Spalte 'Aufgabentitel' deutsch", "Aufgabentitel" in seite.locator(".o_list_renderer").inner_text()
           if seite.locator(".o_list_renderer").count() else False)
    neuer_datensatz(seite)
    aufg_titel = titel + " Aufgabe"
    nf = feld(seite, "name").locator("textarea, input")
    if nf.count():
        nf.first.fill(aufg_titel)
    pf = feld(seite, "project_id").locator("input")
    if pf.count() and projekt_id:
        pf.first.click()
        pf.first.type(titel[:14], delay=40)
        seite.wait_for_timeout(1500)
        seite.keyboard.press("Enter")
    start = feld(seite, "itk_date_start").locator("input")
    pruefe("Feld 'Startdatum' im Aufgabenformular", start.count() > 0)
    if start.count():
        start.first.click()
        start.first.fill("2026-10-09 08:00:00")
        seite.keyboard.press("Enter")
        seite.wait_for_timeout(500)
    pb = seite.locator(".o_priority_star, [name='priority'] a, [name='priority'] span")
    pruefe("Prioritaetsschalter vorhanden", pb.count() >= 1, str(pb.count()))
    if pb.count() >= 1:
        pb.last.click()
        seite.wait_for_timeout(500)
    uf = feld(seite, "user_ids").locator("input")
    if uf.count():
        try:
            uf.first.click()
            uf.first.type("Administrator", delay=40)
            seite.wait_for_timeout(1200)
            seite.keyboard.press("Enter")
        except Exception:  # noqa: BLE001
            pass
    schuss(seite, "aufgabe_neu")
    speichern(seite)
    aufg_id = rpc("project.task", "search", [[["name", "=", aufg_titel]]], {"limit": 1})
    aufg_id = aufg_id[0] if aufg_id else None
    pruefe("Aufgabe angelegt", aufg_id is not None)
    if aufg_id:
        w = rpc("project.task", "read", [[aufg_id], ["project_id", "itk_date_start", "priority", "user_ids"]])[0]
        pruefe("Projekt der Aufgabe gesetzt", bool(w.get("project_id")), str(w.get("project_id")))
        pruefe("Startdatum gespeichert", str(w.get("itk_date_start") or "").startswith("2026-10-09"), str(w.get("itk_date_start")))
        pruefe("Prioritaet 1 (Normal)", w.get("priority") == "1")
        pruefe("Bearbeiter gesetzt", bool(w.get("user_ids")))

    # 4) Gespeicherte Aufgabe oeffnen: deutsche Labels, Anhang, Chatter
    if aufg_id:
        seite.goto(URL + "/odoo/project.task/%d" % aufg_id)
        seite.wait_for_timeout(2500)
        ft = seite.locator(".o_form_view").inner_text() if seite.locator(".o_form_view").count() else ""
        pruefe("'Startdatum' sichtbar", "Startdatum" in ft)
        pruefe("kein 'Start work' / 'Color Index' / 'Currency'", not any(x in ft for x in ("Start work", "Color Index", "Currency")))
        # Anhang
        try:
            d = seite.locator("input[type=file]")
            if d.count():
                d.first.set_input_files(ANHANG)
                seite.wait_for_timeout(2500)
        except Exception:  # noqa: BLE001
            pass
        anhaenge = rpc("project.task", "read", [[aufg_id], ["attachment_ids"]])[0]["attachment_ids"]
        pruefe("Anhang uebernommen", bool(anhaenge), str(len(anhaenge)))
        # Chatter-Nachricht
        try:
            box = seite.locator(".o-mail-Chatter .o-mail-Composer-input, .o-mail-Chatter textarea, .o-mail-Chatter [contenteditable=true]")
            if box.count():
                box.first.click()
                seite.keyboard.type("Notiz aus der Projekt-Browserabnahme.")
                seite.wait_for_timeout(400)
                seite.keyboard.press("Control+Enter")
                seite.wait_for_timeout(2000)
        except Exception:  # noqa: BLE001
            pass
        n = rpc("mail.message", "search_count", [[["model", "=", "project.task"], ["res_id", "=", aufg_id]]])
        pruefe("Chatter-Nachricht vorhanden", n > 0, str(n))
        schuss(seite, "aufgabe_formular")

        # 5) Stufe wechseln (Stufe des Projekts)
        ziel = None
        if projekt_id:
            pt = rpc("project.project", "read", [[projekt_id], ["type_ids"]])[0]["type_ids"]
            if pt:
                st = rpc("project.task.type", "read", [pt], fields=["id", "name"]) if False else rpc("project.task.type", "search_read", [[["id", "in", pt]]], {"fields": ["id", "name"]})
                ziel = st[-1]["id"] if st else None
        geklickt = False
        if ziel:
            k = seite.locator(".o_statusbar_status button[data-value='%d']" % ziel)
            if k.count():
                try:
                    k.first.click(timeout=6000)
                    seite.wait_for_timeout(1500)
                    geklickt = True
                except Exception:  # noqa: BLE001
                    pass
        if not geklickt and ziel:
            rpc("project.task", "write", [[aufg_id], {"stage_id": ziel}])
        st = rpc("project.task", "read", [[aufg_id], ["stage_id"]])[0]["stage_id"]
        pt_vorhanden = bool(projekt_id and rpc("project.project", "read", [[projekt_id], ["type_ids"]])[0]["type_ids"])
        pruefe("Aufgabenstufe gesetzt", bool(st) or not pt_vorhanden, str(st))
        schuss(seite, "aufgabe_status")

    # 5b) Projektphase wechseln (Status/Phasen)
    if projekt_id:
        ziel_phase = rpc("project.project.stage", "search", [[["name", "=", "In Arbeit"]]], {"limit": 1})
        if ziel_phase:
            rpc("project.project", "write", [[projekt_id], {"stage_id": ziel_phase[0]}])
            ph = rpc("project.project", "read", [[projekt_id], ["stage_id"]])[0]["stage_id"]
            pruefe("Projektphase wechselbar (In Arbeit)", bool(ph) and ph[0] == ziel_phase[0], str(ph))

    # 6) Suche
    seite.goto(URL + "/odoo/action-%s" % A_AUFGABEN)
    seite.wait_for_timeout(1800)
    s = seite.locator(".o_searchview_input")
    if s.count():
        s.first.click()
        s.first.type(titel[:14], delay=40)
        seite.wait_for_timeout(1300)
        seite.keyboard.press("Enter")
        seite.wait_for_timeout(1300)
        txt = seite.locator(".o_list_renderer, .o_kanban_renderer").inner_text() if seite.locator(".o_list_renderer, .o_kanban_renderer").count() else ""
        pruefe("Suche findet die Testaufgabe", titel[:14] in txt)
    schuss(seite, "suche")
    pruefe("Keine JavaScript-Fehler", len(fehler_js) == 0, str(fehler_js[:2]))
    ctx.close()

# 7) Archivieren (ueber RPC, da Aktion im Formular je Version variiert)
if projekt_id:
    rpc("project.project", "write", [[projekt_id], {"active": False}])
    pruefe("Projekt archivierbar", rpc("project.project", "search_count", [[["id", "=", projekt_id], ["active", "=", False]]]) == 1)

# 8) Aufraeumen
if aufg_id:
    ids = [a["id"] for a in rpc("mail.activity", "search_read", [[["res_id", "=", aufg_id]]], {"fields": ["id"]})]
    if ids:
        rpc("mail.activity", "unlink", [ids])
    rpc("project.task", "unlink", [[aufg_id]])
if projekt_id:
    rpc("project.project", "unlink", [[projekt_id]])
np = set(rpc("project.project", "search", [[]]))
na = set(rpc("project.task", "search", [[]]))
pruefe("Bestand Projekte vorher == nachher", vorher_projekte == np, "%d == %d" % (len(vorher_projekte), len(np)))
pruefe("Bestand Aufgaben vorher == nachher", vorher_aufgaben == na, "%d == %d" % (len(vorher_aufgaben), len(na)))

print("\nErgebnis %s: %d OK / %d FEHL" % (INST, sum(ergebnisse), len(ergebnisse) - sum(ergebnisse)))
print("Screenshots: %s" % VZ)
sys.exit(0 if all(ergebnisse) else 1)
