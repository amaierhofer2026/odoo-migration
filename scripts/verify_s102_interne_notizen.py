"""Browser-Pruefung des Tabs 'Interne Notizen' (Session 102, Bereich Kontakte).

Prueft im echten Browser gegen die VM (verbindliche Abnahmeumgebung), dass der Tab die
Odoo-11-Abschnitte zeigt: Alarmierung bei Auftrag (sale_warn), Warnung zu Rechnung (invoice_warn),
Warnung beim Einkaufsauftrag (purchase_warn) und das Notizfeld (comment).
Legt einen Screenshot im Desktop-Ordner ab.

Aufruf:  uv run --with playwright python scripts/verify_s102_interne_notizen.py
"""
import json, os, time

ZIEL = r"C:\Users\anna.maierhofer\Desktop\Odoo18-Layoutvergleich-Session95"
VM = "https://k001959vsx.ipax.at"
PARTNER = 69

env = {}
for z in open(r"C:\Odoo-Test\.env", encoding="utf-8"):
    if "=" in z and not z.strip().startswith("#"):
        k, v = z.split("=", 1)
        env[k.strip()] = v.strip()

JS = """() => {
  const sichtbar = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const pane = document.querySelector('.o_notebook .tab-pane.active');
  const felder = [...document.querySelectorAll('.o_notebook .tab-pane.active .o_field_widget[name]')]
        .filter(sichtbar).map(e => e.getAttribute('name'));
  const sep = [...document.querySelectorAll('.o_notebook .tab-pane.active .o_horizontal_separator, .o_notebook .tab-pane.active separator')]
        .filter(sichtbar).map(e => (e.innerText || '').trim());
  const labels = [...document.querySelectorAll('.o_notebook .tab-pane.active label.o_form_label')]
        .filter(sichtbar).map(e => (e.innerText || '').trim());
  const ph = [...document.querySelectorAll('.o_notebook .tab-pane.active textarea, .o_notebook .tab-pane.active input')]
        .filter(sichtbar).map(e => e.getAttribute('placeholder')).filter(Boolean);
  return { text: pane ? pane.innerText : '', felder: felder, sep: sep, labels: labels, platzhalter: ph };
}"""

from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    s = b.new_page(viewport={"width": 1680, "height": 1100}, ignore_https_errors=True)
    s.goto(VM + "/web/login", wait_until="load"); time.sleep(2)
    s.fill("input[name='login']", env["ODOO18_USER"]); s.fill("input[name='password']", env["ODOO18_PWD"])
    s.click(".oe_login_form button[type=submit]"); s.wait_for_load_state("load"); time.sleep(4)
    s.goto("%s/odoo/contacts/%d" % (VM, PARTNER), wait_until="load")
    s.wait_for_selector(".o_form_view"); time.sleep(5)
    tabs = s.evaluate("[...document.querySelectorAll('.o_notebook .nav-link')].map(e => e.innerText.trim())")
    print("Tabs:", tabs)
    idx = tabs.index("Interne Notizen") if "Interne Notizen" in tabs else 1
    s.click(".o_notebook .nav-link >> nth=%d" % idx); time.sleep(3)
    info = s.evaluate(JS)
    print("Abschnitts-Titel (separator):", info["sep"])
    print("Feld-Labels:", info["labels"])
    print("Platzhalter:", info["platzhalter"])
    print("Sichtbare Felder:", info["felder"])
    print("--- sichtbarer Text des Tabs ---")
    for zeile in [z for z in info["text"].split("\n") if z.strip()][:20]:
        print("   ", zeile.strip()[:110])
    os.makedirs(ZIEL, exist_ok=True)
    s.screenshot(path=os.path.join(ZIEL, "13_VM_InterneNotizen.png"), full_page=False)
    b.close()
print("Screenshot:", os.path.join(ZIEL, "13_VM_InterneNotizen.png"))
