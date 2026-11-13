# Verkauf und Abonnements: Migration und Prüfung

Stand 12.11.2026, Session 142. Freigabe Anna Maierhofer (Option A).
Quelle: Odoo 11 `ITK_V1_a`, ausschliesslich lesend. Ziel: Odoo 18 (`odoo18_test`).
Datenschutz: nur IDs, Nummern, Betraege und Zaehlwerte, keine Personenbezuege.

## 1 Ergebnis lokal

| Objekt | Odoo 11 | Odoo 18 | Differenz |
|---|---|---|---|
| Auftraege (`sale.order`) | 2.519 | **2.519** | 0 |
| Auftragszeilen | 4.079 | 4.099 (davon 20 Zeilen aus 12 verbliebenen Testauftraegen) | +20 |
| Abonnements (`sale.subscription`) | 1.786 | **1.786** | 0 |
| Abozeilen | 2.457 | 2.456 | -1 |

Die eine fehlende Abozeile verweist auf ein Produkt, das in Odoo 18 nicht existiert.

**Idempotenz (zweiter Lauf, beide Bereiche):**

| Bereich | Ergebnis |
|---|---|
| Verkauf | 2.519 erkannt, **0 Neuanlagen**, 0 Fehler |
| Abonnements | 1.786 erkannt, **0 Neuanlagen**, 0 Fehler |

Auftragsnummern aus Odoo 11 (z. B. `A-1900491`) bleiben erhalten. Statusabbildung:
`done` wird zu `sale`, weil Odoo 18 diesen Zustand nicht kennt; der Fakturierungsstand
steht an den Rechnungen.

## 2 Abweichung bei den Auftragssummen (offener Pruefpunkt)

Summe der Zwischensummen: Odoo 11 **3.735.562,56** gegen Odoo 18 **3.738.285,06**
(Differenz **+2.722,50**, 0,07 %).

Betroffen sind **94 von 2.519 Auftraegen**. Muster am Beispiel `A-1900491`:

| | Odoo 11 | Odoo 18 |
|---|---|---|
| Zeile 1 | 1 × 65,00 = 65,00 | 1 × 65,00 = 65,00 |
| Zeile 2 | 12 × 10,00 = 120,00 | 12 × 10,00 = 120,00 |
| Zeilensumme | 185,00 | 185,00 |
| Kopfsumme (`amount_untaxed`) | **129,50** | **185,00** |

Die Zeilen sind in beiden Systemen identisch. Odoo 11 fuehrt im Auftragskopf einen Wert,
der zur Zeilensumme nicht passt (Altbestand-Inkonsistenz, kein Rabattfeld auf Auftrags-
oder Zeilenebene vorhanden, `discount` = 0). Odoo 18 berechnet die Kopfsumme immer aus den
Zeilen. Die migrierten Zeilen sind also unveraendert; die Differenz entsteht ausschliesslich
aus den in Odoo 11 veralteten Kopfwerten.

**Entscheidung (Anna, 12.11.2026):** In Odoo 18 gilt die aus den migrierten Zeilen
berechnete Summe. Die Odoo-11-Kopfwerte werden NICHT uebernommen und die Odoo-18-
Berechnungslogik wird nicht ausser Kraft gesetzt. Die 94 Faelle sind als dokumentierte
Datenabweichung protokolliert (CSV-Export ausserhalb des Repositories, 94 Zeilen).

**Nachweis der Zeilenuebernahme** (`scripts/migration/verkauf_abgleich.py`, read-only):

| Pruefung | Ergebnis |
|---|---|
| Auftraege | 2.519 = 2.519 |
| Auftragszeilen | 4.079 = 4.079 |
| Zeilen mit Abweichung Menge/Preis/Rabatt | **0** |
| Auftraege mit abweichender Zeilenzahl | **0** |
| Auftraege ohne Zeilen (auch in Odoo 11 ohne Positionen) | 12 |
| Zeilen mit abweichendem Steuersatz | 9 (werden nachgezogen) |

Mengen, Einzelpreise und Rabatte sind also zeilengenau identisch; die Differenz entsteht
ausschliesslich aus den veralteten Kopfwerten.

## 3 Steuerzuordnung (geklaert)

Die frueher dokumentierte Vorsteuer-ID 43 ist richtig; die im ersten Lauf verwendete ID 57
war falsch. Beleg ueber Steuersatz, Typ, Steuergruppe und Repartition-Konto:

| Odoo-11-Steuer | Odoo-18-Ziel | Konto | Begruendung |
|---|---|---|---|
| 20% Umsatzsteuer | **15** „20% Ust" | 3500 VAT 20% | Verkaufssteuer, Standardkonto |
| 20% Vorsteuer | **43** „20% Vst" | 2500 Input tax 20% | Einkaufssteuer, Standardkonto |

ID 57 heisst „20% Vst EU" und bucht auf 2505 „Other tax 13%" - ein EU-Sonderfall.
Die Zuordnung erfolgt im Skript jetzt ueber Satz + Verwendungsart + Steuergruppe +
Repartition-Konto; Sonderfaelle (EU, Reverse Charge, Intra-Community) sind ausgeschlossen.
Kontrolliert: alle 662 migrierten Produkte tragen die Verkaufssteuer 15.

## 4 Mengeneinheiten (geklaert)

Odoo 11 fuehrt 33 Einheiten, darunter „13 Gemeinden", „15 Gemeinden" usw. mit
**Faktor 1,0, Rundung 0,01, Typ reference**. Es ist keine Umrechnung, sondern eine
Bezeichnung der Abrechnungspauschale; `to_multiply_by_factor` waere deshalb falsch
(nichts zu multiplizieren).

Umsetzung: Die Einheiten werden 1:1 in Odoo 18 angelegt (Faktor, Rundung, Kategorie) und
in der Kategorie „Unit" gefuehrt, weil Odoo 18 fuer Zeile und Produkt dieselbe
Einheitenkategorie verlangt. Der fachliche Rechenwert bleibt identisch.

## 5 Preislistenregel ohne Produkt (geklaert)

Die eine Regel (Nr. 8 in Liste 1) verweist auf Produktvorlage 300, ein **archiviertes**
Testprodukt. Sie ist fachlich nicht verwaist, sondern gueltig - meine Produktemigration
hatte archivierte Vorlagen uebersehen. Korrigiert: Die Produkte-Migration liest jetzt mit
`active_test=False` und uebernimmt auch die 4 archivierten Vorlagen. Damit sind
**1.876 von 1.876** Regeln zugeordnet.

## 6 Kontakte ohne Namen (dokumentiert, nicht migriert)

32 Kontakte haben in Odoo 11 keinen Namen. Sie werden **nicht** migriert und Odoo 11 wird
nicht veraendert. Pruefung der Referenzen:

| Objekt | Anzahl |
|---|---|
| Auftraege | 0 |
| Abonnements | 0 |
| **Rechnungen (gebucht)** | **7** |

Die 7 gebuchten Rechnungen (2021-2022, u. a. `R-22633`, `R-21774`, `R-21684`, drei
Bankbelege `BNK1/...`) haengen an 4 dieser Kontakte. Es handelt sich um
**Rechnungsadressen** von Firmen, deren `name` in Odoo 11 leer ist und deren Anzeigename
nur den Firmennamen des Elternkontakts zeigt.

Pruefung der Zuordnung (12.11.2026):

| Rechnungsadresse (o11) | Typ | Elternkontakt (o11) | Elternkontakt in Odoo 18 | Rechnungen | Bewertung |
|---|---|---|---|---|---|
| 9798 | Firma | 7863 | ja | BNK1/2022/0373, R-22633 | **eindeutig** |
| 10323 | Firma | 5963 | ja | BNK1/2022/0753, BNK1/2021/0707, R-21684 | **eindeutig** |
| 10737 | Person (Rechnungsadresse) | 6433 | ja | R-21774 | **eindeutig** |
| 10326 | Person | **kein Elternkontakt** | - | BNK1/2022/0417 | **nicht eindeutig** |

6 der 7 Rechnungen koennen damit ueber den bestehenden Firmen-/Elternkontakt zugeordnet
werden; die Odoo-11-Referenz der Rechnungsadresse wird dabei dokumentiert. Die Rechnung
`BNK1/2022/0417` wird vor dem Rechnungs-Schreiblauf separat aufgelistet - kein Platzhalter,
keine Erfindung. Odoo 11 bleibt unveraendert.

## 7 Skripte (reproduzierbar, im Repository)

| Bereich | Skript | Umfang |
|---|---|---|
| Kontakte | `scripts/migration/kontakte_migration.py` | 123 Tags, 169 Anreden, 6.020 Kontakte |
| Produkte | `scripts/migration/produkte_migration.py` | 33 Einheiten, 31 Kategorien, 662 Vorlagen, 657 Varianten |
| Preislisten | `scripts/migration/preislisten_migration.py` | 50 Listen, 1.876 Regeln |
| Verkauf | `scripts/migration/verkauf_migration.py` | 2.519 Auftraege, 4.079 Zeilen |
| Abonnements | `scripts/migration/abonnement_migration.py` | 1.786 Abos, 2.457 Zeilen |
| Abgleich | `scripts/migration/verkauf_abo_stammdaten_abgleich.py` | read-only Zuordnungsbericht |

Alle Skripte: Trockenlauf ist Standard, Schreiben nur mit `--ausfuehren --ich-habe-freigabe`,
Erkennung ueber `itk_o11_id`, Mapping-Export, Zusammenfassung je Objektart.

## 8 Testdaten

12 Odoo-18-Testauftraege ohne Odoo-11-Bezug konnten nicht entfernt werden, weil Odoo 18
das Loeschen bestaetigter Auftraege verweigert (Storno noetig, an Rechnungen gebunden).
Die 25 Testprodukte bleiben zunaechst erhalten, weil an ihnen 28 Auftrags- und 6 Abo-Zeilen
haengen; sie werden gemeinsam mit den Testbelegen bereinigt.


## 9 Browserabnahme (12.11.2026)

Je Bereich wurde ein echter Datensatz im Browser geoeffnet (Chrome, Odoo-18-Webclient),
lokal und VM:

| Bereich | Lokal | VM | Beleg |
|---|---|---|---|
| Verkauf | A-1900491 | A-1900491 | 2 Zeilen (65,00 + 120,00), Nettobetrag 185,00, Steuern 37,00 (20 %), Status "Verkaufsauftrag", Auftragsdatum 26.05.2019 |
| Abonnements | Liste | NV-00954 | Vorlage "Jahresabrechnung-Abonnement", Mindestvertragsdauer 24 Monate, Vertragsende 07.08.2015, Kuendigungsfrist 3 Monate |
| Kontakte | Kontakt 256 | Kontakt 2264 | Firmenkontakt mit KENNDATEN (GKZ, Multiplication Factor/Thsd, zu Handen, Organisationsbezeichnung) |
| Produkte | Vorlage 305 | Vorlage 812 | Verkaufspreis 65,00 bzw. 1,00, "To multiply by Factor(per 1000)", Abonnement-Produkt |
| Preislisten | 50 Listen | 50 Listen | Namen aus Odoo 11 erhalten, z. B. "Preisliste 2026 + Valorisierung", "GemDat Niederoesterreich alt/nicht mehr verwenden" |

## 10 Idempotenz (zweiter Lauf, VM)

| Bereich | Ergebnis |
|---|---|
| Kontakte | 0 Neuanlagen, 6.020 erkannt, 0 Fehler |
| Produkte | 0 Neuanlagen, 31 Kategorien / 662 Vorlagen / 657 Varianten, 0 Fehler |
| Preislisten | 0 Neuanlagen, 50 Listen / 1.876 Regeln, 0 Fehler |
| Verkauf | 0 Neuanlagen, 2.519 erkannt, 0 Zeilensteuer-Korrekturen, 0 Fehler |
| Abonnements | 0 Neuanlagen, 1.786 erkannt, 0 Fehler |

Der Abgleich auf der VM ist identisch zum lokalen Stand: 2.519 Auftraege / 4.079 Zeilen,
0 Abweichungen bei Menge/Preis/Rabatt/Steuer, 94 Kopfsummen-Faelle, 1.786 Abos.

## 11 Vorfall 12.11.2026: fehlende Modulabhaengigkeit

Das Modul `itk_migration_keys` erbt `sale.subscription`, deklarierte aber nur
`base`, `product`, `sale`. Nach einem Neustart brach der Registry-Aufbau ab
(`Model 'sale.subscription' does not exist in registry`, HTTP 500) - lokal und VM.

Behoben: `depends` um `itk_subscription` ergaenzt (Branch `itk/s142k-fix-depends`,
Commit 198cc0c); in der Datenbank vorhandener Phantom-Eintrag `sale_subscription`
(0 Datensaetze) auf `uninstalled` gesetzt. Zusaetzlich waren die Asset-Bundles
inkonsistent und wurden neu erzeugt (ir.attachment `/web/assets/%` geloescht, Neustart).

Beide Instanzen sind wieder erreichbar (HTTP 200), alle Daten unversehrt.
**Offen: der Branch ist noch nicht auf `main` gemergt** - ohne Merge ist der Dreistand
nicht herstellbar.
