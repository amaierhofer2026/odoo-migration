# Bereich WEBSITE / WEBINHALTE: Umsetzung und Abnahme (Odoo 11 -> Odoo 18)

Stand: 12.11.2026, Session 142. Grundlage: `docs/o11-o18-vergleich-website.md`
(Bestandsaufnahme Session 141) und die Entscheidungen E1-E14 von Anna.

Odoo 11 Prod (`ITK_V1_a`) wurde ausschliesslich lesend befragt. Geschrieben wurde
nur in Odoo 18 (lokal und VM).

## 1 Entscheidungen und Umsetzung

| Nr | Entscheidung | Umsetzung |
|---|---|---|
| E1 | Markup automatisch auf Bootstrap 5 umschreiben, Startseite gestalterisch neu | `scripts/website_markup.py` (Regelwerk unten), Startseite als eigenes Odoo-18-Layout in `scripts/website_homepage_o18.html` mit den Texten aus Odoo 11 |
| E2 | FAQ-Aufklapper wieder aufklappbar | 261 `panel-group`-Blöcke in Bootstrap-5-Akkordeons (`accordion`, `data-bs-toggle="collapse"`, `accordion-body`) umgebaut; Klick im Browser geprüft |
| E3 | Doppelt escapte Zeichen bereinigen | 3.482 x `&amp;nbsp;` -> geschütztes Leerzeichen, 66 x `&amp;amp;` -> `&`; im Browser keine sichtbaren `&nbsp;`-Artefakte mehr |
| E4 | Nur die zwei fachlich genutzten unveröffentlichten Seiten übernehmen | `FAQs Umstellung zur Gemeindecloud` und `FAQS IFG-Portal (Kunden)` übernommen, **beide unveröffentlicht** wie in Odoo 11 |
| E5 | Odoo-18-Standardseiten behalten | `Contact Us` (`/contactus`), `Thanks (Contact us)` unverändert; Odoo-11-Seiten 2/3/4 nicht übernommen |
| E6 | Odoo-11-Menüstruktur abbilden, keine 404-Links | 10 Menüpunkte unter der Wurzel `Top Menü`; Punkt 7 zeigt auf die interne Seite (nicht mehr auf die absolute 404-Adresse); Punkt 10 hängt an der unveröffentlichten Seite und ist für Besucher automatisch unsichtbar |
| E7 | `website_sale` nicht installieren | nicht installiert; Odoo 11 hatte 0 veröffentlichte Produkte |
| E8 | `website_rating` nicht nachbauen | Modul existiert in Odoo 18 nicht; 0 Bewertungen in Odoo 11 |
| E9 | Link-Tracker mit Klickzahlen migrieren | 837 Tracker, 563 Klicks, 16 Kampagnen, 9 Medien, 220 Quellen; Kurz-URL-Codes unverändert |
| E10 | Website-Rechte nicht pauschal nachbauen | keine Benutzer- oder Rechtänderung; Rollenlogik geprüft (`scripts/pruefe_website_rechte.py`, 17 OK) |
| E11 | Einstellungen: Name, Domain, Twitter, CRM-Team | Name `ITK Portal`, Twitter `@IT_Kommunal`, CRM-Standardteam `Vertriebskanäle (Intern)`, Favicon und Kopf-Logo aus Odoo 11; Domain bleibt `https://www.it-kommunal.at` |
| E12 | Cookie-Hinweis behalten, deutsch | Text deutsch, Banner aktiv, OK-Knopf geprüft (Session gesetzt, blockiert nichts) |
| E13 | Wortlaute im Backend | `Site` -> `Webseite`, `Analytics` -> `Analysen` (Modul `itk_website`, Quelle + de_DE + en_US) |
| E14 | Eindeutige Demodaten entfernen | Konfigurator-Startseite gelöscht, Odoo-Standard-Startseite als unveröffentlichte Vorlage entkoppelt, Demo-Besucher/-Seitenansichten gelöscht, Demo-Kontaktblock im Kopf und Demo-Fußzeile ersetzt |

## 2 Markup-Regelwerk (E1-E3)

`scripts/website_markup.py`, nur Standardbibliothek. Je Seite protokolliert:

| Umbau | Anzahl |
|---|---|
| `<font>` -> `<span>` (Farbe/Größe als `style`) | 1.590 |
| `panel-group` -> Bootstrap-5-Akkordeon | 261 |
| `panel`/`s_panel` ohne Aufklapper -> Karte | 8 |
| `col-*-offset-*` -> `offset-*-*` | 5 |
| `pull-left/right` -> `float-start/end` | 14 |
| `page-header` -> Odoo-11-Abstand als `style` | 47 |
| `jumbotron` -> `s_text_block` mit Abstand | 2 |
| Odoo-11-Bausteine (`s_feature_grid`, `s_big_message`, `s_button`) -> `s_text_block` | 5 |
| doppelt escapte Zeichen | 3.482 x `&nbsp;`, 66 x `&` |
| leere Editor-Reste entfernt | 174 |
| Word-Paste-Klassen (`MsoNormal`) entfernt | 19 |

Odoo-11-Themefarben ohne Bootstrap-5-Gegenstück werden mit den **exakten Odoo-11-Werten**
als `style` gesetzt (aus dem Live-CSS belegt): `text-gamma`/`bg-gamma` #ba3c3d,
`text-beta`/`bg-beta` #875a7b, `bg-gray-lighter` #cccccc/#666666,
`bg-white-50` rgba(255,255,255,.5).

Restprüfung je Seite: 0 `panel*`, 0 `data-toggle`, 0 `<font>`, 0 `col-*-offset`,
0 sichtbare `&nbsp;`-Artefakte.

## 3 Seiten (Mapping)

| Odoo 11 | Odoo 18 | Status |
|---|---|---|
| Webseite `/` (id 1) | Startseite, Key `website.webseite` | veröffentlicht, gestalterisch neu (E1) |
| Wie bestelle ich einen Kurs (6) | `/wie-bestelle-ich-einen-kurs` | veröffentlicht |
| Kurse (10) | `/kurse` | veröffentlicht |
| FAQs Umstellung zur Gemeindecloud (11) | `/faqs-umstellung-zur-gemeindecloud` | **unveröffentlicht** wie Odoo 11 |
| Gemeindecloud.at (14) | `/gemeindecloud-at` | veröffentlicht |
| FAQs Städtebund-Academy (16) | `/faqs-staedtebund-academy` | veröffentlicht |
| FAQ IFG-Portal (Partner) (17) | `/faqs-ifg-portal-partner` | veröffentlicht, Bild migriert |
| FAQ Anonymisierungs-Portal (18) | `/faq-anonymisierungs-portal` | veröffentlicht |
| FAQS IFG-Portal (Kunden) (19) | `/faqs-ifg-portal-kunden` | **unveröffentlicht** wie Odoo 11 |

Nicht übernommen (dokumentiert): 2 Contact Us, 3 About us, 4 Thanks (Odoo-Standard),
5 Kurse (Kopie), 7 test, 9 Sicherung, 12 Testseite, 13 FAQs (Sicherung).

Odoo 18 hat danach 12 Seiten: 9 übernommene + Contact Us + Thanks + die
unveröffentlichte Standard-Startseite `/homepage-vorlage`.

## 4 Menüs

Wurzel `Top Menü` (Odoo 11: "Top Menü"), 10 Punkte in Odoo-11-Reihenfolge:
ITK Portal, ITK Webseite (extern), Ticket (`/support/ticket/submit`, Formular aus
`itk_helpdesk_compat`), Webinare (`/event`), Kurse, Wie bestelle ich einen Kurs,
FAQ Umstellung Ebox - Gemeindecloud, FAQ IFG-Portal (Partner),
FAQ Anonymisierungs-Portal, FAQS IFG-Portal (Kunden).

- Punkt 7 zeigt auf die **interne** Seite (Odoo 11: absolute Adresse, die live 404 lieferte).
- Punkt 7 und 10 sind mit ihrer Zielseite verknüpft; Odoo 18 blendet Menüpunkte
  unveröffentlichter Seiten für Besucher automatisch aus (`_compute_visible`).
  Für Besucher sind 8 Punkte sichtbar, 2 unsichtbar - kein 404, keine vorzeitige
  Veröffentlichung.
- `website.main_menu` („Default Main Menu") ist Odoo-Standarddatum, wird nicht
  gelöscht und nicht verändert.

## 5 Einstellungen

| Feld | Odoo 11 | Odoo 18 vorher | Odoo 18 jetzt |
|---|---|---|---|
| Name | ITK Portal | IT-Kommunal | **ITK Portal** |
| Domain | `localhost` (defekt) | `https://www.it-kommunal.at` | unverändert (Produktivdomain = externer Konfigurationspunkt) |
| Twitter | `@IT_Kommunal` | leer | **@IT_Kommunal** |
| CRM-Standardteam | Vertriebskanäle (Intern) | Sales/Verkauf | **Vertriebskanäle (Intern)** (id 5) |
| Favicon | vorhanden | vorhanden (anders) | Odoo-11-Favicon |
| Kopf-Logo | Unternehmenslogo | leer (kaputtes Bild) | Odoo-11-Unternehmenslogo |

`salesteam_id` („Webseite") gibt es in Odoo 18 nicht mehr - dokumentiert, kein Ersatzwert.

## 6 Link-Tracker (E9)

| Wert | Odoo 11 | Odoo 18 |
|---|---|---|
| Tracker | 837 | 837 |
| Klicksumme | 563 | 563 |
| Klick-Einzelsätze | 563 | 563 |
| Kampagnen | 16 | 16 |
| Medien | 9 | 9 (Odoo-18-Namen: Banner Ads -> Banner, Twitter Ads -> X, Facebook Ads -> Facebook) |
| Quellen | 220 | 220 |

- Klick-Einzelsätze wurden **ohne IP-Adresse und ohne Mail-/Kontaktbezug** angelegt
  (nur Link + Zeitpunkt), damit die Klickzahlen in Odoo 18 dauerhaft stimmen
  (`link.tracker.count` ist ein berechnetes Feld über `link.tracker.click`).
- Odoo 18 verlangt Eindeutigkeit von (URL, Kampagne, Medium, Quelle, Bezeichnung);
  Odoo 11 erlaubte Dubletten (ein Kurzlink je Mailing). 633 Tracker tragen deshalb
  die technische Kennung `Odoo-11-Link <id>` im Feld Bezeichnung. Das Feld ist
  rein intern (Backend-Spalte), erscheint nicht auf der Website; URL, Titel,
  Kampagne, Quelle und Klickzahl bleiben unverändert.
- Kurz-URL-Codes sind übernommen, die Links funktionieren über die Odoo-18-Domain:
  `/r/wFy` -> 302 auf das historische Ziel mit den UTM-Parametern.

## 7 Idempotenz

Schlüssel: Seite = View-Key, Menü = URL unter der Wurzel, Tracker = Kurz-URL-Code,
Anhang = Name + Dateigröße, Klicks = Sollzahl je Link.

Ergebnis der Läufe (lokal):

| Lauf | Ergebnis |
|---|---|
| 1 | Trockenlauf, schreibfrei (Vor/Nach-Snapshot von 10 Modellen identisch) |
| 2 | Schreiblauf: 9 Seiten, 10 Menüs, Einstellungen, Anhang, 837 Tracker, 563 Klicks |
| 3 | 0 Neuanlagen, 8 Arch-Aktualisierungen (Serialisierung), 0 Klicks |
| 4 | 0 Neuanlagen, 0 Aktualisierungen, 0 Klicks (nach Normalisierung des Arch-Vergleichs) |
| 5 | 0 Neuanlagen, 0 Aktualisierungen, 0 Klicks (**idempotent bestätigt**) |

## 8 Abnahme

### Rechnerisch/technisch
- Alle veröffentlichten Seiten HTTP 200, alle unveröffentlichten HTTP 404 (wie Odoo 11).
- 0 sichtbare `&nbsp;`/`&amp;`-Artefakte in allen 7 veröffentlichten Seiten.
- 261 Akkordeon-Knöpfe vorhanden (`/kurse` 54, `/faqs-ifg-portal-partner` 33, ...).

### Browser (echter Chrome, lokal)
- Startseite: Logo, Cookie-Banner deutsch, zwei Produktspalten mit Icons, Support-Block,
  Kontaktblock mit Button auf `/contactus`.
- `/kurse`: Preistabelle, 49 Akkordeon-Knöpfe, Aufklapper öffnet und schliesst.
- `/faqs-ifg-portal-partner` mobil (398 px): lesbar, Aufklapper bedienbar, kein Überlauf.
- Cookie-Banner: OK setzt die Session, Banner verschwindet nach Neuladen, blockiert nichts.
- Kopfzeile: 8 Menüpunkte, Punkt 7 und 10 nicht sichtbar.

### Rechte (`scripts/pruefe_website_rechte.py`, lokal)
17 Prüfungen OK / 0 Fehler: Redakteur darf Seiten und Menüs schreiben, interner Leser
nicht (AccessError), Redakteur sieht unveröffentlichte Seiten, Leser nicht,
Besucher-Menü korrekt, Website-Einstellungen nur für Designer, Testbenutzer
vollständig entfernt (14 Benutzer vorher = nachher), Seiten-/Menübestand unverändert.

## 9 Bewusst nicht migriert

- 563 Klick-Einzelsätze mit IP-Adresse und Mailbezug (personenbezogen) - die Klickzahlen
  selbst sind übernommen.
- Formularübermittlungen, Kontakte, Leads, Aufträge: Odoo 11 hatte auf keiner
  Website-Seite ein Formular (0 `<form>`); das Kontaktformular entsteht in Odoo 18
  über die Standardseite `/contactus` (`website_crm` -> `crm.lead`).
- Odoo-11-Seiten 5, 7, 9, 12, 13 (Test/Kopie/Sicherung) und die Odoo-11-Standardseiten
  2, 3, 4.
- SEO-Texte: in Odoo 11 bei 0 von 17 Seiten gesetzt, nichts zu übertragen.

## 10 Werkzeuge

| Datei | Zweck |
|---|---|
| `scripts/analyse_o11_website.py` | read-only Bestandsaufnahme (Session 141) |
| `scripts/website_markup.py` | Markup-Konverter BS3 -> BS5, mit Restprüfung |
| `scripts/website_homepage_o18.html` | Startseite (Odoo-18-Layout, Inhalte aus Odoo 11) |
| `scripts/migrate_website.py` | Migration mit Trockenlauf/Schreiblauf, `--nur`, `--abnahme` |
| `scripts/pruefe_website_rechte.py` | Rechteprüfung mit temporären Testbenutzern |
| `addons/itk_website` | Wortlaute (E13), Cookie-Hinweis deutsch (E12), Fußzeile/Kopf (E14) |
