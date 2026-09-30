# Gesamtstatus R1 bis R8: Migrationsrisiken im Bereich Verkauf

Stand: 29.09.2026, Session 121. Alle acht Risiken aus dem gezielten Migrations-Check sind
analysiert und technisch vorbereitet. **Es wurden keine Odoo-11-Daten migriert.** Odoo 11 Prod
(`portal.it-kommunal.at`, DB `ITK_V1_a`) wurde ausschliesslich lesend verwendet.

Grundlagen:
- `docs/o11-o18-verkauf-migrationscheck.md` (Risikoliste R1-R8)
- `docs/o11-o18-verkauf-migrationscheck-felder.md` (Feldzuordnung, Detailtabelle)
- Einzeldokumente je Risiko (unten verlinkt)

## 1. Uebersicht: Risiko, finale Regel, Abhaengigkeit

| Nr | Gegenstand | Finale Regel | Odoo-18-Aenderung | Betroffene Datensaetze (Odoo 11) | Abhaengigkeit |
|---|---|---|---|---|---|
| R1 | Mengeneinheiten (`product_uom`) | Zuordnung ueber den NAMEN, nie ueber IDs; `Einheit(en)`/`ITK Einheit` Rundung 0,001, Genauigkeit 3; `GB` eigener Bereich "Datenmenge" (Gigabyte, keine Umrechnung zu Liter); 7 historische "NN Gemeinden"-Einheiten bleiben und werden 1:1 nach Namen zugeordnet (nicht auf `Einheit(en)` zusammenfuehren) | **Ja, umgesetzt** (Genauigkeit 2 -> 3, zwei Rundungen, 8 Einheiten angelegt) | 4.011 Zeilen / 13 Einheiten | Stammdaten (Einheiten) |
| R2 | `price_reduce` | Nicht nachbauen, nicht migrieren - Wert wird aus `price_unit`, `discount`, `product_uom_qty`, `tax_id`, `currency_id` neu berechnet (`price_reduce_taxexcl` / `price_reduce_taxinc`) | Nein | 3.980 Zeilen | keine |
| R3 | Zustand `done` | `done` -> `state='sale'` + `locked=True`; alle anderen Zustaende 1:1; bei `sale` wird `locked` NICHT automatisch gesetzt; Wortlaut "Storniert" bleibt | Nein | 0 Auftraege in `done` (Fallback-Regel) | keine |
| R4 | `note` (TEXT -> HTML) | Umwandlung mit der Odoo-18-Standardfunktion `odoo.tools.mail.plaintext2html` (maskieren, Umbrueche erhalten, URLs als Links, Inhalt unveraendert) | Nein | 3 Auftraege mit echtem Text | keine |
| R5 | `invoice_lines` (Modellwechsel) | Keine Wertuebernahme: Verknuepfung ueber `sale_order_line_invoice_rel` wiederherstellen, Zuordnung ueber stabilen fachlichen Schluessel (Rechnungsnummer, Position, ggf. Produkt/Auftragszeilenbezug), nie ueber IDs; erst wenn Rechnungen vorhanden und eindeutig zuordenbar sind | Nein | 1.863 Zeilen aus 1.201 Rechnungen, 1.198 Auftraege | **Rechnungen/Abrechnung** |
| R6 | `tag_ids` (`crm.lead.tag` -> `crm.tag`) | Zuordnung ausschliesslich ueber den Tag-NAMEN; fehlende Tags mit Name und Farbindex anlegen; Verknuepfung ueber `sale_order_tag_rel` bzw. `crm_tag_rel`; gleichnamige Tags als Konflikt melden; die 44 Tags sind migrationsrelevante Stammdaten und werden zentral einmal angelegt | Nein | 1 Auftrag mit Stichwort; 44 Tags (CRM: 6.155 Leads) | **CRM/Stammdaten** |
| R7 | `layout_category_id` / `_sequence` | Bewusst NICHT migrieren (Modell `sale.layout.category` in Odoo 11 nicht registriert, ITK-Vorlage ohne Sektion, Sequenz nie genutzt); keine kuenstlichen Abschnittszeilen anlegen | Nein | 2 Zeilen (Sektion "Dienstleistungen") | keine |
| R8 | `amt_invoiced` / `amt_to_invoice` | Keine Wertuebernahme (in Odoo 18 berechnet, nicht speicherbar); Odoo 18 berechnet aus den migrierten, GEBUCHTEN Rechnungszeilen; Verknuepfung nach R5 | Nein | 1.669 / 1.950 Zeilen | **Rechnungen/Abrechnung, R5** |

Einzeldokumente:
`docs/o11-o18-verkauf-r1-mengeneinheiten.md`, `...-r2-preis-reduziert.md`,
`...-r3-status-done.md`, `...-r4-note-html.md`, `...-r5-invoice-lines.md`,
`...-r6-tag-ids.md`, `...-r7-layout-category.md`, `...-r8-invoiced-amounts.md`.

## 2. Abhaengigkeiten zu anderen Bereichen

```
Abrechnung / Rechnungen (zentral):
  - R5: Die Verknuepfung Auftragszeile <-> Rechnungszeile kann nur entstehen, wenn die Rechnungen
    und Rechnungszeilen in Odoo 18 vorhanden und eindeutig zuordenbar sind (Tabelle
    sale_order_line_invoice_rel, Zuordnung ueber Rechnungsnummer + Position).
  - R8: amount_invoiced / amount_to_invoice werden von Odoo 18 aus den verknuepften, GEBUCHTEN
    Rechnungszeilen berechnet. Ohne Rechnungsmigration bleibt amount_invoiced 0, amount_to_invoice
    zeigt den offenen Betrag, invoice_status kann "to invoice" lauten - dokumentierte Erwartung,
    nicht als Migrationsfehler zu deuten. Ziel bleibt, die historischen Rechnungsbezuege zu
    erhalten, damit die Werte identisch zu Odoo 11 berechnet werden.
  - R2: price_reduce_taxinc rechnet die Steuern mit; die Neuberechnung setzt die migrierten
    Steuerzuordnungen voraus (Steuersaetze/Steuerkonten aus der Buchhaltung).
CRM / Stammdaten:
  - R6: Die Tags werden von Verkauf UND CRM genutzt. Sie werden in der Stammdatenmigration
    zentral einmal angelegt; danach ordnen Verkauf und CRM dieselben Tags zu.
  - R1: Die Mengeneinheiten sind Stammdaten (inklusive der 8 in Odoo 18 neu angelegten).
Lager:
  - keine offene Abhaengigkeit (Lageranbindung wurde in Teil 5 Block 2 geschlossen).
```

## 3. Was nur vorbereitet ist und erst bei der echten Datenmigration greift

```
ALLE Regeln R1-R8 sind bisher nur REGELN - es wurde kein einziger Odoo-11-Datensatz uebernommen.
Sie greifen erst, wenn Anna die Datenmigration freigibt:
  R1  Einheiten-Mapping anwenden (Name -> Name), Mengen unveraendert uebernehmen
  R2  price_reduce nicht schreiben, Odoo 18 rechnet aus price_unit/discount
  R3  locked nur setzen, wenn der Odoo-11-Auftrag tatsaechlich 'done' war
  R4  note beim Schreiben in HTML umwandeln
  R5  Verknuepfung Auftragszeile <-> Rechnungszeile herstellen (nach Rechnungsmigration)
  R6  Tags ueber den Namen zuordnen (Anlage der 44 Tags zentral in der Stammdatenmigration)
  R7  layout_category_id/_sequence nicht uebernehmen
  R8  amount_invoiced / amount_to_invoice nicht schreiben - Odoo 18 berechnet sie
Ebenfalls nicht uebernommen werden berechnete Felder wie qty_invoiced, amount_untaxed,
  amount_total, price_subtotal, invoice_status (werden von Odoo 18 aus Positionen, Steuern und
  Rechnungen ermittelt).

In Odoo 18 wurde bisher NUR R1 umgesetzt (Dezimalgenauigkeit "Product Unit of Measure" 2 -> 3,
Rundung "Einheit(en)" und "ITK Einheit" 0,01 -> 0,001, 8 Einheiten angelegt: GB in der Kategorie
"Datenmenge" und die sieben "NN Gemeinden"-Einheiten). R2 bis R8 erforderten KEINE Aenderung an
Odoo 18. Alle Odoo-18-Zusatzfunktionen sind unveraendert erhalten.
```

## 4. Bestaetigung: keine Odoo-11-Daten migriert

```
- Odoo 11 wurde ausschliesslich read-only verwendet (RPC-Lesen, Felder-/Ansichtsanalyse,
  Zaehlungen, read_group). Keine Schreib-, Aenderungs-, Loesch- oder Upgrade-Operation.
- Es wurden keine Stammdaten, Auftraege, Produkte, Preise, Einheiten, Tags oder Rechnungen aus
  Odoo 11 nach Odoo 18 uebernommen.
- Alle Testdaten der Analysen (Testauftraege, Testrechnungen, Testprodukte) wurden nach der
  Pruefung wieder entfernt.
Bestand (unveraendert, geprueft):
  lokal  18 Auftraege | 28 Auftragszeilen | 13 Produkte | 15 Kunden | 37 Rechnungen | 0 Lagerbelege
  VM     20 Auftraege | 29 Auftragszeilen | 13 Produkte | 15 Kunden |  0 Lagerbelege
  37 Einheiten (lokal und VM), 12 Zahlungsbedingungen, 8 Verkaufsteams, 0 crm.tag-Datensaetze
Berechnete Werte wurden nie direkt geschrieben - auch nicht waehrend der Tests (ausserhalb der
  Testdatensaetze, die wieder entfernt wurden).
```

## 5. Pruefstand nach R1-R8

```
Regression Verkauf + Abonnements: 886 OK / 0 FEHL (11 Prueflaeufe, lokal und VM)
R1-Pruefung Mengeneinheiten:      64 OK / 0 FEHL (lokal und VM)
R2-Pruefung price_reduce:          9 OK / 0 FEHL je Instanz
Browser-Gesamtdurchgang auf der VM (echter Browser, Abnahmeumgebung):
  43 OK / 0 FEHL, 0 JavaScript- und 0 RPC-Fehler
View-Gesundheit: alle vorhandenen Ansichtstypen je Modell laden fehlerfrei, keine offenen
  View-Fehler; keine Meldungen zu ungueltigen Ansichten in den Server-Logs
```

## 6. Abschlussmarkierung und Reihenfolge der spaeteren Datenmigration

```
ABSCHLUSSMARKIERUNG (Entscheidung Anna, 29.09.2026):
  VERKAUF: FUNKTIONAL VOLLSTAENDIG UND MIGRATIONSVORBEREITET.
  Die Regeln R1-R8 sind ausschliesslich vorbereitete Regeln fuer die spaetere Datenmigration und
  KEINE offenen Funktionsluecken im Odoo-18-Verkaufsmodul.

Reihenfolge fuer die spaetere Datenmigration (dokumentiert, NICHT ausgefuehrt):
  1. Stammdaten zuerst - insbesondere Mengeneinheiten (R1) und Tags (R6)
  2. danach Auftraege und Auftragszeilen
  3. Rechnungen/Rechnungszeilen im Bereich Abrechnung migrieren
  4. danach die Verknuepfung Auftragszeile <-> Rechnungszeile gemaess R5 herstellen
  5. berechnete Felder wie amount_invoiced, amount_to_invoice und invoice_status anschliessend
     von Odoo 18 neu berechnen lassen (R8)

Es wurden keine Odoo-11-Daten migriert; Odoo 11 wurde ausschliesslich read-only verwendet.
Offene funktionale oder strukturelle Punkte im Bereich Verkauf: keine.
```
