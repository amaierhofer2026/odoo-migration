# -*- coding: utf-8 -*-
{
    'name': "itk_initial_product_import",

    'summary': """
        Initial ITK product import""",

    'description': """
        Initial ITK product import
    """,

    'author': "Alvarium Services, Andreas Väthröder, Fabian Väthröder",
    'website': "http://www.alvarium-services.de",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'ITK - Specific Industry Applications',
    'version': '0.1',

    # any module necessary for this one to work correctly

    'depends': ['base', 'product',

                ],

    # always loaded
    'data': [
        'data/itk_product_uom.xml',
        'data/itk_product_category.xml',
        'data/itk_product_type.xml',
        # 'data/itk_projectcategory.xml',
        'data/itk_product_products.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #   'demo/demo.xml',
    # ],
    'installable': False,
}
