"""Diagnose 3: DOM des Drucken-Untermenues (Struktur, Ausklappmechanik)."""
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
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_diag_drucken3"),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1400}, accept_downloads=True)
    ctx.add_cookies([{"name": "session_id", "value": sid, "domain": "localhost", "path": "/"}])
    s = ctx.pages[0] if ctx.pages else ctx.new_page()
    s.goto("%s/odoo/sales/%d" % (url, g["id"]))
    s.wait_for_selector(".o_form_view", timeout=90000)
    s.wait_for_timeout(4500)
    s.click(".o_cp_action_menus button")
    s.wait_for_timeout(1500)
    print("=== Klick: Zahnrad -> Drucken ===")
    s.click(".o_cp_action_menus button")
    s.wait_for_timeout(1200)
    s.click(".o-dropdown--has-parent:has-text('Drucken')", timeout=8000)
    s.wait_for_timeout(2000)
    print("Popover:", s.evaluate("() => { const m = document.querySelector('.o_popover, .o-dropdown--menu');
        return m ? m.innerText.replace(/\s+/g,' ').trim().slice(0, 400) : 'kein Menue'; }"))
    print("=== Berichtseintraege suchen ===")
    print(s.evaluate("""() => [...document.querySelectorAll('.o_popover *, .o-dropdown--menu *')]
        .filter(e => e.children.length === 0 && (e.innerText||'').trim())
        .map(e => e.tagName + ' :: ' + e.innerText.trim()).slice(0, 20)"""))
    print("=== Klick auf ITK-Angebot/Auftrag (Download?) ===")
    try:
        with s.expect_download(timeout=60000) as dl:
            s.click(".o-popover *:text-is('ITK-Angebot/Auftrag')", timeout=10000)
        d = dl.value
        pfad = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session121", "druckberichte", "test_itk.pdf")
        os.makedirs(os.path.dirname(pfad), exist_ok=True)
        d.save_as(pfad)
        print("Download:", pfad, os.path.getsize(pfad), "Bytes")
        from pypdf import PdfReader
        r = PdfReader(pfad)
        print("Seiten:", len(r.pages))
        print("Text:", (r.pages[0].extract_text() or "")[:600].replace("
", " | "))
    except Exception as ex:
        print("Download fehlgeschlagen:", str(ex)[:300])
    ctx.close()
