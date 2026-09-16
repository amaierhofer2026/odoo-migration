# Odoo 11 Prod → Odoo 18: Strukturvergleich Kontaktformular → Tab „Interne Notizen“

**Session 102, 15.09.2026** · Referenz: Odoo 11 Prod (`portal.it-kommunal.at`, DB `ITK_V1_a`) · Vergleich: Odoo 18 lokal + VM.

## 1. Ausgangslage (Annas Beobachtung)

In Odoo 11 sind im Tab „Interne Notizen“ fünf Abschnitte sichtbar: Interner Hinweis,
Warnung beim Kommissionieren, Warnung zu Rechnung, Alarmierung bei Auftrag, Warnung beim Einkaufsauftrag.
In Odoo 18 waren nur drei sichtbar (Interne Notizen, Warnung auf Verkaufsauftrag, Warnung zu Rechnung).

## 2. Feldvergleich

| Odoo 11 (Feld / Titel) | Odoo 18 | Befund |
|---|---|---|
| `comment` / „Interner Hinweis…“ | `comment` vorhanden (jetzt `html` statt `text`) | vorhanden; Odoo-18-Technik (HTML) bleibt, Platzhalter auf Odoo-11-Wortlaut gesetzt |
| `picking_warn` / „Warnung beim Kommissionieren“ | **Feld existiert in Odoo 18 nicht mehr** | kein Nachbau — Odoo hat die Partner-Warnung für die Kommissionierung abgeschafft |
| `invoice_warn` / „Warnung zu Rechnung“ | `invoice_warn` + `invoice_warn_msg` | vorhanden, Titel identisch |
| `sale_warn` / „Alarmierung bei Auftrag“ | `sale_warn` + `sale_warn_msg` | vorhanden, Titel hieß „Warnung auf Verkaufsauftrag“ → angepasst |
| `purchase_warn` / „Warnung beim Einkaufsauftrag“ | `purchase_warn` + `purchase_warn_msg` vorhanden, aber **unsichtbar** | Ursache: Abschnitt hängt an `purchase.group_warning_purchase` → aktiviert |

**Auswahlwerte** aller Warnfelder sind in beiden Systemen identisch: Keine Nachricht / Warnung / Blockierende Meldung.

## 3. Ursache der fehlenden Einkaufs-Warnung
Der Abschnitt steckt im Modul `purchase` in der Ansicht `res.partner.view.purchase.buttons` innerhalb der Gruppe
`purchase.group_warning_purchase` — in Odoo 18 der Einstellungsschalter **Warnungen** (Einkauf). Annas Benutzer hatte diese
Gruppe nicht, deshalb wurde der Abschnitt beim Rendern entfernt. Die Felder selbst sind vorhanden und tragen keine
Feldgruppen-Beschränkung (`groups = keine`). **Lösung: die Odoo-18-Standardeinstellung aktivieren** (kein Nachbau).

## 4. Umgesetzt (Modul `itk_base_setup` 18.0.1.2.0)
- Abschnittstitel „Alarmierung bei Auftrag“ (Odoo 11) statt „Warnung auf Verkaufsauftrag“
- Abschnittstitel „Warnung beim Einkaufsauftrag“ (Odoo 11) statt „Warnung auf Bestellung“
- Platzhalter des Notizfelds „Interner Hinweis ...“ (Odoo 11) statt „Interne Notizen ...“
- Einkaufs-Warnung sichtbar über die Odoo-18-Einstellung `purchase.group_warning_purchase` (auf lokal und VM aktiviert)
- Robustheit geprüft: das Upgrade läuft auch mit **ausgeschalteter** Einstellung fehlerfrei (die XPaths greifen unabhängig).

## 5. Verifikation (VM = Abnahmeumgebung)
- Modul `itk_base_setup` **18.0.1.2.0** auf der VM installiert (Upgrade über HTTPS-RPC).
- Gerenderter Arch auf der VM zeigt: Platzhalter „Interner Hinweis ...“, Abschnitte „Alarmierung bei Auftrag“
  „Warnung zu Rechnung“, „Warnung beim Einkaufsauftrag“ mit `sale_warn`, `invoice_warn`, `purchase_warn`.
- Echter Browser gegen https://k001959vsx.ipax.at, Kontakt 69, Tab „Interne Notizen“:
  Abschnitte „ALARMIERUNG BEI AUFTRAG“, „WARNUNG ZU RECHNUNG“, „WARNUNG BEIM EINKAUFSAUFTRAG“ sichtbar,
  sichtbare Felder `comment`, `sale_warn`, `invoice_warn`, `purchase_warn`, jeweils mit den drei Auswahlwerten.
  Screenshot: `Desktop\Odoo18-Layoutvergleich-Session95\13_VM_InterneNotizen.png`.
- Kontrollzahlen unverändert (70 Kontakte); **keine Datensätze angelegt/geändert/gelöscht**.

## 6. Analyse „Warnung beim Kommissionieren“ (picking_warn) in Odoo 11 Prod - Session 103

Read-only-Auswertung gegen `portal.it-kommunal.at` (DB `ITK_V1_a`):

| Auswertung | Ergebnis |
|---|---|
| Kontakte gesamt | 5.842 |
| `picking_warn = 'no-message'` | **5.842** (alle) |
| `picking_warn = 'warning'` | 0 |
| `picking_warn = 'block'` | 0 |
| `picking_warn` leer/unbestimmt | 0 |
| `picking_warn_msg` mit individuellem Text | **0** |
| Kontakte mit `sale_warn` aktiv | 0 |
| Kontakte mit `invoice_warn` aktiv | 0 |
| Kontakte mit `purchase_warn` aktiv | 0 |
| `stock.picking.note` gefüllt | 0 |

**Ergebnis: Das Feld wird in Odoo 11 Prod von keinem einzigen Datensatz verwendet** (kein Wert gesetzt, kein Warntext).
Das gilt auch für die übrigen Partner-Warnfelder (Verkauf, Rechnung, Einkauf): strukturell vorhanden, Datenbestand 0.

**Vergleich mit den Odoo-18-Warnmechanismen (Feldinventar):** Odoo 18 hat auf dem Kontakt `sale_warn`, `invoice_warn`,
`purchase_warn` (Wortlaute/Werte identisch zu Odoo 11) sowie zusätzlich **linienbezogene Warnungen am Produkt**
(`product.template.sale_line_warn`, `purchase_line_warn`). Ein partnerbezogenes Kommissionier-/Lieferwarnfeld gibt es nicht mehr.

**Empfehlung (Entscheidung bei Anna):**
1. **Kein eigenes Feld nötig** — es existieren keine Daten, die migriert werden müssten (0 von 5.842).
2. Ein Mapping auf bestehende Odoo-18-Funktionen ist möglich, aber **nicht erforderlich**, weil keine Werte zu übertragen sind.
3. Falls ITK künftig eine Liefer-/Kommissionierwarnung benötigt, ist der Odoo-18-gerechte Weg ein **neues Feld an der Position**
   (z. B. Linienwarnung am Produkt) — kein Nachbau des Odoo-11-Partnerfelds.

## 7. Einkaufs-Warnungen bleiben aktiv

Auf Anweisung von Anna bleibt die Odoo-18-Einstellung **Warnungen** (Einkauf, `purchase.group_warning_purchase`) auf lokal und
VM **aktiviert**, damit der Abschnitt „Warnung beim Einkaufsauftrag“ sichtbar und für die spätere Migration verfügbar ist.
