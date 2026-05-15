{
<<<<<<< HEAD
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
        'data/paperformat.xml',
        'data/sequence_data.xml',
        'wizard/reprint_wizard_views.xml',
        'views/form50_print_views.xml',
        'views/form50_views.xml',
        'views/form50_menu.xml',
        'reports/form50_report_actions.xml',
        'reports/form50_preview_template.xml',
        'reports/form50_final_template.xml',
=======
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
>>>>>>> 1da0b02963efdf00571f36e5c3c19f784f02f26e
    ],
    'installable': True,
    'application': False,
}
