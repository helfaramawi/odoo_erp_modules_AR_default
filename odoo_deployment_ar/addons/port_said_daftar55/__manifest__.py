{
    'name': 'دفتر 55 - سجل المدفوعات المتسلسل',
    'summary': 'C-FM-01: Daftar 55 Sequential Payment Register – Port Said Governorate',
    'version': '17.0.1.0.0',
    'category': 'Accounting',
    'author': 'Paradise Integrated Solutions',
    'website': 'https://paradise.solutions.com',
    'license': 'LGPL-3',
    'depends': ['account', 'base', 'mail', 'port_said_menu'],
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
