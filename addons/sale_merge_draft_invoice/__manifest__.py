{
    "name": "Sale Merge Draft Invoice",
    "author": "Eficent, Odoo Community Association (OCA)",
    "version": "18.0.1.0.0",
    "category": "Sale Workflow",
    "website": "https://github.com/OCA/sale-workflow",
    "depends": [
        'sale',
    ],
    "data": [
        'security/sale_merge_draft_invoice_security.xml',
        'wizard/sale_make_invoice_advance_views.xml',
        'view/res_config_settings_views.xml',
    ],
    "license": 'LGPL-3',
    "installable": True,
    "application": False,
    "auto_install": False,
}
