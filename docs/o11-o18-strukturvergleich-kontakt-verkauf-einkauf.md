# Strukturvergleich Odoo 11 Prod ↔ Odoo 18: Kontakte → Kontaktformular → Verkauf & Einkauf

Stand: 15.09.2026 (Session 105)
Quellen: Odoo 11 Prod `portal.it-kommunal.at` (DB `ITK_V1_a`, nur gelesen) und Odoo 18 (lokal + VM `k001959vsx.ipax.at`, DB `odoo18_test`)

Auftrag von Anna: **kein optischer Rückbau auf Odoo 11.** Ziel ist ausschließlich, dass bei der späteren
Datenmigration alle relevanten Felder korrekt und eindeutig in Odoo 18 landen. Odoo 18 ist im Tab
"Verkauf & Einkauf" **fachlich vollständiger** als Odoo 11 (Zahlungsbedingungen, Zahlungsmethoden,
Steuerposition, Käufer, Eingangserinnerung stehen dort, in Odoo 11 teilweise im Tab "Abrechnung").
Diese Felder bleiben unverändert erhalten.

## 1. Feld-Mapping (Auftrag: Feld / Bedeutung / Zielfeld / Typ / 1:1 / Transformation / entfällt / neu)

| Odoo 11 Feld | Bedeutung | Odoo 18 Zielfeld | Typ | 1:1 möglich | Transformation | entfällt | neu ohne O11-Quelle |
|---|---|---|---|---|---|---|---|
| `customer` | Ist ein Kunde | `is_customer` (compute) → `customer_rank` | boolean → boolean/integer | ja, über Odoo-18-Logik | **ja**: `customer=True` → `customer_rank = 1` | – | – |
| `supplier` | Ist ein Lieferant | `is_supplier` (compute) → `supplier_rank` | boolean → boolean/integer | ja, über Odoo-18-Logik | **ja**: `supplier=True` → `supplier_rank = 1` | – | – |
| `user_id` | Verkäufer | `user_id` | many2one `res.users` | ja | nein (nur Benutzer-ID-Mapping) | – | – |
| – | – | `buyer_id` | many2one `res.users` | – | – | – | **ja** (Einkäufer) |
| `property_product_pricelist` | Verkaufspreisliste | `property_product_pricelist` ("Preisliste") | many2one `product.pricelist`, firmenabhängig | ja, nach ID-Mapping | **ja**: Preislisten-ID-Mapping nötig | – | – |
| `property_payment_term_id` | Zahlungsbedingungen Verkauf | `property_payment_term_id` | many2one `account.payment.term`, firmenabhängig | ja | nein (nur Stammdaten-Zuordnung) | – | – |
| `property_supplier_payment_term_id` | Zahlungsbedingungen Einkauf | `property_supplier_payment_term_id` | many2one `account.payment.term`, firmenabhängig | ja | nein | – | – |
| – (O11 führt keine Zahlungsmethode am Kontakt) | – | `property_inbound_payment_method_line_id`, `property_outbound_payment_method_line_id` | many2one `account.payment.method.line`, firmenabhängig | – | – | – | **ja** (Zahlungsmethode Ein-/Ausgang) |
| `property_purchase_currency_id` | Lieferantenwährung | `property_purchase_currency_id` | many2one `res.currency`, firmenabhängig | ja | nein | – | – |
| `property_account_position_id` | Steuerzuordnung | `property_account_position_id` ("Steuerposition") | many2one `account.fiscal.position`, firmenabhängig | ja, Feld/Technik identisch | **ja**: Steuerpositions-Inhalte müssen zugeordnet werden | – | – |
| `ref` | Interne Referenz | `ref` ("Referenz") | char | ja | nein (nur Beschriftung weicht ab) | – | – |
| `industry_id` | Branche | `industry_id` | many2one `res.partner.industry` | ja | nein | – | – |
| – | – | `company_registry` ("Unternehmens-ID") | char | – | – | – | **ja** |
| `multi_factor` (Modul `itk_multifactor`) | Multiplication Factor/Thsd | `multi_factor` ("Multiplikationsfaktor (pro 1.000)") | integer | **ja, 1:1** (identischer Feldname, identisches Modul, identischer Typ) | nein | – | – |
| `website` | Website | `website` | char | ja | nein | – | – |
| – | – | `website_id` | many2one `website` | – | – | – | **ja** |
| `bank_ids` | Bankkonten | `bank_ids` ("Banken") | one2many `res.partner.bank` | ja | nein | – | – |
| `property_account_receivable_id` / `property_account_payable_id` | Debitoren-/Kreditorenkonto | gleichnamig | many2one `account.account`, firmenabhängig | ja | nein (Odoo 18 nutzt eigene Lokalisierungs-Standardwerte) | – | – |
| `currency_id`, `company_id` | Hilfsfelder (in beiden unsichtbar) | gleichnamig | many2one | ja | nein | – | – |
| `message_bounce` | Unzustellbar (unsichtbar) | `message_bounce` | integer | ja | nein | – | – |
| `payment_token_count` | Kreditkarte(n) (Statistikfeld) | `payment_token_count` | integer | Feld vorhanden | nein | im Tab nicht mehr angezeigt | – |
| `opt_out` | Keine Werbe-E-Mails | – | boolean | **nein** | **ja**: in Odoo 18 über Marketing-Abos (`mailing.contact.opt_out`, `mailing.subscription`) | **ja** | – |
| `property_stock_customer` / `property_stock_supplier` | Kundenlagerort / Lagerort des Lieferanten | – | many2one `stock.location` | **nein** | Funktion in Odoo 18 über Lager/Routen; kein Feld-Nachbau | **ja** | – |
| – | – | `global_location_number` (GLN), `receipt_reminder_email`, `reminder_date_before_receipt` | char/boolean/integer | – | – | – | **ja** |

## 2. Verwendung in Odoo 11 Prod (Datenlage, read-only)

| Feld | Kontakte mit Wert |
|---|---|
| `customer = True` | **5.829** von 5.842 |
| `supplier = True` | 0 |
| `user_id` (Verkäufer) | 4.397 (34 verschiedene Verkäufer) |
| `property_product_pricelist` | 3.751 Individualwerte |
| `property_payment_term_id` | 619 (ausschließlich "14 Tage") |
| `property_supplier_payment_term_id` | 0 |
| `property_purchase_currency_id` | 0 |
| `property_account_position_id` | 1 ("Dienstleister EU (mit USt-ID)") |
| `ref` | 2.281 |
| `industry_id` | 0 (21 Branchen angelegt, keine genutzt) |
| `multi_factor` | 2.663 |
| `website` | 2.129 |
| `bank_ids` | 1 Bankverbindung (1 Kontakt) |
| `opt_out = True` | 22 |

Preislisten-Verteilung (Individualwerte): Public Pricelist 2.576 · GSZ Kärnten 2019+2020 (nicht mehr verwenden) 206 ·
GemDat Oberösterreich BLFS oö (nicht mehr verwenden) 165 · GemDat Niederösterreich alt (nicht mehr verwenden) 53 ·
weitere. In Odoo 11 sind 50 Preislisten angelegt (alle aktiv), in Odoo 18 zwei.

## 3. Prüfpunkte aus dem Auftrag

**a) Sind `customer`/`supplier` korrekt auf die Odoo-18-Logik gemappt?**
Ja. In Odoo 18 existieren die Odoo-11-Booleanfelder nicht mehr; die Funktion liegt in `customer_rank`/`supplier_rank`
(Modul `account`, gespeichert). Unser Modul `itk_base_setup` bildet die Bedienlogik korrekt ab: `is_customer` und
`is_supplier` sind berechnete Felder mit `inverse` auf `customer_rank`/`supplier_rank` (Häkchen setzen → Rang 1,
Häkchen löschen → Rang 0). Verifiziert lokal und auf der VM (Kontakt mit `customer_rank = 1` zeigt
`is_customer = True`). Für die Migration genügt daher ein Schreibvorgang auf `customer_rank`/`supplier_rank`.

**b) Können Preislisten-IDs später eindeutig gemappt werden?**
Technisch ja (gleiches Feld, gleiche Technik, firmenabhängig). Inhaltlich **noch nicht**: Odoo 11 nutzt 50 Preislisten,
Odoo 18 hat zwei, und keine der in Odoo 11 tatsächlich verwendeten Preislisten existiert in Odoo 18. Vor der
Datenmigration ist deshalb eine **Preislisten-Zuordnungstabelle** zu erstellen (inkl. Anlage der benötigten
Preislisten) – offener Punkt, siehe Abschnitt 5.

**c) Sind Verkäufer-/Käufer-Beziehungen auf Benutzer sauber auflösbar?**
Nur teilweise. Odoo 11 hat 61 Benutzer, in Odoo 18 existieren davon **15**; **46 fehlen**. Da 4.397 Kontakte einen
Verkäufer haben, müssen diese Benutzer vor der Datenmigration angelegt bzw. eindeutig zugeordnet werden.
`buyer_id` (Käufer) hat in Odoo 11 keine Quelle (neues Feld, keine Migration nötig).

**d) Müssen Zahlungsbedingungen und Währungen vorher als Stammdaten vorhanden sein?**
Ja. Ergebnis der Prüfung ist hier aber positiv:
- Währungen: EUR und USD sind in beiden Systemen aktiv – keine Lücke.
- Zahlungsbedingungen: der einzige in Odoo 11 tatsächlich verwendete Wert "14 Tage" (619 Kontakte) ist in Odoo 18
  vorhanden; "Immediate Payment", "15 Days" und "30 Days" ebenfalls. Nur "30 Net Days" fehlt in Odoo 18 – in Odoo 11
  aber **0-mal verwendet**, daher ohne Migrationswirkung.

**e) Passen die bestehenden Custom-Felder (Multiplikationsfaktor, Referenz) zur Migration?**
Ja, exakt. `multi_factor` ist in beiden Systemen Feld des Moduls `itk_multifactor` mit identischem Namen und Typ
(integer) – 1:1 übernehmbar (2.663 Werte). `ref` ist in beiden `res.partner.ref` (char), ausschließlich die
Beschriftung weicht ab (Odoo 11 "Interne Referenz", Odoo 18 "Referenz"). Auf einen optischen Rückbau wurde auf
Anweisung verzichtet; die Umbenennung wäre auf Wunsch jederzeit möglich. Odoo 11 hat auf `res.partner` keine
weiteren eigenen Felder.

## 4. Umgesetzte Änderungen (Sessions 105 und 106)

**Ein struktureller GAP wurde direkt behoben:** In Odoo 18 waren **beide** Preislisten inaktiv
(`Standard-Preisliste` USD, `Preisliste 2026 + Valorisierung` EUR). Das Feld `property_product_pricelist` verweist auf
Preislisten, die im Zielsystem auswählbar sein müssen. Die inaktive EUR-Preisliste wurde daher auf **lokal und VM**
aktiviert (reversibel, keine Produktionsdaten, keine Datensätze geändert).

**Zweite Änderung (Anweisung Anna, Session 106): Beschriftung „Referenz“ → „Interne Referenz“**

Odoo 11 Prod führt das Feld als „Interne Referenz“; Odoo 18 setzt in der Basis-Ansicht ausdrücklich „Referenz“.
Umgesetzt in `itk_base_setup` 18.0.1.2.1:
- Modell: `ref = fields.Char(string='Interne Referenz', index=True)` in `models/res_partner.py` (identische Felddefinition,
  nur die Beschriftung) → gilt auch für Suche/Filter und alle Ansichten ohne eigene Beschriftung
- Formular: XPath auf `//page[@name='sales_purchases']//field[@name='ref']` setzt die Beschriftung im Tab
- Deutsche Übersetzung des Feldtitels in beiden Datenbanken auf „Interne Referenz“ gesetzt (`ir.model.fields` id 908,
  `field_description` im Kontext `lang=de_DE`), weil der alte de_DE-Eintrag „Referenz“ sonst bestehen bleibt.
  Eine frische Datenbank braucht das nicht, weil der Quelltext bereits deutsch ist.

Das Feld selbst (`res.partner.ref`, char) und alle Inhalte bleiben unverändert. Die Beschriftung „GKZ“ im Kenndatenblock
und in der Kontaktliste bleibt wie bisher (in Odoo 11 Prod ebenfalls „GKZ“) — dort ist die ITK-Bedeutung eine andere.

Am übrigen Tab wurde **nichts** geändert: Odoo 18 ist dort vollständiger als Odoo 11 und bleibt unverändert.

Prüfwerkzeug: `scripts/verify_s105_verkauf_einkauf.py` (read-only, prüft Felder, Typen, Odoo-18-Kundenlogik,
Stammdaten, Arch des Tabs) → lokal **50 OK / 0 FEHL**, VM **50 OK / 0 FEHL**.

## 5. Entscheidungen von Anna und verbindliche Vorgaben für die Migration (Session 106)

Alle fünf Punkte sind entschieden. **Nichts davon wird jetzt angelegt** — die folgenden Vorgaben sind bei der
späteren Datenmigration verbindlich einzuhalten.

### 5.1 Preislisten — VOR der Kontakt-/Verkaufsdatenmigration anzulegen bzw. zu mappen

**Verbindlich:** Bevor Kontakt- oder Verkaufsdaten migriert werden, müssen die in Odoo 11 tatsächlich verwendeten
Preislisten in Odoo 18 angelegt und in einer Zuordnungstabelle (Odoo-11-Preislisten-ID → Odoo-18-Preislisten-ID) gemappt
sein. Ohne diese Zuordnung darf `property_product_pricelist` nicht geschrieben werden.

Zu berücksichtigen (Stand Session 105/106):
- Odoo 11: 50 Preislisten; tatsächlich am Kontakt verwendet: Public Pricelist (2.576), GSZ Kärnten 2019 + 2020
  Valorisierung (206), GemDat Oberösterreich BLFS oö (165), GemDat Niederösterreich alt (53)
- Odoo 18: zwei Preislisten, beide waren inaktiv — die EUR-Preisliste „Preisliste 2026 + Valorisierung“ wurde in
  Session 105 aktiviert und **bleibt aktiv** (Anweisung Anna)
- die Odoo-18-Standard-Preisliste (id 1) ist in **USD**, die Odoo-11-Entsprechung in **EUR** → bei der Zuordnung festlegen

### 5.2 Benutzer / Verkäufer — Mapping- und Abfangstrategie

**Verbindlich (Anweisung Anna):** keine fehlenden Odoo-11-Benutzer jetzt anlegen. Bei der Migration gilt:
1. **Vorhandener aktiver Odoo-18-Benutzer** → 1:1 zuordnen (Abgleich über `login` bzw. E-Mail).
2. **Ausgeschiedene oder nicht mehr benötigte Odoo-11-Benutzer** → historische Verkäuferbeziehung erhalten, ohne
   zwingend einen aktiven Login anzulegen: Benutzer deaktiviert anlegen (`res.users.active = False`, ohne Passwort) und
   `res.partner.user_id` darauf setzen; der Datensatz bleibt als Referenz erhalten und in Berichten sichtbar.
   Hinweis für die Planung: auch deaktivierte interne Benutzer zählen in der Odoo-Lizenzierung.
3. **Fachlich unklare Benutzer** → später einzeln entscheiden (Sammelliste bei der Migration vorlegen).

Datenlage: 4.397 Kontakte mit Verkäufer, 34 verschiedene Verkäufer; Odoo 11 hat 61 Benutzer, in Odoo 18 existieren 15.

### 5.3 Steuerpositionen — vor der Migration zuordnen

**Verbindlich:** nichts jetzt anlegen. Vor der Migration sind die fünf in Odoo 11 vorhandenen Steuerpositionen den
Odoo-18-Steuerpositionen zuzuordnen; fehlende Stammdaten sind vorher vorzubereiten.

| Odoo 11 (5 Positionen) | mögliche Odoo-18-Entsprechung |
|---|---|
| Dienstleister Ausland | Drittstaaten (oder neu anzulegen) |
| Geschäftspartner Ausland | Drittstaaten (oder neu anzulegen) |
| Geschäftspartner EU (mit USt-ID) | Europäische Union |
| Dienstleister EU (mit USt-ID) | Europäische Union (oder neu anzulegen) |
| Geschäftspartner EU (ohne USt-ID) | National + EU (ohne UID) |

Die endgültige Zuordnung ist fachlich über die Buchhaltung zu bestätigen. Betroffene Daten: 1 Kontakt in Odoo 11.

### 5.4 opt_out (22 Kontakte) — in die Odoo-18-Marketing-/Blacklist-Logik überführen, nicht nachbauen

**Verbindlich:** kein Nachbau des Odoo-11-Feldes `res.partner.opt_out`. In Odoo 18 liegt die Kennzeichnung nicht mehr
am Kontakt, sondern in der Marketing-/Blacklist-Logik (Modul `mass_mailing`, bereits Abhängigkeit unseres Moduls):

| Odoo-18-Objekt | Feld | Bedeutung |
|---|---|---|
| `mail.blacklist` | `email`, `opt_out_reason_id` | zentrale Sperrliste, wirkt auf alle Mailings |
| `mailing.contact` | `opt_out`, `is_blacklisted`, `subscription_ids` | Empfänger-Datensatz der Mailinglisten |
| `mailing.subscription` | `opt_out`, `opt_out_datetime`, `opt_out_reason_id`, `is_blacklisted` | Abo je Liste |
| `mailing.list` | `contact_count_opt_out`, `contact_pct_opt_out` | Auswertung |

Empfohlener Weg bei der Migration: für die 22 Kontakte mit „Keine Werbe-E-Mails“ die E-Mail-Adresse in
`mail.blacklist` eintragen; existiert bereits ein Empfänger-Datensatz, zusätzlich `mailing.subscription.opt_out = True`
mit `opt_out_datetime` setzen. Damit sind diese Adressen in Odoo 18 wirksam gegen Mailings gesperrt — ohne Altfeld-Nachbau.

### 5.5 Beschriftung „Interne Referenz“

Umgesetzt in Session 106 (siehe Abschnitt 4): Modellbeschriftung, Formular-XPath und deutsche Übersetzung.

## 6. Ergebnis

Der Tab „Verkauf & Einkauf“ ist **migrationsbereit und abgeschlossen** (Session 106).

- Alle 23 geprüften Zielfelder existieren in Odoo 18 mit korrektem Typ und korrekter Relation.
- Die Odoo-18-Kunden-/Lieferantenlogik (`customer_rank`/`supplier_rank` mit `is_customer`/`is_supplier`) ist aktiv und
  lokal sowie auf der VM verifiziert.
- Bewusst entfallende Odoo-11-Felder sind dokumentiert, kein Nachbau.
- Beschriftung „Interne Referenz“ wie in Odoo 11 umgesetzt.
- Stammdaten: Währungen und Zahlungsbedingungen vollständig; Preislisten, Benutzer und Steuerpositionen sind als
  verbindliche Vorgaben für die Datenmigration dokumentiert (Abschnitt 5).
- Kein optischer Rückbau, keine Produktionsdaten übernommen.

Nachweis: `scripts/verify_s105_verkauf_einkauf.py` (read-only) und Browser-Prüfung des Tabs auf der VM.
