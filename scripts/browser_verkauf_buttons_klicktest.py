"""Browser-Klicktest Verkauf Teil 3, Schritt 2: Buttons und Smart Buttons (Odoo 18).

Legt einen eigenen Testauftrag an (Status Angebot), klickt die Kopf-Buttons und Smart Buttons im
echten Browser, prueft die Reaktionen und loescht den Testauftrag am Ende wieder. Der Statuswechsel
wird dabei nur als Nebenwirkung des Buttonklicks beruehrt und danach zurueckgesetzt; die
systematische Zustandsanalyse folgt in einem eigenen Schritt.

Aufruf:
    uv run --with playwright python scripts/browser_verkauf_buttons_klicktest.py --instanz lokal
    uv run --with playwright python scripts/browser_verkauf_buttons_klicktest.py --instanz vm
"""
from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from browser_verkauf_menue import lade_env, rpc_client, REPO

VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session121")
SP = {"lang": "de_DE"}
# Buttons, die im Status "Angebot" (draft) sichtbar sein muessen
BUTTONS_DRAFT = ["Per E-Mail versenden", "Bestätigen", "Vorschau", "Stornieren"]
# Smart Buttons: bei Zaehler 0 ausgeblendet
SMART_NAMEN = ["Abonnements", "Rechnungen", "Einkauf"]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["vm", "lokal"], default="vm")
    p.add_argument("--ohne-screenshot", action="store_true")
    p.add_argument("--behalten", action="store_true", help="Testauftrag nicht loeschen")
    a = p.parse_args()

    env = lade_env(os.path.join(REPO, ".env"))
    url = "https://k001959vsx.ipax.at" if a.instanz == "vm" else "http://localhost:8069"
    domain = "k001959vsx.ipax.at" if a.instanz == "vm" else "localhost"
    sid, kw = rpc_client(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])

    partner = kw("res.partner", "search_read", [[("customer_rank", ">", 0)], ["id", "name"]],
                 limit=1, context=SP)
    partner = partner or kw("res.partner", "search_read", [[("is_company", "=", True)], ["id", "name"]],
                            limit=1, context=SP)
    produkt = kw("product.template", "search_read", [[("sale_ok", "=", True)],
                                                     ["id", "name", "list_price"]], limit=1, context=SP)
    if not partner or not produkt:
        raise SystemExit("Kunde oder Produkt fuer den Testauftrag fehlt.")
    kunde, prod = partner[0], produkt[0]
    variante = kw("product.product", "search_read", [[("product_tmpl_id", "=", prod["id"])], ["id"]],
                  limit=1, context=SP)
    if not variante:
        raise SystemExit("Keine Produktvariante zu '%s' gefunden." % prod["name"])
    auftrag = kw("sale.order", "create", [{
        "partner_id": kunde["id"],
        "order_line": [(0, 0, {"product_id": variante[0]["id"],
                               "product_uom_qty": 1, "price_unit": prod["list_price"] or 1})],
    }], context=SP)
    auftrag_id = auftrag[0] if isinstance(auftrag, list) else auftrag
    daten = kw("sale.order", "read", [[auftrag_id], ["name", "state"]], context=SP)[0]
    print("Instanz: %s (%s)" % (a.instanz, url))
    print("Testauftrag: %s (id %s, Status %s, Kunde %s, Produkt %s)"
          % (daten["name"], auftrag_id, daten["state"], kunde["name"], prod["name"]))

    from playwright.sync_api import sync_playwright
    os.makedirs(VZ, exist_ok=True)
    ok = fehler = 0
    js_fehler, rpc_fehler = [], []

    def pruefe(bedingung, text):
        nonlocal ok, fehler
        if bedingung:
            ok += 1
            print("  OK   %s" % text)
        else:
            fehler += 1
            print("  FEHL %s" % text)

    def saeubere(t):
        return re.sub(r"\s+", " ", t or "").strip()

    def standard(seite):
        return saeubere(seite.eval_on_selector(".o_form_statusbar", "e => e ? e.innerText : ''"))

    def kopf_text(seite):
        return saeubere(seite.eval_on_selector(".o_statusbar_buttons", "e => e ? e.innerText : ''"))

    def smart_text(seite):
        return saeubere(seite.eval_on_selector_all(".oe_stat_button", "els => els.map(e => e.innerText).join(' | ')"))

    def schuss(seite, name):
        if not a.ohne_screenshot:
            datei = os.path.join(VZ, name)
            seite.screenshot(path=datei, full_page=True)
            print("       Screenshot: %s" % datei)

    def modal_offen(seite):
        return bool(seite.evaluate("""() => [...document.querySelectorAll('.modal, .o_technical_modal')]
            .some(e => e.getClientRects().length)"""))

    def modal_schliessen(seite):
        """Alle sichtbaren Dialoge ohne Speichern schliessen (aktiv und inaktiv im Stapel)."""
        for _ in range(6):
            if not modal_offen(seite):
                return True
            # bevorzugt den aktiven Dialog schliessen
            for selektor in (".modal:not(.o_inactive_modal) .modal-footer .o_form_button_cancel",
                             ".modal:not(.o_inactive_modal) .modal-footer button[special='cancel']",
                             ".modal:not(.o_inactive_modal) .modal-header .btn-close",
                             ".modal .modal-footer .o_form_button_cancel",
                             ".modal .modal-header .btn-close"):
                knopf = seite.query_selector(selektor)
                if knopf is not None and knopf.bounding_box():
                    try:
                        knopf.click(force=True, timeout=5000)
                    except Exception:
                        knopf.evaluate("e => e.click()")
                    break
            else:
                seite.keyboard.press("Escape")
            seite.wait_for_timeout(1500)
        return not modal_offen(seite)

    def aktiver_dialog_titel(seite):
        return saeubere(seite.evaluate("""() => {
            const m = [...document.querySelectorAll('.modal')]
                .filter(e => e.getClientRects().length && !e.className.includes('o_inactive_modal'));
            return m.length ? (m[m.length-1].querySelector('.modal-title') || {}).innerText || '' : '';
        }"""))

    def aktiven_dialog_schliessen(seite):
        """Nur den obersten (aktiven) Dialog schliessen - weitere Dialoge bleiben erhalten."""
        for selektor in (".modal:not(.o_inactive_modal) .modal-footer .o_form_button_cancel",
                         ".modal:not(.o_inactive_modal) .modal-footer button[special='cancel']",
                         ".modal:not(.o_inactive_modal) .modal-header .btn-close"):
            knopf = seite.query_selector(selektor)
            if knopf is not None and knopf.bounding_box():
                try:
                    knopf.click(force=True, timeout=5000)
                except Exception:
                    knopf.evaluate("e => e.click()")
                seite.wait_for_timeout(1800)
                return True
        seite.keyboard.press("Escape")
        seite.wait_for_timeout(1800)
        return False

    def klick(seite, text, bereich=".o_statusbar_buttons"):
        knopf = seite.query_selector("%s button:has-text('%s')" % (bereich, text))
        if not knopf:
            return False
        knopf.click()
        seite.wait_for_timeout(3000)
        return True

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_verkauf_buttons_%s" % a.instanz),
            channel="chrome", headless=True, viewport={"width": 1800, "height": 1400})
        ctx.add_init_script(
            "window.__errs=[];"
            "window.addEventListener('error', e => window.__errs.push(''+e.message));"
            "window.addEventListener('unhandledrejection', e => window.__errs.push(''+e.reason));"
            "const ce=console.error; console.error=(...x)=>{window.__errs.push(x.map(String).join(' ')); ce(...x);};")
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        seite = ctx.pages[0] if ctx.pages else ctx.new_page()
        seite.on("response", lambda r: rpc_fehler.append("%s %s" % (r.status, r.url))
                 if ("/web/dataset/call_kw" in r.url and r.status >= 400) else None)

        print("\n--- 1. Angebot geoeffnet: sichtbare Buttons und Smart Buttons ---")
        seite.goto("%s/odoo/action-429/%s" % (url, auftrag_id))
        seite.wait_for_selector(".o_form_view", timeout=90000)
        seite.wait_for_timeout(4000)
        pruefe("Angebot" in standard(seite), "Statusleiste zeigt 'Angebot' (%s)" % standard(seite)[:60])
        kt = kopf_text(seite)
        print("       Kopf-Buttons: %s" % kt)
        for b in BUTTONS_DRAFT:
            pruefe(b in kt, "Button '%s' sichtbar" % b)
        st = smart_text(seite)
        print("       Smart Buttons: %s" % (st or "(keine)"))
        pruefe(st == "", "keine Smart Buttons bei Zaehler 0 (wie in Odoo 11)")
        schuss(seite, "06_Buttons_Angebot_%s.png" % a.instanz)

        print("\n--- 2. Drucken-Menue (Zahnrad) ---")
        zahnrad = seite.query_selector(".o_cp_action_menus button, .o_control_panel button[data-menu-xmlid]")
        if zahnrad:
            zahnrad.click()
            seite.wait_for_timeout(1500)
            menue = saeubere(seite.evaluate("""() => {
                const b = [...document.querySelectorAll('.dropdown-menu, .o-dropdown--menu')]
                    .filter(e => e.getClientRects().length);
                return b.length ? b[b.length-1].innerText : '';
            }"""))
            print("       Menue: %s" % menue[:200])
            pruefe("Drucken" in menue, "Zahnradmenue enthaelt 'Drucken'")
            drucken_ok = False
            try:
                seite.locator(".o-dropdown--menu .dropdown-item, .dropdown-menu .dropdown-item",
                              has_text="Drucken").first.click(timeout=8000)
                drucken_ok = True
            except Exception:
                drucken_ok = False
            if drucken_ok:
                seite.wait_for_timeout(2000)
                unter = saeubere(seite.evaluate("""() => {
                    const b = [...document.querySelectorAll('.o-dropdown--menu, .dropdown-menu')]
                        .filter(e => e.getClientRects().length);
                    return b.length ? b.map(x => x.innerText).join(' | ') : '';
                }"""))
                print("       Drucken-Untermenue: %s" % unter[:200])
                pruefe("PDF-Angebot" in unter or "ITK-Angebot" in unter,
                       "Druckmenue bietet die Angebotsberichte an")
            else:
                pruefe(False, "Untermenue 'Drucken' nicht auffindbar")
            seite.keyboard.press("Escape")
            seite.wait_for_timeout(800)
            modal_schliessen(seite)
        else:
            pruefe(False, "Drucken-Menue nicht gefunden")

        print("\n--- 3. 'Per E-Mail versenden' (Assistent, ohne Senden) ---")
        if klick(seite, "Per E-Mail versenden"):
            seite.wait_for_timeout(2500)
            dialog = saeubere(seite.eval_on_selector(".modal-dialog", "e => e ? e.innerText : ''"))
            print("       Dialog: %s" % dialog[:160])
            pruefe(bool(dialog), "Assistent 'Angebot senden' geoeffnet")
            schuss(seite, "07_Button_Email_Assistent_%s.png" % a.instanz)
            pruefe(modal_schliessen(seite), "Assistent ohne Senden geschlossen")
        else:
            pruefe(False, "Button 'Per E-Mail versenden' nicht klickbar")

        print("\n--- 4. 'Vorschau' ---")
        vorher_seiten = len(ctx.pages)
        if klick(seite, "Vorschau"):
            seite.wait_for_timeout(7000)
            ziel = ctx.pages[-1] if len(ctx.pages) > vorher_seiten else seite
            try:
                ziel.wait_for_load_state("domcontentloaded", timeout=45000)
            except Exception:
                pass
            print("       Vorschau-URL: %s" % ziel.url)
            pruefe(any(x in ziel.url for x in ("/my/orders/", "/report/", "sale")),
                   "Vorschau wurde geoeffnet (Kundenvorschau des Angebots)")
            if ziel is not seite:
                ziel.close()
            # zurueck zum Auftragsformular
            seite.goto("%s/odoo/action-429/%s" % (url, auftrag_id))
            seite.wait_for_selector(".o_form_view", timeout=90000)
            seite.wait_for_timeout(3000)
        else:
            pruefe(False, "Button 'Vorschau' nicht klickbar")

        modal_schliessen(seite)
        print("\n--- 5. 'Bestätigen', Sperre/Entsperren und Smart Buttons ---")
        print("       Kopf-Buttons vor dem Klick: %s" % kopf_text(seite))
        if klick(seite, "Bestätigen"):
            seite.wait_for_timeout(4000)
            std = standard(seite)
            print("       Statusleiste: %s" % std[:90])
            pruefe("Verkaufsauftrag" in std or "Auftrag" in std, "Statuswechsel im Formular sichtbar")
            kt2 = kopf_text(seite)
            print("       Kopf-Buttons: %s" % kt2)
            # In dieser Datenbank ist "Bestellungen automatisch sperren" aktiv
            # (sale.group_auto_done_setting): der bestaetigte Auftrag ist gesperrt.
            if "Entsperren" in kt2:
                pruefe(True, "Auftrag nach dem Bestaetigen automatisch gesperrt (Einstellung aktiv)")
                if klick(seite, "Entsperren"):
                    seite.wait_for_timeout(3500)
                    pruefe("Sperren" in kopf_text(seite), "nach 'Entsperren' ist 'Sperren' sichtbar")
            else:
                pruefe("Sperren" in kt2, "Button 'Sperren' nach dem Bestaetigen sichtbar")
            # Smart Buttons gegen die Zaehler pruefen
            zaehler = kw("sale.order", "read", [[auftrag_id],
                                               ["invoice_count", "subscription_count", "purchase_order_count"]],
                         context=SP)[0]
            st2 = smart_text(seite)
            print("       Smart Buttons: %s | Zaehler: %s" % (st2 or "(keine)", zaehler))
            for name, feld in (("Rechnungen", "invoice_count"), ("Abonnements", "subscription_count"),
                               ("Einkauf", "purchase_order_count")):
                if zaehler[feld] > 0:
                    pruefe(name in st2, "Smart Button '%s' sichtbar (Zaehler %s)" % (name, zaehler[feld]))
                else:
                    pruefe(name not in st2, "Smart Button '%s' ausgeblendet (Zaehler 0)" % name)
            schuss(seite, "08_Button_Bestaetigt_%s.png" % a.instanz)
            print("       Hinweis: 'Auf Angebot setzen' gibt es in Odoo 18 nur im Status Storniert; "
                  "das Zuruecksetzen erfolgt daher in Schritt 6 ueber Stornieren.")
        else:
            pruefe(False, "Button 'Bestätigen' nicht klickbar")

        print("\n--- 6. 'Stornieren': Dialog pruefen, dann Storno ueber den Assistenten ---")
        modal_schliessen(seite)
        seite.wait_for_timeout(1000)
        if klick(seite, "Stornieren"):
            seite.wait_for_timeout(3000)
            dialoge = seite.evaluate("""() => [...document.querySelectorAll('.modal')]
                .filter(e => e.getClientRects().length)
                .map(e => (e.className||'').includes('o_inactive_modal') ? 'inaktiv' : 'aktiv')""")
            print("       offene Dialoge: %s" % dialoge)
            # Knoepfe des Storno-Dialogs unabhaengig vom Dialogstapel auflisten
            knoepfe = seite.evaluate("""() => [...document.querySelectorAll('.modal-footer button')]
                .map(e => ({text: e.innerText.trim(), name: e.getAttribute('name')}))""")
            print("       Dialogknoepfe: %s" % knoepfe)
            pruefe(any(k["name"] == "action_cancel" for k in knoepfe),
                   "Bestaetigungsdialog bietet den Knopf 'Stornieren' (name=action_cancel)")
            pruefe(any(k["name"] == "action_send_mail_and_cancel" for k in knoepfe),
                   "Bestaetigungsdialog bietet 'Senden und stornieren' (wird nicht benutzt)")
            if not a.ohne_screenshot:
                datei = os.path.join(VZ, "09_Button_Storno_Dialog_%s.png" % a.instanz)
                seite.screenshot(path=datei, full_page=True)
                print("       Screenshot: %s" % datei)
            # "Verwerfen" ist gefahrlos: der Dialog schliesst ohne Storno
            verworfen = False
            for knopf in seite.query_selector_all(".modal-footer button[special='cancel']"):
                try:
                    knopf.click(force=True, timeout=6000)
                    verworfen = True
                    break
                except Exception:
                    knopf.evaluate("e => e.click()")
                    verworfen = True
                    break
            seite.wait_for_timeout(2500)
            pruefe(verworfen, "Dialog mit 'Verwerfen' geschlossen (kein Storno ausgeloest)")
            stand_v = kw("sale.order", "read", [[auftrag_id], ["state"]], context=SP)[0]["state"]
            pruefe(stand_v == "sale", "Auftrag nach 'Verwerfen' unveraendert (state=%s)" % stand_v)

        # Storno fachlich ausfuehren (ueber den Assistenten, wie ihn der Dialog aufruft)
        w = kw("sale.order.cancel", "create", [{"order_id": auftrag_id}], context=SP)
        kw("sale.order.cancel", "action_cancel", [[w[0] if isinstance(w, list) else w]], context=SP)
        stand3 = kw("sale.order", "read", [[auftrag_id], ["state"]], context=SP)[0]["state"]
        pruefe(stand3 == "cancel", "Auftrag ist storniert (state=%s)" % stand3)
        seite.reload()
        seite.wait_for_selector(".o_form_view", timeout=90000)
        seite.wait_for_timeout(3500)
        print("       Statusleiste nach dem Storno: %s" % standard(seite)[:70])
        if klick(seite, "Auf Angebot setzen"):
            seite.wait_for_timeout(4000)
            stand4 = kw("sale.order", "read", [[auftrag_id], ["state"]], context=SP)[0]["state"]
            pruefe(stand4 == "draft", "'Auf Angebot setzen' (echter Klick) fuehrt auf state=%s" % stand4)
        else:
            pruefe(False, "Button 'Auf Angebot setzen' nicht klickbar")

        js_fehler.extend(seite.evaluate("window.__errs") or [])
        pruefe(not js_fehler, "keine JavaScript-Fehler (%d)" % len(js_fehler))
        pruefe(not rpc_fehler, "keine RPC-Fehler (HTTP >= 400) (%d)" % len(rpc_fehler))
        if js_fehler:
            print("       JS: %s" % js_fehler[:3])
        if rpc_fehler:
            print("       RPC: %s" % rpc_fehler[:3])
        ctx.close()

    if not a.behalten:
        try:
            for versuch in range(2):
                stand = kw("sale.order", "read", [[auftrag_id], ["state", "locked"]], context=SP)
                if not stand:
                    break
                stand = stand[0]
                if stand.get("locked"):
                    kw("sale.order", "action_unlock", [[auftrag_id]], context=SP)
                if stand["state"] != "cancel":
                    # Odoo 18 storniert ueber den Assistenten sale.order.cancel
                    w = kw("sale.order.cancel", "create", [{"order_id": auftrag_id}], context=SP)
                    kw("sale.order.cancel", "action_cancel", [[w[0] if isinstance(w, list) else w]],
                       context=SP)
                try:
                    kw("sale.order", "unlink", [[auftrag_id]], context=SP)
                except Exception:
                    pass
            rest = kw("sale.order", "search_count", [[("id", "=", auftrag_id)]], context=SP)
            pruefe(rest == 0, "Testauftrag wieder geloescht (vorhanden: %d)" % rest)
        except Exception as ausnahme:
            print("  Hinweis: Testauftrag konnte nicht geloescht werden: %s" % str(ausnahme)[:160])

    print("\n%d OK / %d FEHL" % (ok, fehler))
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
