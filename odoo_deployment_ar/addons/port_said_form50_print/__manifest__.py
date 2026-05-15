{
    'name': 'استمارة 50 ع.ح — طبقة الطباعة الرسمية',
    'summary': 'C-FM-01-P: Form 50 Official Print Layer for Daftar 55',
    'version': '17.0.1.0.0',
    'category': 'Accounting',
    'author': 'Paradise Integrated Solutions',
    'license': 'LGPL-3',
    'depends': [
        'port_said_daftar55',
        'port_said_dossier',
    ],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'wizard/reprint_wizard_views.xml',
        'reports/form50_report_actions.xml',
        'reports/form50_preview_template.xml',
        'reports/form50_final_template.xml',
        'views/form50_views.xml',
    ],
    'installable': True,
    'application': False,
}
