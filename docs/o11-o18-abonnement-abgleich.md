# Abonnement: Abgleich Odoo 11 gegen Odoo 18

Stand: 02.10.2026. Odoo 11 (Produktion) ausschliesslich lesend. Pruefskripte:
`scripts/abgleich_abonnements_1_bestand.py` bis `..._5_filter_cron.py`,
`scripts/browser_abo_abnahme.py`, `scripts/abo_labels_setzen.py`.

## 1. Bestand

| Modell | Odoo 11 | Odoo 18 (VM) |
|---|---|---|
| sale.subscription | 1768 (open 1484, cancel 232, close 49, draft 3) | 17 (open 11, draft 2, pending 2, close 1, cancel 1) |
| sale.subscription.line | 2438 | 13 |
| sale.subscription.template | 5 | 5 |
| itk_subscription.noticeperiod | vorhanden | 3 Kuendigungsfristen |

Die Abonnement-Modelle sind in beiden Systemen dieselben (itk_subscription erweitert
sale.subscription). Nur Odoo 18 hat zusaetzlich mailing.subscription (Massenmailing, ohne Bezug).

## 2. Was bereits identisch war

- Menuebaum: Abonnements > Abonnements (Abonnements, Zu erneuernde Abonnements, Abonnement
  Produkte), Konfiguration > Vorlagen fuer Abonnements.
- Formularaufbau: gleiche Feldreihenfolge, gleiche Reiter ("Wiederkehrende Buchungen",
  "Einstellungen"), gleiche Knopfgruppe (Abonnement starten, Zu erneuern, schliessen,
  abbrechen, Erneuerungsangebot, Zusatzverkaeufe), gleiche Smart Buttons (Rechnungen, Verkauf).
- Suchansicht: alle Filter (Neu, Laufend, Zu erneuern, Abgeschlossen, Abgebrochen, Abgelaufen,
  Laeuft bald ab, Laeuft in weniger als 7 Monaten aus, Nicht zugewiesene Abonnements,
  Aktivitaetsfilter) und alle Gruppierungen (Status, Verkaeufer, Partner, Branche, Vorlage,
  Startmonat, Monatsende, Preisliste) - wortgleich.
- Listenansicht: gleiche Spalten in gleicher Reihenfolge.
- Cronjobs: "Verkaufsabonnement: Ablauf des Abonnements" (woechentlich) und
  "Verkaufsabonnement: wiederkehrende Rechnungen und Zahlungen erstellen" (taeglich), beide aktiv.
- Zustaende: Odoo 18 fuehrt zusaetzlich state=pending ("Zu erneuern") - Odoo-11-Zustaende
  draft/open/close/cancel sind vollstaendig vorhanden.

## 3. Angeglichen (umgesetzt)

| Stelle | vorher (Odoo 18) | jetzt (Odoo-11-Wortlaut) | Datei |
|---|---|---|---|
| Knopf | Abo-Auftrag schliessen | Aboauftrag schliessen | itk_subscription/i18n/de.po |
| Knopf | Abo-Auftrag abbrechen | Aboauftrag abbrechen | itk_subscription/i18n/de.po |
| Feldlabel | Vertragsend am | Vertragsende am | itk_subscription/i18n/de.po |
| Feldlabel | Rechnung manuell erstellen | Generate Invoice manually | itk_subscription/i18n/de.po |
| Feldlabel | Total (recurring_amount_total) | Gesamtbetrag | itk_subscription/i18n/de.po |
| Feldlabel | Multiplikationsfaktor (pro 1.000) | Multiplication Factor/Thsd | itk_multifactor/models/models.py |
| Listenkopf | Datum der naechsten Rechnung | Start-Datum des naechsten Leistungszeitraums | itk_subscription/views/sale_subscription_views.xml |

Die Aenderungen gelten fuer die Abonnementzeile (sale.subscription.line) und die Verkaufszeile
(sale.order.line) - beide tragen in Odoo 11 den Wortlaut "Multiplication Factor/Thsd".

## 4. Bewusst nicht uebernommen (Abweichungen dokumentiert)

| Feld/Stelle | Odoo 11 | Odoo 18 | Begruendung |
|---|---|---|---|
| activity_state | Beschriftung "Bundesland" | Activity State | In Odoo 11 ist das Feld falsch beschriftet (Aktivitaetsstatus, nicht Bundesland); die Fehlbeschriftung wird nicht kopiert |
| Knopf Erneuerungsangebot | "Erneuerungsabgebot" (Tippfehler) | Erneuerungsangebot | Tippfehler wird nicht uebernommen |
| message_*/activity_* (Chatter) | deutsch (Nachrichten, Abonnenten) | englisch | Standard-Chatterfelder; Odoo 18 liefert fuer mail noch keine deutsche Uebersetzung. Lokal und VM identisch, keine Abweichung zwischen den Systemen |
| message_channel_ids, message_last_post, message_unread(_counter) | vorhanden | entfallen | Odoo-18-Chatter kennt diese Felder nicht mehr; nicht migrationsrelevant |

## 5. Betriebswissen (wichtig)

Odoo ueberschreibt vorhandene Uebersetzungen bei einem Modul-Upgrade NICHT. Nach einer
Aenderung an .po-Dateien muss mit `--i18n-overwrite` aktualisiert werden:

- VM: `cd /opt/odoo18 && docker compose run --rm -T odoo odoo -u itk_subscription,itk_multifactor,itk_translation --i18n-overwrite -d odoo18_test --stop-after-init --no-http`
  danach `docker compose restart odoo`, danach `python scripts/apply_abrechnung_labels.py --instanz vm`.
- Lokal: `docker exec odoo18 odoo -u <module> --i18n-overwrite -d odoo18_test --db_host=db --db_user=odoo --db_password=<POSTGRES_PASSWORD> --stop-after-init --no-http`,
  danach `docker restart odoo18`, danach `python scripts/apply_abrechnung_labels.py --instanz lokal`.

Die .mo-Dateien werden von `scripts/abo_labels_setzen.py` mitkompiliert.

## 6. Browser-Abnahme (echter Browser, 02.10.2026)

| Pruefung | lokal | VM |
|---|---|---|
| Liste Spalten (Referenz, Kunde, Nutzungsvereinbarung vom, Start-Datum des naechsten Leistungszeitraums, Vertragsende-Datum, Preisliste, Verkaeufer, Wiederkehrender Preis, Status) | OK | OK |
| Knoepfe Aboauftrag schliessen / abbrechen | OK | OK |
| Label Vertragsende am | OK | OK |
| Label Generate Invoice manually | OK | OK |
| Statusband Neu / Laufend / Zu erneuern | OK | OK |
| Smart Buttons Rechnungen / Verkauf | OK | OK |

Screenshots: `Desktop/Odoo18-Abnahme-Session122/abonnement/` (abo_liste_*, abo_formular_*,
abo_zeilen_* je Instanz).
