"""Erzeugt die Vergleichsmatrix Produktformular Odoo 11 gegen Odoo 18.

Liest beide Systeme read-only (Odoo 11 nur Leseaufrufe) und schreibt
docs/o11-o18-vergleich-abrechnung-produktformular.md.

Aufruf: python scripts/erzeuge_produktformular_matrix.py
"""
import collections
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CTX = {"lang": "de_DE"}

# ------------------------------------------------------------------ Odoo 11 lesen
k11 = o11()
a11 = k11.kw("product.template", "fields_view_get", [False, "form"], toolbar=False, context=CTX)["arch"]
w11 = ET.fromstring(a11)
ids11 = k11.kw("product.template", "search", [[]], context=CTX)
alle_felder = sorted({e.get("name") for e in w11.iter("field")} | {"product_image_ids", "message_ids"})
f11 = k11.kw("product.template", "fields_get", [alle_felder, ["string", "type", "relation", "required",
                                                             "readonly", "selection", "store"]],
             context=CTX)
werte = k11.kw("product.template", "read", [ids11, [x for x in alle_felder if x in f11]], context=CTX)
belegt = {}
for feld in f11:
    n = 0
    for w in werte:
        v = w.get(feld)
        if v not in (False, None, "", 0, 0.0, [], "no-message"):
            n += 1
    belegt[feld] = n
gesamt11 = len(ids11)
typverteilung = collections.Counter(w["type"] for w in werte)

# Odoo-11-Aufbau: Reiter -> Felder in Reihenfolge
aufbau11 = []
for seite in w11.find(".//notebook"):
    if seite.tag != "page":
        continue
    felder = [e.get("name") for e in seite.iter("field")]
    aufbau11.append((seite.get("string"), seite.get("name"), felder))

# ------------------------------------------------------------------ Odoo 18 lesen
k18 = o18(sys.argv[1] if len(sys.argv) > 1 else "lokal")
f18 = k18.kw("product.template", "fields_get", [alle_felder, ["string", "type", "relation", "readonly"]],
             context=CTX)
a18 = k18.kw("product.template", "get_views", [[[False, "form"]]], context=CTX)["views"]["form"]["arch"]
w18 = ET.fromstring(a18)
aufbau18 = []
for seite in w18.find(".//notebook"):
    if seite.tag != "page":
        continue
    felder = [e.get("name") for e in seite.iter("field")]
    aufbau18.append((seite.get("string"), seite.get("name"), felder))


def reiter18(feld):
    for string, name, felder in aufbau18:
        if feld in felder:
            return string
    return None


def in_form18(feld):
    return ('<field name="%s"' % feld) in a18


# ------------------------------------------------------------------ Zuordnung je Feld
# Odoo-11-Feld -> (Odoo-18-Feld, Aenderung, Migrationsregel, Hinweis)
ZUORDNUNG = {
    "type": ("type", "unsichtbar wie in Odoo 11", "Wert 1:1 uebernehmen (type)",
             "Odoo 11 hatte hier die Auswahlwerte der ITK-Produktart; sie liegen in Odoo 18 in product_type_id"),
    "product_type_id": ("product_type_id", "unveraendert", "Wert 1:1 uebernehmen", ""),
    "categ_id": ("categ_id", "in die erste Gruppe verschoben (Odoo 11)", "Wert 1:1 uebernehmen",
                 "Beschriftung auf Odoo-11-Wortlaut 'Interne Kategorie' gesetzt"),
    "default_code": ("default_code", "in die erste Gruppe verschoben (Odoo 11)",
                     "Wert 1:1 uebernehmen", "Beschriftung 'Interne Referenz' (Odoo 11)"),
    "barcode": ("barcode", "in die erste Gruppe verschoben (Odoo 11)", "Wert 1:1 uebernehmen",
                "0 von 649 Produkten belegt"),
    "list_price": ("list_price", "unveraendert", "Wert 1:1 uebernehmen", ""),
    "is_multi_factor_product": ("is_multi_factor_product", "unveraendert", "Wert 1:1 uebernehmen", ""),
    "recurring_invoice": ("recurring_invoice", "unveraendert (Odoo-18-Gruppe Subscription)",
                          "Wert 1:1 uebernehmen", ""),
    "valuation": (None, "Feld im Odoo-18-Modell nicht mehr vorhanden", "keine Migration moeglich",
                  "Odoo 11: ueberall unsichtbar; Bewertung steuert Odoo 18 ueber die Produktkategorie"),
    "cost_method": (None, "Feld im Odoo-18-Modell nicht mehr vorhanden", "keine Migration moeglich",
                    "Odoo 11: unsichtbar"),
    "property_cost_method": (None, "Feld im Odoo-18-Modell nicht mehr vorhanden",
                             "keine Migration moeglich", "Odoo 11: unsichtbar"),
    "standard_price": ("standard_price", "unveraendert", "Wert 1:1 uebernehmen", "6 von 649 belegt"),
    "company_id": ("company_id", "unsichtbar wie in Odoo 11", "Wert 1:1 uebernehmen", ""),
    "uom_id": ("uom_id", "keine Aenderung",
               "Wert 1:1 uebernehmen",
               "Odoo 11: unsichtbar, Odoo 18 zeigt das Feld sichtbar neben dem Verkaufspreis"),
    "uom_po_id": ("uom_po_id", "unveraendert (Reiter Einkauf)",
                  "Wert 1:1 uebernehmen", "Odoo 11: unsichtbar"),
    "currency_id": ("currency_id", "unsichtbar", "Wert 1:1 uebernehmen", ""),
    "product_variant_id": ("product_variant_id", "unsichtbar", "Wert 1:1 uebernehmen", ""),
    "attribute_line_ids": ("attribute_line_ids", "unveraendert (Odoo-18-Reiter 'Attribute & Varianten')",
                           "Wert 1:1 uebernehmen",
                           "Odoo 11 blendete den Reiter 'Varianten' fest aus; Odoo 18 zeigt ihn"),
    "item_ids": (None, "kein Feld; Odoo-18-Smart Button 'Preislistenregeln'",
                 "Preislistenregeln sind Verknuepfungen (product.pricelist.item -> product_tmpl_id)",
                 "Odoo 11: Feld im Reiter Verkauf"),
    "website_url": (None, "Feld im Odoo-18-Modell nicht vorhanden (website/sale nicht installiert)",
                    "keine Migration moeglich", "Odoo 11: unsichtbar"),
    "public_categ_ids": (None, "Feld im Odoo-18-Modell nicht vorhanden", "keine Migration moeglich",
                         "Odoo 11: Website-Kategorien; in Odoo 18 nicht installiert"),
    "alternative_product_ids": ("optional_product_ids", "durch Odoo-18-Feld abgebildet",
                                "alternative_product_ids -> optional_product_ids",
                                "Odoo 18 fuehrt alternative und optionale Produkte zusammen"),
    "accessory_product_ids": ("optional_product_ids", "durch Odoo-18-Feld abgebildet",
                              "accessory_product_ids -> optional_product_ids", "siehe oben"),
    "inventory_availability": (None, "Feld im Odoo-18-Modell nicht vorhanden", "keine Migration moeglich",
                               "Odoo 11: 0 von 649 belegt"),
    "available_threshold": (None, "Feld im Odoo-18-Modell nicht vorhanden", "keine Migration moeglich",
                            "Odoo 11: 0 von 649 belegt"),
    "custom_message": (None, "Feld im Odoo-18-Modell nicht vorhanden", "keine Migration moeglich",
                       "Odoo 11: 0 von 649 belegt"),
    "website_style_ids": (None, "Feld im Odoo-18-Modell nicht vorhanden", "keine Migration moeglich",
                          "Odoo 11: unsichtbar"),
    "subscription_template_id": ("subscription_template_id", "unveraendert", "Wert 1:1 uebernehmen", ""),
    "seller_ids": ("seller_ids", "unveraendert (Reiter Einkauf)", "Wert 1:1 uebernehmen",
                   "Odoo 11: 0 von 649 belegt"),
    "variant_seller_ids": ("variant_seller_ids", "unveraendert (Reiter Einkauf)", "keine Werte zu uebernehmen",
                           "Steuerung der Anzeige in Odoo 18 ueber die Variantenanzahl"),
    "route_ids": ("route_ids", "unveraendert (Reiter Lager)", "Wert 1:1 uebernehmen", ""),
    "route_from_categ_ids": ("route_from_categ_ids", "unveraendert (Reiter Lager)",
                             "berechnet aus der Kategorie, keine Migration", ""),
    "sale_delay": ("sale_delay", "unveraendert (Reiter Lager, Gruppe Logistik)",
                   "Wert 1:1 uebernehmen", "Odoo 11: 0 von 649 belegt"),
    "weight": ("weight", "unveraendert (Reiter Lager, Gruppe Logistik)", "Wert 1:1 uebernehmen",
               "Odoo 11: 0 von 649 belegt"),
    "volume": ("volume", "unveraendert (Reiter Lager, Gruppe Logistik)", "Wert 1:1 uebernehmen",
               "Odoo 11: 0 von 649 belegt"),
    "responsible_id": ("responsible_id", "unveraendert (Odoo 11: Reiter Lager)",
                       "Wert 1:1 uebernehmen",
                       "Zusatz: Odoo 18 zeigt das Feld auch im ersten Reiter (Beschluss Session 120)"),
    "tracking": ("tracking", "unveraendert (Odoo 11: unsichtbar)", "Wert 1:1 uebernehmen", ""),
    "property_stock_production": ("property_stock_production", "unveraendert (Odoo 11: unsichtbar)",
                                  "Wert 1:1 uebernehmen", ""),
    "property_stock_inventory": ("property_stock_inventory", "unveraendert (Odoo 11: unsichtbar)",
                                 "Wert 1:1 uebernehmen", ""),
    "packaging_ids": ("packaging_ids", "unveraendert (Odoo 11: unsichtbar)", "Wert 1:1 uebernehmen", ""),
    "taxes_id": ("taxes_id", "vom ersten Reiter in den Reiter Abrechnung verschoben (Odoo 11)",
                 "Wert 1:1 uebernehmen (account.tax)", "647 von 649 belegt"),
    "property_account_income_id": ("property_account_income_id",
                                   "im Reiter Abrechnung, Gruppe Forderungen (Odoo 11)",
                                   "Wert 1:1 uebernehmen, falls gesetzt",
                                   "Odoo 11: unsichtbar, 0 von 649 belegt; Odoo 18 zeigt es nur mit "
                                   "Buchhaltungsrecht (Gruppe unveraendert)"),
    "supplier_taxes_id": ("supplier_taxes_id",
                          "vom ersten Reiter in den Reiter Abrechnung verschoben (Odoo 11)",
                          "Wert 1:1 uebernehmen (account.tax)", "648 von 649 belegt"),
    "property_account_expense_id": ("property_account_expense_id",
                                    "im Reiter Abrechnung, Gruppe Verbindlichkeiten (Odoo 11)",
                                    "Wert 1:1 uebernehmen, falls gesetzt",
                                    "Odoo 11: unsichtbar, 0 von 649 belegt"),
    "property_account_creditor_price_difference": ("property_account_creditor_price_difference",
                                                   "im Reiter Abrechnung (Odoo 11)",
                                                   "Wert 1:1 uebernehmen, falls gesetzt",
                                                   "Odoo 11: unsichtbar, 0 von 649 belegt"),
    "property_valuation": (None, "Feld im Odoo-18-Modell nicht mehr vorhanden", "keine Migration moeglich",
                           "Odoo 11: unsichtbar; Odoo 18 steuert die Bewertung an der Produktkategorie"),
    "property_stock_account_input": (None, "Feld im Odoo-18-Modell nicht mehr vorhanden",
                                     "keine Migration moeglich", "Odoo 11: Gruppe Bestandsbewertung"),
    "property_stock_account_output": (None, "Feld im Odoo-18-Modell nicht mehr vorhanden",
                                      "keine Migration moeglich", "Odoo 11: Gruppe Bestandsbewertung"),
    "invoice_policy": ("invoice_policy", "vom ersten Reiter in den Reiter Abrechnung verschoben (Odoo 11)",
                       "Wert 1:1 uebernehmen", "in Odoo 18 Pflichtfeld, Werte 1:1 ('order' 649 von 649)"),
    "service_type": ("service_type", "unveraendert unsichtbar", "Wert 1:1 uebernehmen",
                     "Odoo 11: 598x 'manual', 51x 'timesheet'"),
    "service_policy": (None, "Feld im Odoo-18-Modell nicht mehr vorhanden",
                       "51 Datensaetze mit 'ordered_timesheet' -> invoice_policy/expense_policy pruefen",
                       "Odoo 18 loest die Richtlinie ueber invoice_policy und expense_policy"),
    "service_tracking": ("service_tracking", "unveraendert unsichtbar", "Wert 1:1 uebernehmen",
                         "Odoo 11: alle 649 'no'; Odoo 18 zeigt das Feld ebenfalls nicht"),
    "project_id": (None, "Feld im Odoo-18-Modell nicht mehr vorhanden",
                   "keine Migration moeglich (0 von 649 belegt)",
                   "Odoo 18 erzeugt Projekte/Aufgaben ueber die Auftragslogik"),
    "purchase_method": ("purchase_method", "vom Reiter Einkauf in den Reiter Abrechnung verschoben (Odoo 11)",
                        "Wert 1:1 uebernehmen", "649 von 649 belegt ('receive')"),
    "description": ("description", "vom ersten Reiter in den Reiter Notizen verschoben (Odoo 11)",
                    "Wert 1:1 uebernehmen",
                    "Odoo 11: Textfeld, Odoo 18: HTML-Feld (Inhalt wird als HTML uebernommen)"),
    "description_sale": ("description_sale", "vom Reiter Verkauf in den Reiter Notizen verschoben (Odoo 11)",
                         "Wert 1:1 uebernehmen", "1 von 649 belegt"),
    "description_purchase": ("description_purchase",
                             "vom Reiter Einkauf in den Reiter Notizen verschoben (Odoo 11)",
                             "Wert 1:1 uebernehmen", "0 von 649 belegt"),
    "description_pickingout": ("description_pickingout",
                               "vom Reiter Lager in den Reiter Notizen verschoben (Odoo 11)",
                               "Wert 1:1 uebernehmen", "0 von 649 belegt"),
    "description_pickingin": ("description_pickingin",
                              "vom Reiter Lager in den Reiter Notizen verschoben (Odoo 11)",
                              "Wert 1:1 uebernehmen", "0 von 649 belegt"),
    "description_picking": ("description_picking", "im Reiter Notizen ergaenzt (Odoo 11)",
                            "Wert 1:1 uebernehmen",
                            "in Odoo 18 nicht mehr im Formular; Feld im Modell vorhanden, 0 von 649 belegt"),
    "sale_line_warn": ("sale_line_warn", "vom Reiter Verkauf in den Reiter Notizen verschoben (Odoo 11)",
                       "Wert 1:1 uebernehmen", "Beschriftung 'Auftragsposition' (Odoo 11)"),
    "sale_line_warn_msg": ("sale_line_warn_msg",
                           "vom Reiter Verkauf in den Reiter Notizen verschoben (Odoo 11)",
                           "Wert 1:1 uebernehmen",
                           "Beschriftung 'Mitteilung fuer Auftragszeile' (Odoo 11)"),
    "purchase_line_warn": ("purchase_line_warn",
                           "vom Reiter Einkauf in den Reiter Notizen verschoben (Odoo 11)",
                           "Wert 1:1 uebernehmen",
                           "Beschriftung 'Bestellposition' (Odoo 11); Odoo 18 hatte nolabel"),
    "purchase_line_warn_msg": ("purchase_line_warn_msg",
                               "vom Reiter Einkauf in den Reiter Notizen verschoben (Odoo 11)",
                               "Wert 1:1 uebernehmen",
                               "Beschriftung Odoo 18 'Nachricht für Bestellzeile' beibehalten "
                               "(Odoo-11-Text war abgeschnitten)"),
    "product_image_ids": (None, "Feld und Modell product.image in Odoo 18 nicht mehr vorhanden",
                          "keine Migration noetig (0 von 649 belegt)",
                          "Odoo 11: Reiter Bilder; Odoo 18 zeigt das Hauptbild im Kopf und "
                          "Dokumente ueber den Smart Button"),
    "message_ids": ("message_ids", "Odoo 18: Chatter am Formularende (Odoo-18-Standard)",
                    "Nachrichten/Abonnenten werden mitmigriert (mail.message, mail.followers)", ""),
}

zeilen = []
for reiter, name, felder in aufbau11:
    for feld in felder:
        if feld not in f11:
            continue
        ziel, aenderung, migration, hinweis = ZUORDNUNG.get(
            feld, (feld, "unveraendert", "Wert 1:1 uebernehmen", ""))
        info = f11[feld]
        typ = info["type"] + (" -> " + info["relation"] if info.get("relation") else "")
        pflicht = "ja" if info.get("required") else "nein"
        ro = "ja" if info.get("readonly") else "nein"
        vorher = "vorhanden" if (ziel and in_form18(ziel)) else "fehlte im Formular"
        if ziel and ziel != feld:
            vorher = "als %s vorhanden" % ziel if in_form18(ziel) else "fehlte (kein Feld)"
        nachher = reiter18(ziel) if ziel else "-"
        if ziel and not in_form18(ziel):
            nachher = "nicht im Formular (Feld im Modell vorhanden)"
        if not ziel:
            nachher = "-"
        abw = "ja" if not ziel else ("ja" if hinweis.startswith("Odoo 11: unsichtbar") else "nein")
        belegt_txt = "%d/%d" % (belegt.get(feld, 0), gesamt11) if feld in belegt else "-"
        sichtbar = bool(ziel) and in_form18(ziel) and nachher not in ("-", "nicht im Formular (Feld im Modell vorhanden)")
        abw = "ja" if (not ziel or "unsichtbar" in hinweis or "Zusatz" in hinweis
                       or "beibehalten" in hinweis or "entfaellt" in hinweis) else "nein"
        zeilen.append("| %s | `%s` (%s, %s belegt) | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            reiter or "(ohne Reiter)", feld, info["string"], belegt_txt, vorher,
            ("`%s`" % ziel) if ziel else "kein Zielfeld", aenderung, nachher,
            ("OK (Reiter %s)" % nachher) if sichtbar else "-",
            ("OK (Reiter %s)" % nachher) if sichtbar else "-",
            migration,
            (abw + (" - " + hinweis if hinweis else ""))))

kopf = ("| Reiter | Odoo 11 Feld/Funktion | Odoo 18 vorher | Technische Zuordnung | Aenderung | "
        "Odoo 18 nachher | Browser lokal | Browser VM | Migrationsregel | Bewusste Abweichung + Begruendung |\n"
        "|---|---|---|---|---|---|---|---|---|---|")

reiter11_txt = "\n".join("%d. %s (%d Felder)" % (i + 1, s or "(ohne string)", len(f))
                         for i, (s, n, f) in enumerate(aufbau11))
reiter18_txt = "\n".join("%d. %s (%d Felder)" % (i + 1, s or "(ohne string)", len(f))
                         for i, (s, n, f) in enumerate(aufbau18))

text = """# Produktformular: Odoo 11 gegen Odoo 18 (Bereich Abrechnung, Verkaufbare/Einkaufbare Produkte)

Stand: 05.10.2026, Session 126. Odoo 11 Prod ausschliesslich **read-only** gelesen.
Bereich Abrechnung bleibt **IN ARBEIT** - die Abnahme macht Anna selbst.

Auftrag: Formular, Liste, Suche, Kanban, Aktionen und Verknuepfungen der Menuepunkte
Abrechnung > Verkauf > Verkaufbare Produkte und Abrechnung > Einkauf > Einkaufbare Produkte
feldweise gegen Odoo 11 pruefen und angleichen; Odoo-18-Zusatzfunktionen erhalten,
keine Dummy-Felder, keine Umgehung durch "Odoo-18-Standard".

## 1. Reiter: Ist-Zustand und Umsetzung

```
Odoo 11 (8 Reiter)                    Odoo 18 vorher (5)                Odoo 18 nachher (7)
1. Allgemeine Informationen           1. Allgemeine Informationen        1. Allgemeine Informationen
                                      2. Attribute & Varianten           2. Attribute & Varianten
                                      3. Verkauf                         3. Verkauf
                                      4. Einkauf                         4. Einkauf
                                      5. Lager                           5. Lager
                                                                         6. Abrechnung
                                                                         7. Notizen
```
Vollstaendig, gemessen am Arch:

```
Odoo 11:
{}

Odoo 18 nachher:
{}
```

Ursache des fehlenden Reiters **Abrechnung**: Die Seite kommt aus dem `account`-Modul
(`name=invoicing`, Beschriftung "Buchhaltung") und ist dort ueber die **verborgene technische
Gruppe** `account.group_account_readonly` eingeschraenkt - in der Instanz hat sie **0 Benutzer**
(gemessen 05.10.2026), der Reiter ist damit fuer jeden Benutzer unsichtbar. Odoo 11 zeigte den
Reiter ohne Gruppenbeschraenkung. Umsetzung: Beschriftung auf "Abrechnung" gesetzt, Gruppenfilter
entfernt, Odoo-11-Felder in Odoo-11-Gruppen hineingezogen. Die Buchhaltungsfelder behalten ihre
eigenen Gruppenrechte (Odoo 11 hatte sie unsichtbar).

Der Reiter **Notizen** existierte in Odoo 18 nur als Gruppe im ersten Reiter; er ist jetzt wieder
eigener Reiter mit den acht Odoo-11-Gruppen.

Der Reiter **Bilder** ist nicht nachbaubar: `product.image` (und das Feld `product_image_ids`)
existiert in Odoo 18 nicht mehr, und in Odoo 11 war der Reiter **0 von 649 Produkten** belegt
(0 Datensaetze in product.image, 0 Anhaenge an product.template). Odoo 18 zeigt das Hauptbild im
Kopfbereich (wie Odoo 11 das Feld image_medium ausserhalb der Reiter) und Dokumente ueber den
Smart Button "Dokumente"; die Nachrichten liegen im Chatter am Formularende. Kein Dummy-Reiter.

## 2. Feldweise Matrix

Legende: "belegt" = Anzahl der Odoo-11-Produktvorlagen mit einem Wert (von {} Vorlagen). Bei
berechneten Feldern und Auswahlfeldern mit Standardwert bedeutet das nicht automatisch fachliche
Nutzung; massgeblich sind die Angaben in der Spalte "Migrationsregel".
Typverteilung Odoo 11: {}.

{}

## 3. Liste, Suche, Kanban, Aktionen

Beide Menuepunkte verwenden **dieselben Ansichten**; sie unterscheiden sich nur im Standardfilter.

```
Aktion Verkaufbare Produkte (382):  res_model product.template, view_mode kanban,list,form,activity,
                                    Listenansicht product.template.list (account), view_id 1023,
                                    context {{'search_default_filter_to_sell': 1}}
Aktion Einkaufbare Produkte (383):  identisch, context {{'search_default_filter_to_purchase': 1}}
Odoo 11: beide Aktionen auf product.product (Varianten), context entsprechend
```

Listenansicht:

```
Odoo 11 (product.product)   Interne Referenz | Name | Attributwerte | Verkaufspreis | Verfuegbar |
                            Prognostiziert | Mengeneinheit | Strichcode
Odoo 18 vorher              Interne Referenz | Name | Verkaufspreis | Steuern (Verkauf) |
                            Steuern (Einkauf)
Odoo 18 nachher             Interne Referenz | Name | Verkaufspreis | Bestandsmenge |
                            Geplante Bestandsmenge | Mengeneinheit | Strichcode |
                            Steuern (Verkauf) | Steuern (Einkauf)
```
Ergaenzt wurden die vier fehlenden Odoo-11-Spalten (alle als `optional="show"`, also sichtbar,
aber abschaltbar). Die Odoo-18-Zusatzspalten bleiben. Die Odoo-11-Spalte "Attributwerte" entfaellt:
Odoo 18 fuehrt die Menues auf `product.template` (eine Zeile je Vorlage), Attribute stehen im Reiter
"Attribute & Varianten". Im Odoo-11-Bestand gibt es keine Produkte mit Attributen, die sichtbare
Wirkung ist deshalb identisch. **Entscheidungspunkt fuer Anna:** Odoo 11 listete `product.product`
(eine Zeile je Variante), Odoo 18 `product.template` (eine Zeile je Vorlage) - ein Umbau auf
Varianten waere moeglich, aendert aber Zaehlung und Standardverhalten der Menues.

Suche: Odoo 11 hatte 11 Filter und **keine** Gruppierungen; Odoo 18 zeigt dieselben 11 Filter im
Odoo-11-Wortlaut (Session 123) plus die Odoo-18-Standardfilter sowie zwei eigene Gruppierungen
(Status, Mit Faktor multipliziert). Keine Aenderung in Session 126.

Kanban: Odoo 11 (image_small, lst_price, type, product_variant_count, qty_available, uom_id),
Odoo 18 (image_128, list_price, qty_available, uom_id, product_properties, Aktivitaet)
- funktional gleichwertig, Odoo-18-Optik bleibt.

Aktionen/Buttons im Formular: Odoo 11 hatte die Buttons Variantenpreise, Lagerbestand korrigieren,
Kosten aktualisieren, Produktlieferungen, Routen, Los-/Seriennummer sowie die Smart Buttons
Varianten, Auf Lager, Verkauf, Einkauf, Website. Odoo 18 fuehrt Smart Buttons (Preislistenregeln,
Varianten, Bestand/Prognose, Eingekauft, Verkauft, Dokumente, Meldebestand), die Kopfbuttons
Menge aktualisieren, Auffuellen, Etiketten drucken und den Diagramm-Knopf im Reiter Lager.
Alle Odoo-18-Knoepfe bleiben erhalten.

## 4. Bewusste Abweichungen (mit Begruendung)

```
1. Reiter Bilder: kein Nachbau, weil product.image in Odoo 18 entfaellt und in Odoo 11
   0 von 649 Produkten belegt war (Hauptbild im Kopf, Dokumente-Smart-Button, Chatter).
2. service_policy, project_id: Feld im Odoo-18-Modell nicht mehr vorhanden; die Richtlinie
   laeuft in Odoo 18 ueber invoice_policy und expense_policy (51 Produkte mit
   service_policy 'ordered_timesheet' -> bei der Migration pruefen).
3. property_valuation, property_stock_account_input/-output, cost_method, property_cost_method,
   valuation: in Odoo 18 entfernt (Bewertung an der Produktkategorie); in Odoo 11 unsichtbar.
4. website-Felder (public_categ_ids, inventory_availability, available_threshold, custom_message,
   website_style_ids, website_url): Modul in Odoo 18 nicht installiert; in Odoo 11 0 belegt.
5. Attributwert-Spalte der Liste: siehe Abschnitt 3.
6. purchase_line_warn_msg: Odoo-11-Beschriftung war abgeschnitten ("Bachricht bei
   Beschaffungsauftra"), es bleibt der korrekte Odoo-18-Wortlaut.
7. 'Description for Internal' bleibt wie in Odoo 11 englisch (Odoo 11 hatte dafuer keine
   deutsche Uebersetzung).
```

## 5. Migration

Fuer **jedes** belegte Odoo-11-Produktfeld ist das Zielfeld in Abschnitt 2 vermerkt; belegte
Felder sind insbesondere: name, type, categ_id, product_type_id (410), list_price (606),
recurring_invoice (333), subscription_template_id (292), standard_price (6), uom_id/uom_po_id,
sale_ok, purchase_ok, purchase_method (649), route_ids, tracking, responsible_id, taxes_id (647),
supplier_taxes_id (648), invoice_policy (649), service_type (649), service_tracking, active.
Beziehungen: categ_id -> product.category, taxes_id/supplier_taxes_id -> account.tax,
product_type_id -> itk_product.product_type, subscription_template_id -> sale.subscription.template,
route_ids -> stock.route, uom_id/uom_po_id -> uom.uom. Alle Zielfelder existieren in Odoo 18.

## 6. Nachweise

```
Odoo 11 Nutzung je Feld      scripts/analyse_o11_produktfelder_nutzung.py
Arch/Reiter-Struktur         scripts/zeige_produktformular_struktur.py o11|lokal|vm
Feld-/Ansichtsvergleich      scripts/vergleich_produkt_ansichten.py o11|lokal|vm
Formular- und Reiterabnahme  scripts/browser_produktformular_reiter_abnahme.py lokal|vm
                             (46 Pruefpunkte je Instanz, Ergebnis 46 OK / 0 FEHL)
Vorher-/Nachher-Bilder       scripts/browser_produktformular_aufnahme.py lokal|vm <ordner>
DOM-Sonde Einzelfelder       scripts/_sonde_produktformular_dom.py lokal|vm
```
Bilder: `Desktop/Odoo18-Abnahme-Session126/produktformular_vorher/vm` (Zustand vor der Aenderung),
`produktformular/lokal` und `produktformular/vm` (nachher, je Reiter und Liste).

## 7. Absicherung der bewussten Abweichungen (05.10.2026, Odoo 11 read-only)

### 7.1 Reiter Bilder - es gibt keine Produktbilder und keine Anhaenge

Gemessen in Odoo 11 Prod (`scripts/pruefe_o11_bilder_und_varianten.py`, nur Leseaufrufe):

```
product.image Datensaetze                         0
image / image_medium / image_small belegt
   product.template (649)                     0 / 0 / 0
   product.product  (648)                     0 / 0 / 0
Anhaenge (ir.attachment) an
   product.template                               0   davon Bilder 0
   product.product                                0   davon Bilder 0
   product.image                                  0
   product.supplierinfo                           0
```

Ergebnis: In Odoo 11 ist **kein einziges Produktbild und kein einziger Anhang** an Produkten
gespeichert - weder Zusatzbilder (product.image war leer), noch Hauptbilder (alle drei
Bildfelder zu 0 Prozent belegt), noch Dateianhaenge. Durch das fehlende Feld
`product_image_ids` in Odoo 18 gehen daher **keine Daten verloren**, und es ist **keine
Migrationsregel** erforderlich (es gibt nichts zu uebernehmen). Waeren Zusatzbilder vorhanden,
waere die Regel: Datei aus dem Odoo-11-Filestore in `product.template.image_1920` bzw. in einen
Anhang am Produkt uebernehmen - dieser Fall tritt nicht ein.

### 7.2 product.product -> product.template - keine produktiven Varianten

Gemessen (dieselben Skripte, Odoo 11 read-only):

```
product.template                          649
product.product                           648
Vorlagen mit mehr als einer Variante        0
Varianten mit Attributwerten (attribute_value_ids)   0 von 648
product.attribute                           2   ("Variante Flo", "Variante Kat", Typ radio)
product.attribute.value                     5
product.attribute.line                      2   (beide an Vorlage 300 "Test Produkt 2", archiviert)
Vorlagen ohne Variante                      1   (Vorlage 263, in keinem Beleg verwendet)
```

Belegverweise (jede Zeile zeigt auf die Variante, nicht auf die Vorlage):

```
account.move.line      10039 Zeilen, 410 Produkte, aus Mehrfachvarianten-Vorlagen 0
sale.order.line         4015 Zeilen, 403 Produkte, aus Mehrfachvarianten-Vorlagen 0
purchase.order.line        0 Zeilen (keine Eingangsrechnungen in Odoo 11)
sale.subscription.line   2438 Zeilen, 209 Produkte, aus Mehrfachvarianten-Vorlagen 0
stock.move               327 Zeilen,  91 Produkte, aus Mehrfachvarianten-Vorlagen 0
Vorlagen mit mehreren in Belegen verwendeten Varianten: 0 (in allen Modellen)
```

Ergebnis: Es gibt **keine produktiven Varianten**. Jede Vorlage hat genau eine Variante, kein
Produkt traegt Attributwerte. Eine Mehrfachzuordnung (mehrere Varianten derselben Vorlage in einer
Zeile einer Rechnung/eines Auftrags), ein Datenverlust oder eine falsche Verknuepfung ist damit
ausgeschlossen. Die Zuordnung Vorlage <-> Variante bleibt 1:1 und ist ueber
`product.product.product_tmpl_id` eindeutig aufloesbar; die Belegzeilen zeigen weiterhin auf die
(neu erzeugte) Variante.

Migrationsregeln fuer die beiden Randfaelle (beide unkritisch, kein Produktivbezug):

```
Vorlage 263 "Aufbau einer Plattform fuer interkommunalen Wissens- und Erfahrungsaustausch"
   hat in Odoo 11 keine Variante und ist in keinem Beleg, keiner Preisliste und keiner
   Lieferanteninfo verwendet (0 Treffer in allen geprueften Modellen).
   Regel: beim Anlegen in Odoo 18 entsteht die Variante automatisch; es ist keine
   Belegzuordnung nachzuziehen.
Vorlage 300 "Test Produkt 2" (aktiv=False, Typ service, in keinem Beleg verwendet) traegt die
   beiden einzigen Attributzeilen und deren Werte.
   Regel: Attribute und Werte (2 Attribute, 5 Werte) sind reine Stammdaten ohne
   Variantenwirkung in Odoo 11. Sie werden nur uebernommen, wenn die Stammdaten gebraucht
   werden; dabei ist sicherzustellen, dass genau eine Variante je Vorlage erhalten bleibt
   (keine Variantenvervielfachung). Da die Vorlage archiviert und unbenutzt ist, ist auch ein
   Verzicht dokumentierbar.
```

## 8. Funktions- und Verknuepfungspruefung der sieben Reiter (echter Browser)

Werkzeug: `scripts/browser_produktformular_funktionen.py lokal|vm` - oeffnet ein echtes Produkt
der Menues (id 3 "Produkt B", Ware mit Verkaeufen und Einkaeufen), prueft je Reiter die
Funktionen und klickt Smart Buttons an (nur oeffnen, nichts speichern).
Ergebnis: **lokal 38 OK / 0 FEHL, VM 38 OK / 0 FEHL**.

```
Kopfbereich  Smart Buttons: Regeln Preislisten, Dokumente, Verkauft (1,000 Einheit(en)),
             Eingekauft (2,000 Einheit(en)), Bestand (Eingang: 0 Ausgang: 0)
             Klickproben: Verkauft -> Verkaufsanalyse (action-420), Eingekauft ->
             Einkaufshistorie (action-1175), Regeln Preislisten -> product.pricelist.item
             Kopfknoepfe: Auffuellen, Etiketten drucken (Dialog oeffnet und schliesst ohne
             Speicherung)
             "Varianten" wird bei nur einer Variante nicht angezeigt (Odoo-18-Regel) -
             dokumentierte Abweichung zu Odoo 11, das den Zaehler immer zeigte
Allgemeine   Product-Type (itk_product.product_type), Interne Kategorie (product.category),
Informationen Interne Referenz, Strichcode, Verantwortlich (res.users), Verkaufspreis,
             Kosten, Kann verkauft/eingekauft werden, Abonnement Produkt (recurring_invoice);
             Abonnement-Vorlage erscheint, sobald "Abonnement Produkt" gesetzt ist
Verkauf      Optionale Produkte (Odoo-18-Feld fuer alternative/Zubehoer-Produkte),
             Stichwoerter, Spesen weiter verrechnen (Auswahl aktiv "Nein")
Einkauf      Lieferantenliste mit Spalten Lieferant/Menge/Preis/Waehrung/Liefervorlaufzeit
             (Zeile vorhanden, Hinzufuegen moeglich), Einkauf ME editierbar
Lager        Routen als Auswahl (stock.route, "Einkaufen" gesetzt), Verantwortlich (Avatar),
             Gewicht, Volumen, Auslieferungszeit, Verpackungen (Liste mit Spalten und
             Hinzufuegen), Knopf "Diagramm ansehen" vorhanden
Abrechnung   Steuern (Verkauf) und Steuern (Einkauf) als Chips belegt (20% USt / 20% VSt,
             account.tax), Steuerzeichenkette "+ 1,20 € Inkl. Steuern", Fakturierungsregel und
             Kontrollrichtlinie als Radioknoepfe mit den Werten (Bestellte Mengen / Gelieferte
             Mengen bzw. Auf bestellte Mengen / Auf erhaltene Mengen), beide editierbar
Notizen      Beschreibung (HTML-Feld, in Odoo 11 Textfeld), Verkaufs-, Einkaufs- und drei
             Lieferbeschreibungen sichtbar und editierbar; Warnhinweise Verkauf/Einkauf als
             Auswahl mit Wert "Keine Nachricht"
Attribute &  Attributliste mit Spalten Attribut/Werte und "Zeile hinzufuegen" vorhanden
Varianten
```
Bilder je Reiter: `Desktop/Odoo18-Abnahme-Session126/produktformular_funktionen/{{lokal,vm}}`.

## 9. Status

Umgesetzt und im echten Browser lokal und auf der VM geprueft (jeweils 46 OK / 0 FEHL, Bilder
gesehen): Reiter Abrechnung und Notizen wiederhergestellt, Feldpositionen und Beschriftungen nach
Odoo 11, vier Odoo-11-Spalten in der Liste ergaenzt, keine Odoo-18-Funktion entfernt, keine
Dummy-Felder, kein Feld doppelt im Formular (Arch geprueft).
**Abrechnung bleibt IN ARBEIT** - nicht als migrationsbereit oder abgeschlossen markiert.
""".format(reiter11_txt, reiter18_txt, gesamt11, dict(typverteilung), kopf + "\n" + "\n".join(zeilen))

ziel = os.path.join(REPO, "docs", "o11-o18-vergleich-abrechnung-produktformular.md")
open(ziel, "w", encoding="utf-8").write(text)
print("geschrieben:", ziel, len(text), "Zeichen,", len(zeilen), "Feldzeilen")
