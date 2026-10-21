# Übergabe Session 133 → 134 — Bereich Projekt (Odoo 11 → Odoo 18)

Stand: 09.10.2026. Diese Datei ist der Einstieg für die nächste Session.

## 1. Auftrag und Ergebnis

Auftrag: das Modul Projekt in Odoo 18 fachlich wie in Odoo 11 nutzbar machen
(read-only Erhebung Odoo 11, Vergleich mit Odoo 18 lokal und VM, Umsetzung,
Abnahme, Regression, Merge, VM-Nachzug, Dreistand). Odoo 11 ausschließlich lesend,
keine Produktivdaten.

Ergebnis: fertig und abgenommen (lokal und VM). Modul `itk_project` 18.0.1.0.1,
`sale_project` und `sale_timesheet` installiert.

## 2. Arbeitsregeln (unverändert)

- Odoo 11 nur lesend; keine Produktivdaten; keine Testdaten zurücklassen
  (Bestand vorher = nachher); Abnahme nur mit echtem Browserbild.
- Menüs/Labels über technische Kennungen; bei Mehrdeutigkeit Kandidaten vorlegen.
- Abrechnung und Helpdesk sind abgeschlossen und werden nicht angefasst.

## 3. Entscheidungen (Anna, 09.10.2026) und Umsetzung

1. sale_timesheet/sale_project installieren — umgesetzt.
2. Startdatum Aufgabe wiederherstellen — als ITK-Feld `itk_date_start` (Odoo 18 hat kein
   Standardfeld).
3. Priorität Niedrig/Normal — sichtbar angeglichen, technische Werte 0/1 bleiben.
4. Menüs funktional angleichen, Odoo-18-Struktur belassen, alles deutsch.
5. Deutsche Bezeichnungen im Odoo-11-Wortlaut — Ansichten (string=) + `i18n/de.po`
   (79 Einträge, Overwrite-Ladung), keine sichtbaren englischen Begriffe mehr.
6. Projekt-Dashboard nicht nachbauen — funktional über „Projekt/Projekte" (Kanban).
7. Odoo-18-Zusatzfunktionen beibehalten, nichts ungefragt aktiviert.
8. Projektphasen deutsch: Zu erledigen / In Arbeit / Erledigt / Abgebrochen.

## 4. Nachweise

- Strukturprüfung `scripts/verify_projekt.py`: 20 OK / 0 FEHL (lokal und VM).
- Browserabnahme `scripts/browser_projekt_abnahme.py`: 26 OK / 0 FEHL (lokal und VM,
  echter Chrome; Projekt anlegen, Aufgabe, Startdatum, Priorität, Bearbeiter, Anhang,
  Chatter, Projektphase, Suche, Archivieren, Testdaten entfernt).
- Regression `scripts/abschluss_verkauf_regression.py`: 881 OK / 0 FEHL (elf Prüfläufe,
  lokal und VM).
- Keine Testdaten zurückgelassen (5 Projekte / 8 Aufgaben vorher = nachher).

## 5. Wichtige Fallen für die neue Session

- Deutsche Feldetiketten: die Ansichten (`string=`) decken die Oberfläche; für Export und
  Dialoge zusätzlich die `i18n/de.po` mit **Overwrite-Ladung** (`scripts/load_terms_de.py`),
  danach Container-Neustart. Der PO-Reader erzeugt je `#:`-Referenzzeile einen Eintrag.
- Kanban-Knöpfe der Zeitsteuerung sind `<a>`-Elemente (Textknoten/Titel), keine `<button>`.
- `ir.ui.view.arch_db` per `search ... like` ist unzuverlässig (jsonb); Ansichten über
  Quellcode bzw. `get_views` prüfen.
- Upgrade immer `--no-deps`, `.po` nur mit `--i18n-overwrite` bzw. Overwrite-Ladung.
- Git: Arbeitsbranch, PR über `scripts/github_pr.py` (kein gh-CLI), selbst mergen,
  VM auf main nachziehen, kein Force-Push/Rebase.
- VM-Shell über `$LOCALAPPDATA/Temp/vm_exec.py`; Skripte laufen vom lokalen Client
  mit `--instanz lokal|vm`.

## 6. Dokumente

- `docs/o11-o18-projekt-vergleich.md` — Iststand Odoo 11, Odoo-18-Ausgangszustand,
  Vergleich, Entscheidungspunkte, Umsetzung.
- `docs/o11-o18-projekt-abnahme.md` — Umsetzung, Prüfergebnisse, Abweichungen.
- Werkzeuge: `scripts/erhebe_projekt.py`, `scripts/projekt_views.py`,
  `scripts/projekt_bestand.py`, `scripts/verify_projekt.py`,
  `scripts/scan_projekt_englisch.py`, `scripts/gen_projekt_de_po.py`,
  `scripts/browser_projekt_abnahme.py`.

## 7. Nächster Schritt

Projekt ist abgeschlossen — keine weiteren Änderungen ohne neuen Auftrag.
Kandidaten für den nächsten Bereich: Preislisten/Regeln, Produkte (Produktstammdaten
vertiefen), Zeiterfassung (eigener Bereich), CRM/Partner-Gegenprüfung.
Vorgehen wie bisher: zuerst read-only Erhebung Odoo 11, dann Abweichungsliste, dann ändern.
