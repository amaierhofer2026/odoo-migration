# Abrechnung: Pflichtfeld "Partner" im Rechnungsformular (Session 126, 05.10.2026)

## Anlass

Meldung von Anna aus der manuellen Kontrolle: Beim blossen Oeffnen des Menuepunkts
"Abrechnung > Verkauf > Eingaenge" (und "Einkauf > Eingaenge") erscheint rechts die Meldung
**"Ungueltige Felder: Partner"**, ohne dass etwas geaendert, gespeichert oder angelegt wurde.

Zuordnung: Anna hatte den Bereich zunaechst irrtuemlich dem Modul **Abonnements** zugeordnet und
diese Zuordnung am 05.10.2026 ausdruecklich korrigiert. Der Fehler und die weitere Pruefung
gehoeren **ausschliesslich zu Abrechnung**; im Modul Abonnements lag kein technischer Befund vor
und es wurde dort nichts geaendert.

## Was gemessen wurde (read-only, beide Instanzen)

1. **Der genannte Menuepfad existiert so nicht.** Die App "Abonnements" (Menue-Wurzel 586) hat auf
   lokaler Instanz und VM **dieselben 10 Menuepunkte** und darunter **keinen** Abschnitt "Verkauf"
   und **keinen** Menuepunkt "Eingaenge":
   `Abonnements`, `Abo-Ansichten`, `Abonnement Produkte`, `Abonnements`, `Endet in weniger als
   7 Monaten`, `Zu erneuernde Abonnements`, `Berichtswesen`, `Einstellungen`, `Gruende fuer
   Beendigung`, `Vorlagen fuer Abonnements`.
   Auch Odoo 11 kennt keinen solchen Pfad (App "Abonnements" 379, gleiche Struktur).
   Die einzigen Menuepunkte "Eingaenge" in Odoo 18 sind:
   - 198 `Abrechnung > Verkauf > Eingaenge`  -> Aktion 360, Modell `account.move`, Domain
     `[('move_type','=','out_receipt')]`, Kontext `{'default_move_type': 'out_receipt'}`
   - 205 `Abrechnung > Einkauf > Eingaenge` -> Aktion 361, Modell `account.move`,
     Domain `[('move_type','=','in_receipt')]`
   - 928 `Lager > Vorgaenge > Transfers > Eingaenge` (Server-Aktion, `stock.picking`)
2. **Anna hat genau diese beiden Menuepunkte geoeffnet.** Das Server-Protokoll der VM zeigt ihre
   Anmeldung und die Seitenaufrufe (ihre IP):
   `11:26:23  GET /odoo/action-360` und `11:26:31  GET /odoo/action-361`.
3. **Kein Serverfehler, keine Schreibzugriffe.** Im VM-Protokoll dieses Zeitraums gibt es keinen
   ERROR und keinen `write`/`create`-Aufruf. Ihre Aufrufe: `account.move/get_views`,
   `account.move/web_search_read`, danach die beiden Menueaufrufe.
4. **Beide Menuepunkte oeffnen heute fehlerfrei** - auf lokaler Instanz und auf der VM, per URL
   und per echtem Menueklick (Sweep ueber 21 Menuepunkte des Abo- und Abrechnungsbereichs,
   zwei Klickfolgen im Browser). Kein Dialog, keine Meldung.
5. **Die Meldung ist eine Client-Meldung des Odoo-18-Webclients.** Sie stammt aus
   `web/static/src/model/relational_model/record.js` (`"Invalid fields: "`, deutsch
   "Ungueltige Felder: ") und listet die **Beschriftungen** aller Felder, die in der Ansicht
   pflichtig sind und leer bleiben, wenn der Datensatz gespeichert werden soll.
   "Partner" ist die Feldbeschriftung von `account.move.partner_id`
   (`string='Partner'`, `required=False`).
   Eine Servermeldung ist es nicht: `Invalid fields` gibt es serverseitig nicht, und im
   Serverprotokoll steht dazu nichts.

## Ursache

- Odoo 11 fuehrte `account.invoice.partner_id` **modellpflichtig** (`required=True`).
- Odoo 18 fuehrt `account.move.partner_id` **nicht** pflichtig (`required=False`, gemessen mit
  `fields_get`); nur Journal, Buchungsdatum, Waehrung und Typ sind Modellpflichtfelder.
- Der ITK-Kopfblock (`views/account_move_form_kopf.xml`, Ansicht
  `account.move.form.itk.o11.kopfbereich`) setzte das Feld zusaetzlich in der Ansicht auf
  `required="1"` - gedacht als Angleichung an Odoo 11.
- Folge: Der Client behandelt `Kunde` als Pflichtfeld. **Jeder** Datensatz ohne Partner ist damit
  nicht speicherbar; beim Speichern erscheint genau die Meldung **"Ungueltige Felder: Partner"**.
  Es gibt im gesamten Bereich Abrechnung/Abonnements **genau eine** solche Stelle: der Audit
  `scripts/pruefe_pflichtfelder.py` meldet vor der Korrektur
  `account.move partner_id 'Partner' leer=2` (lokal) und leer=3 (VM) und sonst nichts.
- Die betroffenen Datensaetze sind bestehende Entwuerfe aus frueheren Testlaeufen, die vor dieser
  Sitzung angelegt wurden:
  lokal id 15, 16 (`out_invoice`, Entwurf, 09./10.07.2026)
  VM id 15, 16 (`out_invoice`) und id 97 (`out_refund`, 01.10.2026)

## Korrektur

`views/account_move_form_kopf.xml`: `required="1"` am Feld `partner_id` entfernt (Modulversion
18.0.1.13.0). Die Odoo-18-Logik (Modell, Pruefungen beim Buchen) bleibt unveraendert.
Kein Feld umbenannt, keine Datenlogik geaendert.

## Nachweis im echten Browser (A/B auf derselben Ansicht, gleiche Instanz, gleicher Datensatz)

`scripts/browser_pflichtfeld_ab.py <instanz> <testbeleg-id>` schreibt die Ansicht voruebergehend
ueber die ORM mit bzw. ohne `required="1"` und setzt sie am Ende auf den Modulstand zurueck.

| Phase | Ansicht | Datensatz ohne Partner: Leistungszeitraum geaendert, dann Speichern | Ergebnis |
|---|---|---|---|
| A (alt) | mit `required="1"` | Meldung **"Ungueltige Felder: Partner"**, Speichern blockiert | nicht gespeichert |
| B (neu) | ohne `required="1"` | keine Meldung | gespeichert |

Gemessen auf lokaler Instanz (Testbeleg 132/133) und auf der VM (Testbeleg 148), jeweils identisch:
`A: Meldung=True, Wert gespeichert=False` / `B: Meldung=False, Wert gespeichert=True`.
Bilder: `Desktop/Odoo18-Abnahme-Session126/pflichtfeld_partner/<instanz>/A_mit_required.png`,
`B_ohne_required.png` (in A ist "Kunde" rot und das Feld rot umrandet, in B nicht).

Sichtbare Folge der Korrektur: Ein leerer Kunde wird nicht mehr als Pflichtfeld gekennzeichnet
(kein rotes Label, kein roter Rahmen). Die Schriftstaerke der Beschriftung ist unveraendert
(gemessen `font-weight: 500` in beiden Varianten).

## Abnahme (14 Pruefungen je Instanz, 0 Fehl)

`scripts/browser_pflichtfeld_abnahme.py <instanz> <testbeleg-id>`:

1. Testbeleg (Entwurf ohne Partner) oeffnet ohne Meldung; Feld Kunde vorhanden und leer;
   Kunde nicht mehr als Pflichtfeld gekennzeichnet (`o_required_modifier` fehlt)
2. Aenderung speichern: keine Meldung, Wert wirklich gespeichert
3. Kunde setzen und speichern: keine Meldung, Partner korrekt zugeordnet
   (`[79, '[20201] Magistrat der Stadt Villach']`)
4. `Verkauf > Eingaenge` und `Einkauf > Eingaenge` oeffnen ohne Meldung
5. Neu anlegen moeglich; Reiter "Andere Informationen" und Statusleiste vorhanden
   (keine Odoo-18-Zusatzfunktion entfernt)

Ergebnis: **lokal 14 OK / 0 FEHL, VM 14 OK / 0 FEHL.**
Testbelege: lokal angelegt 132/133 und wieder entfernt, VM angelegt 148 und wieder entfernt;
Bestand lokal 40, VM 62 (vorher/nachher gleich), keine Reste.

## Pruefung der uebrigen Ansichten

`scripts/pruefe_pflichtfelder.py lokal|vm` prueft fuer `account.move`, `account.move.line`,
`account.payment`, `sale.subscription`, `sale.subscription.line`, `sale.subscription.template`,
`product.template`, `account.journal`, `account.analytic.account`, `helpdesk.ticket` jede
sichtbare Pflichtfeldkennzeichnung in allen Formular- und Listenansichten gegen die vorhandenen
Datensaetze.

Die Abo-Modelle standen nur deshalb mit in der Liste, weil Anna den Fehler zunaechst dem Modul
Abonnements zugeordnet hatte (am 05.10.2026 korrigiert: der Fehler gehoert zu Abrechnung). Dort
wurde nichts geaendert; die Pruefung war rein lesend.

- Vor der Korrektur: **ein** Befund (`account.move.partner_id`, leer=2 lokal / 3 VM).
- Nach der Korrektur: **kein** Befund auf beiden Instanzen.
- Weitere stille View-/Pflichtfeldfehler im Abrechnungsbereich: keine.

## Abschlusscheck

- Feldbeschriftungen: lokal 155 Feldpaare / 0 Abweichungen, VM ebenso (nach dem Upgrade wurde
  `scripts/apply_abrechnung_labels.py --instanz vm` nachgezogen: 20 Labels gesetzt - das Upgrade
  setzt deutsche Feldbeschriftungen zurueck, siehe Betriebslehre unten)
- Ansicht `account.move.form.itk.o11.kopfbereich`: lokal und VM byteidentisch
  (sha256 `ba832b7d27fee7da`), ohne `required` am Partnerfeld
- Modulversion `itk_account_migration` 18.0.1.13.0 lokal = VM
- lokal/VM-Vergleich: Menuezeilen 0/0 Abweichungen, Modulversionen identisch
- Regression Verkauf und Abonnements: 886 OK / 0 FEHL ueber 11 Prueflaeufe

## Betriebslehre

1. **Nach jedem Modul-Upgrade** die deutschen Feldbeschriftungen neu setzen
   (`scripts/apply_abrechnung_labels.py --instanz lokal|vm`), sonst stehen auf der VM wieder die
   englischen Quelltexte (hier 20 Abweichungen). Danach `check_abrechnung_labels.py --instanz beide`
   muss 155/0 zeigen.
2. `installed_version` ist in Odoo 18 ein berechnetes Feld; nach einem Upgrade ueber einen zweiten
   Prozess zeigt der laufende Server erst nach `docker restart odoo18` / `docker compose restart
   odoo` die neue Version.
3. Pflichtfelder nie "aus Optik" in der Ansicht setzen oder entfernen: der Client prueft sie beim
   Speichern und blockiert vorhandene Datensaetze. Vor jeder Pflichtfeld-Kennzeichnung in der
   Ansicht messen, ob Odoo 18 das Feld selbst schon als pflichtig fuehrt.
4. Die Meldung "Ungueltige Felder: <Bezeichnung>" ist immer eine Client-Meldung aus
   `web/.../relational_model/record.js`; im Serverprotokoll steht dazu nichts. Zur Eingrenzung
   hilft: `scripts/pruefe_pflichtfelder.py` (Pflichtfeld leer?) und die Server-`GET /odoo/...`-
   Eintraege im Container-Protokoll (welche Seite wurde wirklich geoeffnet?).

## Werkzeuge

- `scripts/pruefe_pflichtfelder.py lokal|vm` - Audit Pflichtfeld vs. leere Datensaetze
- `scripts/browser_pflichtfeld_ab.py <instanz> <id>` - A/B-Nachweis im Browser
- `scripts/browser_pflichtfeld_abnahme.py <instanz> <id>` - Abnahme (14 Pruefungen)
- `scripts/_pf_testbeleg.py <instanz> anlegen|entfernen|pruefen` - Testbeleg ohne Partner

## Offen

- Der Fehler gehoert ausschliesslich zu Abrechnung: Anna hat bestaetigt, dass die Meldung beim
  Oeffnen von `Abrechnung > Verkauf > Eingaenge` auftrat; ihre erste Zuordnung zu "Abonnements" war
  ein Irrtum und wurde am 05.10.2026 korrigiert. Im Menueinventar gibt es "Verkauf > Eingaenge" nur
  in der App Abrechnung (Menuepunkt 198), passend zum VM-Protokoll (`/odoo/action-360`).
- Der genaue Ausloeser, der in ihrer Sitzung das Speichern eines partnerlosen Entwurfs angestossen
  hat, liess sich nicht reproduzieren (weder per URL, per Menueklick, per Sitzungswechsel, per
  Neuanlage noch durch Verlassen eines partnerlosen Entwurfs im Browser). Ursache und Wirkung der
  Meldung selbst sind belegt und behoben.
