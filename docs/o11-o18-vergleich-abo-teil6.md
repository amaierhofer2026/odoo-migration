# Abonnements / Subscriptions: Teil 6 - Abschluss (Zusatzverkaeufe, EUR, Browser)

Stand: 18.09.2026 (Session 118, Teil 6). Odoo 11 Prod ausschliesslich read-only.
Keine Datenmigration.

## 1. Button "Abonnement-Zusatzverkäufe"

```
Odoo 11: Button "Abonnement-Zusatzverkäufe" -> Aktion 513
         Aktion 513 = ir.actions.act_window, "Optionen hinzufügen", Modell sale.subscription.wizard, view_mode form
Odoo 18: dieselbe Funktion = Aktion 1101 "Optionen hinzufügen" (xmlid itk_subscription.wizard_action),
         Modell sale.subscription.wizard, view_mode form
```
Ergebnis: **identischer Assistent, identische Datensaetze und Verknuepfungen** - in Odoo 18 war er nur
nicht direkt im Formular, sondern ausschliesslich ueber Aktion -> Optionen hinzufügen erreichbar.

Umgesetzt in `addons/itk_subscription/views/sale_subscription_views_zusatzverkaeufe.xml`
(Modulversion 18.0.1.2.0): zusaetzlicher Header-Button **"Abonnement-Zusatzverkäufe"** im Abo-Formular,
der genau diesen Assistenten oeffnet. Die Odoo-18-Aktion "Optionen hinzufügen" bleibt unveraendert erhalten.

## 2. Waehrung EUR / keine USD-Verwendung

```
Odoo 11: Firmenwaehrung EUR, alle Preislisten EUR
Odoo 18 vorher: Firmenwaehrung EUR, aber Standard-Preisliste id 1 = USD (inaktiv), 1 aktive EUR-Preisliste
                (id 34 "Preisliste 2026 + Valorisierung"), Auftraege/Abos/Partner zeigten auf die USD-Preisliste
```
Umgesetzt mit `scripts/fix_currency_eur.py` (idempotent, --pruefen liest nur):
```
res.partner        70 Datensaetze auf EUR-Preisliste umgestellt
sale.subscription   4 Datensaetze auf EUR-Preisliste umgestellt -> 0 USD-Abos
sale.order          7 Datensaetze (Angebote/Entwuerfe) umgestellt
sale.order          8 bestaetigte Testauftraege gesperrt (Odoo laesst bei bestaetigten Auftraegen
                    keine Preislisten-/Waehrungsaenderung zu) - siehe offene Punkte
```
Die USD-Preisliste id 1 ist inaktiv; die EUR-Preisliste ist die einzige aktive Preisliste und der
Standard fuer alle Partner (property_product_pricelist), damit neue Datensaetze automatisch EUR verwenden.

## 3. Erneut geprueft (Werkzeug `scripts/verify_s118_abo.py`)

Alle vorbereiteten Zuordnungen bleiben erhalten: Vorlagen 4 verwendet/1 bewusst nicht, 31 Beendigungs-
gruende, Felder beider Modelle, Status, Intervalle, `recurring_next_date`, Nummer/Code, Multiplikations-
faktor, Abo-Zeilen, Rechnungserzeugung (2 aktive Cronjobs), Verlaengerung, Kuendigung,
Abo ohne und mit Verkaufsauftrag. Lokal und VM: 19 OK / 0 FEHL.

## 4. Offene Punkte (nur Testdaten, keine Migration)

```
8 bestaetigte Odoo-18-Testauftraege und 4 Testrechnungen tragen noch USD (Testdaten aus frueheren
Sessions, S001xx). Odoo erlaubt bei bestaetigten Belegen keine Waehrungsaenderung; bereinigen nur durch
Loeschen/Neuanlage der Testdatensaetze - Entscheidung von Anna, nicht ohne Freigabe.
Fachlich relevant ist: neue Datensaetze entstehen jetzt in EUR, die Odoo-11-Daten sind ohnehin durchgehend EUR.
```

## 5. Falle fuer den Betrieb (Windows/Docker)

Neu angelegte Dateien im Addons-Ordner (`C:\Odoo-Test\addons`) sind fuer den laufenden Odoo-Container
erst nach `docker restart odoo18` sichtbar (Bind-Mount-Cache unter Windows). Ein Modul-Upgrade ohne
Neustart laeuft fehlerfrei durch, laedt die neue Datei aber nicht.
