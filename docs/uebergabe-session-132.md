# Übergabe Session 132 → 133 — Bereich Helpdesk (Odoo 11 → Odoo 18)

Stand: 08.10.2026. Diese Datei ist der Einstieg für die nächste Session.

## 1. Auftrag und Ergebnis

Auftrag: Helpdesk in Odoo 18 fachlich und funktional so aufbauen, dass die
Arbeit aus Odoo 11 (OCA `website_support`) möglich ist - **ohne Migration der
1.223 Odoo-11-Tickets** -, danach vollständige Abnahme, Regression, Merge,
VM-Nachzug und Dreistand. Zusätzlich: Produktivstart-Konfiguration umsetzen.

Ergebnis: technisch und fachlich fertig, produktionsbereit bis auf zwei
externe Werte (Abschnitt 5).

## 2. Arbeitsregeln (unverändert)

- Odoo 11 nur lesend; keine Helpdesk-Altdaten migrieren; keine Testdaten
  zurücklassen (Bestand vorher = nachher); Abnahme nur mit echtem Browserbild.
- Menüs/Labels über technische Kennungen, nie über Namen; bei Mehrdeutigkeit
  Abbruch und Kandidaten vorlegen.
- Abrechnung ist abgeschlossen und wird nicht angefasst.

## 3. Was umgesetzt wurde

Module: `itk_helpdesk_compat` 18.0.1.1.3, `itk_helpdesk_category_user`,
`itk_crm` 18.0.1.5.10 (Aktivitäten-Fix).

- Vier Odoo-11-Kanäle (Email, Manual, Website (Public), Website (User)),
  Kanal automatisch aus dem Entstehungsweg; OCA-Kanal „Web" archiviert.
- Öffentliches Formular `/support/ticket/new` ohne Anmeldung mit Honigtopf,
  Rate-Limit und reCAPTCHA-Vorbereitung; reCAPTCHA greift, sobald Schlüssel da sind.
- Ticketnummern fortlaufend, lückenlos, ohne Präfix.
- Liste (acht Odoo-11-Spalten), Kanban, Formular, Suche, Filter, Gruppierung,
  Stufen, Prioritäten, Kategorien/Unterkategorien, Zusatzfelder, deutsche Labels.
- Produktivstart-Konfiguration: Team „IT-Kommunal Support" (SLA aktiv, im Portal
  sichtbar, Alias `help`), SLA „Standard SLA Support ITK Produkte" (48 h,
  Kategorien amtsweg.gv.at, Amtssignatur, E-Learning, Verwaltungsmanager,
  Zielstufe Geschlossen/Behoben, on Hold pausiert die Frist), 4 Prioritäten mit
  Odoo-11-Farben, 17 Kategorien, 20 Unterkategorien, Kanäle wie Odoo 11.

## 4. Nachweise

- Browser lokal: 58 OK / 1 Meldung (Werkzeuggrenze: die Stufe „on Hold" ist in
  der Statusleiste eingeklappt und wird vom Prüfskript nicht aufgeklappt).
- Browser VM: 55 OK / 4 Meldungen (drei davon: die Textsuche im Menüband der VM
  findet „Support Tickets" und „Arbeitszeittabelle" nicht - per RPC widerlegt,
  die Menüs existieren als Helpdesk/Support Tickets und Helpdesk/Arbeitszeittabelle;
  eine wie lokal die eingeklappte Stufe „on Hold").
- SLA-Mechanik per RPC belegt: Frist 48 h, `on_hold` bei Stufe „on Hold"
  (Frist wird nicht gezählt), Rückkehr nach „in Bearbeitung" setzt dieselbe
  Frist fort, „Geschlossen/Behoben" beendet die SLA als erfüllt.
- Aktivitäten: Anlegen im Chatter von Ticket und Kontakt geprüft.
- Regression: 886 OK / 0 FEHL (elf Prüfläufe, lokal und VM).

## 5. Offene Punkte (nur externe Produktivparameter)

1. `mail.catchall.domain` - die reale Mail-Domain der Organisation. Erst damit
   ist die Adresse des Team-Alias (`help@…`) vollständig und der E-Mail-Kanal
   per Mail-Eingang produktiv. Es gibt in Odoo 11 keinen Ticket-Alias; der
   vorhandene Alias heißt `help` und wurde nicht erfunden.
2. `recaptcha_public_key` und `recaptcha_private_key` - Site-Key und Secret-Key
   von Google reCAPTCHA. Honigtopf und Rate-Limit arbeiten unabhängig davon.

Optionale Werte, die keine Entscheidung blockieren: `mail.default.from`
(Absender der Benachrichtigungen; derzeit greift der Odoo-11-Wert
„ITK-Support <office@it-kommunal.at>"), Teamleiter des Helpdesk-Teams.

## 6. Dokumente

- `docs/o11-o18-helpdesk-vergleich.md` - Iststand, Vergleich, Umsetzung.
- `docs/o11-o18-helpdesk-abnahme.md` - Prüfumfang und Befunde.
- `docs/o11-o18-helpdesk-produktivstart.md` - Konfiguration und ihre Werte.
- Werkzeuge: `scripts/helpdesk_produktivstart.py` (Konfiguration, idempotent,
  `--pruefen` schreibt nichts), `browser_helpdesk_abnahme.py`, `helpdesk_bestand.py`,
  `erhebe_helpdesk_o11*.py`, `erhebe_helpdesk_o18.py`, `vergleiche_helpdesk_labels.py`.

## 7. Systeme, Zugang und Stand

- Lokal: Docker-Compose in `C:\Odoo-Test`, Odoo unter `http://localhost:8069`,
  Testdatenbank `odoo18_test`, DB-Volume `odoo18_pgdata` (VM: `odoo18_odoo18_pgdata`).
- VM: `k001959vsx.ipax.at`; Shell nur über `$LOCALAPPDATA/Temp/vm_exec.py`
  (Paramiko, Passwortdatei `vm_pw.txt`), SSH nur mit VPN/Teleport, sonst Port 443.
  **Falle:** die VM hat in `/opt/odoo18/.env` keine Odoo-Zugangsdaten - alle
  Skripte laufen vom lokalen Client und werden mit `--instanz lokal|vm` gesteuert.
- Odoo 11 (Produktion): `portal.it-kommunal.at`, nur lesend, Client
  `scripts/_o11o18_client.py`.
- Upgrade-Befehl: `docker compose run --rm --no-deps -T odoo odoo -u <modul> -d
  odoo18_test --stop-after-init`, danach Neustart. `.po` greift nur mit
  `--i18n-overwrite`, Python-Labels erst nach dem Neustart.
- Dreistand bei Sitzungsende: main = lokal = GitHub = VM =
  `ca1281de9de0d2300f06da7fdd4410eb0f6b0ce4`, Baum
  `4e88ea969c42ba3ed7a8589e8744c07eaadc5679`, Nachweis
  `0967fb23baacd2453272760c758b62ac1b07ad22`, Arbeitsbäume sauber (PR #224).
- Git-Weg: Arbeitsbranch pushen, PR über `scripts/github_pr.py` (kein gh-CLI),
  selbst mergen, VM auf main nachziehen. Kein Force-Push, kein Rebase.

## 8. Pflichtlektüre in dieser Reihenfolge

1. Memory und USER-Profil (Arbeitsregeln, Sprachregeln, Berichtsraster).
2. Skill `odoo-migration-ops` samt `references/`.
3. `PROJECT_KNOWLEDGE.md` und die Migrations-Checkliste.
4. Diese Übergabedatei, dann die drei Helpdesk-Dokumente (Abschnitt 6).
5. Den neuen Bereich zuerst read-only in Odoo 11 erheben, dann mit Odoo 18
   (lokal und VM) vergleichen und die Abweichungsliste als Entscheidungsgrundlage
   vorlegen - erst danach ändern.

## 9. Nächster Schritt

Helpdesk ist abgeschlossen - keine weiteren Änderungen ohne neuen Auftrag.
Kandidaten für den nächsten Bereich: Preislisten/Regeln, Abonnements, Produkte,
CRM/Partner. Vorgehen wie bisher: zuerst read-only-Erhebung in Odoo 11 gegen
Odoo 18 (lokal und VM), daraus eine Abweichungsliste als Entscheidungsgrundlage.
