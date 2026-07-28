# Hermes Memory Backup — 27. Juli 2026

Sicherung VOR der Bereinigung. Passwörter und Zugangsdaten wurden entfernt.

---

## Memory (Agent-Notizen) — 93% voll (2.064 / 2.200 Zeichen)

### Eintrag 1: Odoo18 Systemumgebung
Odoo18: 192.168.56.1:8069 (localhost:8069 funktioniert NICHT — Docker auf Windows-Host via VirtualBox, nur 192.168.56.1 erreichbar). DB=odoo18_test, User-UID=2.
(Zugangsdaten aus Sicherheitsgründen entfernt — siehe .hermes_secrets oder Docker-Config)

### Eintrag 2: Admin-Gruppen & Odoo-18-Quirks
Admin (uid=2) braucht explizite Gruppenzuweisung (itk_crm, itk_subscription) sonst AccessError. Odoo-18: `team_id` auf res.partner NICHT in read() — silent-Failure. `sale.subscription.line`-Inversfeld = `analytic_account_id`. itk_crm-Modelle: `itk_crm.statusofcommunity`, `itk_crm.communitymagnitude`. Fakturiert=Summe amount_untaxed. Payment via account.payment.register.

### Eintrag 3: Anna's Test-Präferenzen
Anna testet via UI+JSON-RPC, will Klick-Pfade. JEDES Modul testen. Vor Docker-Neustart Fix per JSON-RPC verifizieren. Nicht iterativ debuggen.

### Eintrag 4: Odoo-11 JSON-RPC
Odoo-11 JSON-RPC: Cookie-Auth via /web/session/authenticate, KEIN "id" in execute_kw-Params.

### Eintrag 5: Native-First-Check & Anna-Präferenzen
Vor Migration Odoo-18-native/OCA pruefen. server_action_mass_edit (OCA/server-ux 18.0). Anna: direkt, keine Schleifen, keine vielen Docker-Restarts, UI+console testen.

### Eintrag 6: Helpdesk
Helpdesk: itk_helpdesk_compat. OCA-IDs: ticket=3721, search=3720, portal=3704, menu=744. view_ids nötig. Odoo18 stripped header+button_box → btn-primary im sheet. reply=mail.compose. JS-Fehler=itk_subscription tour.js(web.core)+portal.js aus Assets. Anna: UI+console testen, Doku VOR Fertig.

### Eintrag 7: Smart-Button-Overflow
Odoo-18: `smart button Subscriptions` kann im Overflow-Dropdown (Mehr) landen, wenn zu viele Stat-Buttons. Klick auf Mehr zeigt alle. Button bleibt funktional, nur UI-Platzierung.

### Eintrag 8: Kontaktmigration-Prüfung 27.7.
status_of_community gefixed (7 Einträge, Code-Mapping ST/M/G/-/MAG/SR/GV). community_magnitude Codes 15+16 ergänzt (nun 16). Gemeinde-Information Tab in id=3997 angelegt. UID-Label-Fix als View id=4005 (erbt von 1168, prio=999) — braucht view-cache clear. Bundesländer O11→O18: Name-basiertes Mapping (Codes unterschiedlich: 'Bgld.'→'1'). comment-Feld: text→html. Stichproben zeigen population=0 bei div. Gemeinden. Migration NOCH NICHT BEREIT.

### Eintrag 9: Odoo-11 fields_get
Odoo-11 JSON-RPC: fields_get fuer Selection-Werte (ir.model.fields liefert in O11 keine selection). O18-URL pruefen: 192.168.56.1 nicht localhost.

---

## User Profile (über Anna) — 65% voll (899 / 1.375 Zeichen)

### Eintrag 1
Anna Maierhofer, Odoo-Entwicklerin ITK. Odoo 11→18 Migration. Docker-Stack C:\Odoo-Test\ (VirtualBox→/media/sf_Odoo-Test/). GitHub amaierhofer2026. Erwartet: 1:1-Strukturen, alle Features intakt, saubere Git-Chronik, JEDE Änderung sofort auf GitHub pushen. Sprache: Deutsch.

### Eintrag 2
Anna ist frustriert, wenn Module als "inkompatibel" geparkt werden ohne vorher zu prüfen, ob Odoo 18 die Funktionalität nativ hat (z.B. mass_editing). NATIVE-FIRST-CHECK ist Pflicht vor jeder Migration. Bei geparkten Modulen (web_group_expand, mass_editing) nachträglich prüfen und ggf. natives Modul aktivieren.

### Eintrag 3
Anna bevorzugt klare Kategorien: Module sind entweder migriert, geparkt (mit realer Chance auf spätere Migration), oder endgültig entfällt. "Geparkt" als Dauerzustand ohne Perspektive mag sie nicht — dann lieber finale Entscheidung. Sie testet gerne selbst per UI, will aber vorher wissen WAS sie wo findet.

---

Ende des Backups. Keine Passwörter oder Zugangsdaten enthalten.
