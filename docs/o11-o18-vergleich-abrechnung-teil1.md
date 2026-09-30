# Odoo 11 -> Odoo 18: Bereich Abrechnung, Teil 1 (Bestandsaufnahme)

Stand: 30.09.2026, Session 122
Status: **BESTANDSAUFNAHME ABGESCHLOSSEN - noch nichts umgebaut**

Vergleichsbasis: Odoo 11 Prod (`https://portal.it-kommunal.at`, DB `ITK_V1_a`) - **ausschliesslich
lesend** verwendet (search_count, search_read, fields_get, ir.model, ir.ui.menu).
Zielsysteme: Odoo 18 lokal (`http://localhost:8069`, DB `odoo18_test`) und VM
`https://k001959vsx.ipax.at` (Docker `odoo18`, DB `odoo18_test`).

Auftrag (Anna, 30.09.2026): Schritt 1 = nur Bestandsaufnahme: alle Menues und Untermenues in
Abrechnung Odoo 11 gegen Odoo 18, installierte relevante Module, tatsaechlich verwendete Bereiche
und Datenmengen, fehlende oder anders aufgebaute Funktionen. Kein Umbau vor Abschluss dieser
Aufnahme.

## 1. Wie gemessen wurde (und eine wichtige Lehre)

Werkzeuge (alle im Repo, read-only):

```
scripts/analyse_abrechnung_menue2.py       Menuebaum beider Systeme (vollstaendig)
scripts/analyse_abrechnung_teil1.py        Module + Modelle + Datensatzzahlen
scripts/analyse_abrechnung_nutzung.py      Nutzungszahlen (Belege, Zustaende, Journale, Stammdaten)
scripts/analyse_abrechnung_details.py      Feldnamen, Menueziele, fehlende Modelle
scripts/analyse_abrechnung_details2.py     Menuepfade je Aktion, Valorisierung, Kostenstellen
scripts/analyse_abrechnung_details3.py     Kostenstellenmenues, Ist-Versteuerung, Nummernkreis
scripts/analyse_abrechnung_details4.py     Feldumbenennungen, Anhaenge, Druckvorlagen
scripts/analyse_abrechnung_details5.py     Berichts-/Zahlungsmodelle beider Systeme
scripts/analyse_abrechnung_details6.py     Menues je Modell, Volumen je Jahr, Gegenprobe O18
scripts/vergleiche_abrechnung_lokal_vm.py  Odoo 18 lokal gegen VM (Menues + Modulversionen)
```

**Lehre (neuer Befund F56):** `ir.ui.menu` filtert bei `search_read` nach der Sichtbarkeit fuer den
angemeldeten Benutzer (`ir.ui.menu._search`). Ohne den Kontext `ir.ui.menu.full_list=True` zeigt
Odoo 11 nur 42 der tatsaechlich 70 Menues der App Abrechnung - alle gruppenbeschraenkten Zweige
(Finanzberater, Berichtswesen/PDF Berichte, Kontenplan, Journale) fehlten. **Menueinventare ab
jetzt immer mit `context={'lang':'de_DE','ir.ui.menu.full_list':True}` lesen**, sonst meldet der
Vergleich faelschlich "fehlendes Menue".

Rohdaten der Messungen liegen nur im Temp-Verzeichnis, nicht im Repo.

## 2. Installierte relevante Module

Installierte Module gesamt: Odoo 11 **130** | Odoo 18 lokal **171**.

```
Modul                          O11                 O18 (lokal = VM)     Bemerkung
account                        11.0.1.1 installed  18.0.1.3 installed   Kernmodul beider Seiten
account_invoicing              11.0.1.0 installed  -                     O11-App "Abrechnung"; in O18 in account aufgegangen
account_invoice_line_number    11.0.1.0.0 inst.    18.0.1.0.0 inst.     ITK-Positionsnummerierung, beide Seiten
account_invoice_line_report    nicht installiert   18.0.1.0.0 inst.     O18-Zusatzfunktion (Positionsbericht)
account_payment                nicht installiert   18.0.2.0 installed   O18: Zahlungsmethoden/Methoden-Zeilen
payment                        11.0.1.0 inst.      18.0.2.0 inst.       Online-Zahlungen (Basismodul)
payment_transfer               11.0.1.0 installed  -                    O11-Zahlungsanbieter "Bankueberweisung"
account_bank_statement_import  11.0.1.0 installed  -                    O11-Bankimport (0 Auszuege verwendet)
account_cash_basis_base_account 11.0.1.0 inst.     -                    O11-Ist-Versteuerung (Journal CABA, 0 Buchungen)
analytic                       11.0.1.1 inst.      18.0.1.2 inst.       Kostenrechnung
itk_valorisierung              11.0.0.1 inst.      18.0.1.0.0 inst.     ITK: Valorisierungstexte
mass_email_invoice             11.0.1.0 inst.      18.0.1.0.0 inst.     ITK: Rechnungen als Massenmail
itk_reports                    11.0.0.4 inst.      18.0.1.0.0 inst.     ITK-Druckvorlagen (u. a. ITK-Rechnung)
itk_projectcategory            11.0.0.1 inst.      18.0.1.0.0 inst.     ITK: Projektkategorie
sale_merge_draft_invoice       nicht installiert   18.0.1.0.0 inst.     O18-Zusatzfunktion (Entwurfsrechnungen sammeln)
account_peppol                 - (nicht vorhanden) 18.0.1.1 installed   O18-Zusatzfunktion: E-Rechnung Peppol
account_edi_ubl_cii            -                   18.0.1.0 installed   O18-Zusatzfunktion: EDI UBL/CII
account_qr_code_sepa           -                   18.0.0.1 installed   O18-Zusatzfunktion: SEPA-QR-Code
snailmail_account              -                   18.0.0.1 installed   O18-Zusatzfunktion: Postversand
spreadsheet_account            -                   18.0.1.0 installed   O18-Zusatzfunktion: Tabellenkalkulation
l10n_de (+ l10n_de_skr03/04)   11.0.1.0/11.0.3.0   -                    O11-Kontenrahmen (deutsch, SKR03 + SKR04)
l10n_at                        nicht installiert   18.0.3.2.1 installed O18-Kontenrahmen (oesterreichisch)
account_reports                - (nicht vorhanden) nicht vorhanden      Enterprise-Berichtsmodul; in O18 nicht installierbar
accountant                     -                   uninstallable (OEEL-1) Enterprise-Katalog, Code fehlt
```

Bewertung: Es fehlen keine **fachlich benoetigten** Module. Die O18-Zusatzfunktionen (Peppol/EDI,
QR-Code, Postversand, Spreadsheet, Sammelrechnung, Positionsbericht) bleiben erhalten. Offener
Punkt ist **nicht** ein fehlendes Modul, sondern der Kontenrahmen (siehe K1) und die acht
Berichtsmenues aus Odoo 11 (siehe Abschnitt 5.1).

## 3. Menuebaum

### 3.1 Odoo 11: App Abrechnung (Wurzel id 133) - 70 Menues (mit full_list)

```
Dashboard                        Buchhaltungsdashboard (account.journal) [Zeige vollstaendige Finanzbuchhaltung]
Verkauf
  Dokumente
    Ausgangsrechnungen           account.invoice
    Kunden-Gutschriften          account.invoice
    Zahlungen                    account.payment
  Erinnerung                     (leer - Mahnwesen nicht installiert)
  Stammdaten
    Kunden                       res.partner
    Verkaufbare Produkte         product.product
Einkauf
  Dokumente
    Eingangsrechnungen           account.invoice
    Lieferanten-Gutschriften     account.invoice
    Zahlungen                    account.payment
  Stammdaten
    Lieferanten                  res.partner
    Einkaufbare Produkte         product.product
Finanzberater                    [Zeige vollstaendige Finanzbuchhaltung]
  Buchungen
    Buchungszeilen               account.move.line [Abrechnungsmanager]
    Buchungssaetze               account.move [Zeige vollstaendige Finanzbuchhaltung]
    Kostenstellenbuchungen       account.analytic.line [Kostenrechnung]
  Verwaltung                     (leer)
  Aktionen
    Manuelle Abstimmung          ir.actions.client (manual_reconciliation_view)
    Steueranpassungen            tax.adjustments.wizard
  Erzeuge Buchungen              (leer)
Berichtswesen                     [Abrechnungsmanager]
  Deutsche Belege                (leer) [Zeige vollstaendige Finanzbuchhaltung]
  Allgemeine Bankbelege          (leer) [Zeige vollstaendige Finanzbuchhaltung]
  Verwaltung
    Rechnungen                   account.invoice.report (Statistik Rechnungen)
    Kostenstellenbuchungen       account.analytic.line [Kostenrechnung]
  Business Intelligence          (leer) [Abrechnung]
  PDF Berichte
    Audit Journale               account.print.journal
    Partner-Kontoauszug          account.report.partner.ledger
    Umsaetze nach Konten/Perioden account.report.general.ledger
    Vorlaeufige Bilanz           account.balance.report
    Bilanz                       accounting.report
    Gewinn und Verlust           accounting.report
    alter Partner Saldo          account.aged.trial.balance
    Umsatzsteuerbericht          account.tax.report
Konfiguration
  Valorisierung                  itk_valorisierung.valorisierung
Konfiguration                    [Abrechnungsmanager]
  Einstellungen                  res.config.settings [Einstellungen]
  Finanzen                       [Abrechnung]
    Kontenplan                   account.account
    Waehrungen                   res.currency [Mehrere Waehrungen]
    Steuern                      account.tax
    Steuerzuordnung              account.fiscal.position
    Berichtswesen                (leer) [Abrechnungsmanager]
    Bankkonten                   account.journal [Abrechnungsmanager]
    Journale                     account.journal [Abrechnungsmanager]
  Verwaltung                     [Abrechnungsmanager]
    Zahlungsbedingungen          account.payment.term
    Bargeldrundungen             account.cash.rounding
  Kostenrechnung                 [Kostenrechnung]
    Kostenstellenkonten          account.analytic.account
    Kostenstellen Tags           account.analytic.tag
  Finanzberichte                 [Zeige vollstaendige Finanzbuchhaltung]
    Finanzberichte               account.financial.report
  Zahlungen
    Zahlungsanbieter             payment.acquirer
    Gespeicherte Zahlungsdaten   payment.token [Technische Eigenschaften]
    Zahlungssymbole              payment.icon [Technische Eigenschaften]
    Zahlungstransaktionen        payment.transaction [Technische Eigenschaften]
```

Zusaetzlich ausserhalb der App Abrechnung (nur zur Kenntnis):
`Einkauf / Kontrolle / Eingangsrechnungen` (account.invoice), `Website / Konfiguration / eCommerce /
Zahlungsanbieter` (payment.acquirer).

### 3.2 Odoo 18: App Rechnungsstellung (Wurzel id 193) - 63 Menues (lokal = VM, 63 = 63)

```
Dashboard                        Dashboard (account.journal) [Basic]
Kunden
  Ausgangsrechnungen             account.move
  Gutschriften                   account.move
  Eingaenge                      account.move (out_receipt) [Verkaufsbeleg]
  Zahlungen                      account.payment (Kundenzahlungen)
  Produkte                       product.template
  Kunden                         res.partner
Lieferanten
  Eingangsrechnungen             account.move
  Rueckerstattungen              account.move
  Eingaenge                      account.move (in_receipt) [Einkaufsbeleg]
  Zahlungen                      account.payment (Lieferantenzahlungen)
  Produkte                       product.template
  Lieferanten                    res.partner
Buchhaltung                      [Buchhaltungsfunktionen anzeigen - schreibgeschuetzt]
  Journalbuchungen               account.move
  Buchungszeilen                 account.move.line
  Kostenstellenbuchungen         account.analytic.line [Kostenrechnung]
  Buchungen festschreiben        account.secure.entries.wizard [Technische Eigenschaften]
Konfiguration
  Valorisierung                  itk_valorisierung.valorisierung
Konfiguration
  Projekt Kategorie              itk_projectcategory.projectcategory
Berichtswesen                     [Buchhaltungsfunktionen anzeigen, Rechnungsstellung]
  Kontoauszugsberichte           (leer - Enterprise-Berichte fehlen)
  Partnerberichte                (leer - Enterprise-Berichte fehlen)
  Verwaltung
    Rechnungsanalyse             account.invoice.report
    Kostenbericht                account.analytic.line
    Pruefpfad                    mail.message
  Abrechnungspositionen          account.invoice.report (list, pivot, graph)
Konfiguration                    [Administrator]
  Einstellungen                  res.config.settings [Einstellungen]
  Rechnungsstellung              [Buchhaltungsfunktionen anzeigen, Rechnungsstellung]
    Zahlungsbedingungen          account.payment.term
    Incoterms                    account.incoterms [Technische Eigenschaften]
  Banken                         [Administrator]
    Ein Bankkonto hinzufuegen    ir.actions.server (res.company)
    Abstimmungsmodelle           account.reconcile.model
  EDI-Proxy-Benutzer             account_edi_proxy_client.user
  Buchhaltung                    [Administrator]
    Kontenplan                   account.account
    Steuern                      account.tax
    Journale                     account.journal
    Berichtswesen                (leer)
    Waehrungen                   res.currency
    Steuerpositionen             account.fiscal.position
    Mehrere Hauptbuecher         account.journal.group
    Steuergruppen                account.tax.group
  Online-Zahlungen               [Administrator]
    Zahlungsanbieter             payment.provider
    Zahlungsmethoden             payment.method
    Zahlungstoken                payment.token
    Zahlungstransaktionen        payment.transaction
  Verwaltung                     [Administrator]
    Produktkategorien            product.category
    Bargeldrundungen             account.cash.rounding
  Kostenrechnung                 [Kostenrechnung]
    Verteilungsschluessel        account.analytic.distribution.model
    Kostenstellen                account.analytic.account
    Kostenstellenplaene          account.analytic.plan
```

Vergleich lokal gegen VM: 63 Menuezeilen auf beiden Instanzen, ein einziger Wortlautunterschied
("Ein Bankkonto hinzufuegen" lokal gegen "Bankkonto hinzufuegen" auf der VM). Alle relevanten
Modulversionen sind lokal und VM identisch (account 18.0.1.3, account_invoice_line_number
18.0.1.0.0, account_invoice_line_report 18.0.1.0.0, account_payment 18.0.2.0, account_peppol
18.0.1.1, analytic 18.0.1.2, itk_valorisierung 18.0.1.0.0, l10n_at 18.0.3.2.1, mass_email_invoice
18.0.1.0.0, sale_merge_draft_invoice 18.0.1.0.0, snailmail_account 18.0.0.1).

### 3.3 Gegenueberstellung der Menues

```
Odoo 11 Abrechnung                          Odoo 18 Rechnungsstellung            Bewertung
Dashboard (Buchhaltungsdashboard)           Dashboard                           1:1 (gleiches Modell account.journal)
Verkauf/Dokumente/Ausgangsrechnungen         Kunden/Ausgangsrechnungen           andere Gruppierung, gleiche Funktion
Verkauf/Dokumente/Kunden-Gutschriften        Kunden/Gutschriften                 andere Gruppierung/Wortlaut
Verkauf/Dokumente/Zahlungen                  Kunden/Zahlungen                    Umbenennung, Domains unterschiedlich (siehe 5.3)
Verkauf/Stammdaten/Kunden                    Kunden/Kunden                       1:1
Verkauf/Stammdaten/Verkaufbare Produkte      Kunden/Produkte                     Modellwechsel product.product -> product.template
Einkauf/Dokumente/Eingangsrechnungen         Lieferanten/Eingangsrechnungen       andere Gruppierung
Einkauf/Dokumente/Lieferanten-Gutschriften   Lieferanten/Rueckerstattungen       anderer Wortlaut
Einkauf/Dokumente/Zahlungen                  Lieferanten/Zahlungen               siehe 5.3
Einkauf/Stammdaten/Lieferanten               Lieferanten/Lieferanten             1:1
Einkauf/Stammdaten/Einkaufbare Produkte      Lieferanten/Produkte                Modellwechsel
Verkauf/Erinnerung (leer)                   -                                   toter O11-Knoten (Mahnwesen nie installiert)
Finanzberater/Buchungen/Buchungszeilen       Buchhaltung/Buchungszeilen          1:1 (andere Gruppierung)
Finanzberater/Buchungen/Buchungssaetze       Buchhaltung/Journalbuchungen        Umbenennung
Finanzberater/Buchungen/Kostenstellenbuchungen Buchhaltung/Kostenstellenbuchungen 1:1
Finanzberater/Aktionen/Manuelle Abstimmung  (in Abstimmung integriert)          Bedienunterschied (O18: im Abstimmungsbereich)
Finanzberater/Aktionen/Steueranpassungen     -                                  FEHLT (Modell tax.adjustments.wizard fehlt)
Berichtswesen/Verwaltung/Rechnungen          Berichtswesen/Verwaltung/Rechnungsanalyse 1:1 (account.invoice.report)
Berichtswesen/Verwaltung/Kostenstellenbuchungen Berichtswesen/Verwaltung/Kostenbericht 1:1
Berichtswesen/PDF Berichte (8 Menues)        Berichtswesen/Kontoauszugsberichte (leer)  FEHLT (siehe 5.1)
                                             Berichtswesen/Partnerberichte     (leer)   FEHLT
                                             Berichtswesen/Abrechnungspositionen        Zusatzfunktion O18
                                             Berichtswesen/Verwaltung/Pruefpfad         Zusatzfunktion O18
                                             Buchhaltung/Buchungen festschreiben        Zusatzfunktion O18
Konfiguration/Valorisierung                  Konfiguration/Valorisierung         1:1
Konfiguration/Finanzen/Kontenplan            Konfiguration/Buchhaltung/Kontenplan  1:1 (Inhalt: siehe K1)
Konfiguration/Finanzen/Waehrungen            Konfiguration/Buchhaltung/Waehrungen  1:1
Konfiguration/Finanzen/Steuern               Konfiguration/Buchhaltung/Steuern     1:1
Konfiguration/Finanzen/Steuerzuordnung       Konfiguration/Buchhaltung/Steuerpositionen Umbenennung
Konfiguration/Finanzen/Bankkonten            (entfaellt)                         O18: Journal Bank, Konto am Journal
Konfiguration/Finanzen/Journale              Konfiguration/Buchhaltung/Journale    1:1
Konfiguration/Finanzen/Berichtswesen (leer)  Konfiguration/Buchhaltung/Berichtswesen (leer) 1:1 (leer)
Konfiguration/Verwaltung/Zahlungsbedingungen Konfiguration/Rechnungsstellung/Zahlungsbedingungen 1:1
Konfiguration/Verwaltung/Bargeldrundungen    Konfiguration/Verwaltung/Bargeldrundungen 1:1
Konfiguration/Kostenrechnung/Kostenstellenkonten Konfiguration/Kostenrechnung/Kostenstellen 1:1
Konfiguration/Kostenrechnung/Kostenstellen Tags -                               FEHLT (Modell account.analytic.tag fehlt)
Konfiguration/Finanzberichte/Finanzberichte  -                                   FEHLT (Modell account.financial.report fehlt)
Konfiguration/Zahlungen/Zahlungsanbieter     Konfiguration/Online-Zahlungen/Zahlungsanbieter 1:1 (Modell payment.provider)
Konfiguration/Zahlungen/Gespeicherte Zahlungsdaten Konfiguration/.../Zahlungstoken 1:1
Konfiguration/Zahlungen/Zahlungssymbole      -                                   FEHLT (Modell payment.icon fehlt)
Konfiguration/Zahlungen/Zahlungstransaktionen Konfiguration/.../Zahlungstransaktionen 1:1
                                             Konfiguration/Rechnungsstellung/Incoterms  Zusatzfunktion O18
                                             Konfiguration/Banken/Abstimmungsmodelle    Zusatzfunktion O18
                                             Konfiguration/EDI-Proxy-Benutzer           Zusatzfunktion O18
                                             Konfiguration/Buchhaltung/Mehrere Hauptbuecher Zusatzfunktion O18
                                             Konfiguration/Buchhaltung/Steuergruppen    Zusatzfunktion O18
                                             Konfiguration/Kostenrechnung/Verteilungs-
                                             schluessel + Kostenstellenplaene           O18-Ersatz fuer Kostenstellen-Tags
                                             Konfiguration/Verwaltung/Produktkategorien Zusatzfunktion O18
```

## 4. Tatsaechlich verwendete Bereiche und Datenmengen

### 4.1 Odoo 11 Prod (read-only gemessen, Datenlage des Kunden)

```
Rechnungen (account.invoice)          6.277
  Ausgangsrechnungen (out_invoice)    6.040
  Kunden-Gutschriften (out_refund)      237
  Eingangsrechnungen (in_invoice)         0   => Einkaufs-Abrechnung NICHT verwendet
  Lieferanten-Gutschriften (in_refund)    0   => in Odoo 18 nicht verwendet
  Zustand: bezahlt 6.220 | offen 43 | Entwurf 14 | storniert 0
  offener Restbetrag > 0: 43
  Zeitraum: 27.05.2019 bis 28.09.2026
  Nummernkreis: aelteste R-1900001, juengste R-26989
Rechnungszeilen (account.invoice.line) 10.031, davon 10.009 mit Steuer
Zahlungen (account.payment)           5.987 - alle gebucht
  Einzahlungen (inbound) 5.877 | Auszahlungen (outbound) 110
  mit Rechnungsbezug 5.985 | Journal: Bank fuer Tirol und Vorarlberg (BNK1)
  Zeitraum: ab 16.09.2019
Abstimmungen: account.partial.reconcile 6.123 | account.full.reconcile 6.081
Buchungen (account.move)             12.251 (12.250 gebucht, 1 Entwurf)
  Journal Ausgangsrechnungen 6.263 | Bank 5.987 | Sonstige Operationen 1
  5 weitere Journale (Kasse/Bank, Einnahmeueberschuss-Steuer, Wechselkurs, Lager,
  Eingangsrechnungen) je 0 Buchungen
Journale (account.journal)                8
Valorisierungstexte: 4.216 von 6.277 Rechnungen tragen einen Valorisierungstext
  10 Texte (2019 bis 2026), Verteilung: 1 / 460 / 534 / 553 / 644 / 639 / 8 / 30 / 697 / 650
Kostenrechnung (account.analytic.line) 12.634
  mit Projekt 12.352 | mit Aufgabe 12.493 | mit Auftragszeile 0
  Rechnungszeilen mit Kostenstelle: 0 | Kostenstellen-Tags verwendet: 0
  Kostenstellen (account.analytic.account): 33 (ITK-Projekte/Produkte)
Steuern (account.tax)                     77, alle aktiv (Verkauf 22 / Einkauf 29 / keine 26)
Konten (account.account)               1.286 (deutscher Kontenrahmen l10n_de SKR03+SKR04)
Steuergruppen (account.tax.group)         13
Steuerpositionen (account.fiscal.position) 5 - auf 4 Rechnungen verwendet
Kontenplan-Typen (account.account.type)   17
Zahlungsbedingungen (account.payment.term) 4, alle mit value=balance:
  Sofortige Zahlung (0 Tage) | 15 Tage | 30 Tage netto | 14 Tage (je ab Rechnungsdatum)
Kostenstellenplaene/Tags (O11: account.analytic.tag) 0 Datensaetze
Waehrungen: EUR (id 1) und USD (id 3), beide aktiv (USD = Altlast F2/F3/F4, unveraendert offen)
E-Mail-Versand von Rechnungen: 2.549 Rechnungen als "versendet" markiert
  Chatter: 34.171 Nachrichten zu Rechnungen, davon 5.772 E-Mails, 9.197 Anhaenge
Druckvorlagen auf Rechnungen: 4 (Odoo-Standard mit/ohne Zahlung, itk_reports ITK-Rechnung
  und ITK-Rechnung mit Zahlung)
Bankauszuege (account.bank.statement)      0  => Bankimport nie verwendet
Online-Zahlungen (payment.transaction)     0  => nie verwendet (10 payment.acquirer angelegt)
Ist-Versteuerung: Journal CABA vorhanden, 0 Buchungen
Mahnwesen: Modul nicht installiert, Menue "Erinnerung" leer
```

Volumen je Jahr (Rechnungen / Zahlungen / Buchungen gesamt):

```
2019  66 /   45 /  111     2023  853 /  785 / 1639
2020 732 /  736 / 1468     2024  861 /  845 / 1706
2021 829 /  816 / 1645     2025  955 /  883 / 1838
2022 828 /  812 / 1640     2026 1139 / 1065 / 2204
```

### 4.2 Odoo 18 Testbestand (keine Produktivdaten, nur Struktur)

```
                                   lokal            VM
account.move gesamt                    37            57
  Ausgangsrechnungen                    26            47
  Buchungen (entry)                     11            10
  uebrige move_type (in/out_refund,
  receipts)                              0             0
Zustand: Entwurf 22 / gebucht 15         -     Entwurf 42 / gebucht 15
account.move.line                     100            -
account.payment                          7             7 (alle bezahlt, Einzahlungen)
account.journal                          8             8
account.tax                             53            53
account.payment.term                    12            12 ("30 Tage netto" lokal id 16, VM id 14)
account.account                        240            -
account.analytic.account                 5             5 | Buchungen 19 | Plan "Projekt"
itk_valorisierung.valorisierung          1             1 (Testwert VAL-OK)
Rechnungen mit Valorisierungstext        1             1
Anhaenge zu Rechnungen                   0             0
Rechnungen mit Steuerposition           21            26
```

## 5. Fehlende oder anders aufgebaute Funktionen

### 5.1 Acht Berichtsmenues aus Odoo 11 fehlen in Odoo 18 (Modelle existieren nicht)

Odoo 11 hatte im Bereich Berichtswesen/PDF Berichte acht Berichte, die in Odoo 11 noch im
Community-Umfang des Moduls `account` lagen. In Odoo 18 sind diese Assistenten entfernt; die
Berichte liegen nur mehr im Enterprise-Modul `account_reports`, das in dieser Installation nicht
verfuegbar ist (`accountant` = `uninstallable`, Lizenz OEEL-1, Code fehlt).

```
Odoo-11-Menue                 Modell (O11)                     Modell in O18
Audit Journale                account.print.journal            fehlt (404)
Partner-Kontoauszug           account.report.partner.ledger    fehlt
Umsaetze nach Konten/Perioden account.report.general.ledger    fehlt
Vorlaeufige Bilanz            account.balance.report           fehlt
Bilanz                        accounting.report                fehlt
Gewinn und Verlust            accounting.report                fehlt
alter Partner Saldo           account.aged.trial.balance       fehlt
Umsatzsteuerbericht           account.tax.report               fehlt
Finanzberichte (Konfiguration) account.financial.report        fehlt (O11: 8 Datensaetze)
Steueranpassungen (Aktionen)  tax.adjustments.wizard           fehlt
Kostenstellen Tags            account.analytic.tag             fehlt (O11: 0 Datensaetze)
Zahlungssymbole               payment.icon                     fehlt (O11: 10 Datensaetze)
```

Gegenprobe: In Odoo 18 (lokal und VM) gibt es **kein** Menue und **keines** dieser Modelle;
die Menueknoten "Kontoauszugsberichte" und "Partnerberichte" existieren, sind aber im
Community-Umfang leer. Nutzungsnachweis fuer die acht Berichte: keiner moeglich, weil es
Assistenten (transiente Modelle) ohne gespeicherte Datensaetze sind - 0 Datensaetze je Modell,
0 Anhaenge je Modell, kein Protokoll. Das wird als offene Fachfrage vorgelegt (K3), nicht
selbst entschieden.

### 5.2 Weitere fehlende Ziele

```
account.account.type (17 Typen)   -> Odoo 18: Auswahlfeld account_type am Konto (kein Modell)
account.analytic.tag (0 Werte)    -> Odoo 18: Kostenstellenplaene + Verteilungsschluessel
Verkaufbare/Einkaufbare Produkte   -> Odoo 18: Produkte (product.template statt product.product)
Bankkonten (account.journal)       -> Odoo 18: Journal "Bank" + Konto am Journal
Manuelle Abstimmung (Client-Aktion) -> Odoo 18: Abstimmung im Buchungs-/Bankbereich
Zahlungssymbole (payment.icon)     -> Odoo 18: Symbol am Zahlungsanbieter/der Methode
```

### 5.3 Anders aufgebaute Funktionen (Bedienung/Struktur, kein Funktionsverlust)

1. **Gruppierung:** Odoo 11 trennt nach Verkauf/Einkauf, Odoo 18 nach Kunden/Lieferanten. Inhaltlich
   dieselben Belege, andere Navigationslogik.
2. **Zahlungsmenues ohne Domain:** Odoo 11 schraenkt die beiden Zahlungsmenues per Domain ein
   (`partner_type = customer` bzw. `supplier`), Odoo 18 setzt nur Vorgabewerte im Kontext
   (Kundenzahlungen/Lieferantenzahlungen) - in Odoo 18 zeigt jedes der beiden Menues alle Zahlungen.
3. **Listen-Ansichten:** Odoo 18 verwendet `list` statt `tree` (Odoo-11-Ansichten sind umbenannt),
   zusaetzlich Aktivitaetsansichten.
4. **Rechnungsmodell:** Odoo 11 `account.invoice`/`account.invoice.line` gegen Odoo 18
   `account.move`/`account.move.line` mit `move_type` (Transformationen siehe Abschnitt 6).
5. **Kontenrahmen:** Odoo 11 fuehrt den deutschen Kontenrahmen (`l10n_de`, SKR03 + SKR04, 1.286
   Konten), Odoo 18 den oesterreichischen (`l10n_at`, 240 Konten). Der Kunde hat in Odoo 11 also
   mit deutschem Kontenrahmen gebucht. Siehe K1.
6. **Berechtigungen:** Odoo 11 steuert die Berichte ueber "Abrechnungsmanager" und "Zeige
   vollstaendige Finanzbuchhaltung"; Odoo 18 ueber "Buchhaltungsfunktionen anzeigen -
   schreibgeschuetzt" (`account.group_account_readonly`), "Rechnungsstellung", "Kostenrechnung",
   "Administrator". Die Menues sind erreichbar, die Gruppenzuordnung ist aber nicht 1:1
   (Detailpruefung in einem spaeteren Teil).
7. **Kostenstellen:** Odoo 11 bucht Kostenstellen ueber `account.analytic.account` +
   `account.analytic.line` (+ unbenutzte Tags); Odoo 18 ueber `account.analytic.plan`,
   `account.analytic.distribution.model` und `analytic_distribution` auf der Buchungszeile.
8. **Zahlungen:** gleicher Modellname (`account.payment`), aber andere Felder und Zustaende
   (O11 `state` open/paid, O18 `state` + `payment_state`; O11 `invoice_ids`, O18
   `reconciled_invoice_ids`; O18 zusaetzlich `payment_method_line_id`).

### 5.4 Tote Menueknoten (in beiden Systemen ohne Inhalt)

```
Odoo 11: Verkauf/Erinnerung (Mahnwesen), Berichtswesen/Deutsche Belege und /Allgemeine Bankbelege
         (Bankauszug-Menues), Finanzberater/Verwaltung, Finanzberater/Erzeuge Buchungen,
         Berichtswesen/Business Intelligence, Konfiguration/Finanzen/Berichtswesen
Odoo 18: Berichtswesen/Kontoauszugsberichte, Berichtswesen/Partnerberichte,
         Konfiguration/Buchhaltung/Berichtswesen
```
Belege: leere Knoten ohne Aktion und ohne Kinder (gemessen mit full_list), zugehoerige Module
nicht installiert (Mahnwesen) bzw. 0 Datensaetze (Bankauszuege 0, Kostenstellen-Tags 0).

### 5.5 Odoo-18-Zusatzfunktionen (bleiben erhalten, nichts entfernen)

```
Abrechnungspositionen (account.invoice.report als Liste/Pivot/Graph), Pruefpfad (mail.message),
Buchungen festschreiben (account.secure.entries.wizard), Mehrere Hauptbuecher (account.journal.group),
Steuergruppen (account.tax.group), Abstimmungsmodelle (account.reconcile.model, 4 Datensaetze),
Incoterms, Kostenstellenplaene + Verteilungsschluessel, Zahlungsmethoden (payment.method),
E-Rechnung/Peppol (account_peppol, account_edi_ubl_cii), SEPA-QR-Code, Postversand (snailmail),
Spreadsheet/Dashboards, Sammelrechnung (sale_merge_draft_invoice), Positionsbericht
(account_invoice_line_report, in Odoo 11 nicht installiert)
```

## 6. Transformationen (gemessene Feld- und Modellumbenennungen)

```
Odoo 11 (gemessen)                        Odoo 18 (gemessen)               Art
account.invoice (6.277)                   account.move (37 Belege)         Modellwechsel
account.invoice.line (10.031)             account.move.line (100)          Modellwechsel
type (out_invoice ...)                    move_type                        Umbenennung
state (draft/open/paid/cancel)            state (draft/posted/cancel) +    geaenderte Zustandswerte
                                          payment_state (not_paid/partial/paid)
residual (6.277 gefuellt)                 amount_residual                  Umbenennung
date_invoice (6.263)                      invoice_date (28)                Umbenennung
date_due (6.268)                          invoice_date_due (37)            Umbenennung
origin (6.140)                            invoice_origin (26)              Umbenennung
reference (0)                             ref (7)                          Umbenennung
user_id (6.277)                           invoice_user_id (24)             Umbenennung
sent (2.549)                              is_move_sent (0)                 Umbenennung
number (6.263) / move_name (6.263)        name (15)                        Umbenennung
payment_term_id (5.737)                   invoice_payment_term_id (8)      Umbenennung
invoice_line_tax_ids (10.009)             tax_ids (40)                     Umbenennung
account_analytic_id (0)                   analytic_distribution (0)        Umbenennung (beide ungenutzt)
uom_id (10.029)                           product_uom_id (40)              Umbenennung
invoice_id                               move_id                          Umbenennung
account.invoice.report (SQL-Sicht)         account.invoice.report           gleicher Name, andere Quelle
customer/supplier (Boolean)               customer_rank/supplier_rank      Umbenennung (Kontakte, bereits dokumentiert)
payment.acquirer (10)                     payment.provider (17)            Umbenennung
payment.token (0)                         payment.token                    gleicher Name
valorisierung_id am account.invoice       valorisierung_id am account.move Feld existiert in beiden
                                          (+ account.bank.statement.line)  (O11 4.216 Rechnungen, O18 1 Testbeleg)
```

Bewertung: Alle Transformationen sind Odoo-Standardumbenennungen oder Modellwechsel mit klarem
Ziel. Kein Feld ist ohne Ziel, ausser den unter 5.1/5.2 genannten Berichtsassistenten und
`account.analytic.tag`/`account.account.type`.

## 7. Technische Blocker

```
keine. Es ist keine IPAX-Freigabe und keine Sonderfreischaltung noetig.
account_reports/accountant sind Enterprise-Katalogeintraege ohne Code - das ist kein Blocker
fuer die vorhandenen Funktionen, erklaert aber die acht fehlenden Berichte (Abschnitt 5.1).
Odoo 11 wurde ausschliesslich lesend verwendet (keine Schreib-, Aenderungs-, Loesch- oder
Upgrade-Operation). An Odoo 18 wurde in diesem Teil NICHTS geaendert.
```

## 8. Offene Fachfragen (KLAERUNG NOETIG - Entscheidung Anna)

```
K1 Kontenrahmen: Odoo 11 bucht mit deutschem Kontenrahmen (l10n_de, SKR03+SKR04, 1.286 Konten),
   Odoo 18 fuehrt den oesterreichischen (l10n_at, 240 Konten). Vor einer Rechnungs-/Buchungs-
   migration braucht es eine Kontenzuordnung (Mapping O11-Konto -> O18-Konto). Frage: bleibt der
   oesterreichische Kontenrahmen in Odoo 18, und wer legt das Mapping fest (Buchhaltung)?

K2 Nummernkreis: Odoo-11-Rechnungsnummern laufen von R-1900001 bis R-26989 (6.263 vergebene
   Nummern). Frage: Nummern bei der Migration uebernehmen oder in Odoo 18 neu vergeben
   (gleiche Frage wie bei den Auftraegen/Verkauf bereits dokumentiert)?

K3 Die acht PDF-Berichte aus Abschnitt 5.1 (Bilanz, Gewinn und Verlust, Vorlaeufige Bilanz,
   Partner-Kontoauszug, Umsaetze nach Konten und Perioden, alter Partner Saldo, Audit Journale,
   Umsatzsteuerbericht): Nutzung ist nicht messbar (Assistenten ohne Datensaetze). Frage: werden
   diese Berichte (insbesondere Umsatzsteuerbericht/UVA) fachlich benoetigt? Wenn ja: Eigenbau in
   Odoo 18 (z. B. Auswertung auf account.move.line) oder Verzicht/Enterprise?

K4 Valorisierungstexte: 10 Texte aus Odoo 11, auf 4.216 Rechnungen verwendet. Das Feld existiert in
   Odoo 18 (account.move). Frage: die 10 Texte als Stammdaten in Odoo 18 anlegen (1:1 mit
   Odoo-11-Wortlaut)? Jetzt wird nichts angelegt.

K5 Steuern: 77 in Odoo 11 gegen 53 in Odoo 18 (Verkauf 22/26, Einkauf 29/26, keine 26/1). Die
   inhaltliche Zuordnung (Saetze, Konten, Namen) wird in Teil 2/3 vorgelegt - bitte erst dort
   entscheiden.

K6 Zahlungsmenues: Odoo 11 schraenkt per Domain nach Kundenzahlung/Lieferantenzahlung ein, Odoo 18
   nicht. Frage: soll die Einschraenkung in Odoo 18 ergaenzt werden (Odoo-11-Bedienlogik) oder
   bleibt der Odoo-18-Standard?

K7 Rechnungs-Versand per E-Mail: in Odoo 11 sind 2.549 Rechnungen als versendet markiert (9.197
   Anhaenge, 5.772 E-Mails im Chatter). SMTP ist in Odoo 18 weiterhin nicht konfiguriert
   (bekannt offen) - der Rechnungsversand ist damit vor der Migration zu pruefen.

K8 Kostenstellen: 33 Kostenstellen und 12.634 Buchungen in Odoo 11, alle aus Projekten/Aufgaben;
   Kostenstellen-Tags in Odoo 11 mit 0 Datensaetzen nie verwendet. Empfehlung: Tags nicht
   nachbauen, Kostenstellenplaene/Verteilungsschluessel aus Odoo 18 verwenden (Entscheidung offen).

K9 US-Waehrung (F2/F3/F4) und USD-Preisliste (F5) bleiben unveraendert offen - im Bereich
   Abrechnung relevant, weil 4 Rechnungen betroffen sind.
```

## 9. Empfohlene Anpassungen fuer Teil 2 (Vorschlag, noch nichts umgesetzt)

```
Teil 2  Feldinventar Rechnung: account.invoice / account.invoice.line gegen account.move /
        account.move.line - je Feld Beschriftung, Typ, Relation, Pflicht, readonly, Zustand
        (gespeichert/berechnet), belegte Datensaetze (n von N), Odoo-18-Ziel, Einstufung
        (1:1 / Transformation / berechnet / nur Odoo 18 / obsolet / kein Ziel / Klaerung).
        Zusaetzlich: Zustandswerte und Zahlungsstatus, Pflichtfelder in beiden Richtungen.
Teil 3  Formulare, Reiter, Buttons, Smart Buttons, Zustandswechsel (Browser, lokal und VM);
        Zahlungs- und Abstimmungslogik; Rechnungsdruck und Versand.
Teil 4  Ansichten (Liste, Kanban, Pivot, Graph), Filter, Suche, Gruppierungen; Menueangleichung
        Kunden/Lieferanten gegen Verkauf/Einkauf (nach Entscheidung K6).
Teil 5  Stammdaten und Abschluss: Steuern (K5), Kontenzuordnung (K1), Zahlungsbedingungen,
        Valorisierungstexte (K4), Kostenstellen (K8), Abschlusspruefung + Migrationsregeln
        (migration/abrechnung_migrationsregeln.json).
Vor Teil 3  Entscheidungen zu K1, K3, K4 und K6 einholen.
```

Nicht bearbeitet in diesem Teil (ausdruecklich offen): Feldinventar, Formulare, Ansichten,
Steuerinhalte, Kontenzuordnung, Valorisierungsanlage, Umbauten jeder Art.

## 10. Rahmenbedingungen (eingehalten)

```
Keine Datenmigration: es wurden keine Odoo-11-Datensaetze uebernommen; Odoo 18 wurde nicht
  veraendert (kein Upgrade, kein Neustart, keine Konfiguration).
Odoo 11 ausschliesslich read-only: alle Aufrufe waren search_count/search_read/fields_get/
  read (Menues, Aktionen, Modelle, Felder, Zaehlungen).
Odoo 18 lokal und VM geprueft: Menuebaum 63 = 63, Modulversionen 20 von 20 identisch.
Bestand Odoo 18 unveraendert (lokal 37 Belege, VM 57 Belege; Zahlungen je 7).
Rohdaten der Messungen liegen nicht im Repo (Temp-Verzeichnis).
```
