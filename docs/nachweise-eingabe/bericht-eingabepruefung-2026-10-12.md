# Nachweis: Eingabemethoden im Hermes-Browserwerkzeug gegen Odoo 18 (lokal und VM)

Datum: 12.10.2026. Anlass: Pruefung nach Hermes-Neustart, ob die geladenen Korrekturen
(browser-harness 0.1.13) Standardaufnahme, Koordinatenklicks und Texteingabe in Odoo 18
zuverlaessig tragen.

Umgebung lokal: http://localhost:8069, DB `odoo18_test`, Administrator uid 2, echter Chrome,
Fenster 1258 x 566. Umgebung VM (Abschnitt 7): https://k001959vsx.ipax.at, DB `odoo18_test`,
Administrator uid 2, echter Chrome, Fenster 1258 x 566. Odoo 11 wurde nicht beruehrt (keine Verbindung zu
portal.it-kommunal.at). Getestet wurde ausschliesslich in einem ungespeicherten
Kontaktformular (`res.partner`, Neuanlage) - nichts davon wurde gespeichert.

## 1. Standardaufnahme (AX-Baum)

| Messung | Wert |
|---|---|
| AX-Knoten Kontakte-Liste | 3778, Aufnahme 0,17 s |
| Elemente mit Rolle und Namen | 303 |
| Geometrie Boxmodell vs. DOM | identisch (Neu-Knopf 40,2 / 71,5 gegen 40 / 71; Ansichtswechsel x = 1152 / 1189 / 1225) |
| Elemente ausserhalb des Fensters im Baum | vorhanden (Reiter bei y = 832, Fensterhoehe 566), `checkVisibility()` trotzdem `true` |
| Symbolknoepfe ohne Text | Name nur Icon-Zeichen (`\ue814`, `\uf013`), keine Beschreibung, kein aria-label im DOM |

## 2. Koordinatenklicks

| Messung | Wert |
|---|---|
| Ansichtswechsel-Knoepfe (3 Ziele, 6 Klicks) | 6 / 6 Treffer |
| "Neu" (40, 71) aus dem AX-Baum | Formular geoeffnet |
| Kleine Ziele (Filter-X 18 x 18, Verwerfen 26 x 18) | getroffen |
| Klick ausserhalb des Fensters (y = 832) | folgenlos |
| Scrollen im inneren Container | `scroll(600, 300, 400)` verschiebt den Reiter y = 832 -> y = 432; `window.scrollY` bleibt 0 |

## 3. Texteingabe (Soll gegen Ist, exakt verglichen)

Solltexte: Volltext 95 Zeichen, Umlaute 39 Zeichen, Sonderzeichen 78 Zeichen,
Tipptext 44 Zeichen.

| Verfahren | Ergebnis |
|---|---|
| `fill_input` | Volltext 95 / 95 exakt, 1,29 s |
| `type_text` (Input.insertText) | Umlaute 39 / 39, Sonderzeichen 78 / 78 exakt |
| `press_key` Zeichen fuer Zeichen | 44 / 44 exakt, 0,75 s |
| `dispatch_key` (DOM-KeyboardEvent) | 0 / 17 - kein Text eingefuegt |
| Ersetzen (Strg+A + Tippen) | nur der neue Text blieb (41 Zeichen, keine Reste) |
| Backspace x5 / Entf x3 ab Anfang | exakt letzte 5 bzw. erste 3 Zeichen entfernt |
| 81 Zeichen vollstaendig leeren | leer, 1,27 s |
| Inhaltsfeld (HTML-Editor, contenteditable) | insertText, Tastendruecke, Ersetzen, Backspace je exakt |
| Auswahlfeld Verkäufer (many2one) | "Würr" -> Vorschlag "Würrer Florian", Enter uebernahm den Datensatz |
| Suchfeld der Liste | "Würrer" -> Filterzeile, 1-1 / 1; Filter per Koordinate wieder entfernt, Endstand 1-71 / 71 |
| Tab-Sprung | Fokus street -> street2, Werte unveraendert |

## 4. Bestandskontrolle

| Pruefung | Wert |
|---|---|
| `res.partner` gesamt vorher / nachher | 71 / 71 |
| Suche nach allen Testtexten (z. B. Prüfhausen, Zwischenstand, Gröbming) | 0 Treffer |
| jüngster Kontakt | id 103, 08.10.2026 (vor dem Testtag) |
| offene Tabs | nur localhost:8069 (Odoo 18) - keine Verbindung zu Odoo 11 |
| Formular | ueber "Alle Änderungen verwerfen" verlassen, Liste wieder 1-71 / 71 |

## 5. Rohdaten

- `docs/nachweise-eingabe/eingabe_ergebnisse.json` (Formularfeld: Volltext, Umlaute, Sonderzeichen,
  Ersetzen, Loeschen, Backspace/Entf)
- `docs/nachweise-eingabe/eingabe_inhaltsfeld.json` (HTML-Editor im Reiter "Interne Notizen")
- `docs/nachweise-eingabe/klick_zuverlaessigkeit.json` (6 Koordinatenklicks auf die Ansichtswechsel)

## 6. Bleibende Einschraenkungen

1. Symbolknoepfe ohne Text sind im AX-Baum nicht ueber einen Namen findbar (nur Icon-Zeichen) - Zuordnung
   ueber Position oder JS-Klasse.
2. Koordinatenklicks wirken nur im sichtbaren Fensterbereich; vorher scrollen und Position neu messen.
3. `dispatch_key` (DOM-`KeyboardEvent`) erzeugt keinen Text - nur fuer Tastenreaktionen.
4. Bei Feldern mit Autovervollstaendigung ist getippter Text nur Suchtext, erst Enter/Klick setzt den Wert.
5. Neue ungueltige Formulare lassen sich nicht ueber die Brotkrume verlassen (Odoo blockt mit
   "Ungueltige Felder"); zum Aufraeumen den Knopf "Alle Änderungen verwerfen" nutzen.
6. Beide Fenster waren 1258 x 566 gross; bei abweichender Fenstergroesse ist mehr Scrollen noetig, die
   Messung selbst bleibt gleich.

## 7. Zweite Messreihe auf der VM (https://k001959vsx.ipax.at, DB odoo18_test)

Gleiche Messreihe wie in den Abschnitten 1-4, ausgefuehrt am 12.10.2026 auf der Abnahme-VM.

### 7.1 Standardaufnahme

| Messung | Wert (VM) |
|---|---|
| AX-Knoten Kontakte-Liste | 3775 in 0,13 s |
| Elemente mit Rolle und Namen | 303 |
| Geometrie Boxmodell vs. DOM ("Neu") | 40,2 / 71,5 gegen 40 / 72 |
| Symbolknoepfe ohne Text | Icon-Zeichen `\ue80d`, `\uf013`, `\uf0d7`, `\ue814`, `\ue817`, `\uf017` |
| Elemente ausserhalb des Fensters | Reiter bei y = 586 bei Fensterhoehe 566 |

### 7.2 Koordinatenklicks

| Messung | Wert (VM) |
|---|---|
| "Neu" per Koordinate geklickt | Formular geoeffnet (URL /odoo/contacts/new) |
| Ansichtswechsel (3 Ziele, 6 Klicks) | 6 / 6 Treffer (x = 1152 / 1189 / 1225, y = 71) |
| Reiter "Interne Notizen" (erst y = 586) | nach einem Scrollschritt y = 186, Klick traf |
| Filter-Entfernen und "Alle Änderungen verwerfen" | getroffen (Pager danach wieder 1-71 / 71) |

### 7.3 Texteingabe (ungespeichertes Kontaktformular, exakter Rueckvergleich)

| Pruefung | Soll | Ist | Ergebnis |
|---|---|---|---|
| `fill_input` Volltext | 95 Zeichen | 95 Zeichen | exakt, 1,59 s |
| `type_text` Umlaute | 39 Zeichen | 39 Zeichen | exakt |
| `type_text` Sonderzeichen | 78 Zeichen | 78 Zeichen | exakt |
| `press_key` Zeichen fuer Zeichen | 44 Zeichen | 44 Zeichen | exakt, 0,69 s |
| `dispatch_key` (DOM-KeyboardEvent) | 17 Zeichen | 0 Zeichen | kein Text (wie lokal) |
| Ersetzen (Strg+A + Tippen) | 41 Zeichen | 41 Zeichen | exakt, keine Reste |
| Backspace x5 | 22 Zeichen | 22 Zeichen | exakt |
| Home + Entf x3 | 19 Zeichen | 19 Zeichen | exakt |
| 81 Zeichen leeren per Backspace | leer | leer | exakt, 1,20 s |
| Feld Straße (Umlaute/Sonderzeichen) | exakt | exakt | OK |
| Tab-Sprung street -> street2 | Fokus street2, Werte erhalten | dito | OK |
| Ort per insertText | exakt | exakt | OK |
| Inhaltsfeld HTML-Editor | 4 Pruefungen | 4 x exakt | OK |
| Auswahlfeld Verkäufer (many2one) | "Würr" -> "Würrer Florian" | dito | OK |
| Suchfeld der Liste | "Würrer" -> 1-1 / 1 | dito | OK, danach wieder 1-71 / 71 |

### 7.4 Bestandskontrolle (VM)

| Pruefung | Wert |
|---|---|
| `res.partner` gesamt vorher / nachher | 71 / 71 |
| Suche nach Testtexten (Prüfhausen, Bestaendigkeit, Altbestand, Gröbming, Prüfstraße, DOM-Ereignis) | je 0 Treffer |
| juengster Kontakt | id 114, 08.10.2026 (vor dem Testtag) |
| Odoo 11 | nicht beruehrt (kein Tab, keine Verbindung zu portal.it-kommunal.at) |
| Formular | ueber "Alle Änderungen verwerfen" verlassen, Liste wieder 1-71 / 71 |

### 7.5 Rohdaten (VM)

`vm_eingabe_name.json`, `vm_eingabe_felder.json`, `vm_eingabe_inhaltsfeld.json`, `vm_klick_suche.json`

## 8. Nach dem Hermes-Update (12.10.2026, v0.21.6+301.g8bff64d -> v0.21.7+20.g3569e84)

Hermes wurde von v0.21.6+301.g8bff64d auf v0.21.7+20.g3569e84 (main @ 3569e8461e, 496 Commits, git-Installation)
aktualisiert. Lokale Aenderungen (4 Dateien unter tools/computer_use) wurden vorher gesichert und nach dem
Update unveraendert wiederhergestellt. Danach dieselbe Messreihe erneut, lokal und auf der VM:

| Messung | lokal (vorher -> nachher) | VM (vorher -> nachher) |
|---|---|---|
| AX-Knoten | 3778 -> 3778 | 3775 -> 3775 |
| benannte Bedienelemente | 303 -> 303 | 303 -> 303 |
| Boxmodell vs. DOM ("Neu") | 40,2/71,5 vs. 40/72 -> gleich | 40,2/71,5 vs. 40/72 -> gleich |
| Klick "Neu" oeffnet Formular | ja -> ja | ja -> ja |
| Koordinatenklicks Ansichtswechsel | 6/6 -> 6/6 | 6/6 -> 6/6 |
| Volltext 95 / Umlaute 39 / Sonderzeichen 78 | exakt -> exakt | exakt -> exakt |
| press_key 44 Zeichen | exakt -> exakt | exakt -> exakt |
| dispatch_key | 0/17 -> 0/17 (kein Text) | 0/17 -> 0/17 |
| Ersetzen 41 / Backspace x5 / Entf x3 / leeren | exakt -> exakt | exakt -> exakt |
| Inhaltsfeld (HTML-Editor): insertText, ersetzen, loeschen | exakt -> exakt | exakt |
| Auswahlfeld Verkäufer | "Würrer Florian" -> gleich | gleich |
| Wert nach Fokuswechsel | erhalten -> erhalten | erhalten -> erhalten |

Bestand nach der Messreihe unveraendert: lokal res.partner 71, VM 71, Suche nach Testtexten 0 Treffer,
juengste Kontakte id 103 (lokal) und 114 (VM) vom 08.10.2026 - also kein Testdatensatz gespeichert.
Odoo 11 wurde nicht beruehrt.

Wichtig fuer die Nachvollziehbarkeit: die Browser-Harness ist vorher und nachher browser-harness 0.1.13
(identische Version), und das laufende Hermes im Terminal nutzt bis zum Neustart noch den alten Code im
Speicher. Fuer Messungen direkt nach einem Update daher den Browser-Daemon neu starten (`restart_daemon()`);
die neuen Commits wirken erst nach einem Hermes-Neustart.

### 8.1 Falle bei mehreren Tabs (Messfehler, kein Klickfehler)

Bei der ersten VM-Messung nach dem Update meldeten die Klick-Durchgaenge 0/6 bzw. 3/6 Treffer, obwohl die
Klicks ankamen. Ursache: es waren drei Tabs offen (chrome://newtab, lokal, VM) und die JS-Auswertung lief
gegen einen anderen Tab als den sichtbaren. Nach dem Schliessen der uebrigen Tabs und `switch_tab()` auf den
VM-Tab: 6/6 Treffer. **Vor jeder Messung `current_tab()` pruefen und die URL gegenpruefen.**

### 8.2 Offene Punkte aus dem Update

- Der cua-driver (Computer-Use-Backend) wurde nicht mitgezogen: "Windows cua-driver refresh deferred
  (autostart registration requires UAC)" - dafuer ist `hermes computer-use install --upgrade` in einem
  interaktiven Terminal noetig.
- Der Computer-Use-Koordinatenklick auf der Desktop-Ebene konnte nicht geprueft werden: die Aktion braucht
  eine Freigabe im UI, die nicht erteilt wurde (Timeout). Standardaufnahme (capture) funktioniert.
- Rohdaten dieser Reihe: `nach-update_lokal_eingabe.json`, `nach-update_vm_eingabe.json`.

