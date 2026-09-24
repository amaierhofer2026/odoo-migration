"""Erzeugt docs/o11-o18-vergleich-verkauf-teil2.md aus docs/_verkauf_teil2_felder.json.

Die Messdaten kommen aus scripts/analyse_verkauf_teil2_felder.py (Odoo 11 read-only,
Odoo 18 lokal und VM). Die Zuordnung Odoo-11-Feld -> Odoo-18-Ziel ist im Abschnitt ZIEL
hinterlegt und wird beim Bauen mit den Messdaten geprueft (Feld vorhanden? Typ gleich?).

Aufruf:
    python scripts/baue_verkauf_teil2_doku.py
"""
from __future__ import annotations

import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUELLE = os.path.join(REPO, "docs", "_verkauf_teil2_felder.json")
ZIEL = os.path.join(REPO, "docs", "o11-o18-vergleich-verkauf-teil2.md")

# Felder, die es in Odoo 11 gibt, in Odoo 18 aber nicht (Name nicht vorhanden).
# Wert = (Einstufung, Odoo-18-Ziel bzw. Begruendung)
OHNE_ZIEL = {
    # sale.order
    "sale.order": {
        "picking_policy": ("kein Ziel vorhanden",
                           "Feld aus `sale_stock`; stock wird nicht installiert (Entscheidung Session 119). "
                           "In Odoo 11 bei allen 2.461 Auftraegen der Standardwert `direct`."),
        "warehouse_id": ("kein Ziel vorhanden",
                         "Feld aus `sale_stock`; in Odoo 11 bei allen Auftraegen das eine Standardlager."),
        "procurement_group_id": ("kein Ziel vorhanden",
                                 "Feld aus `sale_stock` (Beschaffungsgruppe, 240 Auftraege)."),
        "picking_ids": ("kein Ziel vorhanden",
                        "Feld aus `sale_stock`; 235 Auftraege hatten Lieferauftraege, davon 0 erledigt."),
        "delivery_count": ("berechnet", "Zaehler aus `picking_ids` (`sale_stock`), entfaellt mit dem Modul."),
        "analytic_account_id": ("obsolet",
                                "0 Verwendungen in Odoo 11. Kostenstellen laufen in Odoo 18 zeilenweise "
                                "ueber `sale.order.line.analytic_distribution`."),
        "incoterm": ("obsolet",
                     "0 Verwendungen in Odoo 11. Odoo 18 fuehrt Incoterms im Modul `sale_stock` "
                     "(nicht installiert)."),
        "payment_tx_id": ("obsolet", "0 Verwendungen. Ziel in Odoo 18 ist `transaction_ids` (many2many payment.transaction)."),
        "payment_tx_ids": ("Transformation", "Ziel in Odoo 18: `transaction_ids` (many2many payment.transaction)."),
        "payment_acquirer_id": ("berechnet", "berechnetes Feld aus `sale_payment`, 0 Verwendungen; Ziel ist `transaction_ids`."),
        "payment_transaction_count": ("berechnet", "Zaehler aus `payment_tx_ids`, 0 Verwendungen; Odoo 18 zaehlt ueber `transaction_ids`."),
        "portal_url": ("berechnet", "berechneter Portal-Link; Odoo 18 fuehrt `access_url` (berechnet)."),
        "product_id": ("berechnet",
                       "related auf die erste Auftragszeile, nicht gespeichert. Funktion in Odoo 18 ueber "
                       "`order_line.product_id`."),
        "project_ids": ("kein Ziel vorhanden", "Feld aus `sale_timesheet` (nicht installiert, 0 Stundenzettelzeilen)."),
        "project_project_id": ("kein Ziel vorhanden", "Feld aus `sale_timesheet` (nicht installiert)."),
        "tasks_count": ("berechnet", "Zaehler aus `sale_timesheet`, Modul nicht installiert."),
        "tasks_ids": ("kein Ziel vorhanden", "Feld aus `sale_timesheet` (nicht installiert)."),
        "timesheet_count": ("berechnet", "Zaehler aus `sale_timesheet`, Modul nicht installiert."),
        "timesheet_ids": ("kein Ziel vorhanden", "Feld aus `sale_timesheet` (nicht installiert)."),
        "can_directly_mark_as_paid": ("obsolet", "Website-Kaufvorgang (`website_sale`), 0 Verwendungen."),
        "cart_recovery_email_sent": ("obsolet", "Website-Kaufvorgang (`website_sale`), 0 Verwendungen."),
        "cart_quantity": ("obsolet", "berechnet, Website-Kaufvorgang, 0 Verwendungen."),
        "is_abandoned_cart": ("obsolet", "berechnet, Website-Kaufvorgang, 0 Verwendungen."),
        "only_services": ("obsolet", "berechnet, Website-Warenkorb, 0 Verwendungen."),
        "website_order_line": ("obsolet", "Website-Warenkorb (`website_sale`), 0 Verwendungen."),
        "warning_stock": ("obsolet", "Website-Bestandshinweis (`website_sale_stock`), 0 Verwendungen."),
        "message_last_post": ("obsolet", "technischer mail-Rest, 0 Verwendungen, in Odoo 18 entfernt."),
        "message_channel_ids": ("obsolet", "technischer mail-Rest, in Odoo 18 entfernt."),
        "message_unread": ("obsolet", "technischer mail-Rest, in Odoo 18 entfernt."),
        "message_unread_counter": ("obsolet", "technischer mail-Rest, in Odoo 18 entfernt."),
        "__last_update": ("obsolet", "technisches Feld, in Odoo 18 entfernt (ersetzt `write_date`)."),
    },
    # sale.order.line
    "sale.order.line": {
        "amt_invoiced": ("Transformation", "Ziel in Odoo 18: `amount_invoiced` (monetary, berechnet)."),
        "amt_to_invoice": ("Transformation", "Ziel in Odoo 18: `amount_to_invoice` (monetary, berechnet)."),
        "price_reduce": ("obsolet",
                         "Odoo 18 fuehrt keinen reduzierten Stueckpreis mehr; Anzeige und Berechnung nutzen "
                         "`price_unit` mit Rabatt und `price_subtotal`."),
        "layout_category_sequence": ("obsolet",
                                     "Rest des Odoo-11-Reportlayouts; 1.366 Zeilen tragen nur den Standardwert 1, "
                                     "Odoo 18 kennt kein `sale.layout.category`."),
        "layout_category_id": ("obsolet",
                               "Modell `sale.layout.category` ist in Odoo 11 nicht registriert (toter Menuepunkt); "
                               "Feld auf 2 von 4.007 Zeilen gesetzt."),
        "move_ids": ("kein Ziel vorhanden", "Feld aus `sale_stock` (Lagerbewegungen, 296 Zeilen)."),
        "analytic_tag_ids": ("obsolet", "0 Verwendungen; Ziel ist `analytic_distribution`."),
        "product_packaging": ("kein Ziel vorhanden",
                              "Feld aus `sale_stock`, 0 Verwendungen; Odoo 18 hat `product_packaging_id` (ebenfalls sale_stock)."),
        "route_id": ("kein Ziel vorhanden", "Feld aus `sale_stock`, 0 Verwendungen."),
        "task_id": ("kein Ziel vorhanden", "Feld aus `sale_timesheet`, 0 Verwendungen."),
        "warning_stock": ("obsolet", "Website-Bestandshinweis (`website_sale_stock`), 0 Verwendungen."),
        "product_image": ("berechnet", "berechnetes Bild der Produktvariante."),
        "qty_delivered_updateable": ("berechnet",
                                     "berechnetes Steuerfeld; Odoo 18 regelt das ueber `qty_delivered_method`."),
        "__last_update": ("obsolet", "technisches Feld, in Odoo 18 entfernt."),
    },
}

# Felder mit gleichem Namen, aber anderem Typ oder anderer Relation (Transformation)
TRANSFORMATION = {
    ("sale.order", "invoice_ids"): "Odoo 11 `account.invoice` -> Odoo 18 `account.move` (Rechnungsmodell umbenannt).",
    ("sale.order", "note"): "Odoo 11 `text` -> Odoo 18 `html` (Odoo-18-Textfeld, Inhalt 1:1 uebernehmbar).",
    ("sale.order", "tag_ids"): "Odoo 11 `crm.lead.tag` -> Odoo 18 `crm.tag` (in Odoo 11 traegt genau 1 von 2.461 Auftraegen ein Stichwort: A-1900710).",
    ("sale.order.line", "invoice_lines"): "Odoo 11 `account.invoice.line` -> Odoo 18 `account.move.line`.",
    ("sale.order.line", "product_uom"): "Odoo 11 `product.uom` -> Odoo 18 `uom.uom` (Modell umbenannt).",
}

# Zusaetzliche Hinweise je Feld (Herkunft, Beschriftung, Bedeutung)
HINWEIS = {
    ("sale.order", "state"): "Odoo 11 kennt zusaetzlich `done` (0 Datensaetze); Odoo 18 fuehrt `sale` + `locked`.",
    ("sale.order", "date_order"): "Odoo 18 setzt `date_order` beim Bestaetigen neu; das Odoo-11-Bestaetigungsdatum liegt in `confirmation_date`.",
    ("sale.order", "confirmation_date"): "In Odoo 18 eigenes Feld des Moduls `itk_sale_management` (18.0.1.1.0), Beschriftung \"Bestätigung am\".",
    ("sale.order", "team_id"): "Beschriftung in Odoo 18 \"Vertriebskanal\" (Angleichung an Odoo 11).",
    ("sale.order", "subscription_management"): "ITK-Feld (`itk_subscription`): steuert, ob der Auftrag ein Abo erzeugt/erneuert.",
    ("sale.order", "subscription_count"): "ITK-Feld (`itk_subscription`), berechneter Zaehler fuer den Smart Button.",
    ("sale.order.line", "qty_multiplication_factor"): "ITK-Feld (`itk_multifactor`): Multiplikationsfaktor je Zeile (1.366 Zeilen != 1).",
    ("sale.order.line", "subscription_id"): "ITK-Feld (`itk_subscription`): Verknuepfung der Zeile zum Abo (2.307 Zeilen).",
    ("sale.order.line", "partner_id"): "ITK-Feld (`itk_saleorder_lines`), in Odoo 11 mit 0 Verwendungen.",
    ("sale.order.line", "salesperson_id"): "ITK-Feld (`itk_saleorder_lines`): Verkaeufer je Zeile, in Odoo 11 mit 0 Verwendungen.",
}


def kuerzen(text, laenge=110):
    text = " ".join((text or "").split())
    return text if len(text) <= laenge else text[:laenge - 1] + "..."


def typ(f):
    t = f["ttype"]
    if f.get("relation"):
        t += " -> " + f["relation"]
    return t


def belegt(f, gesamt):
    if f.get("belegt") is None:
        if f.get("related"):
            return "abgeleitet (related)"
        if not f["gespeichert"]:
            return "berechnet (nicht gespeichert)"
        return "nicht gezaehlt"
    if isinstance(f["belegt"], str):
        return f["belegt"]
    return "%d von %d" % (f["belegt"], gesamt)


def tabelle(modell, d):
    a = d["o11"][modell]["felder"]
    b = d["o18"][modell]["felder"]
    gesamt11 = d["o11"][modell]["datensaetze"]
    zeilen = []
    zeilen.append("| Odoo-11-Feld | Beschriftung | Typ / Relation | Pflicht | readonly | gespeichert | "
                  "belegte Datensaetze | Odoo-18-Ziel | Einstufung |")
    zeilen.append("|---|---|---|---|---|---|---|---|---|")
    for n in sorted(a):
        f = a[n]
        g = b.get(n)
        if g:
            if (modell, n) in TRANSFORMATION:
                ziel = TRANSFORMATION[(modell, n)]
                stufe = "Transformation"
            elif f["ttype"] != g["ttype"] or (f.get("relation") or "") != (g.get("relation") or ""):
                ziel = "Odoo 18 `%s` (%s)" % (n, typ(g))
                stufe = "Transformation"
            else:
                ziel = "Odoo 18 `%s` (%s)" % (n, typ(g))
                stufe = "berechnet" if not f["gespeichert"] else "1:1"
        else:
            stufe, ziel = OHNE_ZIEL[modell][n]
        hinweis = HINWEIS.get((modell, n))
        if hinweis:
            ziel += " " + hinweis
        zeilen.append("| `%s` | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            n, (f.get("anzeige") or f.get("beschriftung") or "").replace("|", "/"),
            typ(f), "ja" if f["pflicht"] else "nein", "ja" if f["readonly"] else "nein",
            "ja" if f["gespeichert"] else "nein (berechnet)",
            belegt(f, gesamt11), kuerzen(ziel, 170), stufe))
    return "\n".join(zeilen)


def main() -> int:
    d = json.load(open(QUELLE, encoding="utf-8"))
    for modell in ("sale.order", "sale.order.line"):
        fehlend = [n for n in d["o11"][modell]["felder"] if n not in d["o18"][modell]["felder"]
                   and n not in OHNE_ZIEL[modell]]
        if fehlend:
            raise SystemExit("Zuordnung fehlt fuer %s: %s" % (modell, fehlend))

    teile = []
    teile.append("""# Odoo 11 -> Odoo 18: Bereich Verkauf, Teil 2 (Feldinventar sale.order und sale.order.line)

Stand: 24.09.2026, Session 121. Odoo 11 Prod (`portal.it-kommunal.at`, DB `ITK_V1_a`) wurde
ausschliesslich lesend gelesen. Keine Datenmigration, keine Aenderung an Produktivdaten,
keine Aenderung an Odoo 18 in diesem Teil.

Werkzeuge: `scripts/analyse_verkauf_teil2_felder.py` (Feldinventar, Nutzung, Auswahlwerte;
schreibt `docs/_verkauf_teil2_felder.json`), `scripts/baue_verkauf_teil2_doku.py` (dieses Dokument).

## 1. Uebersicht

```
                                  sale.order                     sale.order.line
Odoo 11 Felder                    89                             53
Odoo 18 Felder (lokal = VM)       110                            80
gemeinsame Feldnamen              58                             39
nur Odoo 11                       31                             14
nur Odoo 18                       52                             41
Typ-/Relationsabweichungen        3                              2
Datensaetze Odoo 11               2.461                          4.007
Datensaetze Odoo 18 (Teststand)   18 lokal / 20 VM               28 lokal / 29 VM
```

Zaehlweise: die Feldlisten stammen aus `ir.model.fields` und wurden gegen `fields_get`
gegengeprueft (beide Quellen liefern dieselben Feldmengen, je Modell und Instanz).
Belegte Datensaetze = `search_count([(feld, '!=', False)])` in Odoo 11, nur bei gespeicherten,
nicht abgeleiteten Feldern.

Einstufung je Feld (Vorgabe): `1:1` | `Transformation` | `berechnet` | `kein Ziel vorhanden` |
`obsolet`. Felder, die es nur in Odoo 18 gibt, sind in Abschnitt 9 als Zusatzfunktion gefuehrt.

## 2. sale.order - Feldinventar Odoo 11 gegen Odoo 18

""")
    teile.append(tabelle("sale.order", d))
    teile.append("\n## 3. sale.order.line - Feldinventar Odoo 11 gegen Odoo 18\n")
    teile.append(tabelle("sale.order.line", d))

    # Selection-Werte
    teile.append("\n## 4. Selection-Werte\n")
    for modell in ("sale.order", "sale.order.line"):
        teile.append("**%s**\n" % modell)
        teile.append("| Feld | Odoo 11 | Odoo 18 | Bewertung |")
        teile.append("|---|---|---|---|")
        a = d["o11"][modell]["felder"]
        b = d["o18"][modell]["felder"]
        namen = sorted({n for n, f in a.items() if f.get("selection")} |
                       {n for n, f in b.items() if f.get("selection")})
        for n in namen:
            s11 = [x[0] for x in a.get(n, {}).get("selection", [])]
            s18 = [x[0] for x in b.get(n, {}).get("selection", [])]
            if not s11:
                bewertung = "nur Odoo 18"
            elif not s18:
                bewertung = "Feld entfaellt (siehe Abschnitt 7/8)"
            elif s11 == s18:
                bewertung = "identisch"
            else:
                mehr = [x for x in s11 if x not in s18]
                bewertung = "Odoo 18 ohne %s (nicht verwendet)" % ", ".join(mehr) if mehr else "Odoo 18 ist Obermenge"
            teile.append("| `%s` | %s | %s | %s |" % (n, ", ".join(s11) or "-", ", ".join(s18) or "-", bewertung))
        teile.append("")

    # Pflicht- und readonly-Felder
    teile.append("## 5. Pflichtfelder und readonly-Felder\n")
    for modell in ("sale.order", "sale.order.line"):
        a = d["o11"][modell]["felder"]
        b = d["o18"][modell]["felder"]
        p11 = sorted(n for n in a if a[n]["pflicht"])
        p18 = sorted(n for n in b if b[n]["pflicht"])
        r11 = sorted(n for n in a if a[n]["readonly"])
        r18 = sorted(n for n in b if b[n]["readonly"])
        teile.append("**%s**\n" % modell)
        teile.append("```")
        teile.append("Pflichtfelder Odoo 11 : %s" % ", ".join(p11))
        teile.append("Pflichtfelder Odoo 18 : %s" % ", ".join(p18))
        teile.append("in Odoo 18 zusaetzlich pflichtig : %s" % (", ".join(sorted(set(p18) - set(p11))) or "keiner"))
        teile.append("nicht mehr pflichtig in Odoo 18    : %s" % (", ".join(sorted(set(p11) - set(p18))) or "keiner"))
        teile.append("readonly Odoo 11       : %s" % ", ".join(r11))
        teile.append("readonly Odoo 18       : %s" % ", ".join(r18))
        teile.append("```\n")
        teile.append("Hinweis: die zusaetzlichen Pflichtfelder in Odoo 11 (`picking_policy`, `warehouse_id`,\n"
                     "`currency_id`) stammen aus `sale_stock` beziehungsweise aus berechneten Feldern; in Odoo 18\n"
                     "ist `company_id` neu pflichtig. Kein Feld verliert dadurch Daten.\n")

    # ITK-Felder
    teile.append("""## 6. ITK-eigene Felder und Sonderlogik

```
sale.order
  sale_contact_id            res.partner       itk_sale_management   Odoo 11 belegt: 3 von 2.461
  administrative_contact_id  res.partner       itk_sale_management   Odoo 11 belegt: 2
  technical_contact_id       res.partner       itk_sale_management   Odoo 11 belegt: 1
  final_customer_id          res.partner       itk_sale_management   Odoo 11 belegt: 0
  product_category_id        product.category  itk_sale_management   Odoo 11 belegt: 47
  confirmation_date          datetime          itk_sale_management   Odoo 11 belegt: 2.437 (in Odoo 18 eigenes Feld)
  subscription_management    selection         itk_subscription      Odoo 11 belegt: 2.461
  subscription_count         integer           itk_subscription      berechnet (Smart Button)

sale.order.line
  qty_multiplication_factor  integer           itk_multifactor       Odoo 11 belegt: 1.366 von 4.007
  subscription_id            many2one          itk_subscription      Odoo 11 belegt: 2.307
  partner_id                 many2one          itk_saleorder_lines   Odoo 11 belegt: 0
  salesperson_id             many2one          itk_saleorder_lines   Odoo 11 belegt: 0
```

Alle ITK-Felder sind in Odoo 18 mit gleichem Namen, gleichem Typ und gleicher Relation vorhanden
(Ausnahme: `confirmation_date` stammt in Odoo 18 aus `itk_sale_management` statt aus `sale`).
Sonderlogik: `subscription_management` steuert die Abo-Erzeugung, `qty_multiplication_factor`
geht in die Abrechnung ein (Faktor 1.000er-Regel), `subscription_id` verbindet Zeile und Abo.

## 7. Felder ohne Ziel in Odoo 18 (Modul in Odoo 18 nicht installiert bzw. Funktion entfaellt)

""")
    ohne = {"kein Ziel vorhanden": [], "Transformation": [], "berechnet": [], "obsolet": []}
    for modell in ("sale.order", "sale.order.line"):
        for n, (stufe, text) in sorted(OHNE_ZIEL[modell].items()):
            if n in d["o18"][modell]["felder"]:
                continue
            ohne[stufe].append((modell, n, d["o11"][modell]["felder"][n], text))
    for stufe in ("kein Ziel vorhanden", "Transformation"):
        for modell, n, f, text in ohne[stufe]:
            teile.append("- `%s.%s` (%s, %s): %s" % (modell, n, typ(f), belegt(f, d["o11"][modell]["datensaetze"]), text))
    teile.append("")
    teile.append("## 8. Fachlich nicht mehr benoetigte Felder (obsolet)\n")
    for modell, n, f, text in sorted(ohne["obsolet"]):
        teile.append("- `%s.%s` (%s, %s): %s" % (modell, n, typ(f), belegt(f, d["o11"][modell]["datensaetze"]), text))
    teile.append("")

    # Nur Odoo 18
    teile.append("## 9. Felder, die es nur in Odoo 18 gibt (Zusatzfunktionen, bleiben)\n")
    ziele = {"transaction_ids": "Ziel von `payment_tx_ids`",
             "amount_invoiced": "Ziel von `amt_invoiced`",
             "amount_to_invoice": "Ziel von `amt_to_invoice`",
             "analytic_distribution": "Ziel von `analytic_account_id`",
             "product_packaging_id": "Odoo-18-Entsprechung zu `product_packaging` (beide sale_stock)",
             "access_url": "Odoo-18-Entsprechung zu `portal_url`",
             "locked": "Odoo-18-Ersatz fuer den Odoo-11-Status `done`"}
    for modell in ("sale.order", "sale.order.line"):
        nur = sorted(set(d["o18"][modell]["felder"]) - set(d["o11"][modell]["felder"]))
        teile.append("\n**%s** (%d Felder)\n" % (modell, len(nur)))
        teile.append("| Feld | Typ / Relation | Bedeutung |")
        teile.append("|---|---|---|")
        for n in nur:
            teile.append("| `%s` | %s | %s |" % (n, typ(d["o18"][modell]["felder"][n]), ziele.get(n, "Odoo-18-Zusatzfunktion")))
    teile.append("")

    # Beschriftungsunterschiede in der Anzeigesprache
    teile.append("## 10. Beschriftungsunterschiede in der Anzeigesprache (de_DE)\n")
    teile.append("Vergleich der Feldbeschriftungen gemeinsamer Felder, gelesen mit `lang=de_DE`.\n")
    zeilen = []
    for modell in ("sale.order", "sale.order.line"):
        a = d["o11"][modell]["felder"]
        b = d["o18"][modell]["felder"]
        for n in sorted(set(a) & set(b)):
            x = (a[n].get("anzeige") or "").strip()
            y = (b[n].get("anzeige") or "").strip()
            if x and y and x != y:
                zeilen.append((modell, n, x, y))
    zuordnung = {
        ("sale.order", "administrative_contact_id"): "bewusst angeglichen (Session 117): Verwaltungskontakt",
        ("sale.order", "team_id"): "bewusst angeglichen (Session 117): Vertriebskanal",
        ("sale.order", "opportunity_id"): "bewusst angeglichen (Session 117): Chance",
        ("sale.order", "source_id"): "bewusst angeglichen (Session 117): Referenz",
        ("sale.order", "activity_state"): "Befund: die Odoo-11-de_DE-Uebersetzung ist falsch (\"Bundesland\"), englisch \"State\"; Odoo 18 ist korrekt",
    }
    teile.append("| Modell | Feld | Odoo 11 (de_DE) | Odoo 18 (de_DE) | Bewertung |")
    teile.append("|---|---|---|---|---|")
    for modell, n, x, y in zeilen:
        teile.append("| %s | `%s` | %s | %s | %s |" % (modell, n, x, y,
                                                       zuordnung.get((modell, n), "Odoo-18-Wortlaut (bleibt, dokumentiert)")))
    teile.append("")
    teile.append("Anzahl der abweichenden Beschriftungen: %d.\n" % len(zeilen))

    teile.append("""## 11. Stammdaten, die vor der Datenmigration zuzuordnen sind

Read-only in Odoo 11 gemessen, mit Odoo 18 abgeglichen (Stand 24.09.2026):

```
Zahlungsbedingungen (Feld sale.order.payment_term_id, 613 von 2.461 Auftraegen belegt)
  Odoo 11 "Sofortige Zahlung"   96 Auftraege   -> Odoo 18 vorhanden (id 1)
  Odoo 11 "14 Tage"            515 Auftraege   -> Odoo 18 vorhanden (id 12)
  Odoo 11 "30 Tage netto"        2 Auftraege   -> Odoo 18 hat "30 Tage" (id 4), aber keinen
                                                  Eintrag "30 Tage netto" -> Zuordnung entscheiden
  Odoo 11 "15 Tage"              0 Auftraege   -> Odoo 18 vorhanden (id 2), nicht noetig

Preisliste (sale.order.pricelist_id, 2.461 von 2.461 belegt)
  Zuordnung der Odoo-11-Preislisten auf die Odoo-18-Preisliste "Preisliste 2026 + Valorisierung"
  (id 34, EUR, aktiv) ist ein Datenmigrationsschritt (offen seit Session 105/117).

Verkaeufer (sale.order.user_id, 2.461 belegt, 31 verschiedene Verkaeufer)
  Groesste Gruppen: IT-Kommunal 1.644, Oberoesterreich GemDAT 205, Waiss Martina 115,
  Sales GSZ Kaernten 113, Niederoesterreich GemDAT 96, Kufgem 71.
  Odoo 11 hat 57 aktive Benutzer, Odoo 18 deutlich weniger -> Benutzerzuordnung vor der Migration
  (offen seit Session 105; ausgeschiedene Benutzer deaktiviert anlegen).

Vertriebskanal (sale.order.team_id, 2.461 belegt)
  Odoo 11 nutzt 4 Kanaele: Vertriebskanaele (Intern) 2.443, Interne Weitergabe 13,
  Persoenlicher Kontakt 4, Newsletter 1. Odoo 18 hat 8 Teams -> Zuordnung entscheiden.

Stichwoerter (sale.order.tag_ids)
  Odoo 11 hat 44 crm.lead.tag-Datensaetze; im Verkauf nutzt genau 1 Auftrag (A-1900710) das
  Stichwort "Up-Sell". Odoo 18 hat derzeit 0 crm.tag-Datensaetze. Tag-Stammdaten sind im
  CRM-Bereich als Migrationspunkt dokumentiert (Session 114).

Weitere Felder ohne Pflege in Odoo 11
  source_id, campaign_id, medium_id (utm): 0 von 2.461 Auftraegen belegt -> keine Zuordnung noetig.
  fiscal_position_id: 0 von 2.461 belegt -> keine Zuordnung noetig.
```

## 12. Befunde dieser Analyse

```
1. Irrefuehrende Odoo-11-Uebersetzung: das Feld activity_state heisst in Odoo 11 auf Deutsch
   "Bundesland" (englisch "State"), in Odoo 18 "Status der Aktivität". Kein Fehler in Odoo 18,
   kein Handlungsbedarf - dokumentiert, damit der Unterschied nicht als Luecke gewertet wird.
2. tag_ids: die Angabe "0 Verwendungen" aus Session 117 ist zu korrigieren - genau 1 von 2.461
   Auftraegen traegt ein Stichwort ("Up-Sell", Auftrag A-1900710).
3. Beschriftung von note: Odoo 11 "Geschäftsbedingungen", Odoo 18 "Allgemeine
   Geschäftsbedingungen"; 2.439 von 2.461 Auftraegen sind befuellt.
4. Odoo 11 fuehrt amount_total/amount_tax/amount_untaxed als gespeicherte Felder, Odoo 18
   berechnet sie. Kein Datenverlust: die Werte entstehen bei der Migration aus den Auftragszeilen.
```

## 13. Offene Punkte und Entscheidungen (Vorschlag)

```
1. note (Geschaeftsbedingungen, 2.439 Auftraege): Odoo 11 speichert reinen Text, Odoo 18 HTML.
   Vorschlag fuer die Migration: Zeilenumbrueche in <br> umwandeln, sonst Inhalt 1:1 uebernehmen.
2. Zahlungsbedingung "30 Tage netto" (2 Auftraege): auf Odoo 18 "30 Tage" abbilden oder
   "30 Tage netto" in Odoo 18 anlegen?
3. Stichwort "Up-Sell" (1 Auftrag): das Tag fehlt in Odoo 18 (0 Datensaetze). Im Rahmen der
   Tag-Stammdaten des CRM-Bereichs anlegen oder den Auftrag ohne Stichwort migrieren?
4. Preislisten-, Verkaeufer- und Vertriebskanal-Zuordnung bleiben Datenmigrationsschritte
   (wie in Session 105/117 dokumentiert), keine Aenderung an Odoo 18 in diesem Teil.
5. Bestaetigung erbeten, dass die entfallenden Felder (Abschnitt 7 und 8) so akzeptiert werden,
   insbesondere die Felder aus sale_stock (Lager) und sale_timesheet (Zeiterfassung).
```

## 14. Nachweise

```
scripts/verify_s121_verkauf_teil2.py       111 OK / 0 FEHL
                                           (prueft Odoo 11 read-only, Odoo 18 lokal und VM in einem Lauf)
Datenlage                                   Odoo 11: sale.order 2.461, sale.order.line 4.007
                                            Odoo 18: 18 Auftraege / 28 Zeilen (lokal),
                                            20 Auftraege / 29 Zeilen (VM)
Vergleichsgrundlage                         ir.model.fields gegen fields_get geprueft (identische Feldmengen)
Testdaten                                   keine angelegt, keine geaendert
Odoo 11 Prod                                ausschliesslich lesend
```
""")
    open(ZIEL, "w", encoding="utf-8", newline="\n").write("\n".join(teile) + "\n")
    print("Dokument geschrieben: %s (%d Zeilen)" % (ZIEL, len("\n".join(teile).splitlines())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
