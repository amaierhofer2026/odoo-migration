# R4 - note (TEXT -> HTML): Zuordnung Odoo 11 -> Odoo 18

Stand: 29.09.2026, Session 121. **Nur Analyse.** Odoo 11 ausschliesslich read-only.
Fuer die Verhaltensbestaetigung wurde in Odoo 18 ein Testauftrag angelegt und wieder entfernt;
es war **keine Aenderung an Odoo 18 erforderlich**.

## 1. Feld in beiden Systemen

```
Odoo 11  sale.order.note   type = text     store = True   Anzeige "Geschäftsbedingungen"
Odoo 18  sale.order.note   type = html     store = True   Anzeige "Allgemeine Geschäftsbedingungen"
         sanitize = True (Odoo reinigt den Inhalt beim Schreiben)
Platzierung im Formular: beide Systeme zeigen das Feld unterhalb der Auftragszeilen bzw. des
  Betragsblocks (Odoo 11 direkt am Betragsblock, Odoo 18 in der Gruppe note_group mit
  Platzhaltertext "Bedingungen und Konditionen ...").
```

## 2. Korrektur einer frueheren Messung (wichtig)

```
Der Migrations-Check (docs/o11-o18-verkauf-migrationscheck.md) hat fuer note "2.442 von 2.464
Zeilen belegt" ausgewiesen. Diese Zahl kam aus der Odoo-Domain [('note','!=',False)], die bei
Textfeldern auch den LEEREN String als "nicht False" zaehlt.

Exakt gemessen (read-only):
  Auftraege gesamt                                2.464
  note ist NULL/False                                22
  note ist nicht leer laut Odoo-Domain             2.442
  davon Inhalt nur Leerzeichen/leerer String       2.439
  davon ECHTER TEXT                                    3
Der Wert ist also praktisch unbenutzt: nur drei Auftraege tragen echten Text.
```

## 3. Die drei tatsaechlichen Inhalte (Volltext, Odoo 11)

```
A-1900897  (12.08.2019, Verkaufsauftrag)
  "30 % auf jährliche Kosten/Einmalige Kosten kein Rabatt. "
A-1900947  (26.11.2019, Verkaufsauftrag)
  "Diese Rechnung umfasst eine Zusatzlizenz im Zeitraum vom 11/2019-12/2019"
A-2300151  (24.10.2023, Verkaufsauftrag)
  "Teilweise Umstellung der Einlieferung der Gemeindeverordnung nach DiVA"
Merkmale: alle einzeilig, keine Zeilenumbrueche, keine HTML-Zeichen (< > &), Laenge 56 bis 72
Zeichen, Umlaute vorhanden (ä), Sonderzeichen % und /.
```

## 4. Verhalten von Odoo 18 beim Schreiben (Testbestaetigung)

```
Test 1 - naiv (reiner Text in das HTML-Feld geschrieben):
  geschrieben "Zeile1\nZeile2 & <b>fett</b> 100 %"
  gespeichert "<p>Zeile1\nZeile2 &amp; <b>fett</b> 100 %</p>"
  -> Der Zeilenumbruch liegt als reines \n im HTML und geht in der Anzeige verloren;
     vom Anwender eingetippte spitze Klammern werden als HTML gedeutet (hier als Fettdruck).
     Reiner Text darf deshalb NICHT ungewandelt uebernommen werden.

Test 2 - umgewandelt (HTML-Entities maskiert, \n -> <br/>):
  geschrieben "Zeile1<br/>Zeile2 &amp; &lt;b&gt;fett&lt;/b&gt; 100 %"
  gespeichert "<p>Zeile1<br>Zeile2 &amp; &lt;b&gt;fett&lt;/b&gt; 100 %</p>"
  -> Zeilenumbruch bleibt erhalten (<br>), der Anwendertext bleibt Text (kein Fettdruck).

Test 3 - echter Odoo-11-Text (Umlaut):
  geschrieben "30 % auf jährliche Kosten/Einmalige Kosten kein Rabatt."
  gespeichert "<p>30 % auf jährliche Kosten/Einmalige Kosten kein Rabatt.</p>"
  -> Inhalt unveraendert, Umlaute und Sonderzeichen erhalten.

Testauftrag nach den Proben wieder entfernt (Bestand unveraendert: 18 Auftraege lokal).
```

## 5. Transformationsregel (vorbereitet)

```
note wird NICHT 1:1 uebernommen, sondern nach der Odoo-18-Standardfunktion umgewandelt:
  odoo.tools.mail.plaintext2html(text)
  (Modul odoo/tools/mail.py, im Odoo-18-Container geprueft)
Was die Funktion tut:
  - maskiert HTML-Entities (html_escape: & < >)
  - ersetzt alle \n und \r durch <br/>
  - wandelt URLs in anklickbare Links
  - fasst den Inhalt in <div> bzw. bei Absaetzen in <p>
Damit bleibt der fachliche Inhalt identisch und die Zeilenumbrueche bleiben sichtbar - genau der
Unterschied zu Test 1 (naive Uebernahme).

Auswirkung im Bestand: 3 Auftraege (A-1900897, A-1900947, A-2300151). Die drei Texte sind
einzeilig und enthalten keine HTML-Zeichen, das Ergebnis ist dort
"<p>Originaltext</p>" - inhaltlich identisch.
Feldbezeichnung: Odoo 11 "Geschäftsbedingungen" gegen Odoo 18 "Allgemeine Geschäftsbedingungen".
  Empfehlung wie bei R3: Odoo-18-Bezeichnung beibehalten und die Abweichung dokumentieren.
Einordnung nach der Statusliste: "Transformationsregel erforderlich" (text -> html, mit
Odoo-Standardfunktion). Keine Aenderung an Odoo 18 erforderlich.
```

## 6. Nachweise

```
Odoo 11: fields_get, search_count mit mehreren Domains, vollstaendige Auswertung aller
  note-Werte (2.464 Auftraege), Formulararchiv
Odoo 18: fields_get (Typ html, sanitize), Formulararchiv, drei Schreibproben mit
  Testauftrag und Ruecklesepruefung, Servercode odoo/tools/mail.py im Container gelesen
Bestand nach der Analyse: lokal 18 Auftraege / 28 Zeilen / 13 Produkte / 0 Lagerbelege,
  VM 20 Auftraege / 29 Zeilen / 13 Produkte / 0 Lagerbelege (unveraendert)
Keine Datenmigration, keine Aenderung an Odoo 18.
```

## 7. Entscheidungen von Anna (29.09.2026) und Status

```
a) Transformationsregel BESTAETIGT:
   note aus Odoo 11 wird bei einer spaeteren Migration mit der Odoo-18-Standardfunktion
   odoo.tools.mail.plaintext2html(text) in das HTML-Feld uebernommen.
   Dabei gilt:
     - Sonderzeichen und HTML-Zeichen werden maskiert
     - Zeilenumbrueche bleiben erhalten
     - URLs duerfen als klickbare Links umgesetzt werden
     - der Inhalt darf fachlich nicht veraendert werden
b) Feldbezeichnung BESTAETIGT: Der Odoo-18-Wortlaut "Allgemeine Geschaeftsbedingungen" bleibt
   bestehen, keine Umbenennung auf "Geschaeftsbedingungen". Die Abweichung wird nur dokumentiert.
c) Messkorrektur BESTAETIGT und dokumentiert: Es tragen nur 3 Auftraege echten Text. Die frueher
   genannte Zahl 2.442 entstand aus der Odoo-Domain [('note','!=',False)], die bei Textfeldern
   auch leere Strings und reine Leerzeichen als "belegt" zaehlt (2.439 solcher Werte).
   Gegenpruefung: Die Abweichung betrifft ausschliesslich note; alle anderen Textfelder von
   sale.order und sale.order.line stimmen exakt.

STATUS: R4 ABGESCHLOSSEN (29.09.2026) - analysiert (read-only in Odoo 11, Schreibproben und
  Servercode in Odoo 18), Transformationsregel festgehalten, Entscheidungen eingetragen,
  Messkorrektur dokumentiert. Es war KEINE Aenderung an Odoo 18 erforderlich; Testauftrag nach
  den Proben entfernt, keine Datenmigration.
Der Bereich Verkauf bleibt bis zur Vorbereitung der Risiken R5 bis R8 weiterhin NICHT endgueltig
abgeschlossen.
```
