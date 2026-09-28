# Odoo 11 -> Odoo 18: Bereich Verkauf, Teil 3, Schritt 4 (Suchfelder, Filter, Gruppierungen, Suche)

Stand: 28.09.2026, Session 121. Odoo 11 Prod (`portal.it-kommunal.at`, DB `ITK_V1_a`) wurde
ausschliesslich lesend gelesen (RPC). Geprueft: Odoo 18 lokal (`odoo18_test`) und VM
(`k001959vsx.ipax.at`, Buer-Zugang).

Analysierte Listen (jeweils ueber den Menuepunkt, den Anna benutzt):

| Odoo 11 Menue | Aktion | Odoo 18 Menue | Aktion |
|---|---|---|---|
| Verkauf/Auftraege/Angebote nach Kunden | 429 | Verkauf/Auftraege/Angebote | 430 |
| Verkauf/Auftraege/Auftraege nach Kunden | 426 | Verkauf/Auftraege/Auftraege | 429 |
| Verkauf/Abrechnung/Auftraege zur Rechnung | 427 | Verkauf/Abzurechnen/Abzurechnende Auftraege | 432 |
| Verkauf/Abrechnung/Auftraege fuer Upselling | 428 | Verkauf/Abzurechnen/Auftraege fuer Upselling | 433 |
| Kundenverwaltung/Pipeline/Angebote | 429 | Kundenverwaltung/Pipeline/Angebote | 431 |

## 1. Suchfelder

| Suchfeld | Odoo 11 | Odoo 18 | Bewertung |
|---|---|---|---|
| Auftragsnummer | `name` (auch Kundenreferenz und Kunde) | `name` (gleicher Ausdruck) | gleich |
| Kunde | `partner_id` (child_of) | `partner_id` (child_of) | gleich |
| Verkaeufer | `user_id` | `user_id` | gleich |
| Vertriebskanal / Verkaufsteam | `team_id` | `team_id` ("Verkaufsteam") | gleich, Label Odoo 18 |
| Produkt | `product_id` (Relation auf Auftragszeilen) | `order_line` ("Produkt") | gleichwertig |
| Endkunde | `final_customer_id` | `final_customer_id` | ITK-Feld, in beiden vorhanden |
| Produktkategorie | `product_category_id` | `product_category_id` | ITK-Feld, in beiden vorhanden |
| Analytisches Konto | `analytic_account_id` | fehlt | in Odoo 11 auf **0** Auftraegen belegt, Feld in Odoo 18 nicht mehr vorhanden (Odoo 18 nutzt `analytic_distribution` an den Auftragszeilen) -> kein Nachbau, dokumentiert |
| Kampagne (UTM) | - | `campaign_id` | Odoo-18-Zusatz, bleibt |
| Erstellt am / Auftragsdatum | - | Datumsfilter | Odoo-18-Zusatz, bleibt |

## 2. Filter

### 2.1 Angebotsliste (Aktion 429 bzw. 430/431)

| Odoo 11 Filter | Domain | Odoo 18 vorher | Umsetzung |
|---|---|---|---|
| Meine Bestellungen | `user_id = uid` | Meine Angebote | gleichwertig vorhanden (Odoo-18-Wortlaut) |
| Angebote | `state = draft` | - (in "Angebote" draft+sendet enthalten) | **ergaenzt:** "Angebote (Entwurf)" |
| Kostenvoranschlag gesendet | `state = sent` | - | **ergaenzt:** "Kostenvoranschlag gesendet" |
| Verkauf | `state in (sale, done)` | Verkaufsauftraege (`state = sale`) | gleichwertig (Odoo 18 hat kein `done`) |
| Ungelesene Nachrichten | `message_needaction = true` | fehlt | **ergaenzt:** "Ungelesene Nachrichten" |
| Meine Aktivitaeten | `activity_ids.user_id = uid` | fehlt | **ergaenzt:** "Meine Aktivitaeten" |
| Verspaetete/Heutige/Anstehende Aktivitaeten | Aktivitaetsdatum | vorhanden | bleibt |
| Bestaetigte Auftraege | `state in (sale, done)` | - | durch "Verkaufsauftraege" abgedeckt, kein Doppelfilter |
| Von Website | `team_id.team_type = website` | - | Website wird bewusst nicht migriert, entfaellt |
| Zu sendende Wiederherstellungs-E-Mail | `cart_recovery_email_sent = false` | - | Website-Kaufvorgang, in Odoo 11 nicht genutzt (0 Warenkoerbe), entfaellt |
| - | - | Erstellt am (Datumsfilter) | Odoo-18-Zusatz, bleibt |

### 2.2 Auftragsliste (Aktion 426 bzw. 429)

| Odoo 11 Filter | Domain | Odoo 18 vorher | Umsetzung |
|---|---|---|---|
| Meine Bestellungen | `user_id = uid` | Meine Auftraege | gleichwertig vorhanden |
| Verkauf | `state in (progress, done)` | - | der Odoo-11-Filter ist defekt: `progress` ist kein Odoo-11-Zustand; die Liste selbst ist bereits auf `state not in (draft, sent, cancel)` eingeschraenkt -> kein Nachbau |
| Abzurechnen | `invoice_status = to invoice` | Abzurechnen | gleich |
| Zusatzverkaeufe | `invoice_status = upselling` | Upselling | gleich |
| Ungelesene Nachrichten | `message_needaction = true` | fehlt | **ergaenzt** |
| Meine Aktivitaeten | `activity_ids.user_id = uid` | fehlt | **ergaenzt** |
| Verspaetete/Heutige/Anstehende Aktivitaeten | Aktivitaetsdatum | vorhanden | bleibt |
| Bestaetigte Auftraege / Von Website / Wiederherstellungs-E-Mail | siehe oben | - | siehe oben |

### 2.3 Abzurechnende Auftraege und Upselling (Aktion 427/428 bzw. 432/433)

| Odoo 11 Filter | Odoo 18 vorher | Umsetzung |
|---|---|---|
| Meine Bestellungen | Meine Auftraege | gleichwertig |
| Ungelesene Nachrichten | fehlt | **ergaenzt** |
| Meine Aktivitaeten | fehlt | **ergaenzt** |
| Aktivitaetsfilter (3) | vorhanden | bleibt |
| Bestaetigte Auftraege, Von Website, Wiederherstellungs-E-Mail | - | siehe oben |

### 2.4 Default-Filter (Voreinstellung beim Menueaufruf)

| Menue | Odoo 11 | Odoo 18 vorher | Umsetzung |
|---|---|---|---|
| Verkauf/Auftraege/Angebote | kein Default | `search_default_my_quotation = 1` (nur eigene Angebote) | **entfernt**, Filter bleibt auswaehlbar |
| Kundenverwaltung/Pipeline/Angebote | kein Default | `search_default_my_quotation = 1` | **entfernt**, Filter bleibt auswaehlbar |
| Verkauf/Auftraege/Auftraege | kein Default | kein Default | nichts zu tun |
| Abzurechnende Auftraege / Upselling | `create = False` | `create = False` | gleich |

Das war die offene Entscheidung aus Teil 1 (24.09.2026) und ist damit umgesetzt.

## 3. Gruppierungen

| Odoo 11 | Odoo 18 | Bewertung |
|---|---|---|
| Verkaeufer (`user_id`) | Vertriebsmitarbeiter (`user_id`) | gleich, Label Odoo 18 |
| Kunde (`partner_id`) | Kunde (`partner_id`) | gleich |
| Endkunde (`final_customer_id`) | Endkunde (`final_customer_id`) | gleich |
| Produktkategorie (`product_category_id`) | Produktkategorie (`product_category_id`) | gleich |
| Auftragsmonat (`date_order`) | Auftragsdatum (`date_order`) | gleich, Label Odoo 18 |
| - | plus Datums-/Feldgruppierungen und "Benutzerdefinierte Gruppe" | Odoo-18-Zusatz, bleibt |

## 4. Gespeicherte Filter (Favoriten)

Odoo 11 hat 14 benutzerspezifische gespeicherte Filter auf `sale.order`, davon 3 als Standard
markiert; Odoo 18 hat keine. Die Entscheidung aus Teil 1 bleibt bestehen: keine Migration.
Siehe `migration/verkauf_migrationsregeln.json`.

## 5. Umsetzung in Odoo 18 (nur ergaenzt, nichts entfernt)

Modul `itk_sale_management`, Version 18.0.1.3.0:

```
views/sale_order_views_suche.xml     zwei geerbte Suchansichten (Wurzel, priority 99):
                                     1) sale.view_sales_order_filter        -> "Ungelesene Nachrichten",
                                                                              "Meine Aktivitaeten"
                                     2) sale.sale_order_view_search_inherit_quotation
                                                                            -> "Angebote (Entwurf)",
                                                                              "Kostenvoranschlag gesendet"
data/sale_actions_kontext.xml        Aktionen sale.action_quotations und
                                     sale.action_quotations_with_onboarding: Kontext ohne
                                     search_default_my_quotation
```

Wortlaut-Abweichung (dokumentiert): Odoo 11 nannte den Entwurfsfilter "Angebote"; dieser Name ist in
Odoo 18 durch den Filter "Angebote" (Entwurf und gesendet) belegt, deshalb "Angebote (Entwurf)".
Alle Odoo-18-Filter, -Gruppierungen und -Suchfelder bleiben unveraendert erhalten.

## 6. Nachweise

```
scripts/analyse_verkauf_teil3_suche.py        je Aktion: Suchansicht, Suchfelder, Filter,
                                              Gruppierungen, Default-Kontext (Odoo 11/lokal/VM)
scripts/verify_s121_verkauf_teil3_filter.py   Prueflauf Odoo 11 (lesend) + lokal + VM
scripts/browser_verkauf_filter_suche.py       Browserabnahme der Suchleiste
docs/_verkauf_teil3_suche.json                Rohdaten (gitignoriert)
```

Ergebnisse lokal (28.09.2026):

```
Modul-Upgrade itk_sale_management 18.0.1.3.0 (nach docker restart odoo18)  ohne Fehler
verify_s121_verkauf_teil3_filter.py    lokal 78 OK / 0 FEHL (Odoo 11 als Ausgangslage 43 OK / 0 FEHL)
browser_verkauf_filter_suche.py        lokal 19 OK / 0 FEHL, 0 JavaScript- und 0 RPC-Fehler
```

Ergebnisse VM (28.09.2026, Buer-Zugang, Git-Stand 3e15474, Container-Neustart durch Anna):

```
Modul-Upgrade itk_sale_management 18.0.1.3.0 auf der VM ueber RPC   ohne Fehler
verify_s121_verkauf_teil3_filter.py    Odoo 11 43 OK + lokal 78 OK + VM 78 OK = 199 OK / 0 FEHL
browser_verkauf_filter_suche.py        VM 19 OK / 0 FEHL, 0 JavaScript- und 0 RPC-Fehler
  - Menueaufruf "Angebote" oeffnet ohne Facette (kein Default-Filter)
  - Suchmenue zeigt: Meine Angebote, Angebote, Angebote (Entwurf), Kostenvoranschlag gesendet,
    Verkaufsauftraege, Erstellt am, Ungelesene Nachrichten, Meine Aktivitaeten
  - Gruppieren nach: Vertriebsmitarbeiter, Kunde, Endkunde, Produktkategorie, Auftragsdatum
  - Filter "Kostenvoranschlag gesendet" per Klick gesetzt (2 Auftraege) und wieder entfernt
  - Gruppierung "Vertriebsmitarbeiter" per Klick gesetzt (gruppierte Liste)
  - Suchfeld: Eingabe der Auftragsnummer S00203 liefert den Auftrag, Begriff erscheint als Facette
  - keine Schreibvorgaenge: nur Suchen, Filtern, Gruppieren in der Ansicht
Screenshots: Desktop\Odoo18-Abnahme-Session121\16_Filter_Angebote_ohne_Default_lokal.png bis
             21_Suchfeld_lokal.png (lokal) und _vm.png (VM)
```

### 6.1 Nachweis, dass keine Odoo-18-Funktion entfernt wurde

`scripts/vergleiche_verkauf_suche_vorher_nachher.py` vergleicht die Suchansichten je Menueaktion
vor und nach der Ergaenzung (Rohdaten `docs/_verkauf_teil3_suche_vorher.json` und
`docs/_verkauf_teil3_suche.json`, beide gitignoriert). Ergebnis fuer Odoo 18 lokal und VM:

```
Aktion 429 Verkaufsauftraege     +2 Filter, Gruppierungen 5 unveraendert, Suchfelder 6 unveraendert
Aktion 430/431 Angebote          +4 Filter, Gruppierungen 5 unveraendert, Suchfelder 8 unveraendert
                                 Kontext: {'search_default_my_quotation': 1} -> {} (gewollt)
Aktion 432/433 Abzurechnen/Upsell +2 Filter, Gruppierungen 3 unveraendert, Suchfelder 5 unveraendert
ERGEBNIS: keine Odoo-18-Funktion entfernt, nur Ergaenzungen.
Zusaetzlich geprueft: Ansichtsarten (list, kanban, calendar, pivot, graph, activity) und Domains
  der Menueaktionen unveraendert; das Odoo-18-Suchfeld "Kampagne" und die Datumsfilter
  ("Erstellt am", "Auftragsdatum") weiterhin vorhanden; benutzerdefinierte Filter und
  Gruppierungen (Suche speichern) unberuehrt.
```

## 7. Hinweis zur Sperre (Entscheidung von Anna, 28.09.2026)

Nur dokumentarisch festgehalten, keine Datenmigration:

- Bestaetigte Verkaufsauftraege waren in Odoo 11 bearbeitbar (Zustand `sale`, kein Sperrfeld).
- Odoo 18 verwendet zusaetzlich das Feld `locked`; in der Testdatenbank ist "Bestellungen
  automatisch sperren" aktiv, ein bestaetigter Auftrag ist dort sofort gesperrt.
- Es wird keine Importregel auf Produktivdaten angewendet und es werden keine der 2.463
  Odoo-11-Auftraege uebernommen oder veraendert. Die Zuordnung in
  `migration/verkauf_migrationsregeln.json` (Abschnitt `statuswechsel`) ist reine Vorbereitung.

**STATUS: TEIL 3, SCHRITT 4 - Suchfelder, Filter, Gruppierungen und Suche ABGENOMMEN
(lokal und VM).**

```
VM-Abnahme 28.09.2026 (Buer-Zugang, Git-Stand 3e15474):
  Modul-Upgrade itk_sale_management 18.0.1.3.0 auf der VM          ohne Fehler
  verify_s121_verkauf_teil3_filter.py  Odoo 11 43 + lokal 78 + VM 78 = 199 OK / 0 FEHL
  browser_verkauf_filter_suche.py      VM 19 OK / 0 FEHL, 0 JS- / 0 RPC-Fehler
  Vorher/Nachher-Vergleich             keine Odoo-18-Funktion entfernt, nur Ergaenzungen
                                       (scripts/vergleiche_verkauf_suche_vorher_nachher.py)
  keine Schreibvorgaenge auf der VM: nur Suchen, Filtern, Gruppieren in der Ansicht
```
