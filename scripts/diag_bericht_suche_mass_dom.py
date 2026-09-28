"""Diagnose: Suchvorschlaege (Gruppierung Vertriebskanal) und Mass-Knopf im Pivot."""
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
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_diag_suche"),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1400})
    ctx.add_cookies([{"name": "session_id", "value": sid, "domain": "localhost", "path": "/"}])
    s = ctx.pages[0] if ctx.pages else ctx.new_page()
    s.goto("%s/odoo/action-itk_sale_management.action_sale_report_all_channels" % url)
    s.wait_for_selector(".o_pivot_view", timeout=90000)
    s.wait_for_timeout(5000)
    print("=== Knoepfe im Kopfbereich ===")
    print(s.eval_on_selector_all(".o_control_panel button",
                                 "els => els.filter(e => e.offsetParent).map(e => JSON.stringify(e.innerText.trim()) + ' class=' + e.className).slice(0, 25)"))
    print("=== alle Elemente mit 'Werte' ===")
    print(s.eval_on_selector_all("*", "els => els.filter(e => e.children.length === 0 && (e.innerText||'').trim() === 'Werte').map(e => e.tagName + '.' + e.className + ' | parent=' + e.parentElement.tagName + '.' + e.parentElement.className).slice(0, 5)"))
    print("=== Suchvorschlaege nach Eingabe 'Vertriebs' ===")
    s.click(".o_searchview_input")
    s.fill(".o_searchview_input", "Vertriebs")
    s.wait_for_timeout(3000)
    print(s.eval_on_selector_all(".o_searchview_autocomplete li",
                                 "els => els.map(e => (e.className + ' :: ' + e.innerText.trim().slice(0,70)))"))
    ctx.close()
