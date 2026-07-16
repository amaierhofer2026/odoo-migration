# ITK-Nummernkreise — Odoo 11 → Odoo 18

> Quelle: Odoo-11-Datenbank (ir.sequence) + itk_nummernkreise.txt
> Stand: 15.07.2026

## IST-Stand Odoo 11 (aus DB ausgelesen)

| Sequenz | Code | Präfix | Padding | Next | Date-Range |
|---|---|---|---|---|---|
| Ausgangsrechnungen | — | R-%(y)s | 3 | 1 | Ja |
| Eingangsrechnungen | — | ER-%(y)s | 5 | 1 | Ja |
| Angebote/Aufträge | sale.order | A-%(y)s | 5 | 1 | Ja |
| Beschaffungsaufträge | purchase.order | E-%(y)s | 5 | 1 | Ja |
| Nutzungsvereinbarungen | sale.subscription | NV- | 5 | 1 | Nein |

## Abweichungen zur Doku (itk_nummernkreise.txt)

| Feld | Doku | DB (Ist) |
|---|---|---|
| Rechnungen Padding | 0 | 3 |
| Rechnungen Next | 111 | 1 (date_range) |
| Nutzungsvereinbarungen | NV-%(y)s | NV- (ohne Jahr) |

## In Odoo 18 einzurichten

1. Einstellungen → Technisch → Sequenzen & Identifikationsarten → Sequenzen
2. Für jede Sequenz:
   - Sequenzcode setzen (für sale.order, purchase.order, sale.subscription)
   - Präfix entsprechend obiger Tabelle
   - Nächste Nummer = 1
   - Bei date_range=True: Datumsbereich für Jahreswechsel konfigurieren

## ACHTUNG

- Rechnungssequenzen haben KEINEN Standard-Code (code=False in Odoo 11)
  → In Odoo 18 müssen sie dem Buchungsjournal zugewiesen werden
- Die Sequenz ist fachlich kritisch — falsche Nummern können zu
  Buchhaltungsproblemen führen (lückenlose Nummerierung gesetzlich vorgeschrieben)
- Nach Produktivsetzung NIE MEHR ändern
