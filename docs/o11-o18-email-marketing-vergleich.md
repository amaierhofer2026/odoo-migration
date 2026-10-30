# Odoo 11 -> Odoo 18: Bereich E-MAIL-MARKETING - Bestandsaufnahme und Vergleich

Stand: 30.10.2026, Session 138 (Nachtrag). **Reine Lesefassung:** In Odoo 11 wurde nichts
geschrieben, in Odoo 18 wurde nichts installiert, angelegt oder geaendert.

Quelle Odoo 11: Produktion (`portal.it-kommunal.at`, DB `ITK_V1_a`, nur Leseabfragen).
Quelle Odoo 18: lokal (`localhost:8069`) und VM (`https://k001959vsx.ipax.at`).

---

## 1. Bestand Odoo 11 (live erhoben)

| Objekt | Modell | Datensaetze |
|---|---|---|
| Massenmailings | mail.mass_mailing | **161** (141 aktiv, 20 archiviert) |
| Mailinglisten | mail.mass_mailing.list | **8** |
| Mailinglistenkontakte | mail.mass_mailing.contact | **13.501** (32 mit Opt-out) |
| Kampagnen | mail.mass_mailing.campaign | **9** |
| Kampagnenstufen | mail.mass_mailing.stage | **3** (Ausfuehrungsplan, Design, Gesendet) |
| Tags | mail.mass_mailing.tag | **1** ("Campaign Tag 1") |

Module Odoo 11: `mass_mailing` 11.0.2.0, `website_mass_mailing` 11.0.1.0,
`mass_mailing_event` 11.0.1.0 (installiert); `mass_mailing_event_track`,
`mass_mailing_sms` nicht installiert.

Zustand der Mailings: `done` 130, `draft` 31. Gesendet-Zeitraum 16.01.2020 bis 07.07.2026
(131 Datensaetze mit Sendedatum). **3 Mailings haben ein geplantes Sendedatum
(`schedule_date`)** - davon geht ohne Sicherung ein Versandrisiko aus.

Zielmodelle der Mailings (`mailing_model_name`): crm.lead 99, res.partner 35,
mail.mass_mailing.list 10, sale.order 2, account.invoice 1, kein Modell 14.
Nur 4 Mailings haengen an einer Mailingliste, 135 an einer Kampagne, 157 ohne Liste
(dort wirkt der Empfaenger-Domain-Filter).

Summen ueber alle Mailings: gesendet 50.871, gesamt 240.634, zugestellt 50.871,
geoeffnet 19.295, geantwortet 0, Bounces 0, fehlgeschlagen 9.900.

Mailinglisten und Groesse (Kontakte je Liste):

| Liste | Name | Kontakte |
|---|---|---|
| 1 | Newsletter | 0 |
| 2 | Test Empfaengerliste | 0 |
| 3 | Test | 1 |
| 5 | Test Kat&Flo | 0 |
| 9 | OGD_Aussendung_03.05.2023 | 2.069 |
| 1459 | IFG-Portal_Benutzer | 722 |
| 1460 | AFS_FSW_Kunden | 1.492 |
| 1461 | nicht_amtsweg_Kunde | 1.146 |

Kampagnen: Marketing, rechnungsversand 01/2020, Rechnungen 19.8.2021, Testkampagne,
OGD-Publikationsservice (3 Mailings), Informationsfreiheitsgesetz (IFG) (101),
amtsweg.gv.at (12), Formularmanager - amtsweg.gv.at LIGHT Kunden (1),
Informationsfreiheitsgesetz (IFG) (14). Alle in Stufe "Ausfuehrungsplan".

Opt-out: 32 Kontakte mit `opt_out = True`. Ein Modell `mail.blacklist` gibt es in Odoo 11
**nicht** (kam erst spaeter); Opt-out liegt ausschliesslich am Kontakt.

Cron in Odoo 11: "Massenmailing: Prozesswarteschlange" (aktiv), zusaetzlich
"E-Mail: E-Mail-Warteschlangen-Manager" und "Mail: Fetchmail Service".

Vorlagen: genau eine auf `mail.mass_mailing` ("Massen-Email", id 78, ohne Betreff);
die Inhalte stecken direkt in `body_html` der Mailings.

## 2. Bestand Odoo 18

| Modul | lokal | VM |
|---|---|---|
| `mass_mailing` | installiert 18.0.2.7 | installiert 18.0.2.7 |
| `mass_mailing_themes` | installiert 18.0.1.2 | installiert 18.0.1.2 |
| `mass_mailing_event` | installiert (seit Events) | installiert |
| `website_mass_mailing` | **nicht installiert** (18.0.1.0) | nicht installiert |
| `mass_mailing_sms` | nicht installiert | nicht installiert |

Modelle (Datensaetze lokal, inkl. Odoo-18-Demodaten):
`mailing.mailing` 1, `mailing.list` 1, `mailing.contact` 1, `mailing.trace` 4,
`mailing.trace.report` 1, `mailing.filter` 0, `mailing.subscription` 1,
`mailing.subscription.optout` 5. Das sind **Demodaten**, keine Fachinhalte.

Zustaende in Odoo 18: `draft` (Entwurf), `in_queue` (In der Warteschlange),
`sending` (Im Versand), `done` (Gesendet). Odoo 11 kennt nur `draft` und `done`.

Menues Odoo 18 (de_DE): E-Mail-Marketing mit Mailings, Mailinglisten
(Mailinglisten, Mailinglistenkontakte), Berichtswesen (Analyse von Massenmailings,
Abmeldungsbericht) und Konfiguration (Einstellungen, Link-Tracker, E-Mail-Adressen auf
der schwarzen Liste, Abmeldungsgruende, Bevorzugte Filter).

Menues Odoo 11: **nur** E-Mail-Marketing > Mailings > Massenmailings. Die Aktionen fuer
Listen ("E-Mail-Empfaengerlisten"), Kontakte, Kampagnen, Kampagnen-Tags und Stufen sind
vorhanden, aber ohne eigenen Menueeintrag.

## 3. Feldmapping Mailing (mail.mass_mailing -> mailing.mailing)

Bewertung: 1:1 vorhanden / anders benannt / Mapping noetig / fehlt / obsolet.

| Odoo-11-Feld | verwendet? | Odoo 18 | Status |
|---|---|---|---|
| name | ja | subject | anders benannt (O18: Betreff ist eigenes Feld) |
| subject | ja (161) | subject | 1:1 vorhanden |
| body_html | ja | body_html / body_arch | 1:1 vorhanden (O18 zusaetzlich body_arch) |
| email_from | ja | email_from | 1:1 vorhanden |
| reply_to | ja | reply_to_mode (+ reply_to berechnet) | Mapping noetig |
| reply_to_mode | ja (email 160, thread 1) | reply_to_mode | 1:1 vorhanden |
| state | ja | state | 1:1 vorhanden, O18 hat zwei Zusatzwerte |
| sent_date | ja (131) | sent_date | 1:1 vorhanden |
| schedule_date | ja (3) | schedule_date + schedule_type | 1:1 vorhanden, aber Sicherung noetig |
| mass_mailing_campaign_id | ja (135) | **fehlt** (nur campaign_id = utm.campaign) | fehlt |
| contact_list_ids | ja (4) | contact_list_ids | 1:1 vorhanden |
| mailing_domain | ja | mailing_domain | 1:1 vorhanden |
| mailing_model_id / _name / _real | ja | mailing_model_id / _name / _real | 1:1 vorhanden |
| attachment_ids | ja | attachment_ids | 1:1 vorhanden |
| keep_archives | ja (alle False) | keep_archives | 1:1 vorhanden |
| active | ja (20 archiviert) | active | 1:1 vorhanden |
| color | ja | color | 1:1 vorhanden |
| sent / delivered / opened / replied / bounced / failed / total | ja | sent / delivered / opened / clicked / failed / canceled; `replied` und `total` fehlen | Mapping noetig, Zaehler werden in O18 aus `mailing.trace` gespeist |
| received_ratio / opened_ratio / replied_ratio / clicks_ratio / bounced_ratio | ja | received_ratio / opened_ratio / clicked_ratio / bounced_ratio; `replied_ratio` fehlt | anders benannt / teilweise fehlt |
| contact_ab_pc | ja | fehlt (O18: A/B-Test mit anderen Feldern) | obsolet |
| statistics_ids | ja | mailing_trace_ids / mailing.trace | anders benannt |
| campaign_id / medium_id / source_id (utm) | ja | campaign_id / medium_id / source_id | 1:1 vorhanden |
| next_departure | ja | next_departure | 1:1 vorhanden |
| (kein Gegenstueck) | - | mailing_filter_id, ab_testing_*, link_trackers_count, lang, mail_server_id | Odoo-18-Zusatz |

## 4. Feldmapping Listen, Kontakte, Kampagnen

| Objekt | Odoo 11 | Odoo 18 | Status |
|---|---|---|---|
| Liste | name, active, contact_nbr | name, active, contact_count, mailing_count, contact_pct_bounce/opt_out/blacklisted, is_public | 1:1 plus Odoo-18-Zusatz |
| Liste (Website) | popup_content, popup_redirect_url | nur mit `website_mass_mailing` | Modul in O18 nicht installiert |
| Kontakt | name, email, company_name, title_id, country_id, tag_ids, list_ids, opt_out, unsubscription_date, message_bounce, create_date | name, email, company_name, title_id, country_id, tag_ids, list_ids, subscription_ids, opt_out, opt_out_datetime, opt_out_reason_id, is_blacklisted, message_bounce | anders benannt (unsubscription_date -> opt_out_datetime), Odoo-18-Zusatz |
| Kampagne | name, user_id, stage_id, tag_ids, unique_ab_testing, mass_mailing_ids, Kennzahlen | **kein Modell**; nur utm.campaign (name, user_id) | fehlt |
| Kampagnenstufe | name, sequence | **kein Modell** | fehlt |
| Tag | name, color | mailing.tag | 1:1 vorhanden |

## 5. Rechte

Odoo 11: Gruppe "E-Mail-Marketing / Benutzer" hat auf allen fuenf Modellen
(Mailings, Listen, Kontakte, Kampagnen, Stufen, Tags) **volle Rechte** (r1 w1 c1 u1);
zusaetzlich "Administration / Einstellungen" auf Mailings und Kampagnen.

Odoo 18: eigene Gruppen `mass_mailing.group_mass_mailing_user` (Benutzer) und
`mass_mailing.group_mass_mailing_manager` (Administrator); Rechte je Modell sind enger
als in Odoo 11 (Loeschen nur Manager). Genaue Matrix wird bei der Umsetzung erhoben und
dokumentiert.

## 6. Automatisierung und Versandrisiko (Kernpunkt)

Odoo 11: Cron "Massenmailing: Prozesswarteschlange" verarbeitet die Warteschlange
(`mail.mail`) und versendet. 31 Mailings sind Entwurf, 3 haben ein geplantes Sendedatum.

Odoo 18: Der Versand laeuft ueber `mailing.mailing.action_send_mail` bzw. die
Warteschlange (Cron "Mail: Email Queue Manager") und `process`-Felder
(`in_queue`, `sending`). Ein Mailing wird **nur** versendet, wenn es aktiv angestossen wird
oder in der Warteschlange steht.

**Sicherungsregeln fuer die Migration (Vorschlag):**
1. Alle 130 gesendeten Mailings werden als `done` uebernommen, ohne Warteschlange, ohne
   `mailing.trace`-Zeilen (keine Empfaenger).
2. Alle 31 Entwuerfe werden als `draft` uebernommen; **`schedule_date` wird nicht gesetzt**
   (die 3 geplanten Termine werden im Dokument und in der CSV festgehalten, nicht als
   aktiver Termin). Kein Mailing erhaelt `in_queue` oder `sending`.
3. Der Odoo-18-Cron "Mail: Email Queue Manager" wird waehrend der Migration pausiert und
   danach wieder aktiviert; die Warteschlange (`mail.mail`) enthaelt keine Zeilen aus der
   Migration, weil keine Empfaenger uebernommen werden.
4. Vor dem Import wird geprueft, dass `mailing.mailing` in Odoo 18 keine
   `mail.mail`-Zeilen erzeugt, solange `state = draft` und kein `schedule_date` gesetzt ist.

## 7. Datenmengen und Migrationsschluessel (Vorschlag)

| Objekt | Menge | Schluessel | Personenbezug |
|---|---|---|---|
| Mailing | 161 | `(subject, sent_date, mailing_model_name)` bzw. `create_date` | keiner (Inhalte sind Werbetexte) |
| Mailingliste | 8 | `name` | keiner |
| Kampagne | 9 | `name` | keiner |
| Kampagnenstufe | 3 | `name` | keiner |
| Tag | 1 | `name` | keiner |
| Kontakt | 13.501 | **nicht migrieren** | personenbezogen |
| Statistik | 50.871 Zeilen `mail.mail.statistics` | **nicht migrieren** (keine Empfaenger) | personenbezogen (E-Mail) |

Nachverknuepfung fuer die spaetere Kontaktmigration: CSV je Instanz mit
`liste -> Kontakt-IDs`, `Kontakt-Opt-out-IDs`, `Mailing -> Listen-IDs`,
`Mailing -> Kampagne`, `Mailing -> Empfaenger-Domain` (nur Kennungen, keine Adressen).

## 8. Entscheidungspunkte

**M1 - Kampagnen und Stufen (blockierend fuer die Mailing-Zuordnung).**
Odoo 18 hat kein Gegenstueck zu `mail.mass_mailing.campaign` mit Stufen
(Ausfuehrungsplan / Design / Gesendet); 135 von 161 Mailings haengen daran.
Optionen:
A) nur `utm.campaign` nutzen (9 Kampagnennamen bleiben sichtbar, Stufen und
   Kampagnen-Kennzahlen entfallen) - einfach, aber Verlust der Stufenlogik;
B) eigenes ITK-Modell "Mailingkampagne" mit Stufen und Kennzahlen nachbauen
   (1:1-Abbildung, mehr Aufwand und ein Modell, das Odoo 18 nicht kennt);
C) Kampagnennamen als `utm.campaign` plus Tag "Kampagne" am Mailing, Stufen nur
   dokumentieren. Empfehlung: **A** (Namen bleiben erhalten), Stufenverlust dokumentieren.

**M2 - Statistik uebernehmen?** Odoo 18 rechnet `sent`/`opened`/`failed` aus
`mailing.trace`. Ohne Empfaenger gaebe es keine Traces, die Zaehler waeren also entweder
statisch (falls schreibbar) oder 0. Empfehlung: Zaehler **nicht** schreiben, sondern die
Odoo-11-Werte je Mailing in der CSV und im Dokument festhalten; die Odoo-18-Anzeige startet
bei 0, was der Wahrheit entspricht (keine Empfaenger in Odoo 18).

**M3 - Entwuerfe mit geplantem Versand (3 Mailings).** Empfehlung: als Entwurf ohne
Sendedatum uebernehmen, Originaldatum in der CSV dokumentieren (siehe Abschnitt 6).

**M4 - Odoo-18-Demodaten.** 1 Mailing, 1 Liste, 1 Kontakt, 4 Traces, 5 Abmeldegruende sind
Demodaten ohne Fachbezug. Empfehlung: vor der Migration entfernen (Kontakt und Traces),
Listen-/Mailing-Demo nur, wenn sie nicht mit Odoo-11-Namen kollidieren.

**M5 - `website_mass_mailing` (Newsletter-Anmeldung auf der Website).** In Odoo 11
installiert, in Odoo 18 nicht. Empfehlung: installieren, wenn die Newsletter-Anmeldung auf
der Website gebraucht wird; sonst dokumentieren (Funktion betrifft Kontakte, die jetzt nicht
migriert werden).

**M6 - `mass_mailing_event`.** In beiden Versionen installiert; ohne Teilnehmerdaten
derzeit ohne Funktion. Keine Aktion, dokumentiert.

**M7 - Opt-out und Blacklist.** 32 Opt-outs in Odoo 11; Odoo 18 fuehrt zusaetzlich eine
Blacklist und Abmeldegruende. Ohne Kontakte nicht uebertragbar. Empfehlung: nur Zaehlwerte
und Kontakt-IDs in der CSV, spaeter mit der Kontaktmigration nachziehen.

## 9. Bewusst nicht migrieren (Vorschlag)

| Objekt | Menge | Begruendung |
|---|---|---|
| mailing.contact (Adressen) | 13.501 | personenbezogene Daten, eigener Bereich |
| Opt-out-Datensaetze | 32 | personenbezogen |
| Statistikzeilen `mail.mail.statistics` | 50.871 | personenbezogen (Empfaengeradresse) |
| `mail.mail`-Warteschlange | - | Versandartefakte, duerfen nie erneut raus |
| Empfaenger-Domains | 157 Mailings ohne Liste | enthalten Feldbezuege, keine Daten - Domain-Text bleibt am Mailing |
| `contact_ab_pc` | - | Odoo-18-A/B-Test hat andere Felder |
| Vorlage "Massen-Email" | 1 | Inhalt steckt in `body_html` der Mailings |

---

## 10. Umsetzung (Session 138, 30.10.2026) - Entscheidungen von Anna

| Punkt | Entscheidung | Umsetzung |
|---|---|---|
| M1 Kampagnen | Variante **B**: eigenes ITK-Modell mit Stufen | `itk.mailing.campaign` + `itk.mailing.campaign.stage` + `itk.mailing.tag` im Modul `itk_mass_mailing_compat`; 9 Kampagnen, 3 Stufen, 1 Tag uebernommen |
| M2 Statistik | historische Kennzahlen erhalten, klar getrennt | eigene Felder `x_o11_*` je Mailing und je Kampagne; Odoo-18-Kennzahlen bleiben unveraendert (aus `mailing.trace`) |
| M3 geplante Entwuerfe | als Entwurf ohne Sendetermin | `schedule_date` bleibt leer, Odoo-11-Termin nur in `x_o11_schedule_date` (3 Datensaetze) |
| M4 Demodaten | entfernen | 1 Demo-Mailing, 1 Demo-Liste, 1 Demo-Kontakt, 4 Demo-Traces entfernt |
| M5 `website_mass_mailing` | installieren, nur Funktion | Modul 18.0.1.0 installiert; keine Abonnenten uebernommen |
| M6 `mass_mailing_event` | bleibt, keine Daten | unveraendert, 0 Teilnehmer |
| M7 Opt-out/Blacklist | nur dokumentieren | siehe Abschnitt 11; keine Adresse angelegt |

### 10.1 Datenmigration

| Objekt | Odoo 11 | Odoo 18 nach Migration |
|---|---|---|
| Kampagnenstufen | 3 | 3 (Ausfuehrungsplan, Design, Gesendet) |
| Kampagnen | 9 | 9, alle mit Odoo-11-Referenz und Kennzahlen |
| Kampagnen-Tags | 1 | 1 ("Campaign Tag 1") |
| Mailinglisten | 8 | 8 (reine Struktur, 0 Mitglieder) |
| Mailings | 161 | **147** (130 gesendet, 17 Entwurf; 14 archiviert) |
| davon mit Kampagne | 135 | 126 der uebernommenen |
| Kennzahlen | 50.871 gesendet, 19.295 geoeffnet, 9.900 fehlgeschlagen | Summen identisch in `x_o11_*` |
| **nicht migriert** | 14 Mailings ohne Empfaengermodell | dokumentiert (Odoo 18: `mailing_model_id` ist Pflichtfeld) |
| Kontakte / Empfaenger | 13.501 | **0** |
| Traces / Versandprotokolle | 50.871 | **0** |
| Opt-out | 32 | **0** (nur dokumentiert) |

Zweiter Lauf: 0 Neuanlagen, 147 Aktualisierungen (idempotent).

Nachverknuepfung (nur Kennungen, keine Personen):
`docs/o11-o18-email-marketing-nachverknuepfung-lokal.csv` und `-vm.csv`
(Typen: mailing, liste, kampagne).

### 10.2 Technische Versandsperre (getestet)

1. **Modul-Sperre:** `action_send_mail`, `action_launch`, `action_put_in_queue`,
   `action_schedule`, `action_set_sending` und ein Statuswechsel auf `in_queue`/`sending`
   sind fuer Mailings mit `x_o11_id` gesperrt (UserError
   "Historische Mailings aus Odoo 11 duerfen nicht erneut versendet werden").
   Getestet fuer je ein gesendetes und ein Entwurfs-Mailing.
2. **Kein Sendetermin:** `schedule_date` bei allen 147 leer, `schedule_type = now`,
   kein Mailing in `in_queue`/`sending`.
3. **Crons:** "Mail: Email Queue Manager", "Mail Marketing: Process queue",
   "Event: Mail Scheduler" und weitere waehrend des Laufs deaktiviert und danach auf
   ihren vorherigen Zustand zurueckgesetzt.
4. **Nachweis:** `mail.mail` 3.359 vor und nach dem Lauf, `mailing.trace` 0,
   keine neue Warteschlangenzeile.

### 10.3 Pruefungen (lokal)

| Pruefung | Ergebnis |
|---|---|
| `verify_s138_marketing.py --instanz lokal` | **37 OK / 0 FEHLER** |
| `browser_marketing_abnahme.py --instanz lokal` | **20 OK / 0 FEHLER** |
| `marketing_labels_de.py --instanz lokal` | 0 offen |
| `marketing_rechte.py --instanz lokal` | Benutzer liest/anlegt/bearbeitet/loescht (Odoo-18-Recht); Testdaten entfernt, Bestand 147/9/3 unveraendert |
| Regression Events / Personal / Projekt | 61/0, 54/0, 20/0 |

## 11. Opt-out und Blacklist - Regel fuer die spaetere Uebernahme (M7)

- **Bestand Odoo 11:** 32 von 13.501 Listeneintraegen mit `opt_out = True`
  (Feld am Kontakt `mail.mass_mailing.contact`, kein eigenes Blacklist-Modell in Odoo 11).
- **Herkunft:** `mail.mass_mailing.contact` mit `opt_out = True`, verteilt auf die
  Mailinglisten (Mitgliedschaft ueber `list_ids`). Die Kontakt-IDs stehen in der
  Nachverknuepfungsliste; Adressen wurden nicht uebernommen.
- **Technische Regel fuer die spaetere Kontaktmigration:**
  1. Kontakt ueber den fachlichen Schluessel (E-Mail, normalisiert) zuordnen.
  2. Bei `opt_out = True` in Odoo 11: in Odoo 18 `mailing.contact.opt_out = True`,
     `opt_out_datetime` aus dem Odoo-11-Austrittsdatum (`unsubscription_date`, soweit
     gesetzt) und einen Abmeldegrund (`mailing.subscription.optout`) setzen.
  3. Zusaetzlich `mail.blacklist` mit derselben Adresse fuehren (Odoo 18 sperrt den Versand
     damit auch fuer andere Mailings).
  4. Gegenprobe: Anzahl Opt-outs in Odoo 18 == 32, keine Adresse doppelt.
- Bis dahin gilt: **keine Blacklist-Adresse, kein Kontakt, kein Listeneintrag in Odoo 18**.
