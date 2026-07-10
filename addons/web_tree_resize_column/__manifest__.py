{
    'name': 'Resize Columns',
    'summary': 'Resize columns in tree views',
    'category': 'Extra Tools',
    'version': '18.0.1.0.0',
    'author': 'Onestein, Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'website': 'https://github.com/OCA/web',
    'depends': [
        'web'
    ],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'web_tree_resize_column/static/src/js/backend.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
