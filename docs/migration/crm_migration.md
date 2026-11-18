# CRM-Migration: `scripts/migration/crm_migration.py`

Technische Dokumentation des Skripts, das die CRM-Daten (Interessenten und
Verkaufschancen) aus Odoo 11 in Odoo 18 uebertraegt. Erstellt und ausgefuehrt im
Rahmen des ITK-Migrationsprojekts unter Freigabe von Anna Maierhofer
(Session 145, 17.11.2026).

## 1 Quelle und Ziel

| | |
|---|---|
| Quelle | Odoo 11 Produktion `https://portal.it-kommunal.at`, DB `ITK_V1_a` - **nur lesend** |
| Ziel | Odoo 18, DB `odoo18_test`, lokal (`http://localhost:8069`) oder VM (`https://k001959vsx.ipax.at`) |
| Zugangsdaten | ausschliesslich aus der lokal nicht versionierten `.env` (`ODOO11_*`, `ODOO18_*`) ueber `scripts/_o11o18_client.py` |

## 2 Umfang

Migriert werden:

- 9 CRM-Stufen (Zuordnung ueber den Namen; die Odoo-18-Stufen tragen dieselben Namen)
- 8 Vertriebskanaele (Zuordnung ueber den Namen; fehlende Teams legt `itk_crm` an)
- 44 Stichwoerter (`crm.lead.tag` -> `crm.tag`, Zuordnung ausschliesslich ueber den Namen)
- 5 Ablehnungsgruende (`crm.lost.reason`, Zuordnung ueber den Namen)
- 1 verwendetes Medium (`utm.medium` "Website"); die uebrigen 8 sind unbenutzt
- 12 Aktivitaetstypen (Zuordnung ueber den Namen, Alias "Zu erledigen" -> "To-Do")
- 6.994 Interessenten und Verkaufschancen, inklusive 21 archivierter Datensaetze
- 32 offene Aktivitaeten auf diesen Vorgaengen
- 1.321 fachliche Chatter-Nachrichten (von 3.479; 2.158 reine Systemmeldungen ohne
  Text werden bewusst nicht uebertragen)
- 204 Anhaenge (67,9 MB, fachliche Dokumente)

Nicht migriert (bewusste Entscheidung, siehe Bereichsdokument Abschnitt 4):

- 2.158 reine Systemnachrichten ohne Text (Stufenwechsel, "Interessent wurde
  erstellt", "Chance gewonnen"); die fachlichen Nachrichten sind vollstaendig uebertragen
- `utm.source` (220) und `utm.campaign` (16), weil kein Vorgang sie referenziert
- `kanban_state`, `opt_out`, `day_open`, `day_close` (in Odoo 18 nicht vorhanden bzw. berechnet)
- Favoriten (`ir.filters`, 17) und die Odoo-11-E-Mail-Automationen

## 3 Voraussetzungen

1. Modul `itk_migration_keys` >= 18.0.1.1.0 installiert (Feld `itk_o11_id` auf
   `crm.lead`, `crm.stage`, `crm.team`, `crm.tag`, `crm.lost.reason`, `utm.*`,
   `mail.activity.type`).
2. Modul `itk_crm` >= 18.0.1.6.1 installiert: Team "Suche / Liste", Odoo-11-Wortlaute
   der Ablehnungsgruende, Aktivitaetstypen, Auswahlwerte der ITK-Felder mit den
   Odoo-11-Schluesseln, `is_won` der Stufe "Verrechnet".
3. Kontakte sind migriert (`scripts/migration/kontakte_migration.py`), weil
   `partner_id` ueber `res.partner.itk_o11_id` zugeordnet wird.
4. `.env` mit Odoo-11- und Odoo-18-Zugang.

## 4 Aufruf

Trockenlauf (Standard, schreibt nichts):

```
python scripts/migration/crm_migration.py --instanz lokal
python scripts/migration/crm_migration.py --instanz vm --mapping "%LOCALAPPDATA%\Temp\crm_mapping_vm.json"
```

Schreiblauf (nur mit beiden Schaltern):

```
python -u scripts/migration/crm_migration.py --instanz lokal --ausfuehren --ich-habe-freigabe \
    --mapping "%LOCALAPPDATA%\Temp\crm_mapping_lokal.json"
```

Weitere Schalter: `--grenze N` (nur die ersten N Vorgaenge, fuer Tests),
`--stammdaten nein` (nur Vorgaenge, ohne Stammdatenpflege).

Lange Laeufe als Hintergrundprozess mit Logdatei (`-u` ist Pflicht, sonst bleibt
die Logdatei bis zum Prozessende leer):

```
python -u scripts/migration/crm_migration.py --instanz vm --ausfuehren --ich-habe-freigabe \
    > "%LOCALAPPDATA%\Temp\crm_vm.log" 2>&1
```

## 5 Sicherheitsmechanismen

- Die Klasse `Schreibschutz` bricht jeden `create`/`write`/`unlink`/`copy` ab,
  solange `--ausfuehren` fehlt. Der Trockenlauf kann strukturell nicht schreiben.
- `--ausfuehren` allein genuegt nicht: ohne `--ich-habe-freigabe` bricht das Skript
  mit Exit-Code 2 ab.
- Odoo 11 wird nur ueber `search`, `search_read` und `read` angesprochen.
- Der Zielbestand wird immer mit `active_test=False` gelesen, damit archivierte
  Datensaetze erkannt und nicht doppelt angelegt werden.
- Fehler einzelner Datensaetze brechen den Lauf nicht ab, sondern werden mit
  Odoo-11-ID und Klartext gezaehlt und am Ende ausgegeben (Exit-Code 1, wenn Fehler
  aufgetreten sind).

## 6 Mapping

| Objekt | Schluessel | Begruendung |
|---|---|---|
| Vorgang | `itk_o11_id` | eindeutige technische Zuordnung, keine Dubletten bei Wiederholung |
| Chatter-Nachricht | `itk_o11_msg_id` auf `mail.message` | Nachrichten haben keinen fachlichen Schluessel |
| Anhang | `itk_o11_att_id` auf `ir.attachment` | Dateinamen sind nicht eindeutig |
| Aktivitaet | `itk_o11_activity_id` auf `mail.activity` | Typ/Benutzer/Frist/Text ist nicht eindeutig (Odoo 18 speichert Summary und Notiz anders ab) |
| Kontakt | `res.partner.itk_o11_id` | aus der Kontaktmigration vorhanden (275 von 275 referenzierten Kontakten) |
| Verkaeufer | **explizite Regel `BENUTZER_MAPPING`**, dann Login (klein geschrieben), dann Name | Odoo-11-Benutzer 20 hat einen veralteten Login (`lorenz.galler@...`), heisst aber "Breiteneder Lorenz" und ist in Odoo 18 als `lorenz.breiteneder@...` vorhanden. Eine reine Login-Zuordnung haette 137 Vorgaenge ohne Verkaeufer gelassen. |
| Stufe, Team, Stichwort, Ablehnungsgrund, Medium, Aktivitaetstyp | Name | Odoo-11- und Odoo-18-IDs sind nicht identisch; gleichnamige Ziele gelten als Konflikt |
| Bundesland | Name innerhalb Oesterreich | die `res.country.state`-IDs unterscheiden sich |
| Land | ISO-Code | |
| Anrede (Titel) | Name des `res.partner.title` | |

Auswahlwerte der ITK-Felder (`x_Anrede_Lead`, `x_Lead_Quelle`,
`x_Produktinteresse`, `x_lead_status`) werden unveraendert uebernommen. Werte, die
in der Odoo-11-Auswahl nicht mehr definiert sind (Altbestand, z. B.
`x_Lead_Quelle = web_iinform`), werden **nicht** erfunden, sondern leer gelassen,
gezaehlt und als Sonderfall protokolliert.

## 7 Sonderfaelle

| Fall | Behandlung |
|---|---|
| Archivierte Vorgaenge (21) | werden mit `active=False` angelegt bzw. aktualisiert |
| Vorgaenge ohne Stufe (3) | Stufe bleibt leer |
| Vorgaenge ohne Verkaeufer (27 in Odoo 11) | bleiben ohne Verkaeufer |
| Verkaeufer fehlt in Odoo 18 (1 Vorgang, Benutzer "ACO-Market") | kein Ersatzwert, als nicht zuordenbar gezaehlt |
| Auswahlwert nicht in der Auswahl | Feld leer, gezaehlt, mit Odoo-11-ID protokolliert |
| Aktivitaeten | nur uebertragen, wenn Vorgang und Aktivitaetstyp zugeordnet sind; Datum bleibt das Odoo-11-Datum (auch wenn es in der Vergangenheit liegt) |
| Doppelte Vorgangsnamen (782 Namen mehrfach, bis 24-mal) | unkritisch, weil ueber `itk_o11_id` zugeordnet wird |

## 7a Technischer Importweg fuer Erstellungsdatum und Bearbeitung

Odoo 18 entfernt `create_uid`, `create_date`, `write_uid` und `write_date` in
`models._sanitize_vals` aus jedem `create`/`write` - auch fuer den Administrator.
Ein ORM-Schreibzugriff kann diese Werte deshalb nicht setzen (in Session 145
belegt: Wert wird stillschweigend durch die Laufzeit ersetzt).

Loesung: das Modul `itk_migration_keys` stellt die TransientModel-Methode
`itk.migration.zeitstempel.setze_zeitstempel(modell, zeilen)` bereit. Sie fuehrt
ein gezieltes `UPDATE` auf einer festen Whitelist (`crm.lead`) aus und setzt
`create_date`, `write_date`, `date_open`, `create_uid` und `write_uid`. Das Skript
ruft sie blockweise (300 Zeilen) und nur fuer tatsaechlich abweichende Datensaetze
auf.

Damit traegt jeder migrierte Vorgang das Odoo-11-Erstellungsdatum, die letzte
Bearbeitung und den urspruenglichen Ersteller.

## 8 Validierung nach der Migration

Read-only Pruefung mit `scripts/migration/crm_abgleich.py`: Mengen je Typ, Stufe,
Team, Verkaeufer, Prioritaet, Status und Produktinteresse; Verteilung der
Stichwoerter, Partnerbezuege, Aktivitaeten und Summen. Das Skript schreibt nichts und
gibt nur Zaehlwerte aus.

Zusaetzlich im Bereichsdokument `docs/o11-o18-vergleich-crm.md` dokumentiert:
Zielwerte aus Odoo 11, Istwerte aus Odoo 18, Abweichungen mit Begruendung.

## 8a Felder, die Odoo 18 beim Schreiben normalisiert

Diese Felder werden bei der Anlage uebertragen, aber **nicht** im
Aktualisierungsvergleich nachgeschrieben - sonst meldet jeder Lauf dieselbe
Scheinabweichung und schreibt das Bearbeitungsdatum neu:

| Feld | Verhalten von Odoo 18 | Umgang |
|---|---|---|
| `website` | ergaenzt ein Schema (`www.x.at` -> `http://www.x.at`) | Wert bleibt migriert stehen, kein Nachschreiben |
| `phone`, `mobile` | formatiert ueber `phone_validation` um | Wert bleibt migriert stehen, kein Nachschreiben |
| `email_from` | wird bei gesetztem Kontakt neu abgeleitet (precompute) | nur leere Ziele werden gefuellt |
| `description` | HTML wird normalisiert | nur leere Ziele werden gefuellt |

Alle uebrigen Felder (Name, Typ, Stufe, Team, Verkaeufer, Kontakt, Prioritaet,
Wahrscheinlichkeit, erwarteter Umsatz, Fristen, Stichwoerter, ITK-Felder,
Bundesland, Land, Anrede, Ablehnungsgrund) werden feldweise verglichen und nur bei
echter Abweichung geschrieben.

## 9 Idempotenz

- Jeder Vorgang traegt `itk_o11_id`. Ein zweiter Lauf findet ihn ueber
  `search([('itk_o11_id','!=',False)], context={'active_test': False})`.
- Vorhandene Datensaetze werden feldweise verglichen; geschrieben wird nur, wenn
  sich ein Wert unterscheidet. Ausgenommen sind `create_date`, `write_date`,
  `create_uid`, `write_uid` (Herkunftsnachweis, wird nicht nachgezogen).
- Stammdaten werden ueber den Namen erkannt; fehlende Stichwoerter werden einmal
  angelegt und danach ueber `itk_o11_id` wiedergefunden.
- Aktivitaeten werden ueber die Kombination (Vorgang, Typ, Benutzer, Frist,
  Zusammenfassung) erkannt.
- Erwartung fuer den zweiten Lauf: `angelegt = 0`, `Dubletten = 0`, `Fehler = 0`,
  `aktualisiert = 0`, `Zeitstempel nachgezogen = 0` (solange Odoo 11 unveraendert
  bleibt).
- Belegt in Session 145 lokal: Lauf 1 (6.753 + 141 angelegt), Lauf 2 (0 angelegt,
  0 Fehler), Lauf 3 bis 8 (Restkorrekturen an Zeitstempeln und normalisierten
  Feldern), Lauf 9 (0 angelegt, 0 aktualisiert, 0 Fehler, 0 Dubletten).

## 10 Wiederholung und Rollback

- Ein abgebrochener Lauf ist unkritisch: der naechste Lauf erkennt alles
  Uebernommene und macht weiter.
- Ruecknahme: alle uebernommenen Vorgaenge tragen `itk_o11_id`; sie lassen sich
  gezielt loeschen (`crm.lead.search([('itk_o11_id','!=',False)]).unlink()`), ohne
  manuell angelegte Vorgaenge zu beruehren. Stammdaten (Stichwoerter, Teams) bleiben
  dabei bestehen und sind wiederverwendbar.
- Vor einem Schreiblauf auf der VM: Modulstand per `git log` festhalten, damit ein
  Lauf mit dem richtigen Skriptstand wiederholt werden kann.
