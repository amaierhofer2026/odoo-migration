{
    "name": "ITK Helpdesk Compatibility",
    "summary": "Restores Odoo 11 helpdesk UI, menus, and workflows in Odoo 18",
    "version": "18.0.1.0.0",
    "license": "LGPL-3",
    "category": "Helpdesk",
    "author": "IT-Kommunal GmbH",
    "website": "https://www.it-kommunal.at",
    "depends": [
        "helpdesk_mgmt",
        "itk_helpdesk_category_user",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/helpdesk_ticket_category_views.xml",
        "views/helpdesk_priority_views.xml",
        "views/helpdesk_subcategory_field_views.xml",
        "views/helpdesk_ticket_views.xml",
        "views/helpdesk_stage_views.xml",
        "views/menus.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "itk_helpdesk_compat/static/src/js/portal_category_filter.esm.js",
        ],
    },
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
    "auto_install": False,
}
