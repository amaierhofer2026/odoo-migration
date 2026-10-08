# Kontenzuordnung 8400 / 3400 (Abrechnung): Belege, Entscheidung und offener Punkt

Stand: 08.10.2026 (Session 131). Quelle: Odoo 11 Produktion `portal.it-kommunal.at`, DB `ITK_V1_a`
(ausschliesslich lesend) gegen Odoo 18 Testinstanz `odoo18_test` (lokal) und VM `k001959vsx`.
Erhebungswerkzeuge (nur lesend): `scripts/erhebe_konterverwendung_8400_3400.py`,
`scripts/erhebe_konterverwendung_teil2.py`, `scripts/erhebe_konterverwendung_teil3.py`
(Rohdaten unter `Desktop/Odoo18-Abnahme-Session131/konten/`).

## 1. Ausgangslage in Odoo 11 (gemessen)

| Punkt | Wert |
|---|---|
| Konto 8400 | "Erloese 19% USt", Kontotyp **Erloese**, **10.040** Belegzeilen |
| Konto 3400 | "Wareneingang 19% Vorsteuer", Kontotyp **Aufwand**, **0** Belegzeilen |
| Steuern mit Verweis auf 8400 oder 3400 | **keine** (geprueft: `account_id`, `refund_account_id`, `cash_basis_account`, `cash_basis_base_account_id` - 0 Treffer) |
| Kontoart | beide ausschliesslich **globale Firmenvorgabe** der Produktkategorien |
| Belege dafuer | 8 `ir.property`-Eintraege zu `product.category`, **alle mit leerem `res_id`** (Firmenvorgabe, IT-Kommunal GmbH), **0 kategoriespezifisch** |
| Eigene Konten der Kategorien | keine: alle **30** Kategorien zeigen den Firmenvorgabewert (Ertrag 8400, Aufwand 3400) |
| Kontenrahmen gesamt | 1.286 Konten |
| Einkaufsbelege (`in_invoice`) | **0** - auf der Aufwandsseite wurde nie gebucht |
| Belegzeilen gesamt | 34.592 (davon 10.040 auf 8400) |

Bedeutung: **8400 ist produktiv im Einsatz** (Erloese aller Ausgangsrechnungen),
**3400 ist reine Konfiguration ohne einen einzigen Buchungssatz**.

## 2. Firmenvorgabe: Odoo 11 gegen Odoo 18 (Mechanik belegt)

| | Odoo 11 | Odoo 18 |
|---|---|---|
| Modell | `ir.property` | `ir.default` (`ir.property` existiert in Odoo 18 nicht mehr - Abfrage liefert 404) |
| Firmenweite Vorgabe | Eintrag mit leerem `res_id` | Eintrag ohne `user_id`/`condition`, mit `company_id` |
| Feld Ertragskonto | `property_account_income_categ_id` -> Konto 1161 = **8400** | `Ertragskonto (Produktkategorie)` -> Konto 152 = **4000** |
| Feld Aufwandskonto | `property_account_expense_categ_id` -> Konto 839 = **3400** | `Aufwandskonto (Produktkategorie)` -> Konto 159 = **5010** |
| Kategorien mit eigenem Konto | 0 | 0 |

Der Wert 4000 auf der Ertragsseite und 5010 auf der Aufwandsseite ist der **Standard des
Odoo-18-Kontenrahmens** (durch die Kontenrahmen-Einrichtung gesetzt), keine Zuordnung durch die
Migration. 5010 wird deshalb ausdruecklich **nicht** als Entsprechung zu 3400 gewertet.

## 3. Entschiedene Zuordnung: 8400 -> 4000

Entscheidung Anna, 08.10.2026: 8400 "Erloese 19% USt" wird auf **4000 "Brutto-Umsatzerloese im
Inland (20%)"** (Kontotyp `income`) gemappt - fuer die Belegzeilen und konsistent auch fuer die
globale Firmenvorgabe der Produktkategorien. **Nicht** pro Produktkategorie.

Belege fuer diese Zuordnung:

1. Das Mapping ist fuer die Belegzeilen bereits dokumentiert und umgesetzt
   (`docs/o11-o18-abrechnung-abschlusspruefung.md`, Abschnitt 3: 1201->2801, 1410->2000,
   1776->3500, 8400->4000; im Werkzeug `scripts/testmigration_abrechnung.py`: `KONTO_MAPPING`).
2. Kontoart stimmt ueberein: Odoo 11 "Erloese" -> Odoo 18 `income`.
3. Die Odoo-18-Firmenvorgabe des Ertragskontos zeigt bereits auf 4000 - die Entscheidung
   bestaetigt damit den vorhandenen Zielzustand, es wird kein Kontenstammdatum angelegt.
4. Verwendung: 8400 traegt in Odoo 11 alle Verkaufserloese; im Ziel tragen die migrierten
   Testbelege 4000 (39 Belegzeilen).

Umsetzung im Werkzeug (`scripts/testmigration_abrechnung.py`):

- neues, dokumentiertes Entscheidungsregister `ENTSCHEIDUNGEN_KONTEN` (Schluessel: Kontonummer),
- `konto_im_ziel()` liest zuerst dieses Register und prueft das Zielkonto ueber **Nummer UND
  Namen**; stimmt der Name nicht oder ist die Nummer nicht eindeutig, bricht der Lauf ab
  (keine stille Fehlzuordnung, kein Anlegen),
- neue Pruefung `pruefe_firmenvorgabe()`: liest die Firmenvorgabe (`ir.default`) im Ziel und
  haelt sie gegen die Entscheidung.

## 4. Entschiedene Zuordnung: 3400 -> 5010 (Entscheidung Anna, 08.10.2026)

3400 "Wareneingang 19% Vorsteuer" wird auf **5010 "Wareneinkauf 20%"** abgebildet - das ist die im
Ziel **bereits gesetzte globale Firmenvorgabe** des Aufwandskontos der Produktkategorien
(`ir.default`, firmenweit). Es wird **kein Konto angelegt**, **kein Mapping auf 5000 erzwungen** und
es werden **keine kategoriespezifischen Konten** erzeugt; die Kategorien erben die firmenweite
Vorgabe.

Begruendung der Entscheidung:

1. 3400 hatte in Odoo 11 **0 Belegzeilen** und diente ausschliesslich als globale Firmenvorgabe der
   Produktkategorien - es gibt keine historischen Buchungen, aus denen eine andere Zuordnung folgen
   wuerde.
2. 5010 ist fachlich **naeher an "Wareneingang/Wareneinkauf"** als 5000 "Wareneinsatz"
   (Einsatz = Materialverbrauch, weiter gefasst).
3. Es soll **kein neues Konto mit 19%-Bezeichnung** angelegt werden.
4. 5010 ist bereits die Odoo-18-Vorgabe; die Kategorien erben sie wie vorgesehen.

Damit ist die Abweichung zum Odoo-11-Namen (19% gegen 20%) bewusst und dokumentiert: sie folgt der
fachlichen Entscheidung, nicht einer automatischen Zuordnung ueber den Namen.

### 4.1 Verworfene Kandidaten (nicht zugeordnet, nichts angelegt)

Alle Kandidaten haben im Ziel 0 Belegzeilen; es gab damit keine Verwendungsevidenz.

| Nummer | Name | Kontotyp | Verwendung im Ziel | Bewertung |
|---|---|---|---|---|
| 5000 | Wareneinsatz | expense_direct_cost | 0 Belegzeilen | verworfen: Begriff weiter gefasst als "Wareneingang"; kein Mapping erzwungen |
| 5010 | Wareneinkauf 20% | expense_direct_cost | 0 Belegzeilen | **gewaehlt**: bestehende globale Aufwandsvorgabe, fachlich naechste Entsprechung |
| 5011 | Wareneinkauf 10% | expense_direct_cost | 0 Belegzeilen | verworfen: ermaessigter Satz, in Odoo 11 nicht vorhanden |
| 5050 | Wareneinkauf ig. Erwerb 20% | expense_direct_cost | 0 Belegzeilen | verworfen: innergemeinschaftlicher Erwerb, in Odoo 11 nicht vorhanden |
| 5051 | Wareneinkauf ig. Erwerb 10% | expense_direct_cost | 0 Belegzeilen | verworfen: dito |
| 5052 | Wareneinkauf ig. Erwerb 0% nach Art. 6 Abs. 2 | expense_direct_cost | 0 Belegzeilen | verworfen: dito |
| 5090 | Wareneinkauf 0% | expense_direct_cost | 0 Belegzeilen | verworfen: Nullsatz, in Odoo 11 nicht vorhanden |

### 4.2 Wirksamkeit

Da 3400 weder in Belegen noch in Steuern vorkommt, betrifft die Zuordnung **ausschliesslich die
Vorgabekonfiguration** der Produktkategorien, nicht die zu uebertragenden Daten (0 zu uebertragende
Belegzeilen). Die bestehende Odoo-18-Firmenvorgabe bleibt unveraendert - es wurde nichts
geschrieben, nur die Zuordnung dokumentiert und im Werkzeug hinterlegt.

## 5. Endgueltige Entscheidungen

| Odoo 11 | Odoo 18 | Art | Stand |
|---|---|---|---|
| 8400 "Erloese 19% USt" | 4000 "Brutto-Umsatzerloese im Inland (20%)" | Belegzeilen-Mapping und globale Firmenvorgabe | entschieden und umgesetzt |
| 3400 "Wareneingang 19% Vorsteuer" | 5010 "Wareneinkauf 20%" | globale Firmenvorgabe (bestehende Odoo-18-Vorgabe beibehalten) | entschieden |
| - | keine kategoriespezifischen Konten | - | entschieden |
| - | keine neuen Konten | - | entschieden |

Beide Zuordnungen sind im Werkzeug als Register `ENTSCHEIDUNGEN_KONTEN` hinterlegt
(`scripts/testmigration_abrechnung.py`) und werden dort ueber Kontonummer **und** Namen geprueft;
weicht der Name ab oder ist die Nummer nicht eindeutig, bricht der Lauf ab.

## 6. Was bewusst NICHT gemacht wurde

- Keine Konten angelegt, umbenannt oder geloescht (Konten sind Stammdaten).
- Keine Zuordnung fuer 3400 geraten (kein 5000, kein 5010).
- Keine kategoriespezifischen Konten gesetzt: die Odoo-11-Grundlage ist die **firmenweite
  Vorgabe**; die Entscheidung lautet ausdruecklich "nicht pro Produktkategorie".
- Kein Ausblenden oder Umbenennen von Konten, um die Abweichung optisch zu beseitigen.

## 7. Bezug

- `docs/o11-o18-abrechnung-abschlusspruefung.md` (Feldmapping Belegzeilen, Abschnitt 3)
- `docs/o11-o18-produktkategorien-mapping.md` (Kategorien, Abschnitt 5: Blocker)
- `docs/o11-o18-abrechnung-abschlussmatrix.md` (Abschnitt 13.5, offene Punkte)
- `scripts/testmigration_abrechnung.py` (`KONTO_MAPPING`, `ENTSCHEIDUNGEN_KONTEN`,
  `konto_im_ziel`, `pruefe_firmenvorgabe`)
