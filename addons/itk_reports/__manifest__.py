{
    'name': "itk_reports",

    'summary': "ITK-spezifische Druckvorlagen (Angebot/Auftrag, Bestellung, Bestellanfrage, Rechnung)",

    'description': """
ITK-Reports
===========
Angepasste QWeb-PDF-Druckvorlagen mit ITK-Briefkopf und -Fußzeile für:
- Angebot / Auftrag (sale.order)
- Bestellung (purchase.order)
- Bestellanfrage (purchase.order)
- Rechnung (account.move)
""",

    'author': "Alvarium Services, Andreas Väthröder, Fabian Väthröder",
    'website': "http://www.alvarium-services.de",

    'category': 'ITK - Specific Industry Applications',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'sale',
        'purchase',
        'account',
        'account_invoice_line_number',
        'sale_order_line_number',
        'itk_sale_management',
        'itk_valorisierung',
    ],

    # always loaded
    'data': [
        'reports/itk_report_actions.xml',
        'reports/itk_report_saleorder.xml',
        'reports/itk_report_purchaseorder.xml',
        'reports/itk_report_purchasequotation.xml',
        'reports/itk_report_invoice.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
}
