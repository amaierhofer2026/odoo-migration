# Uebergabe Session 141 -> 142

Stand: 11.11.2026. Diese Datei ist der Einstieg fuer die naechste Session.

## 1 Gesperrter Stand (nicht ohne ausdruecklichen Auftrag aendern)

| Bereich | Status |
|---|---|
| Projekt | ABGENOMMEN und GESPERRT |
| Personal | ABGENOMMEN und GESPERRT |
| Zeiterfassung | ABGENOMMEN und GESPERRT |
| Anwesenheiten / Urlaubsantraege | ABGENOMMEN und GESPERRT |
| Verkauf | ABGENOMMEN und GESPERRT |
| Abonnements | ABGENOMMEN und GESPERRT |
| Abrechnung | MIGRATIONSBEREIT (Struktur), Datenmigration offen |
| Helpdesk | ABGENOMMEN und GESPERRT |
| Events | ABGENOMMEN und GESPERRT |
| E-Mail-Marketing | ABGENOMMEN und GESPERRT |
| Massenbearbeitung | ABGENOMMEN und GESPERRT (05.11.2026, Session 140) |
| **Website / Webinhalte** | **Bestandsaufnahme fertig, Entscheidungen E1-E14 offen** |

## 2 Neue Projektregel seit 11.11.2026 (Anna): Datenmigration gehoert zum Modul

Ein Bereich gilt erst als ABGENOMMEN, wenn auch seine fachlichen Daten aus Odoo 11 migriert und
geprueft sind. Ablauf je Bereich: Trockenlauf, Anzahl und Mapping dokumentieren, Abhaengigkeiten
pruefen, idempotenter Schreiblauf (zweiter Lauf = 0 Neuanlagen, vorhandene Saetze aktualisieren,
nie O11-IDs als Bruecke), O11-Anzahl gegen O18-Anzahl, Browserstichproben, Beziehungen, Summen,
Browserabnahme lokal UND VM, Rechtepruefung, Regression, Testdaten entfernen, Doku,
Commit/Push/PR/Merge, VM auf main, Dreistand lokal = GitHub = VM.

Ausnahmen bleiben: keine historischen Helpdesk-Tickets, keine personenbezogenen Event- und
E-Mail-Marketing-Daten. Odoo-18-Demo-/Testdaten duerfen entfernt oder ueberschrieben werden.

Abschlussbericht-Pflichtfelder: technisch fertig, fachlich fertig, Datenmigration abgeschlossen,
O11-Datensaetze, O18-Datensaetze, neu migriert, aktualisiert, bewusst nicht migriert, technisch
nicht uebertragbar, Dubletten, Browser lokal, Browser VM, Rechte, Regression, Testdaten entfernt,
Dreistand identisch, offene Blocker.

## 3 Was Session 141 gemacht hat (nur gelesen, nichts geaendert)

Bereich **Website / Webinhalte** read-only erhoben: Odoo 11 Prod `ITK_V1_a` per JSON-RPC
(`search_read`/`read`/`fields_get`) plus oeffentliche HTTP-GETs, Odoo 18 lokal und VM per RPC.
Kein Testdatensatz, keine Modulinstallation, kein Commit.

Neu im Arbeitsbaum (noch nicht committet):
- `docs/o11-o18-vergleich-website.md` - vollstaendiger Vergleich, Entscheidungspunkte E1-E14
- `scripts/analyse_o11_website.py` - read-only Bestandsaufnahme (`--json`, `--seiten-arch`)

Zahlen Odoo 11: 17 Seiten (10 veroeffentlicht, 7 nicht), 11 Menues, 217.092 Zeichen sichtbarer
Seitentext, 261 FAQ-Aufklapper, 837 Link-Tracker-Eintraege mit 563 Klicks, 0 Bewertungen,
0 SEO-Texte, Shop installiert aber 0 veroeffentlichte Produkte.

Zahlen Odoo 18 (lokal = VM): 4 Demo-Seiten (zwei mit URL `/`), 8 Menues aus 2 Wurzelmenues,
0 Link-Tracker, 3 Demo-Besucher, 8 Demo-Seitenansichten. `website_sale` nicht installiert,
`website_rating` existiert nicht mehr, `website_form` ist in `website` aufgegangen,
`website_support` durch `helpdesk_mgmt` ersetzt (gesperrt).

Technisches Hauptrisiko: Seiteninhalte sind Bootstrap 3. Odoo 18 liefert Bootstrap 5
(`bootstrap.css` ohne `panel-group` und `jumbotron`; `website/views` nur mit `data-bs-toggle`).
Unveraendert uebernommen bleiben die 261 FAQ-Antworten zugeklappt und nicht bedienbar,
Spaltenversatz und Jumbotron verlieren die Gestaltung. Dazu 3.482-mal sichtbares "&nbsp;"
und 66-mal "&amp;" (doppelt escapte Zeichen, heute in Odoo 11 schon sichtbar).

## 4 Offene Entscheidungen (E1-E14, Details im Vergleichsdokument)

| Nr | Frage | Empfehlung |
|---|---|---|
| E1 | Seiteninhalte 1:1, Markup auf Odoo 18 umschreiben oder neu bauen | umschreiben, Seite 1 zusaetzlich gestalterisch neu |
| E2 | FAQ-Aufklapper aufklappbar oder offen | aufklappbar |
| E3 | Doppelt escapte Zeichen bereinigen | ja, je Seite dokumentieren |
| E4 | Welche der 7 nicht veroeffentlichten Seiten uebernehmen | id 11 und 19 ja; 5, 7, 9, 12, 13 nein |
| E5 | Odoo-Standardseiten aus Odoo 11 uebernehmen | nein, Odoo-18-Standard behalten |
| E6 | Menues 1:1 inkl. Wurzel "Top Menu"; Punkt 7 auf interne Seite; Punkt 10 erst nach Veroeffentlichung | ja |
| E7 | `website_sale` installieren | nein (Shop war leer) |
| E8 | `website_rating` nachbauen | nein (0 Datensaetze, Modul in O18 nicht vorhanden) |
| E9 | Link-Tracker migrieren (837/563), Kampagnen und Quellen vorher anlegen | ja |
| E10 | Website-Rechte je Benutzer nachziehen (O11 37/41, O18 2/14) | eigene Freigabe noetig |
| E11 | Name, Domain, Twitter, CRM-Standardteam | offen |
| E12 | Cookie-Hinweis (englisch) | offen |
| E13 | Wortlaute/Site im Backend | Odoo-18-Standard bestaetigen |
| E14 | Odoo-18-Demodaten entfernen | ja, lokal und VM |

## 5 Start der naechsten Session

```
cd C:\Odoo-Test
git status --short --branch && git log --oneline -3
python scripts/analyse_o11_website.py --json "$LOCALAPPDATA/Temp/website_bestand.json"
```

Regression vor dem ersten Eingriff (je `--instanz lokal` und `vm`):

```
python scripts/verify_s138_events.py --instanz lokal
python scripts/verify_s138_marketing.py --instanz lokal
python scripts/verify_personal.py --instanz lokal
python scripts/verify_s135_projekt.py --instanz lokal
python scripts/abschluss_verkauf_regression.py
python scripts/apply_massenbearbeitung.py --instanz lokal --pruefen
```

## 6 Git-Stand

Der gueltige Stand ist immer `git log -1`. Session 141 hat **keinen** Commit erzeugt:
`docs/o11-o18-vergleich-website.md` und `scripts/analyse_o11_website.py` liegen als
unversionierte Dateien im Arbeitsbaum (`git status` zeigt `??`).

## 7 Werkzeuge

| Datei | Zweck |
|---|---|
| `scripts/_o11o18_client.py` | RPC-Client `o11()` / `o18("lokal"\|"vm")`, read-only |
| `scripts/analyse_o11_website.py` | Bestandsaufnahme Website (Module, Seiten, Menues, Rechte, Zaehler) |
| `scripts/o11_o18_mapping.py` | 5-Spalten-Mapping fuer Stammdaten |
| `scripts/browser_form_layout.py` | echter Browser-Layoutvergleich lokal/VM |
| `scripts/upgrade_modules.py` | Modulinstallation/-update je Instanz |
| `%LOCALAPPDATA%\Temp\vm_exec.py` | Shell auf der VM (Paramiko) |

## 8 Naechster Schritt

Annas Entscheidungen E1-E14 einholen, dann: Vergleichsdokument mit den Entscheidungen ins Repo,
Bereichsmodul (Seiten, Menues, Einstellungen) bauen, Trockenlauf mit Mapping und Anzahl,
Schreiblauf idempotent, Anzahlvergleich, Browserstichproben, Browserabnahme lokal und VM,
Rechtepruefung, Regression, Testdaten raus, Doku, Commit/Push/PR/Merge, VM auf main,
Dreistand-Nachweis.

Danach offen: Umfragen/Survey (O11 2 Umfragen, 73 Teilnahmen), Valorisierung, Lager/Bestand.
