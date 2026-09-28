"""Diagnose: Aufbau des Pivots "Verkaufsauftraege aller Kanaele" im DOM."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from browser_verkauf_menue import lade_env, rpc_client, REPO

url = "http://localhost:8069"
env = lade_env(os.path.join(REPO, ".env"))
sid, kw = rpc_client(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])

from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_diag_pivot"),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1400})
    ctx.add_cookies([{"name": "session_id", "value": sid, "domain": "localhost", "path": "/"}])
    s = ctx.pages[0] if ctx.pages else ctx.new_page()
    s.goto("%s/odoo/action-itk_sale_management.action_sale_report_all_channels" % url)
    s.wait_for_selector(".o_pivot", timeout=90000)
    s.wait_for_timeout(5000)
    print("=== .o_pivot_view innerText ===")
    print(s.eval_on_selector(".o_pivot_view", "e => e.innerText"))
    print("=== Steuerung (Werte-Knopf) ===")
    print(s.eval_on_selector_all(".o_control_panel button, .o_control_panel .o_dropdown_toggler_btn",
                                 "els => els.map(e => e.innerText.trim()).filter(t => t).join(' | ')"))
    print("=== Mass-Auswahl (Dropdown oeffnen) ===")
    try:
        s.click(".o_pivot_measures, button:has-text('Werte')", timeout=8000)
        s.wait_for_timeout(1200)
        print(s.eval_on_selector(".o-dropdown--menu, .dropdown-menu", "e => e ? e.innerText : 'kein Menue'"))
    except Exception as ex:
        print("Dropdown nicht geoeffnet: %s" % ex)
    print("=== Tabellenzeilen im Pivot ===")
    print(s.evaluate("""() => [...document.querySelectorAll('.o_pivot table tr')].map(tr =>
        [...tr.querySelectorAll('th, td')].map(c => (c.innerText || '').trim() + '[' + (c.tagName) + ']').join(' ~ '))"""))
    print("=== Kopfzellen mit Klassen ===")
    print(s.eval_on_selector_all(".o_pivot thead th, .o_pivot thead td",
                                 "els => els.map(e => (e.className + ' || ' + e.innerText.trim()).slice(0,120))"))
    ctx.close()
