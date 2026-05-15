{
    'name': 'استمارة 50 ع.ح — طباعة على الاستمارة الرسمية',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Egypt Government',
    'summary': 'طباعة دفتر 55 على خلفية استمارة 50 ع.ح الرسمية مع تحديد مواضع الحقول بدقة',
    'author': 'Paradise Integrated Solutions',
    'license': 'LGPL-3',
    'depends': ['port_said_daftar55', 'port_said_dossier'],
    'data': [
        'security/ir.model.access.csv',
        'reports/form50_report.xml',
        'reports/form50_template.xml',
    ],
    'installable': True,
    'application': False,
}
