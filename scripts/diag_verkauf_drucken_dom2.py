"""Diagnose 2: Struktur des Drucken-Untermenues im Auftragsformular."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from browser_verkauf_menue import lade_env, rpc_client, REPO

url = "http://localhost:8069"
env = lade_env(os.path.join(REPO, ".env"))
sid, kw = rpc_client(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])
SP = {"lang": "de_DE"}
g = kw("sale.order", "search_read", [[("state", "=", "sale")], ["name"]], context=SP)[0]

from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_diag_drucken2"),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1400}, accept_downloads=True)
    ctx.add_cookies([{"name": "session_id", "value": sid, "domain": "localhost", "path": "/"}])
    s = ctx.pages[0] if ctx.pages else ctx.new_page()
    s.goto("%s/odoo/sales/%d" % (url, g["id"]))
    s.wait_for_selector(".o_form_view", timeout=90000)
    s.wait_for_timeout(4500)
    s.click(".o_cp_action_menus button")
    s.wait_for_timeout(1500)
    sel = ".o-dropdown--has-parent:has-text('Drucken')"
    print("=== Hover-Versuch ===")
    try:
        s.hover(sel, timeout=8000)
        s.wait_for_timeout(2500)
    except Exception as ex:
        print("  hover fehlgeschlagen: %s" % str(ex)[:120])
    print("=== sichtbare Menues nach Hover ===")
    print(s.evaluate("""() => [...document.querySelectorAll('.o-dropdown--menu, .dropdown-menu')]
        .filter(e => e.offsetParent).map(e => e.innerText.replace(/\s+/g,' ').trim().slice(0,400))"""))
    if not s.evaluate("() => [...document.querySelectorAll('.o-dropdown--menu')].some(e => e.offsetParent)"):
        print("=== Klick-Versuch ===")
        try:
            s.click(sel, timeout=8000)
            s.wait_for_timeout(2500)
        except Exception as ex:
            print("  klick fehlgeschlagen: %s" % str(ex)[:120])
        print(s.evaluate("""() => [...document.querySelectorAll('.o-dropdown--menu, .dropdown-menu')]
            .filter(e => e.offsetParent).map(e => e.innerText.replace(/\s+/g,' ').trim().slice(0,400))"""))
    print("=== Menuepunkte jetzt (alle sichtbaren) ===")
    print(s.evaluate("""() => [...document.querySelectorAll('.o-dropdown--menu, .dropdown-menu')]
        .filter(e => e.offsetParent).map(e => e.innerText.replace(/\\s+/g,' ').trim().slice(0,300))"""))
    print("=== Bericht-Eintraege (a[data-menu]) ===")
    print(s.evaluate("""() => [...document.querySelectorAll('a, button')]
        .filter(e => e.offsetParent && /Bericht|Angebot|Proforma|Drucken/i.test(e.innerText||''))
        .map(e => e.tagName + ' :: ' + e.innerText.replace(/\\s+/g,' ').trim().slice(0,60) + ' | ' + e.className.slice(0,60))"""))
    ctx.close()
