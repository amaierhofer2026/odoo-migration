# Abonnements / Subscriptions: Teil 7 - Endabnahme EUR-konsistent

Stand: 18.09.2026 (Session 118, Teil 7). Odoo 11 Prod ausschliesslich read-only. Keine Datenmigration.

## 1. Gefundene und behobene Luecke: Zugriffsrechte der Assistenten

Der Button "Abonnement-Zusatzverkäufe" oeffnete den Assistenten, der Browser-Test zeigte aber:
```
Zugriffsfehler: Sie haben keinen Zugriff auf Datensaetze "sale.subscription.wizard".
Keine Gruppe erlaubt derzeit diesen Vorgang.
```
Ursache: fuer drei Modelle fehlten in Odoo 18 vollstaendig die Zugriffsregeln (in Odoo 11 vorhanden):
`sale.subscription.wizard`, `sale.subscription.wizard.option`, `sale.subscription.close.reason.wizard`.

Behoben in itk_subscription **18.0.1.2.1** (`security/ir.model.access.csv`, 6 Regeln):
Lesen fuer interne Benutzer (`base.group_user`), voller Zugriff fuer
`itk_subscription.group_sale_subscription_manager`. Damit funktionieren Zusatzverkaeufe und der
Beendigungsgrund-Assistent. Keine Modell- oder Feldnamen geaendert.

## 2. USD-Testdaten bereinigt

```
4 USD-Testrechnungen (account.move, Entwurf)  -> geloescht
8 USD-Testauftraege (sale.order, bestaetigt)  -> von Odoo gesperrt
   Odoo 18 erlaubt bei bestaetigten Auftraegen weder Preislisten-/Waehrungsaenderung noch Loeschen
   (weder direkt noch nach Storno oder Entwurf). Diese 8 Testauftraege bleiben bestehen; sie sind
   reine Testdaten mit Produkt- und Preiszeilen aus frueheren Sessions.
Waehrungsstand Odoo 18 (Testumgebung): Abos 0 USD, Rechnungen 0 USD, Auftraege 8 USD (Testdaten).
Odoo 11 Prod: unveraendert, ausschliesslich gelesen.
```

## 3. EUR-Testdaten und EUR-Standardwerte

```
Angelegt (lokal und VM): je ein Testabo in Neu, Laufend, Zu erneuern, Abgeschlossen, Abgebrochen
   (Namen "TEST Abnahme open|pending|close|cancel", alle EUR) sowie ein bestaetigter EUR-Testauftrag
   mit Abo-Verknuepfung.
Nachweis neue Belege (VM, RPC): neues Angebot -> EUR + "Preisliste 2026 + Valorisierung (EUR)",
   neue Rechnung -> EUR, neues Abo -> EUR + EUR-Preisliste. Alle Partner stehen auf der EUR-Preisliste,
   die USD-Preisliste id 1 ist inaktiv.
```

## 4. Browser-Abschlusspruefung (Werkzeug `scripts/browser_abo_abschluss.py`, echte VM)

```
48 OK / 0 FEHL (nach der Korrektur der Zugriffsrechte)
je Zustand: Statusleiste, zustaendige Buttons, Smart Buttons, Felder, Euro-Zeichen vorhanden,
   kein Dollar-Zeichen, Smart Button Rechnungen vorhanden
Abo mit Verkaufsauftrag: Zaehler "1 Verkauf", Feld Verkaufsauftrag sichtbar
Abo ohne Verkaufsauftrag: Zaehler "0 Verkauf"
Button "Abonnement-Zusatzverkäufe": oeffnet den Assistenten "Optionen hinzufügen" als Dialog,
   ohne Speichern geschlossen
Screenshots 50_VM_Abo_*.png und 51_VM_Abo_Zusatzverkaeufe.png
```

## 5. Abschluss

**ABONNEMENTS = VOLLSTAENDIG FUNKTIONSFAEHIG, EUR-KONSISTENT UND MIGRATIONSBEREIT.**
