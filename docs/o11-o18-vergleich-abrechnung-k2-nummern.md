# Odoo 11 -> Odoo 18: Bereich Abrechnung, K2 - historische Rechnungsnummern

Stand: 30.09.2026, Session 122
Status: **K2 ANALYSIERT UND GEPRUEFT - nichts migriert, keine Nummer geaendert**

Auftrag (Anna, 30.09.2026): K2 vollstaendig klaeren, weil die historischen Rechnungsnummern
kritisch sind.
- K2a: Odoo-18-konforme Loesung fuer die Doppelnummer R-25001 - eigene Sequenz/Gutschriftjournal,
  beide Nummern erhalten, oder muss eine Nummer neu vergeben werden? Die urspruengliche
  Odoo-11-Nummer muss in jedem Fall nachvollziehbar erhalten bleiben (ggf. eigenes
  unveraenderliches Feld wie "Odoo-11-Rechnungsnummer").
- K2b: Wie zaehlt Odoo 18 nach der spaeteren Uebernahme der historischen Nummern automatisch
  weiter - ohne Kollision? Noch keine Sequenz konfigurieren.
- K2c: Wie lassen sich gebuchte, migrierte Rechnungen nach der Migration gegen unbeabsichtigtes
  Umnummerieren schuetzen? Noch keine Aenderung umsetzen.

Rahmen: Odoo 11 Prod ausschliesslich read-only (RPC-Lesen). Odoo 18 wurde **nicht** geaendert -
alle Aussagen stammen aus dem Quellcode der Testumgebung (Odoo 18.0-20260817), dem
Datenbankschema (read-only Abfragen) und der Nachbildung des Odoo-18-Nummernregelwerks gegen die
echten Odoo-11-Nummern.

## 1. Ausgangslage in Odoo 11 (gemessen, read-only)

```
6.277 Rechnungen, davon 6.263 mit Nummer (14 Entwuerfe ohne Nummer)
alle Nummern im einen Journal "Ausgangsrechnungen (EUR)" (id 1), Praefix immer "R-"
237 Kunden-Gutschriften liegen im selben Journal wie die Rechnungen
Odoo-11-Eindeutigkeit: SQL-Constraint account_invoice_number_uniq
  = unique(number, company_id, journal_id, type)
```

Nummernkreis je Jahr (Zaehler numerisch ausgewertet, nicht alphabetisch):

```
Jahr  Anzahl  Stellen    kleinster Zaehler   groesster Zaehler
2019      66  5 und 7     R-19515             R-1900002
2020     732  5           R-20001             R-20732
2021     829  5           R-21001             R-21829
2022     828  5           R-22001             R-22828
2023     853  5           R-23001             R-23853
2024     861  5           R-24001             R-24861
2025     955  5           R-25001             R-25954
2026   1.139  5 und 6     R-26001             R-261139
```

Aufbau: "R-" + zweistelliges Jahr + laufende Nummer. Die laufende Nummer ist dreistellig
(R-26001, R-26989) und waechst bei Ueberschreitung in die Vierstelligkeit
(R-260990, R-260999, R-261000 bis R-261139). Die hoechste Rechnung 2026 ist daher
**R-261139**, nicht R-26989.

**Messkorrektur zu Teil 2 (datiert 30.09.2026):** In Dokument Teil 2 stand "2026: kleinste
R-26001, groesste R-26989". Diese Angabe entstand durch alphabetische Sortierung und ist falsch;
numerisch ist R-261139 die hoechste Nummer 2026. Inhalt der Aussage (Nummernkreis, Praefix,
Jahreswechsel) bleibt unveraendert; die Zahlenangabe wurde in Teil 2 als Nachtrag richtiggestellt.

**Doppelnummer (K2a): genau eine im gesamten Bestand**

```
R-25001 = id 9703  | out_invoice | 02.01.2025 | Magistrat der Stadt Wels      | 27.593,52
R-25001 = id 11531 | out_refund  | 06.02.2025 | Verein Gesundheitsland Kaernten | 1.474,76
                   |             |            | Ursprung (Odoo 11): R-25584
```
In Odoo 11 zulaessig, weil `type` Teil des eindeutigen Schluessels war; eine Rechnung und eine
Gutschrift durften also dieselbe Nummer tragen. Alle anderen 6.262 Nummern sind eindeutig.

## 2. Wie Odoo 18 Nummern vergibt (Regelwerk, aus dem Quellcode belegt)

```
1) Feld account.move.name: compute + inverse, readonly=False, store=True
   (addons/account/models/account_move.py Zeile 128) - die Nummer ist also grundsaetzlich
   schreibbar; im Formular erscheint bei einer Nummer unterhalb der hoechsten nur eine
   Warnung (_onchange_name_warning, Zeile 2411), keine Sperre.
2) Automatische Vergabe beim Buchen: sequence.mixin._set_next_sequence
   -> _get_next_sequence_format -> _get_last_sequence (addons/account/models/sequence_mixin.py
   Zeile 352, 311, 267). Ein bereits gesetzter Name wird nicht ueberschrieben.
3) "Letzte Nummer" ermitteln (_get_last_sequence_domain, Zeile 241):
   - gleiches Journal (journal_id)
   - name != '/'
   - Bezugsbeleg = Beleg mit dem spaetesten Datum (date desc, limit 1); gibt es keinen,
     der aelteste Beleg
   - daraus wird der Reset-Typ abgeleitet (_deduce_sequence_number_reset, Zeile 192) und der
     Suchzeitraum bestimmt: 'year' = Kalenderjahr des neuen Belegs, 'never' = 01.01.0001 bis
     31.12.9999 (_get_sequence_date_range, Zeile 117)
   - Prefix = sequence_prefix des zuletzt ANGELEGTEN Belegs (hoechste id); darin der hoechste
     sequence_number (SQL in Zeile 293-302)
   - sequence_prefix/sequence_number werden aus dem Namen berechnet (_compute_split_sequence,
     Zeile 182, ueber die Fixed-Regex)
4) Erkannte Formate kommen aus fuenf Regexen (Zeile 30-46): monatlich, jaehrlich, Jahresbereich,
   Jahresbereich-monatlich, fest (ohne Datumsbezug). `sequence_override_regex` im Journal
   ersetzt alle fuenf (account_journal.py Zeile 147, Feldbeschriftung
   "Regex fuer Sequenzueberschreibung") - genau fuer Faelle, die Odoo "normalerweise
   missversteht".
5) Kollisionsschutz beim Vergeben: _locked_increment (Zeile 352) sperrt ueber den
   UNIQUE INDEX und wiederholt den Versuch, bis eine freie Nummer gefunden ist
   (Ausnahme UniqueViolation/ExclusionViolation wird abgefangen).
6) Eindeutigkeit in der Datenbank (geprueft in odoo18_test):
   UNIQUE INDEX account_move_unique_name ON account_move (name, journal_id)
     WHERE state = 'posted' AND name <> '/'
   Modell-Constraint account_move_unique_name mit der Meldung
   "Ein anderer Datensatz mit demselben Namen existiert bereits."
   => Anders als in Odoo 11 zaehlt `type` NICHT mit; Entwuerfe sind nicht betroffen
      (Indexbedingung state='posted').
```

## 3. K2a - Doppelnummer R-25001: Optionen mit Bewertung

```
Frage 1: Kann Odoo 18 fuer Gutschriften eine eigene/dedizierte Sequenz verwenden?
  Ja, aber sie loest diesen Fall NICHT. Das Journalfeld "Gesonderter Nummerkreis fuer
  Gutschriften" (refund_sequence, account_journal.py Zeile 144) trennt nur den Nummernkreis
  fuer die kuenftige Vergabe (eigener Prefix/Zaehlerlauf im selben Journal). Der
  UNIQUE INDEX bleibt (name, journal_id) - zwei gebuchte Belege mit dem Namen R-25001 im
  selben Journal sind also auch mit getrennter Sequenz nicht moeglich.

Frage 2: Reicht ein separates Journal, damit beide R-25001 behalten koennen?
  Ja, technisch: der Index gilt je Journal, zwei Journale koennen also dieselbe Nummer
  fuehren. Odoo 18 unterstuetzt beliebig viele Verkaufsjournale; das zweite Journal muesste
  aber erst angelegt werden, und die 237 Gutschriften wuerden dann in einem anderen Journal
  liegen als in Odoo 11 (dort lagen sie im Journal "Ausgangsrechnungen (EUR)").
  Bewertung: moeglich, aber es aendert die Journalstruktur und damit jede Auswertung nach
  Journal. Nur sinnvoll, wenn die Buchhaltung das bewusst will.

Frage 3: Muss eine der beiden Nummern neu vergeben werden?
  Wenn die Journalstruktur unveraendert bleiben soll: ja, genau eine von beiden. Die
  urspruengliche Odoo-11-Nummer bleibt in jedem Fall nachvollziehbar erhalten, wenn sie
  zusaetzlich in einem eigenen Feld gespeichert wird (Vorschlag unten).

Ergebnis: es gibt genau drei saubere Wege, keiner davon ohne Nebenwirkung:
  Weg A (Journalstruktur bleibt): Rechnung behaelt R-25001, die Gutschrift erhaelt eine neue,
      nachvollziehbare Nummer; die Originalnummer steht im Feld "Odoo-11-Rechnungsnummer".
  Weg B (Journalstruktur bleibt): Gutschrift behaelt R-25001, die Rechnung erhaelt eine neue
      Nummer + Originalnummer im Feld. (Fachlich meist unerwuenscht, weil die Rechnung das
      Hauptdokument ist.)
  Weg C (Journalstruktur aendert sich): zweites Verkaufsjournal fuer Gutschriften; dann
      behalten beide ihre Originalnummer, dafuer liegen die Gutschriften in einem anderen
      Journal als in Odoo 11.
```

Empfehlung: **Weg A**. Begruendung: nur eine von 6.263 Nummern betroffen, die
Rechnungsnummer (das Dokument gegenueber dem Kunden) bleibt unveraendert, die Gutschrift
verweist ueber das Feld "Odoo-11-Rechnungsnummer" und ueber ihren Ursprungsbeleg
(`reversed_entry_id` / Ursprung R-25584) eindeutig auf das Original, und die Journalstruktur
bleibt 1:1 wie in Odoo 11.

### 3.1 Vorschlag fuer das Feld "Odoo-11-Rechnungsnummer" (nur Vorschlag, nicht umgesetzt)

```
Odoo 18 hat kein Standardfeld fuer "historische Nummer". Vorhandene Felder und ihre Eignung:
  name               Dokumentnummer; wird vom Regelwerk vergeben und ist der Primaerschluessel
                     fuer die Nummernfortfuehrung -> fuer die Ersatzkennung nicht geeignet
  ref                "Referenz"; beschreibbar, nicht geschuetzt, in Odoo 11 unbenutzt (0 Werte)
                     -> als Zusatzablage brauchbar, aber nicht unveraenderlich
  payment_reference  Zahlungsreferenz; fachlich anderer Zweck -> nicht geeignet
Empfehlung: eigenes ITK-Feld auf account.move, z. B.
  itk_o11_invoice_number = fields.Char(string='Odoo-11-Rechnungsnummer',
                                       readonly=True, copy=False, tracking=True, index=True)
  - fuer ALLE migrierten Rechnungen und Gutschriften gefuellt (= name, ausser beim
    Sonderfall R-25001) -> damit ist eine Kontrollabfrage moeglich:
    "name != itk_o11_invoice_number" liefert genau die abweichenden Belege.
  - readonly=True schuetzt vor Eingabe im Formular; techisch bleibt das Feld per ORM
    schreibbar. Echte Unveraenderlichkeit liefert erst die Hash-Sicherung (siehe K2c).
  - Einbauort: bestehendes ITK-Modul mit account.move-Erweiterung (z. B. itk_base_setup)
    oder ein kleines eigenes Modul; Entscheidung bei der Umsetzung.
  - alternative Absicherung ohne neues Feld: die Originalnummer zusaetzlich als Notiz in den
    Chatter schreiben (nachvollziehbar, aber nicht auswertbar).
```

## 4. K2b - wie Odoo 18 nach der Uebernahme weiterzaehlen wuerde (gemessen)

Das Odoo-18-Regelwerk wurde mit den echten Odoo-11-Nummern nachgerechnet
(Werkzeug `scripts/pruefe_k2_nummernformat.py`, Regexe woertlich aus dem Quellcode; es wird
nichts geschrieben).

```
Ergebnis ohne Zusatzkonfiguration:
  Reset-Typ fuer alle 6.263 Nummern: 'never' (fest, kein Jahresbezug)
  Prefix immer 'R-' (Fixed-Regex: sequence_prefix = alles vor dem letzten Ziffernblock)
  hoechster sequence_number im Journal: 1.900.002 (aus dem 2019er Beleg R-1900002)
  => Zaehlung wuerde bei R-1900003 weiterlaufen. Das waere zwar kollisionsfrei
     (der Retry-Mechanismus findet die erste freie Nummer), aber fachlich falsch
     (Fortsetzung des 2019er Zaehlers).

Ergebnis mit sequence_override_regex ^(?P<prefix1>R-)(?P<year>\d{2})(?P<seq>\d+)$ :
  deckt alle 6.263 Nummern ab (0 ohne Treffer)
  Reset-Typ: 'year' fuer alle Nummern
  Format aus R-261139: {prefix1}{year:02d}{seq:06d}
  naechste Nummer im laufenden Jahr 2026:      R-261140
  naechste Nummer in einem neuen Jahr (2027): R-2700001
  (im neuen Jahr greift die Vorperioden-Logik _get_last_sequence(relaxed=True);
   die Stellenzahl wird dabei vom Bezugsbeleg uebernommen)
Alle Werte sind Fortsetzungen oberhalb der historischen Nummern - eine Kollision mit
bestehenden Nummern ist damit ausgeschlossen; zusaetzlich greift der Retry-Mechanismus.
```

Empfehlung K2b: **Journal "Ausgangsrechnungen" mit `sequence_override_regex`
`^(?P<prefix1>R-)(?P<year>\d{2})(?P<seq>\d+)$`** - dann laeuft die Zaehlung wie in Odoo 11
je Jahr weiter (2026 -> R-261140, 2027 -> R-2700001) und kann nicht in historische Nummern
laufen. Voraussetzung: die Festlegung erfolgt VOR der ersten neuen Rechnung und wird in einer
Testkopie einmal gegengeprueft (die Stellenzahl des ersten Belegs eines neuen Jahres).

Nebenbefund fuer die Planung: `sequence_override_regex` wirkt journaleinheitlich; eine Nummer,
die dem Muster nicht entspricht, wuerde beim Ableiten des Formats eine
ValidationError-Meldung ausloesen ("The sequence regex should at least contain the seq grouping
keys"). Deshalb wurde geprueft, dass alle 6.263 Altnnummern dem Muster entsprechen (0 Ausnahmen).

## 5. K2c - Schutz der historischen Nummern nach der Migration (belegt)

```
1) Hash-Sicherung je Journal (stark, empfohlen):
   account.journal.restrict_mode_hash_table = "Gebuchte Posten mit Hash festschreiben"
   (account_journal.py Zeile 123): beim Buchen wird der Beleg und die Kette bis zum letzten
   gesicherten Beleg hashiert (account_move.inalterable_hash "Unveraenderlichkeitshash",
   secure_sequence_number "Unveraenderlichkeit, Keine Luecke Sequenz #").
   Die Felder, die der Hash schuetzt, sind _get_integrity_hash_fields()
   (account_move.py Zeile 4066): fuer Hash-Version 2-4 = **name**, date, journal_id, company_id
   (und in den Zeilen name, debit, credit, account_id, partner_id).
   Ein Schreibversuch auf diese Felder wird serverseitig abgebrochen:
   "This document is protected by a hash. Therefore, you cannot edit the following fields: %s."
   (account_move.py Zeile 3426). Damit ist die Rechnungsnummern selbst per ORM nicht mehr
   aenderbar.
   Einmal gesichert, kann die Einstellung nicht mehr ausgeschaltet werden, solange gebuchte
   Belege existieren: "You cannot modify the field %s of a journal that already has accounting
   entries." (account_journal.py Zeile 671).
   Nachholen ist moeglich: Assistent "Buchungen festschreiben"
   (account.secure.entries.wizard, Menue unter Buchhaltung) sichert die Kette nachtraeglich -
   also erst importieren, dann sichern.
2) Loeschsperre fuer Kettenbelege (ohne Hash):
   Belege mit Nummer koennen nur geloescht werden, wenn sie das letzte Element der
   Nummernfolge sind (_unlink_forbid_parts_of_chain, account_move.py Zeile 3535).
   Folge: keine Luecken durch Loeschen.
3) Sperren beim Schreiben (ohne Hash):
   - Journal eines gebuchten Belegs aendern: nur wenn die Nummer entfernt wird
     ("You cannot edit the journal of an account move if it has been posted once, unless the
     name is removed or set to '/' ...", Zeile 3437 ff.).
   - Datum/Nummer in einer gesperrten Periode (Journal-/Steuer-/Jahressperre) sind nicht
     aenderbar (Pruefung im write, Zeile 3449 ff.).
   - Gebuchte Belege: readonly-Felder werden serverseitig geprueft
     ("You cannot modify the following readonly fields on a posted move: %s", Zeile 3468).
4) Pruefpfad (Protokollierung):
   res.company.check_account_audit_trail = "Pruefpfad" (Einstellung, Standard aus). Ist er aktiv,
   werden kritische Aktionen (z. B. erzwungenes Loeschen gebuchter Belege) protokolliert
   (account_move.py Zeile 3529/3570).
```

Empfehlung K2c: nach der Migration **`restrict_mode_hash_table` auf dem Verkaufsjournal
aktivieren** (ggf. nachtraeglich per Assistent "Buchungen festschreiben") - das schuetzt genau
die Felder name, date, journal_id, company_id und ist nicht mehr abschaltbar. Zusaetzlich
Pruefpfad (`check_account_audit_trail`) fuer die Protokollierung aktivieren. Beides ist eine
Einstellung, keine Datenmigration - Umsetzung erst nach Freigabe und in einer Testkopie
verifizieren.

## 6. Offene Entscheidungen (nichts umgesetzt)

```
K2a: Welcher Weg fuer R-25001? Empfehlung Weg A (Rechnung behaelt R-25001, Gutschrift erhaelt
     eine neue Nummer, Originalnummer im Feld "Odoo-11-Rechnungsnummer").
K2a-2: Soll das Feld "Odoo-11-Rechnungsnummer" in einem bestehenden ITK-Modul entstehen
     (Vorschlag itk_base_setup) oder in einem eigenen kleinen Modul?
K2b: sequence_override_regex wie vorgeschlagen einsetzen (Jahr + laufende Nummer)?
     Alternativ: Nummerierung bewusst fortlaufend ohne Jahreswechsel.
K2c: restrict_mode_hash_table auf dem Verkaufsjournal aktivieren (ja/nein) und Pruefpfad
     (check_account_audit_trail) aktivieren (ja/nein)?
```

## 7. Rahmenbedingungen und Nachweise

```
keine Datenmigration, keine Nummer geaendert, kein Schreibvorgang in Odoo 18
Odoo 11 Prod ausschliesslich read-only (search_read auf account.invoice)
Odoo 18: Quellcode-Lesen im Container (docker exec ... sed/grep) und Schema-Abfrage
  (pg_constraint/pg_indexes, read-only); kein Upgrade, kein Neustart
Werkzeuge: scripts/pruefe_k2_nummernformat.py (Nachbildung des Nummernregelwerks),
  scripts/analyse_abrechnung_details*.py (Nr. 3 und 6: Nummernkreis und Bedingungen)
Tests vor der spaeteren Umsetzung (Vorschlag): Import von 6.263 Nummern in einer Testkopie,
  Gegenprobe der naechsten Nummer je Jahr, Hash-Sicherung nach dem Import.
```
