# Odoo 11 gegen Odoo 18 - Bereich Abrechnung, Teil 6: Berichte (Vorgabe K3)

Stand: 30.09.2026, Session 122. Analyse; es wurde nichts migriert, Odoo 11 nur gelesen.
Vorgabe K3: die acht Odoo-11-Berichte nicht nachbauen, zuerst Nutzung und Inhalt feststellen.

## 1. Die acht Berichts-Assistenten aus Odoo 11 (Berichtswesen / PDF Berichte)

| Odoo-11-Aktion | Bezeichnung | Modell (Odoo 11) | Inhalt |
| --- | --- | --- | --- |
| act 262 | Audit Journale | account.print.journal | Journalauszug je Journal und Periode |
| act 263 | Partner-Kontoauszug | account.report.partner.ledger | Kontobewegungen je Partner |
| act 264 | Umsaetze nach Konten und Perioden | account.report.general.ledger | Summen- und Saldenliste je Konto |
| act 265 | Vorlaeufige Bilanz | account.balance.report | Salden je Konto (vorlaeufig) |
| act 266/267/268 | Bilanz, Gewinn und Verlust, Finanzberichte | accounting.report | Bilanz, GuV, Kennzahlen |
| act 269 | alter Partner Saldo | account.aged.trial.balance | Offene Posten nach Faelligkeit |
| act 276 | Steuerberichte | account.tax.report | Steuersummen je Periode |
| act 227 | Finanzberichte (Verwaltung) | account.financial.report | Berichtsdefinitionen |

Nutzung: nicht rekonstruierbar. Odoo 11 (Community) fuehrt kein Protokoll ueber ausgeführte
Berichte; die 12.350 Anhaenge enthalten keine Belegdateien mit Berichtsnamen (geprueft auf
"Aged Partner", "Partner Ledger", "Trial Balance", "Balance Sheet", "General Ledger",
"Tax Report", "Journal Audit").

Verfuegbarkeit in Odoo 18: keines dieser acht Modelle existiert (account.print.journal,
account.report.partner.ledger, account.report.general.ledger, account.balance.report,
accounting.report, account.aged.trial.balance, account.tax.report, account.financial.report
fehlen). Das Enterprise-Berichtsmodul ist auf der Testumgebung nicht verfuegbar
(Modul "accountant" = uninstallable). Damit gilt der Befund aus Teil 1: die acht PDF-Berichte
sind mit Odoo 18 Community nicht reproduzierbar und bleiben als offener
Infrastruktur-/Lizenzpunkt dokumentiert (Entscheidung Anna).

## 2. Rechnungsdruck in beiden Systemen

```
Odoo 11 (account.invoice):
  id 537  Rechnung                     itk_reports.report_itk_invoice                 (ITK)
  id 538  Rechnung mit Zahlung         itk_reports.report_itk_invoice_with_payments   (ITK)
  id 230  Rechnungen ORG               account.report_invoice_with_payments           (Odoo)
  id 231  Rechnungen ohne Zahlung ORG  account.report_invoice                         (Odoo)
Odoo 18 (account.move):
  id 1231 ITK-Rechnung                 itk_reports.report_itk_invoice                 vorhanden, gebunden
  id 323  PDF-Rechnung                 account.report_invoice_with_payments           vorhanden
  id 325  PDF ohne Zahlung             account.report_invoice                         vorhanden, gebunden
  id 324  Originalrechnungen           account.report_original_vendor_bill            vorhanden (Eingangsbelege)
  id 406  von Odoo erstellter Rechnungsbericht (account_edi_ubl_cii)                 Zusatzfunktion
Browser-Nachweis (Teil 4): das Drucken-Menue der Rechnungsliste zeigt PDF | PDF ohne Zahlung | ITK-Rechnung.
```

Ergebnis: Die ITK-Rechnungsvorlage ist portiert und im Browser nachgewiesen. Nicht portiert ist
die Odoo-11-Vorlage "Rechnung mit Zahlung" (id 538, gleicher ITK-Briefkopf, zusaetzlich die
Zahlungen im PDF). Die Odoo-18-Vorlage "PDF-Rechnung" (323) enthaelt die Zahlungen, aber im
Odoo-Standardlayout ohne ITK-Briefkopf.

## 3. Umgesetzt: ITK-Rechnung mit Zahlung (30.09.2026)

Der fehlende Bericht wurde als Community-/ITK-Bericht nachgebaut (Modul `itk_reports`, Version
18.0.1.4.0):

```
Vorlage   : itk_reports.report_itk_invoice_document_with_payments (Zahlungsblock ergaenzt)
Aktion    : itk_reports.action_report_itk_invoices_with_payments, Name "ITK-Rechnung mit Zahlung",
            gebunden an account.move (erscheint im Drucken-Menue)
Inhalt    : wie Odoo 11 (Bericht id 538): zuerst die geleisteten Zahlungen
            ("Bezahlt am <Datum>" mit Betrag), danach der offene Betrag, wenn Zahlungen
            vorhanden sind. Datenquelle: invoice_payments_widget (Odoo 18).
Layout    : identisch zum bestehenden ITK-Rechnungsbericht (ITK-Briefkopf), nur mit Zahlungsblock.
Nachweis lokal: /report/html und /report/pdf fuer RE/2026/0001 und RE/2026/0002 ->
            "Bezahlt am" und "Offener Betrag" enthalten, PDF 27 KB mit PDF-Kennung;
            der alte Bericht ohne Zahlungen zeigt beides nicht (Vergleich).
Nachweis VM (Browser): Drucken-Menue der Rechnungsliste zeigt PDF | PDF ohne Zahlung |
            ITK-Rechnung | ITK-Rechnung mit Zahlung; Klick erzeugt "ITK-Rechnung mit Zahlung.pdf"
            (4 OK / 0 FEHL).
Odoo-18-Zusatzfunktionen (PDF-Rechnung, PDF ohne Zahlung, Originalrechnungen, EDI-Bericht)
            bleiben unveraendert erhalten.
```

## 3a. Weitere Vorbereitung fuer Odoo 18
2. Acht Berichts-Assistenten: nicht nachbauen. Wenn Berichtswesen gebraucht wird, ist das
   Enterprise-Modul (account_reports) die einzige belastbare Option; die Entscheidung ist
   fachlich/organisatorisch und liegt bei Anna.
3. Welche Vorlage in Odoo 11 fuer welche Rechnung gedruckt wurde, ist nicht gespeichert
   (kein Protokoll, keine Anhangsnamen); die Vorlagen selbst sind belegt.

## 4. Naechster Schritt

Punkt 1 (ITK-Vorlage mit Zahlungen) als naechste Umsetzung in Odoo 18, danach Abnahme im Browser
auf der VM.
