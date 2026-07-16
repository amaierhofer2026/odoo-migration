# -*- coding: utf-8 -*-
{
    'name': "itk_initial_data_ha_basis_GSZK_import",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Alvarium Services, Andreas Väthröder, Fabian Väthröder",
    'website': "http://www.alvarium-services.de",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'ITK - Specific Industry Applications',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'itk_initial_data_import',
                ],


    # always loaded
    'data': [
        'data/itk_gszk_customers_and_pricelist.xml',  # set partners as gszk customers
        'data/itk_gszk_product_products.xml',   # set gszk products
        'data/itk_gszk_abo_auftrag_ha.xml',  # create gszk saleorders
        'data/itk_gszk_abo_vertrag_ha.xml',  # create gszk contracts
        'data/connect_gszk_contracts_orders_ha.xml',  # connect gszk contracts and orders

    ],
    # only loaded in demonstration mode
    # 'demo': [
    #   'demo/demo.xml',
    # ],
    'installable': False,
}
