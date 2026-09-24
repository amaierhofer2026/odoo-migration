# Uebergabe Session 120 - Abonnements und Abonnement Produkte abgeschlossen

Stand: 24.09.2026. Odoo 11 Prod ausschliesslich read-only verwendet (nur Leseaufrufe), keine
Datenmigration, keine Aenderung an Produktivdaten.

Diese Datei ist die Arbeitsgrundlage fuer die naechste Session. Kurzfassung:

```
Bereich Abonnements (inkl. Abonnement Produkte) ist abgeschlossen:
Teile 1-15 der Bereichsdokumentation, Checkliste 6.14 auf ABGESCHLOSSEN.
Der Bereich ist auf Wunsch von Anna EINGEFROREN: keine Aenderung mehr, ausser bei der
Datenmigration wird ein konkretes Problem festgestellt (dann mit Freigabe).

Endstand lokal = GitHub = VM: main = 29c0ea6
Werkzeuge, Nachweise und die Vollstaendigkeitsbestaetigung: Abschnitte 4 bis 7.

Naechstes Modul/naechster Bereich: von Anna noch festzulegen.
```

## 1. Auftrag dieser Session

Aus der Uebergabe der Session 119 kam der Unterbereich "Abonnement Produkte" mit offenem Punkt
(Produktformular vollstaendig vergleichen). Ablauf: Analyse Odoo 11 gegen Odoo 18, Umsetzung in
Odoo 18, VM-Deploy und Browser-Abnahme, Werkzeugbereinigung, Abschlussverifikation.
Am Ende stand die ausdrueckliche Bestaetigungsfrage: ist jedes in Odoo 11 tatsaechlich verwendete
Feld, jeder Reiter, Button, Smart Button, Statuswechsel, Filter, Such-/Gruppierungsfunktion und
jeder Geschaeftsprozess entweder in Odoo 18 gleich vorhanden, funktional gleichwertig an anderer
Stelle vorhanden oder bewusst als nicht verwendet dokumentiert?

## 2. Ergebnis in einem Satz

Ja, fuer beide Bereiche - Abonnements (sale.subscription, -line, -template) und Abonnement Produkte
(Produktformular) - ist lueckenlos abgebildet; eine offene funktionale oder strukturelle
Abweichung vor der Migration gibt es nicht. Es bleiben nur Daten und bewusst dokumentierte
Abweichungen (Abschnitte 6 und 7).

## 3. Was umgesetzt wurde (nur Odoo 18, itk_product 18.0.1.0.2)

```
1. "Verantwortlich" (responsible_id, many2one res.users) neu im Modul. Odoo 11 hatte das Feld
   (auf allen 649 Produkten gepflegt), Odoo 17/18 hat es entfernt. Gleicher Feldname und gleiche
   Relation -> 1:1 migrierbar. Im Formular eigene Gruppe im Reiter "Allgemeine Informationen",
   weil das Feld in Odoo 11 im Reiter "Lager" stand (bei Dienstleistungen ausgeblendet).
2. Gruppe "Interne Notizen" heisst sichtbar wieder "Notizen" (Odoo-11-Wortlaut). Inhalt
   unveraendert, keine Odoo-18-Zusatzfunktion entfernt.
3. Reiter "Buchhaltung": KEINE Aenderung. In Odoo 11 waren die Kontofelder dieses Reiters selbst
   ausgeblendet (invisible="1"), 0 von 649 Produkten hatte ein eigenes Konto; die sichtbaren
   Felder (Steuern, Dienstleistungslogik, Kontrollrichtlinie) sind in Odoo 18 an anderer Stelle
   erreichbar. Keine Gruppenaufnahme, keine zusaetzlichen Rechte, keine Ersatzseite.
4. Zeiterfassung: sale_timesheet bleibt uninstalliert; service_type wird nicht uebernommen
   (51 Produkte, 0 Stundenzettelzeilen dieser Produkte, 246 Auftragszeilen ohne gelieferte Menge).
5. Reiter "Bilder": kein Nachbau (product_image_ids in Odoo 11 mit 0 Datensaetzen belegt).
```

## 4. Nachweise (jeweils 0 FEHL)

```
                                       lokal             VM
itk_product                            18.0.1.0.2        18.0.1.0.2 (Upgrade ohne Fehler)
verify_produktformular.py              27 OK / 0 FEHL    27 OK / 0 FEHL
verify_abo_produkte.py                 34 OK / 0 FEHL    34 OK / 0 FEHL
test_abo_smartbuttons.py               11 OK / 0 FEHL    11 OK / 0 FEHL
browser_produktformular.py             20 OK / 0 FEHL    20 OK / 0 FEHL (echte Klicks)
pruefe_view_render.py                   8 OK / 0 FEHL     8 OK / 0 FEHL
verify_s118_abo.py                          -            19 OK / 0 FEHL
pruefe_abo_xmlids.py                        -             0 fehlende XML-IDs
/web/login auf der VM                  HTTP 200
Screenshots                            Desktop\Odoo18-Abnahme-Session120\01..06_*.png
Testdaten                              Testrechnungen und Testwert "Verantwortlich" entfernt,
                                       Produkte 13 vorher wie nachher
```

## 5. Vollstaendigkeitsbestaetigung (Messung 24.09.2026, Odoo 11 Prod gegen Odoo 18 VM)

### 5.1 Felder

```
Abos        sale.subscription         O11 64 / O18 70 Felder, 59 gemeinsam
            sale.subscription.line    O11 18 / O18 17, 17 gemeinsam
            sale.subscription.template O11 37 / O18 38, 32 gemeinsam
            Nur Odoo 11: technische mail-Reste (__last_update, message_channel_ids,
            message_last_post, message_unread, message_unread_counter)
            Nur Odoo 18: neue mail-/Aktivitaets-/Rating-Felder
            Pflichtfelder 0 Abweichungen; Auswahlwerte identisch; 2 Typabweichungen, beide
            Odoo-18-Umbenennungen: uom_id product.uom -> uom.uom,
            tag_ids account.analytic.tag -> crm.tag (tag_ids in Odoo 11 mit 0 Verwendungen)
Produkte    Feld fuer Feld geprueft (Teil 15): jedes verwendete Feld vorhanden, an anderer Stelle
            oder begruendet entfallen. Belegte Nutzung: Steuern 647/648, Abo-Vorlage 292,
            Faktor-Flag 1, Preislistenpositionen 321 Produkte, Verantwortlich 649.
```

### 5.2 Reiter

```
Abos        O11 2 = O18 2 ("Wiederkehrende Buchungen", "Einstellungen"), im Browser bestaetigt
Produkte    O11 8 gegen O18 5. "Lager" ist in beiden vorhanden und in beiden bei Dienstleistungen
            ausgeblendet. "Abrechnung" und "Notizen" liegen in Odoo 18 an anderer Stelle,
            "Bilder" ist ohne Verlust aufgeloest (Hauptbild, Dokumente, Chatter).
```

### 5.3 Buttons und Smart Buttons

```
Abos        O11 5 = O18 dieselben 5; O18 zusaetzlich "Abonnement-Zusatzverkäufe"
            (in Odoo 11 Aktion 513, derselbe Assistent). Smart Buttons beidseitig dieselben 3
            (Website-Vorschau, Rechnungen, Verkaeufe)
Produkte    Die sichtbaren Odoo-11-Buttons sind zugeordnet: "Einkauf" (Aktion 470) -> O18 "Einkauf",
            "Verkaeufe" -> O18 "Verkauft", "Varianten" -> O18 Varianten,
            "Aktiv/Inaktiv" -> O18 Archivieren, Website-Veroeffentlichen -> in Odoo 11
            0 veroeffentlichte Produkte. Alle weiteren Odoo-11-Buttons sind im Arch ausgeblendet
            oder lagerbezogen (Variantenwerte, Produktmenge anpassen, Bestandsvorschau,
            Standardpreis, Produktlieferungen, Meldebestaende). O18 bietet zusaetzlich
            Preislistenregeln, Dokumente, Konfigurieren, Etiketten drucken.
```

### 5.4 Statuswechsel

```
Abos        Zustandswerte identisch (Neu, Laufend, Zu erneuern, Abgeschlossen, Abgebrochen),
            Wechsel-Buttons identisch (Abonnement starten, Zu erneuern, schliessen, abbrechen)
Produkte    Aktiv/Inaktiv ueber Archivieren vorhanden
```

### 5.5 Filter, Suche, Gruppierungen

```
Abos        Filter 5 = 5 identisch; Gruppierungen 8 = 8 (Status, Verkäufer, Partner, Branche,
            Vorlage, Startmonat, Monatsende, Preisliste). Die in Odoo 11 sichtbaren Eintraege
            "Country"/"State" sind dort auskommentiert, state_id existiert nicht -> kein Verlust.
            Rest: in Odoo 11 sind "Verkäufer"/"Partner" mit expand gesetzt, in Odoo 18 nicht
            (Anzeigedetail beim Klick auf die Gruppierung)
Produkte    Teil 14: Spalten, Filter "Mit Faktor multipliziert" / "Aktive Abonnement Produkte",
            Gruppierungen "Status" / "Mit Faktor multipliziert"; die Odoo-11-"Service Type ..."-
            Filter sind bewusst nicht nachgebaut (Odoo 18 gruppiert nach Produkttyp),
            Bestandsfilter entfallen begruendet (stock nicht installiert)
```

### 5.6 Cronjobs und Stammdaten

```
Cronjobs    beidseitig dieselben 2 Abo-Jobs aktiv: wiederkehrende Rechnungen (taeglich),
            Ablauf des Abonnements (woechentlich)
Vorlagen    5 = 5 mit identischen Namen
Beendigungsgruende O11 33 / O18 31 - Differenz sind genau zwei in Odoo 11 nie verwendete Gruende
            ("Maria Saal", "wird noch Intrakommuna abgelöst") und ein Leerzeichen-Duplikat
```

### 5.7 Geschaeftsprozesse

```
Rechnungslauf (Cron) 13 OK / 0 FEHL, manuelle Rechnung 16 OK / 0 FEHL (Session 118/119),
Smart Buttons 11 OK / 0 FEHL, Reiterbeschriftung, Zusatzverkaufs-Assistent, Statuswechsel,
Browser-Abnahme 20 OK / 0 FEHL - alles auf der VM geprueft, keine RPC- oder JavaScript-Fehler
```

## 6. Bewusst dokumentierte Abweichungen (vollstaendige Kategorien)

```
- bestandsbezogene Felder (Bestandsmenge, geplante Bestandsmenge, Meldebestaende, Lagerbewegungen):
  stock wird nicht installiert, in Odoo 11 mit 0 Nutzung belegt
- Zeiterfassung service_type: 0 Stundenzettelzeilen, Festlegung "nicht uebernehmen"
- zwei unbenutzte Beendigungsgruende und ein Leerzeichen-Duplikat
- company_id-Spalte in der Abo-Liste (bei einem Unternehmen ohne Wirkung)
- englische Beschriftungen der mail-/Systemfelder (Rest 34, Befund F17)
- Wortlaut recurring_next_date (Entscheidung Anna: Wortlaut bleibt)
- "Service Type ..."-Filter der Produktliste (ersetzt durch Gruppierung nach Produkttyp)
- Website-Verkaufsfelder am Produkt (0 veroeffentlichte Produkte)
- 42 Alt-Abos ohne Verkaufsauftrag: Auswahlregel ist ein Datenschritt, nicht Teil 15
```

## 7. Was bleibt (nur Daten) und zwei Doku-Kosmetikpunkte

```
Daten der Migration: 42 Alt-Abos (Auswahlregel), Auftraege vor Abos, Verantwortlich-Werte,
NV-Nummern, 8 USD-Testauftraege, Cron vor der Migration pausieren.
Regeln: migration/abo_migrationsregeln.json.

Doku-Kosmetik (nur mit Freigabe, kein Funktionsproblem):
1. MIGRATION_READINESS_CHECKLIST.md Zeilen 135/136 (Abschnitt 1 Sprache) beschreiben den Zustand
   vor Befund F17 ("FEHLER", "teilweise"); F17 ist behoben, Rest 34 mail-/Systemfelder.
2. docs/o11-o18-vergleich-abo-teil2.md fuehrt recurring_amount_total als "Gesamtbetrag"; in
   Odoo 18 heisst das Feld "Total". Das Feld ist nicht gespeichert und in keiner Ansicht sichtbar.
```

## 8. Merksaetze und Befunde dieser Session

```
F41/F50 Die Kontofelder des Odoo-11-Reiters "Abrechnung" waren in Odoo 11 selbst ausgeblendet;
        der Reiter "Buchhaltung" in Odoo 18 haengt an der Technik-Gruppe account.group_account_readonly
        (id 35), die niemand hat -> deshalb kein Ersatzreiter, keine Rechteaenderung.
F49     pruefe_view_render.py brach bei Ansichten mit mehr als einem Wurzelelement ab
        ("Extra content at the end of the document"). Arch muss in <data> gekapselt werden.
F51     Odoo 18 verlangt je PO-Eintrag die Kommentarzeile "#. module: <name>"; Freitext in
        Kommentarzeilen bricht das Modul-Upgrade mit AttributeError ab. Freitext auf "#:"-Zeilen
        erzeugt "malformed po file: unknown occurrence" (harmlos, aber laut).
F52     test_abo_smartbuttons.py darf den Fall "genau eine Rechnung" nicht voraussetzen: Testfall
        selbst herstellen (Abo ohne Rechnung, genau eine Testrechnung anlegen, pruefen, loeschen).
F53     Suchen mit ilike auf uebersetzten Feldern (z. B. ir.ui.menu.name) brauchen context lang=de_DE.
F54     Odoo 18 zeigt Abschnittstitel im Formular per CSS gross ("NOTIZEN") - DOM-Vergleiche
        schreibweisenunabhaengig machen.
Werkzeug  Mit get_views liefert erst der letzte Eintrag den zusammengefuehrten Arch
          (scripts/pruefe_o18_form_arch.py). Odoo 18 kennt fields_view_get nicht mehr.
```

## 9. Repo-Stand und Werkzeugliste

```
main = 29c0ea6 (lokal, GitHub, VM identisch)
PRs Session 120: #95 Produktformular (4da003d2), #96 Helfer github_pr.py (f41b2c6),
                 #97 Werkzeugfixes F52/F53 + VM-Abnahme (54eedfc),
                 #98 Statuszeilen bereinigt (29c0ea6)

Neue Werkzeuge (alle read-only gegen Odoo 11 Prod):
  vergleich_abo_produktformular.py / _felder.py     Formular- und Feldvergleich einer Instanz
  analyse_o11_produktformular_nutzung.py            Nutzung je Feld in Odoo 11, in Python gezaehlt
  analyse_produktformular_teil2/3/4.py              Kategorien/Konten, Kontofelder, Module, Timesheet
  pruefe_o11_abrechnung_sichtbarkeit.py             welche Felder des Odoo-11-Reiters sichtbar waren
  pruefe_account_gruppen.py / _2.py                 Buchhaltungsgruppen und Vererbung
  pruefe_o18_form_arch.py                           richtiger Arch aus get_views
  schlussprobe_produktformular.py                   Feld fuer Feld: im Modell / im Formular
  dump_produktformular_arch.py, zeige_o11_abrechnung_seite.py, zeige_o18_buchhaltung_seite.py
  browser_produktformular.py                        Browser-Abnahme mit echten Klicks
  github_pr.py                                      Pull Requests per REST-API (gh-CLI fehlt)
```

## 10. Start der naechsten Session

```
1. git pull --ff-only lokal und auf der VM (Stand 29c0ea6)
2. Bereich Abonnements NICHT anfassen (eingefroren; Ausnahme: konkreter Datenmigrations-Befund)
3. Anna nennt das naechste Modul / den naechsten Bereich; dann gilt der uebliche Ablauf:
   Analyse Odoo 11 read-only -> Struktur in Odoo 18 -> lokale Pruefung -> VM-Deploy und
   Modul-Upgrade -> Browser-Abnahme auf der VM -> Doku und Checkliste -> Commit/PR.
4. Arbeitsregeln: VM ist die verbindliche Abnahmeumgebung (docs/arbeitsregel-vm-abnahme.md),
   Odoo 11 nur lesend, keine Datenmigration ohne freigegebene Regel.
```
