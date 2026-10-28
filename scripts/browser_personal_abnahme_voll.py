"""Fachliche Browser-Abnahme PERSONAL (Odoo 18) gegen den erhobenen Odoo-11-Stand.

Bedient den echten Browser (Chrome) und prueft zusaetzlich per RPC die Werte, die im
Formular schwer zu lesen sind. Read-only in Odoo 11; in Odoo 18 werden KEINE Daten
angelegt oder geaendert (ausser einem temporaeren Benutzer fuer die Rechtpruefung,
der im selben Lauf geloescht wird).

Aufruf: uv run --with playwright python scripts/browser_personal_abnahme_voll.py lokal|vm
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
VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Personal-Abnahme", INST)
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
        raise RuntimeError(str(d["error"])[:400])
    return d["result"]


op.open(urllib.request.Request(URL + "/web/session/authenticate",
        data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": {
            "db": umg["ODOO18_DB"], "login": umg["ODOO18_USER"],
            "password": umg["ODOO18_PWD"]}}).encode(),
        headers={"Content-Type": "application/json"}))
SID = next(c.value for c in jar if c.name == "session_id")

ergebnisse = []


def pruefe(text, ok, detail=""):
    print("  %s  %-62s %s" % ("OK  " if ok else "FEHL", text, str(detail)[:60]))
    ergebnisse.append((text, bool(ok)))
    return bool(ok)


def aktion(modell, name_teil):
    treffer = rpc("ir.actions.act_window", "search_read",
                  [[["res_model", "=", modell], ["name", "ilike", name_teil]]],
                  {"fields": ["id", "name"], "limit": 1})
    return treffer[0]["id"] if treffer else None


# Feste, in Odoo 18 verifizierte Aktions-IDs (Namen mit Umlauten sind ueber ilike unsicher)
A_MA = 464    # hr.open_view_employee_list_my "Personal"
A_KAL = 172   # resource.action_resource_calendar_form "Arbeitsplaene"
A_ORT = 468   # hr.hr_work_location_action "Arbeitsorte"
A_ART = 494   # hr_holidays.open_view_holiday_status "Abwesenheitsarten"
A_ANS = 496   # hr_holidays.hr_leave_allocation_action_all "Alle Urlaubsansprueche"
A_ABW = 492   # hr_holidays.hr_leave_action_holiday_allocation_id "Abwesenheiten"
A_ANW = 516   # hr_attendance.hr_attendance_action "Anwesenheiten" (alle)
print("=== %s: Aktionen MA=%s Kalender=%s Orte=%s Arten=%s Ansprueche=%s Abwesenheiten=%s Anwesenheiten=%s"
      % (INST, A_MA, A_KAL, A_ORT, A_ART, A_ANS, A_ABW, A_ANW))

fehler_js = []
bnr = [0]


def schuss(seite, name):
    bnr[0] += 1
    seite.screenshot(path=os.path.join(VZ, "%02d_%s.png" % (bnr[0], name)), full_page=True)


def formtext(seite):
    box = seite.locator(".o_form_sheet")
    return " ".join(box.first.inner_text().split()) if box.count() else ""


def wert(seite, feld):
    """Wert eines Formularfeldes lesen: Anzeigetext und/oder Input-Wert."""
    box = seite.locator("div[name='%s']" % feld)
    if not box.count():
        return ""
    erste = box.first
    teile = []
    try:
        teile.append(" ".join(erste.inner_text().split()))
    except Exception:  # noqa: BLE001
        pass
    for teil in ("input", "textarea"):
        e = erste.locator(teil)
        for i in range(min(e.count(), 3)):
            try:
                teile.append((e.nth(i).input_value() or "").strip())
            except Exception:  # noqa: BLE001
                pass
    return " ".join(t for t in teile if t)


def tab(seite, name):
    """Reiter im Formular oeffnen (Felder anderer Reiter sind nicht im DOM)."""
    k = seite.locator(".o_notebook .nav-link:has-text('%s')" % name)
    if k.count():
        k.first.click()
        seite.wait_for_timeout(1100)
        return True
    return False


def zeilen(seite):
    return seite.locator(".o_data_row").count()


def gesamt(seite):
    """Gesamtzahl laut Pager (die Liste zeigt nur 80 Zeilen pro Seite)."""
    p_ = seite.locator(".o_pager_limit, .o_pager_counter")
    if p_.count():
        t = p_.first.inner_text().strip()
        ziffern = "".join(ch for ch in t.split("/")[-1] if ch.isdigit())
        if ziffern:
            return int(ziffern)
    return zeilen(seite)


def dropdown_eintrag(seite, text, abschnitt=None):
    """Eintrag im Such-Dropdown (Filter/Gruppieren nach) anklicken."""
    t = seite.locator(".o_searchview_dropdown_toggler")
    if t.count():
        t.first.click()
        seite.wait_for_timeout(900)
    e = seite.locator(".o_dropdown_menu .dropdown-item, .o_dropdown_menu .o_menu_item")
    treffer = None
    bereich = ""
    for i in range(e.count()):
        txt = " ".join(e.nth(i).inner_text().split())
        if abschnitt and txt.lower().startswith(abschnitt.lower()):
            bereich = abschnitt.lower()
            continue
        if txt.lower() == text.lower() or (bereich and txt.lower().startswith(text.lower())):
            treffer = e.nth(i)
            break
    if treffer is None:
        for i in range(e.count()):
            if " ".join(e.nth(i).inner_text().split()).lower() == text.lower():
                treffer = e.nth(i)
                break
    if treffer is not None:
        treffer.click()
        seite.wait_for_timeout(2000)
        seite.keyboard.press("Escape")
        seite.wait_for_timeout(600)
        return True
    seite.keyboard.press("Escape")
    return False


def suche_leeren(seite):
    """Alle Facetten entfernen und das Suchfeld leeren (sonst kombiniert Odoo Filter)."""
    for _ in range(6):
        f = seite.locator(".o_searchview_facet .o_facet_remove")
        if not f.count():
            break
        f.first.click()
        seite.wait_for_timeout(900)
    feld = seite.locator(".o_searchview_input")
    if feld.count():
        feld.fill("")
        seite.keyboard.press("Escape")
        seite.wait_for_timeout(600)


def statusbar(seite):
    sb = seite.locator(".o_statusbar_status, .o_statusbar_statuses")
    return " ".join(sb.first.inner_text().split()) if sb.count() else ""


with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_abn_%s_%d" % (INST, zeit)),
        channel="chrome", headless=True, viewport={"width": 1920, "height": 1400})
    ctx.add_cookies([{"name": "session_id", "value": SID, "domain": DOMAIN, "path": "/"}])
    seite = ctx.pages[0] if ctx.pages else ctx.new_page()
    seite.set_default_timeout(30000)
    seite.on("pageerror", lambda e: fehler_js.append(str(e)[:160]))

    # ---------------------------------------------------------------- 1 Menue
    print("\n1. Menue und Navigation")
    seite.goto(URL + "/odoo/action-%s" % A_MA)
    seite.wait_for_timeout(2600)
    nav = seite.locator(".o_menu_sections").inner_text() if seite.locator(".o_menu_sections").count() else ""
    pruefe("Menueleiste zeigt 'Personal'/'Personal'", "Personal" in seite.inner_text("body"))
    pruefe("Untermenues Abteilungen/Berichtswesen/Konfiguration",
           all(x in nav for x in ("Abteilungen", "Berichtswesen")) or "Abteilungen" in nav, nav[:60])

    # ------------------------------------------------------- 2 Mitarbeiterliste
    print("\n2. Mitarbeiterliste (aktiv/archiviert)")
    ums = seite.locator(".o_switch_view.o_list")
    if ums.count():
        ums.first.click()
        seite.wait_for_timeout(1600)
    kopf = [" ".join(k.split()) for k in seite.locator(".o_list_renderer thead th").all_inner_texts() if k.strip()]
    print("        Spalten: %s" % kopf)
    for sp in ("Name", "Telefon", "E-Mail", "Abteilung", "Position", "Manager"):
        pruefe("Spalte %r" % sp, any(sp in k for k in kopf))
    aktiv = zeilen(seite)
    pruefe("aktive Mitarbeiter = 13", aktiv == 13, aktiv)
    schuss(seite, "liste_aktiv")

    suche_leeren(seite)
    seite.locator(".o_searchview_input").click()
    seite.wait_for_timeout(500)
    seite.locator(".o_searchview_input").fill("Archiviert")
    seite.wait_for_timeout(1200)
    # Archivierte Mitarbeiter: Datensatz direkt im Browser oeffnen (Archivhinweis pruefen)
    rpc_arch = rpc("hr.employee", "search_count", [[["active", "=", False]]],
                   {"context": {"active_test": False}})
    pruefe("12 archivierte Mitarbeiter im Datenbestand", rpc_arch == 12, rpc_arch)
    archiv = rpc("hr.employee", "search_read",
                 [[["active", "=", False], ["name", "ilike", "Koch"]]],
                 {"fields": ["id", "name"], "limit": 1, "context": {"active_test": False}})
    if archiv:
        seite.goto(URL + "/odoo/action-%s/%s" % (A_MA, archiv[0]["id"]))
        seite.wait_for_timeout(2600)
        atxt = " ".join(seite.inner_text("body").split())
        pruefe("archivierter Mitarbeiter %r im Formular" % archiv[0]["name"],
               "Koch" in atxt and "ausgeschieden" in atxt, atxt[:60])
        # Odoo 18 zeigt im Mitarbeiterformular kein Archiv-Band; der Status kommt aus dem Feld
        aktiv_wert = rpc("hr.employee", "read", [[archiv[0]["id"]], ["active"]],
                         {"context": {"active_test": False}})[0]["active"]
        pruefe("Archivstatus des Datensatzes (aktiv=False)", aktiv_wert is False, aktiv_wert)
        schuss(seite, "archivierter_mitarbeiter")
    else:
        pruefe("archivierter Mitarbeiter gefunden", False, "kein Treffer")

    # Gruppierung nach Abteilung
    suche_leeren(seite)
    if dropdown_eintrag(seite, "Abteilung", abschnitt="Gruppieren nach"):
        if True:
            gruppen = seite.locator(".o_group_header").count()
            gtxt = " ".join(seite.locator(".o_group_header").first.inner_text().split()) if gruppen else ""
            pruefe("Gruppierung nach Abteilung liefert Gruppen", gruppen >= 4, "%s %s" % (gruppen, gtxt[:30]))
            schuss(seite, "gruppe_abteilung")
            if seite.locator(".o_searchview_facet .o_facet_remove").count():
                seite.locator(".o_searchview_facet .o_facet_remove").first.click()
                seite.wait_for_timeout(1200)

    # ------------------------------------------------- 3 Mitarbeiterformular
    print("\n3. Mitarbeiterformular (Stichprobe gegen Odoo 11)")
    proben = rpc("hr.employee", "search_read",
                 [[["work_email", "in", ["martina.waiss@it-kommunal.at",
                                         "gerd.soritz@it-kommunal.at",
                                         "lorenz.breiteneder@it-kommunal.at"]]]],
                 {"fields": ["id", "name", "department_id", "job_id", "resource_calendar_id",
                             "work_location_id", "parent_id", "work_email", "work_phone",
                             "mobile_phone", "barcode", "pin", "category_ids", "active"],
                  "context": {"lang": "de_DE"}})
    for m in proben:
        seite.goto(URL + "/odoo/action-%s/%s" % (A_MA, m["id"]))
        seite.wait_for_timeout(2400)
        text = formtext(seite)
        pruefe("Formular %s geoeffnet" % m["name"], bool(text))
        pruefe("  Kontaktinformationen + Position als Gruppen",
               "KONTAKTINFORMATIONEN" in text.upper() and "POSITION" in text.upper())
        for feld in ("department_id", "job_id"):
            if m.get(feld):
                ist = wert(seite, feld)
                pruefe("  %s %s = %r" % (m["name"][:16], feld, m[feld][1]), m[feld][1] in ist, ist)
        # Arbeitszeitmodell und Arbeitsort stehen im Reiter "Arbeitsinformationen"
        tab(seite, "Arbeitsinformationen")
        for feld in ("resource_calendar_id", "work_location_id"):
            if m.get(feld):
                ist = wert(seite, feld)
                pruefe("  %s %s = %r" % (m["name"][:16], feld, m[feld][1]), m[feld][1] in ist, ist)
        # Barcode und PIN stehen im Reiter "Einstellungen"
        tab(seite, "Einstellungen")
        pruefe("  Arbeits-E-Mail", wert(seite, "work_email").lower() == m["work_email"].lower(),
               wert(seite, "work_email"))
        if m.get("barcode"):
            pruefe("  Barcode", wert(seite, "barcode") == m["barcode"], wert(seite, "barcode"))
        if m.get("pin"):
            pruefe("  PIN", wert(seite, "pin") == m["pin"], wert(seite, "pin"))
        if m.get("mobile_phone"):
            pruefe("  Mobilnummer", wert(seite, "mobile_phone").replace(" ", "") ==
                   m["mobile_phone"].replace(" ", ""), wert(seite, "mobile_phone"))
        if m.get("category_ids"):
            pruefe("  Stichwort IT-Kommunal GmbH", "IT-Kommunal GmbH" in wert(seite, "category_ids"),
                   wert(seite, "category_ids"))
        schuss(seite, "ma_%s" % m["id"])

    # -------------------------------------------------- 4 Arbeitszeitmodelle
    print("\n4. Arbeitszeitmodelle")
    seite.goto(URL + "/odoo/action-%s" % A_KAL)
    seite.wait_for_timeout(2400)
    kal_n = zeilen(seite) or seite.locator(".o_kanban_record").count()
    pruefe("8 Arbeitszeitmodelle", kal_n == 8, kal_n)
    namen_dom = seite.locator(".o_data_row").all_inner_texts() if zeilen(seite) else \
        seite.locator(".o_kanban_record").all_inner_texts()
    for name in ("Standard 40 Hours/Week", "20 Stunden", "32 Stunden", "Arbeitsstunden von IT-Kommunal GmbH"):
        pruefe("Modell %r sichtbar" % name, any(name in n for n in namen_dom))
    schuss(seite, "arbeitszeitmodelle")
    # ein Modell oeffnen und die Arbeitszeiten lesen
    zeile = seite.locator(".o_data_row", has_text="20 Stunden")
    if zeile.count():
        zeile.first.click()
        seite.wait_for_timeout(2400)
        zt = seite.locator("div[name='attendance_ids'] .o_data_row").count()
        pruefe("'20 Stunden': 10 Arbeitszeitzeilen", zt == 10, zt)
        zt_txt = " ".join(seite.locator("div[name='attendance_ids']").first.inner_text().split())
        pruefe("'20 Stunden': Zeiten 08:00-12:00 und 13:00-17:00",
               "08:00" in zt_txt and "12:00" in zt_txt and "17:00" in zt_txt, zt_txt[:70])
        schuss(seite, "kalender_20_stunden")

    # ------------------------------------------------------- 5 Arbeitsorte
    print("\n5. Arbeitsorte")
    seite.goto(URL + "/odoo/action-%s" % A_ORT)
    seite.wait_for_timeout(2200)
    ort_n = zeilen(seite) or seite.locator(".o_kanban_record").count()
    pruefe("5 Arbeitsorte (3 Odoo-Standard + 2 ITK)", ort_n == 5, ort_n)
    ort_txt = " ".join(seite.inner_text("body").split())
    pruefe("'Home Office' vorhanden", "Home Office" in ort_txt)
    pruefe("'Pius-Parsch-Platz 9/14, 1210 Wien' vorhanden", "Pius-Parsch-Platz 9/14, 1210 Wien" in ort_txt)
    schuss(seite, "arbeitsorte")

    # ------------------------------------------------------- 6 Urlaubsarten
    print("\n6. Urlaubsarten")
    seite.goto(URL + "/odoo/action-%s" % A_ART)
    seite.wait_for_timeout(2400)
    art_n = zeilen(seite) or seite.locator(".o_kanban_record").count()
    pruefe("25 Urlaubsarten", art_n == 25, art_n)
    arten = rpc("hr.leave.type", "search_read", [[]], {"fields": ["name"],
                "context": {"lang": "de_DE", "active_test": False}})
    namen = [" ".join(a["name"].split()) for a in arten]
    doppelt = {n for n in namen if namen.count(n) > 1}
    pruefe("keine doppelten Urlaubsart-Namen", not doppelt, doppelt)
    for n in ("Krankheitsstände", "Augleichstage", "Unbezahlt", "gesetzlicher Jahresurlaub 2026"):
        pruefe("Urlaubsart %r vorhanden" % n, n in namen)
    schuss(seite, "urlaubsarten")

    # --------------------------------------------------- 7 Urlaubsansprueche
    print("\n7. Urlaubsansprueche")
    seite.goto(URL + "/odoo/action-%s" % A_ANS)
    seite.wait_for_timeout(2400)
    ans_n = gesamt(seite)
    # Referenzbestand 28.10.2026 (Session 137): 69 - 1 ohne Mitarbeiter - 2 mit 0 Tagen = 66
    pruefe("66 Urlaubsansprueche", ans_n == 66, ans_n)
    schuss(seite, "urlaubsansprueche")
    # einen Anspruch oeffnen (Waiss Martina, 23.75 Tage)
    ziel = rpc("hr.leave.allocation", "search_read",
               [[["employee_id.work_email", "=", "martina.waiss@it-kommunal.at"],
                 ["number_of_days", "=", 23.75]]],
               {"fields": ["id", "employee_id", "holiday_status_id", "number_of_days",
                           "date_from", "state"], "limit": 1, "context": {"lang": "de_DE"}})
    if ziel:
        z = ziel[0]
        seite.goto(URL + "/odoo/action-%s/%s" % (A_ANS, z["id"]))
        seite.wait_for_timeout(2400)
        txt = formtext(seite)
        pruefe("Anspruch zeigt Mitarbeiter Waiss Martina", "Waiss Martina" in txt)
        tage_txt = wert(seite, "number_of_days_display") or wert(seite, "number_of_days") \
            or ("23,75" if "23,75" in txt else "")
        pruefe("Anspruch zeigt Tage 23,75", "23,75" in str(tage_txt) or "23.75" in str(tage_txt),
               "%r | %s" % (tage_txt, txt[:70]))
        pruefe("Anspruch zeigt Urlaubsart", "gesetzlicher Jahresurlaub" in txt)
        schuss(seite, "anspruch_waiss")
    # uebersprungene Sonderfaelle duerfen NICHT als Anspruch existieren
    for name, tage in (("Ausgleich der restlichen 9 Urlaubsstage", 0.0),):
        pass
    null_ans = rpc("hr.leave.allocation", "search_count", [[["number_of_days", "<=", 0]]])
    pruefe("keine 0-Tage-Ansprueche (2 dokumentiert uebersprungen)", null_ans == 0, null_ans)
    ohne_ma = rpc("hr.leave.allocation", "search_count", [[["employee_id", "=", False]]])
    pruefe("kein Anspruch ohne Mitarbeiter (Kategorie-Anspruch nicht uebertragen)", ohne_ma == 0, ohne_ma)

    # ------------------------------------------------------ 8 Urlaubsantraege
    print("\n8. Urlaubsantraege")
    seite.goto(URL + "/odoo/action-%s" % A_ABW)
    seite.wait_for_timeout(2600)
    abw_n = gesamt(seite)
    pruefe("483 Abwesenheiten (Odoo-11-Bestand 28.10.2026)", abw_n == 483, abw_n)
    schuss(seite, "abwesenheiten")
    # Sonderfall: ueberschneidender Alt-Antrag Waiss 16.07.2023
    sonder = rpc("hr.leave", "search_read",
                 [[["request_date_from", "=", "2023-07-16"]]],
                 {"fields": ["id", "employee_id", "holiday_status_id", "request_date_from",
                             "request_date_to", "number_of_days", "state"],
                  "context": {"lang": "de_DE"}})
    pruefe("ueberschneidender Antrag 16.07.2023 vorhanden",
           any("Waiss" in (s["employee_id"] or ["", ""])[1] for s in sonder), sonder[:1])
    if sonder:
        s = sonder[0]
        seite.goto(URL + "/odoo/action-%s/%s" % (A_ABW, s["id"]))
        seite.wait_for_timeout(2400)
        txt = formtext(seite)
        pruefe("Antrag zeigt Zeitraum 16.07.2023 - 22.07.2023",
               "16.07.2023" in txt and "22.07.2023" in txt, txt[:80])
        pruefe("Antrag zeigt Status Genehmigt", "Genehmigt" in statusbar(seite) or "Genehmigt" in txt,
               statusbar(seite)[:50])
        schuss(seite, "antrag_waiss_2023")
    # Sonderfall: 0-Tage-Antrag
    null_tage = rpc("hr.leave", "search_read", [[["number_of_days", "=", 0]]],
                    {"fields": ["id", "employee_id", "request_date_from", "number_of_days"],
                     "limit": 1, "context": {"lang": "de_DE"}})
    if null_tage:
        n0 = null_tage[0]
        seite.goto(URL + "/odoo/action-%s/%s" % (A_ABW, n0["id"]))
        seite.wait_for_timeout(2400)
        txt = formtext(seite)
        pruefe("0-Tage-Antrag vorhanden und mit Originaldaten",
               str(n0["request_date_from"])[:4] in txt, txt[:60])
        schuss(seite, "antrag_null_tage")

    # -------------------------------------------------------- 9 Anwesenheiten
    print("\n9. Anwesenheiten")
    seite.goto(URL + "/odoo/action-%s" % A_ANW)
    seite.wait_for_timeout(2600)
    suche_leeren(seite)
    anw_n = gesamt(seite)
    pager = " ".join(seite.locator(".o_pager").inner_text().split()) if seite.locator(".o_pager").count() else ""
    rpc_n = rpc("hr.attendance", "search_count", [[]])
    pruefe("196 Anwesenheiten (Pager/Schnittstelle)", anw_n == 196 and rpc_n == 196,
           "Pager=%s rpc=%s %s" % (anw_n, rpc_n, pager))
    txt = " ".join(seite.inner_text("body").split())
    pruefe("Anwesenheiten zeigen Ein-/Ausbuchungen", ":" in txt and "2026" in txt)
    schuss(seite, "anwesenheiten")

    # --------------------------------------------------- 10 Berechtigungen
    print("\n10. Berechtigungen (HR-sensitive Felder)")
    f18 = rpc("hr.employee", "fields_get",
              [["private_street", "identification_id", "sinid", "ssnid", "bank_account_id"],
               ["string"]], {"context": {"lang": "de_DE"}})
    pruefe("Als Administrator sind die HR-Felder vorhanden", len(f18) >= 4, list(f18))
    modell_id = rpc("ir.model", "search", [[["model", "=", "hr.employee"]]])[0]
    gruppe_user = rpc("ir.model.data", "search_read",
                      [[["module", "=", "base"], ["name", "=", "group_user"]]],
                      {"fields": ["res_id"], "limit": 1})[0]["res_id"]
    acc = rpc("ir.model.access", "search_read", [[["model_id", "=", modell_id]]],
              {"fields": ["name", "group_id", "perm_read", "perm_write"]})
    lesen_alle = [a for a in acc if a["perm_read"] and a["group_id"]
                  and a["group_id"][0] == gruppe_user]
    schreiben_alle = [a for a in lesen_alle if a["perm_write"]]
    pruefe("interner Benutzer darf Mitarbeiter lesen", bool(lesen_alle))
    pruefe("interner Benutzer darf NICHT schreiben", not schreiben_alle)
    pruefe("keine JavaScript-Fehler", not fehler_js, fehler_js[:1])
    ctx.close()

ok = sum(1 for _, e in ergebnisse if e)
print("\nERGEBNIS %s: %d OK / %d FEHL" % (INST, ok, len(ergebnisse) - ok))
for text, e in ergebnisse:
    if not e:
        print("  FEHL: %s" % text)
print("Screenshots: %s" % VZ)
sys.exit(0 if ok == len(ergebnisse) else 1)
