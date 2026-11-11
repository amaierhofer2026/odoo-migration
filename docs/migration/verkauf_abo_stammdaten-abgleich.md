# Stammdaten-Abgleich Verkauf und Abonnements (read-only)

Stand: 12.11.2026, Session 142. Werkzeug:
`scripts/migration/verkauf_abo_stammdaten_abgleich.py` (read-only, schreibt nichts).
Odoo 11 `ITK_V1_a` wurde ausschliesslich lesend befragt.

**Datenschutz:** Dieses Dokument enthaelt nur Zaehlwerte, Odoo-IDs und technische
Schluessel. Keine Namen von Personen oder Firmen, keine E-Mail-Adressen, keine
Steuernummern. Der CSV-Report des Werkzeugs liegt ausserhalb des Repositories.

## 1 Umfang der Erhebung

| Objekt | Anzahl Odoo 11 |
|---|---|
| Auftraege (`sale.order`) | 2.514 |
| Auftragszeilen (`sale.order.line`) | 4.076 |
| Abonnements (`sale.subscription`) | 1.788 |
| Abo-Zeilen (`sale.subscription.line`) | 2.459 |
| **benoetigte Partner** (distinct) | **1.265** |
| **benoetigte Produkte** (distinct) | **440** |
| **benoetigte Preislisten** (distinct) | **28** |
| **benoetigte Abo-Vorlagen** (distinct) | **4** |

## 2 Zuordnungsergebnis (lokal; VM praktisch identisch)

Zuordnungsreihenfolge, bewusst ohne Raten: `ref` -> `vat` -> `email`, jeweils nur bei
**genau einem** Treffer. Namensmatching wurde zusätzlich gemessen, aber nicht verwendet.

| Objekt | benoetigt | eindeutig zuordenbar | mehrdeutig | fehlend |
|---|---|---|---|---|
| Partner | 1.265 | **6** | 0 | **1.252** (davon 7 ohne jeden Schluessel) |
| Produkte | 440 | **0** | 0 | **440** |
| Preislisten | 28 | **1** | 0 | **27** |
| Abo-Vorlagen | 4 | **4** | 0 | 0 |

Namens-Fallback als Kontrollmessung:
- Produkte der Auftragszeilen: 411 distinct, ueber Namen eindeutig 6, kein Treffer 405.
- Partner der Auftraege: 1.125 distinct, ueber Namen eindeutig 6, mehrdeutig 1, kein Treffer 1.118.

## 3 Bestand in Odoo 18 (Ursache)

| Objekt | Odoo 11 | Odoo 18 lokal | Odoo 18 VM |
|---|---|---|---|
| Partner | 5.851 | 96 | 89 |
| Produkte | 657 (nur **2** mit `default_code`) | 15 (0 mit Code) | 12 |
| Preislisten | 50 | **1** | 1 |
| Abo-Vorlagen | 5 | 4 | 5 |

Die Stammdaten fuer Verkauf und Abonnements existieren in Odoo 18 nicht. Es fehlt nicht
die Zuordnung, es fehlen die Datensaetze selbst.

## 4 Antworten auf die acht Fragen

1. **Welche Kunden werden benoetigt?** 1.265 distinct Partner aus Auftraegen und Abos
   (IDs im CSV-Report ausserhalb des Repos).
2. **Welche existieren bereits korrekt?** 6 - eindeutig ueber `ref`, `vat` oder `email`.
3. **Welche fehlen?** 1.252; davon 7 ohne jede technische Kennung.
4. **Welche Produkte werden benoetigt und welche fehlen?** 440 benoetigt, **0 vorhanden**.
   Zusatzproblem: Odoo 11 fuehrt nur 2 von 657 Produkten mit `default_code`, eine
   eindeutige technische Zuordnung ist damit grundsaetzlich nicht moeglich.
5. **Welche Preislisten und Vorlagen?** 28 Preislisten (1 vorhanden, 27 fehlen),
   4 Abo-Vorlagen (alle 4 vorhanden).
6. **Mehrdeutige Zuordnungen?** Keine bei `ref`/`vat`/`email`; genau 1 bei Namensmatching
   (deshalb nicht verwendet).
7. **Ohne Aenderung eindeutig migrierbar:** 6 Partner, 4 Abo-Vorlagen, 1 Preisliste,
   0 Produkte. Das sind zusammen 0,5 % der benoetigten Stammdaten - zu wenig, um einen
   Auftrag oder ein Abo vollstaendig zu bilden.
8. **Benoetigt eine Entscheidung:** ja, siehe Abschnitt 5.

## 5 Entscheidungspunkt (Vorlage fuer Anna)

Eine vollstaendige Migration von Verkauf und Abonnements setzt voraus:

| Vorarbeit | Umfang | Betroffen |
|---|---|---|
| Kunden/Partner anlegen | ~1.252 Datensaetze, personenbezogen | Bereich Kontakte/Kundenverwaltung |
| Produkte anlegen | ~440 Datensaetze, ohne belastbaren Code | Bereich Produkte |
| Preislisten anlegen | 27 Datensaetze | Bereich Produkte/Preise |
| danach Belege | 2.514 Auftraege + 4.076 Zeilen, 1.788 Abos + 2.459 Zeilen | Verkauf, Abonnements |

Das ist keine "Aufloesung von Abhaengigkeiten" mehr, sondern die Migration der Bereiche
Kontakte, Produkte und Preislisten. Genau das hat Ihr Auftrag ausgeschlossen
("NICHT das gesamte Modul Kontakte/Kundenverwaltung bearbeiten oder pauschal alle
Kontakte migrieren"). Deshalb wurde **nichts geschrieben**.

Drei Optionen:

- **A (empfohlen):** Kontakte, Produkte und Preislisten als eigenes Teilprojekt freigeben
  (mit eigenem Strukturvergleich, Skript, Trockenlauf, Datenschutz-Freigabe fuer
  personenbezogene Daten). Danach Verkauf und Abos in einem Zug migrieren.
- **B:** Nur die technisch eindeutigen Stammdaten migrieren (6 Partner, 1 Preisliste,
  4 Vorlagen) und den Rest dokumentieren. Ergebnis: kein einziger vollstaendiger Auftrag.
- **C:** Verkauf und Abonnements bleiben OFFEN (Struktur abgenommen, Daten nicht migriert)
  und werden in der Bereichsuebersicht so gefuehrt.

Ohne Ihre Entscheidung wird weder migriert noch etwas angelegt.

## 6 Laufprotokoll (Mengenwerte)

| Datum/Zeit | Commit | Quelle | Ziel | Modus | Ergebnis |
|---|---|---|---|---|---|
| 12.11.2026 16:59 | 61140ec | Odoo 11 `ITK_V1_a` (lesend) | lokal `odoo18_test` | read-only | 1.265 Partner / 440 Produkte / 28 Preislisten / 4 Vorlagen benoetigt; 6 / 0 / 1 / 4 zuordenbar |
| 12.11.2026 17:02 | 61140ec | Odoo 11 `ITK_V1_a` (lesend) | VM `odoo18_test` | read-only | gleiche Bedarfszahlen, Vorlagen 4 von 5 in Odoo 18 vorhanden |

## 7 Werkzeug

```
python scripts/migration/verkauf_abo_stammdaten_abgleich.py --instanz lokal
```

Read-only: die Schreibschutz-Klasse des Werkzeugs bricht jeden `create`/`write`/`unlink`
ab. `--csv` schreibt den Zuordnungsreport (nur IDs, Schluessel, Status) an einen Pfad
ausserhalb des Repositories.
