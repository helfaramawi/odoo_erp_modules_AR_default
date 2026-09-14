{
    'name': 'استمارة 75 - الحسابات الشهرية والختامية',
    'category': 'الخدمات الحكومية التجريبية/الحسابات',
    'summary': 'C-FM-04: Form 75 Monthly/Annual Closing with 3-Stage Sequential Approval',
    'version': '17.0.1.0.0',
    'author': 'Enterprise Solutions Demo',
    'license': 'LGPL-3',
    'depends': ['demo_gov_form69', 'mail', 'demo_branding'],
    'data': [
        'security/ir.model.access.csv',
        'views/form75_views.xml',
        'reports/form75_report.xml',
        'reports/form75_template.xml',
    ],
    'installable': True,
}
