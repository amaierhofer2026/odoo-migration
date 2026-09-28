# Odoo 11 -> Odoo 18: Bereich Verkauf, Teil 3, Schritt 3 (Statuswechsel)

Stand: 24.09.2026, Session 121. Odoo 11 Prod (`portal.it-kommunal.at`, DB `ITK_V1_a`) wurde
ausschliesslich lesend gelesen (RPC). Gepruefte Odoo-18-Instanzen: lokal (`odoo18_test`) und VM
(`k001959vsx.ipax.at`). Analysewerkzeug: `scripts/analyse_verkauf_teil3_status.py`,
Auswertung der Sichtbarkeitsbedingungen: `scripts/sichtbarkeit_bedingungen.py`.

## 1. Statuswerte

| System | Auswahlwerte des Feldes `state` | Statusleiste `statusbar_visible` |
|---|---|---|
| Odoo 11 | `draft`, `sent`, `sale`, `done`, `cancel` (5) | `draft,sent,sale` |
| Odoo 18 | `draft`, `sent`, `sale`, `cancel` (4) | `draft,sent,sale` |

Der Zustand `sale` wird in Odoo 18 zusaetzlich durch das Ja/Nein-Feld `locked` getrennt
(gesperrt/entsperrt). Odoo 11 kannte diese Trennung nicht; dort war `done` der gesperrte Auftrag.
Odoo 11 hat kein Feld `locked`, Odoo 18 keinen Zustand `done`.

Bestand (Odoo 11 Prod, lesend gemessen am 24.09.2026):

```
draft   5      sent  0      sale  2311      done  0      cancel  147      gesamt 2463
```

`done` und `sent` sind in Odoo 11 nie benutzt worden. Der Bestand waechst, weil das
Produktivsystem laufend Auftraege erhaelt (in Session 121 von 2461 auf 2463 gemessen).

Bestand Odoo 18: lokal 18 Auftraege (`draft` 1, `sent` 2, `sale` 10, `cancel` 5),
VM 20 Auftraege (`draft` 2, `sent` 2, `sale` 11, `cancel` 5) - Testdaten, keine Migration.

## 2. Anzeige der Statusleiste im Formular

Beide Systeme zeigen im Kopf genau drei Stufen als Klickleiste: **Angebot**, **Angebot gesendet**,
**Verkaufsauftrag**. Die Stufen **Storniert** und (Odoo 11) **Erledigt** erscheinen als zusaetzliche
Stufe, sobald der Datensatz in diesem Zustand ist.

## 3. Uebergaenge und zugehoerige Buttons

Ausgewertet aus dem Formular-Arch (`sale.order`), Bedingung je Zustand ausgewertet mit
`scripts/sichtbarkeit_bedingungen.py`. "Sichtbar" heisst: Button ist im jeweiligen Zustand
eingeblendet.

### Odoo 11

| von | Button | Methode | nach |
|---|---|---|---|
| Angebot | Auftrag bestätigen | `action_confirm` | Verkaufsauftrag |
| Angebot | Per E-Mail versenden | `action_quotation_send` | Angebot gesendet (nach dem Versand) |
| Angebot | Drucken | `print_quotation` | kein Wechsel |
| Angebot | Abbrechen | `action_cancel` | Storniert |
| Angebot gesendet | Auftrag bestätigen | `action_confirm` | Verkaufsauftrag |
| Angebot gesendet | Drucken | `print_quotation` | kein Wechsel |
| Angebot gesendet | Abbrechen | `action_cancel` | Storniert |
| Verkaufsauftrag | Sperre | `action_done` | Erledigt (gesperrt) |
| Verkaufsauftrag | Abbrechen | `action_cancel` | Storniert |
| Verkaufsauftrag | Drucken | `print_quotation` | kein Wechsel |
| Erledigt | Entsperren | `action_unlock` | Verkaufsauftrag |
| Storniert | Setze auf Angebot | `action_draft` | Angebot |

Odoo 11 storniert **ohne Rueckfrage** (kein Dialog). `action_confirm` ist zweimal im Kopf
definiert: einmal sichtbar nur im Status Angebot gesendet, einmal nur im Status Angebot.

### Odoo 18

| von | Button | Methode | nach |
|---|---|---|---|
| Angebot | Bestätigen | `action_confirm` | Verkaufsauftrag (automatisch gesperrt) |
| Angebot | Per E-Mail versenden | `action_quotation_send` | Angebot gesendet (nach dem Versand) |
| Angebot | Stornieren | `action_cancel` | Storniert (ueber Dialog) |
| Angebot gesendet | Bestätigen | `action_confirm` | Verkaufsauftrag (automatisch gesperrt) |
| Angebot gesendet | Stornieren | `action_cancel` | Storniert (ueber Dialog) |
| Verkaufsauftrag (entsperrt) | Sperren | `action_lock` | gesperrt |
| Verkaufsauftrag (entsperrt) | Stornieren | `action_cancel` | Storniert (ueber Dialog) |
| Verkaufsauftrag (gesperrt) | Entsperren | `action_unlock` | Verkaufsauftrag (entsperrt) |
| Storniert | Auf Angebot setzen | `action_draft` | Angebot |

Zusaetzlich und ohne Statuswechsel: Vorschau (`action_preview_sale_order`), Rechnung erstellen
(`428`, nur in bestimmten Rechnungsstellungen sichtbar), Pro-forma-Rechnung senden,
Transaktion erfassen/stornieren (nur bei Transaktionen), Drucken (Zahnradmenue).

## 4. Unterschiede Odoo 11 gegen Odoo 18

1. **Gesperrt ist kein Status mehr.** Odoo 11: Zustand `done`; Odoo 18: Zustand `sale` plus
   Schalter `locked`. Die Methoden heissen jetzt `action_lock`/`action_unlock`.
2. **Storno nur mit Rueckfrage.** Odoo 18 oeffnet den Assistenten `sale.order.cancel`
   ("Verkaufsauftrag stornieren") mit den Knoepfen "Senden und stornieren"
   (`action_send_mail_and_cancel`, verschickt eine Storno-E-Mail), "Stornieren" (`action_cancel`)
   und "Verwerfen". Odoo 11 storniert sofort ohne Dialog.
3. **Ein gesperrter Auftrag laesst sich nicht stornieren.** In Odoo 18 ist der Storno-Button
   solange ausgeblendet, bis der Auftrag entsperrt ist (`invisible="... or locked"`). In Odoo 11
   war "Abbrechen" im Status Verkaufsauftrag immer sichtbar; die Sperre war ein eigener Zustand
   `done`, in dem es keinen Abbrechen-Button gab (dort nur "Entsperren").
4. **Automatische Sperre.** In der Odoo-18-Datenbank ist "Bestellungen automatisch sperren" aktiv:
   Das Bestaetigen fuehrt direkt zu `sale` + `locked=True` (im Klicktest bestaetigt). In Odoo 11
   war ein bestaetigter Auftrag zunaechst bearbeitbar.
5. **Statusleiste und Zustandsnamen** sind ansonsten gleich; die sichtbaren Stufen sind identisch.
6. `sent` wird in beiden Systemen nicht durch einen Kopf-Button, sondern durch den Versand des
   Angebots gesetzt (Kontextmerkmal `mark_so_as_sent` des E-Mail-Assistenten).

## 5. Klicktests im echten Browser

Werkzeug: `scripts/browser_verkauf_statuswechsel_klicktest.py` (legt einen Testauftrag an,
durchlaeuft alle Uebergaenge, prueft nach jedem Klick den Zustand per RPC, loescht den Auftrag
wieder).

```
lokal  35 OK / 0 FEHL   JavaScript-Fehler 0   RPC-Fehler 0
VM     35 OK / 0 FEHL   JavaScript-Fehler 0   RPC-Fehler 0
Testdaten: lokal wieder 18 Auftraege, VM wieder 20 Auftraege (Ausgangsstand)
Screenshots: Desktop\Odoo18-Abnahme-Session121\10_Status_draft_*.png bis 15_Status_sent_*.png
```

Geprueft und bestaetigt:

```
Angebot          aktive Stufe "Angebot"; sichtbar Bestätigen, Stornieren; nicht sichtbar
                 Sperren, Entsperren, Auf Angebot setzen
Angebot -> sale  Klick Bestätigen -> Zustand sale + locked=True; Bestätigen weg, Entsperren da,
                 Stornieren ebenfalls weg (gesperrter Auftrag)
sale entsperren  Klick Entsperren -> locked=False, jetzt Sperren und Stornieren sichtbar
sale sperren     Klick Sperren -> locked=True, wieder Entsperren sichtbar
sale -> cancel   Klick Stornieren -> Dialog "Verkaufsauftrag stornieren" mit
                 name=action_cancel; Klick Stornieren -> Zustand cancel; nur noch
                 "Auf Angebot setzen" sichtbar
cancel -> draft  Klick Auf Angebot setzen -> Zustand draft, Bestätigen wieder sichtbar
sent             Zustand "Angebot gesendet" per RPC gesetzt (echter Versand wuerde Post
                 verschicken): Bestätigen und Stornieren sichtbar, Auf Angebot setzen nicht
sent -> sale     Klick Bestätigen -> Zustand sale + locked=True
```

Hinweis fuer die Bedienung: Beim Klick auf "Stornieren" oeffnet Odoo 18 neben dem Storno-Dialog
zusaetzlich einen Bearbeitungsdialog des Kundenkontakts (Zustand des Browsers im Test). Der
Storno-Dialog liegt darunter und funktioniert unabhaengig; im Klicktest wird gezielt der Knopf
`name=action_cancel` des Storno-Dialogs verwendet.

## 6. Mapping fuer die spaetere Datenmigration

| Odoo 11 `state` | Anzahl | Odoo 18 Ziel | Bemerkung |
|---|---|---|---|
| `draft` | 5 | `state=draft`, `locked=False` | 1:1 |
| `sent` | 0 | `state=sent`, `locked=False` | 1:1, kein Datensatz vorhanden |
| `sale` | 2311 | `state=sale` | Sperre muss ausdruecklich gesetzt werden |
| `done` | 0 | `state=sale`, `locked=True` | Odoo-18-Entsprechung der alten Sperre, kein Datensatz |
| `cancel` | 147 | `state=cancel`, `locked=False` | 1:1 |

Praktischer Hinweis: Ein direktes Schreiben von `state=sale` (Import/RPC) loest `action_confirm`
**nicht** aus, deshalb greift auch die automatische Sperre nicht. `locked` muss beim Import also
ausdruecklich mitgeschrieben werden.

**ENTSCHIEDEN (Anna, 28.09.2026): nur dokumentieren.** Bestaetigte Verkaufsauftraege waren in
Odoo 11 bearbeitbar, Odoo 18 verwendet zusaetzlich das Feld `locked`. Es wird derzeit keine
Importregel auf Produktivdaten angewendet; die 2311 Auftraege werden nicht uebernommen und nicht
veraendert. Der Abschnitt `statuswechsel` in `migration/verkauf_migrationsregeln.json` ist reine
Vorbereitung.

## 7. Nachweise

```
scripts/analyse_verkauf_teil3_status.py           Statuswerte, Bestand, Buttons je Zustand
scripts/sichtbarkeit_bedingungen.py               Auswerter fuer attrs/states (O11) und invisible (O18)
scripts/browser_verkauf_statuswechsel_klicktest.py  Klicktest lokal und VM je 35 OK / 0 FEHL
scripts/verify_s121_verkauf_teil3_status.py       Prueflauf Odoo 11 (lesend) + lokal + VM
docs/_verkauf_teil3_status.json                   Rohdaten (gitignoriert)
```

**STATUS: TEIL 3, SCHRITT 3 - Statuswechsel verglichen und auf der VM mit echten Klicks
abgenommen (lokal 35 OK, VM 35 OK, je 0 FEHL).** Offen ist nur die fachliche Entscheidung zur
Sperre migrierter Auftraege. Filter, Gruppierungen, Suche und Berichte sind nicht Teil dieses
Schrittes.
