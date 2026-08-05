# CRM-Teams / Vertriebskanäle: Odoo 11 → Odoo 18 Mapping

Erstellt: 04.08.2026
Quelldaten: JSON-RPC Odoo 11 (ITK_V1_a) + Odoo 18 (odoo18_test)
Status: ANALYSE — keine Migration ohne Freigabe

---

## 1. Odoo 11: Bestandsaufnahme crm.team

### 1.1 Alle Teams (8)

| ID | Name | Typ | Leiter | Mitglieder | Leads |
|----|------|-----|--------|------------|-------|
| 1 | Vertriebskanäle (Intern) | sales | — | 35 User | 601 |
| 2 | Webseite | website | — | — | 2 |
| 3 | Webinar | sales | Breit Christiane (46) | — | 4 |
| 4 | Newsletter | sales | Breit Christiane (46) | — | 9 |
| 5 | Telefon | sales | Breit Christiane (46) | — | 1 |
| 6 | Persönlicher Kontakt | sales | Breit Christiane (46) | Würrer Florian (15) | 5.626 |
| 7 | Suche / Liste | sales | — | — | 633 |
| 8 | Interne Weitergabe | sales | — | — | 56 |

**Gesamt:** 8 Teams, 6.932 Leads

### 1.2 Team-Details

#### Vertriebskanäle (Intern) — Mitglieder (35 User)
```
33 — Abfallverband Schwechat         1  — Administrator
43 — ausgeschieden/Horniak Günter    16 — ausgeschieden/Koch Katharina
19 — ausgeschieden/Steinecker Julia  41 — ausgeschieden/Vercimak Daniel
20 — Breitenender Lorenz             54 — dd
26 — GDV Region Amstetten            28 — GVA Bruck/Leitha
27 — GVA Baden                       31 — GVA Mödling
34 — GVA Waidhofen/Thaya             37 — GV Horn
29 — GV Krems                        30 — GVU Melk
32 — GVU Scheibbs                    35 — GV Zwettl
21 — IT-Kommunal                     60 — Mobilitätsverbünde Österreich
6  — Niederösterreich GemDAT          7 — Oberösterreich GemDAT
58 — Pellkvist Tobias                42 — PSC
23 — RIS                             18 — Ronald Sallmann
36 — rubicon IT GmbH                 12 — Sales GSZ Kärnten
14 — Sales ÖSTB Burgenland           55 — Sales ÖSTB Steiermark
45 — Sallmann Alexander              17 — Soritz Gerd
71 — Tiefling Agnes                  57 — VVT Tirol
10 — Waiss Martina
```

### 1.3 crm.team Modell (Odoo 11)

Relevante Felder:

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| name | char | Sales Channel (Anzeigename) — REQUIRED |
| team_type | selection | Channel Type ('sales'/'website') — REQUIRED |
| user_id | many2one → res.users | Channel Leader |
| member_ids | one2many → res.users | Channel Members |
| active | boolean | Aktiv |
| use_leads | boolean | Leads nutzen |
| use_opportunities | boolean | Pipeline nutzen |
| alias_id | many2one → mail.alias | E-Mail-Alias — REQUIRED |
| company_id | many2one → res.company | Unternehmen |
| color | integer | Farb-Index |
| reply_to | char | Reply-To E-Mail |
| favorite_user_ids | many2many → res.users | Favoriten |
| is_favorite | boolean | Auf Dashboard zeigen |

---

## 2. Odoo 18: Aktueller Stand crm.team

### 2.1 Vorhandene Teams

| ID | Name | Typ | Mitglieder |
|----|------|-----|------------|
| 1 | Sales | sales | 1 (Administrator) |

**Nur das Odoo-18-Default-Team existiert. Keine ITK-Teams angelegt.**

### 2.2 crm.team Modell (Odoo 18)

Felder im Vergleich zu Odoo 11:

| Status | Feld |
|--------|------|
| ✅ identisch | name, user_id, member_ids, active, use_leads, use_opportunities, team_type, company_id, color, reply_to |
| ⚠️ verschoben | alias_id → alias_name + alias_domain (anderes Alias-Modell) |
| ❌ entfällt | is_favorite, favorite_user_ids (Odoo 18 hat Dashboard-Favoriten anders) |
| ❌ entfällt | dashboard_graph_* (Odoo 18 hat eigenes Dashboard-System) |
| ✅ neu in O18 | assignment_domain (automatische Zuweisungsregeln) |
| ✅ neu in O18 | crm_lead_count, opportunities_count (computed) |

---

## 3. Mapping-Plan: Odoo 11 → Odoo 18

### 3.1 Team-Erstellung (8 Teams)

| Seq | O11 Name | O18 Aktion | Anmerkung |
|-----|----------|-----------|-----------|
| 1 | Vertriebskanäle (Intern) | create(name, team_type='sales') | Hauptteam, 35 Mitglieder |
| 2 | Webseite | create(name, team_type='website') | use_leads=False, use_opp=False |
| 3 | Webinar | create(name, team_type='sales') | Breit Christiane als Leiter |
| 4 | Newsletter | create(name, team_type='sales') | Breit Christiane als Leiter |
| 5 | Telefon | create(name, team_type='sales') | Breit Christiane als Leiter |
| 6 | Persönlicher Kontakt | create(name, team_type='sales') | Breit Christiane + Würrer Florian |
| 7 | Suche / Liste | create(name, team_type='sales') | Kein Leiter |
| 8 | Interne Weitergabe | create(name, team_type='sales') | Kein Leiter |

### 3.2 Benutzer-Mapping (kritisch)

⚠️ **Abhängigkeit von Kontaktmigration:**
- `user_id` (Channel Leader) → muss auf existierende res.users in Odoo 18 verweisen
- `member_ids` (Channel Members) → müssen als res.users in Odoo 18 existieren
- Ohne migrierte Benutzer können Teams NUR mit Namen angelegt werden, OHNE Mitglieder/Leiter

**Aktueller Stand Odoo 18:**
- Nur 1 Benutzer: Administrator (id=2, anna.maierhofer@it-kommunal.at)
- Keine der 35+ Odoo-11-Benutzer existieren in Odoo 18

### 3.3 Abhängigkeiten

```
CRM-Teams anlegen
  ├── Benutzer müssen existieren (user_id, member_ids)
  │   └── ⚠️ BLOCKIERT: Kontaktmigration nicht freigegeben
  ├── mail.alias wird automatisch erstellt (alias_name)
  │   └── ✅ Kein Blocker
  └── crm.lead.team_id wird bei Lead-Migration gesetzt
      └── ⚠️ BLOCKIERT: Lead-Migration nicht freigegeben
```

---

## 4. Migrationsreihenfolge (wenn freigegeben)

1. **Benutzer anlegen** (res.users) → alle 35+ O11-Benutzer
2. **Teams anlegen** (crm.team) → 8 Teams mit Namen + Typ
3. **Team-Leiter zuweisen** (crm.team.user_id) → Breit Christiane für 4 Teams
4. **Team-Mitglieder zuweisen** (crm.team.member_ids) → 35 User zu "Vertriebskanäle (Intern)"
5. **Leads migrieren** (crm.lead) → team_id per Team-Namen mappen

---

## 5. Vergleich mit früherer Analyse (crm_structure_mapping.md)

Die Datei `docs/crm_structure_mapping.md` (28.07.) dokumentierte bereits:
- "Alle 8 O11-Teams per Name in O18 angelegt (JSON-RPC)"

⚠️ **Dies war eine temporäre Analyse/Prototyp.** Die Teams wurden NIE dauerhaft in Odoo 18 angelegt. Der aktuelle Stand (04.08.) zeigt nur das Default-Team "Sales" (id=1).

---

## 6. Nächste Schritte

- [ ] Auf Freigabe der Kontaktmigration warten
- [ ] Benutzer-Mapping O11→O18 erstellen (welche User werden übernommen?)
- [ ] Team-Struktur in Odoo 18 per JSON-RPC oder XML-Daten anlegen
- [ ] Leads-Team-Zuordnung bei Datenmigration berücksichtigen
