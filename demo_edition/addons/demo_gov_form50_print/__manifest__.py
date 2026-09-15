{
    'name': 'استمارة 50 ع.ح - طبقة الطباعة الرسمية',
    'summary': 'C-FM-01-P: Form 50 official print layer — invoice lines, print readiness, image-overlay report',
    'version': '17.0.1.0.0',
    'category': 'الخدمات الحكومية التجريبية/الحسابات',
    'author': 'Enterprise Solutions Demo',
    'website': 'https://example.com',
    'license': 'LGPL-3',
    'depends': ['demo_gov_daftar55', 'demo_gov_dossier', 'account', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/daftar55_form50_views.xml',
        'views/form50_reprint_wizard_views.xml',
        'reports/form50_report.xml',
        'reports/form50_template.xml',
    ],
    'installable': True,
    'application': False,
}
