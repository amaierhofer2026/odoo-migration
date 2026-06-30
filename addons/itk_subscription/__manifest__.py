{
    'name': 'ITK Abo-Management',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Management of Abos',
    'description': """
This module allows you to manage Abos.

Features:
    - Create & edit abos
    - Modify abos with sales orders
    - Generate invoice automatically at fixed intervals
""",
    'author': "Alvarium Services, Andreas Väthröder, Fabian Väthröder",
    'website': "http://www.alvarium-services.de",
    'depends': [
        'sale',
        'portal',
        'account',
        'analytic',
    ],
    'data': [
        'security/sale_subscription_security.xml',
        'security/ir.model.access.csv',
        'wizard/sale_subscription_close_reason_wizard_views.xml',
        'wizard/sale_subscription_wizard_views.xml',
        # 'views/product_template_views.xml',
        'views/res_partner_views.xml',
        'views/account_analytic_account_views.xml',
        'views/sale_subscription_views.xml',
        'views/subscription_portal_templates.xml',
        'views/res_config_settings_views.xml',
        'views/payment_views.xml',
        'views/account_invoice_views.xml',
        'views/sale_order_views.xml',
        'data/sale_subscription_data.xml',
        'data/mail_template_data.xml',
        'report/sale_subscription_report_view.xml',
        'data/itk_noticeperiod.xml',
        'data/itk_sale_subscription_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'itk_subscription/static/src/js/tour.js',
            'itk_subscription/static/src/css/sale_subscription_backend.less',
        ],
        'web.assets_frontend': [
            'itk_subscription/static/src/less/portal_subscription.less',
            'itk_subscription/static/src/js/portal_subscription.js',
        ],
    },
    'demo': [
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
