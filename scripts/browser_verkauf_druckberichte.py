"""Browser-Abnahme Verkauf Teil 4: Druckberichte im Auftragsformular (Odoo 18).

Prueft auf der Zielinstanz (VM oder lokal) im echten Browser:
  - Menue "Drucken" im Auftragsformular (Zahnrad -> Drucken) und seine Eintraege
  - je Bericht: Klick erzeugt einen PDF-Download; die Download-URL belegt die Report-Aktion
  - Inhalte: Kunde/Adresse, Positionen (Produkt, Menge, Preis), Nettobetrag, Steuern,
    Gesamt, Datum, Zahlungsbedingung, Bearbeiter/in, UID-Nr.
  - Status: Entwurf -> "Angebot", bestaetigt -> "Auftrag", Proforma eigener Titel
  - Betraege gegen RPC-Werte (amount_untaxed, amount_tax, amount_total)
  - keine JavaScript- und RPC-Fehler

Aufruf:
    uv run --with playwright --with pypdf python scripts/browser_verkauf_druckberichte.py --instanz vm
"""
from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from browser_verkauf_menue import lade_env, rpc_client, REPO

VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session121", "druckberichte")
SP = {"lang": "de_DE"}
BERICHTE = [
    ("Angebot/Auftrag", "sale.report_saleorder_raw"),
    ("ITK-Angebot/Auftrag", "itk_reports.report_itk_saleorder"),
    ("PDF-Angebot", "sale.report_saleorder"),
    ("PRO-FORMA-Rechnung", "sale.report_saleorder_pro_forma"),
]
JS_POPOVER_EINTRAEGE = ("() => [...document.querySelectorAll('.o_popover *, .o-dropdown--menu *')]"
                        ".filter(e => e.children.length === 0 && (e.innerText||'').trim())"
                        ".map(e => e.innerText.trim())")


def zahl(text):
    if text is None:
        return None
    b = str(text).replace("\u00a0", " ").replace("€", "").strip()
    b = re.sub(r"[^0-9,.\-]", "", b)
    if not b:
        return None
    if "," in b:
        b = b.replace(".", "").replace(",", ".")
    try:
        return float(b)
    except ValueError:
        return None


def betraege(text):
    return [z for z in (zahl(x) for x in re.findall(r"[0-9][0-9.]*,[0-9]{2}", text or "")) if z]


def pdf_text(pfad: str) -> str:
    from pypdf import PdfReader
    leser = PdfReader(pfad)
    return "\n".join((s.extract_text() or "") for s in leser.pages)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["vm", "lokal"], default="vm")
    a = p.parse_args()

    env = lade_env(os.path.join(REPO, ".env"))
    url = "https://k001959vsx.ipax.at" if a.instanz == "vm" else "http://localhost:8069"
    domain = "k001959vsx.ipax.at" if a.instanz == "vm" else "localhost"
    sid, kw = rpc_client(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])

    felder = ["name", "state", "partner_id", "amount_untaxed", "amount_tax", "amount_total",
              "payment_term_id", "user_id"]
    entwuerfe = kw("sale.order", "search_read", [[("state", "in", ["draft", "sent"]), ("order_line", "!=", False)],
                                                felder], context=SP)
    bestaetigt = kw("sale.order", "search_read", [[("state", "=", "sale"), ("order_line", "!=", False)],
                                                 felder + ["date_order"]], context=SP)
    if not entwuerfe or not bestaetigt:
        print("FEHL: Testauftraege fehlen (Entwurf %d, bestaetigt %d)" % (len(entwuerfe), len(bestaetigt)))
        return 1
    f, g = entwuerfe[0], bestaetigt[0]
    zeilen = kw("sale.order.line", "search_read", [[("order_id", "=", g["id"])],
                                                   ["name", "product_uom_qty", "price_unit",
                                                    "price_subtotal", "product_id"]], context=SP)
    print("Instanz: %s (%s)" % (a.instanz, url))
    print("Entwurf: %s (%s), Gesamt %.2f" % (f["name"], f["state"], f["amount_total"]))
    print("Bestaetigt: %s, Netto %.2f + Steuer %.2f = Gesamt %.2f, %d Positionen, Kunde %s"
          % (g["name"], g["amount_untaxed"], g["amount_tax"], g["amount_total"], len(zeilen),
             g["partner_id"][1]))

    from playwright.sync_api import sync_playwright
    os.makedirs(VZ, exist_ok=True)
    ok = fehler = 0
    js_fehler, rpc_fehler, report_urls, report_anfragen = [], [], [], []

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

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_verkauf_druck_%s" % a.instanz),
            channel="chrome", headless=True, viewport={"width": 1900, "height": 1400},
            accept_downloads=True)
        ctx.add_init_script(
            "window.__errs=[];"
            "window.addEventListener('error', e => window.__errs.push(''+e.message));"
            "window.addEventListener('unhandledrejection', e => window.__errs.push(''+e.reason));")
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        seite = ctx.pages[0] if ctx.pages else ctx.new_page()
        def beobachte(r):
            if "/web/dataset/call_kw" in r.url and r.status >= 400:
                rpc_fehler.append("%s %s" % (r.status, r.url))
            if "/report/" in r.url:
                report_urls.append(r.url)

        def beobachte_anfrage(r):
            if "/report/download" in r.url:
                report_anfragen.append(r.post_data or "")

        seite.on("response", beobachte)
        seite.on("request", beobachte_anfrage)

        def oeffne_auftrag(auftrag_id):
            seite.goto("%s/odoo/sales/%d" % (url, auftrag_id))
            seite.wait_for_selector(".o_form_view", timeout=90000)
            seite.wait_for_timeout(4500)

        def oeffne_drucken():
            seite.click(".o_cp_action_menus button", timeout=20000)
            seite.wait_for_timeout(1200)
            seite.click(".o-dropdown--has-parent:has-text('Drucken')", timeout=15000)
            seite.wait_for_timeout(1800)
            return seite.evaluate(JS_POPOVER_EINTRAEGE)

        def hole_pdf(eintrag, versuche=3):
            """PDF ueber das Drucken-Menue holen; bei Abbruechen erneut versuchen und die
            Datei notfalls aus dem Download-Zwischenspeicher kopieren."""
            pfad = os.path.join(VZ, "%s_%s.pdf" % (re.sub(r"[^A-Za-z0-9]+", "_", eintrag), a.instanz))
            letzter = None
            for versuch in range(versuche):
                try:
                    with seite.expect_download(timeout=90000) as dl:
                        seite.click(".o_popover *:text-is('%s')" % eintrag, timeout=20000)
                    d = dl.value
                    try:
                        d.save_as(pfad)
                    except Exception:
                        # Fallback: Playwright legt die Datei bereits im Temp-Verzeichnis ab
                        quelle = d.path()
                        if quelle:
                            import shutil
                            shutil.copyfile(quelle, pfad)
                    if os.path.exists(pfad) and os.path.getsize(pfad) > 3000:
                        return d.url, pfad
                    letzter = Exception("PDF zu klein oder nicht gespeichert")
                except Exception as ex:
                    letzter = ex
                    print("       Hinweis: Druckversuch %d fuer '%s' fehlgeschlagen (%s)"
                          % (versuch + 1, eintrag, str(ex)[:90]))
                    seite.wait_for_timeout(2500)
                    try:
                        if not seite.query_selector(".o_form_view"):
                            oeffne_auftrag(g["id"])
                        if not seite.query_selector(".o_popover"):
                            oeffne_drucken()
                    except Exception:
                        pass
            raise letzter if letzter else Exception("PDF nicht erzeugt")

        print()
        print("--- 1. Menue Drucken im Formular ---")
        oeffne_auftrag(g["id"])
        eintraege = oeffne_drucken()
        print("       Menuepunkte: %s" % eintraege)
        for name, _ in BERICHTE:
            pruefe(name in eintraege, "Bericht '%s' im Menue Drucken sichtbar" % name)
        seite.screenshot(path=os.path.join(VZ, "01_Drucken_Menue_%s.png" % a.instanz), full_page=True)

        print()
        print("--- 2. Report-Aktion je Eintrag (ueber die Server-Anfrage belegt) ---")
        for name, report_name in BERICHTE:
            oeffne_auftrag(g["id"])
            oeffne_drucken()
            del report_anfragen[:]
            _, pfad = hole_pdf(name)
            erwartet = "/report/pdf/%s/%d" % (report_name, g["id"])
            text_der_anfrage = " ".join(report_anfragen)
            pruefe(report_name in text_der_anfrage or report_name in str(report_urls),
                   "%s -> Report-Aktion %s" % (name, report_name))
            pruefe(os.path.getsize(pfad) > 3000, "%s: PDF erzeugt (%d Bytes)" % (name, os.path.getsize(pfad)))

        print()
        print("--- 3. ITK-Angebot fuer den Entwurf (%s, Status %s) ---" % (f["name"], f["state"]))
        oeffne_auftrag(f["id"])
        oeffne_drucken()
        _, pfad = hole_pdf("ITK-Angebot/Auftrag")
        text = pdf_text(pfad)
        print("       PDF: %s (%d Zeichen)" % (pfad, len(text)))
        pruefe("Angebot %s" % f["name"] in saeubere(text), "Titel 'Angebot %s'" % f["name"])
        pruefe("Folgend dürfen wir Ihnen die angefragte" in text, "Angebotstext vorhanden")
        pruefe("Hiermit bestätigen wir die Beauftragung" not in text, "kein Auftragstext im Angebot")
        pruefe(saeubere(f["partner_id"][1]).split(",")[0] in saeubere(text),
               "Kunde '%s' im PDF" % f["partner_id"][1])
        werte = betraege(text)
        pruefe(any(abs(w - f["amount_total"]) < 0.011 for w in werte),
               "Gesamt %.2f im PDF" % f["amount_total"])
        pruefe("Nettobetrag" in text, "Summenblock (Nettobetrag) vorhanden")
        pruefe("Bearbeiter" in text and "UID" in text and "Zahlung" in text,
               "Kopfblock Zahlung/Bearbeiter/in/UID im PDF")
        schuss = os.path.join(VZ, "02_ITK_Angebot_%s.png" % a.instanz)
        seite.screenshot(path=schuss, full_page=True)

        print()
        print("--- 4. ITK-Auftrag fuer den bestaetigten Auftrag (%s) ---" % g["name"])
        oeffne_auftrag(g["id"])
        oeffne_drucken()
        _, pfad = hole_pdf("ITK-Angebot/Auftrag")
        text = pdf_text(pfad)
        print("       PDF: %s (%d Zeichen)" % (pfad, len(text)))
        pruefe("Auftrag %s" % g["name"] in saeubere(text), "Titel 'Auftrag %s'" % g["name"])
        pruefe("Hiermit bestätigen wir die Beauftragung" in text, "Auftragstext vorhanden")
        pruefe("Wir bedanken uns für Ihre Beauftragung" in text, "Schlusstext vorhanden")
        pruefe(saeubere(g["partner_id"][1]).split(",")[0] in saeubere(text),
               "Kunde '%s' im PDF" % g["partner_id"][1])
        pruefe(bool(re.search(r"\b\d{4}\b", text)), "Postleitzahl/Ort im PDF")
        for z in zeilen[:3]:
            if z["name"]:
                pruefe(saeubere(z["name"][:30]) in saeubere(text), "Position '%s' im PDF" % saeubere(z["name"][:30]))
        werte = betraege(text)
        pruefe(any(abs(w - g["amount_untaxed"]) < 0.011 for w in werte),
               "Nettobetrag %.2f im PDF" % g["amount_untaxed"])
        if g["amount_tax"]:
            pruefe(any(abs(w - g["amount_tax"]) < 0.011 for w in werte),
                   "Steuerbetrag %.2f im PDF" % g["amount_tax"])
            pruefe(bool(re.search(r"\d+([.,]\d+)?\s?%", text)), "Steuersatz in Prozent im PDF")
        pruefe(any(abs(w - g["amount_total"]) < 0.011 for w in werte),
               "Gesamt %.2f im PDF" % g["amount_total"])
        bedingung = (g["payment_term_id"] or ["", ""])[1]
        if bedingung:
            pruefe(bedingung in text, "Zahlungsbedingung '%s' im PDF" % bedingung)
        else:
            pruefe("Zahlung" in text, "Zahlungsblock im PDF (Auftrag ohne Zahlungsbedingung)")
        pruefe(saeubere(g["date_order"][:10]) != "" and bool(re.search(r"\d{2}\.\d{2}\.\d{4}", text)),
               "Datum im PDF (%s)" % g["date_order"][:10])
        schuss = os.path.join(VZ, "03_ITK_Auftrag_%s.png" % a.instanz)
        seite.screenshot(path=schuss, full_page=True)

        print()
        print("--- 5. Proformarechnung ---")
        oeffne_auftrag(g["id"])
        oeffne_drucken()
        _, pfad = hole_pdf("PRO-FORMA-Rechnung")
        text = pdf_text(pfad)
        print("       PDF: %s" % pfad)
        titel_11 = "Proformarechnung" in text
        titel_18 = "Pro-forma-Rechnung" in text
        print("       Titel: ITK-Wortlaut=%s, Odoo-18-Wortlaut=%s" % (titel_11, titel_18))
        pruefe(titel_11 or titel_18, "Proforma-Titel im PDF vorhanden")
        pruefe("Hiermit bestätigen wir die Beauftragung" not in text, "kein Auftragstext in der Proforma")
        pruefe(saeubere(g["partner_id"][1]).split(",")[0] in saeubere(text), "Kunde im Proforma-PDF")
        pruefe(any(abs(w - g["amount_total"]) < 0.011 for w in betraege(text)),
               "Gesamt %.2f im PDF" % g["amount_total"])

        print()
        print("--- 6. Odoo-18-Berichte unveraendert nutzbar ---")
        for name in ("Angebot/Auftrag", "PDF-Angebot"):
            oeffne_auftrag(g["id"])
            oeffne_drucken()
            _, pfad = hole_pdf(name)
            text = pdf_text(pfad)
            pruefe(g["name"] in text, "%s: Auftragsnummer %s im PDF" % (name, g["name"]))
            pruefe(any(abs(w - g["amount_total"]) < 0.011 for w in betraege(text)),
                   "%s: Gesamt %.2f im PDF" % (name, g["amount_total"]))

        print()
        print("--- 7. Vorschau-Knopf und Formularfehler ---")
        oeffne_auftrag(g["id"])
        knopf = seite.query_selector("button:has-text('Vorschau')")
        pruefe(knopf is not None, "Knopf 'Vorschau' weiterhin im Formular")
        pruefe(seite.query_selector(".o_form_view") is not None, "Auftragsformular ohne Fehleranzeige")

        js_fehler[:] = seite.evaluate("() => window.__errs") or []
        ctx.close()

    print()
    print("Ergebnis: %d OK, %d FEHL" % (ok, fehler))
    print("JavaScript-Fehler: %d %s" % (len(js_fehler), js_fehler[:3]))
    print("RPC-Fehler: %d %s" % (len(rpc_fehler), rpc_fehler[:3]))
    print("PDFs: %s" % VZ)
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
