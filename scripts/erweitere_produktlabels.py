"""Erweitert die Label-Skripte um die Produktfelder (verkaufbare/einkaufbare Produkte).

Einmalig ausgefuehrt; danach sind apply_abrechnung_labels.py und check_abrechnung_labels.py
um die Produkt-Beschriftungen erweitert.
"""
import io
import re

APPLY = r"C:/Odoo-Test/scripts/apply_abrechnung_labels.py"
CHECK = r"C:/Odoo-Test/scripts/check_abrechnung_labels.py"

# Feldname -> Odoo-11-Wortlaut (fuer beide Produktmodelle, sofern dort vorhanden)
PRODUKT_LABELS = [
    "barcode|Strichcode",
    "categ_id|Interne Kategorie",
    "cost_method|Kostenmethode",
    "description_picking|Beschreibung der Kommisionierung",
    "expense_policy|Spesen weiter verrechnen",
    "invoice_policy|Fakturierungsregel",
    "is_multi_factor_product|To multiply by Factor(per 1000)",
    "nbr_reordering_rules|Meldebestände",
    "orderpoint_ids|Meldebestandsregeln",
    "outgoing_qty|Ausgehend",
    "packaging_ids|Produktverpackungen",
    "partner_ref|Kunden Ref",
    "product_type_id|Product-Type",
    "product_variant_count|# Produkt Varianten",
    "property_account_income_id|Erlöskonto",
    "property_stock_inventory|Lagerort Bestandsaufnahme",
    "property_stock_production|Fertigungort (virtuelles Lager)",
    "purchase_line_warn|Bestellposition",
    "purchase_ok|Kann eingekauft werden",
    "qty_available|Bestandsmenge",
    "sale_delay|Auslieferungszeit",
    "sale_line_warn|Auftragsposition",
    "sale_line_warn_msg|Mitteilung für Auftragszeile",
    "sale_ok|Kann verkauft werden",
    "sales_count|# Verkäufe",
    "sequence|Nummernfolge",
    "service_type|Dienstleistungsverfolgung",
    "supplier_taxes_id|Steuern (Einkauf)",
    "taxes_id|Steuern (Verkauf)",
    "uom_id|Mengeneinheit",
    "uom_po_id|Einkauf ME",
    "valuation|Bewertung",
    "warehouse_id|Lager",
    "lst_price|Verkaufspreis",
    "is_product_variant|Ist eine Produktvariante",
]
# Odoo-11-Wortlaut je Modell unterschiedlich
NUR_TEMPLATE = ["virtual_available|Geplante Bestandsmenge"]
NUR_PRODUCT = ["virtual_available|Prognostizierter Bestand"]

# Bewusst abweichend (Odoo-11-Beschriftung wird nicht uebernommen)
BEGRUENDET = {
    "activity_state": "Odoo-11-Beschriftung 'Bundesland' ist falsch (Aktivitaetsstatus)",
    "activity_summary": "Standard-Aktivitaetsfeld (Chatter)",
    "activity_user_id": "Standard-Aktivitaetsfeld (Chatter)",
    "message_follower_ids": "Standard-Chatterfeld (mail)",
    "message_is_follower": "Standard-Chatterfeld (mail)",
    "message_partner_ids": "Standard-Chatterfeld (mail)",
    "website_message_ids": "Standard-Chatterfeld (website)",
    "rating_ids": "technisches Bewertungsfeld",
    "write_date": "technisches Feld",
    "write_uid": "technisches Feld",
    "service_tracking": "Odoo-18-Feld hat andere Auswahl/Bedeutung (Aufgabe/Projekt)",
    "cost_currency_id": "Odoo-11-Beschriftung ist ein englischer Rest ('Cost Currency')",
    "purchase_line_warn_msg": "Odoo-11-Text enthaelt Schreibfehler ('Bachricht')",
}

# ---------------------------------------------------------------------------------------------
apply_text = io.open(APPLY, encoding="utf-8").read()
apply_neu = ""
for eintrag in PRODUKT_LABELS:
    feld, text = eintrag.split("|")
    for modell, extra in (("product.template", NUR_TEMPLATE), ("product.product", NUR_PRODUCT)):
        apply_neu += '    ("%s", "%s"): "%s",\n' % (modell, feld, text)
    for modell, extra in (("product.template", NUR_TEMPLATE), ("product.product", NUR_PRODUCT)):
        for zusatz in extra:
            zfeld, ztext = zusatz.split("|")
            if zfeld == feld and (modell, zfeld) not in apply_neu:
                apply_neu += '    ("%s", "%s"): "%s",\n' % (modell, zfeld, ztext)
# virtuelle Bestandsmengen je Modell unterschiedlich benannt
apply_neu += '    ("product.template", "virtual_available"): "Geplante Bestandsmenge",\n'
apply_neu += '    ("product.product", "virtual_available"): "Prognostizierter Bestand",\n'
# Duplikat entfernen (template/product wurden oben schon erzeugt)
apply_neu = "".join(
    dict((zeile, None) for zeile in apply_neu.splitlines(True)).keys())

if "Produkte (Odoo-11-Wortlaut)" not in apply_text:
    kopf = "    # --- Produkte (Odoo-11-Wortlaut, verkaufbare/einkaufbare Produkte) ---\n"
    text = apply_text.replace(
        '    ("account.move.line", "analytic_distribution"): "Kostenstelle",\n}',
        '    ("account.move.line", "analytic_distribution"): "Kostenstelle",\n' + kopf + apply_neu + "}")
    if text == apply_text:
        raise SystemExit("Anker in apply_abrechnung_labels.py nicht gefunden")
    io.open(APPLY, "w", encoding="utf-8", newline="\n").write(text)
    print("apply_abrechnung_labels.py erweitert: %d Zeilen" % len(apply_neu.splitlines()))
else:
    print("apply_abrechnung_labels.py enthaelt die Produkteintraege bereits")

# ---------------------------------------------------------------------------------------------
check_text = io.open(CHECK, encoding="utf-8").read()
paare = PRODUKT_LABELS + NUR_TEMPLATE + NUR_PRODUCT + \
    ["%s|" % k for k in BEGRUENDET if not k.startswith(("activity", "message", "rating", "write",
                                                        "service_tracking", "cost_currency",
                                                        "purchase_line_warn_msg"))]
mapping_neu = ""
gesehen = set()
for eintrag in paare:
    feld = eintrag.split("|")[0]
    for modell in ("product.template", "product.product"):
        if (modell, feld) in gesehen:
            continue
        gesehen.add((modell, feld))
        mapping_neu += '    ("%s", "%s", "%s", "%s", ""),\n' % (modell, feld, modell, feld)
for feld in ("activity_state", "activity_summary", "activity_user_id", "message_follower_ids",
             "message_is_follower", "message_partner_ids", "website_message_ids", "rating_ids",
             "write_date", "write_uid", "service_tracking", "cost_currency_id",
             "purchase_line_warn_msg"):
    for modell in ("product.template", "product.product"):
        gesehen.add((modell, feld))
        mapping_neu += '    ("%s", "%s", "%s", "%s", "bewusst abweichend"),\n' % (modell, feld, modell, feld)
begruendet_neu = ""
for feld, grund in BEGRUENDET.items():
    for modell in ("product.template", "product.product"):
        begruendet_neu += '    ("%s", "%s"): "%s",\n' % (modell, feld, grund)

if "Produkte (verkaufbare" not in check_text:
    t = check_text.replace(
        '    ("account.invoice.line", "account_analytic_id", "account.move.line", "analytic_distribution", "anderes Modell"),\n]',
        '    ("account.invoice.line", "account_analytic_id", "account.move.line", "analytic_distribution", "anderes Modell"),\n'
        '    # --- Produkte (verkaufbare/einkaufbare Produkte) ---\n' + mapping_neu + "]", 1)
    if t == check_text:
        raise SystemExit("MAPPING-Anker nicht gefunden")
    t2 = t.replace(
        '    ("account.move", "name"): "Odoo-11-Feld name = Begruendung/Beschreibung, nicht die Belegnummer (Regel in Teil 5)",\n}',
        '    ("account.move", "name"): "Odoo-11-Feld name = Begruendung/Beschreibung, nicht die Belegnummer (Regel in Teil 5)",\n'
        '    # Produkte\n' + begruendet_neu + "}", 1)
    if t2 == t:
        raise SystemExit("BEGRUENDET-Anker nicht gefunden")
    io.open(CHECK, "w", encoding="utf-8", newline="\n").write(t2)
    print("check_abrechnung_labels.py erweitert: %d Zuordnungen, %d Begruendungen"
          % (len(mapping_neu.splitlines()), len(begruendet_neu.splitlines())))
else:
    print("check_abrechnung_labels.py enthaelt die Produkteintraege bereits")
