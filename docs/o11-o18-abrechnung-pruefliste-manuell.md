# Abrechnung - Pruefliste fuer die manuelle Browserkontrolle (Stand 01.10.2026)

Status des Bereichs Abrechnung: **IN ARBEIT** - die endgueltige Markierung erfolgt erst nach Ihrer
manuellen Browserkontrolle. Bis dahin finden **keine weiteren Umbauten** und **kein neues Modul**
statt. Letzter synchroner Stand: `main = ba7ecf2` (lokal = GitHub = VM).

## 1. Die fuenf Bereiche mit Menueweg, Aktion und Nachweis

| Bereich | Menueweg (Odoo 18) | Aktion | Nachweis |
|---|---|---|---|
| Ausgangsrechnungen | Abrechnung > Verkauf > Ausgangsrechnungen | 354 (`account.move`, list/kanban/form/activity) | `Desktop\Odoo18-Abnahme-Session122\rechnung\Rechnung_lokal.png` und `Rechnung_vm.png`; Matrix `docs/o11-o18-abrechnung-ausgangsrechnungen-visuell.md` |
| Kunden-Gutschriften | Abrechnung > Verkauf > Kunden-Gutschriften | 355/356 (Belegart Kunden-Gutschrift) | `belege\Gutschrift_lokal.png` und `Gutschrift_vm.png` (Testbeleg nur in Odoo 18, danach entfernt); Matrix `docs/o11-o18-abrechnung-gutschrift-zahlung-visuell.md` |
| Zahlungen | Abrechnung > Verkauf > Zahlungen | 330 (`account.payment`) | `belege\Zahlung_lokal.png` und `Zahlung_vm.png`; Matrix `docs/o11-o18-abrechnung-gutschrift-zahlung-visuell.md` |
| Eingangsrechnungen | Abrechnung > Einkauf > Eingangsrechnungen | 357 | `belege\Eingangsrechnungen_lokal.png` und `Eingangsrechnungen_vm.png`; Matrix `docs/o11-o18-abrechnung-einkauf-visuell.md` |
| Lieferanten-Gutschriften | Abrechnung > Einkauf > Lieferanten-Gutschriften | 358 | `belege\Lieferanten_Gutschriften_lokal.png` und `Lieferanten_Gutschriften_vm.png`; Matrix `docs/o11-o18-abrechnung-einkauf-visuell.md` |

Sichtbarer Aufbau nach der Anpassung (alle Belegarten ausser Zahlung nutzen dieselbe Ansicht):

```
Kopfbereich : Kunde/Lieferant, Lieferadresse, Zahlungsbedingungen, Leistungszeitraum,
              Rechnungsdatum, Faelligkeit, Verkaeufer, Vertriebskanal, Project Category,
              Valorisation Text, Waehrung, Nettobetrag, Gesamt, Steuersatz
Reiter      : Rechnung | Andere Informationen
Zeilen      : Line NO. | Produkt | Kostenstelle | Menge | Preis pro ME | Rabatt (%) |
              Steuern | Zwischensumme   (Maßeinheit bleibt optionale Odoo-18-Spalte)
Zahlung     : Zahlungsart, Zahlungsdatum, Betrag, Journal, Kunde, Notiz,
              Odoo-11-Zahlungsnummer, Senden; Buttons Bestaetigen und "setze auf Entwurf"
```

## 2. Ihre vier Abnahmepunkte und wo sie belegt sind

1. **Sichtbare Odoo-11-Bezeichnungen uebernommen, soweit technisch moeglich.**
   Umgesetzt und im Browser belegt: Reiter "Rechnung"/"Andere Informationen", Buttons
   "Auf Entwurf setzen", "Nach Gutschrift fragen", "Einzahlung erfassen", "setze auf Entwurf",
   Zeilenbezeichnungen "Produkt", "Kostenstelle", "Menge", "Preis pro ME", "Rabatt (%)",
   "Steuern", "Zwischensumme", "Total", Konfigurationsfelder (Steuern, Journale, Steuerzuordnung,
   Waehrungen), Menuebezeichnungen (Abrechnung, Verkauf, Einkauf, Kunden-Gutschriften,
   Lieferanten-Gutschriften, Finanzen, Steuerzuordnung, Bankkonten, Zahlungen) sowie
   App- und Menuepositionen (Zahlungsbedingungen unter Konfiguration > Verwaltung).
   Nicht angleichbar: Griffspalte "Line NO." (Renderer der Griffspalte), Beschreibung
   (Zusammenfuehrung im Produktfeld), Sektion (Zeiltyp statt Spalte), Kostenstellen-Tags
   (in Odoo 18 nicht mehr vorhanden).

2. **Gleiche fachliche Position.**
   Die Odoo-11-Kopffelder stehen jetzt im sichtbaren Kopfbereich (vorher hinter dem Reiter);
   die Zeilenspalten stehen in Odoo-11-Reihenfolge. Belegt in den drei Matrizen mit der Spalte
   "gleiche Position ja/nein".

3. **Odoo-18-Zusatzfunktionen bleiben erhalten.**
   Erhalten und im Browser sichtbar: Kundenreferenz, Lieferbedingungen, Liefertermin,
   Incoterm-Standort, Steuerzuordnung, Zahlungsmethode, Zahlungsreferenz, Automatisch buchen,
   Geprueft, Odoo-11-Rechnungsnummer/-Zahlungsnummer, Bankkonto des Unternehmens, Senden,
   Erhalten, Katalog, Vorschau, Sperren/Storno, Peppol, Rechnungsanalyse, Pruefpfad,
   Abrechnungspositionen, Kostenstellenplaene, Verteilungsschluessel, Maßeinheit-Spalte,
   Smart Buttons und alle Zusatzfilter.

4. **Technisch bedingte Abweichungen klar dokumentiert.**
   Siehe Punkt 3 dieser Liste; zusaetzlich in `docs/o11-o18-abrechnung-abnahmeliste.md`
   mit Migrationsregel je Punkt.

## 3. Technisch bedingte Abweichungen (Kurzfassung)

| Odoo 11 | Odoo 18 | Migrationsregel |
|---|---|---|
| Spalte "Pos" | Spalte "Line NO." (Bezeichnung der Griffspalte) | Zeilennummer wird neu vergeben; keine Datenuebernahme |
| Spalte "Beschreibung" | im Produktfeld enthalten (Produkt, Abschnitt, Notiz, Beschreibung in einer Spalte) | `account.invoice.line.name` -> `account.move.line.name`, 1:1 |
| Spalte "Sektion" | Zeilentyp "Abschnitt" (`display_type`) | 2 von 10.057 Zeilen werden Abschnittszeilen; keine Sektionsstammdaten |
| Spalte "Kostenstellen-Tags" | kein Gegenstueck (Odoo 18 kennt keine Kostenstellen-Tags) | 0 von 10.057 Zeilen betroffen, nichts zu uebernehmen |
| Spalte "Total" | Spalte "Total" nur bei Steuer-inklusive Preisangabe | `price_total` -> `price_total`, 1:1 |
| Smart Buttons der Zahlung | dynamische Bezeichnungen mit Anzahl | Abstimmung ueber `reconciled_invoice_ids`, keine Bezeichnungsmigration |
| Statuswerte der Belege | Entwurf/Gebucht/Abgebrochen bzw. Zahlung/In Bearbeitung/Bezahlt | Zustandsmapping bei der Migration |

## 4. Was bis zu Ihrer Kontrolle nicht mehr passiert

- Keine weiteren Ansichts- oder Feldumbauten in Abrechnung.
- Kein neues Modul, keine Aenderung an bestehenden Modulen ausserhalb von Abrechnung.
- Odoo 11 bleibt ausschliesslich lesend, keine Datenmigration.
- Nach Ihrer Kontrolle: Rueckmeldung aufnehmen, gefundene Punkte gezielt nachziehen, danach
  endgueltige Markierung "funktional vollstaendig und migrationsvorbereitet".
