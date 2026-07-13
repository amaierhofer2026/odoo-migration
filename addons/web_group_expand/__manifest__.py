{
    "name": "Group Expand Buttons",
    "summary": "Enables expanding/reset all groups in list view",
    "version": "18.0.1.0.0",
    "category": "Web",
    "author": "OpenERP SA, "
              "AvanzOSC, "
              "Tecnativa, "
              "Odoo Community Association (OCA)",
    "website": "https://github.com/oca/web",
    "license": "AGPL-3",
    "depends": [
        "web"
    ],
    "assets": {
        "web.assets_backend": [
            "web_group_expand/static/src/less/web_group_expand.less",
            "web_group_expand/static/src/js/web_group_expand_menu.js",
            "web_group_expand/static/src/js/web_group_expand.js",
            "web_group_expand/static/src/xml/web_group_expand.xml",
        ]
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
