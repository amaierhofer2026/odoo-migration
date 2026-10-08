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

## 4. Offener Punkt: 3400 "Wareneingang 19% Vorsteuer"

**Keine eindeutige Entsprechung nachweisbar - deshalb bleibt der Punkt BLOCKER.** Es wird nichts
zugeordnet und nichts angelegt.

Kandidaten im Odoo-18-Kontenrahmen (alle Kontotyp `expense_direct_cost`, Gruppe `expense`):

| Nummer | Name | Belegzeilen im Ziel | Bewertung |
|---|---|---|---|
| 5000 | Wareneinsatz | 0 | fachlich "Einsatz" (Materialverbrauch), nicht "Wareneingang" - moegliche Entsprechung, aber Begriff weiter gefasst |
| 5010 | Wareneinkauf 20% | 0 | entspricht dem Satz des Zielkontenrahmens; Odoo-11-Konto nennt 19% (deutscher Satz), oesterreichischer Normalsatz ist 20% - Satzanalogie, nicht belegt |
| 5011 | Wareneinkauf 10% | 0 | ermaessigter Satz - in Odoo 11 nicht vorhanden |
| 5050 | Wareneinkauf ig. Erwerb 20% | 0 | innergemeinschaftlicher Erwerb - in Odoo 11 nicht vorhanden |
| 5051 | Wareneinkauf ig. Erwerb 10% | 0 | dito |
| 5052 | Wareneinkauf ig. Erwerb 0% nach Art. 6 Abs. 2 | 0 | dito |
| 5090 | Wareneinkauf 0% | 0 | Nullsatz - in Odoo 11 nicht vorhanden |

Gruende, warum daraus kein eindeutiger Nachfolger hervorgeht:

1. Es gibt **keine Verwendungsevidenz**: 3400 hat 0 Belegzeilen, und im Ziel hat **keines** der
   Kandidatenkonten auch nur eine Belegzeile (0/0/0/0/0/0/0). Weder Quelle noch Ziel liefern
   einen Nutzungshinweis.
2. Es gibt **keine Steuerlogik**, die eingrenzt: 3400 wird von keiner Odoo-11-Steuer referenziert
   und Odoo 18 fuehrt Konten nicht an Steuern (`account.tax` kennt kein Kontofeld mehr, geprueft:
   nur `cash_basis_transition_account_id`).
3. Der Name nennt einen **Steuersatz (19%)**, den es im Zielkontenrahmen nicht gibt (20% / 10% /
   0%). Eine Zuordnung ueber den Satz waere eine Annahme, keine Ableitung.
4. Auf der Aufwandsseite gibt es in Odoo 11 **keinen einzigen Einkaufsbeleg** (0 `in_invoice`) -
   es fehlt damit auch jede fachliche Spur, welcher Aufwandskontotyp gemeint war.
5. Der bestehende Odoo-18-Wert 5010 ist der Kontenrahmen-Standard, nicht das Ergebnis eines
   Vergleichs mit Odoo 11.

Auswirkung: da 3400 weder in Belegen noch in Steuern vorkommt, betrifft der offene Punkt
**ausschliesslich die Vorgabekonfiguration** der Produktkategorien, nicht die zu migrierenden
Daten (0 zu uebertragende Belegzeilen).

## 5. Benoetigte Entscheidungen (von Anna)

1. Welches Konto ersetzt 3400 als **Aufwandsvorgabe** der Produktkategorien: 5000 Wareneinsatz,
   5010 Wareneinkauf 20% oder ein anderes Konto?
2. Falls ein anderes Konto gewuenscht ist, das im Zielkontenrahmen fehlt: Anlegen durch wen, mit
   welcher Nummer und Bezeichnung? (Die Migration legt keine Konten an.)
3. Soll die Aufwandsvorgabe im Ziel ueberhaupt gesetzt werden, oder bleibt sie auf dem
   Kontenrahmen-Standard 5010? (Fachliche Folge: Produkte ohne eigenes Aufwandskonto buchen dann
   auf 5010, nicht auf ein aus Odoo 11 abgeleitetes Konto.)
4. Bestaetigung, dass 8400 -> 4000 (Abschnitt 3) so bleibt - auch fuer die Firmenvorgabe.

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
