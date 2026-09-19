{
    'name': 'الخدمة العامة — خريجات بدون راتب',
    'summary': 'C-04: Public Service worker type — one-year unpaid assignment for female graduates, outside Payroll, with automatic expiry',
    'version': '17.0.1.0.0',
    'category': 'الخدمات الحكومية التجريبية/الموارد البشرية',
    'author': 'Enterprise Solutions Demo',
    'license': 'LGPL-3',
    'depends': ['demo_gov_hr_employee', 'demo_gov_hr_training'],
    'data': [
        'data/cron_data.xml',
        'views/hr_employee_views_inherit.xml',
        'views/hr_public_service_menu.xml',
        'reports/public_service_reports.xml',
        'reports/public_service_template.xml',
    ],
    'installable': True,
    'application': False,
}
