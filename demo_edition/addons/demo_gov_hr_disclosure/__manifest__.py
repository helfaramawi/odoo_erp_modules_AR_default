{
    'name': 'إقرار الذمة المالية',
    'summary': 'C-02: Financial disclosure at appointment + automatic 6-year renewal, with 30-day expiry alerts',
    'version': '17.0.1.0.0',
    'category': 'الخدمات الحكومية التجريبية/الموارد البشرية',
    'author': 'Enterprise Solutions Demo',
    'license': 'LGPL-3',
    'depends': ['demo_gov_hr_employee', 'demo_gov_hr_training'],
    'data': [
        'security/ir.model.access.csv',
        'data/cron_data.xml',
        'views/hr_disclosure_views.xml',
        'views/hr_disclosure_menu.xml',
    ],
    'installable': True,
    'application': False,
}
