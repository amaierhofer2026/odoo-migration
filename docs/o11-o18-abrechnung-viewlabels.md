# View-Bezeichnungen Abrechnung (Odoo 11 gegen Odoo 18)

Erzeugt von `scripts/check_abrechnung_viewlabels.py` (Stand 30.09.2026, Session 122).

## Listen: Spalten

| Odoo-11-Feld | Odoo-11-Bezeichnung | Odoo-18-Feld | Odoo-18-Bezeichnung |
| --- | --- | --- | --- |
| `partner_id` | Lieferant | `invoice_partner_display_name` | Kunde |
| `date_invoice` | Rechnungsdatum | `invoice_date` | Rechnungsdatum |
| `number` | - | `name` | - |
| `reference` | - | `ref` | - |
| `date_due` | - | `invoice_date_due` | - |
| `origin` | - | `invoice_origin` | Referenzbeleg |
| `amount_total_signed` | Total | `amount_total_in_currency_signed` | Total |
| `residual_signed` | Zu Bezahlen | `amount_residual_signed` | Zu Bezahlen |
| `state` | - | `state` | - |
| `type` | - | `move_type` | - |
| `user_id` | - | `invoice_user_id` | Verkäufer |
| `team_id` | - | `team_id` | - |
| `payment_term_id` | - | `invoice_payment_term_id` | - |
| `name` | - | `narration` | - |

## Suche: Filter

| System | Bezeichnung | Bedingung |
| --- | --- | --- |
| Odoo 11 | Entwurf | [('state','=','draft')] |
| Odoo 11 | Offen | [('state', '=', 'open')] |
| Odoo 11 | Bezahlt | [('state', '=', 'paid')] |
| Odoo 11 | Überfällig | ['&', ('date_due', '<', time.strftime('%Y-%m-%d')), ('state', '=', 'open')] |
| Odoo 11 | - | [('user_id','=',uid)] |
| Odoo 11 | Meine Aktivitäten | [('activity_ids.user_id', '=', uid)] |
| Odoo 11 | Verspätete Aktivitäten | [('activity_ids.date_deadline', '<', context_today().strftime('%Y-%m-%d'))] |
| Odoo 11 | Heutige Aktivitäten | [('activity_ids.date_deadline', '=', context_today().strftime('%Y-%m-%d'))] |
| Odoo 11 | Anstehende Aktivitäten | [('activity_ids.date_deadline', '>', context_today().strftime('%Y-%m-%d'))       |
| Odoo 18 | - | [('invoice_user_id', '=', uid)] |
| Odoo 18 | Entwurf | [('state','=','draft')] |
| Odoo 18 | Gebucht | [('state', '=', 'posted')] |
| Odoo 18 | Abgebrochen | [('state', '=', 'cancel')] |
| Odoo 18 | Nicht gesendet | [('is_move_sent', '=', False)] |
| Odoo 18 | Ausgangsrechnungen | [('move_type', '=', 'out_invoice')] |
| Odoo 18 | Gutschriften | [('move_type', '=', 'out_refund')] |
| Odoo 18 | Zu prüfen | [('checked', '=', False), ('state', '!=', 'draft')] |
| Odoo 18 | Peppol bereit | [('state', '=', 'posted'), ('peppol_move_state', '=', 'ready'), ('move_type', 'i |
| Odoo 18 | Zu zahlen | [('state', '!=', 'cancel'), ('payment_state', 'in', ('not_paid', 'partial')), (' |
| Odoo 18 | In Zahlung | [('state', '=', 'posted'), ('payment_state', '=', 'in_payment')] |
| Odoo 18 | Überfällig | [                         ('invoice_date_due', '<', time.strftime('%Y-%m-%d')),  |
| Odoo 18 | Offen | [('state', '=', 'posted'), ('payment_state', 'in', ('not_paid', 'partial'))] |
| Odoo 18 | Bezahlt | [('payment_state', '=', 'paid')] |
| Odoo 18 | Rechnungsdatum |  |
| Odoo 18 | Buchungsdatum |  |
| Odoo 18 | Fälligkeitsdatum |  |
| Odoo 18 | Meine Aktivitäten | [('activity_user_id', '=', uid)] |
| Odoo 18 | Verspätete Aktivitäten | [('activity_ids.date_deadline', '<', context_today().strftime('%Y-%m-%d'))] |
| Odoo 18 | Heutige Aktivitäten | [('activity_ids.date_deadline', '=', context_today().strftime('%Y-%m-%d'))] |
| Odoo 18 | Anstehende Aktivitäten | [('activity_ids.date_deadline', '>', context_today().strftime('%Y-%m-%d'))] |
| Odoo 18 | Verspätete Aktivitäten | [('my_activity_date_deadline', '<', context_today().strftime('%Y-%m-%d'))] |
| Odoo 18 | Heutige Aktivitäten | [('my_activity_date_deadline', '=', context_today().strftime('%Y-%m-%d'))] |
| Odoo 18 | Anstehende Aktivitäten | [('my_activity_date_deadline', '>', context_today().strftime('%Y-%m-%d'))] |

## Suche: Gruppierungen

| System | Bezeichnung | Bedingung |
| --- | --- | --- |
| Odoo 11 | Partner | {'group_by':'commercial_partner_id'} |
| Odoo 11 | Verkäufer | {'group_by':'user_id'} |
| Odoo 11 | Status | {'group_by':'state'} |
| Odoo 11 | Vertriebskanal | [] |
| Odoo 11 | Rechnungsdatum | {'group_by':'date_invoice'} |
| Odoo 11 | Fälligkeit | {'group_by':'date_due'} |
| Odoo 18 | Verkäufer | {'group_by':'invoice_user_id'} |
| Odoo 18 | Partner | {'group_by':'partner_id'} |
| Odoo 18 | Status | {'group_by':'state'} |
| Odoo 18 | Verkaufsteam | [] |
| Odoo 18 | Peppol-Status | {'group_by': 'peppol_move_state'} |
| Odoo 18 | Zahlungsmethode | {'group_by': 'preferred_payment_method_line_id'} |
| Odoo 18 | Journal | [] |
| Odoo 18 | Rechnungsdatum | {'group_by': 'invoice_date'} |
| Odoo 18 | Fälligkeit | {'group_by': 'invoice_date_due'} |
| Odoo 18 | Datum | {'group_by': 'date'} |
| Odoo 18 | Sequenz-Präfix | {'group_by': 'sequence_prefix'} |

## Formular: Reiter, Gruppen, Knoepfe

- Odoo 11 Reiter: ['Rechnung', 'Andere Informationen']
- Odoo 18 Reiter: ['Rechnungszeilen', 'Andere Informationen', 'Weitere Informationen']
- Odoo 11 Gruppen: []
- Odoo 18 Gruppen: ['Buchhaltung', 'Herkunft (Migration)', 'Rechnung']
- Odoo 11 Knoepfe: ['Bestätigen', 'Einzahlung erfassen', 'Nach Gutschrift fragen', 'Auf Entwurf setzen']
- Odoo 18 Knoepfe: ['Abbrechen', 'Als geprüft markieren', 'Auf Entwurf setzen', 'Bestätigen', 'Buchen', 'Buchung stornieren', 'Drucken', 'Einzahlung erfassen', 'Katalog', 'Nach Gutschrift fragen', 'PEPPOL abbrechen', 'Senden', 'Sperren', 'Steuern und Konten aktualisieren', 'Stornierung anfordern', 'Stornobuchung', 'Transaktion erfassen', 'Transaktion stornieren', 'Vorschau', 'Zahlen']
