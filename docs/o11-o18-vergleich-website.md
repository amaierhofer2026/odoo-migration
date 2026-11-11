# Bereich WEBSITE / WEBINHALTE: Odoo 11 gegen Odoo 18

Stand: 11.11.2026, Session 141. **Bestandsaufnahme, noch keine Aenderung an Odoo 11 oder Odoo 18.**

Odoo 11 Prod (`ITK_V1_a`, portal.it-kommunal.at) wurde ausschliesslich lesend befragt
(JSON-RPC, nur `search_read`/`read`/`fields_get`) und zusaetzlich oeffentlich per HTTP GET
abgerufen. Odoo 18 wurde lokal und auf der VM gelesen. Es wurde nichts angelegt, geaendert,
geloescht, migriert oder umbenannt; in Odoo 18 wurde kein Testdatensatz erzeugt.

Werkzeug (wiederverwendbar, read-only): `scripts/analyse_o11_website.py`
(`--json <datei>` schreibt den Rohbestand, `--seiten-arch <verz>` die Seiteninhalte).

## 1 Kurzbefund

| Punkt | Odoo 11 Prod | Odoo 18 lokal | Odoo 18 VM |
|---|---|---|---|
| Website-Datensatz | 1 (`ITK Portal`) | 1 (`IT-Kommunal`) | 1 (`IT-Kommunal`) |
| Seiten (`website.page`) | **17** (10 veroeffentlicht, 7 nicht) | **4** (Demodaten) | **4** (Demodaten) |
| Menues (`website.menu`) | **11** (1 Wurzel + 10 Punkte) | **8** (2 Wurzelmenues = Demo) | **8** |
| Sichtbarer Seitentext | **217.092 Zeichen** | Demo | Demo |
| FAQ-Aufklapper (`data-toggle`) | **261** | 0 | 0 |
| Link-Tracker | **837 Links, 563 Klicks** | 0 | 0 |
| Bewertungen (`rating.rating`) | 0 | 0 | 0 |
| Veroeffentlichte Produkte (Shop) | **0** | 0 (`website_sale` nicht installiert) | 0 |
| Website-Gruppen (aktive Benutzer) | Redakteur+Designer **37**, Eingeschraenkter Editor **41** | **2** / **14** | **2** / **14** |

Odoo 18 Website ist derzeit reine Demolage: zwei Home-Seiten mit URL `/` (id 2 und 4), zwei
Wurzelmenues (`Default Main Menu`, `Top-Menue fuer Website 1`), Odoo-Mustertext ("Wir sind ein
Team von leidenschaftlichen..."), US-Platzhaltertelefon "+1 555-555-5556".
Quelle: HTTP-Abruf https://k001959vsx.ipax.at/ am 11.11.2026.

## 2 Modulvergleich

Odoo 11 (installiert): `website` 11.0.1.0, `website_crm` 11.0.2.0, `website_sale` 11.0.1.0,
`website_form` 11.0.1.0, `website_links` 11.0.1.0, `website_mail` 11.0.0.1,
`website_mass_mailing` 11.0.1.0, `website_rating` 11.0.1.0, `website_event` 11.0.1.0,
`website_partner` 11.0.0.1, `website_odoo_debranding` 11.0.1.0.0, `website_support` 11.0.1.3.1,
`survey` 11.0.2.0, `survey_crm` 11.0.2.0.
Nicht installiert (also nicht Gegenstand): `website_blog`, `website_forum`, `website_slides`,
`website_legal_page`, `website_livechat`, `website_hr_recruitment`, `website_sale_comparison`.

| Odoo-11-Modul | Odoo 18 | Bewertung |
|---|---|---|
| `website` | installiert 18.0.1.0 | 1:1 vorhanden |
| `website_form` | **Modul existiert in Odoo 18 nicht mehr** | Formularbau ist Teil von `website` (Snippet `s_website_form`); in Odoo 11 auf keiner Seite benutzt |
| `website_crm` | installiert 18.0.2.1 | vorhanden (Kontaktformular -> `crm.lead`) |
| `website_links` | installiert 18.0.1.0 | vorhanden, `link.tracker` in beiden Versionen |
| `website_rating` | **kein Odoo-18-Modul** | Odoo 11 hat 0 Bewertungen -> kein Bedarf (dokumentierte Nicht-Uebernahme) |
| `website_mail` | installiert 18.0.0.1 | vorhanden |
| `website_mass_mailing` | installiert 18.0.1.0 | vorhanden (Bereich E-Mail-Marketing ist gesperrt) |
| `website_event` | installiert 18.0.1.4 | vorhanden; Menuepunkt `/event` bleibt |
| `website_partner` | installiert 18.0.0.1 | vorhanden |
| `website_odoo_debranding` | installiert 18.0.1.0.0 (Repo-Modul) | vorhanden, Fusszeile ohne Odoo-Hinweis |
| `website_support` | **Ersatz: `helpdesk_mgmt` 18.0.1.17.1** | Bereich Helpdesk: abgenommen und gesperrt |
| `website_sale` | **nicht installiert** (18.0.1.1 verfuegbar) | Odoo 11: Shop leer, 0 veroeffentlichte Produkte -> Entscheidung E7 |
| `website_cookie_notice` (Odoo 11: nicht installiert) | installiert 18.0.1.0.0 | Odoo-18-Zusatzfunktion, Banner derzeit englisch -> E12 |
| `survey` | installiert 18.0.3.7, **0 Umfragen** | eigener Bereich (Odoo 11: 2 Umfragen, 73 Teilnahmen), hier nicht bearbeitet |

Odoo 18 zusaetzlich vorhanden und ohne Odoo-11-Gegenstueck: `website_rewrite` (URL-Umleitungen,
0 Datensaetze), `website.robots` (0), `website.visitor`/`website.track` (3/8 Demo),
`website.configurator.feature` (13), `map.website` (6, Kartenmodul).

## 3 Menues

Odoo 11, Wurzel `Top Menu` (id 1), 10 Punkte in Reihenfolge:

| seq | Menue | Ziel | Seite verknuepft |
|---|---|---|---|
| 1 | ITK Portal | `/` | ja (Seite 1) |
| 2 | ITK Webseite | `http://www.it-kommunal.at` (extern) | nein |
| 3 | Ticket | `/support/ticket/submit` (website_support) | nein |
| 4 | Webinare | `/event` | nein |
| 5 | Kurse | `/kurse` | ja (Seite 10) |
| 6 | Wie bestelle ich einen Kurs | `/wie-bestelle-ich-einen-kurs` | ja (Seite 6) |
| 7 | FAQ Umstellung Ebox - Gemeindecloud | `https://portal.it-kommunal.at/faqs-umstellung-zur-gemeindecloud` | nein (absolute URL) |
| 8 | FAQ IFG-Portal (Partner) | `/faqs-ifg-portal-partner` | ja (Seite 17) |
| 9 | FAQ Anonymisierungs-Portal | `/faq-anonymisierungs-portal` | ja (Seite 18) |
| 10 | FAQS IFG-Portal (Kunden) | `/faqs-ifg-portal-kunden` | ja (Seite 19, **nicht veroeffentlicht**) |

Befund: Menuepunkt 7 zeigt auf eine **nicht veroeffentlichte** Seite -> im Livebetrieb HTTP 404
(geprueft 11.11.2026). Menuepunkt 10 ebenso 404. Zwei der zehn Menuepunkte laufen damit ins Leere.

Odoo 18: 8 Menues, davon zwei Wurzelmenues (`Default Main Menu` id 1, `Top-Menue fuer Website 1`
id 4) mit je Home, Events, Contact us. Das ist doppelte Demolage, keine fachliche Struktur.

## 4 Seiten

17 Seiten, alle als QWeb-View mit `<t t-call="website.layout">` (identische Bauform wie Odoo 18,
ein 1:1-Import des Rahmens ist technisch moeglich). Kennzahlen je Seite:

| id | Name | URL | veroeff. | Text (Zeichen) | FAQ-Aufklapper | Inhalt |
|---|---|---|---|---|---|---|
| 1 | Webseite | `/` | ja | 2.278 | 0 | ITK-Startseite: Produkte bestellen (Online-Formulare, IFG-Portal, Cloud-Speicher, Hinweis-Portal, Amtssignatur), Support & Anfragen |
| 2 | Contact Us | `/mailto:office@it-kommunal.at` | ja | 142 | 0 | Odoo-Standardseite, Formular entfernt, URL verbogen |
| 3 | About us | `/aboutus` | ja | 302 | 0 | **Odoo-Demotext** ("Great products for great people") |
| 4 | Thanks (Contact us) | `/contactus-thank-you` | ja | 163 | 0 | Modulseite `website_crm` (Danke-Seite) |
| 5 | Kurse (Kopie) | `/kurse2` | nein | 80.820 | 70 | Kopie der Kursseite |
| 6 | Wie bestelle ich einen Kurs | `/wie-bestelle-ich-einen-kurs` | ja | 2.133 | 4 | Anleitung Voucher-Bestellung + FAQ |
| 7 | test | `/test` | nein | 0 | 0 | leer |
| 9 | Sicherung | `/sicherung` | nein | 0 | 0 | leer |
| 10 | Kurse | `/kurse` | ja | 64.099 | 54 | vollstaendiger Kurskatalog der Staedtebund-Academy (statischer Text, 72 Ueberschriften, Preistabelle) |
| 11 | FAQs Umstellung zur Gemeindecloud | `/faqs-umstellung-zur-gemeindecloud` | nein | 17.549 | 32 | 26 Fragen zur E-Box-Umstellung |
| 12 | Testseite | `/testseite` | nein | 47 | 0 | Odoo-Snippet-Demotext |
| 13 | FAQs Umstellung ... - Sicherung | `/faqs-umstellung-zur-gemeindecloud-1` | nein | 8.033 | 15 | aeltere Fassung von id 11 |
| 14 | Gemeindecloud.at | `/gemeindecloud-at` | ja | 993 | 0 | Bundeslaender-Adressen der Gemeindecloud |
| 16 | FAQs Staedtebund-Academy | `/faqs-staedtebund-academy` | ja | 1.988 | 6 | FAQ Katalog-Buchung, 3 eingebettete Bilder |
| 17 | FAQ IFG-Portal (Partner) | `/faqs-ifg-portal-partner` | ja | 16.600 | 33 | 49 Ueberschriften, 1 verweistes Bild |
| 18 | FAQ Anonymisierungs-Portal | `/faq-anonymisierungs-portal` | ja | 3.896 | 14 | 20 Ueberschriften |
| 19 | FAQS IFG-Portal (Kunden) | `/faqs-ifg-portal-kunden` | nein | 18.049 | 33 | 49 Ueberschriften, im Menue verlinkt |

Live-Pruefung (HTTP GET, 11.11.2026): alle 10 veroeffentlichten Seiten HTTP 200, alle 7 nicht
veroeffentlichten HTTP 404. Die Seite 2 ist nur unter der krummen URL `/mailto:office@it-kommunal.at`
erreichbar (HTTP 200), `/contactus` gibt es in Odoo 11 **nicht** (404).

Sitemap Odoo 11: 143 URLs (102 Event-Eintraege, 4 Umfrage-Routen aus 2 Umfragen,
10 `/support/*`-Routen, 14 Shop-Routen, 10 eigene Seiten). Sitemap Odoo 18 VM: 106 URLs. Die Odoo-11-Sitemap nennt als Basis
`http://93.189.27.136` (IP statt Domain) - eine Altlast der Konfiguration, kein Seiteninhalt.

## 5 Formulare

- Odoo 11 hat **kein** Formular auf einer Website-Seite (`<form` kommt in keiner der 17 Seiten
  vor). Die Kontaktseite enthaelt nur einen Mail-Link; die Bestellungen laufen ueber externe
  Formulare (amtsweg.gv.at, IFG-Portal, Cloud-Speicher).
- `website_crm.contactus_form` (View 1555) ist vorhanden, aber auf keiner Seite platziert.
- Die einzigen echten Odoo-Formulare sind die Helpdesk-/Support-Funktionen (`website_support`,
  `/support/ticket/submit`, 1.261 Tickets) - **Bereich Helpdesk, abgenommen und gesperrt**.
- Odoo 18: Kontaktseite `/contactus` bringt das Standardformular mit (`s_website_form` ->
  `crm.lead`, Standardteam). Funktionalitaet ist damit vorhanden, ohne Nachbau.

## 6 Felder

`website.page`: Odoo 18 hat alle in Odoo 11 benutzten Felder. Unterschiede:

| Feld | Odoo 11 | Odoo 18 |
|---|---|---|
| Veroeffentlichung | `website_published` (Label "Im Website sichtbar") | `is_published` (Label "Auf der aktuellen Website sichtbar"); `website_published` bleibt als Alias |
| Indizierung | `website_indexed` ("Seite indiziert") | gleich, Label "Ist indiziert" |
| nur Odoo 11 | `field_parent`, `model_ids`, `website_ids` | entfallen (Mehrwebsite ueber `website_id`) |
| nur Odoo 18 | - | `visibility`/`visibility_password` (Passwortschutz), `is_in_menu`, `header_visible`/`footer_visible`/`header_overlay`, `is_seo_optimized`, `website_meta_og_img`, `arch_prev`/`arch_updated`, `track`, `theme_template_id` |
| SEO-Felder | vorhanden, **alle leer** (0 Seiten mit Meta-Titel/-Beschreibung) | vorhanden |

`website.menu`: identische Kernfelder. Nur Odoo 11: `parent_left`/`parent_right` (Nested-Set).
Nur Odoo 18: `parent_path`, `group_ids` (Menue je Benutzergruppe), `is_mega_menu` +
Mega-Menue-Felder, `controller_page_id`.

`link.tracker`: identische Kernfelder (`url`, `title`, `count`, `short_url`, `campaign_id`,
`medium_id`, `source_id`). Nur Odoo 11: `mass_mailing_campaign_id`, `icon_src`, `favicon`.
Nur Odoo 18: `absolute_url`, `label`.

`website`: Odoo 18 hat alle benutzten Felder (Name, Domain, Standardsprache, Social,
Analytics, CRM-Standardteam, CDN). Zusaetzlich `robots_txt`, `cookies_bar`,
`google_search_console`, `plausible_*`, `block_third_party_domains`.

## 7 Ansichten, Buttons, Aktionen, Filter

| Objekt | Odoo 11 | Odoo 18 |
|---|---|---|
| Aktionsliste Seiten | "Website Pages" (id 400, `tree,form`) - **an kein Menue gehaengt**, nur als Aktion vorhanden | "Website Pages" (id 1249, `list,kanban`), Menue `Website/Site/Inhalt/Seiten` |
| Spalten Seitenliste | name, url, website_indexed, website_published, create_uid (unsichtbar), write_uid, write_date | is_homepage, name, website_url, view_id, website_indexed, is_in_menu, is_seo_optimized, is_published, create_uid, write_uid, write_date, track |
| Filter Seitensuche | keine (Standard-Suchview) | Veröffentlicht / Nicht veröffentlicht / Verfolgt / Nicht nachverfolgt |
| Menue-Liste | Aktion 401 `list` (an kein Menue gehaengt) | Aktion 1240 `list,form`, Menue `Website/Site/Menü-Editor`; Spalten sequence, name, url, is_mega_menu, new_window, parent_id, group_ids |
| Link-Tracker | Aktion 93 `tree,form,graph` + 2 Klickstatistiken | Aktion 1132 `list,form,graph` + 1134 |
| Backend-Menue `Website` | Dashboard, Konfiguration (Einstellungen, eCommerce, Produkte), Auftraege, Katalog, Berichtswesen (alles `website_sale`) | Site (Homepage, Menü-Editor, Inhalt/Seiten, Veranstaltungen, Diese Seite inkl. SEO/HTML-CSS/Link-Tracker), Berichtswesen (Analytics, Besucher, Seitenansichten), Konfiguration |

Damit fehlt Odoo 11 **keine** Backend-Funktion: die Seiten- und Menueverwaltung war dort nur
nicht im Menue verlinkt (Editor im Frontend). Odoo 18 bietet sie zusaetzlich im Backend.

## 8 Rechte und Record Rules

`website.page`/`website.menu`: Lesen fuer alle, Schreiben nur fuer die Designer-Gruppe - in beiden
Versionen gleich aufgebaut (Odoo 11: ACL "Web Page Manager"/"Web Menu Manager" auf Gruppe 50
`Website / Editor and Designer`; Odoo 18: ACL 1779/1776 auf Gruppe 613).

| Gruppe | Odoo 11 aktive Benutzer | Odoo 18 lokal/VM aktive Benutzer |
|---|---|---|
| Redakteur und Designer | 37 | 2 |
| Eingeschraenkter Editor | 41 | 14 |
| Website Support / Manager (Odoo 11) | 6 | entfaellt (Helpdesk) |

Record Rules Odoo 18: `website.page` - Portal/Public liest nur veroeffentlichte Seiten;
`website.menu` - Menues mit `group_ids` nur fuer die jeweilige Gruppe. Odoo 11 hat keine
entsprechende Menue-Regel (Menue-Gruppen gibt es erst ab Odoo 18) und 0 eigene Regeln auf
`website.page` (Schutz erfolgt dort ueber die Sichtbarkeit im Controller).
Folge: die Rechte sind strukturell gleich, die **Benutzerzuordnung** ist offen (Entscheidung E10).

## 9 Automatisierungen

Odoo 11: **kein** Website-Cron. Die beiden website-nahen Crons betreffen andere Bereiche:
"Update SLA Timer" (`website.support.ticket`, Helpdesk, gesperrt) und "Event: Mail Scheduler".
Odoo 18: "Website Visitor : clean inactive visitors" (1x taeglich) - Zusatzfunktion, stoert nichts.
Keine Server Actions, keine Automation Rules im Website-Bereich auf beiden Seiten.

## 10 Beziehungen

- **CRM**: Odoo 11 `website.crm_default_team_id` = "Vertriebskanäle (Intern)" (id 1),
  `salesteam_id` = "Webseite" (id 2), `crm_default_user_id` leer.
  Odoo 18 lokal/VM: `crm_default_team_id` = "Sales" (id 1). -> E11.
- **Kontakte**: Die Website legt in Odoo 11 keine Kontakte an (kein Formular in Benutzung).
- **Produkte/Shop**: 658 Produkte, davon **0 veroeffentlicht**; `/shop` liefert "Es ist kein
  Produkt vorhanden."; 6 Entwurfs-Auftraege, 2.356 bestaetigte Auftraege (Bereich Verkauf,
  gesperrt). Odoo 18: `website_sale` nicht installiert.
- **Events**: 121 Events, 101 veroeffentlicht; `/event` ist Menuepunkt 4. Events sind
  abgenommen und gesperrt, die 121 Events liegen bereits in Odoo 18 (lokal und VM je 121).
- **E-Mail-Marketing**: 8 Listen, 13.501 Kontakte, 141 Mailings - Bereich gesperrt
  (Menuepunkt "Webinare"/`/unsubscribe_from_list` betroffen, keine Aenderung).
- **Kampagnen/Quellen (link.tracker)**: Odoo 11 16 Kampagnen, 9 Medien, 220 Quellen;
  Odoo 18 0 Kampagnen, 10 Medien, 10 Quellen. Fuer eine Link-Migration muessen die utm-Werte
  mitgemappt werden (E9).
- **Tags/Kategorien**: keine Website-Kategorien in Benutzung.

## 11 Deutsche Bezeichnungen

- Seitenamen: 4 der 17 sind englisch benannt ("Contact Us", "About us", "Thanks (Contact us)",
  "test"), die Inhalte sind deutsch. Reine ITK-Seiten sind deutsch benannt.
- Menues, Aktionen und Felder sind in Odoo 11 uebersetzt (z.B. `Website-Seiten`, "Im Website
  sichtbar", "Seite indiziert"). Odoo 18 ist an diesen Stellen ebenfalls deutsch, teilweise
  anders formuliert: "Ist indiziert", "Auf der aktuellen Website sichtbar",
  "Redakteur und Designer" (Odoo 11: "Editor und Designer").
- Odoo-18-Backendmenue Website ist deutsch: Site, Menü-Editor, Inhalt/Seiten,
  Veranstaltungen, Diese Seite, Eigenschaften, SEO optimieren, HTML-/CSS-Editor,
  Link-Tracker, Berichtswesen/Analytics/Besucher/Seitenansichten, Konfiguration.
- Offen (Wortlaut): "Site" (Odoo 18) hat kein Odoo-11-Gegenstueck; Odoo 11 nannte den
  Seitenbereich nur im Editor "Seiten". Vorschlag: Odoo-18-Standard belassen (E13).

## 12 Odoo-18-Zusatzfunktionen (bleiben erhalten)

Website-Editor mit Bausteinen und Vorschau, Seitenverwaltung im Backend inkl. Kanban,
Passwortschutz je Seite, Mega-Menue, Menue je Benutzergruppe, SEO-Panel mit Optimierungsanzeige,
`robots.txt`-Editor, URL-Umleitungen (`website.rewrite`), Besucher-/Seitenansichten-Statistik,
Cookie-Hinweis (`website_cookie_notice`), Debranding (Repo-Modul), dynamische Snippets,
Karten-/Formularbaustein. Keine davon beeintraechtigt Odoo-11-Funktionalitaet.

## 13 Technisches Risiko einer 1:1-Uebernahme der Seiteninhalte

Die Seiteninhalte sind Bootstrap-3-Markup aus dem Odoo-11-Editor. Odoo 18 liefert
**Bootstrap 5** und andere Bausteine. Belegt im Container (11.11.2026):

- `bootstrap.css` in Odoo 18 enthaelt **0** Treffer fuer `panel-group` und **0** fuer `jumbotron`
  (Bootstrap 3 hat beides, Odoo 11 nutzt beides).
- Odoo 18 rendert Aufklapper ueber `data-bs-toggle` (13 Treffer in `website/views`),
  `data-toggle` kommt dort **0**-mal vor. Die Odoo-11-Seiten haben 261 `data-toggle`-Aufklapper.
- Betroffene Klassen in den 17 Seiten: `col-md-offset-*` 5x, `jumbotron` 2x,
  `pull-left`/`pull-right` 15x, `panel*` 1.384x (steckt im FAQ-Aufklapper),
  Font-Awesome-4-Icons 16x, dazu die Odoo-11-Bausteine `s_big_message`, `s_feature_grid`,
  `s_button`, `s_panel` (in Odoo 18 nicht vorhanden; `s_faq_collapse`, `s_text_block`,
  `s_title`, `s_button` gibt es, aber mit anderem Innenaufbau).
- Folge bei unveraenderter Uebernahme: FAQ-Antworten bleiben zugeklappt und lassen sich nicht
  oeffnen (die Klasse `collapse` bleibt ohne Bootstrap-3-JS), Spaltenversaetze und die
  Jumbotron-Bloecke verlieren ihre Gestaltung.
- Zusaetzlich: die Inhalte enthalten 3.482-mal den Text `&amp;nbsp;` und 66-mal `&amp;amp;`,
  also doppelt escapte Zeichen. Sie werden **heute schon** in Odoo 11 als sichtbarer Text
  "&nbsp;" angezeigt (nachgewiesen am Liveabruf `/kurse`: 1.261 sichtbare "&nbsp;").

Damit ist die Uebernahme der Inhalte eine echte Entscheidung (E1-E3), keine Formsache.

## 14 Bilder und Dateien

- Seite 16: 3 Bilder als Base64 direkt im Seiteninhalt (selbsttragend, keine Datei noetig).
- Seite 17: 1 Bild als Anhang `ir.attachment` id 54092 "Screenshot 2025-07-29 Bild FAQ.png"
  (16.719 Byte, oeffentlich, `store_fname` b6/b6402df6...). Datei muss mit migriert werden.
- Seite 1: Hintergrundbild ueber `/web/image/website.s_background_image_01` - dieser Pfad
  liefert in Odoo 11 **und** Odoo 18 dieselbe Datei (identischer SHA1
  `fdad1b8c19d8561eecf9d6cc7f00a3e59888a8e3`, 133.894 Byte). Kein Handlungsbedarf.
- Anhaenge gesamt: Odoo 11 12.594, Odoo 18 lokal 420, VM 424.

## 15 Datenmigration: Umfang (Vorschlag, noch nicht freigegeben)

| Datensatz | Odoo 11 | Ziel in Odoo 18 | Weg |
|---|---|---|---|
| `website.page` | 17 (Auswahl offen, E1/E4) | `website.page` + `ir.ui.view` | `arch_db` je Seite, Name, URL, Key, Veroeffentlichung, Indizierung |
| `website.menu` | 11 | `website.menu` + Menue-Verknuepfung auf die neue Seite | Hierarchie, Sequence, URL, `new_window` |
| `website` | 1 | der bestehende Datensatz (id 1) | Name, Domain, Sprache, Social, CRM-Team (E11) |
| `link.tracker` | 837 / 563 Klicks | `link.tracker` | `url`, `title`, `count`, `short_url`, Kampagne/Medium/Quelle (E9) |
| `ir.attachment` | 1 (id 54092) | `ir.attachment` (oeffentlich, ohne Datensatzbezug) | Datei + Datensatz |
| `rating.rating` | 0 | - | nichts zu tun |
| Cookies/Crons/Regeln | keine | Odoo-18-Standard | nichts zu tun |

Idempotenz-Vorschlag: Schluessel je Seite = `key` (z.B. `website.kurse`), sonst `url`; Menue =
`url` + Elternpfad + Sequence; Link-Tracker = `url` + `title` + Kampagne. Vorhandene Datensaetze
werden aktualisiert, nicht neu angelegt; ein zweiter Lauf muss 0 Neuanlagen melden.

Nicht Gegenstand dieses Bereichs (bleibt wie beschlossen): Helpdesk-Tickets (`website_support`),
Events, E-Mail-Marketing, Kontakte, Umfragen (`survey`), Produkte/Shop, Rechnungen.

## 16 Entscheidungspunkte (nichts davon umgesetzt)

- **E1 Inhalt der Seiten.** Wie sollen die Seiteninhalte nach Odoo 18 kommen?
  A) 1:1 HTML uebernehmen (schnell, Layout an mehreren Stellen kaputt),
  B) Markup automatisch auf Odoo 18 umschreiben (`col-md-offset` -> `offset-md`,
  `pull-*` -> `float-*`, `jumbotron` -> Karte mit Abstand, FAQ-Aufklapper -> Odoo-18-Akkordeon),
  C) Seiten im Editor neu bauen und nur die Texte uebernehmen.
  Empfehlung: **B**, je Seite Browserabnahme; C nur fuer Seite 1 (Startseite), wenn sie
  gestalterisch neu soll.
- **E2 FAQ-Aufklapper (261).** Aufklappbar wie Odoo 11 (Umbau auf `website.s_accordion`) oder
  offen darstellen (alle Antworten sichtbar)? Empfehlung: aufklappbar, 1:1 wie heute.
- **E3 Doppelt escapte Zeichen.** 3.482x `&nbsp;` und 66x `&amp;` bereinigen (in Odoo 11 heute
  als Text sichtbar) oder unveraendert uebernehmen? Empfehlung: bereinigen, Aenderung je Seite
  dokumentieren.
- **E4 Welche der 7 nicht veroeffentlichten Seiten uebernehmen?** Kandidaten: id 11 (FAQ
  Gemeindecloud, 17.549 Zeichen, im Menue verlinkt), id 19 (FAQs IFG Kunden, 18.049 Zeichen);
  nicht uebernehmen: id 5 (Kopie Kurse), 7 (test), 9 (leer), 12 (Testseite), 13 (Sicherung).
- **E5 Odoo-Standardseiten.** "About us" (Demotext), "Contact Us" (Formular entfernt, URL
  `/mailto:...`) und "Thanks" aus Odoo 11 nicht uebernehmen, Odoo-18-Standard behalten?
  Empfehlung: ja, nur ITK-Inhalte migrieren.
- **E6 Menues.** 10 Punkte wie Odoo 11 uebernehmen, Wurzelname "Top Menu"? Und soll der
  Menuepunkt 7 (FAQ Umstellung Ebox) auf die interne Seite zeigen (heute 404), und Punkt 10
  (FAQs IFG Kunden) erst nach Veroeffentlichung sichtbar sein?
- **E7 Shop (`website_sale`).** Odoo 11 hat das Modul installiert, aber 0 veroeffentlichte
  Produkte, `/shop` = "Es ist kein Produkt vorhanden", Kopfzeile zeigt "Mein Warenkorb" und
  "Anmelden". In Odoo 18 installieren (Optik wie Odoo 11) oder weglassen (Shop unbenutzt)?
  Empfehlung: weglassen, Warenkorb/Anmelden entfallen.
- **E8 Bewertungen.** `website_rating` hatte 0 Datensaetze und existiert in Odoo 18 nicht ->
  nicht nachbauen. Bestaetigung erbeten.
- **E9 Link-Tracker.** 837 Links mit 563 Klicks migrieren? Die Kurz-URLs lauten kuenftig
  `<Odoo-18-Domain>/r/xxx` (Odoo 11: `http://portal.it-kommunal.at/r/xxx`); Kampagnen/Quellen
  werden mitgemappt (Odoo 18 hat 0 Kampagnen, 220 Quellen gegen 10).
  Empfehlung: ja, mit Klickzahlen; Kampagnen/Quellen vorher anlegen.
- **E10 Website-Rechte.** Odoo 11: 37 Redakteur+Designer, 41 eingeschraenkter Editor;
  Odoo 18: 2 bzw. 14. Sollen die Website-Rechte je Benutzer (Login) 1:1 nachgezogen werden?
  Das beruehrt die Benutzerverwaltung und braucht eine eigene Freigabe.
- **E11 Website-Einstellungen.** Odoo 11: Name "ITK Portal", Domain `localhost` (defekt),
  Twitter `@IT_Kommunal`; Odoo 18: Name "IT-Kommunal", Domain `https://www.it-kommunal.at`.
  Welche Werte gelten (Name, Domain fuer Test-VM vs. Produktion, Social, CRM-Standardteam
  "Vertriebskanäle (Intern)" statt "Sales")?
- **E12 Cookie-Hinweis.** Odoo 11 hat kein Cookie-Modul; Odoo 18 hat `website_cookie_notice`
  aktiv mit englischem Text ("This website uses cookies..."). Deutsch uebersetzen, im
  Seitenfuss belassen oder abschalten?
- **E13 Wortlaute.** "Site" bleibt Odoo-18-Bezeichnung; Seiten-/Menueverwaltung im Backend
  bleibt Odoo 18 (Odoo 11 hatte sie nur im Frontend-Editor). Bestaetigung erbeten.
- **E14 Demodaten in Odoo 18.** Doppelte Home-Seite (id 2/4), zwei Wurzelmenues, Demo-Besucher
  und Demo-Seitenansichten duerfen entfernt werden. Bestaetigung erbeten (lokal und VM).

## 17 Nadelfunde, die im Abschlussbericht stehen muessen

1. Zwei Odoo-11-Menuepunkte fuehren im Livebetrieb auf HTTP 404 (Punkt 7 und 10), weil die
   Zielseiten nicht veroeffentlicht sind.
2. Die Odoo-11-Kontaktseite ist nur unter `/mailto:office@it-kommunal.at` erreichbar;
   `/contactus` ist 404. Das Kontaktformular ist nicht platziert.
3. Die Odoo-11-Seiten zeigen an 3.482 Stellen den Text `&nbsp;` und 66-mal `&amp;` an
   (doppelt escapt).
4. `website.domain` steht in Odoo 11 auf `localhost`, die Sitemap nennt die IP
   `93.189.27.136` - beides Altlasten, in Odoo 18 bereits auf `https://www.it-kommunal.at`.
5. Der Odoo-11-Seiten-Editorzustand enthaelt keinerlei SEO-Texte (0 von 17 Seiten).
6. Die Odoo-18-Website ist reine Demolage (2 Home-Seiten, 2 Wurzelmenues, Odoo-Mustertext).
