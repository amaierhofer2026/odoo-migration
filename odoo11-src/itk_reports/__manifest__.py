# -*- coding: utf-8 -*-
{
    'name': "itk_reports",

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
    'version': '0.4',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account_invoice_line_number', 'sale_order_line_number', 'itk_sale_management', 'sale',
                'itk_valorisierung',
                ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'reports/itk_report_actions.xml',
        'reports/itk_report_invoice.xml',
        'reports/itk_report_saleorder.xml',
        'reports/itk_report_purchasequotation.xml',
        'reports/itk_report_purchaseorder.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
