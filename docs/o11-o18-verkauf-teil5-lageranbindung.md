# Odoo 11 -> Odoo 18: Bereich Verkauf, Teil 5 - Schliessung der Luecke "Lageranbindung"

Stand: 29.09.2026, Session 121. Odoo 11 Prod (`portal.it-kommunal.at`, DB `ITK_V1_a`) wurde
ausschliesslich lesend gelesen. Aenderungen ausschliesslich in Odoo 18. Keine Datenmigration,
keine Uebernahme von Lagerbestaenden, Lieferungen oder sonstigen Odoo-11-Daten.

## 1. Auftrag

Die in Teil 5 Block 2 gefundene strukturelle Luecke schliessen: Lager-/Lieferanbindung des
Verkaufs soll wie in Odoo 11 grundsaetzlich vorhanden und funktionsfaehig sein
(Installation von `stock`, `stock_account`, `sale_stock`), danach Pruefung der Felder
`warehouse_id`, `picking_ids`, `delivery_count` und der Lieferfunktion, echter Testauftrag mit
Bereinigung, Browserpruefung auf der VM, Regressionstest Verkauf und Abonnements.

## 2. Durchgefuehrte Aenderungen (nur Odoo 18)

```
a) itk_product 18.0.1.0.2 -> 18.0.1.0.3
   Feld product.template.responsible_id wird identisch zum Odoo-18-Standard definiert
   (company_dependent=True, check_company=True). Vorher brach die Installation von sale_stock mit
   "cannot cast type integer to jsonb" ab, weil das Modul stock dasselbe Feld
   unternehmensabhaengig (jsonb) fuehrt. Beschriftung "Verantwortlich" bleibt erhalten,
   die Feldbedeutung (Odoo-11-Feld "Verantwortlich") unveraendert.
b) Datenbankschema (nur Testdatenbanken, Spalte war leer):
   ALTER TABLE product_template DROP COLUMN responsible_id;  (lokal und VM, je 23 Produkte,
   0 belegte Werte) - damit Odoo die Spalte beim Upgrade neu als jsonb anlegt.
c) Module installiert: sale_stock 18.0.1.0 (zieht stock 18.0.1.1 und stock_account 18.0.1.1 mit)
   - lokal: sofort erfolgreich
   - VM: zunaechst Abbruch "missing tax tag +KZ 124 Bemessungsgrundlage for country Austria.
     You should probably update your localization app first." -> Ursache: veralteter Datenstand der
     Lokalisierung. Nach Upgrade von l10n_at (18.0.3.2.1, unveraenderte Version) lief die
     Installation fehlerfrei.
d) project_stock 18.0.1.0 zusaetzlich auf der VM installiert
   Ursache: die VM hatte Datenreste (Ansicht stock.picking.form.inherit.project_stock) aus dem
   Modul project_stock, das auf der VM nicht installiert war; dadurch brach die Lieferansicht im
   Browser mit "stock.picking"."project_id" field is undefined ab. Lokal war das Modul installiert.
   Kein Verkaufsfunktionsumfang wurde entfernt.
e) delivery bleibt uninstalliert - genau wie in Odoo 11.
```

## 3. Pruefung der Felder und der Lieferfunktion (RPC, echte Testdaten)

```
Werkzeug: scripts/pruefe_verkauf_lieferung.py --instanz lokal|vm
Ablauf: Testprodukt (is_storable) + Verkaufsauftrag anlegen, bestaetigen, Lieferung pruefen,
        danach alles wieder loeschen und Bestandszahlen vergleichen.

Felder vorhanden (lokal und VM): sale.order warehouse_id, picking_policy, picking_ids,
  delivery_count, procurement_group_id; sale.order.line move_ids, qty_delivered
Ergebnis lokal 26 OK / 0 FEHL, VM 26 OK / 0 FEHL
Belege (VM): Auftrag S00207 (Testauftrag) -> Status sale, Lager "IT-Kommunal GmbH",
  Lieferpolitik direct, delivery_count 1, Lagerbeleg WH/OUT/00001 (confirmed) mit
  Ursprung S00207, Bewegung 2,00 x Testprodukt, verknuepft mit der Auftragsposition
Bereinigung: Lieferung storniert und geloescht, Auftrag storniert und geloescht, Produkt geloescht
  Bestand unveraendert (lokal 18 Auftraege / 0 Lagerbelege / 13 Produkte,
  VM 20 Auftraege / 0 Lagerbelege / 13 Produkte, kein Testprodukt zurueckgeblieben)
```

## 4. Browserpruefung auf der VM (echter Klick, mit Testauftrag)

```
Werkzeug: scripts/browser_verkauf_lieferung.py --instanz vm|lokal
Ergebnis: VM 14 OK / 0 FEHL, lokal 14 OK / 0 FEHL, 0 JavaScript-Fehler, 0 RPC-Fehler
Belege (VM): Auftragsformular zeigt Smart Button "1 Lieferung"; Gruppe "Weitere Informationen"
  enthaelt Lagerhaus und Versandbedingungen; Klick auf den Smart Button oeffnet den Lieferbeleg
  WH/OUT/00006 (Einzeltreffer oeffnet direkt das Formular) mit Lieferadresse, Vorgangsart
  "IT-Kommunal GmbH: Lieferauftraege", Position des Testprodukts, Menge 2,00 und
  Referenzbeleg S00212
Bereinigung nach der Pruefung: Testauftrag, Lieferbeleg und Testprodukt entfernt,
  Bestand unveraendert (VM 20 Auftraege, lokal 18 Auftraege)
Screenshots: Desktop/Odoo18-Abnahme-Session121/lieferung/ (01 bis 04, lokal und VM)
```

## 5. Regressionstest Verkauf und Abonnements

```
Werkzeug: scripts/abschluss_verkauf_regression.py (11 Prueflaeufe, lokal und VM)
Ergebnis: 886 OK / 0 FEHL, keine Regression
  menue 41, teil2 111, reiter 64, status 53, filter 199, ansichten 146, kalender 33,
  bericht kanaele 84, druckberichte 69, s117 Auftraege/Lageranbindung 67, s118 Abo 19
Nachgezogene Erwartungen (Folge der geschlossenen Luecke, keine Fehler):
  verify_s121_verkauf_teil2.py   picking_policy, warehouse_id, procurement_group_id, picking_ids,
     delivery_count, incoterm, move_ids, route_id gelten nicht mehr als "entfallen", sondern als
     vorhanden (Liste NEU_SEIT_TEIL5); incoterm und route_id zusaetzlich als Transformation
     dokumentiert (stock.incoterms -> account.incoterms, stock.location.route -> stock.route)
  verify_s121_verkauf_teil3_reiter.py   Gruppe "Lieferadresse" heisst in Odoo 18 jetzt "Lieferung"
     (Odoo-18-Standard nach Installation von sale_stock; vorher "Versand")
  verify_s117_auftraege.py       incoterm, warehouse_id, picking_ids gelten als vorhanden
     (Liste SEIT_TEIL5_VORHANDEN), incoterm nicht mehr in ENTFAELLT
  abschluss_verkauf_regression.py  Referenzwert s117 65 -> 67 (drei neue Pruefungen)
```

## 6. Ergebnis

```
Die in Block 2 gefundene Luecke ist geschlossen: Odoo 18 kann wie Odoo 11 Verkaufsauftraege mit
Lagerbezug fuehren und Lieferungen erzeugen (Felder, Smart Button, Lieferbeleg mit Position und
Verkaufsbezug, Warehouse und Lieferpolitik). Nachgewiesen per RPC und im echten Browser auf der VM.
Odoo-11-Daten wurden nicht uebernommen; alle Testdaten wurden wieder entfernt.
Odoo-18-Zusatzfunktionen blieben erhalten (u. a. vier Druckberichte, Auftrags- und
Aktivitaetenkalender, Abo-Funktionen, zusaetzliche Lager-/Lieferfunktionen).
Odoo 11 Prod wurde ausschliesslich lesend verwendet.
```
