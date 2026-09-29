"""Diagnose: Drucken-Menue im Auftragsformular (Odoo 18) und Report-URLs."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from browser_verkauf_menue import lade_env, rpc_client, REPO

url = "https://k001959vsx.ipax.at"
env = lade_env(os.path.join(REPO, ".env"))
sid, kw = rpc_client(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])
SP = {"lang": "de_DE"}
orders = kw("sale.order", "search_read", [[("state", "in", ["draft", "sent"])], ["name", "state"]],
            context=SP)
konf = kw("sale.order", "search_read", [[("state", "=", "sale")], ["name", "state"]], context=SP)
print("Entwuerfe/gesendet:", orders[:5])
print("Bestaetigt:", konf[:3])
ziel = (orders[0] if orders else konf[0])
print("Testauftrag:", ziel)

from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_diag_drucken"),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1400},
        accept_downloads=True)
    ctx.add_cookies([{"name": "session_id", "value": sid, "domain": "k001959vsx.ipax.at", "path": "/"}])
    s = ctx.pages[0] if ctx.pages else ctx.new_page()
    s.goto("%s/odoo/sales/%d" % (url, ziel["id"]))
    s.wait_for_selector(".o_form_view", timeout=90000)
    s.wait_for_timeout(5000)
    print("Titel:", s.title())
    print("=== Kopf-Knoepfe ===")
    print(s.eval_on_selector_all(".o_form_statusbar button, .o_control_panel button, .o_cp_buttons button",
                                 "els => els.map(e => e.innerText.trim() + ' | ' + e.className).slice(0, 20)"))
    print("=== Zahnrad/Aktionen-Menue ===")
    for sel in (".o_cp_action_menus button", ".o_cog_menu", "button.o_cp_action_menus"):
        try:
            if s.query_selector(sel):
                s.click(sel, timeout=5000)
                s.wait_for_timeout(1500)
                print("Menue (%s):" % sel, s.eval_on_selector_all(
                    ".o-dropdown--menu *", "els => els.filter(e => e.children.length === 0 && (e.innerText||'').trim()).map(e => e.innerText.trim()).slice(0, 25)"))
                s.keyboard.press("Escape")
                break
        except Exception as ex:
            print("  %s -> %s" % (sel, ex))
    print("=== Drucken-Knopf suchen ===")
    print(s.eval_on_selector_all("button, a", "els => els.filter(e => /Drucken|Print/.test(e.innerText||'')).map(e => e.innerText.trim() + ' | ' + e.className).slice(0, 10)"))
    print("=== Report-URLs (Reihenfolge) ===")
    rep = kw("ir.actions.report", "search_read",
             [[("model", "=", "sale.order")], ["name", "report_name", "binding_type"]], context=SP)
    for r in rep:
        print("   %-24s %s" % (r["name"], r["report_name"]))
    ctx.close()
