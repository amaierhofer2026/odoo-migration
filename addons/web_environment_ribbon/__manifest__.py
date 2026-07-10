{
    'name': "Web Environment Ribbon",
    'version': '18.0.1.0.0',
    'category': 'Web',
    'author': 'Francesco OpenCode Apruzzese, '
              'Tecnativa, '
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/web',
    'license': 'AGPL-3',
    "depends": [
        'web',
    ],
    "data": [
        'data/ribbon_data.xml',
    ],
    "assets": {
        'web.assets_backend': [
            'web_environment_ribbon/static/src/css/ribbon.css',
            'web_environment_ribbon/static/src/js/ribbon.js',
        ],
    },
    "auto_install": False,
    'installable': True,
    'application': False,
}
