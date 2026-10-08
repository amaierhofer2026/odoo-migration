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
- Browser VM: siehe Abschlussbericht Session 132.
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

## 7. Nächster Schritt

Helpdesk ist abgeschlossen - keine weiteren Änderungen ohne neuen Auftrag.
Kandidaten für den nächsten Bereich: Preislisten/Regeln, Abonnements, Produkte,
CRM/Partner. Vorgehen wie bisher: zuerst read-only-Erhebung in Odoo 11 gegen
Odoo 18 (lokal und VM), daraus eine Abweichungsliste als Entscheidungsgrundlage.
