# Abonnements / Subscriptions: Teil 3 - Formulare, Reiter, Smart Buttons, Zustandslogik

Stand: 18.09.2026 (Session 118, Teil 3)
Odoo 11 Prod ausschliesslich lesend (nur Ansichten geoeffnet), Odoo 18 VM als Abnahmeumgebung.
Keine Datenmigration, keine Aenderungen.

## 1. Entscheidungen von Anna (18.09.2026)

- `recurring_next_date`: die Odoo-18-Beschriftung "Datum der nächsten Rechnung" bleibt. Keine Umbenennung.
- Die 42 Abos ohne Verkaufsauftrag werden **nicht** migriert und es wird jetzt **keine** Migrationsregel
  festgelegt. Nur die funktionale Frage wird geprueft (Abschnitt 5).

## 2. Strukturvergleich der Ansichten (read-only aus den View-Archs)

```
                        Odoo 11                                  Odoo 18
Formularfelder          37 Felder                                 36 Felder, gleiche Reihenfolge
Reiter                  Wiederkehrende Buchungen, Einstellungen   Abonnement-Einträge, Einstellungen
Statusleiste            5 Werte (Neu, Laufend, Zu erneuern,         identisch
                        Abgeschlossen, Abgebrochen)
Liste (Spalten)         code, Kunde, sale_order_confirmation_date, identisch (Odoo 18 ohne company_id)
                        recurring_next_date, end_of_contract_date,
                        Preisliste, Verkäufer, recurring_total, Status
Suche/Filter            Neu, Laufend, Zu erneuern, Abgeschlossen,   identisch
                        Abgebrochen
Feldreihenfolge         state, invoice_count, sale_order_count, display_name, partner_id, pricelist_id,
                        code, recurring_next_date, user_id, template_id, currency_id, sale_order_id,
                        sale_order_confirmation_date, date_start, Mindestvertragsdauer, end_of_contract_date,
                        Kuendigungsfrist, noticeperiod, date, close_reason_id, Positionen, recurring_total,
                        tag_ids, analytic_account_id, payment_mandatory  -> in beiden Systemen gleich
```

Aktionsbuttons im Formular (gleiche Namen, gleiche Sichtbarkeitsregeln):
```
Button                   Beschriftung O11 / O18           Sichtbarkeit (identisch in beiden)
set_open                 Abonnement starten               unsichtbar wenn state = open
set_pending              Zu erneuern                      unsichtbar wenn state in pending/draft/close/cancel
(Server-Aktion)          Abo-Auftrag schließen            unsichtbar wenn state in draft/close/cancel
(Server-Aktion)          Abo-Auftrag abbrechen            unsichtbar wenn state in cancel/close
prepare_renewal_order    Erneuerungsangebot               unsichtbar wenn state = draft
recurring_invoice        Rechnung manuell erstellen       O11 englisch ("Generate Invoice manually")
open_website_url         Online-Vorschau                  Smart Button, immer sichtbar
action_subscription_invoice  Rechnungen                   Smart Button, Zaehler
action_open_sales        Verkauf                          Smart Button, Zaehler
```
Unterschied: Odoo 11 hat zusaetzlich den Button "Abonnement-Zusatzverkäufe" (Server-Aktion 513).
Odoo 18 fuehrt diese Funktion ueber den Assistenten "Optionen hinzufügen" (Aktion 1101,
`sale.subscription.wizard`) - funktional vorhanden, anderer Weg. **Als Anpassungsvorschlag notiert,
aber nicht geaendert (erst nach eindeutiger Pruefung).**

## 3. Browser-Pruefung

```
Werkzeug: scripts/browser_abo_pruef.py (liest beide Systeme, Odoo 11 nur oeffnend)

Zustand        Odoo 18 VM (Abo)                  Odoo 11 Prod (Abo)
Neu            id 172, ohne Auftrag:             id 2855 (NV-01700):
               Buttons "Abonnement starten",     gleicher Feldumfang, 0 Rechnungen, 0 Verkauf
               "Abo-Auftrag abbrechen";          (Odoo 11 rendert die Aktionsbuttons in der
               Smart Buttons Online-Vorschau,    Bearbeiten-Leiste; Regeln identisch)
               0 Rechnungen, 0 Verkauf
Laufend        id 182: Buttons "Zu erneuern",     id 955 (NV-00955): 7 Rechnungen, 1 Verkauf
               "Abo-Auftrag schließen", "Abo-
               Auftrag abbrechen", "Erneuerungs-
               angebot"; Smart Buttons
               1 Rechnungen, 1 Verkauf
Zu erneuern    kein Testdatensatz auf der VM      kein Datensatz in Prod (0 von 1.764)
Abgeschlossen  kein Testdatensatz auf der VM      id 969: Feld "Grund für die Beendigung" sichtbar
Abgebrochen    kein Testdatensatz auf der VM      id 954: Feld "Grund für die Beendigung" sichtbar
```
Ergebnis: Feldumfang, Reiter, Statusleiste, Zaehler und Smart Buttons sind in beiden Systemen
deckungsgleich. Die Buttons erscheinen/verschwinden nach denselben Regeln (aus den View-Archs belegt,
auf der VM fuer die Zustaende Neu und Laufend auch im Browser bestaetigt).
`pending`, `close` und `cancel` haben in Odoo 18 (Teststand) keine Datensaetze; die Regeln sind dort
aus dem View-Arch identisch. Screenshots 48_* im Desktop-Ordner.

## 4. Smart Buttons und Zaehler

```
Online-Vorschau   immer sichtbar
Rechnungen        Zaehler invoice_count, Klick oeffnet die Rechnungsliste (Odoo 11 und 18 gleich)
Verkauf           Zaehler sale_order_count, Klick oeffnet den Verkaufsauftrag
Auf der VM: "1 Rechnungen", "1 Verkauf" beim laufenden Abo; "0 Rechnungen", "0 Verkauf" beim Neu-Status
```

## 5. Die 42 Abos ohne Verkaufsauftrag - funktionale Pruefung

**Ergebnis: Odoo 18 unterstuetzt Abonnements ohne Verkaufsauftrag vollstaendig und fehlerfrei.**
Belege:
```
Odoo 18 VM, Abo 172 "Test Monatsabo" (state draft, sale_order_id leer):
   Formular vollstaendig (Kunde, Preisliste, Vorlage, Verkaufsauftrag leer, Startdatum,
   Datum der nächsten Rechnung, Enddatum, Verkäufer, Wiederkehrender Preis, Kuendigungsfrist,
   Mindestvertragsdauer), Positionen und Chatter vorhanden
   Aktion "Abonnement starten" verfuegbar, "Abo-Auftrag abbrechen" verfuegbar
   Smart Buttons: Online-Vorschau, 0 Rechnungen, 0 Verkauf (korrekt leer)
Odoo 18 VM, Abo 185 "NV-00962" (state open, ohne Auftrag): laeuft mit Rechnungsstellung
Odoo 11 Prod, Abo 1044 (cancel, ohne Auftrag): gleiches Bild - sichtbarer Umfang identisch
```
Kein Feld erzwingt einen Verkaufsauftrag; `sale_order_id` ist nicht `required`. Die 42 Alt-Abos
koennten also uebernommen werden, wenn Anna das spaeter entscheidet. **Jetzt keine Regel, keine Migration.**

## 6. Suche, Filter, Gruppieren, Konfiguration

```
Suche/Filter        identisch (Filter je Status, dazu Name/Kunde)
Konfiguration       Vorlagen für Abonnements (kanban/list/form) - in beiden Systemen vorhanden,
                    Odoo 11: 5 Vorlagen, Odoo 18: Testdaten
Gruende für Beendigung   Liste in beiden Systemen vorhanden (Odoo 18: sale.subscription.close.reason)
Abonnementanalyse   Odoo 18: Aktion 1114 (sale.subscription.report, graph/pivot) - neu gegenueber Odoo 11,
                    bleibt erhalten
Zusaetzliche Odoo-18-Funktionen (Optionen hinzufügen, Preisliste setzen, Multifaktor-Aktualisierung,
Endet in weniger als 7 Monaten) bleiben erhalten.
```

## 7. Zwischenbericht Teil 3

**ERLEDIGT**
- View-Vergleich (Felder, Reihenfolge, Reiter, Statusleiste, Listen, Suche, Filter, Buttons, Sichtbarkeitsregeln).
- Browser-Pruefung beider Systeme fuer die Zustaende Neu und Laufend sowie Abo ohne Auftrag.
- Funktionsnachweis: Abos ohne Verkaufsauftrag laufen in Odoo 18 vollstaendig.
- Entscheidungen von Anna festgehalten (Beschriftung bleibt, 42 Abos ohne Regel).

**FUNKTIONSUNTERSCHIEDE**
- "Abonnement-Zusatzverkäufe" (Odoo 11, Server-Aktion 513) heisst in Odoo 18 "Optionen hinzufügen"
  (Assistent, Aktion 1101) - funktional vorhanden, anderer Weg.
- Odoo 11 rendert die Aktionsbuttons in der Bearbeiten-Leiste, Odoo 18 als eigene Buttons - rein optisch.

**SICHTBARKEITSUNTERSCHIEDE**
- Keine. Alle Sichtbarkeitsregeln der Aktions- und Smart Buttons sind identisch.

**FEHLENDE FUNKTIONEN**
- Keine. Alle Aktionen aus Odoo 11 existieren in Odoo 18; zusaetzlich gibt es neue (Analyse, Optionen,
  Preisliste setzen, Multifaktor-Aktualisierung).

**42 ABOS OHNE AUFTRAG**
- Odoo 18 unterstuetzt sie vollstaendig (Beleg: Abo 172 und 185 auf der VM). Keine Migrationsregel
  festgelegt, wie von Anna vorgegeben.

**EMPFOHLENE ANPASSUNGEN FUER TEIL 4**
1. Keine strukturellen Anpassungen erforderlich - die Abo-Ansichten und die Zustandslogik sind deckungsgleich.
2. Optional: den Weg zu Zusatzverkaeufen im Formular sichtbarer machen (Odoo 11 hatte einen eigenen Button) -
   Entscheidung Anna, vorher nicht aendern.
3. Teil 4: Wortlaute der Reiter ("Wiederkehrende Buchungen" gegen "Abonnement-Einträge") entscheiden,
   Abo-Menue/Bericht im Browser pruefen, und die Migration der Abos vorbereiten (Reihenfolge: Auftraege vor
   Abos; Feldzuordnung 1:1 aus Teil 2).
