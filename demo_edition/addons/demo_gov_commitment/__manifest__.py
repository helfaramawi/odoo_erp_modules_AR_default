{
    'name': 'الارتباطات والتسميح - رقابة الموازنة',
    'category': 'الخدمات الحكومية التجريبية/الحسابات',
    'summary': 'C-FM-06: Budget Commitment & Clearance (ارتباط → تجنيب → تسميح)',
    'version': '17.0.1.0.0',
    'author': 'Enterprise Solutions Demo',
    'license': 'LGPL-3',
    'depends': ['mail', 'demo_gov_daftar55', 'demo_branding'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/commitment_views.xml',
        'views/menu.xml',
        'reports/commitment_report.xml',
        'reports/commitment_template.xml',
    ],
    'installable': True,
}
