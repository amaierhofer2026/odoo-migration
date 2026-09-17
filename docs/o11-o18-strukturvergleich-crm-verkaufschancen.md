# Strukturvergleich Odoo 11 Prod ↔ Odoo 18: CRM → Verkaufschancen

Stand: 15.09.2026 (Session 114)
Quellen: Odoo 11 Prod `portal.it-kommunal.at` (DB `ITK_V1_a`, nur gelesen) und Odoo 18 (lokal + VM `k001959vsx.ipax.at`, DB `odoo18_test`)

Auftrag von Anna: CRM-Verkaufschancen migrationsgerecht vorbereiten (Stufen, Vertriebsteams, Verlustgründe, Felder der
Verkaufschance), **keine** Datenmigration, eindeutige Unterschiede direkt beheben, moderne Odoo-18-Logik beibehalten.

## 1. Wichtige Zahl-Korrektur vorab

Der bisher notierte Wert "**6.966 Verkaufschancen**" aus Session 101 war die **Gesamtzahl aller `crm.lead`-Datensätze**
(Interessenten **und** Chancen). Live gegen Odoo 11 Prod geprüft:

| Objekt | Anzahl |
|---|---|
| `crm.lead` gesamt | **6.967** (6.988 inkl. archivierter) |
| davon Typ **`lead`** (Interessent) | **6.608** |
| davon Typ **`opportunity`** (Verkaufschance) | **359** (379 inkl. archivierter) |

Für die Migration sind also **359 Verkaufschancen** und **6.608 Interessenten** getrennt zu betrachten. Beide werden
jetzt **nicht** übernommen. Odoo 18 enthält aktuell 1 `crm.lead` (Typ `lead`, Testdatensatz).

## 2. CRM-Stufen

### 2.1 Live-Vergleich (Odoo 11 Prods gegen Odoo 18)

| Reihenfolge Odoo 11 | Odoo 11 Name | Chancen O11 | Gewinnwahrsch. O11 | Odoo-18-Ziel | Odoo 18 seq | is_won | fold |
|---|---|---|---|---|---|---|---|
| 1 | New | 9 | 10 % | **Neu** (id 1) | 1 | nein | nein |
| 2 | Angebotsphase | 10 | 10 % | **Angebotsphase** (id 2) | 2 | nein | nein |
| 3 | On-Hold | 1 | 10 % | **On-Hold** (id 3) | 3 | nein | nein |
| 4 | **Angebot ausgesendet** | **2** | 10 % | **NEU ANGELEGT** (id 21) | **4** | nein | nein |
| 5 | Positive Rückmeldung | 0 | 10 % | **Positive Rückmeldung** (id 17) | 5 | nein | nein |
| 6 | Won | 1 | 100 % | **Erfolgreich** (id 4) | 6 | **ja** | nein |
| 7 | Verloren | 130 | 0 % | **Verloren** (id 19) | 7 | nein | **ja** |
| 8 | Zur Verrechnung bereit | 0 | 10 % | **Zur Verrechnung bereit** (id 18) | 8 | nein | nein |
| 9 | Verrechnet | 206 | 10 % | **Verrechnet** (id 20) | 9 | nein | **ja** |

**Befund:** In Odoo 18 fehlte die Stufe **"Angebot ausgesendet"** (die Annahme aus Session 101 ist bestätigt). Sie wurde
angelegt; die Reihenfolge der Odoo-18-Stufen entspricht jetzt der Odoo-11-Reihenfolge.

**Technische Unterschiede, die bleiben (moderne Odoo-18-Logik):**

- **Gewinnwahrscheinlichkeit** liegt in Odoo 18 **nicht** mehr an der Stufe, sondern am Datensatz
  (`crm.lead.probability`, Typ float, beschreibbar). Die Odoo-11-Stufenwerte (10 % / 100 % / 0 %) haben daher kein
  Stufen-Gegenstück; sie sind bei der späteren Migration am jeweiligen Datensatz zu setzen.
- **`fold`** (in der Kanban eingeklappt) ist in Odoo 18 bei "Verloren" und "Verrechnet" gesetzt, in Odoo 11 bei keiner
  Stufe. Das ist Odoo-18-Standardverhalten für abgeschlossene Stufen und bleibt erhalten (Entscheidung siehe Abschnitt 6).
- **`is_won`** gibt es nur in Odoo 18 ("Erfolgreich" = gewonnen). In Odoo 11 wurde "gewonnen" über die 100 %-Stufe
  abgebildet. Entsprechung ist eindeutig.

### 2.2 Wo die Stufen künftig gepflegt werden

Die Stufen sind **im Repo** definiert und werden bei jedem Modul-Upgrade idempotent nachgezogen:

- `addons/itk_crm/data/crm_stages.xml` (Namen, Reihenfolge, fold/is_won)
- `addons/itk_crm/setup_runtime.py` → `_STAGES` und `_setup_stage_labels()`
- `addons/itk_crm/migrations/18.0.1.5.2/post-migration.py` (zieht die Änderung bei Bestandsdatenbanken nach)

Modulversion: **`itk_crm` 18.0.1.5.2**.

## 3. Vertriebsteams (Kanäle)

### 3.1 Verwendung in Odoo 11 Prod

| Odoo-11-ID | Team | Leiter O11 | Mitglieder | **Verkaufschancen** | Odoo-18-Ziel |
|---|---|---|---|---|---|
| 1 | Vertriebskanäle (Intern) | – | 35 | **276** | neu angelegt (id 5) |
| 8 | Interne Weitergabe | – | 0 | **74** | neu angelegt (id 6) |
| 6 | Persönlicher Kontakt | Breit Christiane | 1 | **3** | neu angelegt (id 7), Leiter gesetzt |
| 2 | Webseite | – | 0 | **2** | entspricht dem Odoo-18-Team **Website** (id 2) → **aktiviert** |
| 3 | Webinar | Breit Christiane | 0 | **2** | neu angelegt (id 8), Leiter gesetzt |
| 4 | Newsletter | Breit Christiane | 0 | **1** | vorhandenes Team **Newsletter** (id 4), Leiter auf Breit Christiane gesetzt |
| 5 | Telefon | Breit Christiane | 0 | **1** | neu angelegt (id 9), Leiter gesetzt |
| 7 | Suche / Liste | – | 0 | **0** | **nicht angelegt** (kein Nachbau unbenutzter Teams) |

Summe der Chancen mit Team: **359** (alle Chancen haben ein Team). Chancen ohne Team: 0.

### 3.2 Fachliche Bewertung / 1:1-Abbildbarkeit

- **Teamnamen** sind 1:1 abbildbar. Einzige Abweichung: Odoo 11 "Webseite" entspricht dem Odoo-18-Standardteam
  "Website" (dieselbe Bedeutung, kein neues Team nötig).
- **Verkaufschancen je Team** lassen sich damit vollständig zuordnen (Zuordnungsschlüssel: Teamname).
- **Teamleiter:** in Odoo 11 nur bei 4 Teams gesetzt (alle "Breit Christiane"); der Benutzer existiert in Odoo 18
  und wurde als Leiter gesetzt. Die Odoo-18-Teams "Sales" und "Point of Sale" sind Odoo-Standardteams ohne
  Odoo-11-Entsprechung (bleiben unverändert).
- **Mitgliedschaften** (Odoo 11: 35 Mitglieder im Team "Vertriebskanäle (Intern)") wurden **nicht** übernommen – das
  ist eine Benutzerzuordnung und gehört zur späteren Migration (offener Punkt).

Angelegt wurde über `addons/itk_crm/setup_runtime.py` → `_setup_crm_teams()` (idempotent, im Repo gepflegt).

## 4. Verlustgründe

| Odoo 11 Name | Odoo-11-Nutzung (Chancen) | Odoo 18 |
|---|---|---|
| Too expensive | 0 | vorhanden (id 1) |
| Im Moment keinen Bedarf | 0 | vorhanden (id 2) |
| Bedarf zu gering | 0 | vorhanden (id 4) |
| Später kontaktieren | 0 | vorhanden (id 5) |
| Mitbewerb | 0 | vorhanden (id 6) |
| – | – | zusätzlich "Not enough stock" (id 3, Odoo-Standard) |

**Befund:** Das Feld `lost_reason` ist in Odoo 11 **bei keiner** der 359 Chancen gesetzt (auch nicht bei den 130
Chancen in der Stufe "Verloren"). Alle fünf in Odoo 11 vorhandenen Namen existieren in Odoo 18 bereits – es musste
**nichts** angelegt werden.

**Feldname:** Odoo 11 `crm.lead.lost_reason` (Label "Ablehnugsgrund") → Odoo 18 **`crm.lead.lost_reason_id`**
(Label "Verlustgrund"). Modell in beiden `crm.lost.reason`.

## 5. Feld-Mapping der Verkaufschance

| Odoo-11-Feld | Odoo-18-Zielfeld | Typ / Relation | Zuordnung |
|---|---|---|---|
| `partner_id` | `partner_id` | many2one `res.partner` | **1:1** (336 von 359 Chancen belegt) |
| `name` | `name` | char | **1:1** (Label O11 "Chance", O18 "Verkaufschance") |
| `user_id` | `user_id` | many2one `res.users` | **1:1** (357 belegt); Benutzerzuordnung nötig (Label O11 "Verkäufer", O18 "Vertriebsmitarbeiter") |
| `team_id` | `team_id` | many2one `crm.team` | **1:1 + Stammdaten-Mapping** (Abschnitt 3) |
| `stage_id` | `stage_id` | many2one `crm.stage` | **1:1 + Stammdaten-Mapping** (Abschnitt 2) |
| `planned_revenue` | **`expected_revenue`** | O11 float → **O18 monetary** | **Transformation** (Feld umbenannt und Typ geändert; 304 Chancen mit Umsatz > 0) |
| `probability` | `probability` | float | **1:1** (359 belegt) |
| `priority` | `priority` | selection | **1:1** (359 belegt) |
| `date_deadline` | `date_deadline` | date | **1:1** (145 belegt) |
| `lost_reason` | **`lost_reason_id`** | many2one `crm.lost.reason` | **Transformation** (Feld umbenannt; 0 belegt) |
| `tag_ids` | `tag_ids` | many2many; O11 `crm.lead.tag` → **O18 `crm.tag`** | **Transformation** (Modell umbenannt; 117 belegt) → Tag-Stammdaten-Mapping nötig |
| `description` | `description` | O11 **text** → O18 **html** | **Transformation** (194 belegt) |
| `date_closed` | `date_closed` | datetime | **1:1**, in Odoo 18 schreibgeschützt → technischer Importweg (190 belegt) |
| `date_open`, `date_last_stage_update` | gleichnamig | datetime | **1:1**, in Odoo 18 schreibgeschützt → technischer Importweg |
| `contact_name`, `email_from`, `phone`, `campaign_id`, `medium_id`, `source_id` | gleichnamig | char / many2one `utm.*` | **1:1** |
| `message_ids` (Chatter) | `message_ids` | one2many `mail.message` | **1:1** (358 von 359 belegt); Anhänge hängen am Chatter (kein eigenes `attachment_ids`-Feld, in beiden Systemen) |
| `active`, `type` | gleichnamig | boolean / selection | **1:1** |
| `kanban_state`, `date_action_last` | – | selection / datetime | **entfällt** in Odoo 18 |
| – | `expected_revenue` (Ziel von `planned_revenue`), `lost_reason_id` (Ziel von `lost_reason`) | monetary / many2one | **neu in Odoo 18** (nur umbenannt, siehe oben) |

**Keine Datenmigration:** Es wurden **keine** der 359 Verkaufschancen und **keine** der 6.608 Interessenten übernommen.

## 6. KLÄRUNG NÖTIG (fachliche Entscheidungen)

1. **Interessenten (`lead`, 6.608 Stück):** Nicht Teil dieses Auftrags – zu entscheiden, ob und nach welcher Regel sie
   migriert werden (analog zur selektiven Ticket-Migration).
2. **Selektive Migration der Chancen:** Nach welcher Regel werden die 359 (bzw. 379 inkl. archivierter) Chancen
   übernommen? Alte, abgeschlossene Verkaufschancen (Stufe "Verrechnet": 206, "Verloren": 130) sollten – wie bei den
   Tickets – nicht automatisch mitkommen.
3. **Stufe "Verrechnet":** Sie ist in Odoo 18 eingeklappt (`fold`) und **nicht** als gewonnen markiert (`is_won`),
   enthält aber 206 der 359 Chancen. Fachlich zu klären: Ist "Verrechnet" gewonnen (dann `is_won`), und soll die
   Stufe im Kanban sichtbar bleiben (dann `fold` aus)?
4. **Gewinnwahrscheinlichkeit:** Die Odoo-11-Stufenwerte (10/100/0 %) haben in Odoo 18 kein Stufen-Gegenstück.
   Soll beim Migrieren die Wahrscheinlichkeit je Chance gesetzt werden (z. B. aus der Odoo-11-Stufe abgeleitet)?
5. **Team-Mitgliedschaften:** Odoo 11 hat 35 Mitglieder im Team "Vertriebskanäle (Intern)". Nicht übernommen –
   Entscheidung im Rahmen der Benutzerzuordnung.
6. **Beschriftungen (Wortlaute):** Odoo 18 nennt Stufen "Phase", `user_id` "Vertriebsmitarbeiter", `team_id`
   "Verkaufsteam", `lost_reason_id` "Verlustgrund"; Odoo 11 nannte sie "Stufe", "Verkäufer", "Vertriebskanal",
   "Ablehnugsgrund". Die Odoo-18-Wortlaute wurden **nicht** geändert (moderne, konsistente Odoo-18-Terminologie).
   Auf Wunsch Umstellung auf die Odoo-11-Wortlaute.
7. **Tags:** Für die 117 Chancen mit Stichwörtern ist ein Tag-Mapping von `crm.lead.tag` (Odoo 11) auf `crm.tag`
   (Odoo 18) zu erstellen.
8. **Chancen in Stufe "Verloren" (130) haben keinen Verlustgrund** – die Information ist in Odoo 11 nicht gepflegt;
   zu entscheiden, ob beim Migrieren ein Standard-Verlustgrund gesetzt wird (bitte nicht raten).

## 7. Nachweis

`scripts/verify_s114_crm_chancen.py` (read-only) prüft Stufen (Namen, Reihenfolge, `is_won`, `fold`), Teams
(vorhanden/aktiv/Leiter), Verlustgründe, die Feldnamen und Typen des Chancen-Formulars sowie die Versionsumbrüche
(`planned_revenue` → `expected_revenue`, `lost_reason` → `lost_reason_id`, `crm.lead.tag` → `crm.tag`).
Zusätzlich Browser-Prüfung auf der VM.
