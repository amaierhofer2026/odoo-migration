# Abonnements: Teil 13 - Reiter "Wiederkehrende Buchungen"

Stand: 22.09.2026. Odoo 11 Prod ausschliesslich read-only. Keine Produktivdaten migriert.

## Auftrag

In Odoo 11 heisst der erste Reiter im Abo-Formular "Wiederkehrende Buchungen", in Odoo 18 hiess er
"Abonnement-Einträge". Die sichtbare Beschriftung sollte angeglichen werden - auf beiden Wegen
(normales Abonnement und Zu erneuernde Abonnements).

## Befund

Die Beschriftung kam aus der englischen Quelle "Subscription Lines" im View
`itk_subscription.sale_subscription_view_form` (Zeile 344) und wurde ueber die Uebersetzung
`i18n/de.po` (msgid "Subscription Lines" -> msgstr "Abonnement-Einträge") deutsch angezeigt.
Dieselbe Quelle wird auch fuer die Suche und die Aktion der Abonnement-Positionen verwendet.

## Umsetzung (Modulversion 18.0.1.2.6)

```
views/sale_subscription_views.xml   <page string="Wiederkehrende Buchungen" id="lines">
i18n/de.po                          msgid/msgstr "Wiederkehrende Buchungen" ergaenzt
```
Die Beschriftung steht damit direkt im Modul (deutscher Quelltext) und nicht mehr nur in der
Uebersetzung.

## Upgradefestigkeit

Das View ist Moduldaten mit noupdate=0; ein Modul-Upgrade schreibt die Ansicht aus dem Modul neu.
Da die Beschriftung jetzt im Modul selbst steht, bleibt sie nach jedem Upgrade erhalten - es braucht
dafuer kein Nachbearbeitungsskript (im Gegensatz zu den Feldbeschriftungen aus F34, die auf
Uebersetzungen beruhen). Die Uebersetzungsdatei sichert die Anzeige zusaetzlich bei lang=de_DE ab.

## Pruefung

```
lokal, Ansicht ueber RPC gelesen:
   lang=de_DE -> Seiten: ['Wiederkehrende Buchungen', 'Einstellungen']
   lang=en_US -> Seiten: ['Wiederkehrende Buchungen', 'Settings']
Browser auf der VM (scripts/browser_abo_reiter.py): beide Wege, siehe Bericht.
Alle Funktionstests unveraendert gruen (verify_s118_abo 19 OK/0 FEHL, Cron 13 OK/0 FEHL,
manueller Weg 16 OK/0 FEHL).
```
Nur die Beschriftung wurde geaendert; Feldnamen, Relationen und Funktionalitaet blieben unberuehrt,
alle zusaetzlichen Odoo-18-Funktionen sind erhalten.
