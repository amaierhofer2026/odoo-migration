# Odoo 11 gegen Odoo 18 - Bereich Abrechnung: Oberflaechenangleichung (Odoo-11-Wortlaut)

Stand: 30.09.2026, Session 122. Status des Bereichs Abrechnung: **IN ARBEIT** (die frueher
gesetzte Abschlussmarkierung wurde auf Wunsch von Anna zurueckgenommen).
Odoo 11 wird ausschliesslich gelesen, geaendert wird nur Odoo 18. Keine Datenmigration.

Grundlage: `scripts/erhebe_abrechnung_menue.py` (Menuebaum, Filter, Gruppierungen, Suchfelder
aus beiden Systemen) und `scripts/browser_abrechnung_oberflaeche.py` (Browser-Abnahme).

## 1. App- und Menuebezeichnungen

Odoo 11 fuehrt die App sichtbar als **Abrechnung**; Odoo 18 nannte sie **Rechnungsstellung**.
Anglichen (sichtbare Bezeichnung de_DE, technische Menue-IDs und Modulnamen unveraendert):

```
vorher (Odoo 18)        nachher (Odoo-11-Wortlaut)   Stelle
Rechnungsstellung   ->  Abrechnung                   App-Wurzel
Kunden              ->  Verkauf                      Abrechnung
Lieferanten         ->  Einkauf                      Abrechnung
Gutschriften        ->  Kunden-Gutschriften          Abrechnung/Verkauf
Rueckerstattungen   ->  Lieferanten-Gutschriften     Abrechnung/Einkauf
Produkte            ->  Verkaufbare Produkte         Abrechnung/Verkauf
Produkte            ->  Einkaufbare Produkte         Abrechnung/Einkauf
Buchhaltung         ->  Finanzen                     Abrechnung/Konfiguration
Steuerpositionen    ->  Steuerzuordnung              Abrechnung/Konfiguration/Finanzen
Banken              ->  Bankkonten                   Abrechnung/Konfiguration
Online-Zahlungen    ->  Zahlungen                    Abrechnung/Konfiguration
```

Umgesetzt ueber `scripts/apply_abrechnung_labels.py` (Abschnitt "App- und Menuebezeichnungen"),
also zusammen mit dem Label-Abgleich nach jedem Upgrade erneut gesetzt und geprueft.
Nachweis lokal: 12 Menues gesetzt, 0 Abweichungen. VM: 20 gesetzt, 0 Abweichungen.

## 2. Filter der Rechnungsliste (account.move)

Odoo 11 (account.invoice) hatte diese Filter; alle sind in Odoo 18 vorhanden, zwei wurden
ergaenzt (Modul `itk_account_migration`, `views/account_move_filters.xml`):

```
Odoo-11-Filter            Odoo 18
Entwurf                   vorhanden
Offen                     ergaenzt (state = gebucht und Zahlungsstatus offen/teilweise)
Bezahlt                   ergaenzt (Zahlungsstatus bezahlt)
Ueberfaellig              vorhanden
Meine Rechnungen          vorhanden
Meine Aktivitaeten        ergaenzt (Aktivitaet beim angemeldeten Benutzer)
Verspaetete Aktivitaeten  ergaenzt (flach sichtbar, wie in Odoo 11)
Heutige Aktivitaeten      ergaenzt (flach sichtbar)
Anstehende Aktivitaeten   ergaenzt (flach sichtbar)
```

Odoo-18-Zusatzfilter bleiben vollstaendig erhalten (im Browser nachgewiesen):
Gebucht, Abgebrochen, Nicht gesendet, Ausgangsrechnungen, Gutschriften, Zu pruefen,
Peppol bereit, Zu zahlen, In Zahlung.

## 3. Gruppierungen der Rechnungsliste

Odoo 11 bot: Partner, Verkaeufer, Status, Rechnungsdatum, Faelligkeit.
In Odoo 18 hiessen die gleichbedeutenden Eintraege teils anders; jetzt stehen beide
Schreibweisen zur Verfuegung (Odoo-11-Wortlaut ergaenzt, Odoo-18-Eintraege unveraendert
erhalten):

```
Odoo 11        Odoo 18 vorher        Umsetzung
Partner        Kunde                 "Partner" ergaenzt (Gruppierung nach Partner)
Verkaeufer     Vertriebsmitarbeiter  "Verkaeufer" ergaenzt
Status         Status                vorhanden
Rechnungsdatum Rechnungsdatum        vorhanden
Faelligkeit    Faelligkeitsdatum     "Faelligkeit" ergaenzt
```

Odoo-18-Zusatzgruppierungen (Verkaufsteam, Peppol-Status, Zahlungsmethode, Journal,
Buchungsdatum) bleiben erhalten.

## 4. Suchfelder der Rechnungsliste

Odoo 11: date, journal_id, number, partner_id, team_id, user_id.
Odoo 18: amount_total, date, invoice_date, invoice_user_id, itk_o11_invoice_number,
journal_group_id, journal_id, line_ids, name, next_payment_date, partner_id,
payment_reference, ref, team_id.
Alle Odoo-11-Suchfelder sind abgedeckt; die Odoo-18-Zusatzfelder bleiben erhalten.

## 5. Browser-Abnahme

Pruefskript `scripts/browser_abrechnung_oberflaeche.py` (echter Browser, angemeldet als
Administrator, Sprache de_DE):

```
lokal : 34 OK / 0 FEHL  (App-Abschnitte, Untermenues, Odoo-11-Filter, Zusatzfilter,
                          Gruppierungen im Odoo-11-Wortlaut)
VM    : 34 OK / 0 FEHL  (Lauf nach dem Deploy auf k001959vsx.ipax.at)
```

## 6. Bewusste Abweichungen (Stand jetzt)

```
1. Die acht Odoo-11-Berichtsassistenten (Audit Journale, alter Partner Saldo,
   Umsatzsteuerbericht, Rechnungsanalyse, Bilanz/Gewinn und Verlust, vorlaeufige Bilanz,
   Umsaetze nach Konten, Partner-Kontoauszug) existieren in Odoo 18 Community nicht.
   Entschieden: kein Enterprise-Modul; Nachbau nur bei nachgewiesenem Bedarf.
2. Odoo-18-Zusatzfunktionen und -menues bleiben erhalten und werden nicht entfernt:
   Eingaenge (Zahlungseingaenge), Pruefpfad, Rechnungsanalyse, Abrechnungspositionen,
   Peppol-Menues, Kostenstellenplaene/Verteilungsschluessel, Dashboard.
3. Menuepositionen verschieben sich technisch bedingt (z. B. Zahlungsbedingungen liegen in
   Odoo 18 unter Konfiguration > Rechnungsstellung). Die Bezeichnung entspricht Odoo 11.
4. Odoo 11 "Kostenstellenkonten" und "Kostenstellen Tags" haben in Odoo 18 keine
   1:1-Entsprechung (dort Kostenstellen, Kostenstellenplaene, Verteilungsschluessel);
   keine Angleichung, weil fachlich nicht eindeutig gleich.
5. Odoo 11 "Kontoauszuege/Bankauszuege" werden nicht genutzt (0 Belege) und daher nicht
   angeglichen.
```

## 7. Offene Arbeiten fuer die Abnahme

```
a) Browser-Durchgang Menuepunkt fuer Menuepunkt fuer die noch nicht durchgegangenen
   Bereiche: Dashboard, Buchungen, Stammdaten, Berichte, Konfiguration (Untermenues),
   Zahlungen/Gutschriften-Formulare.
b) VM-Browser-Lauf: erledigt (34 OK / 0 FEHL, Stand 30.09.2026).
c) Liste der verbleibenden bewussten Abweichungen (Abschnitt 6) nach dem Durchgang
   ergaenzen.
Der Bereich Abrechnung bleibt bis dahin IN ARBEIT.
```
