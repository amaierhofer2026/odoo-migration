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

**Entscheidung offen:** Kopfwerte aus Odoo 11 uebernehmen (waere in Odoo 18 nur manuell
moeglich und wuerde die automatische Berechnung aushebeln) oder die korrekte Zeilensumme
gelten lassen.

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
nur den Firmennamen des Elternkontakts zeigt. Diese Falle werden vor dem Abrechnungslauf
gesondert vorgelegt; es wird kein Platzhalterkontakt erfunden.

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
