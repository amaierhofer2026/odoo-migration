"""Diagnose: Gruppierung in Odoo 18 - welcher Selektor traegt die Gruppenkoepfe?

Nur lesend, keine Daten. Aufruf: uv run --with playwright python scripts/diag_gruppierung.py
"""
from __future__ import annotations

import http.cookiejar
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env

env = lade_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
url, domain = "http://localhost:8069", "localhost"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
req = urllib.request.Request(url + "/web/session/authenticate",
                            data=json.dumps({"jsonrpc": "2.0", "method": "call",
                                             "params": {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"],
                                                        "password": env["ODOO18_PWD"]}}).encode(),
                            headers={"Content-Type": "application/json"})
json.loads(op.open(req, timeout=120).read().decode())
sid = next(c.value for c in jar if c.name == "session_id")

from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_diag_grupp"), channel="chrome",
        headless=True, locale="de-DE", viewport={"width": 1800, "height": 1200})
    ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
    s = ctx.pages[0] if ctx.pages else ctx.new_page()
    s.goto("%s/odoo/action-393" % url)   # Abrechnung > Verkauf > Kunden
    s.wait_for_timeout(6000)
    print("Zeilen ohne Gruppierung:", len(s.query_selector_all(".o_data_row")))
    s.click(".o_searchview_dropdown_toggler")
    s.wait_for_timeout(1500)
    punkte = s.eval_on_selector_all(".o_group_by_menu .dropdown-item, .o_group_by_menu span",
                                    "els => els.map(e => e.textContent.trim()).filter(t => t)")
    print("Eintraege im Gruppieren-Menue:", punkte)
    treffer = s.query_selector_all(".o_group_by_menu .dropdown-item")
    for t in treffer:
        if "Verkäufer" in (t.inner_text() or ""):
            t.click()
            break
    s.wait_for_timeout(6000)
    print("nach Gruppierung:")
    print("  .o_group_header          :", len(s.query_selector_all(".o_group_header")))
    print("  .o_group_header (sichtb.):", len([e for e in s.query_selector_all(".o_group_header") if e.is_visible()]))
    print("  .o_list_table tr.o_group_header:", len(s.query_selector_all(".o_list_table tr.o_group_header")))
    klassen = s.eval_on_selector_all(".o_list_table tr, .o_list_renderer tr",
                                     "els => [...new Set(els.map(e => e.className))].slice(0, 12)")
    print("  Zeilenklassen:", klassen)
    texte = s.eval_on_selector_all(".o_list_table tr",
                                   "els => els.slice(0, 6).map(e => (e.textContent||'').trim().slice(0, 60))")
    print("  erste Zeilen:", texte)
    s.screenshot(path=os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session131",
                                   "diag_gruppierung_kunden.png"), full_page=True)
    ctx.close()
