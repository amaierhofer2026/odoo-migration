{
    'name': 'ITK Abrechnung - Migrationsfelder',
    'version': '18.0.1.18.0',
    'summary': 'Felder zur Nachvollziehbarkeit der Odoo-11-Herkunft (Rechnungs- und Zahlungsnummer)',
    'description': """
ITK Abrechnung - Migrationsfelder
================================
Ergaenzt Felder, die ausschliesslich der historischen Nachvollziehbarkeit der Odoo-11-Daten
dienen (Entscheidung K2a und Zahlungsnummern-Regel, Bereich Abrechnung):

* account.move.itk_o11_invoice_number   - Odoo-11-Rechnungsnummer (read-only im normalen Betrieb)
* account.payment.itk_o11_payment_number - Odoo-11-Zahlungsnummer (read-only im normalen Betrieb)

Die Felder werden bei der spaeteren Migration befuellt; die laufende Odoo-18-Nummerierung
(account.move.name) und die Odoo-18-Sequenzen bleiben unveraendert.
""",
    'author': 'IT Kommunal',
    'license': 'LGPL-3',
    'depends': ['account', 'itk_projectcategory', 'itk_subscription', 'itk_valorisierung',
                'itk_product'],
    'assets': {
        'web.assets_backend': [
            'itk_account_migration/static/src/xml/itk_tax_totals.xml',
        ],
    },
    'data': [
        'views/account_move_views.xml',
        'views/account_move_pc_spalte.xml',
        'views/account_move_filters.xml',
        'views/account_payment_views.xml',
        'views/account_config_labels.xml',
        'views/account_form_texte.xml',
        'views/account_form_erweiterung.xml',
        'views/account_move_line_labels.xml',
        'views/account_move_line_columns.xml',
        'views/account_move_form_kopf.xml',
        'views/partner_product_labels.xml',
        'views/product_template_form_o11.xml',
        'views/product_template_list_o11.xml',
        'views/config_sichtbarkeit.xml',
        'views/suchansichten.xml',
    ],
    'installable': True,
    'application': False,
}
