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

## 6. KLÄRUNG NÖTIG
- **Warnung beim Kommissionieren** (`picking_warn`): in Odoo 18 ersatzlos entfallen. Die fachliche Funktion wird heute über die
  Verkaufs- und Rechnungswarnung abgedeckt. Falls ITK eine eigene Lieferwarnung braucht, wäre das ein **neues, eigenes Feld**
  (bewusst nicht gebaut — veraltete Odoo-11-Technik wird nicht nachgebaut).
- Die Einstellung „Warnungen“ im Einkauf ist nun aktiv; sie wirkt instanzweit (auch in Einkaufsbelegen). Falls das nicht gewünscht
  ist, lässt sie sich mit einem Klick wieder deaktivieren — der Abschnitt verschwindet dann erneut.
