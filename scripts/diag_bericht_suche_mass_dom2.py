"""Diagnose 2: Suchmenue (Gruppieren nach) und Mass-Knopf im Pivot-Bericht."""
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
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_diag_suche2"),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1400})
    ctx.add_cookies([{"name": "session_id", "value": sid, "domain": "localhost", "path": "/"}])
    s = ctx.pages[0] if ctx.pages else ctx.new_page()
    s.goto("%s/odoo/action-itk_sale_management.action_sale_report_all_channels" % url)
    s.wait_for_selector(".o_pivot_view", timeout=90000)
    s.wait_for_timeout(5000)

    print("=== Elemente, die 'Werte' enthalten ===")
    print(s.eval_on_selector_all("*", """els => els.filter(e => e.children.length === 0 &&
        (e.innerText||'').includes('Werte')).map(e => e.tagName + '.' + e.className +
        ' | sichtbar=' + !!e.offsetParent).slice(0, 6)"""))

    print("=== Suchmenue ueber den Dropdown-Pfeil oeffnen ===")
    s.click(".o_searchview_dropdown_toggler")
    s.wait_for_timeout(2000)
    print(s.eval_on_selector_all(".o-dropdown--menu *", """els => els.filter(e =>
        e.children.length === 0 && (e.innerText||'').trim()).map(e =>
        e.tagName + ' :: ' + e.innerText.trim().slice(0, 60))"""))

    print("=== Gruppierung 'Vertriebskanal' anklicken ===")
    ziel = s.query_selector(".o-dropdown--menu :text('Vertriebskanal')")
    print("gefunden:", bool(ziel))
    if ziel:
        ziel.click()
        s.wait_for_timeout(5000)
        print("Facetten:", s.eval_on_selector_all(".o_searchview_facet", "els => els.map(e => e.innerText.replace(/\\s+/g,' '))"))
        print("Pivot:", s.eval_on_selector(".o_pivot_view", "e => e.innerText.replace(/\\s+/g,' ').slice(0,220)"))
    ctx.close()
