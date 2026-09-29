# Odoo 11 -> Odoo 18: Bereich Verkauf, Teil 5 - Abschlussprüfung

Stand: 29.09.2026, Session 121. Odoo 11 Prod (`portal.it-kommunal.at`, DB `ITK_V1_a`) wird
ausschliesslich lesend gelesen. Aenderungen nur in Odoo 18. Keine Datenmigration.
Odoo-18-Zusatzfunktionen bleiben erhalten (Nachweis ueber die Erhaltungspruefungen der Teile 3 und 4).

## Auftrag (Anna, 29.09.2026)

```
- Gesamtpruefung aller Teile 1-4
- keine Datenmigration, Odoo 11 strikt read-only
- Odoo-18-Zusatzfunktionen erhalten
- offene funktionale/strukturelle Luecken suchen
- Regressionstest
- Browserpruefung auf der VM
- erst wenn wirklich keine offenen Punkte mehr bestehen: Verkauf als vollstaendig funktionsfaehig
  und vollstaendig migrationsvorbereitet markieren
- in kleinen Schritten, Zwischenbericht nach dem ersten Abschlussblock
```

## Blockplan

```
Block 1  Regressionstest: alle Prueflaeufe der Teile 1-4 gegen lokal und VM     (dieser Block)
Block 2  Lueckenanalyse: Abgleich der Odoo-11-Funktionen des Verkaufs gegen Odoo 18
         (Menues, Felder, Reiter, Buttons, Status, Filter/Gruppierungen, Ansichten, Berichte,
          Druckberichte, Stammdaten) und Suche nach offenen strukturellen Luecken
Block 3  Browserpruefung auf der VM: Menue, Formular, Ansichten, Kalender, Bericht, Drucken
Block 4  Abschlussmarkierung: Checkliste/README/PROJECT_KNOWLEDGE, Abschlussdokument
```

## Block 1 - Regressionstest (29.09.2026)

Werkzeug: `scripts/abschluss_verkauf_regression.py` (fuehrt alle Verkaufs-Prueflaeufe aus,
vergleicht gegen die dokumentierten Referenzwerte, sammelt Abweichungen;
Rohdaten `docs/_verkauf_teil5_regression.json`).

```
Prueflauf                                            Ergebnis      Referenz      Bereich
verify_s121_verkauf_menue.py                          41 OK / 0     41            Teil 1 Menues/Module
verify_s121_verkauf_teil2.py                         111 OK / 0    111            Teil 2 Feldinventar
verify_s121_verkauf_teil3_reiter.py                   64 OK / 0     64            Teil 3.1 Formulare/Reiter
verify_s121_verkauf_teil3_status.py                   53 OK / 0     53            Teil 3.3 Statuswechsel
verify_s121_verkauf_teil3_filter.py                  199 OK / 0    199            Teil 3.4 Filter/Grupp./Suche
verify_s121_verkauf_teil4_ansichten.py               146 OK / 0    146            Teil 4.1 Ansichten
verify_s121_verkauf_kalender.py                       33 OK / 0     33            Teil 4.1 Kalender
verify_s121_verkauf_teil4_bericht_kanaele.py          84 OK / 0     84            Teil 4.2 Bericht Kanaele
verify_s121_verkauf_teil4_druckberichte.py            69 OK / 0     69            Teil 4.3 Druckberichte
verify_s117_auftraege.py                              65 OK / 0     65            Bestand Auftraege
verify_s118_abo.py                                    19 OK / 0     19            Bestand Abonnements
------------------------------------------------------------------------------
Gesamt                                              884 OK / 0 FEHL   -           11 Prueflaeufe
```

Keine Regression. Zwei Referenzwerte mussten nachgezogen werden, weil die Pruefung noch den Stand
vor Teil 4 abbildete (fachlich keine Fehler, sondern Ergebnisse der Umsetzung):

```
verify_s121_verkauf_menue.py
  1. Menueumfang Odoo 18 unter "Verkauf": 37 -> 39
     (+1 "Auftragskalender" aus Teil 4 Schritt 1, +1 "Verkaufsaufträge aller Kanäle" aus Teil 4 Schritt 2)
  2. "Berichtswesen/Verkaufsaufträge aller Kanäle": galt als nicht nachgebaut, ist seit
     Teil 4 Schritt 2 vorhanden -> Pruefung von "nicht vorhanden" auf "vorhanden" umgestellt
     (Liste IN_O18_SEIT_TEIL4); die beiden uebrigen bewusst nicht uebernommenen Odoo-11-Menues
     (Reportlayout Kategorien, Reklamationen) bleiben unveraendert geprueft
```

Modul- und Bestandsstand (beide Instanzen geprueft):

```
itk_sale_management 18.0.1.6.0, itk_reports 18.0.1.0.0, itk_saleorder_lines 18.0.1.0.0,
sale 18.0.1.2, sale_management 18.0.1.0 - lokal und VM identisch, jeweils installiert
Bestand unveraendert: lokal 18 Auftraege / 28 Positionen / 28 Berichtszeilen,
                      VM 20 Auftraege / 29 Positionen / 29 Berichtszeilen
```

## Block 2 - Lueckenanalyse und Schliessung der Luecke (29.09.2026)

```
Block 2 durchgefuehrt: systematischer Abgleich aller in Odoo 11 verwendeten Verkaufsfunktionen
  (Felder, Menueziele/Modelle, Automatismen, Mailvorlagen, Stammdaten, Module, Ansichten,
  Berichte, Druckberichte, Nutzungsspuren) gegen Odoo 18.
Ergebnis: eine echte strukturelle Luecke - die Lageranbindung des Verkaufs (sale_stock/stock/
  stock_account fehlten in Odoo 18, in Odoo 11 mit 238 Lagerbelegen aus Verkaeufen in Verwendung).
  Alle uebrigen Kandidaten waren Scheinbefunde (Feldumbenennungen, tote Funktionen mit
  0 Verwendung) oder dokumentierte Abweichungen.
Dokumente: docs/o11-o18-vergleich-verkauf-teil5-luecken.md,
           docs/o11-o18-verkauf-teil5-lageranbindung.md

Luecke geschlossen (29.09.2026, Freigabe Anna):
  stock 18.0.1.1, stock_account 18.0.1.1, sale_stock 18.0.1.0 in Odoo 18 installiert (lokal und VM)
  Nebenschritte: itk_product 18.0.1.0.3 (responsible_id auf Odoo-18-Standarddefinition),
    l10n_at auf der VM aktualisiert, project_stock auf der VM installiert
  Pruefung: pruefe_verkauf_lieferung.py lokal 26 OK / 0 FEHL, VM 26 OK / 0 FEHL
    (Testauftrag -> Lieferbeleg mit Position und Verkaufsbezug, danach bereinigt)
  Browserpruefung: browser_verkauf_lieferung.py lokal 14 OK / 0 FEHL, VM 14 OK / 0 FEHL,
    0 JavaScript-Fehler, 0 RPC-Fehler (Smart Button "1 Lieferung", Lieferbeleg im Formular)
  Regressionstest Verkauf und Abonnements: 886 OK / 0 FEHL (11 Prueflaeufe, lokal und VM)
  Testdaten vollstaendig entfernt; keine Odoo-11-Daten uebernommen
```

## Offene Punkte nach Block 2

Keine. Block 3 (Browserpruefung auf der VM) folgt.
