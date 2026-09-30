# R6 - tag_ids / Modellwechsel crm.lead.tag -> crm.tag

Stand: 29.09.2026, Session 121. **Nur Analyse.** Odoo 11 ausschliesslich read-only.
In Odoo 18 wurde nichts geaendert - es war keine Aenderung erforderlich.

## 1. Definitionen und Verknuepfungstabellen

```
Odoo 11:
  sale.order.tag_ids   many2many -> crm.lead.tag   Tabelle sale_order_tag_rel  (order_id / tag_id)
  crm.lead.tag_ids     many2many -> crm.lead.tag   Tabelle crm_lead_tag_rel    (lead_id / tag_id)
Odoo 18:
  sale.order.tag_ids   many2many -> crm.tag        Tabelle sale_order_tag_rel  (order_id / tag_id)
  crm.lead.tag_ids     many2many -> crm.tag        Tabelle crm_tag_rel         (lead_id / tag_id)

Also: Die Verkaufstabelle behaelt in Odoo 18 denselben Namen und dieselben Spalten
(sale_order_tag_rel). Nur das Tag-Modell wurde umbenannt (crm.lead.tag -> crm.tag); die
Lead-Tabelle heisst in Odoo 18 crm_tag_rel (vorher crm_lead_tag_rel).
crm.tag fuehrt Name und Farbindex (0-11) - dieselbe Systematik wie Odoo 11 (color 0-11).
```

## 2. Bestand und Verwendung in Odoo 11 (gemessen)

```
Tag-Stammdaten: 44 Datensaetze (crm.lead.tag), Namen und Farben liegen vollstaendig vor
  (u. a. "Up-Sell" (Farbe 5), "Gemeindecloud" (4), "Mandanten-Anlage gesendet" (8),
   "Anonym-Portal", "IFG-Portal", "Organisation - ..." (10), "bis 10.000 EW" (11) usw.)

Verwendung im Verkauf:
  Auftraege gesamt                                  2.464
  Auftraege mit Stichwort                              1
    A-1900710 | Magistrat Linz | Auftragsdatum 25.07.2019 | Zustand "Abgebrochen"
    Stichwort "Up-Sell" | zuletzt geaendert 24.11.2020 durch Administrator
  -> Im Verkauf ist das Stichwort also praktisch unbenutzt; der einzige Datensatz ist ein
     stornierter Auftrag aus 2019.

Verwendung im CRM (nur zur Einordnung, Bereich Kundenverwaltung/CRM):
  Leads gesamt                                      6.968
  Leads mit Stichwort                               6.155
  haeufigste Stichworte: IFG-Portal 5.089 Leads, Verband 264, Organisation - Bildung und Kunst
    153, Webinar "Digitalisierung" 240130 123, Organisation - Gesundheit 118, Staedtebetrieb 116,
    Bundes- Landeseinrichtung 94, Organisation - Energie 82, Organisation - Tourismus 64 ...
  Diese Nutzung ist bereits in den CRM-Dokumenten beschrieben
  (docs/o11-o18-strukturvergleich-crm-verkaufschancen.md, ...-kundenverwaltung-crm.md:
  "crm.lead.tag -> crm.tag, Modell umbenannt, Tag-Stammdaten-Mapping noetig").
```

## 2b. Alle 44 Tags als migrationsrelevante Stammdaten (Entscheidung Anna)

Die Tags sind nicht nur fuer den Verkauf relevant - sie werden im CRM von 6.155 Leads genutzt.
Deshalb werden hier alle 44 Odoo-11-Tags mit Name, Farbindex und Nutzung dokumentiert. Sie werden
in der spaeteren Stammdatenmigration **zentral einmal** angelegt, damit Verkauf und CRM dieselben
Tags verwenden. **Jetzt wird nichts angelegt und nichts migriert.**

| Nr | Tag-Name (Odoo 11) | Farbindex | Leads | Auftraege | angelegt |
|---|---|---|---|---|---|
| 1 | Amtsweg.gv.at | 2 | 3 | 0 | 2022-12-06 |
| 2 | Angemeldet | 10 | 22 | 0 | 2024-01-09 |
| 3 | Anonym-Portal | 10 | 40 | 0 | 2025-05-15 |
| 4 | bis 100.000 EW | 11 | 0 | 0 | 2022-12-06 |
| 5 | bis 10.000 EW | 11 | 3 | 0 | 2022-12-06 |
| 6 | bis 1.000 MA | 11 | 0 | 0 | 2022-12-06 |
| 7 | bis 100 MA | 11 | 1 | 0 | 2022-12-06 |
| 8 | bis 15.000 EW | 11 | 3 | 0 | 2022-12-06 |
| 9 | bis 20.000 EW | 11 | 1 | 0 | 2022-12-06 |
| 10 | bis 2.000 MA | 11 | 0 | 0 | 2022-12-06 |
| 11 | bis 200 MA | 11 | 0 | 0 | 2022-12-06 |
| 12 | bis 25.000 EW | 11 | 1 | 0 | 2022-12-06 |
| 13 | bis 300.000 EW | 11 | 0 | 0 | 2022-12-06 |
| 14 | bis 50.000 EW | 11 | 1 | 0 | 2022-12-06 |
| 15 | bis 5.000 MA | 11 | 1 | 0 | 2022-12-06 |
| 16 | bis 500 MA | 11 | 1 | 0 | 2022-12-06 |
| 17 | Bundes- Landeseinrichtung | 10 | 94 | 0 | 2023-06-19 |
| 18 | Gemeindecloud | 4 | 1 | 0 | 2022-12-01 |
| 19 | Gemeindeverband | 10 | 0 | 0 | 2024-08-05 |
| 20 | Hinweis-Neu | 10 | 47 | 0 | 2023-06-20 |
| 21 | Hinweis-Portal | 11 | 16 | 0 | 2022-12-01 |
| 22 | IFG-Portal | 10 | 5089 | 0 | 2025-02-14 |
| 23 | Mandanten-Anlage gesendet | 8 | 1 | 0 | 2022-12-05 |
| 24 | Mandaten angelegt | 0 | 1 | 0 | 2022-12-06 |
| 25 | öffentliche Einrichtung | 10 | 0 | 0 | 2024-08-05 |
| 26 | OGD Publikationsservice | 10 | 13 | 0 | 2023-08-21 |
| 27 | Organisation - Bildung und Kunst | 10 | 153 | 0 | 2023-04-06 |
| 28 | Organisation - Energie | 10 | 82 | 0 | 2023-04-06 |
| 29 | Organisation - Gesundheit | 10 | 118 | 0 | 2023-04-06 |
| 30 | Organisation - Gewerbe | 10 | 15 | 0 | 2023-04-07 |
| 31 | Organisation - Lebensmittel | 10 | 4 | 0 | 2023-04-06 |
| 32 | Organisation - Tourismus und Freizeit | 10 | 64 | 0 | 2023-04-06 |
| 33 | Organisation - Wohn- und Bauwesen | 10 | 38 | 0 | 2023-04-06 |
| 34 | Sonstige | 10 | 0 | 0 | 2024-08-05 |
| 35 | Städtebetrieb | 10 | 116 | 0 | 2023-04-06 |
| 36 | Test Mail | 10 | 0 | 0 | 2023-04-12 |
| 37 | über 300.000 EW | 11 | 0 | 0 | 2022-12-06 |
| 38 | Unternehmen | 10 | 0 | 0 | 2024-08-05 |
| 39 | Up-Sell | 5 | 0 | 1 | 2019-08-27 |
| 40 | Verband | 10 | 264 | 0 | 2023-04-06 |
| 41 | Versand 2 | 10 | 1 | 0 | 2023-04-13 |
| 42 | Verwaltungsmanager | 10 | 0 | 0 | 2022-12-06 |
| 43 | VKÖ & VÖWG Mitglied | 11 | 0 | 0 | 2022-12-06 |
| 44 | Webinar "Digitalisierung" 240130 | 10 | 123 | 0 | 2024-02-01 |

```
Summe: 44 Tags | Leads mit Stichwort 6.155 | Auftraege mit Stichwort 1
Ohne jede Nutzung (13 Tags): bis 100.000 EW, bis 1.000 MA, bis 2.000 MA, bis 200 MA,
  bis 300.000 EW, ueber 300.000 EW, Gemeindeverband, oeffentliche Einrichtung, Sonstige,
  Unternehmen, Verwaltungsmanager, VKOe & VOeWG Mitglied, Test Mail
  -> Test- bzw. Altbestand; beim Anlegen mitfuehren oder bewusst weglassen (Entscheidung in der
     Stammdatenmigration).
Nur im Verkauf genutzt: Up-Sell (1 Auftrag A-1900710, Zustand Abgebrochen).
Farbindex: Odoo 11 nutzt 0, 2, 4, 5, 8, 10, 11 - Odoo 18 fuehrt denselben ganzzahligen
  Farbindex (Anzeige "Farbe"; Odoo 11 "Farbkennzeichnung").
```

## 3. Gegenstueck in Odoo 18 (gemessen)

```
crm.tag-Stammdaten in Odoo 18: 0 Datensaetze (Testbestand) -> es existiert noch kein Tag,
  auf den zugeordnet werden koennte.
Auftraege mit Stichwort in Odoo 18: 0 (Testbestand)
Leads mit Stichwort in Odoo 18:     0 (Testbestand)
Die Verknuepfungstabellen sind vorhanden und beschreibbar (sale_order_tag_rel / crm_tag_rel).
```

## 4. Transformationsregel (vorbereitet)

```
tag_ids wird NICHT ueber Odoo-11-IDs uebernommen, sondern ueber den TAG-NAMEN zugeordnet:
  1. Tag-Stammdaten in Odoo 18 ueber den Namen suchen
  2. fehlt der Tag: in Odoo 18 anlegen mit Name und Farbindex aus Odoo 11
  3. Verknuepfung ueber die Tabelle sale_order_tag_rel setzen (order_id / tag_id)
  Mehrdeutigkeit (mehrere Odoo-18-Tags mit gleichem Namen): nicht automatisch zuordnen, vorlegen.
Auswirkung im Verkauf: 1 Auftrag (A-1900710, Zustand "Abgebrochen") mit dem Stichwort "Up-Sell".
Auswirkung im CRM: 6.155 Leads mit Stichworten (Bereich Kundenverwaltung/CRM, dort dokumentiert);
  die 44 Tag-Stammdatensaetze werden fuer die Zuordnung benoetigt.
Einordnung nach der Statusliste: "umbenannt" (Modell) bzw. "Transformationsregel erforderlich"
  fuer die Zuordnung ueber den Namen. Keine Aenderung an Odoo 18 erforderlich.
```

## 5. Nachweise

```
Odoo 11: fields_get und ir.model.fields (Feld, Relation, Verknuepfungstabelle, Spalten),
  crm.lead.tag (44 Datensaetze mit Name und Farbe), search_count je Tag auf sale.order und
  crm.lead, Detaildatensatz A-1900710
Odoo 18: ir.model.fields (Tabellen und Spalten), crm.tag-Bestand, Verwendung auf sale.order
  und crm.lead, Beschreibbarkeit der Verknuepfungstabellen
Bestand unveraendert: lokal 18 Auftraege / 28 Zeilen / 13 Produkte, VM 20 / 29 / 13
Keine Datenmigration, keine Aenderung an Odoo 18.
```

## 6. Entscheidungen von Anna (29.09.2026) und Status

```
a) Transformationsregel BESTAETIGT: tag_ids wird spaeter NICHT ueber Odoo-11-IDs uebernommen.
   Zuordnung ausschliesslich ueber den Tag-NAMEN:
     - vorhandenen Tag in Odoo 18 ueber den Namen suchen
     - falls nicht vorhanden: mit Name und Farbindex aus Odoo 11 anlegen
     - Verknuepfung anschliessend ueber sale_order_tag_rel (Verkauf) bzw. die passende
       Odoo-18-Relation (crm_tag_rel fuer Leads) herstellen
     - bei mehreren gleichnamigen Tags NICHT automatisch zuordnen, sondern als Konflikt melden
b) Umfang der Stammdaten BESTAETIGT: Die 44 tatsaechlich vorhandenen Odoo-11-Tags sind
   migrationsrelevante Stammdaten und werden vollstaendig dokumentiert (Abschnitt 2b, mit Name,
   Farbindex und Nutzung) - nicht nur der im Verkauf verwendete Tag "Up-Sell", weil die Tags im
   CRM von 6.155 Leads genutzt werden.
   Weiterhin gilt: JETZT keine Tags anlegen und keine Daten migrieren. Vorbereitet werden nur
   Mapping-Regel, Namen/Farbindex sowie die Abhaengigkeit zum CRM; die eigentliche
   Stammdatenmigration erfolgt spaeter ZENTRAL EINMAL, damit Verkauf und CRM dieselben Tags
   verwenden.

STATUS: R6 ABGESCHLOSSEN (29.09.2026) - analysiert (read-only in Odoo 11), Mapping-Regel und
  Stammdatenumfang festgehalten, alle 44 Tags dokumentiert, Entscheidungen eingetragen.
  Es war KEINE Aenderung an Odoo 18 erforderlich; kein Tag angelegt, keine Datenmigration.
Der Bereich Verkauf bleibt bis zur Vorbereitung der Risiken R7 und R8 weiterhin NICHT endgueltig
abgeschlossen.
```
