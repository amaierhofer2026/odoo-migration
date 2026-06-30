{
    'name': "itk_product",
    'version': '18.0.1.0.0',
    'category': 'Uncategorized',
    'summary': 'ITK Product extensions',
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'depends': ['base', 'product',
                'itk_subscription',
                ],
    'data': [
        'security/ir.model.access.csv',
        'views/itk_product.xml',
    ],
    'demo': [
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
