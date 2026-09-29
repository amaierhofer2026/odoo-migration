"""Browser-Klicktest Verkauf Teil 3, Schritt 3: Statuswechsel (Odoo 18).

Legt einen Testauftrag an, durchlaeuft alle Statusuebergaenge mit echten Klicks im Browser,
prueft nach jedem Klick den Zustand per RPC und loescht den Testauftrag am Ende wieder.
Der Versand der E-Mail wird nicht ausgeloest (wuerde Post verschicken); der Zustand
"Angebot gesendet" wird fuer die Sichtbarkeitspruefung per RPC gesetzt.

Aufruf:
    uv run --with playwright python scripts/browser_verkauf_statuswechsel_klicktest.py --instanz lokal
    uv run --with playwright python scripts/browser_verkauf_statuswechsel_klicktest.py --instanz vm
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
MODALS = ("[...document.querySelectorAll('.modal, .o_technical_modal')]"
          ".filter(e => e.getClientRects().length)")


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
    produkt = kw("product.template", "search_read", [[("sale_ok", "=", True)],
                                                     ["id", "name", "list_price"]], limit=1, context=SP)
    variante = kw("product.product", "search_read",
                  [[("product_tmpl_id", "=", produkt[0]["id"])], ["id"]], limit=1, context=SP)
    auftrag = kw("sale.order", "create", [{
        "partner_id": partner[0]["id"],
        "order_line": [(0, 0, {"product_id": variante[0]["id"], "product_uom_qty": 1,
                               "price_unit": produkt[0]["list_price"] or 1})],
    }], context=SP)
    auftrag_id = auftrag[0] if isinstance(auftrag, list) else auftrag

    def stand():
        return kw("sale.order", "read", [[auftrag_id], ["name", "state", "locked", "invoice_status"]],
                  context=SP)[0]

    testauftrag_name = stand()["name"]   # fuer die Bereinigung der Lagerbelege merken
    print("Instanz: %s (%s)" % (a.instanz, url))
    print("Testauftrag: %s (id %s, Status %s)" % (testauftrag_name, auftrag_id, stand()["state"]))

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

    def leiste(seite):
        return saeubere(seite.eval_on_selector(".o_form_statusbar", "e => e ? e.innerText : ''"))

    def stufe(seite):
        return saeubere(seite.evaluate(
            "() => { const e = document.querySelector('.o_arrow_button_current');"
            " return e ? e.innerText : ''; }"))

    def kopf(seite):
        return saeubere(seite.eval_on_selector(".o_statusbar_buttons", "e => e ? e.innerText : ''"))

    def schuss(seite, name):
        if not a.ohne_screenshot:
            datei = os.path.join(VZ, name)
            seite.screenshot(path=datei, full_page=True)
            print("       Screenshot: %s" % datei)

    def dialog_titel(seite, enthaelt=""):
        """Titel des sichtbaren Dialogs, der den Suchbegriff im Titel traegt."""
        js = ("(suche) => { const m = %s; "
              "const t = suche ? m.filter(e => ((e.querySelector('.modal-title') || {}).innerText || '')"
              ".toLowerCase().includes(suche)) : m; "
              "const l = t.length ? t : m; "
              "return l.length ? (l[l.length-1].querySelector('.modal-title') || {}).innerText || '' : ''; }"
              % MODALS)
        return saeubere(seite.evaluate(js, enthaelt))

    def dialog_liste(seite):
        js = ("() => %s.map(e => ((e.querySelector('.modal-title') || {}).innerText || '').trim())" % MODALS)
        return seite.evaluate(js) or []

    def modal_offen(seite):
        return bool(seite.evaluate("() => %s.length" % MODALS))

    def alle_dialoge_schliessen(seite):
        for _ in range(5):
            if not modal_offen(seite):
                return True
            knopf = seite.query_selector(".modal .modal-footer .o_form_button_cancel") or \
                seite.query_selector(".modal .modal-header .btn-close")
            if knopf is not None:
                try:
                    knopf.click(force=True, timeout=5000)
                except Exception:
                    knopf.evaluate("e => e.click()")
            else:
                seite.keyboard.press("Escape")
            seite.wait_for_timeout(1500)
        return not modal_offen(seite)

    def klick(seite, text):
        knopf = seite.query_selector(".o_statusbar_buttons button:has-text('%s')" % text)
        if not knopf:
            return False
        try:
            knopf.click(timeout=10000)
        except Exception:
            knopf.evaluate("e => e.click()")
        seite.wait_for_timeout(3000)
        return True

    def oeffne(seite):
        seite.goto("%s/odoo/action-429/%s" % (url, auftrag_id))
        seite.wait_for_selector(".o_form_view", timeout=90000)
        seite.wait_for_timeout(3500)

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_verkauf_status_%s" % a.instanz),
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

        print("\n--- 1. Ausgangszustand Angebot (draft) ---")
        oeffne(seite)
        kt = kopf(seite)
        print("       Statusleiste: %s" % leiste(seite).replace("\n", " / "))
        print("       Aktive Stufe: %s" % stufe(seite))
        print("       Kopf-Buttons: %s" % kt)
        pruefe(stufe(seite).startswith("Angebot"), "aktive Stufe ist 'Angebot'")
        for b in ("Bestätigen", "Stornieren"):
            pruefe(b in kt, "Button '%s' im Angebot sichtbar" % b)
        for b in ("Sperren", "Entsperren", "Auf Angebot setzen"):
            pruefe(b not in kt, "Button '%s' im Angebot nicht sichtbar" % b)
        schuss(seite, "10_Status_draft_%s.png" % a.instanz)

        print("\n--- 2. Angebot -> Verkaufsauftrag (Klick 'Bestätigen') ---")
        pruefe(klick(seite, "Bestätigen"), "Klick auf 'Bestätigen' ausgefuehrt")
        seite.wait_for_timeout(2500)
        s = stand()
        pruefe(s["state"] == "sale", "Status ist 'sale' (Verkaufsauftrag), war %s" % s["state"])
        pruefe(s["locked"] is True, "Auftrag ist automatisch gesperrt (locked=True)")
        kt = kopf(seite)
        print("       Kopf-Buttons jetzt: %s" % kt)
        pruefe("Entsperren" in kt, "Button 'Entsperren' jetzt sichtbar")
        pruefe("Bestätigen" not in kt, "Button 'Bestätigen' jetzt nicht mehr sichtbar")
        pruefe("Stornieren" not in kt,
               "Button 'Stornieren' im gesperrten Auftrag nicht sichtbar (erst entsperren)")
        schuss(seite, "11_Status_sale_gesperrt_%s.png" % a.instanz)

        print("\n--- 3. Entsperren und Sperren ---")
        pruefe(klick(seite, "Entsperren"), "Klick auf 'Entsperren'")
        seite.wait_for_timeout(2000)
        pruefe(stand()["locked"] is False, "locked ist jetzt False")
        pruefe("Stornieren" in kopf(seite), "Button 'Stornieren' nach dem Entsperren sichtbar")
        pruefe("Sperren" in kopf(seite), "Button 'Sperren' jetzt sichtbar")
        pruefe(klick(seite, "Sperren"), "Klick auf 'Sperren'")
        seite.wait_for_timeout(2000)
        pruefe(stand()["locked"] is True, "locked ist wieder True")
        pruefe("Entsperren" in kopf(seite), "Button 'Entsperren' wieder sichtbar")
        schuss(seite, "12_Status_sperren_%s.png" % a.instanz)

        print("\n--- 4. Verkaufsauftrag -> Storniert (Dialog) ---")
        klick(seite, "Entsperren")
        seite.wait_for_timeout(2000)
        pruefe(klick(seite, "Stornieren"), "Klick auf 'Stornieren' oeffnet den Dialog")
        seite.wait_for_timeout(2000)
        titel = dialog_titel(seite, "stornier")
        print("       Dialog (Storno): %s" % titel)
        print("       Alle offenen Dialoge: %s" % ", ".join(dialog_liste(seite)))
        pruefe("stornier" in titel.lower(), "Bestaetigungsdialog '%s' geoeffnet" % titel)
        schuss(seite, "13_Status_storno_dialog_%s.png" % a.instanz)
        knopf = seite.query_selector(".modal button[name='action_cancel']") or \
            seite.query_selector("button[name='action_cancel']")
        pruefe(knopf is not None, "Dialog bietet den Knopf 'Stornieren' (name=action_cancel)")
        if knopf:
            try:
                knopf.click(timeout=8000)
            except Exception:
                knopf.evaluate("e => e.click()")
            seite.wait_for_timeout(4500)
        s = stand()
        pruefe(s["state"] == "cancel", "Status ist 'cancel' (Storniert), war %s" % s["state"])
        alle_dialoge_schliessen(seite)
        seite.wait_for_timeout(1500)
        kt = kopf(seite)
        print("       Kopf-Buttons jetzt: %s" % kt)
        pruefe("Auf Angebot setzen" in kt, "Button 'Auf Angebot setzen' im Status Storniert sichtbar")
        pruefe("Bestätigen" not in kt and "Stornieren" not in kt,
               "keine Buttons 'Bestätigen'/'Stornieren' im Status Storniert")
        schuss(seite, "14_Status_cancel_%s.png" % a.instanz)

        print("\n--- 5. Storniert -> Angebot (Klick 'Auf Angebot setzen') ---")
        pruefe(klick(seite, "Auf Angebot setzen"), "Klick auf 'Auf Angebot setzen'")
        seite.wait_for_timeout(3000)
        s = stand()
        pruefe(s["state"] == "draft", "Status ist wieder 'draft' (Angebot), war %s" % s["state"])
        pruefe("Bestätigen" in kopf(seite), "Button 'Bestätigen' wieder sichtbar")

        print("\n--- 6. Zustand 'Angebot gesendet' (sent) ---")
        kw("sale.order", "write", [[auftrag_id], {"state": "sent"}], context=SP)
        oeffne(seite)
        print("       Aktive Stufe: %s" % stufe(seite))
        kt = kopf(seite)
        print("       Kopf-Buttons: %s" % kt)
        pruefe(stufe(seite).startswith("Angebot gesendet"), "aktive Stufe ist 'Angebot gesendet'")
        pruefe("Bestätigen" in kt, "Button 'Bestätigen' im Status 'Angebot gesendet' sichtbar")
        pruefe("Stornieren" in kt, "Button 'Stornieren' im Status 'Angebot gesendet' sichtbar")
        pruefe("Auf Angebot setzen" not in kt, "'Auf Angebot setzen' hier nicht sichtbar")
        schuss(seite, "15_Status_sent_%s.png" % a.instanz)

        print("\n--- 7. Angebot gesendet -> Verkaufsauftrag (Klick 'Bestätigen') ---")
        pruefe(klick(seite, "Bestätigen"), "Klick auf 'Bestätigen' aus 'Angebot gesendet'")
        seite.wait_for_timeout(3000)
        s = stand()
        pruefe(s["state"] == "sale", "Status ist 'sale', war %s" % s["state"])
        pruefe(s["locked"] is True, "Auftrag wieder gesperrt (locked=True)")

        js_fehler[:] = seite.evaluate("() => window.__errs") or []
        if not a.behalten:
            # Lagerbelege zuerst entfernen (seit Teil 5 erzeugt ein bestaetigter Auftrag eine
            # Lieferung; ein Auftrag mit Lieferung laesst sich sonst nicht loeschen)
            belege = kw("stock.picking", "search_read",
                        [[("origin", "=", testauftrag_name)], ["name", "state"]], context=SP)
            for b in belege:
                try:
                    if b["state"] not in ("cancel", "done"):
                        kw("stock.picking", "action_cancel", [[b["id"]]], context=SP)
                    kw("stock.picking", "unlink", [[b["id"]]], context=SP)
                except Exception:
                    pass
            if belege:
                print("       Lagerbelege des Testauftrags entfernt: %s"
                      % [b["name"] for b in belege])
            for versuch in range(2):
                s = stand()
                if s["locked"]:
                    kw("sale.order", "write", [[auftrag_id], {"locked": False}], context=SP)
                if stand()["state"] != "cancel":
                    try:
                        ass = kw("sale.order.cancel", "create", [{"order_id": auftrag_id}], context=SP)
                        ass_id = ass[0] if isinstance(ass, list) else ass
                        kw("sale.order.cancel", "action_cancel", [[ass_id]],
                           context={"active_model": "sale.order", "active_ids": [auftrag_id],
                                    "active_id": auftrag_id, "lang": "de_DE"})
                    except Exception as fehlertext:
                        print("       Hinweis Storno: %s" % str(fehlertext)[:120])
                try:
                    kw("sale.order", "unlink", [[auftrag_id]], context=SP)
                    break
                except Exception as fehlertext:
                    print("       Hinweis Loeschen (Versuch %d): %s" % (versuch + 1, str(fehlertext)[:120]))
            # Lagerbelege des Testauftrags mitentfernen (seit Teil 5 erzeugt ein bestaetigter
            # Auftrag eine Lieferung; sie bleibt nach dem Loeschen des Auftrags sonst liegen)
            belege = kw("stock.picking", "search_read",
                        [[("origin", "=", testauftrag_name)], ["name", "state"]], context=SP)
            for b in belege:
                try:
                    if b["state"] not in ("cancel", "done"):
                        kw("stock.picking", "action_cancel", [[b["id"]]], context=SP)
                    kw("stock.picking", "unlink", [[b["id"]]], context=SP)
                except Exception:
                    pass
            if belege:
                print("       Lagerbelege des Testauftrags entfernt: %s"
                      % [b["name"] for b in belege])
            rest = kw("sale.order", "search_count", [[("id", "=", auftrag_id)]], context=SP)
            print("       Testauftrag geloescht: %s (vorhanden: %d)" % (rest == 0, rest))
        ctx.close()

    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    print("JavaScript-Fehler: %d %s" % (len(js_fehler), js_fehler[:3]))
    print("RPC-Fehler: %d %s" % (len(rpc_fehler), rpc_fehler[:3]))
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
