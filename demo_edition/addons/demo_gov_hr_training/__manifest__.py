{
    'name': 'التدريب الحكومي — احتياجات وخطة ودورات',
    'summary': 'C-HR-03: Training needs assessment, annual plan, course registration, impact measurement',
    'version': '17.0.1.0.0',
    'category': 'الخدمات الحكومية التجريبية/الموارد البشرية',
    'author': 'Enterprise Solutions Demo',
    'license': 'LGPL-3',
    'depends': ['demo_gov_hr_employee', 'demo_branding'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/hr_training_views.xml',
        'views/hr_training_menu.xml',
    ],
    'installable': True,
    'application': False,
}
