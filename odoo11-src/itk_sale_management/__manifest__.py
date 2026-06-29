# -*- coding: utf-8 -*-
{
    'name': "itk_sale_management",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of 
    """,

    'author': "Alvarium Services, Andreas Väthröder, Fabian Väthröder",
    'website': "http://www.alvarium-services.de",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'ITK - Specific Industry Applications',
    'version': '0.2',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', #'sale_order_price_recalculation'
             ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml' ,
        'views/templates.xml',
        'views/sale_order.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
