# Odoo 11 Prod → Odoo 18: Layoutvergleich der geöffneten Kontaktansicht

**Session 95, 15.09.2026** · Referenz: Odoo 11 Prod (`portal.it-kommunal.at`, DB `ITK_V1_a`, Kontakt 5792
„der Landeshauptstadt Freistadt Eisenstadt") · Vergleich: Odoo 18 Kontakt 69 (gleicher Name).

## Warum dieser Vergleich
Die technische Prüfung (Felder in der Arch vorhanden) hat nicht gereicht: Anna hat im Browser geprüft und
festgestellt, dass die Ansicht praktisch unverändert aussah. **Regel ab jetzt: „vorhanden" ≠ „erledigt".**
Für jeden Punkt ist zusätzlich zu prüfen: **sichtbar? richtige Position? gleiche fachliche Funktion? gleiche Bedienlogik?**

## Vorgehen (echter Browser, keine XML-Simulation)
`scripts/browser_form_layout.py` rendert die Detailansicht in Chromium (Playwright, installiertes Chrome,
eigenes Temp-Profil), meldet sich mit den hinterlegten Zugangsdaten an und liest **sichtbare** Feldbezeichnungen
mit CSS-Position, Gruppenüberschriften, Notebook-Tabs und Smart Buttons aus; dazu Screenshots und JSON.

```
uv run --with playwright python scripts/browser_form_layout.py --instanz prod --url https://portal.it-kommunal.at --partner 5792 --out <pfad>
uv run --with playwright python scripts/browser_form_layout.py --instanz lokal --partner 69 --out <pfad>
uv run --with playwright python scripts/browser_form_layout.py --instanz vm --url https://k001959vsx.ipax.at --partner 69 --out <pfad>
```

## Befund 1: Tabs

| | Reihenfolge im Browser |
|---|---|
| Odoo 11 Prod | Kontakte & Adressen · Interne Notizen · Verkauf & Einkauf · Abrechnung · Abrechnung · Gemeinde-Information · Support Ticket |
| Odoo 18 **vorher** | Kontakte & Adressen · Verkauf & Einkauf · Abrechnung · Interne Notizen · Gemeinde-Information · Support Ticket |
| Odoo 18 **nachher** (lokal = VM) | Kontakte & Adressen · Interne Notizen · Verkauf & Einkauf · Abrechnung · Gemeinde-Information · Support Ticket |

→ Umgesetzt: `page name="internal_notes"` per `position="move"` an die zweite Stelle (Odoo-11-Reihenfolge).
→ Der **zweite „Abrechnung"-Tab** aus Odoo 11 ist in Odoo 18 die Seite `accounting_disabled` („Invoicing"):
  Odoo 18 zeigt sie nur Benutzern **ohne** Buchhaltungsrechte. Fachlich entspricht sie der Odoo-11-Dublette;
  die Odoo-18-Lösung ist bewusst beibehalten (keine Dublette nachgebaut).

## Befund 2: Smart Buttons oben

| | Reihenfolge im Browser |
|---|---|
| Odoo 11 Prod | 1 Verkaufschancen · 9 Verkauf · 0 Meetings · 0 Kostenstellenkonten · Aktiv · Unveröffentlicht Auf Website · 5 Abonnements · Mehr |
| Odoo 18 **vorher** | 0 Meetings · 0 Verkaufschancen · 0 Verkauf · 0,00 € Fakturiert · 0 Aufgaben · 0 Einkäufe · Karte · Mehr |
| Odoo 18 **nachher** | 0 Verkaufschancen · 0 Verkauf · 0 Meetings · 0,00 € Fakturiert · 0 Aufgaben · 0 Einkäufe · Karte · Mehr |

→ Umgesetzt: „Meetings" per `position="move"` hinter „Verkauf" verschoben (Odoo-11-Reihenfolge: Verkaufschancen,
  Verkauf, Meetings).
**Offen (KLÄRUNG NÖTIG):** „Kostenstellenkonten" (`contracts_count`) und „Website-Veröffentlichung" (`website_published`)
sowie der Archiv-Status-Button „Aktiv" existieren in Odoo 18 nicht als Smart Button — in Odoo 18 sind das
  (a) nicht migrierte Odoo-11-Module und (b) Standardbedienung über Zahnradmenü/Website-Toggle. „Abonnements" ist in
  Odoo 18 vorhanden, wird bei der Buttonanzahl aber in das Menü „Mehr" einsortiert.

## Befund 3: Kenndaten-Block

| Odoo 11 Prod | Odoo 18 vorher | Odoo 18 nachher (lokal = VM) |
|---|---|---|
| „GKZ" (`ref`) | „GKZ" (`ref`) | „GKZ" (`ref`) |
| „Verkäufer" (`user_id`) | „Verkäufer" (`user_id`) | „Verkäufer" (`user_id`) |
| „Multiplication Factor/Thsd" (`multi_factor`) | „Multiplication Factor/Thsd" (`multi_factor`) | „Multiplication Factor/Thsd" (`multi_factor`) |
| „Ist ein Lieferant" (`supplier`) | „Ist ein Lieferant" (`is_supplier`) | „zu Handen" (`attention_of`) |
| „Ist ein Kunde" (`customer`) | „Ist ein Kunde" (`is_customer`) | „Organisationsbezeichnung" (`community_salutation`) |
| „Organisationsbezeichnung" (`community_salutation`) | „zu Handen" (`attention_of`) | „Ist ein Lieferant" (`is_supplier`) |
| „Status" (`status_of_partner_id`) | „Status" (`status_of_partner_id`) | „Ist ein Kunde" (`is_customer`) |
| – | „Organisationsbezeichnung" (`community_salutation`) | „Status" (`status_of_partner_id`) |

→ Umgesetzt: `is_supplier` / `is_customer` in die **linke** Spalte (nach Multiplication Factor), „zu Handen" und
  „Organisationsbezeichnung" in die **rechte** Spalte (nach Verkäufer, vor Status) — damit die Spaltenzuordnung
  der Odoo-11-Ansicht entspricht. `is_supplier`/`is_customer` sind die Odoo-18-Entsprechung von `supplier`/`customer`
  (Odoo-18-Technik, gleiche Beschriftung „Ist ein Lieferant"/„Ist ein Kunde").
→ Hinweis Optik: Odoo 18 schreibt Gruppenüberschriften per CSS in Großbuchstaben („KENNDATEN") — reine Darstellung.
→ Hinweis Optik: das „?" hinter „Verkäufer" ist das Odoo-18-Hilfe-Symbol (`<sup>` mit Feld-Hilfetext), kein Fehler.

## Befund 4: Adressblock und Feldbezeichnungen
Sichtbar vorhanden und benannt wie in Odoo 11: Adresse (`street`), Straße 2 (`street2`), PLZ/Ort/Bundesland (`zip`,
`city`, `state_id`), Land (`country_id`), Telefon (`phone`), Mobil (`mobile`), E-Mail (`email`), Website (`website`),
Sprache (`lang`), Stichwörter (`category_id`), UID (`vat`).

**Offen (KLÄRUNG NÖTIG):** `vat` zeigt in Odoo 18 „USt" statt „UID" — das Label wird von Odoo 18 zur Renderzeit aus
den Basisdaten `res.country.vat_label` (Österreich = „USt") gesetzt (`FormatVATLabelMixin._get_view`), ein View-Label
kann das nicht übersteuern. Lösung wäre das Setzen von `res.country` (AT) `vat_label = "UID"` (Basisdaten-Änderung).

## Screenshots

`C:\Users\anna.maierhofer\Desktop\Odoo18-Layoutvergleich-Session95\`

1. `1_Odoo11_PROD_Referenz.png` — Odoo 11 Prod, Kontakt 5792
2. `2_Odoo18_VORHER_lokal.png` — Odoo 18 lokal, Zustand vor dieser Anpassung
3. `3_Odoo18_NACHHER_lokal.png` — Odoo 18 lokal, Zustand nach der Anpassung
4. `4_Odoo18_NACHHER_VM.png` — Odoo 18 Test-VM, gleicher Zustand

## Umgesetzt in dieser Session (Modul `itk_base_setup` 18.0.1.0.5)
- Tab-Reihenfolge wie Odoo 11 (Interne Notizen an zweiter Stelle)
- Kenndaten-Spalten wie Odoo 11 (links GKZ/Thsd/Lieferant/Kunde, rechts Verkäufer/zu Handen/Organisationsbezeichnung/Status)
- Smart-Button-Reihenfolge wie Odoo 11 (Verkaufschancen, Verkauf, Meetings)
- `multi_factor`-Label repo-durable gesetzt (lokal und VM zeigten unterschiedliche Beschriftungen)
- Werkzeug `scripts/browser_form_layout.py` (echter Browser-/Layoutvergleich)

**Verifiziert:** Browser-Render lokal und VM **identisch**, Tabs/Buttons/Kenndaten in Odoo-11-Reihenfolge. Keine Daten übernommen.
