# -*- coding: utf-8 -*-
{
    'name': "itk_third_party_setup",

    'summary': """
        ITK third party setup. Installs all modules used by ITK and delivered 
        - by the odoo-app-Store 
        - by OCA (OCA-Github)
        """,

    'description': """
        ITK third party setup. Installs all modules used by ITK and delivered 
        - by the odoo-app-Store 
        - by OCA (OCA-Github)
        
        Modules ar located in addon-directory /itk
    """,

    'author': "Alvarium Services, Andreas Väthröder, Fabian Väthröder",
    'website': "http://www.alvarium-services.de",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'ITK - Specific Industry Applications',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'itk_base_setup',
        'mass_editing',
        'mass_email_invoice',
        'web_sheet_full_width',
        'hr_employee_firstname',
        # 'contract',
        'website_support',
        'website_support_analytic_timesheets',
        'website_support_billing',
        'account_invoice_line_number',
        #'sale_order_line_number',
        'purchase_order_line_number',
        'partner_academic_title',
        'bi_crm_claim',
        'web_tree_resize_column',
        'web_tree_resize_column',
        # 'web_listview_sticky_header',
        'web_no_bubble',
                ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        #    'demo/demo.xml',
    ],
    'installable': False,
}
