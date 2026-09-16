# Odoo 11 Prod → Odoo 18: Strukturvergleich Kontakte → Firmen/Personen-Logik und Ansprechpartner

**Session 100, 15.09.2026** · Referenz: Odoo 11 Prod (`portal.it-kommunal.at`, DB `ITK_V1_a`) · Vergleich: Odoo 18 lokal + VM.
Vergleichspaar: Breitenbrunn am Neusiedler See (O11 id 5794 ↔ O18 id 72, je 3 Kind-Datensätze).

## 1. Datengrundlage (read-only)

| Größe | Odoo 11 Prod | Odoo 18 (Test) |
|---|---|---|
| Unternehmen (`is_company = True`) | 2.380 | 12 |
| Personen | 3.461 | 58 |
| Kontakte mit `parent_id` (Ansprechpartner/Adressen bei Organisation) | 3.355 | 5 |
| Firmen mit `child_ids` | 1.951 | 3 |
| Adresstyp `contact` | 5.363 | 67 |
| Adresstyp `invoice` | 468 | 1 |
| Adresstyp `delivery` / `other` / `private` | 0 / 0 / 0 | 1 / 0 / – |

Die Ansprechpartner-/Adressstruktur ist im Produktivsystem also **zentral** (3.355 Kind-Datensätze).

## 2. Feld- und Funktionsvergleich

| Element | Odoo 11 | Odoo 18 | Bewertung |
|---|---|---|---|
| Firmen/Personen-Umschaltung | `company_type` als Radio (nur im Bearbeiten-Modus) | `company_type` als Radio | gleich ✓ |
| Kennzeichen | `is_company` (Boolesch) | `is_company` (Boolesch) | gleich ✓ |
| „Ansprechpartner bei“ | `parent_id`, Domain nur Unternehmen, Label „Verbundenes Unternehmen“ | `parent_id`, gleiche Domain, Widget `res_partner_many2one`, Label „Zugehöriges Unternehmen“ | Wortlaut (KLÄRUNG) |
| Kontakte/Adressen beim Kontakt | `child_ids` (Kanban, Kontext setzt Adressfelder des Unternehmens vor) | `child_ids` (Kanban, gleicher Kontext + `default_user_id`) | gleich ✓ |
| **Neuer Kind-Datensatz** | Adresstyp **`contact`** (Kontakt) | Adresstyp **`other`** (Andere Adresse) | **abweichend → angepasst** |
| Karten im Tab „Kontakte & Adressen“ | Name, Funktion, E-Mail, PLZ/Ort, Bundesland, Land, Telefon, Mobil | dieselben Felder | gleich ✓ |
| Adresstyp-Feld (`type`) | im Hauptformular ausgeblendet, Pflege über Kind-Datensätze | im Adressformular als Radio sichtbar | Odoo 18 besser ✓ |
| Adresstyp-Werte | Kontakt, Rechnungsadresse:, Zustellungsadresse, Andere Adresse, **Privatadresse**, Administration, Technik | Kontakt, Rechnungsadresse, Lieferadresse, Andere Adresse, Administration, Technik (**ohne** Privatadresse) | siehe 4. |
| Feldlabel `function` | „Job Position“ (englisch) | „Stelle“ | Odoo 18 besser ✓ |

## 3. Umgesetzt (Modul `itk_base_setup` 18.0.1.1.0)

**Neue Ansprechpartner/Adressen werden wieder als Kontakt angelegt.** Odoo 18 setzt im Kontext des Feldes `child_ids`
`default_type: 'other'` — ein neu angelegter Ansprechpartner wurde damit zur „Andere Adresse“. Odoo 11 setzt keinen
Adresstyp im Kontext, der Feldstandard `contact` greift. Der Kontext ist in unserer erbenden View entsprechend angepasst
(die übrigen Vorgaben — Adressfelder des Unternehmens, Sprache, Verkäufer — bleiben erhalten).

**Nachweis:** gerenderter `child_ids`-Kontext ohne `default_type`; `res.partner.default_get(['type'])` mit dem Tab-Kontext
liefert `contact` (vorher `other`) — lokal und auf der VM identisch.

## 4. Weitere Befunde

**Adresstyp „Privatadresse“:** Odoo 11 führt `private` als Auswahlwert, **verwendet ihn aber in keinem einzigen Datensatz**
(0 von 5.831). Odoo 18 hat den Wert aus der Auswahl entfernt und bildet Privatadressen über einen eigenen Datensatztyp ab.
→ Für ITK **keine Migrationswirkung**; ein Nachbau ist nicht erforderlich.

**Wortlaute (KLÄRUNG NÖTIG, nicht geändert):**
- „Adressart“ (O11) vs. „Adresstyp“ (O18) — Feldbezeichnung `type`
- „Verbundenes Unternehmen“ (O11) vs. „Zugehöriges Unternehmen“ (O18) — `parent_id`
- „Zustellungsadresse“ (O11) vs. „Lieferadresse“ (O18) — Auswahlwert `delivery` (Odoo-18-Standarddeutsch)
- „Rechnungsadresse:“ (O11, mit Doppelpunkt) vs. „Rechnungsadresse“ (O18) — Odoo 18 ist hier sauberer

**Beibehalten (Odoo-18-Technik, gleiche fachliche Funktion):** Radio-Adresstyp im Adressformular, `res_partner_many2one`-Widget
für `parent_id`, „Stelle“ statt des englischen „Job Position“, zusätzlicher „Hinzufügen“-Button im Tab.

## 5. Verifikation (VM = Abnahmeumgebung)

- `itk_base_setup` **18.0.1.1.0** auf der VM installiert (Upgrade in `odoo18_test` geladen).
- RPC gegen die VM: `child_ids`-Kontext ohne `default_type`, `default_get` → `type = contact`.
- Echter Browser gegen https://k001959vsx.ipax.at: Tab „Kontakte & Adressen“ von Kontakt 72 gerendert — Karten
  (Name, Funktion, E-Mail, PLZ/Ort, Bundesland, Land, Telefon) und „Hinzufügen“-Button wie erwartet.
  Screenshot: `Desktop\Odoo18-Layoutvergleich-Session95\12_VM_Ansprechpartner_oben.png` (und `_tab.png`).
- Kontrollzahlen unverändert (70 Kontakte, 5 mit `parent_id`); **keine Datensätze angelegt, geändert oder gelöscht**.

## 6. Nachtrag Session 101: Adressblock und Adresstypen — Entscheidungen (migrationsbereit abgeschlossen)

**Annas Entscheidung (15.09.2026):** „Der Vergleich der Adressmaske passt für mich funktional. Bitte hier keinen
Odoo-11-Nachbau durchführen.“

| Offener Punkt | Entscheidung | Umsetzung |
|---|---|---|
| „Zustellungsadresse“ (O11) vs. „Lieferadresse“ (O18) | fachlich **gleichwertig** — keine strukturelle Änderung nötig | **keine** — Odoo-18-Standardwortlaut bleibt |
| Adresstyp „Privatadresse“ (O11) | **nicht nachbauen**: in Odoo 11 von 0 Datensätzen genutzt; Odoo 18 hat eine eigene, moderne Logik | **keine** |
| „Adressart“ (O11) vs. „Adresstyp“ (O18) | funktional identisch, keine Änderung gewünscht | **keine** |
| „Verbundenes Unternehmen“ (O11) vs. „Zugehöriges Unternehmen“ (O18) | funktional identisch, keine Änderung gewünscht | **keine** |
| übrige Adresstypen und Adressfelder | funktional vorhanden | **keine** |

**Status: MIGRATIONSBEREIT.** Alle Punkte des Adressblocks sind entschieden; es sind dafür **keine Code-/Strukturänderungen**
erforderlich. Die einzige umgesetzte Anpassung in diesem Bereich bleibt der `default_type`-Fix aus Session 100
(neue Ansprechpartner werden als Kontakt angelegt).
