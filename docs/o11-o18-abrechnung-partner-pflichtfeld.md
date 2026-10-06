# Abrechnung: Pflichtfeld "Partner" im Rechnungsformular (Session 126, 05.10.2026)

## Anlass

Meldung von Anna aus der manuellen Kontrolle: Beim Oeffnen bzw. Navigieren im Menuepunkt
"Abrechnung > Verkauf > Eingaenge" (und "Einkauf > Eingaenge") erscheint rechts die Meldung
**"Ungueltige Felder: Partner"**, ohne dass etwas bewusst geaendert oder gespeichert wurde.

Zuordnung: Anna hatte den Bereich zunaechst irrtuemlich dem Modul **Abonnements** zugeordnet und
diese Zuordnung am 05.10.2026 ausdruecklich korrigiert. Der Fehler und die weitere Pruefung
gehoeren **ausschliesslich zu Abrechnung**; im Modul Abonnements lag kein technischer Befund vor
und es wurde dort nichts geaendert.

## Fachliche Grundlage (Odoo 11, read-only gemessen)

| Feld | Odoo 11 | Odoo 18 |
|---|---|---|
| `partner_id` (Kunde/Partner) | **required=True** (Modell) | `required=False` (Modell, gemessen) |
| `journal_id` | required=True | required=True |
| `date_invoice` / `invoice_date` | required=False | required=False |
| Pruefung beim Buchen | - | keine Pruefung auf den Partner |

Odoo 11 fuehrte **alle** Rechnungsarten in `account.invoice`; die Modellpflicht galt damit fuer
Ausgangsrechnung, Kunden-Gutschrift, Eingangsrechnung und Lieferanten-Gutschrift gleichermassen.
In den Odoo-11-Produktivdaten gibt es **0 von 6301 Rechnungen und 0 von 10057 Zeilen ohne Partner** -
ein Beleg ohne Partner war in Odoo 11 nicht anlegbar.

In Odoo 18 gibt es weder eine Modellpflicht noch eine Buchungspruefung fuer `partner_id`. Die
fachliche Pflicht aus Odoo 11 muss deshalb **in der Ansicht** gehalten werden
(`required="1"` am Feld `partner_id` im ITK-Kopfblock).

## Was gemessen wurde (read-only, beide Instanzen)

1. **Der urspruenglich genannte Menuepfad existierte nicht.** Die App "Abonnements" (Menue-Wurzel
   586) hat lokal und auf der VM dieselben 10 Menuepunkte, darunter keinen Abschnitt "Verkauf" und
   keinen Menuepunkt "Eingaenge" (Odoo 11 ebenso, App 379). Die einzigen "Eingaenge"-Menuepunkte in
   Odoo 18: 198 `Abrechnung > Verkauf > Eingaenge` (Aktion 360, `account.move`,
   `move_type=out_receipt`), 205 `Abrechnung > Einkauf > Eingaenge` (Aktion 361) und 928
   `Lager > Vorgaenge > Transfers` (Server-Aktion, `stock.picking`).
2. **Annas Sitzung auf der VM** (Serverprotokoll, ihre IP): `11:26:23 GET /odoo/action-360` und
   `11:26:31 GET /odoo/action-361`; dazu `account.move/get_views` und `web_search_read`. Im selben
   Zeitraum **kein ERROR, kein write/create**.
3. **Die Meldung ist eine Client-Meldung des Odoo-18-Webclients** - Quelle
   `web/static/src/model/relational_model/record.js` (`"Invalid fields: "`, deutsch
   "Ungueltige Felder: "). Sie listet die **Beschriftungen** aller in der Ansicht pflichtigen,
   leeren Felder. Serverseitig gibt es keine solche Meldung; im Protokoll steht dazu nichts.

## Ursache der Meldung (nachtraeglich vollstaendig geklaert)

Nicht das Oeffnen loest die Meldung aus, sondern **Odoo 18 speichert ein offenes Formular
automatisch**:

    web/static/src/views/form/form_controller.js
      beforeVisibilityChange()   -> bei visibilitychange auf "hidden" (Tab-Wechsel, Fenster
                                    wechseln, Minimieren) ruft save() auf - OHNE Dirty-Pruefung
      beforeLeave()              -> beim Verlassen eines geaenderten Belegs (Breadcrumb, Menue)

    web/static/src/model/relational_model/record.js
      _save()  ->  if (!this._checkValidity({ displayNotification: true })) { return false; }
      ... erst DANACH werden Aenderungen ermittelt und gesendet

Das erklaert alle Beobachtungen:

- Die Meldung erscheint beim Tab-Wechsel bzw. Menueklick, ohne dass bewusst gespeichert wird.
- Es gibt **keinen** Serverzugriff: `_checkValidity` bricht **vor** dem Schreiben ab. Im Protokoll
  der Abnahme steht genau ein `account.move/web_save` - der erfolgreiche Speichern-Vorgang mit
  Partner. Beim Tab-Wechsel mit partnerlosem Beleg: kein Schreibaufruf.
- Der Datensatz bleibt unveraendert (Abnahme: `write_date` vorher = nachher).
- Die Meldung erscheint auch, wenn am Beleg selbst nichts geaendert wurde: `_save()` prueft die
  Pflichtfelder unabhaengig davon, ob es Aenderungen gibt.

Ohne `required="1"` in der Ansicht (Stand 18.0.1.13.0) faellt die Meldung aus - aber nur, weil
Odoo 18 das Pflichtfeld dann stillschweigend speichert und die Odoo-11-Fachlogik verloren ist.

## Korrektur (Stand 18.0.1.14.0)

- `views/account_move_form_kopf.xml`: `required="1"` am Feld `partner_id` **wieder gesetzt**
  (Modul 18.0.1.13.0 -> 18.0.1.14.0). Die fachliche Pflicht aus Odoo 11 bleibt damit erhalten.
- Kein Feld umbenannt, keine Datenlogik, keine State-/Zahlungs-/Buchungslogik geaendert, keine
  Odoo-18-Funktion entfernt.
- Sichtbare Folge: Ist der Kunde leer, ist die Beschriftung rot und das Feld rot umrandet
  (Odoo-18-Pflichtfeld-Kennzeichnung, DOM-Klasse `o_required_modifier`).

Die zuvor (18.0.1.13.0) entfernte Pflicht war ein Fehlschuss: sie hat die Meldung beseitigt, aber
die Odoo-11-Fachlogik abgeschafft und zugelassen, dass Belege ohne Partner gespeichert werden.

## Die drei partnerlosen Entwuerfe

| Instanz | id | Typ | Inhalt | angelegt | Bewertung |
|---|---|---|---|---|---|
| lokal | 15 | out_invoice | 2 Zeilen (Produkt A, Produkt C), 2,40 EUR | 09.07.2026 | Testrest |
| lokal | 16 | out_invoice | **0 Zeilen**, 0,00 EUR | 10.07.2026 | Testrest (leerer Neu-Versuch) |
| VM | 97 | out_refund | **0 Zeilen**, 0,00 EUR | 01.10.2026 | Testrest (leerer Neu-Versuch) |

Alle drei: kein Name, keine Nummer, kein Rechnungsdatum, kein Referenzbeleg, kein Kunde, angelegt
von "Administrator" in frueheren Testsitzungen (die Zeilen tragen die Testprodukte "Produkt A"/"Produkt C").
Es sind **keine Produktivdaten**: Odoo 11 hat 0 von 6301 Rechnungen ohne Partner, sie koennen also
nicht aus der Migration stammen. Ergebnis der Pruefung: **alte Testreste, teilweise leere
Neu-Versuche**. Ein Beleg ohne Partner ist in Odoo 11 nie entstanden und kann auch in Odoo 18 nicht
gebucht werden. Sie wurden **nicht geloescht** (Entscheidung von Anna) - solange sie offen sind,
meldet Odoo 18 beim Tab-Wechsel die Meldung, weil diese Datensaetze die Odoo-11-Pflicht verletzen.

## Nachweis im echten Browser

`scripts/browser_partnerpflicht_abnahme.py lokal|vm <gueltige_id> <partnerlose_id>`:

```
1. Menue Verkauf > Eingaenge und Einkauf > Eingaenge        keine Meldung
2. gueltiger Beleg (mit Partner), Tab-Wechsel               keine Meldung
3. Entwurf ohne Partner: oeffnen                            keine Meldung
   Entwurf ohne Partner: Tab-Wechsel                        "Ungueltige Felder: Partner"
   Datensatz danach unveraendert                            write_date 09.07.2026 = 09.07.2026
4. neuer Beleg ohne Partner, Speichern                      wird verhindert (Meldung), kein
                                                            Datensatz angelegt
5. Partner setzen, Speichern                                gelingt, Partner korrekt gesetzt
6. Testbeleg entfernt, Bestand                              unveraendert (lokal 40, VM 62)
```

Ergebnis: **lokal 13 OK / 0 FEHL, VM 13 OK / 0 FEHL** (Ablauf identisch).
Testbelege: lokal id 134 und VM id 149 angelegt und wieder entfernt.
Bilder: `Desktop/Odoo18-Abnahme-Session126/partnerpflicht/<instanz>/`
(`03b_tabwechsel_meldung.png` zeigt die Meldung bei offenem Beleg 15,
`03_entwurf_ohne_partner.png` den roten Kunden, `04_neu_ohne_partner.png` den verhinderten
Speicherversuch, `05_mit_partner_gespeichert.png` den erfolgreichen).

## Messung des Mechanismus (A/B, weiterhin gueltig)

`scripts/browser_pflichtfeld_ab.py <instanz> <id>` schreibt die Ansicht voruebergehend ueber die
ORM mit bzw. ohne `required="1"` und setzt sie am Ende zurueck:

| Phase | Ansicht | Speichern eines partnerlosen Belegs |
|---|---|---|
| A | mit `required="1"` | Meldung "Ungueltige Felder: Partner", **nicht** gespeichert |
| B | ohne `required="1"` | keine Meldung, gespeichert |

Belegt: `required="1"` ist die Ursache der Meldung und die einzige Stelle, an der die
Odoo-11-Pflicht im Odoo-18-Bestand wirkt.

## Audit auf weitere stille Pflichtfeld-/View-Fehler

`scripts/pruefe_pflichtfelder.py lokal|vm` prueft fuer `account.move`, `account.move.line`,
`account.payment`, `sale.subscription`, `sale.subscription.line`, `sale.subscription.template`,
`product.template`, `account.journal`, `account.analytic.account`, `helpdesk.ticket` jede
sichtbare Pflichtfeldkennzeichnung in allen Formular- und Listenansichten gegen die vorhandenen
Datensaetze.

Die Abo-Modelle standen nur deshalb mit in der Liste, weil Anna den Fehler zunaechst dem Modul
Abonnements zugeordnet hatte (am 05.10.2026 korrigiert). Dort wurde nichts geaendert; die Pruefung
war rein lesend.

- Befund im Abrechnungsbereich: **ein** Eintrag - `account.move.partner_id`, leer=2 (lokal) / 3 (VM).
  Das sind die drei oben bewerteten Testreste. Fachlich richtig: diese Datensaetze verletzen die
  Odoo-11-Pflicht und koennen in Odoo 18 nicht gebucht werden.
- Weitere stille View-/Pflichtfeldfehler: keine, auf beiden Instanzen.

## Abschlusscheck

- Feldbeschriftungen: lokal 155 Feldpaare / 0 Abweichungen, VM ebenso (nach jedem Upgrade
  `apply_abrechnung_labels.py --instanz vm`)
- Ansicht `account.move.form.itk.o11.kopfbereich`: lokal und VM byteidentisch
  (sha256 `0b4ce8ace8a3...`), `required="1"` gesetzt
- Modulversion `itk_account_migration` 18.0.1.14.0 lokal = VM
- Regression Verkauf und Abonnements: 886 OK / 0 FEHL ueber 11 Prueflaeufe

## Betriebslehre

1. **Odoo 18 speichert Formulare automatisch** (Tab-Wechsel, Verlassen eines geaenderten Belegs).
   Pflichtfelder wirken dadurch auch ohne bewusstes Speichern - genau hier entstand die Meldung.
   Kein Serverzugriff, weil `_checkValidity` vor dem Schreiben abbricht.
2. **Pflichtfeldlogik nicht aus Optik aendern** - aber auch nicht abschalten, um eine Meldung
   loszuwerden. Erst messen, was Odoo 11 vorschrieb und was Odoo 18 erzwingt; fehlt die
   Erzwingung in Odoo 18, gehoert die Pflicht in die Ansicht.
3. **Nach jedem Modul-Upgrade** die deutschen Feldbeschriftungen neu setzen
   (`apply_abrechnung_labels.py --instanz lokal|vm`), sonst stehen auf der VM die englischen
   Quelltexte (05.10.2026: 20 Abweichungen).
4. `installed_version` ist in Odoo 18 berechnet; erst `docker restart` / `docker compose restart`
   zeigt die neue Version.
5. Die Meldung "Ungueltige Felder: <Bezeichnung>" ist immer eine Client-Meldung aus
   `web/.../relational_model/record.js`; im Serverprotokoll steht dazu nichts. Zur Eingrenzung:
   `scripts/pruefe_pflichtfelder.py` und die `GET /odoo/...`-Zeilen im Containerprotokoll.

## Werkzeuge

- `scripts/pruefe_pflichtfelder.py lokal|vm` - Audit Pflichtfeld vs. leere Datensaetze
- `scripts/browser_partnerpflicht_abnahme.py lokal|vm <gueltige_id> <partnerlose_id>` - Abnahme
  (13 Pruefungen: Menue, gueltiger Beleg, partnerloser Entwurf, neuer Beleg ohne/mit Partner)
- `scripts/browser_pflichtfeld_ab.py lokal|vm <id>` - A/B-Nachweis des Mechanismus
- `scripts/_pf_testbeleg.py lokal|vm anlegen|entfernen|pruefen` - Testbeleg ohne Partner

## Offen

- Der genaue Ablauf in Annas Sitzung ist rekonstruiert: Beleg ohne Partner geoeffnet (id 15/16/97),
  dann Tab-Wechsel bzw. Menueklick -> automatisches Speichern -> Meldung. Nicht rekonstruierbar ist,
  **welchen** der drei Belege sie offen hatte; das Protokoll zeigt in dem Zeitfenster nur die beiden
  Menueaufrufe und keine Datensatz-Lesevorgaenge (die Seiten waren vollstaendig neu geladen).
- Entscheidung von Anna offen: ob die drei partnerlosen Testreste (lokal 15/16, VM 97) geloescht
  werden sollen. Solange sie existieren, meldet Odoo 18 bei ihrem Tab-Wechsel die Meldung - fachlich
  korrekt, weil diese Datensaetze die Odoo-11-Pflicht verletzen.
