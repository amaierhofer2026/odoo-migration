# Helpdesk: Konfiguration für den Produktivstart (Vorschlag, nichts angelegt)

Stand: 08.10.2026, Session 132. Alle Werte sind aus der read-only-Erhebung von
Odoo 11 belegt. Es wurde **nichts** davon angelegt - die Liste ist zur Freigabe
gedacht; nach Freigabe lege ich sie in der Zielinstanz an.

## 1. Gruppen und Rechte

| Odoo 11 | Benutzer | Odoo 18 | Hinweis |
|---|---|---|---|
| Support Staff | 21 | Helpdesk / User (14 Benutzer) | Sachbearbeitung, kein Konfigurationsrecht |
| Support Manager | 6 | Helpdesk Manager (14 Benutzer) | Konfiguration, Löschrecht |
| Support Client | 21 | Portal (base.group_portal) | Kunden sehen nur eigene Tickets |

Zu prüfen: Mitgliederliste der beiden Odoo-18-Gruppen gegen die Odoo-11-Listen
abgleichen (Odoo 11: Support Staff = alle 21 aktiven internen Benutzer).

## 2. Teams (Odoo-18-Zusatz, Odoo 11 hatte keine)

- Ein Team genügt zum Start, z. B. "ITK Support"; Teamleiter festlegen.
- Arbeitszeiten (Arbeitszeiten des Teams) sind für die SLA-Frist massgeblich.
- "Use SLA" muss aktiv sein.
- "Im Portal anzeigen", wenn Kunden das Team beim Anlegen wählen sollen.

## 3. SLA (Odoo 11: "Standard SLA Support ITK Produkte")

| Punkt | Odoo-11-Wert |
|---|---|
| Antwortzeit | 48 Stunden je Kategorie |
| Zählung | 24 Stunden (auch ausserhalb der Arbeitszeit) |
| Kategorien | amtsweg.gv.at (Formulare & Postfächer), Amtssignatur (Sendhybrid Client), E-Learning (Städtebund Academy), Verwaltungsmanager (MAYAN EDMS) |
| Alarme | 3 E-Mail-Alarme (Zeitpunkte aus Odoo 11 übernehmen) |

Odoo-18-Umsetzung: SLA-Datensatz mit diesen Kategorien, Zielstufe
"Geschlossen/Behoben", Ignorier-Stufe "on Hold" - das entspricht dem
Odoo-11-Knopfpaar "SLA pausieren"/"SLA fortsetzen".

## 4. Kanäle

Vier Odoo-11-Kanäle sind hergestellt: Email, Manual, Website (Public),
Website (User); Phone und Other bleiben als Odoo-18-Zusatz. Keine weitere
Konfiguration nötig.

## 5. Öffentliches Formular und Spamschutz

- Route: `/support/ticket/new` (ohne Anmeldung).
- Honigtopf und Rate-Limit (5 je IP und Stunde, 60 gesamt je Stunde) sind aktiv
  und in den Helpdesk-Einstellungen änderbar.
- reCAPTCHA: Schlüssel unter Einstellungen > Google reCAPTCHA eintragen
  (Odoo 11 hatte reCAPTCHA im Formular). Ohne Schlüssel ist die Prüfung inaktiv.
- Team für öffentliche Tickets in den Helpdesk-Einstellungen hinterlegen.

## 6. E-Mail-Eingang

Odoo 11 hatte keinen Ticket-Alias (Tickets kamen über das Website-Formular);
der Kanal "Email" entsteht beim Mail-Eingang. Falls gewünscht: Alias am Team
hinterlegen (z. B. support@it-kommunal.at) - damit werden Mails automatisch
Tickets mit Kanal "Email".

## 7. Stammdaten

**Prioritäten** (Odoo 11, Farben beibehalten):

| Name | Farbe |
|---|---|
| Niedrig | #ffff00 |
| Mittel | #ffbf00 |
| Hoch | #ff0000 |
| Angebotsanforderung | #58acfa |

**Kategorien** (Odoo 11, 17 Hauptkategorien): amtsweg.gv.at (Formulare & Postfächer),
Amtssignatur (Sendhybrid Client), E-Learning (Städtebund Academy),
Verwaltungsmanager (MAYAN EDMS), Gemeindeverordnungen Kärnten & amtstafel.at,
Communex (vormals Intrakommuna), Gemeindecloud/Verwaltungscloud, Hinweisportal,
Public Management Expert*Innen-Netzwerk, Acta Nova, IFG-Portal, Sonstiges,
Vertragsmanagement, IFG-Verfahren, Anonymisierungsportal, opendesk,
Kommunaler KI-Assistent. (In der Testinstanz bereits vorhanden; Odoo 11 hatte
zusätzlich eine leere Kategorie - nicht übernehmen.)

**Unterkategorien** (Odoo 11, 20 Stück): Allgemeine Anfrage (Support),
Störung/Fehler melden, Angebot anfordern, Individuelle Formularerstellung und
Deployment, Als Administrator anmelden, Verordnung löschen, allgemeiner Support,
Zugangsdaten vergessen - jeweils der passenden Hauptkategorie zugeordnet.

**Zusatzfelder je Unterkategorie** (Odoo 11 nutzte 191 Werte). Belegte Definitionen:

| Zusatzfeld | Unterkategorie |
|---|---|
| Einwohnerzahl (Hauptwohnsitze) | Angebot anfordern (amtsweg.gv.at, Amtssignatur) |
| Produkt (Basis, Bundesland Standard, Bundesland Premium) | Angebot anfordern (amtsweg.gv.at) |
| Gemeinde \| Name, Gemeinde \| Gemeindekennziffer (GKZ), Gemeinde \| Mitglied im Österreichischen Städtebund? | Als Administrator anmelden |
| Administrator \| Vor- & Nachname, Administrator \| E-Mail Adresse, Administrator \| Position | Als Administrator anmelden |
| Name der zu löschenden Datei | Verordnung löschen |

## 8. Nummernkreis

Fortlaufend, lückenlos, ohne Präfix - bereits eingestellt (wie Odoo 11).
Die Zählung beginnt neu, da keine Altdaten übernommen werden.

## 9. Was bewusst nicht konfiguriert wird

- Genehmigungsanfrage und Umfrage (in Odoo 11 mit 2 Bewertungen praktisch ungenutzt).
- Help Groups / Help Pages (0 Datensätze, Menü entfernt).
- Zuordnungen über Datenbank-IDs: es wird ausschliesslich über Namen und
  Kennungen gearbeitet.
