{
    "name": "Show sheets with full width",
    "version": "18.0.1.0.0",
    "author": "Therp BV, Sudokeys, GRAP, Métal Sartigan, "
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "summary": "Use the whole available screen width when displaying sheets",
    "category": "Tools",
    "depends": [
        'web',
    ],
    "data": [],
    "assets": {
        'web.assets_backend': [
            'web_sheet_full_width/static/src/css/web_sheet_full_width.css',
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
