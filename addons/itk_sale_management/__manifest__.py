{
    'name': "itk_sale_management",
    'summary': "ITK Sale Management extensions",
    'description': "Adds administrative/technical contacts, product category, and final customer to sale orders.",
    'author': "Alvarium Services, Andreas Väthröder, Fabian Väthröder",
    'website': "http://www.alvarium-services.de",
    'category': 'ITK - Specific Industry Applications',
    'version': '18.0.1.0.0',
    'depends': ['base', 'sale'],
    'data': [
        'views/views.xml',
        'views/templates.xml',
        'views/sale_order.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
