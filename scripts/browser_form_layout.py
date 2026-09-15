#!/usr/bin/env python3
"""Echter Browser-/Layoutvergleich des geoeffneten Kontaktformulars (Session 95).

Rendert die Kontakt-Detailansicht in einem echten Browser (Playwright/Chromium),
liest die SICHTBAREN Feldbezeichnungen mit ihrer Position aus (x/y in CSS-Pixeln),
dazu Gruppenueberschriften, Notebook-Tabs (je Tab die sichtbaren Felder) und die
Smart-Button-Leiste, und legt Screenshots + eine JSON-Datei ab.

Damit laesst sich pruefen, was Anna einfordert: sichtbar? richtige Position?
gleiche fachliche Funktion? gleiche Bedienlogik? - nicht nur "irgendwo vorhanden".

Aufruf:
    uv run --with playwright python scripts/browser_form_layout.py \
        --instanz lokal --partner 69 --out %TEMP%/layout_lokal

    --instanz lokal|vm  -> Odoo 18 (Zugangsdaten aus C:\\Odoo-Test\\.env)
    --instanz prod      -> Odoo 11 Prod (Zugangsdaten aus %TEMP%/o11_creds.txt:
                           Zeile 1 = URL, Zeile 2 = DB, Zeile 3 = Login, Zeile 4 = Passwort)

Ausgabe: <out>.json, <out>_oben.png, <out>_<tab>.png
"""
import argparse, json, os, re, sys, tempfile, time

EXTRAKT = r"""
() => {
  const sichtbar = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const pos = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width)]; };
  const txt = (e) => (e.innerText || e.textContent || "").replace(/\s+/g, " ").trim();

  const ergebnis = { titel: document.title, url: location.href, felder: [], gruppen: [], tabs: [], stats: [], knoepfe: [] };

  document.querySelectorAll(".oe_stat_button").forEach((e) => {
    if (sichtbar(e)) ergebnis.stats.push({ text: txt(e), pos: pos(e) });
  });

  document.querySelectorAll(".o_notebook .nav-link").forEach((e, i) => {
    ergebnis.tabs.push({ index: i, text: txt(e), aktiv: e.classList.contains("active"), pos: pos(e) });
  });

  document.querySelectorAll(".o_group_name, .o_horizontal_separator").forEach((e) => {
    if (sichtbar(e) && txt(e)) ergebnis.gruppen.push({ text: txt(e), pos: pos(e) });
  });

  // Zeilenbehaelter (Odoo 11: td, Odoo 18: .o_cell) -> Label<->Feld zuordnen
  const zeile = (el) => { const c = el.closest(".o_cell, td, .o_wrap_field"); return c ? c.parentElement : null; };
  const labels = [...document.querySelectorAll("label.o_form_label")].filter(sichtbar);
  document.querySelectorAll(".o_field_widget[name]").forEach((e) => {
    if (!sichtbar(e)) return;
    const name = e.getAttribute("name");
    const z = zeile(e);
    let lbl = null;
    for (const l of labels) { if (zeile(l) === z) { lbl = l; break; } }
    ergebnis.felder.push({
      name: name,
      label: lbl ? txt(lbl) : "",
      pos: pos(e),
      readonly: e.classList.contains("o_readonly_modifier"),
      wert: txt(e).slice(0, 40),
    });
  });

  // Tabs auch fuer Odoo 11 (ul.nav-tabs > li > a)
  if (!ergebnis.tabs.length) {
    document.querySelectorAll("ul.nav-tabs > li > a, .o_notebook ul.nav > li > a").forEach((e, i) => {
      ergebnis.tabs.push({ index: i, text: txt(e), aktiv: (e.parentElement || {}).classList ? e.parentElement.classList.contains("active") : false, pos: pos(e) });
    });
  }
  // "Mehr"-Menue der Smart Buttons aufklappen und Inhalt mitnehmen
  const mehr = document.querySelector(".oe_stat_button .o_dropdown_toggler_btn, .o_button_box .dropdown-toggle");
  if (mehr) {
    try {
      mehr.click();
      document.querySelectorAll(".dropdown-menu.show .dropdown-item, .dropdown-menu.show .o_menu_item").forEach((e) => {
        if (txt(e)) ergebnis.knoepfe.push({ text: "[Mehr] " + txt(e), pos: pos(e) });
      });
    } catch (err) {}
  }
  document.querySelectorAll(".o_form_button_save, .o_form_button_cancel, .o_statusbar_status button, .btn-primary, .btn-secondary").forEach((e) => {
    if (sichtbar(e) && txt(e)) ergebnis.knoepfe.push({ text: txt(e), pos: pos(e) });
  });
  return ergebnis;
}
"""


def creds(instanz):
    env = {}
    for zeile in open(r"C:\Odoo-Test\.env", encoding="utf-8"):
        if "=" in zeile and not zeile.strip().startswith("#"):
            k, v = zeile.split("=", 1)
            env[k.strip()] = v.strip()
    if instanz == "prod":
        return {"url": env["ODOO11_URL"], "db": env["ODOO11_DB"], "user": env["ODOO11_USER"], "pwd": env["ODOO11_PWD"]}
    url = "http://localhost:8069" if instanz == "lokal" else "https://k001959vsx.ipax.at"
    return {"url": url, "db": env["ODOO18_DB"], "user": env["ODOO18_USER"], "pwd": env["ODOO18_PWD"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", required=True, choices=["lokal", "vm", "prod"])
    ap.add_argument("--partner", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--url", help="Basis-URL ueberschreiben (z. B. Hostname statt IP)")
    ap.add_argument("--tab-klicks", action="store_true", help="jeden Tab anklicken und Felder je Tab erfassen")
    a = ap.parse_args()
    c = creds(a.instanz)
    if a.url:
        c["url"] = a.url.rstrip("/")

    from playwright.sync_api import sync_playwright
    # Bereits installiertes Chrome verwenden (kein Browser-Download, eigenes Temp-Profil
    # -> Chrome fragt nicht nach "Allow remote debugging").
    chrome_pfade = [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]
    start = {}
    for pfad in chrome_pfade:
        if os.path.exists(pfad):
            start["executable_path"] = pfad
            break
    bericht = {"instanz": a.instanz, "partner": a.partner, "basis": {}, "je_tab": {}}
    with sync_playwright() as p:
        b = p.chromium.launch(**start)
        seite = b.new_page(viewport={"width": 1680, "height": 1050}, ignore_https_errors=True)
        seite.goto(c["url"] + "/web/login", wait_until="domcontentloaded", timeout=60000)
        seite.fill("input[name='login']", c["user"])
        seite.fill("input[name='password']", c["pwd"])
        seite.click(".oe_login_form button[type=submit]")
        seite.wait_for_load_state("load", timeout=60000)
        time.sleep(4)
        print("  angemeldet:", seite.title())

        if a.instanz == "prod":
            ziel = "%s/web?db=%s#id=%s&model=res.partner&view_type=form" % (c["url"], c["db"], a.partner)
        else:
            ziel = c["url"].rstrip("/") + "/odoo/contacts/" + str(a.partner)
        seite.goto(ziel, wait_until="load", timeout=90000)
        seite.wait_for_selector(".o_form_view", timeout=90000)
        time.sleep(5)
        print("  Formular:", seite.title(), "|", seite.url)

        seite.screenshot(path=a.out + "_oben.png", full_page=False)
        seite.screenshot(path=a.out + "_ganz.png", full_page=True)

        bericht["basis"] = seite.evaluate(EXTRAKT)
        print("  Felder sichtbar oben: %d | Gruppen: %d | Tabs: %d | Smart-Buttons: %d"
              % (len(bericht["basis"]["felder"]), len(bericht["basis"]["gruppen"]),
                 len(bericht["basis"]["tabs"]), len(bericht["basis"]["stats"])))

        if a.tab_klicks:
            for t in list(bericht["basis"]["tabs"]):
                try:
                    seite.click(".o_notebook .nav-link >> nth=%d" % t["index"], timeout=15000)
                    time.sleep(2)
                    d = seite.evaluate(EXTRAKT)
                    bericht["je_tab"][t["text"]] = [{"name": f["name"], "label": f["label"], "pos": f["pos"]} for f in d["felder"]]
                    seite.screenshot(path="%s_tab%d.png" % (a.out, t["index"]), full_page=False)
                    print("     Tab %-28s -> %d Felder" % (t["text"][:28], len(bericht["je_tab"][t["text"]])))
                except Exception as e:
                    print("     Tab %s nicht klickbar: %s" % (t["text"], str(e)[:80]))
        b.close()

    with open(a.out + ".json", "w", encoding="utf-8") as f:
        json.dump(bericht, f, ensure_ascii=False, indent=1)
    print("  Dateien:", a.out + ".json", a.out + "_oben.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
