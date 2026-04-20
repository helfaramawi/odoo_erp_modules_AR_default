{
    'name': 'دفتر 224 ع.ح — السجل اليومي المزدوج',
    'summary': 'C-FM-02: Daftar 224 Dual Daily Register (صرفيات + تسويات)',
    'version': '17.0.1.0.0',
    'category': 'Accounting',
    'author': 'Paradise Integrated Solutions',
    'license': 'LGPL-3',
    'depends': ['account', 'mail', 'port_said_daftar55'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/daftar224_views.xml',
        'reports/daftar224_report.xml',
        'reports/daftar224_template.xml',
    ],
    'installable': True,
}
