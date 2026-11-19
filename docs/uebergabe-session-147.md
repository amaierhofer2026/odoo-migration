# Uebergabe Session 147 - Umfragen / Survey, Rechteanpassung

**Status: UMFRAGEN / SURVEY = ABGENOMMEN UND GESPERRT (19.11.2026).**
Ab hier keine Aenderungen mehr an diesem Bereich.

## Auftrag

Die in Session 146 offen gebliebene Berechtigungsfrage loesen: normale Umfrage-Benutzer
sollen wie in Odoo 11 nur ihre eigenen Teilnahmen und Antworten sehen, Manager und
Administratoren weiterhin alles.

## Umsetzung

Neues Modul `addons/itk_survey_security` (18.0.1.0.0), nur Rechtekonfiguration:

- Es ueberschreibt die beiden Gruppenregeln des Moduls `survey` mit derselben XML-ID:
  `survey.survey_user_input_rule_survey_user` und
  `survey.survey_user_input_line_rule_survey_user`.
- Neue Domain: Umfragetyp wie bisher UND (`create_uid = user` ODER
  `partner_id = user.partner_id`), fuer Antwortzeilen ueber `user_input_id`.
- Die Manager-Regeln bleiben unveraendert. Odoo kombiniert Gruppenregeln mit ODER, daher
  sehen Mitglieder von "Umfragen / Administrator" weiterhin alle Antworten.
- Die Regeln liegen im Modul `survey` in einem Block `noupdate="1"`; ein survey-Upgrade
  setzt sie nicht zurueck, ein Upgrade von `itk_survey_security` schreibt sie erneut.
- Oeffentliche Umfragen (Ausfuellen ohne Anmeldung) laufen ueber den Controller mit
  erhoehten Rechten und sind nicht betroffen.

Verworfene Wege (dokumentiert in `docs/o11-o18-vergleich-survey.md`, Abschnitt 5.2):
zusaetzliche Gruppenregel (wirkungslos wegen ODER), globale Regel (haette Manager
eingeschraenkt), manueller Eingriff in der Datenbank (nicht reproduzierbar).

## Nachweise

| Pruefung | Werkzeug | Ergebnis |
|---|---|---|
| Rollen und Zugriffe | `scripts/migration/survey_rechte_pruefung.py` | 28 OK / 0 FEHL je Instanz |
| Browser inkl. URL auf fremde Antwort | `scripts/browser_survey_rechte.py` | 6 OK / 0 FEHL je Instanz |
| Anlegen/Bearbeiten unveraendert | `scripts/browser_survey_abnahme.py` | 44 OK / 0 FEHL je Instanz |
| Identitaet der Daten | `scripts/migration/survey_abgleich.py` | 409 OK / 0 Abweichungen je Instanz |
| Idempotenz | `scripts/migration/survey_migration.py` | 0/0/151/0/0 je Instanz |
| Regression | `scripts/regression_gesperrte_bereiche.py` | lokal 725 OK / 9 FEHL, VM 721 OK / 13 FEHL (Werkzeuggrenzen, siehe unten) |

## Fuer die naechste Sitzung

Der Bereich ist gesperrt. Naechstes Modul nur auf Zuruf.

Beim Arbeiten an anderen Bereichen beachten:

- Record Rules fremder Module nur per gleichnamiger XML-ID ueberschreiben, wenn sie dort
  unter `noupdate="1"` stehen; sonst driftet die Regel bei jedem Fremd-Upgrade.
- Odoo kombiniert Gruppenregeln mit ODER, globale Regeln mit AND: eine Einschraenkung
  fuer "normale" Benutzer braucht entweder eine geaenderte Gruppenregel oder eine globale
  Regel mit Ausnahme - Letzteres ist ohne Zusatzfeld nicht sauber moeglich.
- Testbenutzer brauchen `base.group_user`, sonst kein Backend-Zugriff.

## Regression im Detail (19.11.2026)

Lokal 725 OK / 9 FEHL, unveraendert zu den Sessions 145 und 146: Kontakte 4
(Formularpruefung oeffnet eine Verkaufschance), Verkauf 4 (Kalender-Randwoche 3,
Pivot vergleicht `max()` statt der Summe) und Helpdesk 1 ("on Hold" eingeklappt).

VM 721 OK / 13 FEHL:

- Kontakte 4 und Helpdesk 1: wie lokal.
- Verkauf 5: zusaetzlich "Ansicht 'Graph' geoeffnet" - die Graph-Ansicht rendert ueber
  VPN nicht immer rechtzeitig (bekannte Werkzeuggrenze aus Session 145).
- E-Mail-Marketing 3: das Werkzeug meldet die Gruppe "Odoo-11-Angaben", die Gruppe
  "Historische Kennzahlen (Odoo 11)" und den Wert "Gesendet" als fehlend. Im echten
  Browser sind sie vorhanden: textContent enthaelt "Odoo-11-Angaben", das Element hat
  `offsetParent` (ist also sichtbar), das Feld `x_o11_sent` liegt im DOM, und das
  gerenderte Formular-Arch ist lokal und VM byte-gleich (23.332 Zeichen, Gruppe
  enthalten). Werkzeug-/Layout-Effekt, keine Aenderung am Bereich.
- Personal: am 18.11. zwei Werkzeuggrenzen, heute 22 OK / 0 FEHL - der Effekt ist
  instabil und ebenfalls werkzeugseitig (Screenshot-Beleg in Session 146).

Die Rechteanpassung betrifft ausschliesslich die Modelle `survey.user_input` und
`survey.user_input.line`; an Kontakten, Verkauf, Helpdesk, Personal und E-Mail-Marketing
wurde nichts geaendert. Keine Regression durch diese Sitzung.

## Live-Drift in Odoo 11 (19.11.2026)

Odoo 11 hat nach der Migration die Teilnahme **1624** geloescht (angefangene Teilnahme an
der Testumfrage, `state = new`, keine Antwortzeile). Odoo 11: 71 Teilnahmen. Odoo 18 lokal
und VM: 72, weil der Datensatz als Historie erhalten bleibt - geloescht wird nur auf
Freigabe.

Der Abgleich meldet deshalb vier Abweichungen (Anzahl, Statusverteilung, Teilnahmen
Umfrage 1, Zeitspanne); alle anderen Pruefungen bleiben deckungsgleich. Wenn der Datensatz
auch in Odoo 18 verschwinden soll: `survey.user_input` mit `itk_o11_id = 1624` loeschen -
eine Zeile je Instanz, danach Abgleich 409/0.
