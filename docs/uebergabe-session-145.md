# Uebergabe Session 145 - CRM / Verkaufschancen

Stand: 18.11.2026. Branch `feature/crm-migration-s145` ist als PR #274 nach `main`
gemergt (main = 2c93ce7). Die VM laeuft auf diesem Stand.

## Was fertig und belegt ist

**Struktur und Stammdaten**
- Neun Stufen mit Odoo-11-Namen, "Verrechnet" ist gewonnen (`is_won`), damit die
  Odoo-11-Bedeutung erhalten bleibt (195 gewonnene Vorgaenge, 192 davon in "Verrechnet").
- Acht Vertriebskanaele inklusive "Suche / Liste" und "Webseite" (vorher "Website"),
  `use_leads`/`use_opportunities` wie Odoo 11.
- Fuenf Ablehnungsgruende, zwoelf Aktivitaetstypen (fuenf ITK-eigene), Menue "Interessenten".
- ITK-Auswahlfelder tragen die Odoo-11-Schluessel: `x_Lead_Quelle` (24 Werte),
  `x_Produktinteresse` (10), `x_lead_status` (12), `x_Anrede_Lead`.
- ITK-Felder sind bei Interessenten *und* Verkaufschancen sichtbar (die Einschraenkung
  `invisible="type == 'opportunity'"` ist entfernt).

**Datenmigration** (`scripts/migration/crm_migration.py`, Trockenlauf als Standard,
Schreiben nur mit `--ausfuehren --ich-habe-freigabe`)
- 6.994 Vorgaenge (6.609 Interessenten, 385 Verkaufschancen, 21 archiviert)
- 44 Stichwoerter mit 6.327 Zuordnungen, 5 Gruende, 1 Medium, 32 Aktivitaeten
- 1.321 fachliche Chatter-Nachrichten (von 3.479; 2.158 reine Systemmeldungen ohne Text
  bleiben in Odoo 11), 204 Anhaenge mit 67,9 MB
- Erstellungs-/Bearbeitungsdatum und Ersteller/Letzter Bearbeiter ueber
  `itk.migration.zeitstempel` (Odoo 18 verwirft Log-Access-Felder im ORM)
- Ankerfelder in `itk_migration_keys` 18.0.1.1.3: `itk_o11_id` (crm.lead, stage, team,
  tag, lost.reason, utm.*, mail.activity.type), `itk_o11_msg_id`, `itk_o11_att_id`,
  `itk_o11_activity_id`

**Verkaeuferzuordnung - 0 offen**
`BENUTZER_MAPPING` im Skript, nie ueber Datenbank-IDs:
- Odoo-11-Benutzer 87 (Anna Maierhofer) -> bestehendes Konto Administrator, 8 Vorgaenge.
  Das Administrator-Konto ist unveraendert (kein neues Konto, keine Umbenennung, keine
  Rechteaenderung). In Odoo 18 existiert zusaetzlich ein Konto "Maierhofer Anna" - es ist
  bewusst *nicht* das Ziel.
- Odoo-11-Benutzer 20 (veralteter Login `lorenz.galler@...`) -> Breiteneder Lorenz,
  137 Vorgaenge.
- Odoo-11-Benutzer 80 (Sammelkonto, keine Person) -> als inaktiver historischer Benutzer
  angelegt (Login `aco-market@it-kommunal.at`), 1 Vorgang.
- 6.821 Vorgaenge ueber Login, 4 ueber Anzeigename. 27 Vorgaenge hatten schon in Odoo 11
  keinen Verkaeufer.

**Nachweise**
- Lokal: Abgleich deckungsgleich (Umsatz 1.195.320,35 EUR, Partner 0 Abweichungen),
  einzig 3 Vorgaenge ohne Stufe stehen auf "Neu" (dokumentierte Mappingregel).
- Lokal Idempotenz: 0 angelegt, 0 aktualisiert, 6.994 uebersprungen, 0 Fehler,
  0 Dubletten.
- Lokal Browser: 55 OK / 0 FEHL, Chatter mit 28 Nachrichten und Anhang sichtbar.
- Lokal Rechte: 22 OK / 0 FEHL (CRM-Benutzer, Verkaufsleiter, Administrator).
- VM: Modul-Upgrade, Migration 6.994 Vorgaenge + 1.321 Nachrichten + 204 Anhaenge,
  zweiter Lauf 0/0/0, Abgleich deckungsgleich, Browser 55 OK / 0 FEHL,
  Rechte 22 OK / 0 FEHL. Ein VM-Testrest ohne Odoo-11-Bezug ("Test-Interessenten",
  12.08.2026) wurde entfernt.
- Regression lokal: 725 OK / 9 FEHL, alle neun als Werkzeuggrenze belegt
  (`docs/o11-o18-vergleich-crm.md`, Abschnitt 7a).

## Was noch fehlt

1. Regression der gesperrten Bereiche **auf der VM** (`scripts/regression_gesperrte_bereiche.py
   --instanz vm`, elf Bereiche, rund eine Stunde).
2. Nach dem naechsten Commit: VM auf den neuen `main` ziehen; die Skript-Korrekturen dieser
   Runde (Blockabfragen, Rechte-Erwartungen, Stackdump, Regressionsrunner) sind noch nicht
   committet.
3. Checkliste und PROJECT_KNOWLEDGE um den CRM-Abschluss ergaenzen.
4. Dreistand lokal = GitHub main = VM nachweisen.
5. Erst dann CRM auf "ABGENOMMEN UND GESPERRT" setzen.

## Stolpersteine, die Zeit gekostet haben

- **Einzelabrufe ueber VPN**: `read` je Vorgang (6.994 Aufrufe) und
  `search_read` ueber 30.000 Partner wirken wie ein Haenger (45+ Minuten ohne Ausgabe).
  Jetzt blockweise (`ids_map`, `VERGLEICHSFELDER`-Cache, Zeitstempel in 500er-Bloecken):
  Laufzeit rund 2,5 Minuten. `ITK_STACKDUMP=1` druckt bei Bedarf alle 120 s den Stack.
- **Aktivitaeten waren nicht idempotent**: Typ/Benutzer/Frist/Text ist kein eindeutiger
  Schluessel (Odoo 18 speichert Summary und Notiz anders). Jetzt ueber
  `itk_o11_activity_id`.
- **Rechtepruefung**: `base.group_system` allein hat in Odoo 18 keinen CRM-Zugriff; das
  reale Administratorkonto ist Systemadmin *und* Verkaufsadministrator. Die Erwartungen
  je Rolle stehen jetzt im Skript (CRM-Benutzer sieht fremde Vorgaenge nicht und darf
  nicht loeschen - Odoo-18-Standard, keine Rechteausweitung).
- **Regressionstest Kontakte**: oeffnet den ersten `crm.lead`, der nach der Migration eine
  Verkaufschance ist, und sucht dort Interessenten-Beschriftungen. Werkzeugfehler, kein
  Produktfehler - Browserbeleg in `docs/o11-o18-vergleich-crm.md`.

## Zahlen zum Nachschlagen

| Kennzahl | Odoo 11 | Odoo 18 lokal | Odoo 18 VM |
|---|---|---|---|
| Vorgaenge | 6.994 | 6.994 | 6.994 |
| aktiv / archiviert | 6.973 / 21 | 6.973 / 21 | 6.973 / 21 |
| Interessenten / Chancen | 6.609 / 385 | 6.609 / 385 | 6.609 / 385 |
| ohne Verkaeufer | 27 | 27 | 27 |
| ohne Stufe | 3 | 0 (auf "Neu") | 0 (auf "Neu") |
| Stichwoerter (Zuordnungen) | 44 (6.327) | 44 (6.327) | 44 (6.327) |
| Aktivitaeten | 32 | 32 | 32 |
| fachliche Nachrichten | 1.321 | 1.321 | 1.321 |
| Anhaenge | 204 (67,9 MB) | 204 (67,9 MB) | 204 (67,9 MB) |
| Umsatz (327 Vorgaenge) | 1.195.320,35 | 1.195.320,35 | 1.195.320,35 |

## Nicht migriert (Begruendung)

- 2.158 reine Systemnachrichten ohne Text (Stufenwechsel, "Interessent wurde erstellt",
  "Chance gewonnen"). Fachliche Nachrichten sind vollstaendig uebertragen.
- `utm.source` (220 Datensaetze) und `utm.campaign` (16): 0 von 6.994 Vorgaengen nutzen
  sie. Das genutzte Medium "Website" (25 Vorgaenge) ist migriert.
