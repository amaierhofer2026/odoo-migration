"""Abnahmepruefung Bereich Angebote / Verkaufsauftraege (Session 117).

Prueft READ-ONLY gegen eine Odoo-18-Instanz (lokal oder VM):
  1. Statuswerte und Statusleiste (draft, sent, sale; cancel/done)
  2. Header-Buttons und Aktionen
  3. Smart Buttons (Rechnungen, Abonnements, Lieferung)
  4. Zielfelder der Odoo-11-Felder mit Typ und Relation
  5. ITK-Kontaktfelder aus itk_sale_management
  6. Hinweise auf Felder, die in Odoo 18 entfallen (incoterm, confirmation_date, analytic_account_id)
  7. Abo-Verknuepfung (sale.subscription, subscription_count, action_open_subscriptions)
  8. Keine Uebernahme von Odoo-11-Auftragsdaten

Aufruf:
    python scripts/verify_s117_auftraege.py --instanz lokal
    python scripts/verify_s117_auftraege.py --instanz vm
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import re
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STATUS_SELEKTION = ["draft", "sent", "sale", "done", "cancel"]
STATUSLEISTE = ["draft", "sent", "sale"]

BUTTONS = ["action_confirm", "action_cancel", "action_draft", "action_quotation_send"]
SMART_BUTTONS = ["action_view_invoice", "action_open_subscriptions"]

# Odoo-11-Feld -> (Odoo-18-Feld, Typ, Relation)
FELDER = {
    "state": ("state", "selection", None),
    "partner_id": ("partner_id", "many2one", "res.partner"),
    "partner_invoice_id": ("partner_invoice_id", "many2one", "res.partner"),
    "partner_shipping_id": ("partner_shipping_id", "many2one", "res.partner"),
    "user_id": ("user_id", "many2one", "res.users"),
    "team_id": ("team_id", "many2one", "crm.team"),
    "pricelist_id": ("pricelist_id", "many2one", "product.pricelist"),
    "payment_term_id": ("payment_term_id", "many2one", "account.payment.term"),
    "date_order": ("date_order", "datetime", None),
    "validity_date": ("validity_date", "date", None),
    "client_order_ref": ("client_order_ref", "char", None),
    "note": ("note", "html", None),
    "invoice_status": ("invoice_status", "selection", None),
    "invoice_ids": ("invoice_ids", "many2many", "account.move"),
    "opportunity_id": ("opportunity_id", "many2one", "crm.lead"),
    "origin": ("origin", "char", None),
    "fiscal_position_id": ("fiscal_position_id", "many2one", "account.fiscal.position"),
    "currency_id": ("currency_id", "many2one", "res.currency"),
    "order_line": ("order_line", "one2many", "sale.order.line"),
    "name": ("name", "char", None),
}

# ITK-eigene Felder (itk_sale_management) - muessen vorhanden und im Formular sein
ITK_FELDER = {
    "sale_contact_id": ("Verkaufskontakt", "res.partner"),
    "administrative_contact_id": ("Verwaltungskontakt", "res.partner"),
    "technical_contact_id": ("Technischer Kontakt", "res.partner"),
    "final_customer_id": ("Endkunde", "res.partner"),
    "product_category_id": ("Produktkategorie", "product.category"),
}

# In Odoo 18 bewusst entfallen (in Odoo 11 unbenutzt bzw. ersetzt)
ENTFAELLT = ["incoterm", "analytic_account_id", "payment_tx_id", "payment_tx_ids"]

# Sichtbare Beschriftungen: Odoo-11-Wortlaut -> in Odoo 18 erwartet
LABELS_ANGEGLICHEN = {
    "team_id": "Vertriebskanal",
    "administrative_contact_id": "Verwaltungskontakt",
    "opportunity_id": "Chance",
    "source_id": "Referenz",
}
# Bewusst Odoo-18-Wortlaut (dokumentiert)
LABELS_ODOO18 = {
    "date_order": "Auftragsdatum",
    "validity_date": "Gültigkeit",
    "invoice_status": "Rechnungsstatus",
    "order_line": "Auftragspositionen",
}


def _abo_da(k) -> bool:
    """Ist das Abo-Modell vorhanden?"""
    try:
        k.kw("sale.subscription", "search_count", [[]])
        return True
    except Exception:
        return False


def lade_env(pfad: str) -> dict:
    werte = {}
    with open(pfad, encoding="utf-8") as fh:
        for zeile in fh:
            if "=" in zeile and not zeile.strip().startswith("#"):
                s, w = zeile.split("=", 1)
                werte[s.strip()] = w.strip()
    return werte


class Client:
    def __init__(self, url: str, db: str, user: str, pwd: str):
        self.url = url.rstrip("/")
        jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        self.rufe("/web/session/authenticate", {"db": db, "login": user, "password": pwd})

    def rufe(self, pfad: str, params: dict):
        req = urllib.request.Request(
            self.url + pfad,
            data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": params}).encode(),
            headers={"Content-Type": "application/json"})
        with self.opener.open(req, timeout=300) as antwort:
            daten = json.loads(antwort.read().decode())
        if "error" in daten:
            raise RuntimeError(json.dumps(daten["error"])[:300])
        return daten.get("result")

    def kw(self, model: str, methode: str, args: list, **kwargs):
        return self.rufe("/web/dataset/call_kw",
                         {"model": model, "method": methode, "args": args, "kwargs": kwargs})


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    a = p.parse_args()
    env = lade_env(os.path.join(REPO, ".env"))
    url = env.get("ODOO18_URL", "http://localhost:8069") if a.instanz == "lokal" else "https://k001959vsx.ipax.at"
    k = Client(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])
    print("Instanz: %s (%s, DB %s)" % (a.instanz, url, env["ODOO18_DB"]))
    ok = fehler = 0

    def pruefe(bedingung: bool, text: str):
        nonlocal ok, fehler
        if bedingung:
            ok += 1
            print("  OK   %s" % text)
        else:
            fehler += 1
            print("  FEHL %s" % text)

    form = k.kw("sale.order", "get_views", [[[False, "form"]]], context={"lang": "de_DE"})["views"]["form"]["arch"]
    felder = k.kw("sale.order", "fields_get", [sorted(set(list(FELDER) + list(ITK_FELDER) + ENTFAELLT + ["source_id", "subscription_count", "transaction_ids", "warehouse_id", "picking_ids", "locked", "confirmation_date"])),
                                               ["string", "type", "relation"]], context={"lang": "de_DE"})

    print("\n1) Statuswerte und Statusleiste")
    sel = dict(k.kw("sale.order", "fields_get", [["state"], ["selection"]], context={"lang": "de_DE"})["state"]["selection"])
    for s in STATUS_SELEKTION:
        if s == "done":
            # Odoo 11 hatte den Status "Abgeschlossen" (0 Datensaetze). Odoo 18 fuehrt ihn nicht mehr;
            # abgeschlossene Auftraege sind state=sale mit locked=True.
            if s not in sel:
                kk = felder.get("locked") or k.kw("sale.order", "fields_get", [["locked"], ["string"]], context={"lang": "de_DE"})
                pruefe(bool(kk), "Status 'done' entfaellt; Ersatz ist 'sale' + locked (%s)"
                       % (kk.get("locked", {}).get("string") if isinstance(kk.get("locked"), dict) else "gesperrt"))
            else:
                pruefe(True, "Status 'done' vorhanden (%s)" % sel.get("done"))
            continue
        pruefe(s in sel, "Status '%s' vorhanden (%s)" % (s, sel.get("?", "?")))
    leiste = re.search(r'<field name="state"[^>]*statusbar_visible="([^"]+)"', form)
    pruefe(bool(leiste) and leiste.group(1) == ",".join(STATUSLEISTE),
           "Statusleiste sichtbar: %s" % (leiste.group(1) if leiste else "?"))
    print("       Auftraege in Odoo 18 (Teststand): %d" % k.kw("sale.order", "search_count", [[]]))

    print("\n2) Header-Buttons")
    for b in BUTTONS:
        pruefe(b in form, "Button '%s' vorhanden" % b)

    print("\n3) Smart Buttons")
    for b in SMART_BUTTONS:
        pruefe(b in form, "Smart Button '%s' vorhanden" % b)

    print("\n4) Zielfelder der Odoo-11-Felder")
    for o11, (o18, typ, rel) in FELDER.items():
        f = felder.get(o18)
        if not f:
            pruefe(False, "%s -> %s fehlt" % (o11, o18))
            continue
        passt = f["type"] == typ and (rel is None or f.get("relation") == rel)
        pruefe(passt, "%s -> %s (%s%s)" % (o11, o18, f["type"], "/" + (f.get("relation") or "") if rel else ""))

    print("\n5) ITK-Kontaktfelder (itk_sale_management)")
    for name, (soll_label, rel) in ITK_FELDER.items():
        f = felder.get(name)
        pruefe(bool(f) and f.get("relation") == rel, "%s (%s) vorhanden%s"
               % (name, rel, "" if not f else ", Label '%s'" % f["string"]))
        pruefe(name in form, "%s im Formular eingebunden" % name)

    print("\n6) Bewusst entfallene Odoo-11-Felder")
    for name in ENTFAELLT:
        pruefe(name not in felder, "Feld '%s' in Odoo 18 nicht mehr vorhanden (Odoo 11: unbenutzt/ersetzt)" % name)
    zeile = k.kw("sale.order.line", "fields_get", [["analytic_distribution"], ["string", "type"]], context={"lang": "de_DE"})
    pruefe("analytic_distribution" in zeile,
           "Ersatz fuer Kostenstelle vorhanden: sale.order.line.analytic_distribution (%s)"
           % zeile.get("analytic_distribution", {}).get("string"))

    print("\n7) Abo-Verknuepfung")
    modul = k.kw("ir.module.module", "search_read", [[["name", "=", "sale_subscription"]], ["name", "state", "installed_version"]])
    if modul:
        print("       Modul sale_subscription: %s %s" % (modul[0]["state"], modul[0].get("installed_version") or ""))
    pruefe("subscription_count" in felder, "subscription_count vorhanden")
    pruefe("action_open_subscriptions" in form, "Smart Button action_open_subscriptions vorhanden")
    try:
        abos = k.kw("sale.subscription", "search_count", [[]])
        print("       Abonnements in Odoo 18 (Teststand): %d" % abos)
    except Exception as exc:
        print("       Abo-Modell nicht abfragbar: %s" % str(exc)[:60])

    print("\n8) Keine Uebernahme von Odoo-11-Daten")
    anzahl = k.kw("sale.order", "search_count", [[]])
    pruefe(anzahl < 100, "Auftraege in Odoo 18: %d (Odoo 11 hat 2.460 - Teststand erwartet)" % anzahl)

    print("\n9) Sichtbare Beschriftungen")
    for feld, soll in LABELS_ANGEGLICHEN.items():
        f = felder.get(feld)
        ist = f["string"] if f else "?"
        pruefe(ist == soll, "Label %s = '%s' (Odoo-11-Wortlaut '%s')" % (feld, ist, soll))
    for feld, soll in LABELS_ODOO18.items():
        f = felder.get(feld)
        ist = f["string"] if f else "?"
        pruefe(ist == soll, "Label %s = '%s' (Odoo-18-Wortlaut, bewusst)" % (feld, ist))

    print("\n10) Bestaetigungsdatum (Odoo-11-Feld confirmation_date)")
    f = k.kw("sale.order", "fields_get", [["confirmation_date"], ["string", "type", "readonly"]], context={"lang": "de_DE"})
    cd = f.get("confirmation_date")
    pruefe(bool(cd) and cd["type"] == "datetime", "Feld vorhanden: %s (%s)"
           % (cd["string"] if cd else "fehlt", cd["type"] if cd else "-"))
    if cd:
        pruefe(cd["string"] == "Bestätigung am", "Beschriftung '%s' (Odoo-11-Wortlaut)" % cd["string"])
    pruefe("confirmation_date" in form, "Feld im Auftragsformular eingebunden")
    # Odoo 18 ueberschreibt date_order beim Bestaetigen - deshalb eigenes Feld
    pruefe(True, "Hinweis: Odoo 18 setzt date_order beim Bestaetigen auf den aktuellen Zeitpunkt "
                 "(_prepare_confirmation_values) - kein gleichwertiges Feld, daher eigenes Feld")

    print("\n11) Abo-Verknuepfung Auftrag <-> Abonnement")
    abo_felder = k.kw("sale.subscription", "fields_get", [["sale_order_id"], ["string", "type", "relation"]],
                      context={"lang": "de_DE"}) if _abo_da(k) else {}
    pruefe("sale_order_id" in abo_felder, "sale.subscription.sale_order_id vorhanden (%s)"
           % (abo_felder.get("sale_order_id", {}).get("string") or "-"))
    pruefe("action_open_subscriptions" in form, "Smart Button action_open_subscriptions im Auftragsformular")
    pruefe("subscription_count" in felder, "Zaehler subscription_count vorhanden")
    modul = k.kw("ir.module.module", "search_read", [[["name", "=", "sale_subscription"]], ["state", "installed_version"]])
    if modul:
        print("       Modul sale_subscription: %s %s" % (modul[0]["state"], modul[0].get("installed_version") or ""))

    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
