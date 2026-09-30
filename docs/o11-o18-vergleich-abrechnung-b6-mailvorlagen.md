# Odoo 11 gegen Odoo 18 - Bereich Abrechnung, B6: Mailvorlagen (Rechnungsversand)

Befund B6 aus Teil 3: In Odoo 11 liegen 9 Mailvorlagen auf der Rechnung, in Odoo 18 waren 5
Vorlagen vorhanden (englische Bezeichnungen). Frage: sind die in Odoo 11 tatsaechlich
verwendeten Rechnungsmailtexte in Odoo 18 verfuegbar?

Stand: 30.09.2026, Session 122. Arbeitsweise: Fertigstellung von Odoo 18 fuer die Migration.
**Odoo 11 wurde ausschliesslich lesend verwendet, es wurde nichts migriert.**
In Odoo 18 wurden zwei Mailvorlagen als Moduldaten ergaenzt (kein Nachbau des Odoo-11-
Assistenten, keine Aenderung an Odoo-Standarddaten).

## 1. Vorgehen und Nachweisquellen

| Quelle | Werkzeug | Inhalt |
| --- | --- | --- |
| Odoo 11 Prod | `mail.template` (Felder, Texte, Berichtsanhang), Versandkennzeichen | Wortlaute und Verwendung |
| Odoo 18 lokal | `scripts/verify_b6_mailvorlagen.py`, Modul-Upgrade `itk_reports` | Vorlagen, Rendern, Anhang, Versandvorbereitung |
| Odoo 18 Test-VM | dieselbe Pruefung `--instanz vm` und Browser-Test | Abnahme auf der Abnahmeumgebung |
| Odoo-18-Quellcode (VM) | `account/models/account_move_send.py`, `account/models/account_move.py` | Vorlagenwahl beim Senden |

## 2. Bestand in Odoo 11 (read-only gemessen)

```
9 Mailvorlagen auf account.invoice:
  id 41  Rechnungsstellung: Allgemeine Rechnung        (Wortlaut: allgemeine Rechnung)
  id 42  Rechnungsstellung: Einzel E-Mail              (Wortlaut identisch mit id 41)
  id 11  Rechnungsstellung: Ihr Abonnement fuer help-amtsweg.gv.at  (Wortlaut: Nutzungsgebuehr
         fuer amtsweg.gv.at)
  id 58  Rechnung: IT-Kommunal GmbH 1. Mahnung         (Mahnung)
  id 61  Rechnung: 2. Mahnung                          (Mahnung)
  id 71  Rechnung: IT-Kommunal GmbH 2. Mahnung         (Mahnung, Variante)
  id 82  Rechnung: ${object.company_id.name} Rechnung  (Erinnerung "noch nicht ueberwiesen")
  id 83  wie id 82                                     (Dublette)
  id 38  Website Subscription: Payment success         (Standardvorlage des Abonnements)
Gemeinsamer Betreff (41, 42, 11): "${object.company_id.name} Rechnung (Ref ${object.number or
  'n/a'})"; Absender "ITK-Office <office@it-kommunal.at>"; als Anhang der Bericht id 537
  "Rechnung"; im Text der ITK-Briefkopf (itk_reports/static/img/itk_pageheader.jpg) und die
  Signatur von Martina Waiss.
Versandkennzeichen Odoo 11: 2.549 Rechnungen als versendet markiert.
Zuordnung einzelner Sendungen zu einer Vorlage: in Odoo 11 nicht gespeichert (mail.message hat
  kein Vorlagenfeld), daher nicht rekonstruierbar; die Vorlagen selbst sind vollstaendig belegt.
```

## 3. Bestand in Odoo 18 vor dieser Aenderung

```
5 Standardvorlagen auf account.move, de_DE bereits uebersetzt:
  id 14  Rechnung: Versand                  Betreff "{{ object.company_id.name }} Rechnung (Ref ...)"
  id 16  Gutschrift: Versand
  id 21  Selbstfakturierte Rechnung: Versand
  id 22  Selbstfakturierte Gutschrift: Versand
  id 66  Website Subscription: Payment success (Betreff "Rechnung fuer Abonnement")
Vorlagenwahl beim Senden (Quellcode Odoo 18, models/account_move.py Z. 5733): der Knopf "Senden"
  verwendet fest die Standardvorlage (Gutschrift: eigene Vorlage). Die PDF-Vorlage ist je Partner
  einstellbar (res.partner.invoice_template_pdf_report_id bzw. Standard "account.account_invoices").
Der Massenversand (Modul mass_email_invoice, installiert) laeuft ueber den Standard-Maildialog,
  in dem die Vorlage gewaehlt wird.
Fehlend gegenueber Odoo 11: der ITK-Wortlaut der Rechnungsmail (allgemein und Abonnement).
```

## 4. Umsetzung in Odoo 18 (Modul itk_reports, Version 18.0.1.1.0)

Neu: `addons/itk_reports/data/mail_template_invoice.xml` mit zwei Vorlagen auf `account.move`:

| Vorlage (xmlid) | Beschriftung | Quelle in Odoo 11 |
| --- | --- | --- |
| `itk_reports.mail_template_itk_invoice` | Rechnungsstellung: Allgemeine Rechnung | id 41 (inhaltsgleich mit id 42) |
| `itk_reports.mail_template_itk_invoice_abo` | Rechnungsstellung: Ihr Abonnement für help-amtsweg.gv.at | id 11 |

Felder der neuen Vorlagen:

```
Modell       : account.move
Betreff      : {{ object.company_id.name }} Rechnung (Ref {{ object.name or 'n/a' }})
Absender     : ITK-Office <office@it-kommunal.at>
Sprache      : {{ object.partner_id.lang }}
Anhang       : ITK-Rechnung (itk_reports.action_report_itk_invoices)
Text         : Wortlaut aus Odoo 11 (Anrede, Rechnungszweck, Dank, Signatur Martina Waiss),
               Briefkopf als Bild mit absoluter Adresse (object.get_base_url() +
               '/itk_reports/static/img/itk_pageheader.jpg'), Signatur des Verkaeufers
               (object.invoice_user_id.signature)
Loeschen nach Versand (auto_delete): wie in Odoo 11
```

Bewusste Entscheidungen:

- Die Vorlagen id 41 und id 42 sind im Wortlaut identisch; in Odoo 18 genuegt eine Vorlage
  (keine Dublette anlegen).
- Die drei Mahnvorlagen (58, 61, 71) und die Erinnerungsvorlage (82/83) werden nicht nachgebaut:
  das Mahnwesen ist in Odoo 11 nicht installiert und war laut Vorgabe K3/K7 nicht Bestandteil
  der Migration.
- Die Standardvorlagen von Odoo 18 (id 14, 16, 21, 22, 66) bleiben unveraendert und weiterhin
  der Standard beim Knopf "Senden" (Odoo-18-Zusatzfunktionen bleiben erhalten).
- Platzhalter wurden auf Odoo 18 umgestellt: `object.number` -> `object.name` (Belegnummer),
  `object.user_id` -> `object.invoice_user_id` (Verkaeufer).

## 5. Pruefungen

### 5.1 Lokal (Modul-Upgrade + Pruefskript)

```
Upgrade: docker exec odoo18 odoo -u itk_reports -d odoo18_test --db-host db ...
Pruefung: python scripts/verify_b6_mailvorlagen.py --instanz lokal -> 31 OK / 0 FEHL
  Vorhandensein, Beschriftung, Modell account.move, Absender, Betreff, Briefkopf, Anrede,
  Wortlaut (allgemein und Abonnement), ITK-Rechnung als Anhang
Rendern an der gebuchten Testrechnung RE/2020/0001:
  Betreff: "IT-Kommunal GmbH Rechnung (Ref RE/2020/0001)"
  Text   : "Sehr geehrte Damen und Herren, Bitte finden Sie anbei unsere Rechnung im
            Zusammenhang fuer unsere Leistungen oder Produkte ..." (wie Odoo 11)
  Briefkopf: https://www.it-kommunal.at/itk_reports/static/img/itk_pageheader.jpg
  Anhang : "Rechnung - Breitenbrunn am Neusiedler See - RE/2020/0001.pdf" (23 KB)
  Zustand: Mail vorbereitet (outgoing); SMTP ist nicht konfiguriert, es wird nichts versendet
Massenversand: Maildialog mit der ITK-Vorlage erzeugt einen Entwurf mit Betreff und Text
```

### 5.2 VM-Abnahme

```
Modul-Upgrade auf der Test-VM, danach:
  python scripts/verify_b6_mailvorlagen.py --instanz vm  -> siehe Abschnitt 6
  Browser-Test auf der VM (Rechnung oeffnen, Versand- und Vorlagenweg pruefen)
```

## 6. VM-Ergebnis

Wird nach dem Ausrollen eingetragen (Teil dieser Aenderung, Abschnitt wird mit den Messwerten
der VM ergaenzt).

## 7. Testdaten

Die Pruefung erzeugt vorbereitete Maildatensaetze (`mail.mail`, Zustand outgoing) in der
jeweiligen Testdatenbank; SMTP ist nicht konfiguriert, es wird nichts verschickt. Keine
Produktivdaten, keine Migration.

## 8. Grenzen der Aussage

- Welche Vorlage in Odoo 11 fuer welche Sendung verwendet wurde, ist nicht gespeichert; belegt
  sind die Vorlagen selbst und die Anzahl versendeter Rechnungen (2.549).
- Der Versand selbst (SMTP) ist offen (Vorgabe K7) und wird hier nicht konfiguriert.

## 9. Naechster Schritt

Teil 4 (Ansichten, Listen, Filter, Massenaktionen der Rechnung).
