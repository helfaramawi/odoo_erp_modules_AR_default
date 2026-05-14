{
    'name': 'Financial Dimensions Engine / محرك الأبعاد المالية',
    'version': '17.0.1.0.0',
    'category': 'الديوان العام/المحاسبة',
    'summary': 'Department / Project / Region dimensions on every journal entry line',
    'author': 'ERP Migration Team',
    'depends': ['account', 'analytic'],
    'data': [
        'security/ir.model.access.csv',
        'data/dimension_data.xml',
        'views/dimension_views.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}