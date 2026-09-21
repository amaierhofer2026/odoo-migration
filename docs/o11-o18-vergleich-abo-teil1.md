# Abonnements / Subscriptions: Teil 1 - Modulstatus und Grundstruktur

Stand: 18.09.2026 (Session 118, Teil 1)
Odoo 11 Prod `portal.it-kommunal.at` DB `ITK_V1_a` ausschliesslich lesend; Odoo 18 lokal + VM.

Keine Datenmigration. Keine Aenderung in Odoo 11 Prod. Keine grossflaechigen Aenderungen in Odoo 18.

## 1. Modulstatus Odoo 18

```
sale_subscription   Katalogeintrag Odoo Enterprise, Lizenz OEEL-1, Autor Odoo S.A., Zustand "uninstallable"
   -> der Moduldatensatz existiert, der Quellcode ist NICHT vorhanden
      (Dateisuche in /usr/lib/python3/dist-packages/odoo/addons und /mnt/extra-addons: kein Verzeichnis)
   -> "uninstallable" bedeutet hier: Enterprise-Modul ohne Code, es fehlen die Enterprise-Addons.
   -> NICHT der Traeger der Abo-Funktion in diesem System.

itk_subscription    ITK-Custom (Alvarium Services / A. + F. Vaethroeder), Lizenz LGPL-3,
                    Zustand INSTALLIERT, Version 18.0.1.1.0, shortdesc "ITK Abo-Management"
itk_multifactor     ITK-Custom, installiert 18.0.1.0.0 - erweitert die Abo-Modelle
```

**Antwort auf die Kernfrage: Das Abo kommt aus dem ITK-eigenen Modul `itk_subscription`.** In Odoo 11 Prod
ist genau dasselbe Modul im Einsatz (`itk_subscription` 11.0.1.1, installiert, gleicher Autor/Lizenz) -
also ITK-Custom in beiden Systemen, auf Basis der OCA-Vorlage (`agreement_sale_subscription` von
Open Source Integrators ist in Odoo 11 vorhanden, aber NICHT installiert).

Geladene Modelle (Modul `itk_subscription`, teils erweitert durch `itk_multifactor`):
```
sale.subscription                       Verkauf über Abonnement
sale.subscription.template              Vorlage für Verkaufsabonnement
sale.subscription.line                  Abonnementbuchung
sale.subscription.report                Abonnementstatistik
sale.subscription.close.reason          Grund für Beendigung
sale.subscription.close.reason.wizard   Assistent Beendigungsgrund
sale.subscription.wizard (+ option)     Assistent "Optionen hinzufügen"
sale.subscription.set.pricelist.confirm (itk_multifactor)
sale.subscriptionline.multifactor.update.confirm (itk_multifactor)
```

Cronjobs (beide aktiv):
```
Verkaufsabonnement: wiederkehrende Rechnungen    1 Tag
Verkaufsabonnement: Ablauf des Abonnements       1 Woche
```

Menues: eigener App-Eintrag "Abonnements" (Menue 586) mit
```
Abonnements            (seq 1)   Aktion 1105/1106 (list, kanban, form, pivot, graph)
Zu erneuernde Abonnements (seq 2) Aktion 1107
Abonnement Produkte    (seq 4)   Aktion 1104/1460 (sale.subscription.line)
Konfiguration          (seq ...) -> Vorlagen für Abonnements (Aktion 1110), Gründe für Beendigung (1111),
                                    Abonnementanalyse (1114, report)
```
Weitere Aktionen: "Endet in weniger als 7 Monaten" (1108), "Optionen hinzufügen" (1101),
"Preisliste für Abonnements festlegen" (1215), "Multifaktor für Abo-Zeilen aktualisieren" (1214).

**Test-Abonnements in Odoo 18 (5 Stueck) - technisch konsistent:**
```
172  Test Monatsabo          draft  Kunde Test Firma             kein Auftrag  Liste Standard  Start 2026-07-01  Summe 0.0
182  Monatsabrechnung-Abo    open   Mustermann Max               S00179        Standard        2026-07-07        79.0
183  Monatsabrechnung-Abo    open   Test Firma                   S00180        Standard        2026-07-08        49.0
184  Monatsabrechnung-Abo    open   Test Firma                   S00190        Standard        2026-07-10        210.0
185  NV-00962                open   Breitenbrunn am Neusiedler S. kein Auftrag  Preisliste ...  2013-07-19        52.0
```
Alle mit Vorlage, Preisliste, Intervall und Startdatum; drei mit Verkaufsauftrag verknuepft
(`sale.subscription.sale_order_id` -> `sale.order`). Datensatz 185 hat ein Startdatum aus 2013 und einen
Namen aus dem alten Nummernkreis (Beobachtung, kein Blocker).

## 2. Odoo 11 Prod read-only: Abo-Bestand

```
sale.subscription gesamt                 1.764
   draft 3 | open 1.482 | pending 0 | close 48 | cancel 231
sale.subscription.line                   2.434 Zeilen
mit Verkaufsauftrag verknuepft           1.722 von 1.764  (42 ohne Auftragsbezug)
```

Vorlagen (5):
```
1  Jahresabrechnung-Abonnement
2  Monatsabrechnung-Abonnement
3  Quartalsabrechnung-Abonnement
4  5-Jahresabo
5  J- Jahresabrechnungsabo-Mindestvertragsdauer 12 Monate
```

Feldnutzung in Odoo 11 (von 1.764):
```
recurring_rule_type 1764 | recurring_interval 1764 | recurring_next_date 1764 | recurring_total 1764
partner_id 1764 | company_id 1764 | template_id 1764 | pricelist_id 1764 | date_start 1764 | user_id 1763
sale_order_id 1722 | close_reason_id 291 | date 52 | tag_ids 0
in Odoo 11 nicht vorhanden: recurring_invoice, payment_term_id, in_progress, team_id
```

## 3. Feldvergleich (vorlaeufig, 18 zentrale Felder)

```
Feld                    Odoo 11 (Label)              Odoo 18 (Label)                Bewertung
name                    Abonnement                   Abonnement                    1:1
partner_id              Kunde                        Kunde                         1:1
state                   Status                       Status                        1:1 (Werte siehe unten)
sale_order_id           Verkaufsauftrag              Verkaufsauftrag               1:1
template_id             Vorlage                      Vorlage                       1:1
pricelist_id            Preisliste                   Preisliste                    1:1
payment_term_id         (fehlt in O11)               Zahlungsbedingungen           neu in O18
user_id                 Verkaeufer                   Verkaeufer                     1:1
company_id              Unternehmen                  Unternehmen                    1:1
date_start              Abo-Start                    Abo-Start                     1:1
date                    Ende                         Ende                           1:1 (O11 nur 52x gefuellt)
recurring_next_date     Naechste Abrechnung          Naechste Abrechnung            1:1
recurring_rule_type     Abrechnungszeitraum          Abrechnungszeitraum            1:1 (Selection-Werte pruefen)
recurring_interval      Intervall                    Intervall                      1:1
recurring_total         Wiederkehrender Betrag       Wiederkehrender Betrag         1:1
close_reason_id         Beendigungsgrund             Beendigungsgrund               1:1 (O11 291x)
in_progress             (fehlt in O11)               In Bearbeitung                 berechnet, kein Ziel
team_id                 (fehlt in O11)               Verkaufsteam                   neu in O18
tag_ids                 Stichwoerter (0x genutzt)    Stichwoerter                   1:1, Datenbestand 0
```

Das vollstaendige Feldinventar ueber alle Felder beider Modelle (inkl. compute/store, Default,
Selection-Werte, required/readonly und Zuordnung je Feld) ist der erste Arbeitsschritt von Teil 2.

## 4. Erste Bewertung fuer die Migration

- Traegermodul ist in beiden Systemen dasselbe ITK-Modul -> gleiche Fachlogik, deutlich kleineres Risiko.
- 1.722 von 1.764 Abos haengen an einem Verkaufsauftrag -> die Reihenfolge der Migration muss
  Auftraege vor Abos vorsehen.
- Zustandswerte: Odoo 11 nutzt draft/open/close/cancel; in Odoo 18 zusaetzlich "pending" vorhanden.
- Kein Abo-Feld in Odoo 11 ohne Ziel; neu in Odoo 18 sind payment_term_id, in_progress und team_id.

## 5. Zwischenbericht Teil 1

**ERLEDIGT**
- Modulstatus geklaert: `sale_subscription` ist Enterprise-Katalog ohne Code (daher uninstallable),
  Traeger ist `itk_subscription` (installiert, 18.0.1.1.0), zusaetzlich `itk_multifactor`.
- Modelle, Views/Aktionen/Menues, Cronjobs und Testdaten-Konsistenz aufgenommen.
- Odoo 11 read-only: 1.764 Abos, Statusverteilung, 5 Vorlagen, Feldnutzung, Auftragsverknuepfung.
- Vorlaeufiger Feldvergleich der 18 zentralen Felder.

**GEFUNDENE UNTERSCHIEDE**
- Zustaende: Odoo 18 kennt zusaetzlich "pending"; Odoo 11 hat 0 Datensaetze darin.
- Felder ohne Odoo-11-Quelle: payment_term_id, in_progress (berechnet), team_id.
- Datensatz 185 in Odoo 18 mit Startdatum 2013 und altem Nummernkreis (Beobachtung).
- 42 Abos in Odoo 11 ohne Auftragsbezug - Auswahlregel fuer die Migration noetig.

**TECHNISCHE BLOCKER**
- Keiner. Insbesondere ist der Enterprise-Katalogeintrag kein Blocker: die Funktion liegt vollstaendig
  im ITK-Modul. Keine IPAX-Anfrage noetig.

**EMPFOHLENER TEIL 2**
1. Vollstaendiges Feldinventar beider Modelle (sale.subscription und sale.subscription.line) mit
   Typ, Relation, required, readonly, compute/store, Default, Selection-Werten, Odoo-11-Nutzung und
   Ziel-Einstufung (1:1 / Transformation / berechnet / obsolet / kein Ziel / Klaerung).
2. Selection-Werte der Zustaende und Abrechnungszeitraeume O11 <-> O18 gegenueberstellen.
3. Formulare, Reiter, Smart Buttons und Zustandslogik vergleichen (O11 gegen O18 im Browser).
4. Zeilenmodell (Produkte, Mengen, Preise, Multiplikationsfaktor) pruefen.
5. Erst danach konkrete Anpassungen in Odoo 18.
