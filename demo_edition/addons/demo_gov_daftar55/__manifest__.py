{
    'name': 'دفتر 55 - سجل المدفوعات المتسلسل',
    'summary': 'C-FM-01: Daftar 55 Sequential Payment Register – Demo Governorate',
    'version': '17.0.1.0.0',
    'category': 'Accounting',
    'author': 'Enterprise Solutions Demo',
    'website': 'https://example.com',
    'license': 'LGPL-3',
    'depends': ['account', 'base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/daftar55_views.xml',
        'reports/daftar55_report.xml',
        'reports/daftar55_template.xml',
    ],
    'installable': True,
    'application': False,
}
