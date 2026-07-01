{
    'name': "itk_valorisierung",
    'summary': "Valorisierung",
    'description': "ITK Valorisierungstexte",
    'author': "Alvarium Services, Andreas Väthröder, Fabian Väthröder",
    'website': "alvarium-services.de",
    'category': 'ITK - Specific Industry Applications',
    'version': '18.0.1.0.0',
    'depends': ['base', 'account', 'itk_subscription'],
    'data': [
        'views/valorisierung_views.xml',
        'views/account_invoice_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
