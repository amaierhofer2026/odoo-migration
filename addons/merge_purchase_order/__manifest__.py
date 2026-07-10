{
    'name': 'Merge Purchase Order',
    'category': 'Purchase',
    'summary': 'This module will merge purchase order.',
    'version': '18.0.1.0.0',
    'website': 'http://www.aktivsoftware.com',
    'author': 'Aktiv Software',
    'description': 'Merge Purchase Order',
    'license': "AGPL-3",

    'depends': [
        'purchase',
    ],

    'data': [
        'security/ir.model.access.csv',
        'wizard/merge_purchase_order_wizard_view.xml',
    ],

    'images': [
        'static/description/banner.jpg',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
}
