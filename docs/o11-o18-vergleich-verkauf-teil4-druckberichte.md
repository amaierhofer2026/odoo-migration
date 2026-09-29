# Odoo 11 -> Odoo 18: Bereich Verkauf, Teil 4, Druckberichte (Abschluss Teil 4)

Stand: 29.09.2026, Session 121. Odoo 11 Prod (`portal.it-kommunal.at`, DB `ITK_V1_a`) wurde
ausschliesslich lesend gelesen. Aenderungen nur in Odoo 18. Keine Datenmigration.

Pruefwerkzeuge:
`scripts/analyse_verkauf_teil4_druckberichte.py` (Bestandsaufnahme, Rohdaten `docs/_verkauf_teil4_druckberichte.json`),
`scripts/vergleiche_verkauf_teil4_itk_bericht_aktiv.py` (Inhaltsvergleich ohne HTML-Kommentare),
`scripts/verify_s121_verkauf_teil4_druckberichte.py` (Prueflauf Odoo 11/lokal/VM),
`scripts/browser_verkauf_druckberichte.py` (echter Browser, PDF-Download und Inhaltspruefung).

## 1. Vorhandene Verkaufsberichte in Odoo 11 und tatsaechliche Verwendung

```
Report-Aktionen auf sale.order (Odoo 11):
  id   Name                     Reportname                            Bindung ins Menue Drucken
  ...  Angebot/Auftrag          sale.report_itk_saleorder             ja (sale.order)
  ...  Angebot / Auftrag ORG    sale.report_itk_saleorder             nein (binding_model_id leer)
  ...  Proformarechnung         sale.report_itk_saleorder_proforma    ja (sale.order)

Formular: zwei "Drucken"-Knoepfe (name="print_quotation", einmal states="draft",
  einmal states="sent,sale") - beide rufen den ITK-Bericht, Berichtsname sale.report_itk_saleorder,
  Papierformat European A4, Anhangsspeicherung ueberall aus (attachment_use = False).

Dokumentvorlage (Kern des Berichts):
  sale.report_itk_saleorder_document, aktiv 24.198 Zeichen (27.140 Zeichen inklusive
  auskommentiertem Code des alten Odoo-Standardberichts)
  Aufbau: Briefkopf/Firmenadresse (doc.company_id.partner_id...), Anschreiben (community_salutation,
  "Zu Handen" + sale_contact_id.attention_of), Datum mit Beschriftung
  ("Angebotsdatum"/"Auftragsdatum"/"Datum Proformarechnung"), Titel (Angebot/Auftrag/Proformarechnung
  in Abhaengigkeit von state), Infoblock rechts (Zahlung, Bearbeiter/in, Waehrung, Ihre UID-Nr.),
  Einleitungstext nach Status, Positionstabelle, Summenblock, Schlusstext nach Status,
  interne Bemerkung (note), Zahlungsbedingungen-Hinweis, Steuerzuordnungshinweis
  Spaltenkoepfe: Pos, Leistungsgegenstand, Menge, Einzelpreis, Rabatt, Gesamtpreis
    (eine Spalte "Steuern" und "Preis" ist im Odoo-11-Standard vorhanden, aber auskommentiert -> nie sichtbar)
  Statusabhaengigkeit: state not in ['draft','sent'] -> "Auftrag" + Beauftragungstext,
    state in ['draft','sent'] -> "Angebot" + Angebotstext
  Summenblock: Nettosumme (doc.amount_untaxed), Steuerzeilen (amount_by_group, u. a. "20,00 % auf ..."),
    Gesamtsumme (doc.amount_total), Waehrung aus doc.pricelist_id.currency_id
  Proformarechnung: eigene Vorlage sale.report_itk_saleorder_proforma (346 Zeichen),
    ruft dieselbe Dokumentvorlage mit is_pro_forma = True -> Titel "Proformarechnung",
    kein Einleitungs- und kein Schlusstext

"Angebot / Auftrag ORG" ist eine Altlast: eigener Menueeintrag, aber identischer Reportname
und ohne Bindung -> im Drucken-Menue nicht sichtbar, fachlich also nicht verwendet.
```

## 2. Druckberichte in Odoo 18 (Status quo, unveraendert)

```
Report-Aktionen auf sale.order (Odoo 18, lokal und VM identisch):
  Name                    Reportname                              Bindung ins Menue Drucken
  Angebot/Auftrag         sale.report_saleorder_raw               ja
  ITK-Angebot/Auftrag     itk_reports.report_itk_saleorder        ja
  PDF-Angebot             sale.report_saleorder                   ja
  PRO-FORMA-Rechnung      sale.report_saleorder_pro_forma         ja

Dokumentvorlage itk_reports.report_itk_saleorder_document: aktiv 7.169 Zeichen (Neuimplementierung
in Odoo-18-Schreibweise), Aufbau wie in Odoo 11 uebernommen:
  community_salutation + "Zu Handen" (sale_contact_id.attention_of), Strasse/Strasse2/PLZ/Ort,
  Datum (date_order) rechts, Titel nach state, Infoblock (Zahlung, Bearbeiter/in, Waehrung,
  Ihre UID-Nr.), Einleitungstext nach Status, Positionstabelle mit denselben Spaltenkoepfen,
  Summenblock ueber den Odoo-18-Standardbaustein account.document_tax_totals (doc.tax_totals),
  Schlusstext nach Status, note, Zahlungsbedingungen-Hinweis, Steuerzuordnungshinweis
Vorhanden, aber nicht gebunden: itk_reports.report_itk_saleorder_proforma
  (ITK-Proformavorlage; das Menue Drucken nutzt fuer die Proforma den Odoo-18-Standardbericht)
```

## 3. Zuordnung Bericht fuer Bericht

| Odoo 11 | gebunden | Odoo 18 | gebunden | Bewertung |
|---|---|---|---|---|
| Angebot/Auftrag (ITK-Dokument) | ja | ITK-Angebot/Auftrag | ja | fachlich gleichwertig, Inhalte 1:1 vorhanden |
| (Formularknopf "Drucken") | - | PDF-Angebot (sale.report_saleorder) | ja | Odoo-18-Standard, zusaetzlich erhalten |
| - | - | Angebot/Auftrag (sale.report_saleorder_raw) | ja | Odoo-18-Zusatz, erhalten |
| Proformarechnung (ITK-Dokument) | ja | PRO-FORMA-Rechnung (Odoo-18-Standard) | ja | Proforma vorhanden; Layout weicht ab (siehe 4.3) |
| Angebot / Auftrag ORG | nein | - | - | Altlast ohne Inhalt, kein Nachbau noetig |

## 4. Unterschiede, die dokumentiert bleiben (keine Aenderung vorgenommen)

```
4.1 Summenbeschriftungen: Odoo 11 "Nettosumme"/"Gesamtsumme" (eigener Tabellenblock),
    Odoo 18 "Nettobetrag"/"Gesamt" (Standardbaustein account.document_tax_totals).
    Die Betraege selbst sind identisch (Netto, Steuersatz mit Steuerbetrag, Gesamt).
4.2 Datumsbeschriftung: Odoo 11 beschriftete das Datum ("Angebotsdatum", "Auftragsdatum",
    "Datum Proformarechnung"), Odoo 18 zeigt das Datum ohne Beschriftung (date_order).
4.3 Proformarechnung: Odoo 11 druckte die Proforma im ITK-Brieflayout (ITK-Dokumentvorlage mit
    is_pro_forma = True), Odoo 18 nutzt fuer den Menueeintrag den Odoo-18-Standardbericht
    (Titel "Pro-forma-Rechnung", eigene Spalten inkl. Steuern, Nettobetrag/Gesamt).
    Die ITK-Proformavorlage ist in Odoo 18 vorhanden, aber an keine Report-Aktion gebunden.
    Fachlich ist eine Proforma damit druckbar; das ITK-Layout ist nicht aktiv.
4.4 Auskommentierter Code der Odoo-11-Vorlage (alter Standardbericht, etwa 3.000 Zeichen mit
    Spalten "Steuern"/"Preis", Layoutkategorien-Summen) wurde nicht uebernommen - war nie sichtbar.
4.5 Firmenadresse im Anschreiben: Odoo 11 rendert sie aus doc.company_id.partner_id,
    Odoo 18 ueber das externe Layout (Briefkopf); im PDF sichtbar geprueft.
```

## 5. Browser-Abnahme (echter Browser, PDF-Download und Inhalt)

```
Werkzeug: scripts/browser_verkauf_druckberichte.py --instanz lokal|vm
  Testauftraege: Entwurf/gesendet S00189 (Gesamt 72,00) und bestaetigt
                 lokal S00200 / VM S00203 (Netto 24,00 + Steuer 4,80 = Gesamt 28,80)

Ergebnis: lokal 41 OK / 0 FEHL, VM 41 OK / 0 FEHL, 0 JavaScript-Fehler, 0 RPC-Fehler

Menue Drucken (Zahnrad -> Drucken) auf der VM, sichtbar und anklickbar:
  Angebot/Auftrag, ITK-Angebot/Auftrag, PDF-Angebot, PRO-FORMA-Rechnung
Report-Aktion je Eintrag (ueber die Server-Anfrage belegt):
  Angebot/Auftrag -> sale.report_saleorder_raw
  ITK-Angebot/Auftrag -> itk_reports.report_itk_saleorder
  PDF-Angebot -> sale.report_saleorder
  PRO-FORMA-Rechnung -> sale.report_saleorder_pro_forma
PDF je Eintrag erzeugt (19.727 bis 21.281 Bytes), Inhalt ausgelesen:
  ITK-Angebot (Entwurf/gesendet): Titel "Angebot S00189", Angebotstext, kein Auftragstext,
    Kunde "Test Firma", Gesamt 72,00, Summenblock, Block Zahlung/Bearbeiter/in/UID
  ITK-Auftrag (bestaetigt, VM S00203): Titel "Auftrag S00203", Beauftragungstext und Schlusstext,
    Kunde mit PLZ/Ort, Position "Abo_Amtssignatur Test", Nettobetrag 24,00, Steuer 20% 4,80,
    Gesamt 28,80, Datum 22.09.2026
  PRO-FORMA-Rechnung: Titel "Pro-forma-Rechnung" (Odoo-18-Wortlaut), kein Auftragstext,
    Kunde und Gesamt 28,80 vorhanden
  Angebot/Auftrag und PDF-Angebot: Auftragsnummer und Gesamt 28,80 vorhanden
Formular: Knopf "Vorschau" weiterhin vorhanden, Formular ohne Fehleranzeige
```

## 6. Teil 4 - Abschluss

```
Teil 4, Schritt 1  Listen-/Kanban-/Pivot-/Graph-/Kalenderansichten   ABGENOMMEN (lokal und VM)
  inkl. Kalenderergänzung "Auftragskalender" (Option A)              Modul 18.0.1.5.0, PR #113/#114
Teil 4, Schritt 2  Bericht "Verkaufsaufträge aller Kanäle"           ABGENOMMEN (lokal und VM)
                   auf Basis sale.report                             Modul 18.0.1.6.0, PR #116/#117
Teil 4, Schritt 3  Druckberichte (dieses Dokument)                   ABGENOMMEN (lokal und VM)
                   keine Modulaenderung noetig (keine Odoo-11-Funktion fehlt)

Ergebnis Teil 4: alle in Odoo 11 vorhandenen und verwendeten Ansichten, Berichte und
Druckberichte des Verkaufs sind in Odoo 18 vorhanden und im echten Browser auf der VM geprueft.
Odoo-18-Zusatzfunktionen wurden nicht entfernt; es wurde in diesem Schritt nichts geaendert.
Odoo 11 Prod wurde ausschliesslich lesend verwendet, keine Datenmigration.
```

Offen zur Entscheidung (nicht blockierend): Punkt 4.3 - soll die vorhandene ITK-Proformavorlage
zusaetzlich an einen Menueeintrag "ITK-Proformarechnung" gebunden werden (der Odoo-18-Eintrag
"PRO-FORMA-Rechnung" bleibt dabei erhalten)?
