{
    'name': 'الاضابير - نظام الأرشفة (استمارة 101 ساير)',
    'category': 'الخدمات الحكومية التجريبية/الحسابات',
    'summary': 'C-FM-08: Dossier Archive System – Form 101 ساير with 9-attachment enforcement',
    'version': '17.0.1.0.0',
    'author': 'Enterprise Solutions Demo',
    'license': 'LGPL-3',
    'depends': ['demo_gov_daftar55'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/dossier_views.xml',
        'views/daftar55_dossier_button_views.xml',
        'reports/dossier_report.xml',
        'reports/dossier_template.xml',
    ],
    'installable': True,
}
