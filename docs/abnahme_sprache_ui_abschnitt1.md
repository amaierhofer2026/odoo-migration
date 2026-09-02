# Abnahme Abschnitt 1 (A Sprache / sichtbare UI-Texte) — Detail-Inventar

> **Stand:** 02.09.2026 (Session 80) — read-only-RPC-Inventar gegen die VM-Referenzumgebung
> https://k001959vsx.ipax.at (DB odoo18_test), uid=2, Sprachkontexte de_DE und en_US.
> Quellen: `ir.module.module.shortdesc`, `ir.ui.menu`, `ir.actions.act_window`, `ir.ui.view`,
> `ir.model.fields.field_description`, `fields_get`, `ir.model.fields.selection`, Datensatznamen
> (Stages/Kategorien/Aktivitätstypen). **Nur gelesen — nichts verändert.**
> Methodik-Hinweis: Ein „Label de == en“ bedeutet, dass für de_DE kein eigener Text hinterlegt ist
> (Anzeige = englischer/technischer Text). Felder wie `Name`, `ID`, `Sequence`, `Partner` sind
> im Deutschen identische Fachbegriffe und deshalb KEINE Befunde. Die Sprach-Klassifikation ist
> eine Wortliste-Heuristik; jede Zeile ist vor einer Korrektur einzeln zu prüfen.

## Zusammenfassung je Modul

| Modul | Menüs | Actions | Views | Felder (modul-eigen) | Sichtbar auffällig (Kurzfassung) |
|---|---|---|---|---|---|
| itk_crm | 0 | 3 | 7 | 105 | Menüs/Aktionen deutsch (Kundenverwaltung, Aktivitäten, Interessenten, Neue Aktivität). Custom-Felder res.partner/res.users: ~15 englische Labels (Status of Community, Member of City Alliance, Title in Front/Back, First/Last name, ...). 4 x_-Felder crm.lead: Labels 'Lead Status'/'Lead Quelle'/'Anrede Lead' (en/teils), Werte deutsch. Eigene Models itk_crm.*: Audit-Labels en (Created on/Display Name/...). |
| itk_translation | 9 | 6 | 0 | 0 | Top-Menü 'ITK-Menu' (technisch); Untermenüs/Actions ENGLISCH (Partner: Actual/All/Former/Target customers; Reseller: All Resellers/All Magnitudes). |
| itk_subscription | 12 | 14 | 30 | 211 | Menüs/Actions deutsch (de.po geladen). Felder sale.subscription/-template + Zusatzfelder sale.order/product/account.move: überwiegend englisch sichtbar (~70+ Labels; Start/End Date, Notice Period, Sale Order, Subscription Management, Customer ...). |
| itk_product | 0 | 0 | 2 | 15 | Keine Menüs. Felder product: 'Product-Type', 'To multiply by Factor(thsd)' englisch sichtbar. |
| itk_sale_management | 0 | 0 | 5 | 5 | Keine Menüs/Actions (nur Layout-Views). 5 Felder sale.order englisch: Administrative/Technical/Sale/Final Customer, Product Category. |
| itk_valorisierung | 2 | 1 | 3 | 11 | Menü/Action deutsch ('Valorisierung'/'Valorisierungs Text'). Feld account.move 'Valorisation Text' englisch; eigene Model-Audit-Labels en. |
| itk_projectcategory | 0 | 0 | 1 | 11 | Kein Menü. Feld account.move 'Project Category' englisch (Rechnungsformular). |
| itk_base_setup | 0 | 1 | 4 | 4 | Felder 'Ist ein Kunde'/'Ist ein Lieferant' deutsch (OK). |
| itk_third_party_setup | 0 | 0 | 0 | 0 | Keine sichtbare UI. |
| itk_reports | 0 | 0 | 11 | 0 | Keine Menüs/Fields (reine Report-Templates; Berichtsprüfung später). |
| itk_saleorder_lines | 1 | 1 | 0 | 2 | Menü/Action 'Aufträge / All Order Lines', 'Order Lines' englisch sichtbar. |
| itk_multifactor | 0 | 3 | 7 | 25 | 3 Wizard-Action-Namen englisch ('Set Pricelist for Subscriptions', 'Update Multifactor ...', 'Update Population and Multifactor for Partners'); Felder 'To multiply by Factor(per 1000)', 'Multiplication Factor/Thsd' englisch (Produkt/Kontakt/Abo-Zeile). |
| itk_automated_actions | 0 | 0 | 0 | 0 | Keine sichtbare UI (Automation, E-Mail). |
| itk_helpdesk_category_user | 0 | 0 | 3 | 1 | Feld helpdesk.ticket.category.user_ids 'Assigned Users' englisch sichtbar (Kategorie-Formular). |
| itk_helpdesk_compat | 10 | 5 | 15 | 49 | Menüs/Actions/Felder deutsch; Ausnahmen: Menü+Aktion 'Support Tickets' (englisch); eigene Modelle: Audit-Labels en. |
| helpdesk_mgmt | 14 | 13 | 33 | 201 | Menüs gemischt: 'Tickets', 'Meine Tickets', Stufen/Kategorien/Teams/Kanäle/Stichwörter deutsch; 'All Tickets', 'Dashboard', 'Settings' (unter Konfiguration), 'Helpdesk Ticket' (Action) englisch. Ticket-Kernfelder deutsch; Lücken englisch (duplicate_*, 'Commercial Partner', 'Followers (Partners)', Settings-Felder 'Auto assign tickets'/'Select category in Helpdesk portal' u. a.). |
| helpdesk_mgmt_project | 0 | 2 | 12 | 14 | Actions 'Helpdesk Tickets'/'Tickets'; Projekt-/Task-Zusatzfelder englisch ('Ticket Count', 'Number of tickets', 'Use Tickets as', 'Helpdesk Ticket Count'). |
| helpdesk_mgmt_sla | 2 | 2 | 12 | 76 | Menüs 'SLA'/'SLA Report' (en); helpdesk.sla- und helpdesk.ticket.sla-Felder überwiegend englisch (Days/Hours, Deadline, Expected Stage, Ignore Stages, ...). |
| helpdesk_mgmt_timesheet | 1 | 1 | 14 | 14 | Menü 'Timesheets'; Ticket-Zusatzfelder englisch ('Allow Timesheet', 'Planned/Remaining/Total Hours', 'Show Timesheet Portal', 'Last Timesheet Activity'). |
| project_timesheet_time_control | 1 | 1 | 10 | 22 | Menü+Aktion 'Start work' (Zeiterfassung), 'Show Time Control', 'Start Time'/'End Time' englisch. |
| server_action_mass_edit | 0 | 0 | 2 | 33 | Feld-/Wizard-Texte deutsch (de.po geladen); nur Modul-Label 'Mass Editing' (F6). |

## Menü-Baum der Modul-Menüs (sichtbarer Name de_DE)

> Es werden die tatsächlich hinterlegten Texte gezeigt (de = Anzeige für den deutschen Benutzer;
> en nur bei Abweichung). Ob ein Text fachlich deutsch sein soll, ist Abnahme-Entscheidung.
### itk_translation
- `ITK-Menu` (id 733) — de='ITK-Menu'
- `ITK-Menu / Partner` (id 734) — de='Partner'
- `ITK-Menu / Partner / Actual customers` (id 737) — de='Actual customers'
- `ITK-Menu / Partner / All customers` (id 736) — de='All customers'
- `ITK-Menu / Partner / Former Customers` (id 738) — de='Former Customers'
- `ITK-Menu / Partner / Target Customers` (id 739) — de='Target Customers'
- `ITK-Menu / Reseller` (id 735) — de='Reseller'
- `ITK-Menu / Reseller / All Magnitudes` (id 741) — de='All Magnitudes'
- `ITK-Menu / Reseller / All Resellers` (id 740) — de='All Resellers'

### itk_subscription
- `Abonnements` (id 586) — de='Abonnements' en='Subscriptions'
- `Abonnements / Abonnements` (id 587) — de='Abonnements' en='Subscriptions'
- `Abonnements / Abonnements / Abo-Ansichten` (id 591) — de='Abo-Ansichten' en='All Subscription Lines'
- `Abonnements / Abonnements / Abonnement Produkte` (id 592) — de='Abonnement Produkte' en='Subscription Products'
- `Abonnements / Abonnements / Abonnements` (id 588) — de='Abonnements' en='Subscriptions'
- `Abonnements / Abonnements / Endet in weniger als 7 Monaten` (id 590) — de='Endet in weniger als 7 Monaten' en='Ending in less than 7 Months'
- `Abonnements / Abonnements / Zu erneuernde Abonnements` (id 589) — de='Zu erneuernde Abonnements' en='Subscriptions to Renew'
- `Abonnements / Berichtswesen` (id 596) — de='Berichtswesen' en='Reporting'
- `Abonnements / Konfiguration` (id 593) — de='Konfiguration' en='Configuration'
- `Abonnements / Konfiguration / Einstellungen` (id 598) — de='Einstellungen' en='Settings'
- `Abonnements / Konfiguration / Gründe für Beendigung` (id 594) — de='Gründe für Beendigung' en='Close Reasons'
- `Abonnements / Konfiguration / Vorlagen für Abonnements` (id 595) — de='Vorlagen für Abonnements' en='Subscription Templates'

### itk_valorisierung
- `Rechnungsstellung / Konfiguration` (id 599) — de='Konfiguration' en='Configuration'
- `Rechnungsstellung / Konfiguration / Valorisierung` (id 600) — de='Valorisierung'

### itk_saleorder_lines
- `Aufträge / All Order Lines` (id 601) — de='All Order Lines'

### itk_helpdesk_compat
- `Konfiguration / Einstellungen` (id 866) — de='Einstellungen'
- `Konfiguration / Helpdesk Gruppen` (id 864) — de='Helpdesk Gruppen'
- `Konfiguration / Hilfeseiten` (id 865) — de='Hilfeseiten'
- `Konfiguration / Kategorien` (id 858) — de='Kategorien'
- `Konfiguration / Prioritäten` (id 862) — de='Prioritäten'
- `Konfiguration / SLA's` (id 863) — de="SLA's"
- `Konfiguration / Status` (id 860) — de='Status'
- `Konfiguration / Stichwörter` (id 861) — de='Stichwörter'
- `Konfiguration / Unterkategorien` (id 859) — de='Unterkategorien'
- `Tickets / Support Tickets` (id 891) — de='Support Tickets'

### helpdesk_mgmt
- `Helpdesk` (id 742) — de='Helpdesk'
- `Helpdesk / Berichtswesen` (id 747) — de='Berichtswesen' en='Reporting'
- `Helpdesk / Berichtswesen / Tickets` (id 748) — de='Tickets'
- `Helpdesk / Dashboard` (id 743) — de='Dashboard'
- `Helpdesk / Konfiguration` (id 749) — de='Konfiguration' en='Configuration'
- `Helpdesk / Konfiguration / Kanäle` (id 751) — de='Kanäle' en='Channels'
- `Helpdesk / Konfiguration / Kategorien` (id 752) — de='Kategorien' en='Categories'
- `Helpdesk / Konfiguration / Settings` (id 750) — de='Settings'
- `Helpdesk / Konfiguration / Stufen` (id 753) — de='Stufen' en='Stages'
- `Helpdesk / Konfiguration / Teams` (id 754) — de='Teams'
- `Helpdesk / Konfiguration / Ticket Stichwörter` (id 755) — de='Ticket Stichwörter' en='Ticket Tags'
- `Helpdesk / Tickets` (id 744) — de='Tickets'
- `Helpdesk / Tickets / All Tickets` (id 746) — de='All Tickets'
- `Helpdesk / Tickets / Meine Tickets` (id 745) — de='Meine Tickets' en='My Tickets'

### helpdesk_mgmt_sla
- `Berichtswesen / SLA Report` (id 775) — de='SLA Report'
- `Konfiguration / SLA` (id 776) — de='SLA'

### helpdesk_mgmt_timesheet
- `Helpdesk / Timesheets` (id 757) — de='Timesheets'

### project_timesheet_time_control
- `Zeiterfassung / Start work` (id 756) — de='Start work'

## Aktionen (ir.actions.act_window) mit nicht-deutschem sichtbaren Namen

### itk_crm
- de='Interessenten' (en='Interessenten') — crm.lead

### itk_translation
- de='Actual customers' (en='Actual customers') — res.partner
- de='All customers' (en='All customers') — res.partner
- de='Former Customers' (en='Former Customers') — res.partner
- de='Target Customers' (en='Target Customers') — res.partner

### itk_subscription
- de='Abonnementanalyse' (en='Subscription Analysis') — sale.subscription.report
- de='Abonnements' (en='Subscriptions') — sale.subscription
- de='Abonnements' (en='Subscriptions') — sale.subscription
- de='Abonnements' (en='Subscriptions') — sale.subscription.line
- de='Einstellungen' (en='Settings') — res.config.settings
- de='Endet in weniger als 7 Monaten' (en='Ending in less than 7 Months') — sale.subscription
- de='Produkte' (en='Products') — product.template

### itk_base_setup
- de='Abonnements' (en='Abonnements') — sale.subscription.line

### itk_saleorder_lines
- de='Order Lines' (en='Order Lines') — sale.order.line

### itk_multifactor
- de='Set Pricelist for Subscriptions' (en='Set Pricelist for Subscriptions') — sale.subscription.set.pricelist.confirm
- de='Update Multifactor for Subscriptionlines' (en='Update Multifactor for Subscriptionlines') — sale.subscriptionline.multifactor.update.confirm
- de='Update Population and Multifactor for Partners' (en='Update Population and Multifactor for Partners') — res.partner.multifactor.update.confirm

### itk_helpdesk_compat
- de='Kategorien' (en='Kategorien') — helpdesk.ticket.category
- de='Support Tickets' (en='Support Tickets') — helpdesk.ticket
- de='Unterkategorien' (en='Unterkategorien') — helpdesk.ticket.category

### helpdesk_mgmt
- de='Berichtswesen' (en='Reporting') — helpdesk.ticket
- de='Dashboard' (en='Dashboard') — helpdesk.ticket.team
- de='Helpdesk Ticket' (en='Helpdesk Ticket') — helpdesk.ticket
- de='Helpdesk Ticket' (en='Helpdesk Ticket') — helpdesk.ticket
- de='Helpdesk Ticket' (en='Helpdesk Ticket') — helpdesk.ticket
- de='Kategorien' (en='Categories') — helpdesk.ticket.category
- de='Meine Tickets' (en='My Tickets') — helpdesk.ticket
- de='Settings' (en='Settings') — res.config.settings
- de='Stufen' (en='Stages') — helpdesk.ticket.stage
- de='Teams' (en='Teams') — helpdesk.ticket.team
- de='Tickets' (en='Tickets') — helpdesk.ticket

### helpdesk_mgmt_project
- de='Helpdesk Tickets' (en='Helpdesk Tickets') — helpdesk.ticket
- de='Tickets' (en='Tickets') — helpdesk.ticket

### helpdesk_mgmt_sla
- de='Helpdesk SLA' (en='Helpdesk SLA') — helpdesk.sla
- de='SLA Report' (en='SLA Report') — helpdesk.sla.report

### helpdesk_mgmt_timesheet
- de='Timesheets' (en='Timesheets') — account.analytic.line

### project_timesheet_time_control
- de='Start work' (en='Start work') — hr.timesheet.switch

## Moduleigene Felder mit nicht-deutschem sichtbaren Label (de_DE-Anzeige)

### itk_crm
- `create_date` (itk_crm.communitycode): de='Created on'
- `create_uid` (itk_crm.communitycode): de='Created by'
- `display_name` (itk_crm.communitycode): de='Display Name'
- `create_date` (itk_crm.communitymagnitude): de='Created on'
- `create_uid` (itk_crm.communitymagnitude): de='Created by'
- `description` (itk_crm.communitymagnitude): de='Description'
- `display_name` (itk_crm.communitymagnitude): de='Display Name'
- `create_date` (itk_crm.statusofcommunity): de='Created on'
- `create_uid` (itk_crm.statusofcommunity): de='Created by'
- `display_name` (itk_crm.statusofcommunity): de='Display Name'
- `display_name_new` (itk_crm.statusofcommunity): de='Display Name New'
- `create_date` (itk_crm.statusofpartner): de='Created on'
- `create_uid` (itk_crm.statusofpartner): de='Created by'
- `display_name` (itk_crm.statusofpartner): de='Display Name'
- `create_date` (itk_crm.titleputinback): de='Created on'
- `create_uid` (itk_crm.titleputinback): de='Created by'
- `display_name` (itk_crm.titleputinback): de='Display Name'
- `create_date` (itk_crm.titleputinfront): de='Created on'
- `create_uid` (itk_crm.titleputinfront): de='Created by'
- `display_name` (itk_crm.titleputinfront): de='Display Name'
- `itk_target_model_id` (mail.activity.schedule): de='Dokumenttyp'
- `itk_target_res_id` (mail.activity.schedule): de='Dokument'
- `res_model` (mail.activity.schedule): de='Modell' en='Model'
- `asset_partner` (res.partner): de='Asset Partner'
- `community_magnitude` (res.partner): de='Magnitude'
- `community_salutation` (res.partner): de='Organisationsbezeichnung' en='Salutation of Community'
- `firstname` (res.partner): de='First name'
- `latitude` (res.partner): de='Latitude'
- `longitude` (res.partner): de='Longitude'
- `member_of_city_alliance` (res.partner): de='Member of City Alliance'
- `official_email` (res.partner): de='Email offiziell' en='Official Email'
- `population` (res.partner): de='Size of Population'
- `reseller` (res.partner): de='Reseller'
- `sales_as_final_customer_count` (res.partner): de='# of Sales as Final Customer'
- `salutation` (res.partner): de='Salutation'
- `status_of_community` (res.partner): de='Status of Community'
- `title_put_in_back` (res.partner): de='Title in Back'
- `title_put_in_front` (res.partner): de='Title in Front'
- `type` (res.partner): de='Adresstyp' en='Address Type'
- `asset_partner` (res.users): de='Asset Partner'
- `attention_of` (res.users): de='For the Attention of'
- `community_magnitude` (res.users): de='Magnitude'
- `community_salutation` (res.users): de='Salutation of Community'
- `firstname` (res.users): de='First name'
- `latitude` (res.users): de='Latitude'
- `longitude` (res.users): de='Longitude'
- `member_of_city_alliance` (res.users): de='Member of City Alliance'
- `official_email` (res.users): de='Official Email'
- `population` (res.users): de='Size of Population'
- `reseller` (res.users): de='Reseller'
- `sales_as_final_customer_count` (res.users): de='# of Sales as Final Customer'
- `salutation` (res.users): de='Salutation'
- `status_of_community` (res.users): de='Status of Community'
- `status_of_partner_id` (res.users): de='Status of Partner'
- `title_put_in_back` (res.users): de='Title in Back'
- `title_put_in_front` (res.users): de='Title in Front'
- `type` (res.users): de='Adresstyp' en='Address Type'

### itk_subscription
- `subscription_count` (account.analytic.account): de='Subscription Count'
- `subscription_ids` (account.analytic.account): de='Subscriptions'
- `notice` (account.bank.statement.line): de='Invoice Note'
- `sale_order_confirmation_date` (account.bank.statement.line): de='Saleorder Confirmation Date'
- `notice` (account.move): de='Invoice Note'
- `sale_order_confirmation_date` (account.move): de='Saleorder Confirmation Date'
- `subscription_id` (account.move.line): de='Subscription'
- `create_date` (itk_subscription.noticeperiod): de='Created on'
- `create_uid` (itk_subscription.noticeperiod): de='Created by'
- `display_name` (itk_subscription.noticeperiod): de='Display Name'
- `invoice_id` (payment.transaction): de='Invoice'
- `recurring_invoice` (product.product): de='Subscription Product'
- `subscription_template_id` (product.product): de='Subscription Template'
- `recurring_invoice` (product.template): de='Subscription Product'
- `subscription_template_id` (product.template): de='Subscription Template'
- `module_sale_subscription_asset` (res.config.settings): de='Deferred revenue management for subscriptions'
- `module_sale_subscription_dashboard` (res.config.settings): de='Sale Subscription Dashboard'
- `subscription_count` (res.partner): de='Subscriptions'
- `subscription_count` (res.users): de='Subscriptions'
- `subscription_count` (sale.order): de='Subscription Count'
- `subscription_management` (sale.order): de='Subscription Management'
- `subscription_id` (sale.order.line): de='Subscription'
- `activity_calendar_event_id` (sale.subscription): de='Next Activity Calendar Event'
- `activity_date_deadline` (sale.subscription): de='Next Activity Deadline'
- `activity_exception_decoration` (sale.subscription): de='Activity Exception Decoration'
- `activity_ids` (sale.subscription): de='Activities'
- `activity_state` (sale.subscription): de='Activity State'
- `activity_summary` (sale.subscription): de='Next Activity Summary'
- `activity_type_icon` (sale.subscription): de='Activity Type Icon'
- `activity_type_id` (sale.subscription): de='Next Activity Type'
- `activity_user_id` (sale.subscription): de='Responsible User'
- `code` (sale.subscription): de='Reference'
- `contract_termination_period_unit` (sale.subscription): de='Contract Termination Period Unit'
- `country_id` (sale.subscription): de='Country'
- `create_date` (sale.subscription): de='Created on'
- `create_uid` (sale.subscription): de='Created by'
- `currency_id` (sale.subscription): de='Currency'
- `date` (sale.subscription): de='End Date'
- `date_start` (sale.subscription): de='Start Date'
- `description` (sale.subscription): de='Description'
- `display_name` (sale.subscription): de='Display Name'
- `end_of_contract_date` (sale.subscription): de='End of Contract Date'
- `industry_id` (sale.subscription): de='Industry'
- `invoice_count` (sale.subscription): de='Invoice Count'
- `message_follower_ids` (sale.subscription): de='Followers'
- `message_has_error_counter` (sale.subscription): de='Number of errors'
- `message_ids` (sale.subscription): de='Messages'
- `message_is_follower` (sale.subscription): de='Is Follower'
- `message_needaction_counter` (sale.subscription): de='Number of Actions'
- `message_partner_ids` (sale.subscription): de='Followers (Partners)'
- `minimum_contract_period_unit` (sale.subscription): de='Minimum Contract Period Unit'
- `my_activity_date_deadline` (sale.subscription): de='My Activity Deadline'
- `payment_mandatory` (sale.subscription): de='Automatic Payment'
- `payment_token_id` (sale.subscription): de='Payment Token'
- `pricelist_id` (sale.subscription): de='Pricelist'
- `rating_ids` (sale.subscription): de='Ratings'
- `recurring_invoice_line_ids` (sale.subscription): de='Invoice Lines'
- `recurring_monthly` (sale.subscription): de='Monthly Recurring Revenue'
- `recurring_next_date` (sale.subscription): de='Date of Next Invoice'
- `recurring_rule_type` (sale.subscription): de='Recurrence'
- `recurring_total` (sale.subscription): de='Recurring Price'
- `sale_order_confirmation_date` (sale.subscription): de='Date of first Saleorder'
- `sale_order_count` (sale.subscription): de='Sale Order Count'
- `sale_order_id` (sale.subscription): de='Sale Order'
- `template_id` (sale.subscription): de='Subscription Template'
- `user_id` (sale.subscription): de='Salesperson'
- `website_message_ids` (sale.subscription): de='Website Messages'
- `website_url` (sale.subscription): de='Website URL'
- `create_date` (sale.subscription.close.reason): de='Created on'
- `create_uid` (sale.subscription.close.reason): de='Created by'
- `display_name` (sale.subscription.close.reason): de='Display Name'
- `create_date` (sale.subscription.close.reason.wizard): de='Created on'
- `create_uid` (sale.subscription.close.reason.wizard): de='Created by'
- `display_name` (sale.subscription.close.reason.wizard): de='Display Name'
- `analytic_account_id` (sale.subscription.line): de='Subscription'
- `create_date` (sale.subscription.line): de='Created on'
- `create_uid` (sale.subscription.line): de='Created by'
- `display_name` (sale.subscription.line): de='Display Name'
- `name` (sale.subscription.line): de='Description'
- `price_subtotal` (sale.subscription.line): de='Sub Total'
- `product_id` (sale.subscription.line): de='Product'
- `quantity` (sale.subscription.line): de='Quantity'
- `salesperson_id` (sale.subscription.line): de='Salesperson'
- `uom_id` (sale.subscription.line): de='Unit of Measure'
- `categ_id` (sale.subscription.report): de='Product Category'
- `commercial_partner_id` (sale.subscription.report): de='Commercial Partner'
- `country_id` (sale.subscription.report): de='Country'
- `date_end` (sale.subscription.report): de='Date End'
- `date_start` (sale.subscription.report): de='Date Start'
- `display_name` (sale.subscription.report): de='Display Name'
- `industry_id` (sale.subscription.report): de='Industry'
- `pricelist_id` (sale.subscription.report): de='Pricelist'
- `product_id` (sale.subscription.report): de='Product'
- `product_tmpl_id` (sale.subscription.report): de='Product Template'
- `product_uom` (sale.subscription.report): de='Unit of Measure'
- `quantity` (sale.subscription.report): de='Quantity'
- `recurring_price` (sale.subscription.report): de='Recurring price(per period)'
- `state` (sale.subscription.report): de='State'
- `template_id` (sale.subscription.report): de='Subscription Template'
- `user_id` (sale.subscription.report): de='Sales Rep'
- `contract_termination_period_unit` (sale.subscription.template): de='Unit'
- `create_date` (sale.subscription.template): de='Created on'
- `create_uid` (sale.subscription.template): de='Created by'
- `display_name` (sale.subscription.template): de='Display Name'
- `journal_id` (sale.subscription.template): de='Accounting Journal'
- `message_follower_ids` (sale.subscription.template): de='Followers'
- `message_has_error_counter` (sale.subscription.template): de='Number of errors'
- `message_ids` (sale.subscription.template): de='Messages'
- `message_is_follower` (sale.subscription.template): de='Is Follower'
- `message_needaction_counter` (sale.subscription.template): de='Number of Actions'
- `message_partner_ids` (sale.subscription.template): de='Followers (Partners)'
- `minimum_contract_life_unit` (sale.subscription.template): de='Unit'
- `payment_mandatory` (sale.subscription.template): de='Automatic Payment'
- `product_count` (sale.subscription.template): de='Product Count'
- `product_ids` (sale.subscription.template): de='Product'
- `rating_ids` (sale.subscription.template): de='Ratings'
- `recurring_rule_type` (sale.subscription.template): de='Recurrence'
- `subscription_count` (sale.subscription.template): de='Subscription Count'
- `user_closable` (sale.subscription.template): de='Closable by customer'
- `website_message_ids` (sale.subscription.template): de='Website Messages'
- `create_date` (sale.subscription.wizard): de='Created on'
- `create_uid` (sale.subscription.wizard): de='Created by'
- `date_from` (sale.subscription.wizard): de='Discount Date'
- `display_name` (sale.subscription.wizard): de='Display Name'
- `option_lines` (sale.subscription.wizard): de='Options'
- `subscription_id` (sale.subscription.wizard): de='Subscription'
- `create_date` (sale.subscription.wizard.option): de='Created on'
- `create_uid` (sale.subscription.wizard.option): de='Created by'
- `display_name` (sale.subscription.wizard.option): de='Display Name'
- `name` (sale.subscription.wizard.option): de='Description'
- `product_id` (sale.subscription.wizard.option): de='Product'
- `quantity` (sale.subscription.wizard.option): de='Quantity'
- `uom_id` (sale.subscription.wizard.option): de='Unit of Measure'
- `wizard_id` (sale.subscription.wizard.option): de='Wizard'

### itk_product
- `create_date` (itk_product.product_type): de='Created on'
- `create_uid` (itk_product.product_type): de='Created by'
- `display_name` (itk_product.product_type): de='Display Name'
- `product_type_id` (product.product): de='Product-Type'
- `to_multiply_by_factor` (product.product): de='To multiply by Factor(thsd)'
- `type` (product.product): de='Produktart' en='Product Type'
- `product_type_id` (product.template): de='Product-Type'
- `to_multiply_by_factor` (product.template): de='To multiply by Factor(thsd)'
- `type` (product.template): de='Produktart' en='Product Type'

### itk_sale_management
- `administrative_contact_id` (sale.order): de='Administrative Contact'
- `final_customer_id` (sale.order): de='Final Customer'
- `product_category_id` (sale.order): de='Product Category'
- `sale_contact_id` (sale.order): de='Sale Contact'
- `technical_contact_id` (sale.order): de='Technical Contact'

### itk_valorisierung
- `create_date` (itk_valorisierung.valorisierung): de='Created on'
- `create_uid` (itk_valorisierung.valorisierung): de='Created by'
- `description` (itk_valorisierung.valorisierung): de='Description'
- `display_name` (itk_valorisierung.valorisierung): de='Display Name'

### itk_projectcategory
- `projectcategory_id` (account.bank.statement.line): de='Project Category'
- `projectcategory_id` (account.move): de='Project Category'
- `create_date` (itk_projectcategory.projectcategory): de='Created on'
- `create_uid` (itk_projectcategory.projectcategory): de='Created by'
- `display_name` (itk_projectcategory.projectcategory): de='Display Name'

### itk_saleorder_lines
- `salesperson_id` (sale.order.line): de='Salesperson'

### itk_multifactor
- `is_multi_factor_product` (product.product): de='To multiply by Factor(per 1000)'
- `is_multi_factor_product` (product.template): de='To multiply by Factor(per 1000)'
- `create_date` (res.partner.multifactor.update.confirm): de='Created on'
- `create_uid` (res.partner.multifactor.update.confirm): de='Created by'
- `display_name` (res.partner.multifactor.update.confirm): de='Display Name'
- `create_date` (sale.subscription.set.pricelist.confirm): de='Created on'
- `create_uid` (sale.subscription.set.pricelist.confirm): de='Created by'
- `display_name` (sale.subscription.set.pricelist.confirm): de='Display Name'
- `pricelist_id` (sale.subscription.set.pricelist.confirm): de='Pricelist'
- `create_date` (sale.subscriptionline.multifactor.update.confirm): de='Created on'
- `create_uid` (sale.subscriptionline.multifactor.update.confirm): de='Created by'
- `display_name` (sale.subscriptionline.multifactor.update.confirm): de='Display Name'

### itk_helpdesk_category_user
- `user_ids` (helpdesk.ticket.category): de='Assigned Users'

### itk_helpdesk_compat
- `close_comment` (helpdesk.ticket): de='Abschluss'
- `sub_category_id` (helpdesk.ticket): de='Unterkategorie'
- `support_comment` (helpdesk.ticket): de='Partner Kommentar'
- `create_date` (itk.helpdesk.priority): de='Created on'
- `create_uid` (itk.helpdesk.priority): de='Created by'
- `display_name` (itk.helpdesk.priority): de='Display Name'
- `create_date` (itk.helpdesk.subcategory.field): de='Created on'
- `create_uid` (itk.helpdesk.subcategory.field): de='Created by'
- `display_name` (itk.helpdesk.subcategory.field): de='Display Name'
- `field_type` (itk.helpdesk.subcategory.field): de='Typ'
- `help_text` (itk.helpdesk.subcategory.field): de='Hilfetext'
- `name` (itk.helpdesk.subcategory.field): de='Buchungstext'
- `required` (itk.helpdesk.subcategory.field): de='Pflichtfeld'
- `selection_options` (itk.helpdesk.subcategory.field): de='Auswahloptionen'
- `sequence` (itk.helpdesk.subcategory.field): de='Reihenfolge'
- `show_in_portal` (itk.helpdesk.subcategory.field): de='Im Portal anzeigen'
- `sub_category_id` (itk.helpdesk.subcategory.field): de='Unterkategorie'
- `create_date` (itk.helpdesk.subcategory.field.value): de='Created on'
- `create_uid` (itk.helpdesk.subcategory.field.value): de='Created by'
- `display_name` (itk.helpdesk.subcategory.field.value): de='Display Name'
- `field_id` (itk.helpdesk.subcategory.field.value): de='Feld'
- `field_type` (itk.helpdesk.subcategory.field.value): de='Feldtyp'
- `sub_category_id` (itk.helpdesk.subcategory.field.value): de='Unterkategorie'
- `ticket_id` (itk.helpdesk.subcategory.field.value): de='Ticket'
- `value_display` (itk.helpdesk.subcategory.field.value): de='Wert'

### helpdesk_mgmt
- `access_token` (helpdesk.ticket): de='Sicherheitstoken' en='Security Token'
- `access_warning` (helpdesk.ticket): de='Zugriffswarnung' en='Access warning'
- `active` (helpdesk.ticket): de='Aktiv' en='Active'
- `activity_calendar_event_id` (helpdesk.ticket): de='Next Activity Calendar Event'
- `activity_exception_icon` (helpdesk.ticket): de='Symbol' en='Icon'
- `category_id` (helpdesk.ticket): de='Kategorie' en='Category'
- `channel_id` (helpdesk.ticket): de='Kanal' en='Channel'
- `closed` (helpdesk.ticket): de='Abgeschlossen' en='Closed'
- `closed_date` (helpdesk.ticket): de='Abschlussdatum' en='Closed Date'
- `color` (helpdesk.ticket): de='Farbindex' en='Color Index'
- `commercial_partner_id` (helpdesk.ticket): de='Commercial Partner'
- `company_id` (helpdesk.ticket): de='Unternehmen' en='Company'
- `description` (helpdesk.ticket): de='Beschreibung' en='Description'
- `display_name` (helpdesk.ticket): de='Anzeigename' en='Display Name'
- `duplicate_id` (helpdesk.ticket): de='Duplicate of'
- `duplicate_ids` (helpdesk.ticket): de='Duplicate tickets'
- `duplicate_tracking_enabled` (helpdesk.ticket): de='Enable duplicate ticket tracking.'
- `duration_tracking` (helpdesk.ticket): de='Status time'
- `kanban_state` (helpdesk.ticket): de='Kanbanstufe' en='Kanban State'
- `message_follower_ids` (helpdesk.ticket): de='Followers'
- `message_ids` (helpdesk.ticket): de='Nachrichten' en='Messages'
- `message_is_follower` (helpdesk.ticket): de='Ist ein Follower' en='Is Follower'
- `message_partner_ids` (helpdesk.ticket): de='Followers (Partner)' en='Followers (Partners)'
- `name` (helpdesk.ticket): de='Titel' en='Title'
- `number` (helpdesk.ticket): de='Ticketnummer' en='Ticket number'
- `partner_email` (helpdesk.ticket): de='E-mail' en='Email'
- `partner_id` (helpdesk.ticket): de='Kontakt' en='Contact'
- `partner_name` (helpdesk.ticket): de='Partnername' en='Partner Name'
- `rating_ids` (helpdesk.ticket): de='Ratings'
- `sequence` (helpdesk.ticket): de='Sequenz' en='Sequence'
- `stage_id` (helpdesk.ticket): de='Stufe' en='Stage'
- `team_id` (helpdesk.ticket): de='Team'
- `unattended` (helpdesk.ticket): de='Unbeaufsichtigt' en='Unattended'
- `user_ids` (helpdesk.ticket): de='Benutzer' en='Users'
- `website_message_ids` (helpdesk.ticket): de='Website-Nachrichten' en='Website Messages'
- `active` (helpdesk.ticket.category): de='Aktiv' en='Active'
- `company_id` (helpdesk.ticket.category): de='Unternehmen' en='Company'
- `complete_name` (helpdesk.ticket.category): de='Complete Name'
- `display_name` (helpdesk.ticket.category): de='Anzeigename' en='Display Name'
- `parent_id` (helpdesk.ticket.category): de='Parent Category'
- `sequence` (helpdesk.ticket.category): de='Sequenz' en='Sequence'
- `show_in_portal` (helpdesk.ticket.category): de='Show In Portal'
- `active` (helpdesk.ticket.channel): de='Aktiv' en='Active'
- `company_id` (helpdesk.ticket.channel): de='Unternehmen' en='Company'
- `display_name` (helpdesk.ticket.channel): de='Anzeigename' en='Display Name'
- `sequence` (helpdesk.ticket.channel): de='Sequenz' en='Sequence'
- `display_name` (helpdesk.ticket.duplicate.wizard): de='Anzeigename' en='Display Name'
- `duplicate_of_id` (helpdesk.ticket.duplicate.wizard): de='Duplicate Of'
- `target_stage_id` (helpdesk.ticket.duplicate.wizard): de='Target Stage'
- `ticket_id` (helpdesk.ticket.duplicate.wizard): de='Ticket'
- `active` (helpdesk.ticket.stage): de='Aktiv' en='Active'
- `close_from_portal` (helpdesk.ticket.stage): de='Close From Portal'
- `closed` (helpdesk.ticket.stage): de='Abgeschlossen' en='Closed'
- `company_id` (helpdesk.ticket.stage): de='Unternehmen' en='Company'
- `description` (helpdesk.ticket.stage): de='Beschreibung' en='Description'
- `display_name` (helpdesk.ticket.stage): de='Anzeigename' en='Display Name'
- `mail_template_id` (helpdesk.ticket.stage): de='E-Mail-Vorlage' en='Email Template'
- `name` (helpdesk.ticket.stage): de='Stufenname' en='Stage Name'
- `sequence` (helpdesk.ticket.stage): de='Sequenz' en='Sequence'
- `team_ids` (helpdesk.ticket.stage): de='Helpdesk Teams'
- `unattended` (helpdesk.ticket.stage): de='Unbeaufsichtigt' en='Unattended'
- `active` (helpdesk.ticket.tag): de='Aktiv' en='Active'
- `color` (helpdesk.ticket.tag): de='Farbindex' en='Color Index'
- `company_id` (helpdesk.ticket.tag): de='Unternehmen' en='Company'
- `display_name` (helpdesk.ticket.tag): de='Anzeigename' en='Display Name'
- `sequence` (helpdesk.ticket.tag): de='Sequenz' en='Sequence'
- `active` (helpdesk.ticket.team): de='Aktiv' en='Active'
- `alias_defaults` (helpdesk.ticket.team): de='Standardwerte' en='Default Values'
- `alias_domain` (helpdesk.ticket.team): de='Alias Domain Name'
- `alias_force_thread_id` (helpdesk.ticket.team): de='Datensatz Thread-ID' en='Record Thread ID'
- `alias_id` (helpdesk.ticket.team): de='E-mail' en='Email'
- `alias_name` (helpdesk.ticket.team): de='Alias Name'
- `alias_status` (helpdesk.ticket.team): de='Alias Status'
- `category_ids` (helpdesk.ticket.team): de='Kategorie' en='Category'
- `color` (helpdesk.ticket.team): de='Farbindex' en='Color Index'
- `company_id` (helpdesk.ticket.team): de='Unternehmen' en='Company'
- `complete_name` (helpdesk.ticket.team): de='Complete Name'
- `display_name` (helpdesk.ticket.team): de='Anzeigename' en='Display Name'
- `message_follower_ids` (helpdesk.ticket.team): de='Followers'
- `message_ids` (helpdesk.ticket.team): de='Nachrichten' en='Messages'
- `message_is_follower` (helpdesk.ticket.team): de='Ist ein Follower' en='Is Follower'
- `message_partner_ids` (helpdesk.ticket.team): de='Followers (Partner)' en='Followers (Partners)'
- `parent_id` (helpdesk.ticket.team): de='Parent Team'
- `rating_ids` (helpdesk.ticket.team): de='Ratings'
- `sequence` (helpdesk.ticket.team): de='Sequenz' en='Sequence'
- `show_in_portal` (helpdesk.ticket.team): de='Show in portal form'
- `ticket_ids` (helpdesk.ticket.team): de='Tickets'
- `todo_ticket_count` (helpdesk.ticket.team): de='Anzahl der Tickets' en='Number of tickets'
- `todo_ticket_count_unassigned` (helpdesk.ticket.team): de='Anzahl der nicht zugewiesenen Tickets' en='Number of tickets unassigned'
- `todo_ticket_count_unattended` (helpdesk.ticket.team): de='Anzahl unbeaufsichtigter Tickets' en='Number of tickets unattended'
- `user_id` (helpdesk.ticket.team): de='Teamleiter' en='Team Leader'
- `user_ids` (helpdesk.ticket.team): de='Mitglieder' en='Members'
- `website_message_ids` (helpdesk.ticket.team): de='Website-Nachrichten' en='Website Messages'
- `helpdesk_mgmt_duplicate_ticket_stage_id` (res.company): de='Move duplicate tickets to this stage'
- `helpdesk_mgmt_duplicate_tracking` (res.company): de='Enable duplicate ticket tracking.'
- `helpdesk_mgmt_portal_category_id_required` (res.company): de='Required Category field in Helpdesk portal'
- `helpdesk_mgmt_portal_select_category` (res.company): de='Select category in Helpdesk portal'
- `helpdesk_mgmt_portal_select_team` (res.company): de='Select team in Helpdesk portal'
- `helpdesk_mgmt_portal_team_id_required` (res.company): de='Required Team field in Helpdesk portal'
- `helpdesk_mgmt_ticket_auto_assign` (res.company): de='Auto assign tickets'
- `helpdesk_mgmt_duplicate_ticket_stage_id` (res.config.settings): de='Move duplicate tickets to this stage'
- `helpdesk_mgmt_duplicate_tracking` (res.config.settings): de='Enable duplicate ticket tracking.'
- `helpdesk_mgmt_portal_category_id_required` (res.config.settings): de='Required Category field in Helpdesk portal'
- `helpdesk_mgmt_portal_select_category` (res.config.settings): de='Select category in Helpdesk portal'
- `helpdesk_mgmt_portal_select_team` (res.config.settings): de='Select team in Helpdesk portal'
- `helpdesk_mgmt_portal_team_id_required` (res.config.settings): de='Required Team field in Helpdesk portal'
- `helpdesk_mgmt_ticket_auto_assign` (res.config.settings): de='Auto assign tickets'
- `helpdesk_ticket_active_count` (res.partner): de='Anzahl aktiver Tickets' en='Ticket active count'
- `helpdesk_ticket_count` (res.partner): de='Anzahl Tickets' en='Ticket count'
- `helpdesk_ticket_count_string` (res.partner): de='Tickets'
- `helpdesk_team_ids` (res.users): de='Helpdesk-Team' en='Helpdesk Team'
- `helpdesk_ticket_active_count` (res.users): de='Anzahl aktiver Tickets' en='Ticket active count'
- `helpdesk_ticket_count` (res.users): de='Anzahl Tickets' en='Ticket count'
- `helpdesk_ticket_count_string` (res.users): de='Tickets'

### helpdesk_mgmt_project
- `milestone_id` (helpdesk.ticket): de='Milestone'
- `project_id` (helpdesk.ticket): de='Project'
- `task_id` (helpdesk.ticket): de='Task'
- `default_project_id` (helpdesk.ticket.team): de='Project'
- `helpdesk_ticket_count` (project.milestone): de='Helpdesk Ticket Count'
- `helpdesk_ticket_ids` (project.milestone): de='Helpdesk Ticket'
- `label_tickets` (project.project): de='Use Tickets as'
- `ticket_count` (project.project): de='Ticket Count'
- `ticket_ids` (project.project): de='Tickets'
- `todo_ticket_count` (project.project): de='Number of tickets'
- `label_tickets` (project.task): de='Use Tickets as'
- `ticket_count` (project.task): de='Ticket Count'
- `ticket_ids` (project.task): de='Tickets'
- `todo_ticket_count` (project.task): de='Number of tickets'

### helpdesk_mgmt_sla
- `activity_calendar_event_id` (helpdesk.sla): de='Next Activity Calendar Event'
- `activity_date_deadline` (helpdesk.sla): de='Next Activity Deadline'
- `activity_exception_decoration` (helpdesk.sla): de='Activity Exception Decoration'
- `activity_ids` (helpdesk.sla): de='Activities'
- `activity_state` (helpdesk.sla): de='Activity State'
- `activity_summary` (helpdesk.sla): de='Next Activity Summary'
- `activity_type_icon` (helpdesk.sla): de='Activity Type Icon'
- `activity_type_id` (helpdesk.sla): de='Next Activity Type'
- `activity_user_id` (helpdesk.sla): de='Responsible User'
- `category_ids` (helpdesk.sla): de='Categories'
- `create_date` (helpdesk.sla): de='Created on'
- `create_uid` (helpdesk.sla): de='Created by'
- `days` (helpdesk.sla): de='Days'
- `display_name` (helpdesk.sla): de='Display Name'
- `domain` (helpdesk.sla): de='Filter'
- `hours` (helpdesk.sla): de='Hours'
- `ignore_stage_ids` (helpdesk.sla): de='Ignore Stages'
- `message_follower_ids` (helpdesk.sla): de='Followers'
- `message_has_error_counter` (helpdesk.sla): de='Number of errors'
- `message_ids` (helpdesk.sla): de='Messages'
- `message_is_follower` (helpdesk.sla): de='Is Follower'
- `message_needaction_counter` (helpdesk.sla): de='Number of Actions'
- `message_partner_ids` (helpdesk.sla): de='Followers (Partners)'
- `my_activity_date_deadline` (helpdesk.sla): de='My Activity Deadline'
- `note` (helpdesk.sla): de='Note'
- `rating_ids` (helpdesk.sla): de='Ratings'
- `stage_id` (helpdesk.sla): de='Stage'
- `team_ids` (helpdesk.sla): de='Teams'
- `website_message_ids` (helpdesk.sla): de='Website Messages'
- `date` (helpdesk.sla.report): de='Date'
- `display_name` (helpdesk.sla.report): de='Display Name'
- `partner_id` (helpdesk.sla.report): de='Contact'
- `state` (helpdesk.sla.report): de='State'
- `team_id` (helpdesk.sla.report): de='Team'
- `ticket_id` (helpdesk.sla.report): de='Ticket'
- `sla_deadline` (helpdesk.ticket): de='SLA deadline'
- `team_sla` (helpdesk.ticket): de='Team SLA'
- `ticket_sla_ids` (helpdesk.ticket): de='Ticket Sla'
- `consumed_time` (helpdesk.ticket.sla): de='Consumed time'
- `create_date` (helpdesk.ticket.sla): de='Created on'
- `create_uid` (helpdesk.ticket.sla): de='Created by'
- `deadline` (helpdesk.ticket.sla): de='Deadline'
- `display_name` (helpdesk.ticket.sla): de='Display Name'
- `expected_stage_id` (helpdesk.ticket.sla): de='Expected Stage'
- `expired` (helpdesk.ticket.sla): de='Expired'
- `hours` (helpdesk.ticket.sla): de='Hours'
- `last_state_date` (helpdesk.ticket.sla): de='Last State Date'
- `sla_id` (helpdesk.ticket.sla): de='Sla'
- `state` (helpdesk.ticket.sla): de='State'
- `ticket_id` (helpdesk.ticket.sla): de='Ticket'
- `resource_calendar_id` (helpdesk.ticket.team): de='Working Hours'

### helpdesk_mgmt_timesheet
- `ticket_id` (account.analytic.line): de='Ticket'
- `ticket_partner_id` (account.analytic.line): de='Ticket partner'
- `allow_timesheet` (helpdesk.ticket): de='Allow Timesheet'
- `last_timesheet_activity` (helpdesk.ticket): de='Last Timesheet Activity'
- `planned_hours` (helpdesk.ticket): de='Planned Hours'
- `progress` (helpdesk.ticket): de='Progress'
- `remaining_hours` (helpdesk.ticket): de='Remaining Hours'
- `show_time_control` (helpdesk.ticket): de='Show Time Control'
- `timesheet_ids` (helpdesk.ticket): de='Timesheet'
- `total_hours` (helpdesk.ticket): de='Total Hours'
- `allow_timesheet` (helpdesk.ticket.team): de='Allow Timesheet'
- `show_timesheet_portal` (helpdesk.ticket.team): de='Show Timesheet Portal'
- `ticket_id` (timesheets.analysis.report): de='Ticket'
- `ticket_partner_id` (timesheets.analysis.report): de='Ticket Partner'

### project_timesheet_time_control
- `date_time` (account.analytic.line): de='Start Time'
- `date_time_end` (account.analytic.line): de='End Time'
- `show_time_control` (account.analytic.line): de='Show Time Control'
- `company_id` (hr.timesheet.switch): de='Unternehmen' en='Company'
- `create_date` (hr.timesheet.switch): de='Created on'
- `create_uid` (hr.timesheet.switch): de='Created by'
- `date_time` (hr.timesheet.switch): de='Start Time'
- `date_time_end` (hr.timesheet.switch): de='End Time'
- `display_name` (hr.timesheet.switch): de='Display Name'
- `name` (hr.timesheet.switch): de='Description'
- `project_id` (hr.timesheet.switch): de='Project'
- `running_timer_duration` (hr.timesheet.switch): de='Previous timer duration'
- `running_timer_id` (hr.timesheet.switch): de='Previous timer'
- `running_timer_start` (hr.timesheet.switch): de='Previous timer start'
- `task_id` (hr.timesheet.switch): de='Task'
- `show_time_control` (hr.timesheet.time_control.mixin): de='Show Time Control'
- `show_time_control` (project.project): de='Show Time Control'
- `show_time_control` (project.task): de='Show Time Control'

### server_action_mass_edit
- `mass_edit_apply_domain_in_lines` (ir.actions.server): de='Filter in Zeilen anwenden' en='Apply domain in lines'
- `mass_edit_message` (ir.actions.server): de='Nachricht' en='Message'
- `state` (ir.actions.server): de='Typ' en='Type'
- `apply_domain` (ir.actions.server.mass.edit.line): de='Filter anwenden' en='Apply Domain'
- `display_name` (ir.actions.server.mass.edit.line): de='Anzeigename' en='Display Name'
- `field_id` (ir.actions.server.mass.edit.line): de='Feld' en='Field'
- `model_id` (ir.actions.server.mass.edit.line): de='Modell' en='Model'
- `sequence` (ir.actions.server.mass.edit.line): de='Sequenz' en='Sequence'
- `server_action_id` (ir.actions.server.mass.edit.line): de='Serveraktion' en='Server Action'
- `mass_edit_apply_domain_in_lines` (ir.cron): de='Filter in Zeilen anwenden' en='Apply domain in lines'
- `mass_edit_message` (ir.cron): de='Nachricht' en='Message'
- `state` (ir.cron): de='Typ' en='Type'
- `display_name` (mass.editing.wizard): de='Anzeigename' en='Display Name'
- `message` (mass.editing.wizard): de='Nachricht' en='Message'

## Sichtbare englische Labels je Fachmodell (fields_get, label de == en)

### crm.lead (3 Kandidaten, nur die auffälligsten)
- - x_Anrede_Lead  'Anrede Lead'                      en='Anrede Lead'                      ENGLISH?
- - x_Lead_Quelle  'Lead Quelle'                      en='Lead Quelle'                      ENGLISH?
- - x_lead_status  'Lead Status'                      en='Lead Status'                      ENGLISH?

### res.partner (8 Kandidaten, nur die auffälligsten)
- - firstname  'First name'                       en='First name'                       ENGLISH?
- - lastname  'Last name'                        en='Last name'                        ENGLISH?
- - status_of_community  'Status of Community'              en='Status of Community'              ENGLISH?
- - member_of_city_alliance  'Member of City Alliance'          en='Member of City Alliance'          ENGLISH?
- - asset_partner  'Asset Partner'                    en='Asset Partner'                    ENGLISH?
- - title_put_in_front  'Title in Front'                   en='Title in Front'                   ENGLISH?
- - title_put_in_back  'Title in Back'                    en='Title in Back'                    ENGLISH?
- - sales_as_final_customer_count  '# of Sales as Final Customer'     en='# of Sales as Final Customer'     ENGLISH?

### res.users (10 Kandidaten, nur die auffälligsten)
- - context_map_website_id  'Map Website'                      en='Map Website'                      ENGLISH?
- - context_route_start_partner_id  'Start Address for Route Map'      en='Start Address for Route Map'      ENGLISH?
- - firstname  'First name'                       en='First name'                       ENGLISH?
- - lastname  'Last name'                        en='Last name'                        ENGLISH?
- - status_of_community  'Status of Community'              en='Status of Community'              ENGLISH?
- - member_of_city_alliance  'Member of City Alliance'          en='Member of City Alliance'          ENGLISH?
- - asset_partner  'Asset Partner'                    en='Asset Partner'                    ENGLISH?
- - title_put_in_front  'Title in Front'                   en='Title in Front'                   ENGLISH?
- - title_put_in_back  'Title in Back'                    en='Title in Back'                    ENGLISH?
- - sales_as_final_customer_count  '# of Sales as Final Customer'     en='# of Sales as Final Customer'     ENGLISH?

### sale.order (7 Kandidaten, nur die auffälligsten)
- - administrative_contact_id  'Administrative Contact'           en='Administrative Contact'           ENGLISH?
- - technical_contact_id  'Technical Contact'                en='Technical Contact'                ENGLISH?
- - product_category_id  'Product Category'                 en='Product Category'                 ENGLISH?
- - final_customer_id  'Final Customer'                   en='Final Customer'                   ENGLISH?
- - sale_contact_id  'Sale Contact'                     en='Sale Contact'                     ENGLISH?
- - subscription_management  'Subscription Management'          en='Subscription Management'          ENGLISH?
- - subscription_count  'Subscription Count'               en='Subscription Count'               ENGLISH?

### sale.subscription (37 Kandidaten, nur die auffälligsten)
- - activity_state  'Activity State'                   en='Activity State'                   ENGLISH?
- - activity_user_id  'Responsible User'                 en='Responsible User'                 ENGLISH?
- - activity_type_id  'Next Activity Type'               en='Next Activity Type'               ENGLISH?
- - activity_type_icon  'Activity Type Icon'               en='Activity Type Icon'               ENGLISH?
- - activity_date_deadline  'Next Activity Deadline'           en='Next Activity Deadline'           ENGLISH?
- - my_activity_date_deadline  'My Activity Deadline'             en='My Activity Deadline'             ENGLISH?
- - activity_summary  'Next Activity Summary'            en='Next Activity Summary'            ENGLISH?
- - message_is_follower  'Is Follower'                      en='Is Follower'                      ENGLISH?
- - message_partner_ids  'Followers (Partners)'             en='Followers (Partners)'             ENGLISH?
- - has_message  'Has Message'                      en='Has Message'                      ENGLISH?
- - message_needaction  'Action Needed'                    en='Action Needed'                    ENGLISH?
- - message_needaction_counter  'Number of Actions'                en='Number of Actions'                ENGLISH?
- - message_has_error  'Message Delivery error'           en='Message Delivery error'           ENGLISH?
- - website_message_ids  'Website Messages'                 en='Website Messages'                 ENGLISH?
- - analytic_account_id  'Analytic Account'                 en='Analytic Account'                 ENGLISH?
- … weitere 22 (siehe Auswerte-Rohdaten, nicht Teil dieses Dokuments)

### sale.subscription.template (18 Kandidaten, nur die auffälligsten)
- - message_is_follower  'Is Follower'                      en='Is Follower'                      ENGLISH?
- - message_partner_ids  'Followers (Partners)'             en='Followers (Partners)'             ENGLISH?
- - has_message  'Has Message'                      en='Has Message'                      ENGLISH?
- - message_needaction  'Action Needed'                    en='Action Needed'                    ENGLISH?
- - message_needaction_counter  'Number of Actions'                en='Number of Actions'                ENGLISH?
- - message_has_error  'Message Delivery error'           en='Message Delivery error'           ENGLISH?
- - website_message_ids  'Website Messages'                 en='Website Messages'                 ENGLISH?
- - description  'Terms and Conditions'             en='Terms and Conditions'             ENGLISH?
- - user_closable  'Closable by customer'             en='Closable by customer'             ENGLISH?
- - payment_mandatory  'Automatic Payment'                en='Automatic Payment'                ENGLISH?
- - journal_id  'Accounting Journal'               en='Accounting Journal'               ENGLISH?
- - product_count  'Product Count'                    en='Product Count'                    ENGLISH?
- - subscription_count  'Subscription Count'               en='Subscription Count'               ENGLISH?
- - contract_termination_period_number  'Notice Period'                    en='Notice Period'                    ENGLISH?
- - noticeperiod  'Notice Period'                    en='Notice Period'                    ENGLISH?
- … weitere 3 (siehe Auswerte-Rohdaten, nicht Teil dieses Dokuments)

### product.template (4 Kandidaten, nur die auffälligsten)
- - website_message_ids  'Website Messages'                 en='Website Messages'                 ENGLISH?
- - recurring_invoice  'Subscription Product'             en='Subscription Product'             ENGLISH?
- - subscription_template_id  'Subscription Template'            en='Subscription Template'            ENGLISH?
- - to_multiply_by_factor  'To multiply by Factor(thsd)'      en='To multiply by Factor(thsd)'      ENGLISH?

### product.category (1 Kandidaten, nur die auffälligsten)
- - website_message_ids  'Website Messages'                 en='Website Messages'                 ENGLISH?

### product.pricelist (1 Kandidaten, nur die auffälligsten)
- - website_message_ids  'Website Messages'                 en='Website Messages'                 ENGLISH?

### account.move (3 Kandidaten, nur die auffälligsten)
- - projectcategory_id  'Project Category'                 en='Project Category'                 ENGLISH?
- - sale_order_benefit_period  'Benefit Period'                   en='Benefit Period'                   ENGLISH?
- - notice  'Invoice Note'                     en='Invoice Note'                     ENGLISH?

### helpdesk.ticket (15 Kandidaten, nur die auffälligsten)
- - duration_tracking  'Status time'                      en='Status time'                      ENGLISH?
- - commercial_partner_id  'Commercial Partner'               en='Commercial Partner'               ENGLISH?
- - duplicate_id  'Duplicate of'                     en='Duplicate of'                     ENGLISH?
- - duplicate_ids  'Duplicate tickets'                en='Duplicate tickets'                ENGLISH?
- - duplicate_count  'Duplicate Count'                  en='Duplicate Count'                  ENGLISH?
- - duplicate_tracking_enabled  'Enable duplicate ticket tracking.' en='Enable duplicate ticket tracking.' ENGLISH?
- - team_sla  'Team SLA'                         en='Team SLA'                         ENGLISH?
- - ticket_sla_ids  'Ticket Sla'                       en='Ticket Sla'                       ENGLISH?
- - sla_deadline  'SLA deadline'                     en='SLA deadline'                     ENGLISH?
- - allow_timesheet  'Allow Timesheet'                  en='Allow Timesheet'                  ENGLISH?
- - planned_hours  'Planned Hours'                    en='Planned Hours'                    ENGLISH?
- - remaining_hours  'Remaining Hours'                  en='Remaining Hours'                  ENGLISH?
- - total_hours  'Total Hours'                      en='Total Hours'                      ENGLISH?
- - last_timesheet_activity  'Last Timesheet Activity'          en='Last Timesheet Activity'          ENGLISH?
- - support_comment  'Partner Kommentar'                en='Partner Kommentar'                ENGLISH?

### helpdesk.ticket.stage (2 Kandidaten, nur die auffälligsten)
- - close_from_portal  'Close From Portal'                en='Close From Portal'                ENGLISH?
- - team_ids  'Helpdesk Teams'                   en='Helpdesk Teams'                   ENGLISH?

### helpdesk.ticket.team (7 Kandidaten, nur die auffälligsten)
- - show_in_portal  'Show in portal form'              en='Show in portal form'              ENGLISH?
- - parent_id  'Parent Team'                      en='Parent Team'                      ENGLISH?
- - complete_name  'Complete Name'                    en='Complete Name'                    ENGLISH?
- - parent_path  'Parent Path'                      en='Parent Path'                      ENGLISH?
- - resource_calendar_id  'Working Hours'                    en='Working Hours'                    ENGLISH?
- - allow_timesheet  'Allow Timesheet'                  en='Allow Timesheet'                  ENGLISH?
- - show_timesheet_portal  'Show Timesheet Portal'            en='Show Timesheet Portal'            ENGLISH?

### helpdesk.ticket.category (6 Kandidaten, nur die auffälligsten)
- - parent_id  'Parent Category'                  en='Parent Category'                  ENGLISH?
- - child_id  'Child Categories'                 en='Child Categories'                 ENGLISH?
- - parent_path  'Parent Path'                      en='Parent Path'                      ENGLISH?
- - complete_name  'Complete Name'                    en='Complete Name'                    ENGLISH?
- - show_in_portal  'Show In Portal'                   en='Show In Portal'                   ENGLISH?
- - user_ids  'Assigned Users'                   en='Assigned Users'                   ENGLISH?

### helpdesk.sla (18 Kandidaten, nur die auffälligsten)
- - activity_state  'Activity State'                   en='Activity State'                   ENGLISH?
- - activity_user_id  'Responsible User'                 en='Responsible User'                 ENGLISH?
- - activity_type_id  'Next Activity Type'               en='Next Activity Type'               ENGLISH?
- - activity_type_icon  'Activity Type Icon'               en='Activity Type Icon'               ENGLISH?
- - activity_date_deadline  'Next Activity Deadline'           en='Next Activity Deadline'           ENGLISH?
- - my_activity_date_deadline  'My Activity Deadline'             en='My Activity Deadline'             ENGLISH?
- - activity_summary  'Next Activity Summary'            en='Next Activity Summary'            ENGLISH?
- - message_is_follower  'Is Follower'                      en='Is Follower'                      ENGLISH?
- - message_partner_ids  'Followers (Partners)'             en='Followers (Partners)'             ENGLISH?
- - has_message  'Has Message'                      en='Has Message'                      ENGLISH?
- - message_needaction  'Action Needed'                    en='Action Needed'                    ENGLISH?
- - message_needaction_counter  'Number of Actions'                en='Number of Actions'                ENGLISH?
- - message_has_error  'Message Delivery error'           en='Message Delivery error'           ENGLISH?
- - website_message_ids  'Website Messages'                 en='Website Messages'                 ENGLISH?
- - ignore_stage_ids  'Ignore Stages'                    en='Ignore Stages'                    ENGLISH?
- … weitere 3 (siehe Auswerte-Rohdaten, nicht Teil dieses Dokuments)

### project.project (15 Kandidaten, nur die auffälligsten)
- - is_favorite  'Show Project on Dashboard'        en='Show Project on Dashboard'        ENGLISH?
- - resource_calendar_id  'Working Time'                     en='Working Time'                     ENGLISH?
- - type_ids  'Tasks Stages'                     en='Tasks Stages'                     ENGLISH?
- - task_count  'Task Count'                       en='Task Count'                       ENGLISH?
- - open_task_count  'Open Task Count'                  en='Open Task Count'                  ENGLISH?
- - closed_task_count  'Closed Task Count'                en='Closed Task Count'                ENGLISH?
- - ticket_count  'Ticket Count'                     en='Ticket Count'                     ENGLISH?
- - todo_ticket_count  'Number of tickets'                en='Number of tickets'                ENGLISH?
- - analytic_account_active  'Active Account'                   en='Active Account'                   ENGLISH?
- - timesheet_ids  'Associated Timesheets'            en='Associated Timesheets'            ENGLISH?
- - total_timesheet_time  'Total number of time (in the proper UoM) recorded in the project, rounded to the unit.' en='Total number of time (in the proper UoM) recorded in the project, rounded to the unit.' ENGLISH?
- - encode_uom_in_days  'Encode Uom In Days'               en='Encode Uom In Days'               ENGLISH?
- - is_internal_project  'Is Internal Project'              en='Is Internal Project'              ENGLISH?
- - is_project_overtime  'Project in Overtime'              en='Project in Overtime'              ENGLISH?
- - purchase_orders_count  '# Purchase Orders'                en='# Purchase Orders'                ENGLISH?

### project.task (15 Kandidaten, nur die auffälligsten)
- - website_message_ids  'Website Messages'                 en='Website Messages'                 ENGLISH?
- - display_in_project  'Display In Project'               en='Display In Project'               ENGLISH?
- - portal_user_names  'Portal User Names'                en='Portal User Names'                ENGLISH?
- - personal_stage_type_ids  'Personal Stages'                  en='Personal Stages'                  ENGLISH?
- - allow_task_dependencies  'Task Dependencies'                en='Task Dependencies'                ENGLISH?
- - display_parent_task_button  'Display Parent Task Button'       en='Display Parent Task Button'       ENGLISH?
- - current_user_same_company_partner  'Current User Same Company Partner' en='Current User Same Company Partner' ENGLISH?
- - display_follow_button  'Display Follow Button'            en='Display Follow Button'            ENGLISH?
- - link_preview_name  'Link Preview Name'                en='Link Preview Name'                ENGLISH?
- - ticket_count  'Ticket Count'                     en='Ticket Count'                     ENGLISH?
- - todo_ticket_count  'Number of tickets'                en='Number of tickets'                ENGLISH?
- - analytic_account_active  'Active Analytic Account'          en='Active Analytic Account'          ENGLISH?
- - allow_timesheets  'Allow timesheets'                 en='Allow timesheets'                 ENGLISH?
- - encode_uom_in_days  'Encode Uom In Days'               en='Encode Uom In Days'               ENGLISH?
- - is_timeoff_task  'Is Time off Task'                 en='Is Time off Task'                 ENGLISH?

### hr.employee (1 Kandidaten, nur die auffälligsten)
- - has_timesheet  'Has Timesheet'                    en='Has Timesheet'                    ENGLISH?

## Sichtbare Status-/Kategorie-/Typnamen (Daten, de_DE)

- **crm_stage:** FEHLER RPC-Fehler: Odoo Server Error
- **helpdesk_stage:** FEHLER RPC-Fehler: Odoo Server Error
- **activity_type:** FEHLER RPC-Fehler: Odoo Server Error

## Mojibake in sichtbaren de_DE-Übersetzungen (Encoding-Befunde, NUR dokumentiert)

Ergänzend zu F1/F7 (res_currency.symbol, ir_module_module.shortdesc) wurden in sichtbaren
Übersetzungen weitere CP850-Artefakte gefunden — **nicht angefasst** (Encoding gilt als
abgeschlossen, 13.08.2026; jede Korrektur nur mit Freigabe):
- `account.move.status_in_payment` (Feldlabel de_DE): `Status ÔÇ×In ZahlungÔÇ£` (statt „Status „In Zahlung““)
- `account.reconcile.model.line.show_force_tax_included` (Feldlabel de_DE): `ÔÇ×Steuer inklusive erzwingenÔÇ£ anzeigen`
- `res.partner.peppol_eas` Auswahlwert `0245` (de_DE): `SK-Steueridentifikationsnummer (DI─î)` — in res.users/res.company über Delegation sichtbar

## Hinweise Datenqualität (Helpdesk-Kategorien, read-only)

- 37 Kategorien: Fachnamen deutsch; Duplikat-Namen sichtbar (z. B. ‚Allgemeine Anfrage (Support)‘ mehrfach, ‚Störung/Fehler melden‘ mehrfach, ‚allgemeiner Support‘ 2×, ‚Zugangsdaten vergessen‘ 2×). Ursache prüfen (2-stufige Kategorien/verschiedene Eltern?), KEINE Änderung.
- Kategorie ‚Anynomisierungsportal‘: sichtbarer Tippfehler (vermutlich ‚Anonymisierungsportal‘).
- Hilfe-Desk-Stages: ‚on Hold‘ (englisch) neben deutschen Stufen; CRM-Stage ‚On-Hold‘ (englisch).

