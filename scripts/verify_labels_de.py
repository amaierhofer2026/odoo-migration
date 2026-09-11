"""Verifikation nach dem Modul-Upgrade: sind die deutschen Begriffe jetzt aktiv?
Prueft Abo-Felder, Abo-Buttons, Modulnamen und die kundenspezifischen Bezeichnungen."""
import http.cookiejar
import json
import os
import re
import urllib.request

ENV = r"C:\Odoo-Test\.env"
TARGETS = [("VM", "https://k001959vsx.ipax.at"), ("LOKAL", "http://localhost:8069")]
FELDER = [("sale.subscription", "partner_id"), ("sale.subscription", "date_start"),
          ("sale.subscription", "date"), ("sale.subscription", "pricelist_id"),
          ("sale.subscription", "template_id"), ("sale.subscription", "recurring_next_date"),
          ("sale.subscription", "recurring_total"), ("sale.subscription", "state"),
          ("sale.subscription.template", "journal_id"), ("sale.subscription.line", "price_unit")]
BUTTONS = ["sale.subscription"]
MODULE = ["itk_crm", "itk_translation", "itk_reports", "itk_subscription",
          "itk_helpdesk_compat", "itk_helpdesk_category_user", "itk_base_setup",
          "itk_product", "itk_valorisierung", "itk_sale_management", "itk_multifactor",
          "itk_projectcategory", "itk_saleorder_lines", "itk_automated_actions",
          "itk_third_party_setup"]
KUNDENSPEZIFISCH = [("Kundenverwaltung", "ir.ui.menu"), ("Kundenverwaltung", "ir.actions.act_window")]

env = {}
for line in open(ENV, encoding="utf-8"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()


def client(url):
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def rpc(service, method, args, kwargs=None):
        payload = {"jsonrpc": "2.0", "method": "call",
                   "params": {"service": service, "method": method, "args": args,
                              "kwargs": kwargs or {}}, "id": 1}
        req = urllib.request.Request(url + "/jsonrpc", data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        with op.open(req, timeout=240) as r:
            out = json.loads(r.read().decode())
        if "error" in out:
            d = out["error"].get("data", {})
            raise RuntimeError("%s | %s" % (d.get("name"), d.get("message")))
        return out["result"]

    uid = rpc("common", "authenticate", [env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"], {}])

    def kw(model, method, args=None, kwargs=None):
        return rpc("object", "execute_kw", [env["ODOO18_DB"], uid, env["ODOO18_PWD"],
                                            model, method, args or [], kwargs or {}])
    return kw


for label, url in TARGETS:
    kw = client(url)
    print("=" * 84)
    print("INSTANZ %s" % label)

    print("\n-- Abo-Feldlabels (de) --")
    for model, feld in FELDER:
        try:
            de = kw(model, "fields_get", [[feld], ["string"]], {"context": {"lang": "de_DE"}})
            en = kw(model, "fields_get", [[feld], ["string"]], {"context": {"lang": "en_US"}})
            d = de[feld]["string"]
            e = en[feld]["string"]
            print("   %-24s %-14s de=%-32r %s" % (model, feld, d, "OK" if d != e else "== en"))
        except Exception as ex:
            print("   %-24s %-14s FEHLER %s" % (model, feld, str(ex)[:60]))

    print("\n-- Auswahlwerte Status (de) --")
    de = kw("sale.subscription", "fields_get", [["state"], ["selection"]], {"context": {"lang": "de_DE"}})
    print("   ", de["state"]["selection"])

    print("\n-- Abo-Buttons im Formular (de) --")
    d = kw("sale.subscription", "get_view", [], {"view_type": "form", "context": {"lang": "de_DE"}})
    b = sorted(set(re.findall(r'string="([^"]{4,45})"', d.get("arch") or "")))
    print("   ", [x for x in b if any(w in x for w in ("Abo", "Kündig", "Beend", "Verläng", "Rechnung",
                                                       "Online", "Verkauf", "Einstell", "Vertrag",
                                                       "Zeilen"))][:12])

    print("\n-- Modulnamen (Apps-Liste) --")
    for name in MODULE:
        r = kw("ir.module.module", "search_read", [[["name", "=", name]]], {"fields": ["shortdesc"]})
        print("   %-30s %s" % (name, r[0]["shortdesc"] if r else "?"))

    print("\n-- Kundenspezifische Bezeichnungen (muessen unveraendert sein) --")
    for begriff, model in KUNDENSPEZIFISCH:
        try:
            ids = kw(model, "search", [[["name", "=", begriff]]], {"limit": 3})
            print("   %-18s in %-22s Treffer: %s" % (begriff, model, len(ids)))
        except Exception as ex:
            print("   %-18s %s FEHLER %s" % (begriff, model, str(ex)[:50]))
    print()
