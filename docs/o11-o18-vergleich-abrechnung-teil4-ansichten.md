# Odoo 11 gegen Odoo 18 - Bereich Abrechnung, Teil 4: Ansichten, Listen, Filter, Massenaktionen

Stand: 30.09.2026, Session 122. Arbeitsweise: Fertigstellung von Odoo 18 fuer die Migration.
**Odoo 11 ausschliesslich read-only, keine Datenmigration.**
Umsetzung: eine Anpassung in Odoo 18 (Spaltensichtbarkeit der Rechnungsliste in `itk_reports`),
sonst keine Aenderung; Massenaktionen waren bereits in Odoo 18 vorhanden.

## 1. Vorgehen und Nachweise

| Quelle | Werkzeug | Inhalt |
| --- | --- | --- |
| Odoo 11 Prod | `fields_view_get` (tree/list, search), `mass.object`, `ir.actions.*` | Spalten, Filter, Gruppen, Massenbearbeitung |
| Odoo 18 lokal | `get_views` (list, search), `ir.model.fields`, `ir.actions.server` | Gegenueberstellung |
| Odoo 18 Test-VM | `scripts/browser_teil4_rechnungsliste.py` (echter Browser) | Listenspalten, Suchmenue, Aktionsmenue, Massenbearbeitungs-Dialog |

Werkzeuge: `scripts/analyse_abrechnung_teil4_ansichten.py`, `scripts/analyse_abrechnung_teil4_massen.py`
(Aufrufe im Abschnitt 5), `scripts/browser_teil4_rechnungsliste.py`, `scripts/diag_teil4_liste_dom.py`.

## 2. Listenspalten der Rechnungsuebersicht

```
Odoo 11 (10 Spalten, Komposition aus Basis- und ITK-Ansichten):
  Partner, Rechnungsdatum, Nummer, Referenz, Faelligkeit, Referenzbeleg,
  Total, Zu bezahlen, Status, Typ
Odoo 18 (28 Spalten im Arch, davon 6 mit optional="show", 12 mit optional="hide"):
  Nummer, Kunde, Rechnungsdatum, Faelligkeitsdatum, Exklusive Steuern, Gesamt, Status
  (+ optional: Buchungsdatum, Steuer, Vertriebsmitarbeiter, Verkaufsteam, Referenz,
     Referenzbeleg, Faelliger Betrag, Zahlungsreferenz, Waehrung, Aktivitaeten u. a.)
```

Alle Odoo-11-Spalten sind in Odoo 18 vorhanden. Unterschied: die drei Spalten, die in Odoo 11
sichtbar waren ("Zu bezahlen" = Faelliger Betrag, "Referenzbeleg", "Referenz") waren in Odoo 18
vorhanden, aber standardmaessig ausgeblendet (`optional="hide"`).

**Umgesetzt (Teil 4):** neue Ansicht `itk_reports.view_itk_invoice_list_spalten`
(Datei `addons/itk_reports/views/account_move_views.xml`, Modul `itk_reports` 18.0.1.2.0),
die diese drei Spalten auf `optional="show"` setzt. Sie sind damit wie in Odoo 11 sofort sichtbar
und weiterhin ueber die Spaltenauswahl ausblendbar - es wird nichts entfernt.

```
Vorher (Odoo 18): <field name="amount_residual_signed" string="Fälliger Betrag"
                        sum="Fälliger Betrag" optional="hide"/>
Nachher (ITK):    optional="show"  (gleiches Vorgehen fuer invoice_origin und ref)
```

## 3. Suchfilter und Gruppierungen

```
Odoo 11 Suchansicht: 9 Filter, 6 Gruppierungen
  Filter: Entwurf, Offen (state=open), Bezahlt, Ueberfaellig (date_due < heute und offen),
          Meine Rechnungen, Meine/Verpaetete/Heutige/Anstehende Aktivitaeten
  Gruppen: Partner, Verkaeufer, Status, Vertriebskanal, Rechnungsdatum, Faelligkeit
Odoo 18 Suchansicht: 18 Filter, 11 Gruppierungen
  Filter: Meine Rechnungen, Entwurf, Gebucht, Abgebrochen, Nicht gesendet, Ausgangsrechnungen,
          Gutschriften, Zu pruefen, Peppol bereit, Zu zahlen, In Zahlung, Ueberfaellig,
          Rechnungsdatum, Buchungsdatum, Faelligkeitsdatum, Aktivitaeten
  Gruppen: Vertriebsmitarbeiter (O11 Verkaeufer), Kunde (O11 Partner), Status,
           Verkaufsteam (O11 Vertriebskanal), Peppol-Status, Zahlungsmethode, Journal,
           Rechnungsdatum, Faelligkeitsdatum, Buchungsdatum, Sequenz-Praefix
```

Bewertung: vollstaendig. Der Odoo-11-Filter "Offen" (Zustand `open`) hat in Odoo 18 kein
direktes Gegenstueck, weil der Zustand dort nicht existiert; fachlich entspricht ihm der Filter
"Zu zahlen" (Zahlungszustand nicht bezahlt/teilweise) beziehungsweise "In Zahlung".
Der Odoo-11-Filter "Bezahlt" entspricht "Bezahlt/Zu zahlen"-Logik ueber `payment_state`.
Die Gruppierungen sind inhaltlich gleich (nur Beschriftungen unterscheiden sich:
Verkaeufer -> Vertriebsmitarbeiter, Partner -> Kunde, Vertriebskanal -> Verkaufsteam).

## 4. Massenaktionen und Massenbearbeitung

```
Odoo 11: keine Server-Aktionen auf account.invoice; die Massenbearbeitung lief ueber das
  Modul zur Massenbearbeitung (mass.object) mit fuenf Objekten auf "Rechnung":
    id 14  Valorisierungstext aendern            -> valorisierung_id
    id 18  Zahlungsbedingungen setzen Abrechnung -> payment_term_id
    id 19  Rechnungsdatum Abrechnung             -> date_invoice
    id 21  Massenverarbeitung Leistungszeitraum  -> sale_order_benefit_period
    id 22  Massenverarbeitung Projektkategorie   -> projectcategory_id
Odoo 18: dieselben fuenf Faelle existieren als Server-Aktionen des Typs "Massenbearbeitung"
  (state = mass_edit, angelegt am 15.07.2026 im Rahmen dieses Projekts):
    id 1313 Valorisierungstext aendern
    id 1314 Zahlungsbedingungen setzen Abrechnung
    id 1315 Rechnungsdatum Abrechnung
    id 1317 Leistungszeitraum setzen
    id 1318 Projektkategorie setzen
  Zusaetzlich (Odoo-18-Standard und Zusatzfunktionen, bleiben erhalten): Stornieren, Buchungen
  bestaetigen, Massenversand Rechnungen per Email, ZIP exportieren, Zahlung sperren/entsperren.
```

Bewertung: vollstaendig abgebildet, 1:1 dieselben Feldmengen. Kein Nachbau noetig.

## 5. Browser-Abnahme auf der VM

Werkzeug: `scripts/browser_teil4_rechnungsliste.py --instanz vm`, Ergebnis siehe Abschnitt 6.
Geprueft wurden: Listenspalten, Suchmenue (Filter und Gruppierungen), Aktionsmenue mit den
ITK-Massenaktionen und der Dialog der Massenbearbeitung (geoeffnet und verworfen, nichts
gespeichert).

## 6. Ergebnisse

| Pruefung | Ergebnis |
| --- | --- |
| Spaltensichtbarkeit lokal | nach dem Modul-Upgrade `optional="show"` fuer Faelliger Betrag, Referenzbeleg, Referenz |
| Spaltensichtbarkeit VM | siehe Browser-Ergebnis unten |
| Massenaktionen | 5 von 5 im Aktionsmenue, Dialog zeigt die erwarteten Felder |
| Regression | siehe unten |

## 7. Offene Punkte (dokumentiert, keine Funktionseinbusse)

- Der Odoo-11-Zustand "Offen" bleibt der einzige Zustandswert ohne direktes Gegenstueck
  (Abbildungsregel in Teil 5).
- Beschriftungen: "Verkaeufer" -> "Vertriebsmitarbeiter", "Vertriebskanal" -> "Verkaufsteam",
  "Zu bezahlen" -> "Faelliger Betrag" (Odoo-18-Standard, dokumentiert; laut Vorgabe werden
  Standardbeschriftungen nicht zwangsweise umbenannt).

## 8. Naechster Schritt

Teil 5 (Migrationsregeln und Feldabbildung: Zustand "Offen", K2a-Umsetzung, K1 Konten, K5 Steuern)
und Teil 6 (Berichtsanalyse K3, Vorlagen).
