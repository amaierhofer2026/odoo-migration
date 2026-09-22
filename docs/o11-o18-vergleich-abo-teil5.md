# Abonnements / Subscriptions: Teil 5 - Stammdaten angelegt, Bereich migrationsbereit

Stand: 18.09.2026 (Session 118, Teil 5)
Odoo 11 Prod ausschliesslich read-only. Keine Datenmigration (keine Abos, Auftraege oder Rechnungen uebernommen).

## 1. Auftrag

Die in Odoo 18 noch fehlenden, in Odoo 11 aber tatsaechlich referenzierten Abo-Stammdaten sollten angelegt
werden, damit jedes verwendete Element ein eindeutiges Ziel hat.

## 2. Vorlagen

```
Pruefung in Odoo 11 (read-only), Verwendung gezaehlt:
   Jahresabrechnung-Abonnement                        1.736 Abos   -> in Odoo 18 vorhanden
   Monatsabrechnung-Abonnement                            3 Abos    -> in Odoo 18 vorhanden
   Quartalsabrechnung-Abonnement                         24 Abos    -> in Odoo 18 vorhanden
   5-Jahresabo                                            0 Abos    -> nicht angelegt (keine Referenz)
   J- Jahresabrechnungsabo-Mindestvertragsdauer 12 Mon.    1 Abo     -> in Odoo 18 ANGELEGT

Angelegte Vorlage (fachlich gleich wie Odoo 11):
   name                            J- Jahresabrechnungsabo-Mindestvertragsdauer 12 Monate
   recurring_rule_type / interval  monthly / 1
   minimum_contract_life / unit    12 / monthly
   contract_termination_period     0 / yearly
   payment_mandatory / user_closable  aus (wie Odoo 11)
```

## 3. Beendigungsgruende

```
Odoo 11: 33 Gruende mit zusammen 291 Verwendungen (an Abos mit Beendigungsgrund)
Odoo 18: 5 vorhanden (121 Verwendungen, namentlich identisch in der deutschen Anzeige)
         -> 26 fehlende Gruende mit 170 Verwendungen ANGELEGT
         -> 2 Gruende ohne jede Verwendung nicht angelegt: "wird noch Intrakommuna abgelöst", "Maria Saal"
Ergebnis Odoo 18: 31 Gruende; fuer alle 291 Verwendungen in Odoo 11 ist ein eindeutiges Ziel vorhanden
                  (Zuordnung ueber den Namen)
```
Die 26 Gruende wurden 1:1 mit dem Odoo-11-Wortlaut angelegt (deutscher Text als Quelle), Lagecheck und
Sonderfaelle inklusive (z. B. "über GV Horn Regionenmandant verrechnet!", "direkter Kunde der Gemdat NÖ").

## 4. Werkzeug

`scripts/apply_abo_stammdaten.py` legt die Stammdaten idempotent an (lokal und VM).
Bereits ausgefuehrt: **lokal 1 Vorlage + 26 Gruende, VM 1 Vorlage + 26 Gruende.**

## 5. Erneute Pruefung (Werkzeug `scripts/verify_s118_abo.py`)

```
                                        lokal            VM
Vorlagen (4 verwendet, 1 bewusst nicht)  OK               OK
Beendigungsgruende (31)                  OK               OK
Felder sale.subscription (25)            OK               OK
Felder sale.subscription.line (11)       OK               OK
Statuswerte (draft/open/pending/close/cancel)  OK         OK
Intervalle (daily/weekly/monthly/yearly) OK               OK
Rechnungserzeugung (2 aktive Cronjobs)   OK               OK
Verlaengerung (Erneuerungsangebot, Zu erneuern) OK        OK
Kuendigung/Abschluss, Smart Buttons      OK               OK
Abo ohne Verkaufsauftrag                 OK (172, 185)    OK
Keine Datenmigration (5 Abos)            OK               OK
ERGEBNIS                                 19 OK / 0 FEHL   19 OK / 0 FEHL
```

## 6. Abschluss

**ABONNEMENTS = VOLLSTAENDIG FUNKTIONSFAEHIG UND MIGRATIONSBEREIT.**

Jedes in Odoo 11 verwendete Feld, jede verwendete Vorlage und jeder verwendete Beendigungsgrund hat ein
eindeutiges Ziel in Odoo 18:
```
Felder               alle 1:1 (Teil 2), berechnet bleiben berechnet
Vorlagen             4 von 5 (die fuenfte wird in Odoo 11 von 0 Abos referenziert)
Beendigungsgruende   31 von 33 (die zwei fehlenden haben 0 Verwendungen)
Status/Intervalle    wortgleich
Rechnungen           Mechanik und Zaehler identisch, Cron aktiv
Verlaengerung/Kuendigung  Buttons und Regeln identisch
Abo ohne Auftrag     funktional vollstaendig unterstuetzt
```
Es wurde **keine** Datenmigration durchgefuehrt; die Stammdaten sind vorbereitet, die Uebernahme der
1.764 Abos, 2.434 Zeilen, 291 Beendigungsgruende-Zuordnungen und 1.722 Auftragsverknuepfungen erfolgt
erst im Migrationstermin.

## 7. Noch vor der eigentlichen Datenmigration zu entscheiden

1. **Auswahlregel der Abos** (Status, Alter, Auftragsbezug) - die 42 ohne Verkaufsauftrag duerfen laut
   Entscheidung mit; Konkretisierung offen.
2. **Reihenfolge:** Verkaufsauftraege vor Abos (1.722 Abos verweisen auf einen Auftrag).
3. **Multiplikationsfaktor** `qty_multiplication_factor` 1:1 uebernehmen (ITK-Preislogik pro 1.000) - Freigabe
   durch die Fachseite, weil es die Abrechnung betrifft.
4. **Rechnungsstellung nach der Migration:** `recurring_next_date` uebernehmen (naechste Rechnung entsteht
   automatisch) oder erst nach manueller Pruefung? Empfehlung: uebernehmen und die erste Rechnung gemeinsam
   kontrollieren.
5. **Nummern/Namen:** NV-Nummern aus Odoo 11 unveraendert in `name`/`code` uebernehmen (Empfehlung: ja).
6. **Zwei Gruende ohne Verwendung** ("wird noch Intrakommuna abgelöst", "Maria Saal"): nicht angelegt -
   nachtragen, falls fachlich doch benoetigt.
7. **Vorlage "5-Jahresabo"**: nicht angelegt (0 Referenzen) - nachtragen, falls kuenftig benoetigt.
