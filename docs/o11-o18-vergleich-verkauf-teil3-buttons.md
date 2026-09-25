# Odoo 11 -> Odoo 18: Bereich Verkauf, Teil 3, Schritt 2 (Buttons und Smart Buttons)

Stand: 24.09.2026, Session 121. Odoo 11 Prod (`portal.it-kommunal.at`, DB `ITK_V1_a`) wurde
ausschliesslich lesend gelesen. Keine Datenmigration. Aenderungen an Odoo 18: nur der Testauftrag
des Klicktests (angelegt und wieder geloescht).

Umfang: **Buttons und Smart Buttons im Angebots-/Auftragsformular** von `sale.order`.
Der systematische Zustandsvergleich (Statuswechsel als eigenes Thema) folgt in einem weiteren
Schritt; hier wird der Status nur als Reaktion auf Buttonklicks beruehrt.

Werkzeuge:
- `scripts/analyse_verkauf_teil3_buttons.py` - liest Kopf-Buttons, Smart Buttons und Zeilen-Buttons
  aus dem Arch (Odoo 11, Odoo 18 lokal und VM), schreibt `docs/_verkauf_teil3_buttons.json`
- `scripts/browser_verkauf_buttons_klicktest.py` - echter Klicktest (legt einen Testauftrag an,
  klickt alle Buttons, loescht den Testauftrag wieder)

## 1. Kopf-Buttons

```
Odoo 11 (Produktivdaten, 15 Button-Knoten, 10 verschiedene)
  Auftrag bestätigen        action_confirm              (states: sent, draft)
  Abbrechen                 action_cancel               (states: draft, sent, sale)
  Setze auf Angebot         action_draft                (states: cancel)
  Sperre                    action_done                 (states: sale)
  Entsperren                action_unlock               (states: done)
  Drucken                   print_quotation             (states: draft, sent, sale)
  Rechnung erzeugen         Aktion 425 "Abrechnung Auftrag" -> sale.advance.payment.inv
  Per E-Mail versenden      action_quotation_send
  Proformarechnung senden   action_quotation_send
  Wiederherstellungs-E-Mail senden  action_recovery_email_send (website_sale, Warenkorb)

Odoo 18 (11 verschiedene)
  Bestätigen                 action_confirm
  Stornieren                 action_cancel
  Auf Angebot setzen         action_draft
  Sperren                    action_lock
  Entsperren                 action_unlock
  Vorschau                   action_preview_sale_order      (neu)
  Rechnung erstellen         Aktion 428 "Rechnung(en) erstellen" -> sale.advance.payment.inv
  Per E-Mail versenden       action_quotation_send
  Pro-forma-Rechnung senden  action_quotation_send
  Transaktion erfassen       payment_action_capture         (neu, Zahlungen)
  Transaktion stornieren     payment_action_void            (neu, Zahlungen)
```

Zuordnung:

| Odoo 11 | Odoo 18 | Bewertung |
|---|---|---|
| Auftrag bestätigen (`action_confirm`) | Bestätigen (`action_confirm`) | 1:1, Wortlaut gekuerzt |
| Abbrechen (`action_cancel`) | Stornieren (`action_cancel`) | Funktionsunterschied: Odoo 18 oeffnet einen Bestaetigungsdialog "Verkaufsauftrag stornieren" (Assistent `sale.order.cancel`) mit "Senden und stornieren", "Stornieren", "Verwerfen" |
| Setze auf Angebot (`action_draft`) | Auf Angebot setzen (`action_draft`) | 1:1 (in beiden Systemen nur im Status Storniert) |
| Sperre (`action_done`) | Sperren (`action_lock`) | gleiche Funktion, Methodenname geaendert |
| Entsperren (`action_unlock`) | Entsperren (`action_unlock`) | 1:1 |
| Drucken (`print_quotation`, Kopf-Button) | Menue "Drucken" im Zahnrad mit 4 Berichten | gleiche Funktion, anderer Ort (Odoo-18-Standard) |
| Rechnung erzeugen (Aktion 425) | Rechnung erstellen (Aktion 428) | gleicher Assistent `sale.advance.payment.inv`, neue Aktions-ID |
| Per E-Mail versenden (`action_quotation_send`) | Per E-Mail versenden | 1:1 |
| Proformarechnung senden | Pro-forma-Rechnung senden | 1:1, Wortlaut |
| Wiederherstellungs-E-Mail senden (`action_recovery_email_send`) | entfaellt | Website-Kaufvorgang; in Odoo 11 **0 verworfene Warenkoerbe** und 0 versandte Wiederherstellungs-Mails |
| (keine Entsprechung) | Vorschau (`action_preview_sale_order`) | Odoo-18-Zusatz (oeffnet die Kundenvorschau des Angebots) |
| (keine Entsprechung) | Transaktion erfassen / stornieren | Odoo-18-Zusatz (Zahlungen) |

Druckberichte mit Bindung an `sale.order`:

```
Odoo 11: Angebot/Auftrag (sale.report_itk_saleorder), Angebot / Auftrag ORG, Proformarechnung
Odoo 18: PDF-Angebot (sale.report_saleorder), Angebot/Auftrag (sale.report_saleorder_raw),
         ITK-Angebot/Auftrag (itk_reports.report_itk_saleorder), PRO-FORMA-Rechnung
```

## 2. Smart Buttons

```
Odoo 11 (7, alle mit "invisible wenn Zaehler 0")
  action_open_subscriptions   Abonnementanzahl      (itk_subscription)
  action_view_invoice         Rechnungen
  action_view_delivery        Warenauslieferung     (sale_stock)
  action_view_timesheet       Zeiterfassung         (sale_timesheet)
  action_view_project_ids     Projekte               (sale_timesheet)
  action_view_task            Aufgaben               (sale_timesheet)
  action_view_transaction     Zahlungen              (sale_payment)

Odoo 18 (3, im Testbestand alle ausgeblendet, weil die Zaehler 0 sind)
  action_open_subscriptions   Abonnements           (itk_subscription)
  action_view_invoice         Rechnungen
  action_view_purchase_orders Einkauf               (neu, sale_purchase)
```

| Odoo 11 Smart Button | Odoo 18 | Bewertung |
|---|---|---|
| Abonnementanzahl (`action_open_subscriptions`) | Abonnements | 1:1, Beschriftung |
| Rechnungen (`action_view_invoice`) | Rechnungen | 1:1 |
| Warenauslieferung (`action_view_delivery`) | entfaellt | `sale_stock` nicht installiert (Entscheidung Session 119) |
| Zeiterfassung, Projekte, Aufgaben | entfaellt | `sale_timesheet` nicht installiert (Entscheidung Session 120) |
| Zahlungen (`action_view_transaction`) | entfaellt als Zaehler-Button | Odoo 18 fuehrt Zahlungen ueber `transaction_ids`; kein Zaehler-Smart-Button |
| (keine Entsprechung) | Einkauf (`action_view_purchase_orders`) | Odoo-18-Zusatz (sale_purchase) |

Alle Odoo-18-Smart-Buttons sind wie in Odoo 11 ausgeblendet, solange der Zaehler 0 ist - im
Klicktest bestaetigt.

## 3. Buttons im Bereich der Auftragszeilen

```
Odoo 11: keine eigenen Buttons im Zeilenbereich (Zeilen werden ueber die Liste gepflegt)
Odoo 18: action_add_from_catalog (Aus Katalog hinzufuegen), action_open_discount_wizard (Rabatt),
         button_add_to_order (Zum Auftrag hinzufuegen, Reiter Optionale Produkte),
         action_update_taxes (Steuern aktualisieren)
```

Alle vier sind Odoo-18-Zusatzfunktionen und bleiben erhalten (Entscheidung: Zusatzfunktionen
bleiben).

## 4. Klicktest

```
Ablauf: Testauftrag per RPC anlegen (Entwurf) -> im Browser oeffnen -> Buttons klicken ->
        Statuswechsel als Nebenwirkung pruefen -> Storno ueber den Assistenten -> Testauftrag loeschen

Ergebnis lokal (24.09.2026): 26 OK / 0 FEHL
  - Statusleiste "Angebot", Kopf-Buttons "Per E-Mail versenden", "Bestätigen", "Vorschau",
    "Stornieren" sichtbar
  - keine Smart Buttons bei Zaehler 0
  - Zahnradmenue enthaelt "Drucken"; Untermenue bietet PDF-Angebot, PRO-FORMA-Rechnung,
    Angebot/Auftrag, ITK-Angebot/Auftrag
  - "Per E-Mail versenden" oeffnet den Assistenten "Angebot senden" (mit Betreff und Text);
    ohne Senden geschlossen
  - "Vorschau" oeffnet die Kundenvorschau des Angebots (/my/orders/<id>)
  - "Bestätigen" bestaetigt den Auftrag; der Auftrag ist danach automatisch gesperrt
    (Einstellung "Bestellungen automatisch sperren" ist aktiv) -> Button "Entsperren" sichtbar,
    nach dem Entsperren "Sperren"
  - Smart Buttons gegen die Zaehler geprueft: Rechnungen, Abonnements, Einkauf bei Zaehler 0
    ausgeblendet
  - "Stornieren" oeffnet den Bestaetigungsdialog mit den Knoepfen "Stornieren"
    (name=action_cancel) und "Senden und stornieren" (name=action_send_mail_and_cancel);
    "Verwerfen" schliesst den Dialog ohne Storno (Status bleibt Verkaufsauftrag)
  - "Auf Angebot setzen" (echter Klick) fuehrt den stornierten Auftrag zurueck auf Angebot
  - 0 JavaScript-Fehler, 0 RPC-Fehler
  - Testauftrag wieder geloescht (0 verbleibend)

Ergebnis VM: folgt nach dem Deploy (Pull, Container-Neustart, Modul-Upgrade).
Screenshots: Desktop\Odoo18-Abnahme-Session121\06_Buttons_Angebot_*.png,
07_Button_Email_Assistent_*.png, 08_Button_Bestaetigt_*.png, 09_Button_Storno_Dialog_*.png
```

**Befund (Funktionsunterschied):** In Odoo 18 storniert `action_cancel` nicht mehr direkt, sondern
oeffnet den Assistenten `sale.order.cancel` (Bestaetigungsdialog mit optionalem E-Mail-Versand).
Derselbe Weg gilt fuer Aufrufe per RPC. Bei der Datenmigration ist das unerheblich; fuer
Schulung/Bedienung ist es eine erklaerenswerte Abweichung zu Odoo 11.

**Befund (Einstellung):** "Bestellungen automatisch sperren" (`sale.group_auto_done_setting`) ist
in der Odoo-18-Testdatenbank aktiv. Folge: ein bestaetigter Auftrag ist direkt gesperrt und muss
zum Aendern erst entsperrt werden. In Odoo 11 war das nicht so (Sperre nur ueber den Button
"Sperre"). Bewertung: Odoo-18-Standardverhalten, keine Anpassung vorgeschlagen; fuer die
Anwenderschulung dokumentiert.

## 5. Nachweise und Status

```
scripts/analyse_verkauf_teil3_buttons.py       Button-Inventar Odoo 11 / Odoo 18 lokal / VM
scripts/browser_verkauf_buttons_klicktest.py   lokaler Klicktest 26 OK / 0 FEHL
Testdaten                                     Testauftrag angelegt und wieder geloescht
Odoo 11 Prod                                  ausschliesslich lesend
```

**STATUS: TEIL 3, SCHRITT 2 - Buttons und Smart Buttons verglichen (Analyse lokal und VM-Daten),
Klicktest lokal erfolgreich. Klicktest auf der VM offen (nach dem Deploy).**
