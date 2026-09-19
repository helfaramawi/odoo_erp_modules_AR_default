{
    'name': 'تقييم الأداء الحكومي — كفاءة وتظلمات',
    'summary': 'C-HR-05: Annual performance appraisal with government rating scale, incentive allowance, grievance workflow (employee → committee → union)',
    'version': '17.0.1.0.0',
    'category': 'الخدمات الحكومية التجريبية/الموارد البشرية',
    'author': 'Enterprise Solutions Demo',
    'license': 'LGPL-3',
    'depends': ['demo_gov_hr_employee', 'demo_gov_hr_training'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/hr_performance_grievance_views.xml',
        'views/hr_performance_appraisal_views.xml',
        'views/hr_performance_menu.xml',
    ],
    'installable': True,
    'application': False,
}
