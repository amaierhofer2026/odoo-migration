# Audit-Bericht: Kontaktstruktur Odoo 11 → Odoo 18

Datum: 27. Juli 2026
Status: **NICHT BEREIT für vollständige Migration** — 8 kritische Abweichungen

---

## 1. Feldvergleich (res.partner)

| Metrik | Odoo 11 | Odoo 18 |
|--------|---------|---------|
| Felder gesamt (ir.model.fields) | 169 | 229 |
| Gemeinsame Felder | 130 | 130 |
| Nur O11 (stored) | 24 | — |
| Nur O18 (stored) | — | 41 |

### 1.1 Nur in Odoo 11 (stored) — müssen migriert werden

| Feld | Typ | Bezeichnung |
|------|-----|-------------|
| customer | boolean | Is a Customer |
| supplier | boolean | Is a Vendor |
| date | date | Date |
| image/medium/small | binary | Images (O18 nutzt avatar_*) |
| last_time_entries_checked | datetime | Latest Invoices Matching |
| last_website_so_id | many2one | Last Online Sales Order |
| message_last_post | datetime | Last Message Date |
| opt_out | boolean | Opt-Out |
| picking_warn | selection | Stock Picking Warning |
| picking_warn_msg | text | Message for Stock Picking |
| signup_expiration | datetime | Signup Expiration |
| signup_token | char | Signup Token |
| sla_id | many2one | SLA |
| stp_ids | many2many | Support Ticket Access Accounts |
| support_ticket_ids | one2many | Tickets |
| team_id | many2one | Sales Channel |
| website_description | html | Website Full Description |
| website_meta_* | text/char | Website SEO fields |
| website_short_description | text | Website Short Description |

### 1.2 Typ-Differenzen

| Feld | O11 | O18 | 
|------|-----|-----|
| comment | text | html |

### 1.3 Bezeichnungs-Differenzen (wichtigste)

| Feld | O11 | O18 |
|------|-----|-----|
| vat | TIN | Tax ID |
| ref | Internal Reference | Reference |
| property_product_pricelist | Sale Pricelist | Pricelist |
| sale_warn | Sales Order | Sales Warnings |
| purchase_warn | Purchase Order | Purchase Order Warning |
| child_ids | Contacts | Contact |

---

## 2. Kontaktübersicht (Listenansicht)

### Odoo 11 (res.partner.tree)
Spalten: display_name, function, phone, email, salutation, user_id, is_company, country_id, parent_id, active, category_id

### Odoo 18 (res.partner.list)
Spalten: complete_name, display_name, phone, mobile, email, user_id, street, city, state_id, country_id, vat, category_id, company_id

**Abweichungen:**
- ✗ O18 hat kein `ref` (GKZ) in der Hauptliste — ITK-Customization listet es aber
- ✗ O18 hat kein `parent_id` in der Hauptliste
- ✓ O18 hat zusätzlich mobile, street, city, state_id, vat — funktional besser
- ✓ Keine doppelten Spalten "Salesperson"/"Verkäufer" mehr (itk_base_setup dedup)

**ITK-Tree-View (O18):** `res.partner.tree (itk)` zeigt GKZ (ref) korrekt an — Priority 16

---

## 3. Hauptbereich "Kenndaten"

### ITK-Form (O18): `res.partner.form (itk)` — Priority 16

Felder in dieser View:
- display_name, name, ref (GKZ), attention_of (zu Handen), community_salutation
- user_id (Verkäufer), customer_rank, status_of_partner_id (Status), type
- street, street2, zip, city, state_id, country_id, vat (UID)
- category_id (Stichwörter), function, phone, mobile, email

**Abweichungen:**
- ✗ `multi_factor` ist in eigener View `itk_multifactor` — nicht im Hauptblock
- ✗ `website` fehlt im ITK-Form — nur im Odoo-Standard-Form
- △ `email` nicht als "Email offiziell" labelbar

### Gemeinde-Information (itk_base_setup, Priority 25):
Enthält: multi_factor, is_supplier, is_customer, population, population_update, community_magnitude_id, status_of_community, member_of_city_alliance, austria_wiki_url

---

## 4. Auswahlfelder (Selection)

### 4.1 type (Address Type)

| Schlüssel | O11-Bezeichnung | O18-Bezeichnung | Status |
|-----------|----------------|-----------------|--------|
| contact | Contact | Contact | ✓ |
| invoice | Invoice address | Invoice Address | ✓ (caps) |
| delivery | Shipping address | Delivery Address | ✓ (caps) |
| other | Other address | Other Address | ✓ (caps) |
| private | **Private Address** | — | **✗ FEHLT** |
| administrative | Administration | Administration | ✓ |
| technical | Technik | Technik | ✓ |

**KRITISCH:** `private` fehlt in O18! Falls O11-Datensätze type=private haben, schlagen diese fehl.

### 4.2 trust, invoice_warn, sale_warn, purchase_warn

Alle 1:1 identisch. ✓

### 4.3 lang

Nur `de_DE` in beiden. ✓

### 4.4 picking_warn

Nur in O11, fehlt in O18 (wurde durch `purchase_warn` konsolidiert). △

---

## 5. Kontakte & Adressen

### Breitenbrunn-Vergleich (O11=5794, O18=72):

| Feld | O11 | O18 | Status |
|------|-----|-----|--------|
| parent_id | False | False | ✓ |
| type | contact | contact | ✓ |
| child_ids count | 3 | 3 | ✓ |
| child_ids IDs | [7983,9519,12811] | [84,86,85] | △ (IDs anders) |

**Hinweis:** child_ids sind migriert, aber mit neuen IDs — das ist normal. Zu prüfen: sind die Unterkontakte korrekt (Name, Funktion, E-Mail, Adresse)?

---

## 6. Interne Notizen

**Status: Noch nicht geprüft** — benötigt Zugriff auf message_ids / mail.message.

Zu prüfen:
- comment-Feld (Notizen)
- Chatter-Nachrichten (nur interne, nicht Kundenkommunikation)
- Anhänge (ir.attachment)
- Aktivitäten (mail.activity)

---

## 7. Verkauf & Einkauf

### Breitenbrunn-Vergleich:

| Feld | O11 | O18 | Status |
|------|-----|-----|--------|
| user_id | [21, 'IT-Kommunal'] | [2, 'Administrator'] | **✗ FALSCH** |
| property_product_pricelist | [1, 'Public Pricelist'] | [34, 'Preisliste 2026…'] | △ (andere Liste) |
| property_payment_term_id | — | [12, '14 Tage'] | △ (neu gesetzt) |
| customer/supplier | Boolean True/False | customer_rank=15, supplier_rank=0 | △ (Modellwechsel) |

### Stichproben-Ergebnis: Alle 4 Kontakte haben user_id=[2,'Administrator'] statt [21,'IT-Kommunal']

---

## 8. Abrechnung

### Breitenbrunn-Vergleich:

| Feld | O11 | O18 | Status |
|------|-----|-----|--------|
| property_account_receivable | [295, '1410 Forderungen…'] | [80, '2000 Trade receivables…'] | △ (neuer Kontenplan) |
| property_account_payable | [401, '1610 Verbindl…'] | [129, '3300 Trade payables…'] | △ (neuer Kontenplan) |
| total_invoiced | 871.01 | 871.01 | ✓ |
| journal_item_count | 42 | 42 | ✓ |
| vat | False | '' | △ |

---

## 9. Gemeinde-Information — KRITISCH ⚠️

### Stichproben:

| Gemeinde | O11 population | O18 population | O11 magnitude | O18 magnitude |
|----------|---------------|----------------|---------------|---------------|
| Eisenstadt (10101) | 15.220 | **0** | 10.001-20.000 | **bis 500** |
| Rust (10201) | 1.953 | **0** | 1.501-2.000 | **bis 500** |
| Breitenbrunn (10301) | 1.909 | 1.909 ✓ | 1.501-2.000 | 1.501-2.000 ✓ |
| Großhöflein (10303) | 2.048 | **0** | 2.001-2.500 | **bis 500** |

**3 von 4 Kontakten haben falsche Einwohnerzahlen (0 statt korrektem Wert) und falsche Größenklassen!**

### status_of_community ID-Mismatch:

| O11 ID | O11 Name | O18 ID | O18 Name |
|--------|----------|--------|----------|
| 9 | Marktgemeinde | 1 | Marktgemeinde |

**Die Many2one-ID hat sich geändert!** Mapping-Tabelle nötig.

---

## 10. Smart Buttons

### Vergleich:

| Button | O11 Feld | O18 Feld | Status |
|--------|----------|----------|--------|
| Opportunities | opportunity_count | opportunity_count | ✓ |
| Meetings | meeting_count | meeting_count | ✓ |
| Sales | sale_order_count | sale_order_count | ✓ |
| Invoiced | total_invoiced | total_invoiced | ✓ |
| Subscriptions | subscription_count | subscription_count | ✓ |
| Support Tickets | support_ticket_string | helpdesk_ticket_count_string | △ |
| Tasks | task_count | task_count | ✓ |
| Purchases | purchase_order_count | purchase_order_count | ✓ |
| On Website | website_published | is_published | △ |
| Active | active (toggle) | active (toggle) | ✓ |

**Zähler werden korrekt berechnet** (sale_order_count=2, subscription_count=1, total_invoiced=871.01 stimmen überein).

---

## 11. Tabs & Reihenfolge

### Odoo 11 (erwartet):
1. Kontakte & Adressen
2. Interne Notizen
3. Verkauf & Einkauf
4. Abrechnung
5. Gemeinde-Information
6. Support Ticket

### Odoo 18 (tatsächlich):
1. Contacts & Addresses (Odoo-Form)
2. Sales & Purchase (Odoo-Form)
3. Internal Notes (Odoo-Form)
4. Gemeinde-Information (ITK-Form — Priority 25)
5. Support Ticket (itk_base_setup smart buttons — Priority 30)

**Abweichungen:**
- ✗ "Abrechnung" Tab fehlt in O18 — wird über Accounting-Modul bereitgestellt (nicht automatisch sichtbar)
- △ Tab-Namen sind auf Englisch ("Sales & Purchase" statt "Verkauf & Einkauf")
- ✓ "Gemeinde-Information" existiert mit korrekten Feldern
- ✓ "Support Ticket" existiert

---

## 12. Verknüpfte Modelle

| Relation | Status | Anmerkung |
|----------|--------|-----------|
| user_id (Verkäufer) | **✗ FALSCH** | Alle auf Admin [2] statt IT-Kommunal [21] |
| state_id (Bundesland) | **✗ ID-Mismatch** | O11=680, O18=1781 für Burgenland |
| country_id | ✓ | [12, 'Austria'] beide |
| status_of_community | **✗ ID-Mismatch** | O11=9, O18=1 für Marktgemeinde |
| category_id (Tags) | **✗ ID-Mismatch** | O11=32, O18=11 |
| property_account_* | △ | Neuer Kontenplan — erwartet |
| property_product_pricelist | △ | Neue Preisliste — erwartet |

---

## 13. Datenvalidierung Stichprobe

4 Kontakte in beiden Systemen gefunden (von 15 geprüften O11-Kontakten). 6 sind noch nicht migriert.

**Alle 4 Stichproben haben mindestens 1 Abweichung.**

---

## 14. Fehlerklassen

### Kritisch (muss vor Migration behoben werden):

| # | Fehler | Kategorie | Betroffene |
|---|--------|-----------|------------|
| 1 | user_id falsch (Admin statt IT-Kommunal) | Relation zeigt auf falschen Datensatz | ALLE |
| 2 | population=0 für 3/4 Gemeinden | Wert nicht importiert | Eisenstadt, Rust, Großhöflein |
| 3 | community_magnitude falsch ("bis 500") | falscher Auswahlwert | Eisenstadt, Rust, Großhöflein |
| 4 | type="private" fehlt in O18-Selection | Feld fehlt | Alle type=private |
| 5 | state_id ID-Mismatch | Relation fehlt/anders | Alle AT-Kontakte |
| 6 | status_of_community ID-Mismatch | Relation zeigt auf falschen Datensatz | Alle Gemeinden |
| 7 | category_id ID-Mismatch | Relation zeigt auf falschen Datensatz | Alle mit Tags |
| 8 | Abrechnung-Tab nicht sichtbar | Ansicht falsch | Alle |

### Mittel (vor Migration prüfen):

| # | Fehler | 
|---|--------|
| 9 | Unterkontakte (child_ids) — Inhalte noch nicht verifiziert |
| 10 | Interne Notizen/Chatter — noch nicht geprüft |
| 11 | Anhänge — noch nicht geprüft |
| 12 | Picking_warn Feld fehlt in O18 |
| 13 | Website-Felder (SEO) fehlen |

### Bereits korrigiert:

- ✓ GKZ (ref) in Listenansicht über ITK-Tree-View
- ✓ Deduplizierung Salesperson/Verkäufer (itk_base_setup)
- ✓ UID-Label-Fix (ITK: Fix UID label)
- ✓ Smart-Button-Zähler funktionieren

---

## 15. Freigabeempfehlung

**STATUS: NICHT BEREIT für vollständige Migration**

### Vor Freigabe zu beheben:

1. **Mapping-Tabellen erstellen für:**
   - user_id (res.users): alte ID → neue ID (Login-basiert)
   - state_id (res.country.state): alte ID → neue ID (Code-basiert)
   - status_of_community (itk_crm.statusofcommunity): alte ID → neue ID (Name-basiert)
   - category_id (res.partner.category): alte ID → neue ID (Name-basiert)

2. **Daten-Import-Script fixen:**
   - population-Feld korrekt importieren
   - community_magnitude_id korrekt mappen
   - user_id korrekt mappen (nicht auf Admin defaulten)

3. **Odoo-18-Struktur anpassen:**
   - type-Selection um "private" ergänzen (falls O11-Daten es nutzen)

4. **Bereits migrierte Kontakte korrigieren:**
   - user_id, population, community_magnitude_id, status_of_community für alle 4 korrigieren

5. **Vor erneuter Migration:**
   - Mapping-Tabellen per JSON-RPC validieren
   - Test-Import mit 1-2 Gemeinden
   - UI-Prüfung durch Anna

---

## 16. Nächste Schritte

1. Alte migrierte Test-Kontakte in O18 löschen/zurücksetzen
2. Mapping-Tabellen erstellen
3. Migrationsscript korrigieren
4. Neu migrieren
5. Diesen Audit erneut durchführen
6. Erst bei 0 kritischen Abweichungen: Freigabe für Vollmigration
